from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from src.graph.state import RAGState, Citation
from src.graph.nodes.retrieve_docs import retrieve_docs_node
from src.graph.nodes.retrieve_sql import retrieve_sql_node


def parallel_retrieve_node(state: RAGState) -> RAGState:
    """Run SQL and docs retrieval concurrently and merge results into state.

    - Honors `state.should_retrieve`.
    - Merges entities, sql_rows, docs, and citations without overwriting.
    """
    if not state.should_retrieve:
        state.docs = []
        state.sql_rows = []
        return state

    cache_ref = getattr(state, "semantic_cache", None)
    try:
        if cache_ref is not None:
            state.semantic_cache = None
    except AttributeError:
        cache_ref = None

    # Create deep copies so each worker can mutate independently
    docs_state: RAGState = state.copy(deep=True)
    sql_state: RAGState = state.copy(deep=True)

    def run_docs() -> RAGState:
        try:
            return retrieve_docs_node(docs_state)
        except Exception:
            # Swallow retrieval errors to allow pipeline to proceed
            docs_state.docs = []
            docs_state.citations = []
            return docs_state

    def run_sql() -> RAGState:
        try:
            return retrieve_sql_node(sql_state)
        except Exception:
            sql_state.sql_rows = []
            return sql_state

    run_docs_flag = bool(getattr(state, "should_retrieve_docs", True))
    run_sql_flag = bool(getattr(state, "should_retrieve_sql", True))

    docs_result: Optional[RAGState] = None
    sql_result: Optional[RAGState] = None

    # Both in parallel
    if run_docs_flag and run_sql_flag:
        with ThreadPoolExecutor(max_workers=2) as executor:
            docs_future = executor.submit(run_docs)
            sql_future = executor.submit(run_sql)
            docs_result = docs_future.result()
            sql_result = sql_future.result()
    # Only docs
    elif run_docs_flag:
        docs_result = run_docs()
    # Only SQL
    elif run_sql_flag:
        sql_result = run_sql()
    else:
        # Nothing to retrieve
        state.docs = []
        state.sql_rows = []
        return state

    # Restore cache reference on original state for downstream nodes
    if cache_ref is not None:
        state.semantic_cache = cache_ref

    # Merge entities (SQL extraction may add identifiers)
    if sql_result is not None and getattr(sql_result, "entities", None):
        try:
            state.entities.update(sql_result.entities or {})
        except Exception:
            pass

    # Adopt results
    state.sql_rows = (sql_result.sql_rows if sql_result is not None else []) or []
    state.docs = (docs_result.docs if docs_result is not None else []) or []

    # Merge citations (keep docs first, then DB facts)
    citations: List[Citation] = []
    if docs_result is not None and getattr(docs_result, "citations", None):
        citations.extend(docs_result.citations)
    if sql_result is not None and getattr(sql_result, "citations", None):
        citations.extend(sql_result.citations)
    state.citations = citations

    return state

