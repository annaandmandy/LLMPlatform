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
            "You must ask exactly 3 rounds of diagnostic questions (e.g., Budget, Usage context, Preferences) if you haven't already.\n"
            "\n"
            "Analyze the conversation history provided.\n"
            "1. Count how many diagnostic questions YOU have ALREADY asked and the user has answered since the start of this shopping session.\n"
            "2. If you have asked less than 3 questions, generate the NEXT single most important question to ask.\n"
            "   - Provide 3-4 short, clear options for the user to choose from (e.g., '$50-$100', 'Under $50', etc.). MAX 5 WORDS PER OPTION.\n"
            "   - Status should be 'question'.\n"
            "3. If you have already asked 3 questions and received answers, OR if the user explicitly asks for the result now, set status to 'complete'.\n"
            "   - Formulate a detailed search query that summarizes all the user's constraints and preferences gathered so far.\n"
            "\n"
            "Return valid JSON only:\n"
            "{\n"
            "  \"status\": \"question\" | \"complete\",\n"
            "  \"question\": \"Question text here...\",\n"
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
