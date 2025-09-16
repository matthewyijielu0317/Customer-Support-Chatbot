import argparse
import sys
from pathlib import Path
from statistics import mean
import re


# Ensure project root for `src` imports
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Tuple

from langchain.schema import Document

from src.ingestion.loaders import load_from_pdf_file
from src.ingestion.preprocess import preprocess_documents
from src.ingestion.ingestion_pipeline import split_documents, SEMANTIC_CHUNKER_AVAILABLE
from src.config.settings import settings


def is_sentence_terminal(text: str) -> bool:
    if not text:
        return False
    t = text.rstrip()
    # Common sentence endings, allow quotes/paren after punctuation
    return bool(re.search(r"[\.!?][\]\)\"'”]*\s*$", t))


def boundary_samples(chunks: List[Document], sample_count: int = 3) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for i in range(min(sample_count, max(0, len(chunks) - 1))):
        left = chunks[i].page_content
        right = chunks[i + 1].page_content
        pairs.append((left[-160:].replace("\n", " "), right[:160].replace("\n", " ")))
    return pairs


def analyze_chunks(label: str, chunks: List[Document]) -> None:
    sizes = [len(c.page_content) for c in chunks]
    term_ratio = sum(1 for c in chunks if is_sentence_terminal(c.page_content)) / len(chunks) if chunks else 0.0
    print(f"\n=== {label} ===")
    print(f"Chunks: {len(chunks)}")
    if sizes:
        print(f"Size (chars): min={min(sizes)}, max={max(sizes)}, avg={int(mean(sizes))}")
    print(f"Ends at sentence boundary: {term_ratio*100:.1f}%")
    for idx, (l, r) in enumerate(boundary_samples(chunks), start=1):
        print(f"-- Boundary {idx} --")
        print(f"[..]{l}")
        print(f"{r}[..]")


def main() -> None:
    p = argparse.ArgumentParser(description="Verify whether semantic chunking is used and inspect boundaries")
    p.add_argument("--file", required=True, help="Path to a PDF file to test")
    p.add_argument("--preprocess", action="store_true", help="Apply preprocessing before splitting (recommended)")
    p.add_argument("--compare-baseline", action="store_true", help="Also run non-semantic baseline for comparison")
    args = p.parse_args()

    print(f"SemanticChunker available: {SEMANTIC_CHUNKER_AVAILABLE}")
    import os
    # Ensure OpenAI key is available to embeddings, falling back to settings
    if not os.getenv("OPENAI_API_KEY") and settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    print(f"OPENAI_API_KEY set: {has_openai}")

    print("Loading PDF pages...")
    docs = load_from_pdf_file(args.file)
    print(f"Loaded {len(docs)} pages")

    if args.preprocess:
        print("Applying preprocessing (header/footer removal, whitespace normalization)...")
        docs = preprocess_documents(docs)

    print("Splitting with semantic=True (SemanticChunker if available)...")
    semantic_chunks = split_documents(docs, semantic=True)
    analyze_chunks("Semantic", semantic_chunks)

    if args.compare_baseline:
        print("\nSplitting with semantic=False (RecursiveCharacterTextSplitter)...")
        baseline_chunks = split_documents(docs, semantic=False)
        analyze_chunks("Baseline", baseline_chunks)


if __name__ == "__main__":
    main()


