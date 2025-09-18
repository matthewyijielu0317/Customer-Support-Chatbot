from langgraph.graph import StateGraph, END

from src.graph.state import RAGState
from src.graph.nodes.router import router_node
from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.retrieve_sql import retrieve_sql_node
from src.graph.nodes.parallel_retrieve import parallel_retrieve_node
from src.graph.nodes.generate import generate_node
from src.graph.nodes.groundedness import groundedness_node
from src.graph.nodes.cache_check import cache_check_node


def build_graph():
    """Build RAG graph with conditional routing.

    router -> generate (if chitchat)
    router -> retrieve_docs -> generate (otherwise)
    -> END
    """
    builder = StateGraph(RAGState)

    builder.add_node("router", router_node)
    builder.add_node("cache_check", cache_check_node)
    builder.add_node("retrieve_sql", retrieve_sql_node)
    builder.add_node("retrieve_docs", retrieve_docs_node)
    builder.add_node("parallel_retrieve", parallel_retrieve_node)
    builder.add_node("generate", generate_node)
    builder.add_node("groundedness", groundedness_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "cache_check")

    def route_after_cache(state: RAGState) -> str:
        if getattr(state, "cache_hit", False):
            return "END"
        if not getattr(state, "should_retrieve", True):
            return "generate"
        return "parallel_retrieve"

    builder.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "generate": "generate",
            "parallel_retrieve": "parallel_retrieve",
            "END": END,
        },
    )

    # Parallel retrieval collapses both retrieval steps into one
    builder.add_edge("parallel_retrieve", "generate")

    # After generate, if we retrieved, run groundedness; else end
    def route_after_generate(state: RAGState) -> str:
        if getattr(state, "should_retrieve", True):
            return "groundedness"
        return "END"

    builder.add_conditional_edges(
        "generate",
        route_after_generate,
        {
            "groundedness": "groundedness",
            "END": END,
        },
    )

    # Loop back to generate if not grounded (allow one retry)
    def route_after_grounded(state: RAGState) -> str:
        if getattr(state, "grounded", None) is False and getattr(state, "grounded_retry_count", 0) < 1:
            return "generate"
        return "END"

    builder.add_conditional_edges(
        "groundedness",
        route_after_grounded,
        {
            "generate": "generate",
            "END": END,
        },
    )

    return builder.compile()

