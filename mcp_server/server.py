"""
Phase 3 — MCP Server
Exposes two tools to LangGraph agents:
  - rag.search  → searches the private ChromaDB product catalog
  - web.search  → calls the Brave Search API for live results

Run with:  python mcp_server/server.py
Transport: stdio (JSON over stdin/stdout)
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

import chromadb
from cachetools import TTLCache
from openai import OpenAI
from tavily import TavilyClient
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/mcp.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log(tool: str, input_data: dict, output_data: dict | str):
    logging.info(f"TOOL={tool} | INPUT={json.dumps(input_data)} | OUTPUT={json.dumps(output_data) if isinstance(output_data, dict) else str(output_data)[:300]}")


# ── Shared clients (loaded once at startup) ───────────────────────────────────
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

chroma_client = chromadb.PersistentClient(path="data/index")
collection = chroma_client.get_collection("products")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
web_cache: TTLCache = TTLCache(maxsize=128, ttl=180)  # 3-minute cache


# ── Tool 1: rag.search ────────────────────────────────────────────────────────
def rag_search(query: str, max_price: float | None = None, category: str | None = None, top_k: int = 5) -> list[dict]:
    """Query the private ChromaDB product catalog."""
    embedding = openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=[query]
    ).data[0].embedding

    # Build metadata filter
    filters = []
    if max_price is not None:
        filters.append({"price": {"$lte": max_price}})
    if category:
        filters.append({"category": {"$eq": category}})

    where = None
    if len(filters) == 1:
        where = filters[0]
    elif len(filters) > 1:
        where = {"$and": filters}

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["metadatas", "distances", "documents"],
    )

    output = []
    for meta, dist, doc in zip(
        results["metadatas"][0],
        results["distances"][0],
        results["documents"][0],
    ):
        output.append({
            "doc_id":       meta.get("id", ""),
            "title":        meta.get("title", ""),
            "brand":        meta.get("brand", ""),
            "category":     meta.get("category", ""),
            "price":        meta.get("price", 0),
            "rating":       meta.get("rating", -1),
            "availability": meta.get("availability", ""),
            "source":       "private_catalog",
            "match_score":  round(1 - dist, 3),
        })
    return output


# ── Tool 2: web.search ────────────────────────────────────────────────────────
def web_search(query: str, top_k: int = 5) -> list[dict]:
    """Search the web via Tavily API for live product results."""
    if not TAVILY_API_KEY or TAVILY_API_KEY == "tvly-your_tavily_api_key_here":
        return [{"error": "TAVILY_API_KEY not configured", "source": "web"}]

    cache_key = f"{query}:{top_k}"
    if cache_key in web_cache:
        logging.info(f"web.search cache hit for: {query}")
        return web_cache[cache_key]

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = client.search(query=query, max_results=top_k)

        results = []
        for item in response.get("results", [])[:top_k]:
            results.append({
                "title":   item.get("title", ""),
                "url":     item.get("url", ""),
                "snippet": item.get("content", ""),
                "source":  "web",
            })

        web_cache[cache_key] = results
        return results

    except Exception as e:
        return [{"error": str(e), "source": "web"}]


# ── MCP Server ────────────────────────────────────────────────────────────────
server = Server("voice-assistant-tools")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Tool discovery — agents call this to learn what tools are available."""
    return [
        types.Tool(
            name="rag.search",
            description="Search the private product catalog using semantic similarity. Returns grounded results with doc_id for citations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query":     {"type": "string",  "description": "Natural language search query"},
                    "max_price": {"type": "number",  "description": "Maximum price filter (optional)"},
                    "category":  {"type": "string",  "description": "Category filter e.g. 'Home', 'Electronics' (optional)"},
                    "top_k":     {"type": "integer", "description": "Number of results to return (default 5)"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="web.search",
            description="Search the live web via Brave Search API. Use for current prices, availability, or products not in the private catalog.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string",  "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Number of results (default 5)"},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Route a tool call to the right function and return results as JSON."""
    if name == "rag.search":
        result = rag_search(
            query=arguments["query"],
            max_price=arguments.get("max_price"),
            category=arguments.get("category"),
            top_k=arguments.get("top_k", 5),
        )
        log("rag.search", arguments, result)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "web.search":
        result = web_search(
            query=arguments["query"],
            top_k=arguments.get("top_k", 5),
        )
        log("web.search", arguments, result)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
