"""
Intent Agent

Wraps the intent classification utility to provide an agent interface for the graph.
"""

from typing import Dict, Any
import logging
from .base_agent import BaseAgent
from app.utils.intent_classifier import detect_intent

logger = logging.getLogger(__name__)

class IntentAgent(BaseAgent):
    """
    Agent that identifies user intent from the query.
    """

    def __init__(self, db=None):
        super().__init__(name="IntentAgent", db=db)

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        query = request.get("query", "")
        
        # Use existing utility
        intent_res = await detect_intent(query)
        
        return {
            "intent": intent_res["intent"],
            "intent_confidence": intent_res["confidence"],
            "matched_patterns": intent_res.get("matched_patterns", 0)
        }
