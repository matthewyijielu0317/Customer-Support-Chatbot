from typing import List

from src.graph.state import RAGState, Citation
from src.retrievers.reranker import Reranker

_reranker = Reranker()


def rerank_filter_node(state: RAGState) -> RAGState:
    # If nothing to rerank, return early
    docs = state.docs or []
    if not docs:
        return state

    # Run reranker to produce new order with `rerank_score`
    reranked_docs = _reranker.rerank(query=state.query, docs=docs, top_k=None)

    # Rebuild citations list to match new order
    new_citations: List[Citation] = []
    for d in reranked_docs:
        new_citations.append(
            Citation(
                source=str(d.get("source") or ""),
                title=(d.get("title") or None),
                page=(int(d.get("page")) if d.get("page") is not None else None),
                score=(float(d.get("score")) if d.get("score") is not None else None),
            )
        )

    state.docs = reranked_docs
    state.citations = new_citations
    return state


