from src.graph.state import RAGState


def generate_node(state: RAGState) -> RAGState:
    # Placeholder: basic answer using intent.
    intent = state.intent or "policy_qna"
    state.answer = state.answer or f"[Template] Intent: {intent}. Implement generator next."
    return state


