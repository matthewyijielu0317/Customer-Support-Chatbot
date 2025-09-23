from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

try:  # pragma: no cover - runtime dependency
    from pinecone import Pinecone
except ImportError:  # pragma: no cover - tests supply their own client
    Pinecone = None  # type: ignore

try:  # pragma: no cover - runtime dependency
    from openai import OpenAI
except ImportError:  # pragma: no cover - tests supply their own embedder
    OpenAI = None  # type: ignore

from src.config.settings import settings

EMBEDDING_MODEL = "text-embedding-3-small"


def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PineconeSemanticCache:
    """Semantic cache backed by a Pinecone namespace."""

    def __init__(
        self,
        index_name: str,
        *,
        namespace: str = "semantic_cache",
        similarity_threshold: float = 0.9,
        top_k: int = 3,
        pinecone_client: Optional[Any] = None,
        openai_client: Optional[Any] = None,
        embedding_model: str = EMBEDDING_MODEL,
    ) -> None:
        self.index_name = index_name
        self.namespace = namespace
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.embedding_model = embedding_model

        self._pc = pinecone_client or self._build_pinecone()
        self._index = self._pc.Index(index_name)
        self._openai = openai_client or self._build_openai()

    def _build_pinecone(self) -> Any:
        if Pinecone is None:
            raise RuntimeError("pinecone package is required for PineconeSemanticCache")
        api_key = settings.pinecone_api_key
        if not api_key:
            raise RuntimeError("PINECONE_API_KEY is required for semantic cache")
        return Pinecone(api_key=api_key)

    def _build_openai(self) -> Any:
        if OpenAI is None:
            raise RuntimeError("openai package is required for PineconeSemanticCache")
        api_key = settings.openai_api_key
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for semantic cache")
        return OpenAI(api_key=api_key)

    @staticmethod
    def build_key(query: str) -> str:
        base = _normalize(query)
        return hashlib.sha256(base.encode("utf-8", "ignore")).hexdigest()

    def _embed(self, text: str) -> Iterable[float]:
        response = self._openai.embeddings.create(model=self.embedding_model, input=[text])
        return response.data[0].embedding

    def similar(self, query: str) -> Optional[Dict[str, Any]]:
        normalized = _normalize(query)
        if not normalized:
            return None

        vector = self._embed(query)
        try:
            res = self._index.query(
                namespace=self.namespace,
                vector=vector,
                top_k=self.top_k,
                include_metadata=True,
                filter=None,
            )
        except Exception:
            return None

        matches = getattr(res, "matches", None) or (res.get("matches") if isinstance(res, dict) else [])
        for match in matches or []:
            score = getattr(match, "score", None) if not isinstance(match, dict) else match.get("score")
            if score is None or score < self.similarity_threshold:
                continue

            metadata = getattr(match, "metadata", None) if not isinstance(match, dict) else match.get("metadata")
            if not metadata:
                continue

            citations = metadata.get("citations")
            if isinstance(citations, str):
                try:
                    citations = json.loads(citations)
                except json.JSONDecodeError:
                    citations = None

            extra_meta = metadata.get("metadata")
            if isinstance(extra_meta, str):
                try:
                    extra_meta = json.loads(extra_meta)
                except json.JSONDecodeError:
                    extra_meta = None

            return {
                "key": getattr(match, "id", None) if not isinstance(match, dict) else match.get("id"),
                "query": metadata.get("query"),
                "answer": metadata.get("answer"),
                "citations": citations,
                "query_type": metadata.get("query_type"),
                "trace_id": metadata.get("trace_id"),
                "created_at": metadata.get("created_at"),
                "similarity": score,
            }

        return None

    def upsert(
        self,
        key: str,
        payload: Dict[str, Any],
        *,
        query: Optional[str] = None,
    ) -> None:
        if not key:
            return

        query_text = query or payload.get("query") or ""
        vector = self._embed(query_text)

        citations = payload.get("citations")
        citations_json = json.dumps(citations) if citations is not None else None

        metadata: Dict[str, Any] = {
            "query": query_text,
            "answer": payload.get("answer"),
            "citations": citations_json,
            "query_type": payload.get("query_type"),
            "trace_id": payload.get("trace_id"),
            "created_at": payload.get("created_at") or _now_iso(),
        }

        metadata = {k: v for k, v in metadata.items() if v is not None}

        try:
            self._index.upsert(
                namespace=self.namespace,
                vectors=[
                    {
                        "id": key,
                        "values": list(vector),
                        "metadata": metadata,
                    }
                ],
            )
        except Exception:
            pass

    def delete(self, key: str) -> None:
        try:
            self._index.delete(ids=[key], namespace=self.namespace)
        except Exception:
            pass
