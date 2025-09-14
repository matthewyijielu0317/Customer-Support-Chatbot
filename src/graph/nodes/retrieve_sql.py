from src.graph.state import RAGState


def retrieve_sql_node(state: RAGState) -> RAGState:
    # Placeholder: attach empty sql_rows list
    state.sql_rows = []
    return state


