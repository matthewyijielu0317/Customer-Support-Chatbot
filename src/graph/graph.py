from langgraph.graph import StateGraph, END

from src.graph.state import RAGState
from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.generate import generate_node
from src.graph.nodes.rerank_filter import rerank_filter_node


def build_graph():
    """Build minimal RAG graph: router -> retrieve_docs -> rerank -> generate -> END."""
    builder = StateGraph(RAGState)

    # Simple router stub for now
    def router_node(state: RAGState) -> RAGState:
        state.intent = state.intent or "policy_qna"
        return state

    builder.add_node("router", router_node)
    builder.add_node("retrieve_docs", retrieve_docs_node)
    builder.add_node("rerank", rerank_filter_node)
    builder.add_node("generate", generate_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "retrieve_docs")
    builder.add_edge("retrieve_docs", "rerank")
    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


