# Voice-to-Voice AI Assistant — Project Task List

> **Learning project**: Go one step at a time. Each phase builds on the previous one.
> Check off tasks as you complete them. Each task includes a "Why" to help you understand the goal.

---

## Phase 0 — Environment & Project Setup

> Goal: Get your machine ready before writing a single line of real code.

- [x] **0.1** Create a Python virtual environment (`python -m venv .venv`) and activate it
- [x] **0.2** Create `requirements.txt` with initial dependencies (listed in Phase 1+)
- [x] **0.3** Create `.env.example` with all required environment variable keys (no secrets)
- [x] **0.4** Copy `.env.example` → `.env` and fill in your API keys (never commit `.env`)
- [x] **0.5** Create a `.gitignore` that excludes `.env`, `__pycache__`, `.venv`, large data files
- [ ] **0.6** Initialize a git repository and make the first commit

---

## Phase 1 — Data Acquisition & Preprocessing

> Goal: Build the private product catalog that the AI will search.

### 1.1 Download Dataset
- [x] **1.1.1** Download **Amazon Product Dataset 2020** from Kaggle (requires Kaggle account + API key)
- [ ] **1.1.2** Filter to one category for a manageable start — e.g., **Household Cleaning**
- [x] **1.1.3** Save the raw CSV/JSON into `data/raw/`

### 1.2 Explore & Understand the Data
- [x] **1.2.1** Open the data in a Jupyter notebook (`notebooks/01_explore_data.ipynb`)
- [x] **1.2.2** Print column names, data types, and sample rows
- [x] **1.2.3** Count nulls per column; understand what `features`, `ingredients`, `rating` look like
- [x] **1.2.4** Plot price distribution to understand the range

### 1.3 Clean & Normalize
- [x] **1.3.1** Select and keep only needed columns: `id, title, brand, category, price, rating, features, ingredients`
- [x] **1.3.2** Drop rows with null `title` or `price`
- [x] **1.3.3** Normalize price to a float (strip `$`, handle ranges by taking the lower bound)
- [ ] **1.3.4** (Optional) Normalize price-per-oz for fair comparisons
- [x] **1.3.5** Create a `text_for_embedding` column: concatenate `title + features + ingredients`
- [x] **1.3.6** Save cleaned data to `data/processed/products.parquet`

### 1.4 (Optional) Reviews
- [ ] **1.4.1** If review data is available, join top 3 review snippets per product into `text_for_embedding`
- [ ] **1.4.2** Save to `data/processed/reviews.parquet`

---

## Phase 2 — Vector Index (Agentic RAG Foundation)

> Goal: Make the catalog searchable by meaning, not just keywords.

### 2.1 Choose an Embedding Model
- [x] **2.1.1** Pick an embedding provider (e.g., OpenAI `text-embedding-3-small`, or a local HuggingFace model)
- [x] **2.1.2** Add the embedding model name to `.env` / config

### 2.2 Generate Embeddings
- [x] **2.2.1** Write `scripts/build_index.py` that reads `products.parquet`
- [x] **2.2.2** Embed the `text_for_embedding` column in batches (to stay within API rate limits)
- [x] **2.2.3** Save embeddings alongside metadata

### 2.3 Build the Vector Store
- [x] **2.3.1** Choose a vector DB: **ChromaDB** (easy, local) or **FAISS** (fast, no server needed)
- [x] **2.3.2** Store each product as a document with metadata: `{id, title, brand, price, rating, category}`
- [x] **2.3.3** Save the index to `data/index/` so it can be reloaded without recomputing
- [x] **2.3.4** Test: query "eco-friendly stainless steel cleaner" and verify top results make sense

### 2.4 Add Metadata Filters
- [x] **2.4.1** Implement price-range filter (e.g., `price <= 15`)
- [x] **2.4.2** Implement category filter
- [x] **2.4.3** Test filtered queries

---

## Phase 3 — MCP Server (Two-Tool Requirement)

> Goal: Create a unified interface that exposes both private search and live web search as "tools" the AI can call.

### 3.1 Understand MCP
- [ ] **3.1.1** Read the Model Context Protocol (MCP) spec overview (~15 min)
- [ ] **3.1.2** Understand what "tool discovery" and "tool call" mean in MCP

### 3.2 Set Up the MCP Server Project
- [x] **3.2.1** Create `mcp_server/` folder
- [x] **3.2.2** Install the MCP Python SDK: `pip install mcp`
- [x] **3.2.3** Create `mcp_server/server.py` with a basic MCP server skeleton

### 3.3 Implement Tool 1 — `rag.search`
- [x] **3.3.1** Define JSON schema: input `{query: str, max_price?: float, category?: str, top_k?: int}`
- [x] **3.3.2** Implement the function: load the vector index and run a filtered similarity search
- [x] **3.3.3** Return `{sku, title, price, rating, brand, ingredients, doc_id}`
- [x] **3.3.4** Register as an MCP tool with name `rag.search`
- [x] **3.3.5** Test the tool in isolation

### 3.4 Implement Tool 2 — `web.search`
- [x] **3.4.1** Pick a web search API: **Tavily** (used instead of Brave — free tier, AI-optimized)
- [x] **3.4.2** Add the API key to `.env`
- [x] **3.4.3** Define JSON schema: input `{query: str, top_k?: int}`
- [x] **3.4.4** Implement the function: call the API, normalize results to `{title, url, snippet, price?, availability?}`
- [x] **3.4.5** Add response caching (TTL 180 seconds) using `cachetools.TTLCache`
- [x] **3.4.6** Add rate-limit handling (try/except with error dict returned)
- [x] **3.4.7** Register as an MCP tool with name `web.search`
- [x] **3.4.8** Test the tool in isolation

### 3.5 Wire Up Transport
- [x] **3.5.1** Use **stdio transport** (simplest): the server reads/writes JSON over stdin/stdout
- [x] **3.5.2** Verify tool discovery works (list available tools)
- [x] **3.5.3** Log every request and response with timestamps to `logs/mcp.log`

---

## Phase 4 — Multi-Agent Orchestration (LangGraph)

> Goal: Build the brain — a graph of cooperating agents that plan, retrieve, and answer.

### 4.1 Learn LangGraph Basics
- [x] **4.1.1** Read the LangGraph "Quick Start" guide (~30 min)
- [x] **4.1.2** Understand: nodes, edges, state, conditional routing

### 4.2 Define Shared State
- [x] **4.2.1** Create `agents/state.py`
- [x] **4.2.2** Define `AgentState` TypedDict with fields:
  - `user_query: str` — raw transcribed text
  - `intent: dict` — extracted constraints (budget, material, category, etc.)
  - `plan: dict` — which sources to call and why
  - `rag_results: list` — results from `rag.search`
  - `web_results: list` — results from `web.search`
  - `final_answer: str` — synthesized recommendation text
  - `citations: list` — doc IDs and URLs
  - `safety_flags: list` — any flagged content

### 4.3 Build Agent 1 — Router / Intent Classifier
- [x] **4.3.1** Create `agents/router.py`
- [x] **4.3.2** Prompt the LLM to extract: task type, budget, material, brand preference, safety flags
- [x] **4.3.3** Output structured JSON (use LLM function/tool calling or strict JSON mode)
- [x] **4.3.4** If safety flag detected (e.g., dangerous chemical advice), route to a safe refusal node
- [x] **4.3.5** Test with sample queries

### 4.4 Build Agent 2 — Planner
- [x] **4.4.1** Create `agents/planner.py`
- [x] **4.4.2** Based on intent, decide: use `rag.search` only, or also call `web.search`
  - Rule: if query contains "current price", "available now", "latest" → call both
  - Rule: otherwise → `rag.search` first; call `web.search` only if no strong match
- [x] **4.4.3** Output a plan dict (tools to call, retrieval fields, comparison criteria)
- [x] **4.4.4** Log the plan for transparency

### 4.5 Build Agent 3 — Retriever
- [x] **4.5.1** Create `agents/retriever.py`
- [x] **4.5.2** Call `rag.search` MCP tool with the query + extracted constraints
- [x] **4.5.3** Conditionally call `web.search` MCP tool if the plan requires it
- [x] **4.5.4** Reconcile results: match by SKU/brand/title similarity; flag price discrepancies > 20%
- [x] **4.5.5** Store results in state

### 4.6 Build Agent 4 — Answerer / Critic
- [x] **4.6.1** Create `agents/answerer.py`
- [x] **4.6.2** Prompt the LLM to synthesize a ≤15-second spoken answer from retrieved results
- [x] **4.6.3** Require the LLM to cite doc IDs and URLs in its answer
- [x] **4.6.4** Add a critic pass: verify the answer only uses facts from retrieved context (no hallucination)
- [x] **4.6.5** If answer fails grounding check, re-prompt once with stricter instructions

### 4.7 Assemble the Graph
- [x] **4.7.1** Create `agents/graph.py`
- [x] **4.7.2** Add nodes: `router → planner → retriever → answerer`
- [x] **4.7.3** Add a conditional edge from `router`: if safety flag → `safe_refusal` node; else → `planner`
- [x] **4.7.4** Compile the graph with `StateGraph.compile()`
- [x] **4.7.5** Run an end-to-end test with a text query (no audio yet)
- [x] **4.7.6** Log the full graph execution trace to `logs/graph.log`

### 4.8 LLM Configuration
- [x] **4.8.1** Create `config.py` or use `.env` to set `LLM_PROVIDER` and `LLM_MODEL`
- [x] **4.8.2** Wrap LLM initialization so swapping provider (OpenAI → Claude → Gemini) requires only an env var change
- [x] **4.8.3** Log all prompts and system messages to `logs/prompts.log`

---

## Phase 5 — Speech Recognition (ASR)

> Goal: Convert the user's voice into text that the graph can process.

### 5.1 Set Up Whisper
- [x] **5.1.1** Install `openai-whisper` (local) or configure OpenAI Whisper API
- [x] **5.1.2** Create `speech/asr.py` with a `transcribe(audio_file_path) -> str` function
- [x] **5.1.3** Test with a sample `.wav` file
- [x] **5.1.4** Handle common errors: file not found, empty audio, unsupported format

### 5.2 Fragment-Based Recording
- [x] **5.2.1** Create `speech/recorder.py` using `sounddevice` or `pyaudio`
- [x] **5.2.2** Implement: press Enter to start, press Enter again to stop → saves to `temp/recording.wav`
- [x] **5.2.3** Test recording → transcription pipeline end-to-end

---

## Phase 6 — Text-to-Speech (TTS)

> Goal: Convert the AI's text answer into a natural-sounding voice response.

### 6.1 Choose TTS Provider
- [x] **6.1.1** Pick one: OpenAI TTS (`tts-1`), ElevenLabs, Azure Speech, or Coqui (open-source local)
- [x] **6.1.2** Add API key to `.env`

### 6.2 Implement TTS
- [x] **6.2.1** Create `speech/tts.py` with a `speak(text: str) -> bytes` function
- [x] **6.2.2** Save output to `temp/response.mp3`
- [x] **6.2.3** Implement `play_audio(file_path)` using macOS `afplay` (built-in, no install)
- [x] **6.2.4** Test with a sample sentence

### 6.3 Connect to Graph Output
- [x] **6.3.1** After the graph returns `final_answer`, pass it to `speak()`
- [x] **6.3.2** Play the audio automatically
- [x] **6.3.3** Ensure answer is ≤15 seconds (enforced via LLM prompt)

---

## Phase 7 — User Interface

> Goal: Give the user a visual interface to interact with the assistant.

### 7.1 Set Up Streamlit
- [x] **7.1.1** Install `streamlit`
- [x] **7.1.2** Create `app.py` with a basic Streamlit page
- [x] **7.1.3** Run `streamlit run app.py` and verify it loads

### 7.2 Build the UI Components
- [x] **7.2.1** **Mic input**: Native `st.audio_input()` recorder with dark/light theme support
- [x] **7.2.2** **Transcript panel**: Displays transcribed text after recording
- [x] **7.2.3** **Agent step log**: Live `st.status()` progress (Router → Planner → Retriever → Answerer)
- [x] **7.2.4** **Product cards**: Top-5 products with title, category, price, rating, match score
- [x] **7.2.5** **Citations**: Private catalog doc IDs + live web URLs shown below products
- [x] **7.2.6** **TTS auto-play**: Audio response plays automatically after answer is generated

### 7.3 Wire Everything Together
- [x] **7.3.1** Record → auto-transcribe → auto-run LangGraph pipeline → display results → play TTS
- [x] **7.3.2** Live status updates via `st.status()` while pipeline runs
- [x] **7.3.3** Unsafe and off-topic queries short-circuit with a clear refusal message
- [x] **7.3.4** Full golden-path tested: voice in → voice out + visual results

---

## Phase 8 — Safety & Quality

> Goal: Make the assistant trustworthy and safe.

- [x] **8.1** Domain allowlist: refuse queries unrelated to product search
- [x] **8.2** Unsafe advice filter: detect and refuse dangerous chemical usage advice
- [x] **8.3** Hallucination check: ensure final answer only references products in retrieved results
- [x] **8.4** Never log API keys or secrets; redact from log files
- [x] **8.5** Respect robots.txt / ToS for the web search API being used
- [x] **8.6** Limit the web search cache to avoid serving stale price/availability data

---

## Phase 9 — Documentation & Delivery

> Goal: Make the project understandable and runnable by anyone (including yourself, 6 months later).

- [ ] **9.1** Write `README.md` covering: project overview, architecture diagram (text is fine), setup steps, how to run
- [ ] **9.2** Document the LangGraph design: each node, edges, and conditional routing logic
- [ ] **9.3** Document MCP server: tool names, JSON schemas for input/output, transport used
- [ ] **9.4** Document data preprocessing: what was kept, what was cleaned, how embeddings were built
- [ ] **9.5** Add safety notes: what the system refuses and why
- [ ] **9.6** Write a `run.sh` or Makefile with commands: `build-index`, `start-mcp`, `start-app`
- [ ] **9.7** Final end-to-end demo test: record the example query from the spec ("eco-friendly stainless-steel cleaner under $15") and verify voice output matches expected behavior

---

## Suggested File Structure (Reference)

```
Voice-to-Voice AI Assistant/
├── .env.example
├── .gitignore
├── requirements.txt
├── config.py
├── app.py                    # Streamlit UI
├── agents/
│   ├── state.py
│   ├── router.py
│   ├── planner.py
│   ├── retriever.py
│   ├── answerer.py
│   └── graph.py
├── mcp_server/
│   └── server.py
├── speech/
│   ├── asr.py
│   ├── recorder.py
│   └── tts.py
├── scripts/
│   └── build_index.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── index/
├── notebooks/
│   └── 01_explore_data.ipynb
├── logs/
│   ├── mcp.log
│   ├── graph.log
│   └── prompts.log
├── temp/                     # Temporary audio files (gitignored)
└── README.md
```

---

## Learning Order Summary

| Phase | What you learn |
|-------|---------------|
| 0 | Python project setup, env management |
| 1 | Data cleaning, Pandas/Parquet |
| 2 | Embeddings, vector databases (RAG fundamentals) |
| 3 | MCP protocol, building tool servers |
| 4 | LangGraph, multi-agent orchestration, prompt engineering |
| 5 | ASR with Whisper |
| 6 | TTS integration |
| 7 | Streamlit UI |
| 8 | AI safety patterns |
| 9 | Documentation and delivery |

**Start with Phase 0, then Phase 1. Do not skip ahead.**
