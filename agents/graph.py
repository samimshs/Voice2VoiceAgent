"""
Phase 4, Task 4.7 — Assemble the LangGraph.

Graph structure:
  user_query
      ↓
   [router]  ──── safety flag? ────→ [safe_refusal] → END
      ↓ (no flag)
   [planner]
      ↓
  [retriever]
      ↓
  [answerer]
      ↓
     END
"""
from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.router import router_node
from agents.planner import planner_node
from agents.retriever import retriever_node
from agents.answerer import answerer_node


def safe_refusal_node(state: AgentState) -> dict:
    if state.get("safety_flags"):
        msg = (
            "I'm sorry, I can't help with that — it looks like the request involves "
            "unsafe or harmful content. I'm only able to help you find and compare products."
        )
    else:
        msg = (
            "I'm a product search assistant, so I can only help you find and compare products. "
            "Try something like: \"find me wireless headphones under $50\" "
            "or \"show me eco-friendly cleaning products\"."
        )
    return {"final_answer": msg, "citations": []}


def route_after_router(state: AgentState) -> str:
    if state.get("safety_flags"):
        return "safe_refusal"
    if state.get("intent", {}).get("task_type") != "product_search":
        return "safe_refusal"
    return "planner"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("router",       router_node)
    graph.add_node("planner",      planner_node)
    graph.add_node("retriever",    retriever_node)
    graph.add_node("answerer",     answerer_node)
    graph.add_node("safe_refusal", safe_refusal_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges("router", route_after_router, {
        "planner":      "planner",
        "safe_refusal": "safe_refusal",
    })
    graph.add_edge("planner",      "retriever")
    graph.add_edge("retriever",    "answerer")
    graph.add_edge("answerer",     END)
    graph.add_edge("safe_refusal", END)

    return graph.compile()
