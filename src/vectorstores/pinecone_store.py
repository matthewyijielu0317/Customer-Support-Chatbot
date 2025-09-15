from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence
import os
import hashlib

from langchain.schema import Document
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from src.config.settings import settings


EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims
EMBEDDING_DIM = 1536


class PineconeStore:
    """Vector store wrapper for Pinecone using OpenAI embeddings."""

    def __init__(self, index_name: str, embedding_model: str = EMBEDDING_MODEL):
        self.index_name = index_name
        self.embedding_model = embedding_model
        self._pc: Optional[Pinecone] = None
        self._index = None
        self._openai = OpenAI(api_key=(settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")))

    def _get_pc(self) -> Pinecone:
        if self._pc is None:
            self._pc = Pinecone(api_key=(settings.pinecone_api_key or os.getenv("PINECONE_API_KEY", "")))
        return self._pc

    def _ensure_index(self) -> None:
        pc = self._get_pc()
        existing = [i["name"] for i in pc.list_indexes()]
        if self.index_name not in existing:
            pc.create_index(
                name=self.index_name,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        self._index = pc.Index(self.index_name)

    def _get_index(self):
        if self._index is None:
            self._ensure_index()
        return self._index

    def _embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        resp = self._openai.embeddings.create(model=self.embedding_model, input=list(texts))
        return [d.embedding for d in resp.data]

    def upsert(self, chunks: Sequence[Document], namespace: Optional[str] = None, batch_size: int = 128) -> int:
        """Upsert chunk Documents into Pinecone.

        Each vector stores embedding and metadata: {source, page, title, text}.
        Returns number of vectors upserted.
        """
        if not chunks:
            return 0

        index = self._get_index()
        total = 0

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            texts = [d.page_content for d in batch]
            embeddings = self._embed_texts(texts)

            vectors: List[Dict[str, Any]] = []
            for doc, emb in zip(batch, embeddings):
                meta = doc.metadata or {}
                source = str(meta.get("source", ""))
                page = str(meta.get("page", ""))
                stable_id = hashlib.sha256((source + "|" + page + "|" + doc.page_content).encode("utf-8")).hexdigest()
                # Only store specific metadata fields: source, title, page, text
                md: Dict[str, Any] = {
                    "source": source,
                    "text": doc.page_content,
                }
                
                # Only add these specific fields if they exist and are not null
                if meta.get("page") is not None:
                    md["page"] = meta.get("page")
                if meta.get("title"):
                    md["title"] = str(meta.get("title"))
                vectors.append({"id": stable_id, "values": emb, "metadata": md})

            index.upsert(vectors=vectors, namespace=namespace)
            total += len(vectors)

        return total


