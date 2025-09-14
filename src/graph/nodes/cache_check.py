from typing import Optional

from src.graph.state import RAGState


def cache_check_node(state: RAGState) -> RAGState:
    """Stub cache check: set cache_key and skip actual lookup for now."""
    state.cache_key = state.query.strip().lower()
    return state


