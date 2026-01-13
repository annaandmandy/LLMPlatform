"""
Experiment Service.

Manages the lifecycle of the active AI Experiment (Graph).
Loads configuration and builds the LangGraph executable.
"""

import os
import logging
from typing import Any, Dict, Optional

from app.experiments.loader import ExperimentLoader
from app.experiments.schema import ExperimentConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

class ExperimentService:
    """
    Singleton service that holds the active Experiment Graph.
    """
    
    def __init__(self):
        self._active_graph = None
        self._active_config: Optional[ExperimentConfig] = None
        self._default_config_path = os.path.join(
            os.path.dirname(__file__), 
            "../experiments/configs/general_v1.json"
        )

    async def initialize(self):
        """Initialize the default experiment."""
        try:
            # In a real app, might load from DB or Env Var
            config_path = self._default_config_path
            logger.info(f"Loading experiment config from {config_path}")
            
            self._active_config = ExperimentLoader.load_config(config_path)
            self._active_graph = ExperimentLoader.build_graph(self._active_config)
            
            logger.info(f"Experiment '{self._active_config.experiment_id}' initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize experiment: {e}")
            raise

    def get_graph(self) -> Any:
        """Get the compiled LangGraph runnable."""
        if self._active_graph is None:
             # Lazy init if not called explicitly (though explicit init is better)
             # We can't await in sync property, so we might need to rely on app startup event
             raise RuntimeError("Experiment Graph not initialized. Call initialize() first.")
        return self._active_graph

    def get_config(self) -> ExperimentConfig:
        if self._active_config is None:
             raise RuntimeError("Experiment Config not initialized.")
        return self._active_config

# Global instance
experiment_service = ExperimentService()
