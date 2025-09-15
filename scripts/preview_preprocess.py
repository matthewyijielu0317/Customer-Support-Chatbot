import sys
from pathlib import Path

# Ensure project root on sys.path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.documents.loaders import load_from_pdf_dir
from src.ingestion.documents.preprocess import preprocess_documents


def main() -> None:
    data_dir = Path("data")
    pdf_name = sys.argv[1] if len(sys.argv) > 1 else "Shipping_and_Delivery_Policy.pdf"

    docs = load_from_pdf_dir(data_dir)
    selected = [d for d in docs if str(d.metadata.get("source", "")).endswith(pdf_name)]
    if not selected:
        print(f"No docs found for {pdf_name}")
        return

    cleaned = preprocess_documents(selected)
    print(f"📄 Showing cleaned text for: {pdf_name}")
    print("\n===== CLEANED PAGE 1 (first 500 chars) =====\n")
    print((cleaned[0].page_content[:500]).strip())
    if len(cleaned) > 1:
        print("\n===== CLEANED PAGE 2 (first 500 chars) =====\n")
        print((cleaned[1].page_content[:500]).strip())


if __name__ == "__main__":
    main()



