# Future Roadmap

This document outlines the planned improvements and feature expansions for the LLM Platform.

## 1. Observability & Agent Transparency

### LangSmith Implementation
**Goal**: Deep tracing of complex multi-agent workflows.
-   **Why**: To debug where agents fail, measure latency per step, and visualize the LangGraph execution path.
-   **Implementation**: Integrate `langsmith` SDK, configure API keys, and instrument the `CoordinatorAgent` and sub-agents.

### Chain of Thought (CoT) Reveal
**Goal**: Show the user *how* the AI is thinking, not just the final answer.
-   **Frontend**: Add a collapsible "Thinking..." UI component that streams intermediate agent events (e.g., "Searching for products...", "Reading memory..."). Should be revealing the model's thought, not just what agent is being used.
-   **Backend**: Ensure all agents emit granular status events via the SSE stream before the final text chunk.

## 2. Experimentation Platform

### Structured Experiment Configuration
**Goal**: Robust A/B testing infrastructure.
-   **Config Management**: Create a structured system (DB or Config Files) to define experiment variants (e.g., `experiment_id: "aggressive_prompts"` vs `experiment_id: "conservative_prompts"`).
-   **Variable parameters**:
    -   System Prompts
    -   Model Temperatures
    -   Agent Routing Logic
-   **Tracking**: Ensure `experiment_id` is propagated to all session logs and analytics for comparison.

## 3. Infrastructure & storage

### S3 / Blob Storage Integration
**Goal**: Persist user uploads securely.
-   **Current State**: Files are local.
-   **Future**: Integrate AWS S3 or Google Cloud Storage for handling user-uploaded images/documents for the Vision Agent.

### Deep Research RAG
**Goal**: Autonomous web research capabilities.
-   **Implementation**: Add `Firecrawl` for scraping.
-   **Architecture**: New `ResearchAgent` in LangGraph.

### Enable different source upload
-   Currently we only have vision agent that reads the photo, next step could be file scraper.
