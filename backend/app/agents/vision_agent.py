"""
Vision Agent

Summarizes image attachments into concise text so non-vision models can consume them.
"""

from typing import Dict, Any, List, Optional
import logging
import os
import asyncio
from openai import OpenAI
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VisionAgent(BaseAgent):
    """
    Uses a vision-capable model to describe attached images.
    """

    def __init__(self, db=None, model: Optional[str] = None):
        super().__init__(name="VisionAgent", db=db)
        self.model = model or "gpt-4o-mini"
        self._client: Optional[OpenAI] = None
        self._disabled = False

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        query = request.get("query", "")
        attachments = request.get("attachments", [])
        if self._disabled:
            return {"vision_notes": ""}
        if not attachments:
            return {"vision_notes": ""}

        parts: List[Dict[str, Any]] = []
        for att in attachments:
            if att.get("type") == "image" and att.get("base64"):
                parts.append({"type": "image_url", "image_url": {"url": att["base64"]}})

        if not parts:
            return {"vision_notes": ""}

        messages = [
            {
                "role": "system",
                "content": "You analyze user-provided images and summarize key objects, text, and brand/product hints. Be concise.",
            },
            {
                "role": "user",
                "content": [{"type": "text", "text": f"Images attached. Task: extract details useful to answer: '{query}'."}] + parts,
            },
        ]

        try:
            client = self._get_client()
            resp = await asyncio.to_thread(
                client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.2,
            )
            if resp.choices and resp.choices[0].message.content:
                return {"vision_notes": resp.choices[0].message.content.strip()}
            return {"vision_notes": ""}
        except Exception as e:
            msg = str(e).lower()
            if "input-images" in msg and "limit 0" in msg:
                logger.warning("VisionAgent disabled due to zero image quota")
                self._disabled = True
            else:
                logger.warning(f"VisionAgent failed: {e}")
            return {"vision_notes": ""}
