"""Document reranking using cross-encoder models for improved retrieval quality."""

from typing import Any, Dict, List

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "sentence-transformers is required for reranking. Please install with: pip install sentence-transformers torch"
    ) from exc


DEFAULT_CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """Document reranker using SentenceTransformers CrossEncoder.
    
    Reranks retrieved documents based on query-document relevance scores.
    Adds `rerank_score` to each document and returns reordered results.
    """

    def __init__(self, cross_encoder_model: str = DEFAULT_CE_MODEL):
        """Initialize the reranker with a cross-encoder model.
        
        Args:
            cross_encoder_model: HuggingFace model name for cross-encoding
        """
        try:
            self._cross_encoder = CrossEncoder(cross_encoder_model)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to load CrossEncoder model '{cross_encoder_model}': {exc}") from exc

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        """Rerank documents based on query-document relevance.
        
        Args:
            query: The search query
            docs: List of document dictionaries with 'text' field
            top_k: Maximum number of documents to return (None for all)
            
        Returns:
            Reranked documents with added 'rerank_score' field
        """
        if not docs:
            return []

        # Create query-document pairs for cross-encoder
        pairs = [(query, (d.get("text") or "")) for d in docs]
        
        # Get relevance scores
        scores = self._cross_encoder.predict(pairs, show_progress_bar=False)
        
        # Create indexed scores and sort by relevance
        indexed_scores: List[tuple[int, float]] = [(i, float(s)) for i, s in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # Apply top_k limit
        if top_k is None:
            top_k = len(indexed_scores)
        keep = indexed_scores[:top_k]

        # Build reranked results with scores
        reranked: List[Dict[str, Any]] = []
        for idx, score in keep:
            doc = dict(docs[idx])
            doc["rerank_score"] = score
            reranked.append(doc)
            
        return reranked
