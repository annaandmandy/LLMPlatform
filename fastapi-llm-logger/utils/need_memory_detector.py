"""NeedMemoryDetector

Determines whether a follow-up query requires prior context and, when
necessary, reconstructs the prompt with recently mentioned products.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import asyncio
import logging
import re

from .embeddings import get_embedding, compute_similarity

logger = logging.getLogger(__name__)


FOLLOWUP_KEYWORDS = [
    "what about",
    "how about",
    "and for",
    "and the",
    "the second one",
    "the previous one",
    "show me again",
    "same as before",
    "continue",
    "continue writing",
    "as mentioned",
    "as i said",
    "based on earlier",
    "based on above",
    "cheaper one",
    "something else",
    "other options",
    "more options",
]


class NeedMemoryDetector:
    """Detects whether a query needs contextual memory before LLM invocation."""

    def __init__(self, db=None, similarity_threshold: float = 0.7):
        self.db = db
        self.similarity_threshold = similarity_threshold
        if db is not None:
            self.queries_collection = db["queries"]
        else:
            self.queries_collection = None

    async def analyze(
        self,
        *,
        query: str,
        session_id: Optional[str],
        history: List[Dict[str, str]] | None,
        base_intent: str,
    ) -> Dict[str, Any]:
        """Return memory requirements and optional intent overrides."""

        history = history or []
        query = (query or "").strip()
        if not query:
            return {
                "need_memory": False,
                "intent": base_intent,
                "reason": "none",
                "history_window": [],
                "full_query": query,
            }

        query_lower = query.lower()
        need_memory = False
        reason = "none"
        intent = base_intent
        history_window: List[Dict[str, str]] = []
        full_query = query

        keyword_hit = any(phrase in query_lower for phrase in FOLLOWUP_KEYWORDS)
        if keyword_hit:
            logger.info("NeedMemoryDetector: keyword follow-up pattern detected")

        previous_doc = await self._get_last_query(session_id)
        previous_intent = previous_doc.get("intent") if previous_doc else None
        previous_product = self._extract_primary_product(previous_doc)
        if previous_doc:
            logger.info(
                "NeedMemoryDetector: previous intent=%s product=%s",
                previous_intent,
                previous_product,
            )

        if keyword_hit:
            need_memory = True
            reason = "keyword_match"

            if (
                previous_intent == "product_search"
                and not self._mentions_new_product_name(query)
            ):
                intent = "product_search"
                reason = "intent_override"
                if previous_product:
                    full_query = f"{previous_product} {query}"
                    logger.info("NeedMemoryDetector: reconstructed query -> %s", full_query)

        if not need_memory:
            sim_reason = await self._embedding_similarity_needed(history, query)
            if sim_reason:
                need_memory = True
                reason = sim_reason
                logger.info("NeedMemoryDetector: embedding similarity triggered")

        if need_memory:
            history_window = self._build_history_window(history)
            logger.info(
                "NeedMemoryDetector: returning %d history messages (reason=%s)",
                len(history_window),
                reason,
            )
        else:
            logger.info("NeedMemoryDetector: no additional context needed")

        return {
            "need_memory": need_memory,
            "intent": intent,
            "reason": reason,
            "history_window": history_window,
            "full_query": full_query,
        }

    async def _get_last_query(self, session_id: Optional[str]) -> Dict[str, Any]:
        if self.queries_collection is None or not session_id:
            return {}

        def _find_latest():
            return self.queries_collection.find_one(
                {"session_id": session_id},
                sort=[("timestamp", -1)]
            )

        try:
            doc = await asyncio.to_thread(_find_latest)
            return doc or {}
        except Exception as exc:
            logger.warning(f"NeedMemoryDetector: failed to load previous query: {exc}")
            return {}

    def _extract_primary_product(self, query_doc: Optional[Dict[str, Any]]) -> Optional[str]:
        if not query_doc:
            return None

        structured = query_doc.get("product_structured") or []
        if isinstance(structured, list) and structured:
            candidate = structured[0]
            if isinstance(candidate, dict):
                return candidate.get("title") or candidate.get("name")

        cards = query_doc.get("product_cards") or []
        if isinstance(cards, list) and cards:
            card = cards[0]
            if isinstance(card, dict):
                return card.get("title") or card.get("name")

        return None

    def _mentions_new_product_name(self, query: str) -> bool:
        return bool(re.search(r"\b[A-Z][a-zA-Z0-9\-]+", query))

    async def _embedding_similarity_needed(self, history: List[Dict[str, str]], query: str) -> Optional[str]:
        user_messages = [msg["content"] for msg in history if msg.get("role") == "user"]
        if not user_messages:
            return None

        recent_user_msgs = user_messages[-5:]
        try:
            query_embedding = get_embedding(query)
            for past_message in reversed(recent_user_msgs):
                past_embedding = get_embedding(past_message)
                similarity = compute_similarity(query_embedding, past_embedding)
                if similarity >= self.similarity_threshold:
                    return "embedding_similarity"
        except Exception as exc:
            logger.warning(f"NeedMemoryDetector: embedding similarity failed: {exc}")

        return None

    def _build_history_window(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        trimmed = [msg for msg in history if msg.get("role") in {"user", "assistant"}]
        if not trimmed:
            return []

        window = trimmed[-6:]
        if len(window) < 2:
            return window

        # Ensure the window starts with a user message when possible
        if window[0].get("role") != "user" and len(window) > 2:
            window = window[1:]

        return window[-6:]
