"""
Base Agent Class

All agents inherit from this base class to ensure consistent interface
and logging capabilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent system.

    Each agent must implement the execute() method which defines its core functionality.
    """

    def __init__(self, name: str, db=None):
        """
        Initialize the base agent.

        Args:
            name: Agent name for logging and tracking
            db: MongoDB database instance (optional)
        """
        self.name = name
        self.db = db
        self.execution_count = 0
        logger.info(f"{self.name} initialized")

    @abstractmethod
    async def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.

        Args:
            request: Dictionary containing the request data

        Returns:
            Dictionary containing the agent's output
        """
        pass

    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wrapper method that adds logging and metrics around execute().

        Args:
            request: Dictionary containing the request data

        Returns:
            Dictionary containing:
                - output: The agent's result
                - metadata: Execution metadata (latency, tokens, etc.)
        """
        start_time = datetime.now()
        self.execution_count += 1

        logger.info(f"{self.name} started execution #{self.execution_count}")

        try:
            output = await self.execute(request)

            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            logger.info(f"{self.name} completed in {latency_ms:.2f}ms")

            return {
                "output": output,
                "metadata": {
                    "agent_name": self.name,
                    "latency_ms": latency_ms,
                    "timestamp": end_time.isoformat(),
                    "execution_count": self.execution_count
                }
            }

        except Exception as e:
            end_time = datetime.now()
            latency_ms = (end_time - start_time).total_seconds() * 1000

            logger.error(f"{self.name} failed: {str(e)}")

            raise
