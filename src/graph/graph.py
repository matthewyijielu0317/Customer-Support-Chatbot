from langgraph.graph import StateGraph, END

from src.graph.state import RAGState


def build_graph():
    """Build a placeholder LangGraph with minimal nodes to be filled later."""
    builder = StateGraph(RAGState)

    # Minimal stubs (wire real implementations later)
    def router_node(state: RAGState) -> RAGState:
        state.intent = state.intent or "policy_qna"
        return state

    def generate_node(state: RAGState) -> RAGState:
        state.answer = state.answer or "Graph template online. Implement nodes next."
        return state

    builder.add_node("router", router_node)
    builder.add_node("generate", generate_node)

    builder.set_entry_point("router")
    builder.add_edge("router", "generate")
    builder.add_edge("generate", END)

    return builder.compile()


