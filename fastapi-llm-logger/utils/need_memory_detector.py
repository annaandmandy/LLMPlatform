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

    def __init__(
        self,
        db=None,
        similarity_threshold: float = 0.7,
        fallback_pairs: int = 1,
    ):
        self.db = db
        self.similarity_threshold = similarity_threshold
        if db is not None:
            self.queries_collection = db["queries"]
        else:
            self.queries_collection = None
        self.fallback_pairs = max(0, fallback_pairs)

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
        previous_topic = self._extract_product_topic(previous_doc)
        if previous_doc:
            logger.info(
                "NeedMemoryDetector: previous intent=%s product=%s category=%s",
                previous_intent,
                previous_product,
                previous_topic,
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
                full_query = self._build_reconstructed_query(
                    follow_up=query,
                    product_name=None,
                    topic=previous_topic,
                )
                logger.info("NeedMemoryDetector: reconstructed query -> %s", full_query)

        if not need_memory:
            sim_reason = await self._embedding_similarity_needed(history, query)
            if sim_reason:
                need_memory = True
                reason = sim_reason
                logger.info("NeedMemoryDetector: embedding similarity triggered")

        if need_memory:
            history_window = self._build_history_window(history)
            fallback_pair_added = False
            if len(history_window) < 2 and self.fallback_pairs and session_id:
                fallback_history = await self._history_from_previous_pairs(
                    session_id=session_id,
                    max_pairs=self.fallback_pairs,
                )
                if fallback_history:
                    history_window = (history_window + fallback_history)[-6:]
                    fallback_pair_added = True

            logger.info(
                "NeedMemoryDetector: returning %d history messages (reason=%s%s)",
                len(history_window),
                reason,
                ", fallback_pair" if fallback_pair_added else "",
            )
            for idx, message in enumerate(history_window, start=1):
                logger.info(
                    "NeedMemoryDetector history[%d] %s: %s",
                    idx,
                    message.get("role"),
                    message.get("content", "")[:200],
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

    def _extract_product_topic(self, query_doc: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Try to recover the broader product category or topic from structured cards
        or fall back to the original user query.
        """
        if not query_doc:
            return None

        structured = query_doc.get("product_structured") or []
        if isinstance(structured, list):
            for item in structured:
                if isinstance(item, dict):
                    category = item.get("category") or item.get("type")
                    if category:
                        return category

        cards = query_doc.get("product_cards") or []
        if isinstance(cards, list):
            for card in cards:
                if isinstance(card, dict):
                    tag = card.get("tag") or card.get("category")
                    if tag:
                        return tag

        query_text = (query_doc.get("query") or "").strip()
        return query_text or None

    def _build_reconstructed_query(
        self,
        *,
        follow_up: str,
        product_name: Optional[str],
        topic: Optional[str],
    ) -> str:
        parts = []
        if product_name:
            parts.append(product_name.strip())
        if topic:
            candidate = topic.strip()
            if candidate and candidate.lower() not in " ".join(parts).lower():
                parts.append(candidate)
        parts.append(follow_up.strip())
        return " ".join(part for part in parts if part)

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

    async def _history_from_previous_pairs(
        self,
        *,
        session_id: Optional[str],
        max_pairs: int,
    ) -> List[Dict[str, str]]:
        if self.queries_collection is None or not session_id or max_pairs <= 0:
            return []

        limit = max_pairs

        def _fetch_recent():
            cursor = self.queries_collection.find(
                {"session_id": session_id},
                sort=[("timestamp", -1)],
                limit=limit,
            )
            return list(cursor)

        try:
            docs = await asyncio.to_thread(_fetch_recent)
        except Exception as exc:
            logger.warning(f"NeedMemoryDetector: failed to load fallback history: {exc}")
            return []

        history: List[Dict[str, str]] = []
        for doc in reversed(docs):
            user_query = (doc.get("query") or "").strip()
            assistant_response = (doc.get("response") or "").strip()
            if not user_query or not assistant_response:
                continue
            history.append({"role": "user", "content": user_query})
            history.append({"role": "assistant", "content": assistant_response})

        return history
