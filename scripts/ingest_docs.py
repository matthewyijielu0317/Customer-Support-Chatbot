import argparse

from src.ingestion.documents.pipeline import ingest_sources


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("sources", nargs="+", help="URLs, txt files, or PDF directories")
    p.add_argument("--namespace", default=None)
    args = p.parse_args()

    n = ingest_sources(args.sources, args.namespace)
    print(f"Processed {n} chunks (template; not yet upserted).")


if __name__ == "__main__":
    main()


