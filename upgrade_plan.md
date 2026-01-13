# LLM Research Platform: Upgrade Proposal & Architecture Roadmap

**Date:** January 8, 2026
**Project:** Finz Core Backend / LLM Research Platform
**Target Environment:** Railway (Hobby Plan)
**Current Status:** Functional Agentic Prototype (FastAPI + Next.js + LangGraph)
**Goal:** Production-Grade Research Environment (Mimicking Gemini/Claude capabilities)

---

## 1. Executive Summary
The current platform is a sophisticated hybrid application leveraging **LangGraph** for agentic orchestration. While it succeeds as a conversational interface, it currently lacks specific "Research-Grade" capabilities required for deep analysis, reproducible experiments, and commercial simulation (Ads).

This proposal outlines the roadmap to transform the codebase from a static "Chat Application" into a **Modular Experimentation Platform**. This will allow dynamic switching between configurations (e.g., General Chat vs. Sponsored Content Experiment) and provide deep observability into the model's reasoning process via **LangSmith**.

---

## 2. Key Functional Upgrades (The "Missing Pieces")

To achieve parity with advanced platforms (Claude Projects/Gemini) and enable specific research goals, the following modules will be integrated:

### 2.1. Real-Time Chain of Thought (CoT) Reveal 🧠
* **Goal:** Visualize the model's reasoning process before it generates the final answer (similar to OpenAI o1 or DeepSeek).
* **Implementation:**
    * **Backend:** Upgrade `stream()` to `stream_events()` in LangChain/LangGraph. Isolate internal agent thoughts (from `tool_calls` or `intermediate_steps`) and emit distinct SSE events (`event: thought`).
    * **Frontend:** Implement a collapsible "Thinking Process" UI component that renders these events in real-time, separate from the final response.

### 2.2. Deep Research Capabilities (RAG on Demand) 📚
* **File Ingestion (Claude Projects style):**
    * Enable users to upload PDF/CSV/Docs.
    * **Pipeline:** Upload $\rightarrow$ **Unstructured.io / LlamaParse** (Parsing) $\rightarrow$ Chunking $\rightarrow$ Vector Store (Atlas).
    * **Graph:** Add a `FileSearchTool` dynamically to the agent's toolkit.
* **Scrape & Store (Search Grounding):**
    * Enable agents to "read" external websites for up-to-date context.
    * **Tool:** Integrate **Firecrawl** to scrape URLs into clean Markdown.
    * **Storage:** Persist scraped content in MongoDB (`scraped_contents`) for persistent RAG retrieval during the session.

### 2.3. Commercial Experimentation (Ads/Sponsored Content) 💰
* **Goal:** Test the impact of RAG-based advertising on user experience and model bias.
* **Strategy:**
    * Create a `sponsored_products` collection with bidding metadata.
    * **Injection:** Implement an `AdsInjector` node or tool that interleaves sponsored results with organic search results.
    * **UI:** Frontend renders "Sponsored" labels based on metadata flags, controllable via experiment config.

---

## 3. Architectural Overhaul: "Experiment as Code"

To support the requirement of **reusable experiments** (switching between "General Chat" and "Ads Experiment" easily), we will refactor the backend from a static graph to a **Configuration-Driven Factory Pattern**.

### 3.1. The "Config-Driven" Concept
Instead of hardcoding the LangGraph workflow, the system will build the graph dynamically based on an `ExperimentConfig`.

* **Scenario A (General):** Graph = `[Memory] -> [Writer] -> [Product Search]`
* **Scenario B (Ads):** Graph = `[Memory] -> [Writer] -> [Product Search] -> [Ads Injector]`

### 3.2. Proposed Folder Structure
A new `experiments` module will be introduced to handle this logic.

```text
backend/
├── app/
│   ├── experiments/            # [NEW] Core Experimentation Layer
│   │   ├── __init__.py
│   │   ├── registry.py         # Registry of all available Agents/Tools
│   │   ├── schema.py           # Pydantic models for ExperimentConfig
│   │   ├── loader.py           # Factory that builds LangGraph from Config
│   │   └── configs/            # JSON/YAML definitions of experiments
│   │       ├── general_v1.json
│   │       └── ads_experiment_v1.json
│   │
│   ├── agents/                 # Pure Logic (Stateless)
│   │   ├── ads_agent.py        # [NEW] Specialized Ads Logic
│   │   └── ... (Existing agents)
│   │
│   ├── services/
│   │   └── graph_service.py    # Modified to call loader.build_graph(config)
```
### 3.3. Admin & Control
Admin API: Endpoints to create/update experiment configs.

Runtime Injection: The Frontend will fetch the active configuration on load, enabling features (e.g., show_sponsored_labels: true) without code deployment.

## 4. Observability Strategy: LangSmith (SaaS)
For a research environment hosted on resource-constrained infrastructure (Railway Hobby Plan), we prioritize minimal operational overhead.

### 4.1. The Logging Platform: LangSmith 🛠️
Decision: Utilize LangSmith (Cloud SaaS) for tracing and debugging.

Rationale:

Zero Infrastructure Overhead: Requires no additional containers (Postgres/Redis) or RAM, preserving Railway resources for the application logic.

Native Integration: Seamlessly integrates with LangGraph via environment variables.

Visualization: Provides best-in-class UI for visualizing agent loops and token usage out of the box.

### 4.2. Configuration
No code changes are required for basic tracing. The integration is handled via Environment Variables in Railway:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="[https://api.smith.langchain.com](https://api.smith.langchain.com)"
LANGCHAIN_API_KEY="<your-api-key>"
LANGCHAIN_PROJECT="finz-research-v1"
```
## 5. Roadmap
### Phase 1: Observability & Refactoring (Weeks 1-2)
[ ] Configure LangSmith environment variables on Railway.

[ ] Refactor backend/app to introduce the experiments/ folder structure.

[ ] Implement the "Graph Factory" to build graphs dynamically.

### Phase 2: Core Features (Weeks 3-4)
[ ] CoT: Update SSE streaming to emit thought events; Update UI.

[ ] Deep Research: Integrate Firecrawl (Scraping) and Unstructured (File Upload).

### Phase 3: Ads Experiment (Week 5)
[ ] Create ads_experiment_v1.json.

[ ] Implement AdsInjector node.

[ ] Update Frontend to render Sponsored Cards based on config flags.

## 6. Conclusion
This upgrade moves the platform from a "Chat App" to a scalable Research Instrument. By leveraging LangSmith for zero-overhead observability and implementing the "Experiment as Code" architecture, we ensure that the platform remains lightweight enough for Railway hosting while delivering the robust logging and flexibility needed for scientific analysis.