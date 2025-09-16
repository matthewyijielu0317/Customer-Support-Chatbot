from langgraph.graph import StateGraph, END

from src.graph.state import RAGState
from src.graph.nodes.router import router_node
from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.generate import generate_node
from src.graph.nodes.groundedness import groundedness_node


def build_graph():
    """Build RAG graph with conditional routing.

    router -> generate (if chitchat)
    router -> retrieve_docs -> generate (otherwise)
    -> END
    """
    builder = StateGraph(RAGState)

    builder.add_node("router", router_node)
    builder.add_node("retrieve_docs", retrieve_docs_node)
    builder.add_node("generate", generate_node)
    builder.add_node("groundedness", groundedness_node)

    builder.set_entry_point("router")
    
    # Conditional edge based on router output
    def route_after_router(state: RAGState) -> str:
        if getattr(state, "intent", None) == "chitchat" or not getattr(state, "should_retrieve", True):
            return "generate"
        return "retrieve_docs"

    builder.add_conditional_edges(
        "router",
        route_after_router,
        {
            "generate": "generate",
            "retrieve_docs": "retrieve_docs",
        },
    )

    builder.add_edge("retrieve_docs", "generate")

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


