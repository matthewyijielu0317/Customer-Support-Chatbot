from __future__ import annotations
from typing import Any, Dict, List, Optional
import os

from langchain.schema import Document
from openai import OpenAI
from pinecone import Pinecone

from src.config.settings import settings


EMBEDDING_MODEL = "text-embedding-3-small"


class PineconeRetriever:
    """Pinecone retriever using OpenAI embeddings."""

    def __init__(self, index_name: str, namespace: Optional[str] = None, embedding_model: str = EMBEDDING_MODEL):
        self.index_name = index_name
        self.namespace = namespace
        self.embedding_model = embedding_model

        self._pc = Pinecone(api_key=(settings.pinecone_api_key or os.getenv("PINECONE_API_KEY", "")))
        self._index = self._pc.Index(index_name)
        self._openai = OpenAI(api_key=(settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")))

    async def aretrieve(self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        emb = self._openai.embeddings.create(model=self.embedding_model, input=[query]).data[0].embedding
        res = self._index.query(
            vector=emb,
            top_k=k,
            include_metadata=True,
            namespace=self.namespace,
            filter=filter,
        )

        docs: List[Document] = []
        for m in getattr(res, "matches", []) or []:
            md = m.metadata or {}
            # Attach score to metadata for downstream citation display
            try:
                md["score"] = float(getattr(m, "score", 0.0) or 0.0)
            except Exception:
                md["score"] = 0.0
            text = md.get("text") or ""
            docs.append(Document(page_content=text, metadata=md))
        return docs

    def retrieve(self, query: str, k: int = 10, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Synchronous variant of retrieval to simplify use in sync graphs/nodes."""
        emb = self._openai.embeddings.create(model=self.embedding_model, input=[query]).data[0].embedding
        res = self._index.query(
            vector=emb,
            top_k=k,
            include_metadata=True,
            namespace=self.namespace,
            filter=filter,
        )

        docs: List[Document] = []
        for m in getattr(res, "matches", []) or []:
            md = m.metadata or {}
            try:
                md["score"] = float(getattr(m, "score", 0.0) or 0.0)
            except Exception:
                md["score"] = 0.0
            text = md.get("text") or ""
            docs.append(Document(page_content=text, metadata=md))
        return docs


