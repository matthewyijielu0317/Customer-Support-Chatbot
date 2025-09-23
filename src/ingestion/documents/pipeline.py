from typing import List, Optional, Type

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings

# SemanticChunker may not be available in all environments
try:
    from langchain_text_splitters import SemanticChunker  # legacy location
    SEMANTIC_CHUNKER_AVAILABLE = True
except ImportError:
    try:
        # Current location in langchain-experimental
        from langchain_experimental.text_splitter import SemanticChunker
        SEMANTIC_CHUNKER_AVAILABLE = True
    except ImportError:
        SemanticChunker = None
        SEMANTIC_CHUNKER_AVAILABLE = False

from .loaders import (
    load_from_url,
    load_from_pdf_dir,
    load_from_pdf_file,
    load_from_txt,
    load_from_docx,
)
from .preprocess import preprocess_documents
from src.vectorstores.pinecone_store import PineconeStore
from src.config.settings import settings


def infer_source_type(src: str) -> str:
    if src.startswith("http://") or src.startswith("https://"):
        return "url"
    if src.lower().endswith(".txt"):
        return "txt"
    if src.lower().endswith(".pdf"):
        return "pdf_file"
    if src.lower().endswith(".docx"):
        return "docx"
    # Assume it's a directory if it doesn't have a file extension
    return "pdf_dir"


def load_documents(sources: List[str]) -> List[Document]:
    docs: List[Document] = []
    for src in sources:
        typ = infer_source_type(src)
        if typ == "url":
            docs.extend(load_from_url(src))
        elif typ == "txt":
            docs.extend(load_from_txt(src))
        elif typ == "pdf_file":
            docs.extend(load_from_pdf_file(src))
        elif typ == "docx":
            docs.extend(load_from_docx(src))
        else:  # pdf_dir
            docs.extend(load_from_pdf_dir(src))
    return docs


def split_documents(documents: List[Document], chunk_size: int = 800, chunk_overlap: int = 150, semantic: bool = True) -> List[Document]:
    """Split documents using semantic chunking when available; fallback to recursive chars.

    Semantic chunker uses OpenAI embeddings to find natural breakpoints.
    """
    if semantic and SEMANTIC_CHUNKER_AVAILABLE:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        print("Using semantic chunker...")
        semantic_splitter = SemanticChunker(
            embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=90,
        )
        return semantic_splitter.split_documents(documents)

    # Fall back to recursive character splitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)


def ingest_sources(sources: List[str], namespace: str | None = None, preprocess: bool = False) -> int:
    """Load, split, and upsert chunks into Pinecone. Returns vectors indexed."""
    docs = load_documents(sources)
    
    # Apply preprocessing if requested
    if preprocess:
        print("Applying preprocessing to documents...")
        docs = preprocess_documents(docs)
        print(f"Preprocessing complete. Documents ready for chunking.")
    
    chunks = split_documents(docs)
    store = PineconeStore(settings.pinecone_index)
    n = store.upsert(chunks, namespace=namespace)
    return n


def ingest_files_with_preprocessing(file_sources: List[str], namespace: str | None = None, semantic: bool = True) -> int:
    """Complete pipeline: Load files -> Preprocess -> Semantic Chunk -> Store in Pinecone.
    
    Args:
        file_sources: List of file paths or directories
        namespace: Pinecone namespace (defaults to 'processed-docs')
        semantic: Whether to use semantic chunking
    
    Returns:
        Number of vectors upserted to Pinecone
    """
    if namespace is None:
        namespace = "processed-docs"
    
    print(f"Starting end-to-end files ingestion pipeline...")
    print(f"Sources: {file_sources}")
    print(f"Namespace: {namespace}")
    print(f"Semantic chunking: {semantic}")
    print("=" * 60)
    
    # Step 1: Load documents from file sources
    print("Step 1: Loading documents...")
    docs = load_documents(file_sources)
    print(f"Loaded {len(docs)} documents from {len(file_sources)} sources")
    
    # Show original content stats
    original_chars = sum(len(doc.page_content) for doc in docs)
    print(f"Original content: {original_chars:,} characters")
    
    # Step 2: Apply preprocessing
    print("\nStep 2: Applying preprocessing...")
    print("  - Removing headers/footers")
    print("  - Normalizing whitespace")
    print("  - Replacing newlines with spaces")
    print("  - Cleaning up multiple spaces")
    
    processed_docs = preprocess_documents(docs)
    processed_chars = sum(len(doc.page_content) for doc in processed_docs)
    reduction = original_chars - processed_chars
    reduction_pct = (reduction / original_chars * 100) if original_chars > 0 else 0
    
    print(f"Processed content: {processed_chars:,} characters")
    print(f"Reduction: {reduction:,} characters ({reduction_pct:.1f}%)")
    
    # Step 3: Apply semantic chunking
    print(f"\nStep 3: Applying semantic chunking...")
    chunks = split_documents(processed_docs, semantic=semantic)
    print(f"Generated {len(chunks)} semantic chunks")
    
    # Show chunk statistics
    chunk_sizes = [len(chunk.page_content) for chunk in chunks]
    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
    min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
    max_chunk_size = max(chunk_sizes) if chunk_sizes else 0
    
    print(f"Chunk statistics:")
    print(f"  Average size: {avg_chunk_size:.0f} characters")
    print(f"  Min size: {min_chunk_size} characters")
    print(f"  Max size: {max_chunk_size} characters")
    
    # Step 4: Store in Pinecone
    print(f"\nStep 4: Storing in Pinecone...")
    print(f"Index: {settings.pinecone_index}")
    print(f"Namespace: {namespace}")
    
    store = PineconeStore(settings.pinecone_index)
    n = store.upsert(chunks, namespace=namespace)
    
    print(f"\n✅ Pipeline completed successfully!")
    print(f"Total vectors upserted: {n}")
    
    return n
