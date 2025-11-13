"""
Coordinator Agent

Routes incoming requests to appropriate specialized agents based on intent detection.
This is the entry point for the multi-agent system.
"""

from typing import Dict, Any, Optional
import logging
from .base_agent import BaseAgent
from utils.intent_classifier import detect_intent

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Coordinates task routing to specialized agents.

    The Coordinator:
    1. Analyzes the user query to detect intent
    2. Routes to appropriate agent(s)
    3. Collects and combines results
    4. Returns final response with metadata
    """

    def __init__(self, db=None):
        """
        Initialize the CoordinatorAgent.

        Args:
            db: MongoDB database instance
        """
        super().__init__(name="CoordinatorAgent", db=db)
        self.memory_agent = None
        self.product_agent = None
        self.writer_agent = None

    def set_agents(self, memory_agent, product_agent, writer_agent):
        """
        Set references to specialized agents.

        Args:
            memory_agent: MemoryAgent instance
            product_agent: ProductAgent instance
            writer_agent: WriterAgent instance
        """
        self.memory_agent = memory_agent
        self.product_agent = product_agent
        self.writer_agent = writer_agent
        logger.info(f"{self.name} agents configured")

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route request to appropriate agents based on intent.

        Args:
            request: Dictionary containing:
                - query: User query string
                - session_id: Session identifier
                - user_id: User identifier
                - history: Optional conversation history
                - model: Preferred model for LLM calls

        Returns:
            Dictionary containing:
                - response: Final response text
                - intent: Detected intent
                - product_cards: Optional product cards
                - memory_context: Optional retrieved context
                - agents_used: List of agents that processed the request
        """
        query = request.get("query", "")
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        history = request.get("history", [])
        model = request.get("model", "gpt-4o-mini-search-preview")

        logger.info(f"Processing query: {query[:100]}...")

        forced_intent_result = request.get("forced_intent_result")
        if forced_intent_result:
            intent_result = forced_intent_result
            intent = intent_result.get("intent", "general")
            confidence = intent_result.get("confidence", 1.0)
        else:
            # Step 1: Detect intent
            intent_result = await detect_intent(query, use_llm=True)
            intent = intent_result["intent"]
            confidence = intent_result["confidence"]

        logger.info(f"Intent detected: {intent} (confidence: {confidence:.2f})")

        # Initialize context collectors
        memory_context = None
        product_cards = None
        structured_products = None
        agents_used = [self.name]
        collected_citations: Optional[list] = None
        collected_tokens: Optional[Dict[str, Any]] = None
        raw_response: Optional[Dict[str, Any]] = None

        # Step 2: Route based on intent
        if intent == "product_search":
            # Product search flow: leverage ProductAgent dual-output prompt for structured data
            agents_used.extend(["WriterAgent", "ProductAgent"])

            writer_request = {
                **request,
                "intent": intent,
                "product_cards": None,
                "memory_context": None
            }
            writer_result = await self.writer_agent.run(writer_request)
            writer_output = writer_result["output"]
            final_response = writer_output["response"]
            collected_citations = writer_output.get("citations")
            collected_tokens = writer_output.get("tokens")
            raw_response = writer_output.get("raw_response")

            product_result = await self.product_agent.run({
                **request,
                "intent": intent,
                "llm_response": final_response
            })
            product_output = product_result["output"]
            product_cards = product_output.get("products", [])
            structured_products = product_output.get("structured_products")

        else:  # general intent
            agents_used.append("WriterAgent")

            writer_request = {
                **request,
                "intent": intent,
                "memory_context": None,
                "product_cards": None
            }
            writer_result = await self.writer_agent.run(writer_request)
            writer_output = writer_result["output"]
            final_response = writer_output["response"]
            collected_citations = writer_output.get("citations")
            collected_tokens = writer_output.get("tokens")
            raw_response = writer_output.get("raw_response")

        # Step 3: Return combined result
        result = {
            "response": final_response,
            "intent": intent,
            "intent_confidence": confidence,
            "agents_used": agents_used
        }

        # Add optional fields if present
        if product_cards:
            result["product_cards"] = product_cards

        if structured_products:
            result["product_json"] = structured_products

        if memory_context:
            result["memory_context"] = memory_context

        if collected_citations:
            result["citations"] = collected_citations

        if collected_tokens:
            result["tokens"] = collected_tokens

        if raw_response:
            result["raw_response"] = raw_response

        logger.info(f"Request processed. Agents used: {', '.join(agents_used)}")

        return result
