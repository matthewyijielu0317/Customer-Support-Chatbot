from typing import Dict, Any, List

from src.graph.state import RAGState, Citation
from src.retrievers.pinecone_retriever import PineconeRetriever
from src.config.settings import settings


_retriever = PineconeRetriever(index_name=settings.pinecone_index, namespace="kb")


def _doc_to_state_dict(doc) -> Dict[str, Any]:
    md = doc.metadata or {}
    return {
        "text": doc.page_content,
        "source": md.get("source"),
        "title": md.get("title"),
        "page": md.get("page"),
        "score": md.get("score"),
    }


def retrieve_docs_node(state: RAGState) -> RAGState:
    """Retrieve top-3 relevant policy chunks from Pinecone into state.

    Honors `state.should_retrieve` to optionally skip retrieval.
    """
    if not state.should_retrieve:
        state.docs = []
        state.citations = []
        return state

    results = _retriever.retrieve(query=state.query, k=3)
    state.docs = [_doc_to_state_dict(d) for d in results]

    citations: List[Citation] = []
    for d in state.docs:
        citations.append(
            Citation(
                source=str(d.get("source") or ""),
                title=(d.get("title") or None),
                page=(int(d.get("page")) if d.get("page") is not None else None),
                score=(float(d.get("score")) if d.get("score") is not None else None),
            )
        )
    state.citations = citations
    return state


