"""
Shopping Agent

Manages the shopping interview process:
1. Asks diagnostic questions to narrow down user preferences.
2. Generates options for easy user interaction.
3. Decides when enough information has been gathered to make a recommendation.
"""

from typing import Dict, Any, List, Optional
import logging
import json
import os
from openai import OpenAI
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ShoppingAgent(BaseAgent):
    """
    Orchestrates the shopping mode interview.
    """

    def __init__(self, db=None):
        super().__init__(name="ShoppingAgent", db=db)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # Use a smart model for reasoning

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze conversation and generate next question or signal completion.

        Args:
            request: Contains 'query', 'history', 'session_id', etc.

        Returns:
            Dict with keys:
            - status: "question" or "complete"
            - response: The question text (if status=question)
            - options: List of option strings (if status=question)
            - search_query: Refined search query (if status=complete)
        """
        query = request.get("query", "")
        history = request.get("history", [])

        # System prompt to guide the interview state machine
        system_prompt = (
            "You are an expert shopping assistant. Your goal is to help the user find the perfect product.\n"
            "You effectively interview the user to understand their needs before making a recommendation.\n"
            "You must ask exactly 3 rounds of diagnostic questions (e.g., Budget, Usage context, Preferences).\n"
            "\n"
            "CRITICAL: Count the number of questions YOU (the assistant) have already asked in the conversation history.\n"
            "1. If you see 0, 1, or 2 questions asked by you previously, generate question #1, #2, or #3.\n"
            "   - Status should be 'question'.\n"
            "   - Provide 3-4 short, clear options for the user to choose from (MAX 5 WORDS PER OPTION).\n"
            "2. If you see 3 or more questions already asked by you, set status to 'complete'.\n"
            "   - Even if the user hasn't fully answered, stop at 3 rounds to avoid fatigue.\n"
            "3. If the user explicitly asks for the result or says 'that is all', set status to 'complete'.\n"
            "\n"
            "When status is 'complete', formulate a detailed search query that summarizes all user constraints.\n"
            "\n"
            "Return valid JSON only:\n"
            "{\n"
            "  \"status\": \"question\" | \"complete\",\n"
            "  \"question\": \"Question text here (only if status is question)\",\n"
            "  \"options\": [\"Option 1\", \"Option 2\", \"Option 3\"],\n"
            "  \"search_query\": \"synthesized search query for product search\"\n"
            "}"
        )


        messages = [{"role": "system", "content": system_prompt}]
        
        # Add limited history to concise context
        # We assume the history contains the "Shopping Mode" interaction
        for msg in history[-10:]:
             # Handle both dict and object (Pydantic model) access if necessary, 
             # but here request['history'] comes from main.py as dicts usually if we process them
             # In main.py: history_messages = [{"role": msg.role, "content": msg.content} for msg in request.history]
             # So it is a list of dicts.
             role = msg.get("role", "user")
             content = msg.get("content", "")
             messages.append({"role": role, "content": content})
        
        # Add current user query
        if query:
            messages.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
                
            data = json.loads(content)
            
            return {
                "status": data.get("status", "question"),
                "response": data.get("question"),
                "options": data.get("options", []),
                "search_query": data.get("search_query", query)
            }

        except Exception as e:
            logger.error(f"ShoppingAgent error: {e}")
            # Fallback to general chat if something breaks
            return {
                "status": "complete",
                "search_query": query
            }
