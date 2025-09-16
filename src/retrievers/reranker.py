from typing import Any, Dict, List

try:
    from sentence_transformers import CrossEncoder  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "sentence-transformers is required for reranking. Please install with: pip install sentence-transformers torch"
    ) from exc


DEFAULT_CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    """Reranker using SentenceTransformers CrossEncoder only.

    Adds `rerank_score` to each doc dict and returns reordered docs.
    """

    def __init__(self, cross_encoder_model: str = DEFAULT_CE_MODEL):
        try:
            self._cross_encoder = CrossEncoder(cross_encoder_model)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to load CrossEncoder model '{cross_encoder_model}': {exc}") from exc

    def rerank(self, query: str, docs: List[Dict[str, Any]], top_k: int | None = None) -> List[Dict[str, Any]]:
        if not docs:
            return []

        pairs = [(query, (d.get("text") or "")) for d in docs]
        scores = self._cross_encoder.predict(pairs, show_progress_bar=False)
        indexed_scores: List[tuple[int, float]] = [(i, float(s)) for i, s in enumerate(scores)]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        if top_k is None:
            top_k = len(indexed_scores)
        keep = indexed_scores[:top_k]

        reranked: List[Dict[str, Any]] = []
        for idx, s in keep:
            d = dict(docs[idx])
            d["rerank_score"] = s
            reranked.append(d)
        return reranked


