from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(dsn: str) -> AsyncEngine:
    return create_async_engine(dsn, pool_pre_ping=True)


