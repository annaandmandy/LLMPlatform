"""
Configuration Schemas for Experiments.

Defines the structure of an experiment configuration file.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration for a specific tool."""
    name: str = Field(..., description="Tool identifier in the registry")
    config: Dict[str, Any] = Field(default_factory=dict, description="kwargs for the tool")


class AgentConfig(BaseModel):
    """Configuration for a specific agent node."""
    id: str = Field(..., description="Unique identifier for this node instance (e.g. 'writer_1')")
    type: str = Field(..., description="Agent Class identifier in the registry (e.g. 'WriterAgent')")
    tools: List[ToolConfig] = Field(default_factory=list, description="Tools available to this agent")
    config: Dict[str, Any] = Field(default_factory=dict, description="Additional kwargs for agent init")


class GraphEdge(BaseModel):
    """Definition of an edge in the StateGraph."""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    condition: Optional[str] = Field(None, description="Condition function name (if conditional edge)")
    path_map: Optional[Dict[str, str]] = Field(None, description="Map of condition result to target node IDs")


class ExperimentConfig(BaseModel):
    """Full configuration for an Agentic Experiment."""
    experiment_id: str = Field(..., description="Unique experiment slug")
    description: str = Field("", description="Human readable description")
    version: str = Field("1.0.0", description="Config version")
    
    # Global settings
    default_model: str = Field("gpt-4o-mini", description="Default model for agents")
    
    # Graph Definition
    agents: List[AgentConfig] = Field(..., description="Nodes in the graph")
    entry_point: str = Field(..., description="ID of the first node")
    edges: List[GraphEdge] = Field(default_factory=list, description="Connections between nodes")
    
    # Feature Flags
    show_sponsored_labels: bool = Field(False, description="Frontend flag for ads")
    enable_thinking_process: bool = Field(False, description="Show CoT UI")
