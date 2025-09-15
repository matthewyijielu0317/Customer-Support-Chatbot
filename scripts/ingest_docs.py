import argparse
import sys
from pathlib import Path

# Add project root to path so 'src' imports work
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingestion.documents.pipeline import ingest_sources


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("sources", nargs="+", help="URLs, txt files, or PDF directories")
    p.add_argument("--namespace", default=None)
    args = p.parse_args()

    n = ingest_sources(args.sources, args.namespace)
    print(f"Successfully upserted {n} vectors to Pinecone.")


if __name__ == "__main__":
    main()


