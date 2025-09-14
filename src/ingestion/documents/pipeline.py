from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document

from src.ingestion.documents.loaders import (
    load_from_url,
    load_from_pdf_dir,
    load_from_txt,
)


def infer_source_type(src: str) -> str:
    if src.startswith("http://") or src.startswith("https://"):
        return "url"
    if src.lower().endswith(".txt"):
        return "txt"
    return "pdf_dir"


def load_documents(sources: List[str]) -> List[Document]:
    docs: List[Document] = []
    for src in sources:
        typ = infer_source_type(src)
        if typ == "url":
            docs.extend(load_from_url(src))
        elif typ == "txt":
            docs.extend(load_from_txt(src))
        else:
            docs.extend(load_from_pdf_dir(src))
    return docs


def split_documents(documents: List[Document], chunk_size: int = 800, chunk_overlap: int = 150) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)


def ingest_sources(sources: List[str], namespace: str | None = None) -> int:
    """Stub for ingestion: load and split; upsert to vector store later.

    Returns number of chunks processed.
    """
    docs = load_documents(sources)
    chunks = split_documents(docs)
    # TODO: upsert chunks into Pinecone (namespace)
    return len(chunks)


