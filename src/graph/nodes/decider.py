from src.graph.state import RAGState


def decider_node(state: RAGState) -> RAGState:
    # Placeholder: never escalate in template.
    state.should_escalate = False
    return state


