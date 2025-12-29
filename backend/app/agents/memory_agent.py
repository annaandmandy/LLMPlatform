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
import numpy as np
from .base_agent import BaseAgent
from app.services.embedding_service import embedding_service
from app.db.repositories.summary_repo import SummaryRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.query_repo import QueryRepository
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
            self.memories = db["memories"]  # Key/value memories collection
            self.summary_repo = SummaryRepository(db)
            self.session_repo = SessionRepository(db)
            self.query_repo = QueryRepository(db)  # Vectors stored in queries collection
        else:
            self.memories = None
            self.summary_repo = None
            self.session_repo = None
            self.query_repo = None

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
            # Get session messages using repository
            session = await self.session_repo.get_session(
                session_id=session_id,
                include_events=True
            )
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
            query_embedding = await embedding_service.generate_embedding(query)
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
            # Note: Embeddings are now stored automatically in queries collection
            # when queries are logged via QueryService. This method is kept for
            # compatibility but may not be actively used.
            logger.info(f"Embedding storage handled by QueryService for {role} message (session: {session_id})")

        except Exception as e:
            logger.error(f"Error in message embedding: {str(e)}")

    async def _store_summary(
        self,
        session_id: str,
        summary_text: str,
        message_count: int,
        model_used: str = "rule_based",
        user_id: Optional[str] = None,
    ):
        """
        Store session summary using repository.

        Args:
            session_id: Session identifier
            summary_text: Generated summary
            message_count: Number of messages summarized
            model_used: Model or strategy used to generate summary
            user_id: Optional user identifier
        """
        try:
            if self.summary_repo is None:
                logger.warning("Summary repository not initialized")
                return

            await self.summary_repo.create_or_update_summary(
                session_id=session_id,
                summary_text=summary_text,
                message_count=message_count,
                model_used=model_used,
                user_id=user_id
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
        Run semantic search over queries with embeddings using repository.
        """
        if self.query_repo is None:
            return [], []

        # Get queries with embeddings from the queries collection
        if session_id:
            vectors = await self.query_repo.get_session_queries(session_id=session_id, limit=200)
        elif user_id:
            vectors = await self.query_repo.get_user_query_history(user_id=user_id, limit=200)
        else:
            vectors = []

        # Filter only those with embeddings
        vectors = [v for v in vectors if v.get("embedding")]

        # Optionally extend with cross-session samples for this user
        if include_cross_session and user_id and len(vectors) < 50:
            extra_vectors = await self.query_repo.get_user_query_history(
                user_id=user_id,
                limit=200 - len(vectors)
            )
            extra_vectors = [v for v in extra_vectors if v.get("embedding")]
            vectors.extend(extra_vectors)

        if len(vectors) == 0:
            return [], []

        # Compute cosine similarity for each candidate
        similarities = []
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        for idx, vector in enumerate(vectors):
            candidate_vec = np.array(vector["embedding"])
            candidate_norm = np.linalg.norm(candidate_vec)

            if query_norm == 0 or candidate_norm == 0:
                similarity = 0.0
            else:
                dot_product = np.dot(query_vec, candidate_vec)
                similarity = float(dot_product / (query_norm * candidate_norm))

            similarities.append((idx, similarity))

        # Sort by similarity (descending) and take top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        similar_indices = similarities[:top_k]

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
        Return the most recent prompt/response pairs from the session events using repository.
        """
        if not session_id or self.session_repo is None:
            return []

        session = await self.session_repo.get_session(
            session_id=session_id,
            include_events=True
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
        Fetch recent summaries for the session and (optionally) across the user using repository.
        """
        if self.summary_repo is None:
            return []

        return await self.summary_repo.get_summaries_for_context(
            user_id=user_id,
            session_id=session_id
        )

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
