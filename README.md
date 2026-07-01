# Voice-to-Voice AI Product Assistant

A multi-agent AI system that lets you **speak a product query** and receive a **spoken recommendation** — backed by a private product catalog and live web search.

Built as a learning project to explore LangGraph, MCP, RAG, Whisper, and TTS end-to-end.

---

## How it works

```
🎙 Voice input
     │
     ▼
 [Whisper ASR]  ──── transcribes speech to text
     │
     ▼
 [Router agent]  ──── classifies intent, extracts budget/category/brand
     │                 routes unsafe or off-topic queries to safe refusal
     ▼
 [Planner agent] ──── decides which tools to call (catalog only vs. catalog + web)
     │
     ▼
 [Retriever agent] ── calls MCP tools:
     │                 • rag.search  → ChromaDB vector search (private catalog)
     │                 • web.search  → Tavily live web results (optional)
     ▼
 [Answerer agent] ── synthesizes a ≤15-second spoken answer, cites sources,
     │                 runs a critic pass to prevent hallucination
     ▼
 [OpenAI TTS]  ──── converts answer text to speech (nova voice)
     │
     ▼
🔊 Voice output + visual product cards
```

---

## Quick start

### 1 — Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11 or 3.12 | 3.13 works but Kaggle download step requires the pinned version |
| OpenAI API key | Covers LLM (gpt-4o-mini), Whisper ASR, TTS, and embeddings |
| Tavily API key | Free tier: 1,000 searches/month — [tavily.com](https://tavily.com) |
| macOS | Audio playback uses built-in `afplay`; Linux/Windows users can swap to `playsound` in `speech/tts.py` |

### 2 — Clone and set up

```bash
git clone https://github.com/samimshs/Voice2VoiceAgent.git
cd Voice2VoiceAgent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3 — Configure API keys

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

All other fields have sensible defaults and can be left as-is.

### 4 — Run the app

The product catalog (ChromaDB index) is already included in the repo — no rebuild needed.

```bash
streamlit run app.py
# or use the helper script:
./run.sh app
```

Open [http://localhost:8501](http://localhost:8501), click the mic, speak your query, and the assistant will respond by voice.

---

## Example queries to try

| Type | Query |
|---|---|
| Budget search | *"find me headphones under 50 dollars"* |
| Material filter | *"show me stainless steel water bottles"* |
| Live prices | *"what are the latest prices for wireless earbuds"* |
| Off-topic (refused) | *"what is the capital of France"* |
| Unsafe (refused) | *"how do I mix bleach and ammonia"* |

---

## Architecture

### LangGraph — agent nodes and routing

```
[router] ──── safety flag or off-topic? ──→ [safe_refusal] → END
   │
   │ product_search intent
   ▼
[planner] ──→ [retriever] ──→ [answerer] → END
```

| Node | File | What it does |
|---|---|---|
| **Router** | `agents/router.py` | Classifies intent; extracts budget, category, material, brand; detects unsafe/off-topic queries |
| **Planner** | `agents/planner.py` | Decides whether to call `rag.search` only or also `web.search` |
| **Retriever** | `agents/retriever.py` | Calls MCP tools; reconciles catalog vs. web results; flags price discrepancies >20% |
| **Answerer** | `agents/answerer.py` | Synthesizes a ≤15-second grounded answer; runs a critic pass to check for hallucination |
| **Safe refusal** | `agents/graph.py` | Returns a helpful refusal message for unsafe or off-topic queries |

### MCP server — two tools

The MCP server (`mcp_server/server.py`) exposes two tools over stdio transport:

**`rag.search`**
```json
Input:  { "query": "string", "max_price": 50.0, "category": "Electronics", "top_k": 5 }
Output: [{ "title", "price", "rating", "brand", "category", "match_score" }, ...]
```
Queries the ChromaDB vector index using OpenAI embeddings (`text-embedding-3-small`).
Supports metadata filters for price and category.

**`web.search`**
```json
Input:  { "query": "string", "top_k": 3 }
Output: [{ "title", "url", "snippet", "price", "availability" }, ...]
```
Calls the Tavily Search API. Results are cached for 180 seconds to avoid redundant requests.

---

## Safety system

| Check | Where | Behaviour |
|---|---|---|
| Off-topic query | Router → graph routing | Detected by `task_type != "product_search"`; routes to safe refusal |
| Unsafe content | Router → graph routing | Detected by `safety_flags` list (dangerous chemical mixing, weapon instructions, etc.); routes to safe refusal |
| Hallucination | Answerer critic pass | Answer is checked to only reference products from retrieved context; re-prompted once if it fails |
| Stale web data | MCP server TTL cache | Web search results expire after 180 seconds |
| Secret leakage | `.gitignore` + logging | `.env` is never committed; logging statements never output API keys |

---

## Switching LLM providers

Change two lines in `.env`:

```bash
# Use Claude instead of GPT
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...

# Use Gemini instead of GPT
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=...
```

Then uncomment the matching line in `requirements.txt` and reinstall.

---

## Rebuilding the product index

The index is pre-built and included. Only run this if you change the dataset or embedding model:

```bash
./run.sh build-index
# or:
python scripts/build_index.py
```

This reads `data/processed/products.parquet`, generates embeddings via the OpenAI API (~1,000 products, costs < $0.01), and writes the ChromaDB index to `data/index/`.

---

## File structure

```
Voice2VoiceAgent/
├── app.py                    # Streamlit UI — mic input, live status, product cards
├── config.py                 # LLM provider switching, env var loading
├── requirements.txt
├── run.sh                    # Helper: setup | build-index | app
├── .env.example              # Template for API keys (copy → .env, never commit .env)
├── .streamlit/
│   └── config.toml           # Light theme, accent colour
├── agents/
│   ├── state.py              # AgentState TypedDict (shared across all nodes)
│   ├── router.py             # Intent classification + safety/off-topic detection
│   ├── planner.py            # Tool selection strategy
│   ├── retriever.py          # Calls MCP tools, reconciles results
│   ├── answerer.py           # Synthesizes answer + critic hallucination check
│   └── graph.py              # LangGraph assembly + safe_refusal node
├── mcp_server/
│   └── server.py             # MCP server: rag.search + web.search tools
├── speech/
│   ├── asr.py                # Whisper API transcription
│   ├── tts.py                # OpenAI TTS (nova voice) + afplay playback
│   └── recorder.py           # Terminal microphone recorder (used in tests)
├── scripts/
│   └── build_index.py        # Embeds products.parquet → ChromaDB index
├── data/
│   ├── processed/
│   │   └── products.parquet  # 1,000 cleaned product rows (committed)
│   └── index/                # ChromaDB vector index (committed, pre-built)
├── notebooks/
│   ├── 01_explore_data.ipynb
│   └── 02_clean_data.ipynb
└── logs/                     # Runtime logs (gitignored)
```

---

## Dataset

Source: [darwish1337/ecommerce](https://www.kaggle.com/datasets/darwish1337/ecommerce) on Kaggle — 1,000 product rows with title, brand, category, price, rating, and description. Cleaned and normalized in `notebooks/02_clean_data.ipynb`.
