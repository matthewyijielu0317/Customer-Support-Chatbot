from typing import List, Tuple


class Reranker:
    """Placeholder cross-encoder reranker."""

    def __init__(self, model_name: str = "bge-reranker-v2-m3"):
        self.model_name = model_name

    def rerank(self, query: str, passages: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        # TODO: implement using sentence-transformers CrossEncoder
        return [(p, 1.0) for p in passages[:top_k]]


