"""
Memory Agent

Handles conversation memory through:
1. Session summarization (mid-term memory)
2. Semantic search via embeddings (long-term memory)
3. RAG-based context retrieval
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from .base_agent import BaseAgent
from utils.embeddings import get_embedding, find_most_similar

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
        else:
            logger.warning(f"Unknown action: {action}")
            return {"error": f"Unknown action: {action}"}

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
            session = await asyncio.to_thread(
                self.db.sessions.find_one,
                {"session_id": session_id}
            )

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

            # Generate summary text
            summary_text = self._create_summary_text(messages)

            # Store summary in summaries collection
            await self._store_summary(session_id, summary_text, len(messages))

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
        top_k = request.get("top_k", 10)

        if not query:
            return {"context": []}

        try:
            # Generate query embedding
            query_embedding = get_embedding(query)

            # Find similar past messages from vectors collection
            pipeline = [
                {"$match": {"session_id": session_id}},
                {"$limit": 100}  # Limit search space for performance
            ]

            cursor = self.db.vectors.find({"session_id": session_id}).limit(100)
            vectors = await asyncio.to_thread(list, cursor)

            if len(vectors) == 0:
                return {"context": [], "message": "No past context available"}

            # Compute similarities
            candidate_embeddings = [v["embedding"] for v in vectors]
            similar_indices = find_most_similar(query_embedding, candidate_embeddings, top_k=top_k)

            # Get top similar messages
            context = []
            for idx, similarity in similar_indices:
                if similarity > 0.5:  # Only include if similarity > threshold
                    vector = vectors[idx]
                    context.append({
                        "role": vector.get("role"),
                        "content": vector.get("content"),
                        "similarity": similarity,
                        "timestamp": vector.get("timestamp")
                    })

            logger.info(f"Retrieved {len(context)} relevant context messages")

            return {
                "context": context,
                "query_embedding_dim": len(query_embedding)
            }

        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return {"context": [], "error": str(e)}

    async def store_message_embedding(
        self,
        session_id: str,
        role: str,
        content: str,
        message_index: int = 0
    ):
        """
        Store a message embedding in the vectors collection.

        Args:
            session_id: Session identifier
            role: "user" or "assistant"
            content: Message content
            message_index: Index in conversation
        """
        try:
            # Generate embedding
            embedding = get_embedding(content)

            # Store in vectors collection
            vector_doc = {
                "session_id": session_id,
                "message_index": message_index,
                "role": role,
                "content": content,
                "embedding": embedding,
                "timestamp": datetime.now()
            }

            await asyncio.to_thread(self.db.vectors.insert_one, vector_doc)
            logger.info(f"Stored embedding for {role} message (session: {session_id})")

        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")

    async def _store_summary(self, session_id: str, summary_text: str, message_count: int):
        """
        Store session summary in summaries collection.

        Args:
            session_id: Session identifier
            summary_text: Generated summary
            message_count: Number of messages summarized
        """
        try:
            # Check if summary document exists
            summary_doc = await asyncio.to_thread(
                self.db.summaries.find_one,
                {"session_id": session_id}
            )

            summary_entry = {
                "t": datetime.now(),
                "text": summary_text,
                "message_count": message_count
            }

            if summary_doc:
                # Append to existing summaries
                await asyncio.to_thread(
                    self.db.summaries.update_one,
                    {"session_id": session_id},
                    {"$push": {"summaries": summary_entry}}
                )
            else:
                # Create new summary document
                await asyncio.to_thread(
                    self.db.summaries.insert_one,
                    {
                        "session_id": session_id,
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
