from typing import Dict, Any, List, Optional

from src.graph.state import RAGState, Citation
from src.config.settings import settings
from src.retrievers.pinecone_retriever import PineconeRetriever
from src.retrievers.reranker import Reranker
import os


_retriever: Optional[PineconeRetriever] = None
_reranker: Optional[Reranker] = None


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


def _get_reranker() -> Optional[Reranker]:
    """Get reranker instance, creating it if needed."""
    global _reranker
    if _reranker is None:
        try:
            _reranker = Reranker()
        except Exception:
            # If reranker fails to load, continue without it
            _reranker = None
            return None
    return _reranker


def _doc_to_state_dict(doc) -> Dict[str, Any]:
    """Convert document to state dictionary format."""
    md = doc.metadata or {}
    return {
        "text": doc.page_content,
        "source": md.get("source"),
        "title": md.get("title"),
        "page": md.get("page"),
        "score": md.get("score"),
    }


def _dict_to_rerank_format(doc_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert state dict to reranker format."""
    return {
        "text": doc_dict.get("text", ""),
        "source": doc_dict.get("source"),
        "title": doc_dict.get("title"),
        "page": doc_dict.get("page"),
        "score": doc_dict.get("score"),
    }


def retrieve_docs_node(state: RAGState) -> RAGState:
    """Retrieve and rerank top relevant policy chunks from Pinecone."""
    if not state.should_retrieve_docs:
        state.docs = []
        state.citations = []
        return state

    retr = _get_retriever()
    if retr is None:
        # No-op when vector service or API keys are not configured
        state.docs = []
        state.citations = []
        return state

    # Retrieve more documents for reranking (e.g., 10) then rerank to top 3
    initial_k = 10
    results = retr.retrieve(query=state.query, k=initial_k)
    docs = [_doc_to_state_dict(d) for d in results]
    
    # Apply reranking if available
    reranker = _get_reranker()
    if reranker is not None and docs:
        try:
            # Convert to reranker format and rerank
            rerank_docs = [_dict_to_rerank_format(d) for d in docs]
            reranked = reranker.rerank(query=state.query, docs=rerank_docs, top_k=3)
            state.docs = reranked
        except Exception:
            # Fall back to original results if reranking fails
            state.docs = docs[:3]
    else:
        # No reranker available, use top 3 from retrieval
        state.docs = docs[:3]

    # Build citations from final documents
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

