from typing import Dict, Any, List, Optional

from src.graph.state import RAGState, Citation
from src.config.settings import settings
from src.retrievers.pinecone_retriever import PineconeRetriever
import os


_retriever: Optional[PineconeRetriever] = None


def _get_retriever() -> Optional[PineconeRetriever]:
    global _retriever
    # Require both Pinecone and OpenAI keys to be present
    pinecone_key = settings.pinecone_api_key or os.getenv("PINECONE_API_KEY", "")
    openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    if not pinecone_key or not openai_key:
        return None
    if _retriever is None:
        try:
            _retriever = PineconeRetriever(index_name=settings.pinecone_index, namespace="kb")
        except Exception:
            _retriever = None
            return None
    return _retriever


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

    retr = _get_retriever()
    if retr is None:
        # No-op when vector service or API keys are not configured
        state.docs = []
        state.citations = []
        return state

    results = retr.retrieve(query=state.query, k=3)
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


