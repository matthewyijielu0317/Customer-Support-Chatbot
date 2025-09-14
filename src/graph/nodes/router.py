from src.graph.state import RAGState
from src.router.intent import classify_intent


def router_node(state: RAGState) -> RAGState:
    state.intent = classify_intent(state.query)
    return state


