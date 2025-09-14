import argparse
import asyncio

from src.ingestion.tabular.loader import create_engine_from_dsn, load_csvs


async def run(args):
    engine = create_engine_from_dsn(args.dsn)
    rows = await load_csvs(engine, args.customers, args.orders, args.products)
    print(f"Loaded {rows} rows (template).")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dsn", required=True)
    p.add_argument("--customers")
    p.add_argument("--orders")
    p.add_argument("--products")
    args = p.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()


