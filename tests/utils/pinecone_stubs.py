from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List


class FakeEmbeddingsAPI:
    def create(self, model: str, input: List[str]):
        text = (input[0] if input else "").strip().lower()
        value = float(len(text))
        return SimpleNamespace(data=[SimpleNamespace(embedding=[value])])


class FakeOpenAI:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsAPI()


class FakePineconeIndex:
    def __init__(self) -> None:
        self.storage: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def upsert(self, *, namespace: str, vectors: List[Dict[str, Any]]) -> None:
        ns = self.storage.setdefault(namespace, {})
        for vector in vectors:
            ns[vector["id"]] = {
                "values": list(vector.get("values", [])),
                "metadata": dict(vector.get("metadata", {})),
            }

    def query(
        self,
        *,
        namespace: str,
        vector: List[float],
        top_k: int = 3,
        include_metadata: bool = True,
        filter: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        matches: List[Dict[str, Any]] = []
        ns = self.storage.get(namespace, {})
        for vector_id, payload in ns.items():
            metadata = payload.get("metadata", {})
            if filter:
                target = filter.get("user_id", {}).get("$eq")
                if target is not None and metadata.get("user_id") != target:
                    continue
            score = 1.0 if list(vector) == payload.get("values", []) else 0.0
            if score <= 0.0:
                continue
            matches.append({"id": vector_id, "score": score, "metadata": metadata})

        matches.sort(key=lambda m: m["score"], reverse=True)
        return {"matches": matches[:top_k]}

    def delete(self, *, ids: List[str], namespace: str) -> None:
        ns = self.storage.get(namespace)
        if not ns:
            return
        for vector_id in ids:
            ns.pop(vector_id, None)


class FakePineconeClient:
    def __init__(self) -> None:
        self.index = FakePineconeIndex()

    def Index(self, _: str) -> FakePineconeIndex:
        return self.index
