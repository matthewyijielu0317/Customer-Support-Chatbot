from pathlib import Path

import pytest

from src.ingestion.documents.loaders import load_from_pdf_dir
from src.ingestion.documents.preprocess import preprocess_documents


@pytest.mark.parametrize("pdf_name", [
    "Shipping_and_Delivery_Policy.pdf",
])
def test_preprocess_removes_headers_and_hyphenation(pdf_name: str):
    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"

    docs = load_from_pdf_dir(data_dir)
    selected = [d for d in docs if str(d.metadata.get("source", "")).endswith(pdf_name)]
    assert selected, f"No docs for {pdf_name}"

    cleaned = preprocess_documents(selected)
    assert cleaned, "Expected cleaned docs"

    # Check common cleaning properties
    for d in cleaned:
        assert "\u00AD" not in d.page_content  # soft hyphen removed
        # no triple newlines
        assert "\n\n\n" not in d.page_content
        # no trailing/leading whitespace lines
        lines = d.page_content.splitlines()
        if lines:
            assert lines[0] == lines[0].strip()
            assert lines[-1] == lines[-1].strip()



