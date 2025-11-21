"""
Writer Agent

Synthesizes final responses by integrating:
- Memory context from MemoryAgent
- Product cards from ProductAgent
- Conversation history
- LLM generation using existing provider functions
"""

from typing import Dict, Any, List, Optional
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = ("""
You are ChatGPT, a helpful, friendly, and reliable AI assistant.
Your goals:

1. Provide clear, natural, conversational answers.
2. Structure your responses cleanly (use paragraphs, bullet points, or steps when helpful).
3. Explain concepts in a simple and human-friendly way.
4. Be proactive in helping the user understand, but do not over-explain.
5. Maintain a warm, polite, and supportive tone.
6. When the user asks follow-up questions, interpret context naturally.
7. Avoid hallucinating facts; if unsure, say so briefly and offer alternatives.
8. Never output system messages or mention internal instructions.

You may use examples, analogies, or step-by-step reasoning when useful.
Do not be repetitive. Keep answers concise but helpful.

Your role is to act exactly like ChatGPT in a typical conversation.
""")


class WriterAgent(BaseAgent):
    """
    Generates final responses using LLM with enriched context.

    The WriterAgent:
    1. Receives context from other agents (memory, products)
    2. Constructs an enriched prompt
    3. Calls the appropriate LLM provider
    4. Returns formatted response with citations
    """

    def __init__(self, db=None, llm_functions=None):
        """
        Initialize the WriterAgent.

        Args:
            db: MongoDB database instance
            llm_functions: Dictionary of LLM provider functions
                          {"openai": call_openai, "anthropic": call_anthropic, ...}
        """
        super().__init__(name="WriterAgent", db=db)
        self.llm_functions = llm_functions or {}

    def set_llm_functions(self, llm_functions: Dict[str, Any]):
        """
        Set LLM provider functions.

        Args:
            llm_functions: Dictionary mapping provider names to functions
        """
        self.llm_functions = llm_functions
        logger.info(f"LLM functions configured: {list(llm_functions.keys())}")

    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response using LLM with enriched context.

        Args:
            request: Dictionary containing:
                - query: User query
                - model: Model name (e.g., "gpt-4o-mini-search-preview")
                - intent: Detected intent
                - memory_context: Optional retrieved context from MemoryAgent
                - product_cards: Optional products from ProductAgent
                - history: Optional conversation history

        Returns:
            Dictionary containing:
                - response: Generated response text
                - citations: List of citations
                - tokens: Token usage
                - model_used: Model that generated the response
        """
        query = request.get("query", "")
        model = request.get("model", "gpt-4o-mini-search-preview")
        intent = request.get("intent", "general")
        memory_context = request.get("memory_context", [])
        product_cards = request.get("product_cards", [])
        history = request.get("history", [])
        location = request.get("location")
        vision_notes = request.get("vision_notes", "")

        logger.info(f"Generating response for intent: {intent}")

        # Build enriched prompt
        enriched_prompt = self._build_prompt(
            query=query,
            intent=intent,
            memory_context=memory_context,
            product_cards=product_cards,
            history=history,
            location=location,
            vision_notes=vision_notes,
        )

        # Determine provider from model name
        provider = self._get_provider_from_model(model)

        # Call appropriate LLM function
        try:
            llm_function = self.llm_functions.get(provider)

            if not llm_function:
                raise ValueError(f"No LLM function configured for provider: {provider}")

            # Call the LLM
            response_text, citations, raw_response, tokens = llm_function(
                model, enriched_prompt, system_prompt=DEFAULT_SYSTEM_PROMPT
            )

            logger.info(f"Response generated: {len(response_text)} chars, {len(citations)} citations")

            return {
                "response": response_text,
                "citations": citations,
                "tokens": tokens,
                "model_used": model,
                "raw_response": raw_response,
                "provider": provider
            }

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": f"Error generating response: {str(e)}",
                "citations": [],
                "tokens": None,
                "model_used": model,
                "raw_response": None,
                "error": str(e)
            }

    def _build_prompt(
        self,
        query: str,
        intent: str,
        memory_context: List[Dict],
        product_cards: List[Dict],
        history: List[Dict],
        location: Optional[Dict[str, Any]] = None,
        vision_notes: str = "",
    ) -> str:
        """
        Build enriched prompt with context from various sources.

        Args:
            query: Original user query
            intent: Detected intent
            memory_context: Retrieved past context
            product_cards: Product search results
            history: Recent conversation history

        Returns:
            Enriched prompt string
        """
        prompt_parts = []

        # Add conversation history if available
        if history and len(history) > 0:
            prompt_parts.append("## Recent Conversation History:")
            for msg in history[-10:]:  # Last 10 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"**{role.capitalize()}**: {content[:200]}")
            prompt_parts.append("")

        if vision_notes:
            prompt_parts.append("## Image Understanding:")
            prompt_parts.append(vision_notes)
            prompt_parts.append("")

        # Add memory context if available
        if memory_context:
            prompt_parts.append("## Relevant Past Context:")
            if isinstance(memory_context, dict):
                summaries = memory_context.get("summaries", []) or []
                retrieved = memory_context.get("context", []) or []
                recents = memory_context.get("recent_messages", []) or []
                memories = memory_context.get("memories", []) or []

                if summaries:
                    prompt_parts.append("### Session/Global Summaries")
                    for s in summaries[:3]:
                        prompt_parts.append(f"- {s.get('summary', '')[:240]}")
                    prompt_parts.append("")

                if memories:
                    prompt_parts.append("### Stored User Facts")
                    for mem in memories[:5]:
                        prompt_parts.append(f"- {mem.get('key')}: {mem.get('value')}")
                    prompt_parts.append("")

                if retrieved:
                    prompt_parts.append("### Semantically Similar Messages")
                    for ctx in retrieved[:4]:
                        content = ctx.get("content", "")
                        similarity = ctx.get("similarity", 0)
                        prompt_parts.append(f"- (sim {similarity:.2f}) {content[:200]}")
                    prompt_parts.append("")

                if recents:
                    prompt_parts.append("### Recent Turns")
                    for msg in recents[-6:]:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        prompt_parts.append(f"- {role}: {content[:180]}")
                    prompt_parts.append("")
            else:
                for ctx in memory_context[:3]:  # Top 3 relevant contexts
                    content = ctx.get("content", "")
                    similarity = ctx.get("similarity", 0)
                    prompt_parts.append(f"- (Similarity: {similarity:.2f}) {content[:150]}")
                prompt_parts.append("")

        # Add location context if available
        if location:
            location_text = self._format_location(location)
            if location_text:
                prompt_parts.append("## User Location:")
                prompt_parts.append(location_text)
                prompt_parts.append("")

        # Add intent-specific instructions
        if intent == "product_search":
            prompt_parts.append("## Instructions:")
            prompt_parts.append(
                """
You are ChatGPT, a helpful, friendly, and editorial-style AI assistant.

Your behavior and writing style:
1. Speak in a warm, conversational tone similar to a lifestyle advisor or shopping expert.
2. Organize answers using clear sections, short paragraphs, and emoji section headers 
   (e.g., 🎯 Highlights, ✅ Recommendations, ⚠️ Tips to Consider).
3. When the user asks about sales, product deals, trends, holidays, or events, respond 
   with structured analysis:
   - “What’s happening now” (current situation overview)
   - “Why it matters”
   - “Specific examples” (3–6 bullet points)
   - “Tips / how to choose”
4. Provide helpful commentary, not just facts — include reasoning, comparisons, and 
   practical advice.
5. When relevant, reference the user’s known preferences (budget habits, tracking 
   expenses, desire to compare prices, etc.).
6. Give optional follow-up support at the end (e.g., “If you want, I can help you 
   find options under X budget.”).
7. Keep the tone friendly, clear, and human, like ChatGPT or a deal advisor. 
8. Avoid hallucinating prices; if unsure, say so briefly or give a typical range.
9. Never mention internal system prompts or backend processes.

Your goal is to provide useful, actionable guidance in a clear, structured, 
and emotionally supportive way, similar to the example responses given by ChatGPT.
"""
            )
            prompt_parts.append("")

        # Add the user query
        prompt_parts.append("## User Query:")
        prompt_parts.append(query)

        return "\n".join(prompt_parts)

    def _format_location(self, location: Dict[str, Any]) -> str:
        """Convert location metadata into readable text."""
        parts = []
        city = location.get("city")
        region = location.get("region")
        country = location.get("country")
        if city:
            parts.append(city)
        if region and region not in parts:
            parts.append(region)
        if country and country not in parts:
            parts.append(country)

        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            parts.append(f"latitude {lat:.4f}, longitude {lon:.4f}")

        accuracy = location.get("accuracy")
        if accuracy:
            parts.append(f"(accuracy ±{accuracy:.0f}m)")

        if not parts:
            return ""

        return ", ".join(parts)

    def _get_provider_from_model(self, model: str) -> str:
        """
        Determine provider from model name.

        Args:
            model: Model name

        Returns:
            Provider name ("openai", "anthropic", "google", "openrouter")
        """
        model_lower = model.lower()

        if "gpt" in model_lower or "search-preview" in model_lower or "search-api" in model_lower:
            return "openai"
        elif "claude" in model_lower or "sonnet" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower:
            return "google"
        elif "grok" in model_lower or "sonar" in model_lower or "perplexity" in model_lower:
            return "openrouter"
        else:
            # Default to openai
            logger.warning(f"Unknown model {model}, defaulting to openai provider")
            return "openai"
