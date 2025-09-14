from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text


async def load_csvs(engine: AsyncEngine, customers: Optional[Path], orders: Optional[Path], products: Optional[Path]) -> int:
    """Stub for CSV ingestion into Postgres using COPY. Returns rows loaded."""
    # This is a placeholder; implement COPY FROM STDIN or pandas to_sql later.
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    return 0


def create_engine_from_dsn(dsn: str) -> AsyncEngine:
    return create_async_engine(dsn, pool_pre_ping=True)


