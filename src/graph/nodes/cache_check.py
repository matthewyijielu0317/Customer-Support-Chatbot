from __future__ import annotations

from typing import Any, Optional

from src.cache.pinecone_semantic import PineconeSemanticCache
from src.graph.state import RAGState, Citation


def _to_citations(raw: Optional[Any]) -> list[Citation]:
    citations: list[Citation] = []
    if not raw:
        return citations
    for item in raw:
        if isinstance(item, dict):
            citations.append(
                Citation(
                    source=str(item.get("source", "")),
                    title=item.get("title"),
                    page=item.get("page"),
                    score=item.get("score"),
                )
            )
        elif isinstance(item, Citation):
            citations.append(item)
    return citations


def cache_check_node(state: RAGState) -> RAGState:
    cache: Optional[PineconeSemanticCache] = getattr(state, "semantic_cache", None)
    query = (state.query or "").strip()

    state.cache_hit = False
    state.should_cache = False

    if not cache or not query:
        state.cache_key = None
        return state

    doc_only = bool(state.should_retrieve_docs) and not bool(state.should_retrieve_sql)
    if not doc_only:
        state.cache_key = None
        return state

    cache_key = PineconeSemanticCache.build_key(query)
    state.cache_key = cache_key

    entry = cache.similar(query)
    if entry:
        state.cache_hit = True
        state.should_retrieve = False
        state.answer = entry.get("answer") or ""
        state.citations = _to_citations(entry.get("citations"))
        trace = entry.get("trace_id")
        if trace:
            state.trace_id = trace
        return state

    state.should_cache = True
    return state
