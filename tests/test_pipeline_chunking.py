from pathlib import Path

import pytest

from src.ingestion.documents.loaders import load_from_pdf_dir
from src.ingestion.documents.pipeline import split_documents


@pytest.mark.parametrize("pdf_name", [
    "Shipping_and_Delivery_Policy.pdf",
])
def test_split_single_pdf_semantic_off(pdf_name: str):
    # Locate data directory relative to repo root
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    pdf_path = data_dir / pdf_name

    if not pdf_path.exists():
        pytest.skip(f"Sample PDF not found: {pdf_path}")

    # Load all PDFs in directory then filter to the chosen file
    docs = load_from_pdf_dir(data_dir)
    selected_docs = [d for d in docs if str(d.metadata.get("source", "")).endswith(pdf_name)]

    assert selected_docs, f"No documents loaded for {pdf_name}"

    # Split with semantic=False to avoid external API calls
    chunks = split_documents(selected_docs, semantic=False, chunk_size=800, chunk_overlap=150)

    assert len(chunks) > 0, "Expected at least one chunk"
    assert all(c.page_content and isinstance(c.page_content, str) for c in chunks)
    assert all(str(c.metadata.get("source", "")).endswith(pdf_name) for c in chunks)

    # Basic sanity on chunk sizes (not too tiny, not huge)
    avg_len = sum(len(c.page_content) for c in chunks) / len(chunks)
    assert 200 <= avg_len <= 2000, f"Unexpected average chunk size: {avg_len}"


