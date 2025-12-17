"""
Memory Agent

Handles conversation memory through:
1. Session summarization (mid-term memory)
2. Semantic search via embeddings (long-term memory)
3. RAG-based context retrieval
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime
import asyncio
from .base_agent import BaseAgent
from utils.embeddings import get_embedding, find_most_similar
from openai import OpenAI
import os

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """
    Manages conversation memory and retrieval.

    Capabilities:
    - Store message embeddings for semantic search
    - Generate session summaries every N turns
    - Retrieve relevant past context using RAG
    """

    def __init__(self, db=None, summary_interval: int = 10):
        """
        Initialize the MemoryAgent.

        Args:
            db: MongoDB database instance
            summary_interval: Create summary every N message pairs (default: 10)
        """
        super().__init__(name="MemoryAgent", db=db)
        self.summary_interval = summary_interval
        if db is not None:
            self.sessions = db.sessions
            self.vectors = db.vectors
            self.summaries = db.summaries
            self.memories = db["memories"]
        else:
            self.sessions = None
            self.vectors = None
            self.summaries = None
            self.memories = None

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute memory operations based on action type.

        Args:
            request: Dictionary containing:
                - action: "summarize" or "retrieve"
                - query: User query (for retrieve action)
                - session_id: Session identifier
                - history: Conversation history (for summarize)

        Returns:
            Dictionary containing summary or retrieved context
        """
        action = request.get("action", "retrieve")

        if action == "summarize":
            return await self._summarize_session(request)
        elif action == "retrieve":
            return await self._retrieve_context(request)
        elif action == "context_bundle":
            return await self._retrieve_context(request)
        else:
            logger.warning(f"Unknown action: {action}")
            return {"error": f"Unknown action: {action}"}

    async def summarize_session(self, session_id: str) -> Dict[str, Any]:
        """
        Public helper to summarize a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Summary payload identical to execute({"action": "summarize"})
        """
        if not session_id:
            return {"summary": "No session ID provided"}

        return await self._summarize_session({"session_id": session_id})

    async def _summarize_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of the conversation session.

        Args:
            request: Request containing session_id and optional history

        Returns:
            Dictionary with summary text
        """
        session_id = request.get("session_id")

        if not session_id:
            return {"summary": "No session ID provided"}

        try:
            # Get session messages from sessions collection
            session = await self.sessions.find_one({"session_id": session_id})
            user_id = session.get("user_id") if session else None

            if not session:
                return {"summary": "No conversation history found"}

            # Extract prompt/response events
            events = session.get("events", [])
            messages = []

            for event in events:
                if event.get("type") == "prompt":
                    messages.append({
                        "role": "user",
                        "content": event.get("data", {}).get("query") or event.get("data", {}).get("text", ""),
                        "timestamp": event.get("t")
                    })
                elif event.get("type") == "model_response":
                    messages.append({
                        "role": "assistant",
                        "content": event.get("data", {}).get("response") or event.get("data", {}).get("text", ""),
                        "timestamp": event.get("t")
                    })

            if len(messages) == 0:
                return {"summary": "No messages to summarize"}

            # Generate summary text (LLM first, fall back to rule-based)
            summary_text = await self._generate_llm_summary(messages)
            if not summary_text:
                summary_text = self._create_summary_text(messages)

            # Store summary in summaries collection
            await self._store_summary(
                session_id,
                summary_text,
                len(messages),
                model_used="gpt-4o-mini" if summary_text else "rule_based",
                user_id=user_id,
            )

            transcript = [
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                for msg in messages
            ]

            return {
                "summary": summary_text,
                "message_count": len(messages),
                "transcript": transcript
            }

        except Exception as e:
            logger.error(f"Error summarizing session: {str(e)}")
            return {"summary": f"Error generating summary: {str(e)}"}

    async def _retrieve_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant past context using semantic search.

        Args:
            request: Request containing query and session_id

        Returns:
            Dictionary with retrieved context messages
        """
        query = request.get("query", "")
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        top_k = request.get("top_k", 8)
        include_cross_session = request.get("include_cross_session", True)

        if not query:
            return {"context": [], "recent_messages": [], "summaries": []}

        try:
            query_embedding = get_embedding(query)
            context, vectors = await self._semantic_search(
                query_embedding=query_embedding,
                session_id=session_id,
                user_id=user_id,
                top_k=top_k,
                include_cross_session=include_cross_session,
            )

            recent_messages = await self._get_recent_messages(session_id, limit=6)
            summaries = await self._get_summaries(user_id=user_id, session_id=session_id)
            memories = await self._get_user_memories(user_id=user_id, limit=8)

            bundle = {
                "context": context,
                "recent_messages": recent_messages,
                "summaries": summaries,
                "memories": memories,
                "query_embedding_dim": len(query_embedding),
            }

            logger.info(f"Retrieved {len(context)} similar snippets, {len(summaries)} summaries, {len(recent_messages)} recents")

            return bundle

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return {"context": [], "error": str(e)}

    async def store_message_embedding(
        self,
        session_id: str,
        role: str,
        content: str,
        message_index: int = 0,
        user_id: Optional[str] = None,
    ):
        """
        Store a message embedding in the vectors collection.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            message_index: Index in conversation
            user_id: Optional user identifier
        """
        try:
            # Generate embedding
            embedding = get_embedding(content)

            # Store in vectors collection
            vector_doc = {
                "session_id": session_id,
                "user_id": user_id,
                "message_index": message_index,
                "role": role,
                "content": content,
                "embedding": embedding,
                "timestamp": datetime.now()
            }

            await self.vectors.insert_one(vector_doc)
            logger.info(f"Stored embedding for {role} message (session: {session_id})")

        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")

    async def _store_summary(
        self,
        session_id: str,
        summary_text: str,
        message_count: int,
        model_used: str = "rule_based",
        user_id: Optional[str] = None,
    ):
        """
        Store session summary in summaries collection.

        Args:
            session_id: Session identifier
            summary_text: Generated summary
            message_count: Number of messages summarized
            model_used: Model or strategy used to generate summary
        """
        try:
            # Check if summary document exists
            summary_doc = await self.summaries.find_one({"session_id": session_id})

            summary_entry = {
                "t": datetime.now(),
                "text": summary_text,
                "message_count": message_count,
                "model": model_used,
            }

            if summary_doc:
                # Append to existing summaries
                await self.summaries.update_one(
                    {"session_id": session_id},
                    {"$push": {"summaries": summary_entry}}
                )
            else:
                # Create new summary document
                await self.summaries.insert_one(
                    {
                        "session_id": session_id,
                        "user_id": user_id,
                        "summaries": [summary_entry],
                        "created_at": datetime.now()
                    }
                )

            logger.info(f"Stored summary for session {session_id}")

        except Exception as e:
            logger.error(f"Error storing summary: {str(e)}")

    def _create_summary_text(self, messages: List[Dict]) -> str:
        """
        Create a lightweight conversational summary without calling an LLM.

        Args:
            messages: List of message dictionaries ordered by time

        Returns:
            Human-friendly summary text
        """
        if not messages:
            return "No conversation history found."

        def _clean(text: str, limit: int = 180) -> str:
            cleaned = " ".join(text.split())
            return (cleaned[:limit] + "…") if len(cleaned) > limit else cleaned

        pairs: List[Dict[str, str]] = []
        pending_user: Optional[str] = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                pending_user = content
            elif role == "assistant" and pending_user:
                pairs.append({
                    "user": pending_user,
                    "assistant": content
                })
                pending_user = None

        if not pairs:
            return "Conversation contains system messages only."

        summary_lines = ["Here’s a quick summary of the recent conversation:", ""]

        recent_pairs = pairs[-5:]  # last up to five exchanges
        for idx, pair in enumerate(recent_pairs, start=1):
            summary_lines.append(f"{idx}. **User asked:** {_clean(pair['user'])}")
            summary_lines.append(f"   **Assistant replied:** {_clean(pair['assistant'])}")

        # Extract key takeaways from assistant replies
        takeaways: List[str] = []
        for pair in recent_pairs:
            reply = pair["assistant"]
            for line in reply.splitlines():
                line = line.strip("•*- ").strip()
                if len(line) < 20:
                    continue
                if line[0].isalpha():
                    takeaways.append(_clean(line, 140))
                if len(takeaways) >= 5:
                    break
            if len(takeaways) >= 5:
                break

        if takeaways:
            summary_lines.append("")
            summary_lines.append("Key points mentioned:")
            for takeaway in takeaways:
                summary_lines.append(f"- {takeaway}")

        return "\n".join(summary_lines)

    async def _generate_llm_summary(self, messages: List[Dict]) -> Optional[str]:
        """
        Generate a concise summary with an LLM when available.
        Falls back to rule-based summary if the call fails.
        """
        if not messages:
            return None

        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Keep the window small to control cost
            recent = messages[-12:]
            prompt_parts = []
            for msg in recent:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")

            prompt = (
                "You are summarizing a chat for fast recall. "
                "Return 4-6 bullet points capturing tasks, decisions, preferences, constraints, and data values. "
                "Stay under 120 tokens. No extra commentary.\n\n"
                + "\n".join(prompt_parts)
            )

            completion = await asyncio.to_thread(
                client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize the dialogue for later retrieval."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=200,
                temperature=0.2,
            )

            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"LLM summary failed, using rule-based summary: {e}")
            return None

    async def _semantic_search(
        self,
        query_embedding: List[float],
        session_id: Optional[str],
        user_id: Optional[str],
        top_k: int = 8,
        include_cross_session: bool = True,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Run semantic search over vectors for the user/session.
        """
        if self.vectors is None:
            return [], []

        vector_filter: Dict[str, Any] = {}
        if session_id:
            vector_filter["session_id"] = session_id
        if user_id:
            vector_filter["user_id"] = user_id

        cursor = self.vectors.find(vector_filter).sort("timestamp", -1).limit(200)
        vectors = await cursor.to_list(length=200)

        # Optionally extend with cross-session samples for this user
        if include_cross_session and user_id and len(vectors) < 50:
            extra_cursor = (
                self.vectors.find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(200 - len(vectors))
            )
            extra_vectors = await extra_cursor.to_list(length=200 - len(vectors))
            vectors.extend(extra_vectors)

        if len(vectors) == 0:
            return [], []

        candidate_embeddings = [v["embedding"] for v in vectors]
        similar_indices = find_most_similar(query_embedding, candidate_embeddings, top_k=top_k)

        context = []
        for idx, similarity in similar_indices:
            if similarity > 0.45:
                vector = vectors[idx]
                context.append(
                    {
                        "role": vector.get("role"),
                        "content": vector.get("content"),
                        "similarity": similarity,
                        "timestamp": vector.get("timestamp"),
                        "session_id": vector.get("session_id"),
                    }
                )

        return context, vectors

    async def _get_recent_messages(self, session_id: Optional[str], limit: int = 6) -> List[Dict[str, Any]]:
        """
        Return the most recent prompt/response pairs from the session events.
        """
        if not session_id or self.sessions is None:
            return []

        session = await self.sessions.find_one(
            {"session_id": session_id},
            {"events": {"$slice": -limit * 2}},
        )
        if not session:
            return []

        recent = []
        for ev in session.get("events", [])[-limit * 2:]:
            if ev.get("type") == "prompt":
                recent.append(
                    {"role": "user", "content": ev.get("data", {}).get("text", ""), "timestamp": ev.get("t")}
                )
            elif ev.get("type") == "model_response":
                recent.append(
                    {"role": "assistant", "content": ev.get("data", {}).get("text", ""), "timestamp": ev.get("t")}
                )
        return recent[-limit:]

    async def _get_summaries(self, user_id: Optional[str], session_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        Fetch recent summaries for the session and (optionally) across the user.
        """
        if self.summaries is None:
            return []

        filters: List[Dict[str, Any]] = []
        if session_id:
            filters.append({"session_id": session_id})
        if user_id:
            filters.append({"user_id": user_id})

        summaries: List[Dict[str, Any]] = []
        for f in filters:
            cursor = self.summaries.find(f).sort("created_at", -1).limit(2)
            docs = await cursor.to_list(length=2)
            for doc in docs:
                # Only take the newest summary entry per doc to save tokens
                latest_entry = doc.get("summaries", [])[-1:] or []
                for entry in latest_entry:
                    summaries.append(
                        {
                            "session_id": doc.get("session_id"),
                            "summary": entry.get("text"),
                            "message_count": entry.get("message_count"),
                            "model": entry.get("model"),
                            "timestamp": entry.get("t"),
                        }
                    )
        # deduplicate by summary text + session_id
        seen = set()
        unique = []
        for s in summaries:
            key = (s.get("session_id"), s.get("summary"))
            if key in seen:
                continue
            seen.add(key)
            unique.append(s)
        # Keep only the newest few summaries for prompt usage
        return unique[:3]

    async def _get_user_memories(self, user_id: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
        """
        Return stored key/value memories for the user (if the collection exists).
        """
        if not user_id or self.memories is None:
            return []

        cursor = self.memories.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
        memories = await cursor.to_list(length=limit)
        return [
            {
                "key": mem.get("key"),
                "value": mem.get("value"),
                "updated_at": mem.get("updated_at"),
                "tokenCount": mem.get("tokenCount"),
            }
            for mem in memories
        ]
