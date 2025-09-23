from langgraph.graph import StateGraph, END

from src.graph.state import RAGState
from src.graph.nodes.router import router_node
from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.retrieve_sql import retrieve_sql_node
from src.graph.nodes.generate import generate_node
from src.graph.nodes.groundedness import groundedness_node
from src.graph.nodes.cache_check import cache_check_node


def build_graph():
    """Build RAG graph with conditional routing.

    router -> cache_check -> retrieve_sql? -> retrieve_docs? -> generate -> groundedness
    """
    builder = StateGraph(RAGState)

    builder.add_node("router", router_node)
    builder.add_node("cache_check", cache_check_node)
    builder.add_node("retrieve_sql", retrieve_sql_node)
    builder.add_node("retrieve_docs", retrieve_docs_node)
    builder.add_node("generate", generate_node)
    builder.add_node("groundedness", groundedness_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "cache_check")

    def route_after_cache(state: RAGState) -> str:
        if getattr(state, "cache_hit", False):
            return "END"
        if getattr(state, "should_retrieve_sql", False):
            return "retrieve_sql"
        if getattr(state, "should_retrieve_docs", False):
            return "retrieve_docs"
        return "generate"

    builder.add_conditional_edges(
        "cache_check",
        route_after_cache,
        {
            "generate": "generate",
            "retrieve_sql": "retrieve_sql",
            "retrieve_docs": "retrieve_docs",
            "END": END,
        },
    )

    def route_after_sql(state: RAGState) -> str:
        if getattr(state, "should_retrieve_docs", False):
            return "retrieve_docs"
        return "generate"

    builder.add_conditional_edges(
        "retrieve_sql",
        route_after_sql,
        {
            "retrieve_docs": "retrieve_docs",
            "generate": "generate",
        },
    )

    builder.add_edge("retrieve_docs", "generate")

    # After generate, if we retrieved, run groundedness; else end
    def route_after_generate(state: RAGState) -> str:
        if getattr(state, "docs", None):
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
