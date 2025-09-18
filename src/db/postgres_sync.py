from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_engine_sync(dsn: str) -> Engine:
    """Create a synchronous SQLAlchemy Engine.

    Uses psycopg driver via DSN (postgresql+psycopg://...).
    """
    return create_engine(dsn, pool_pre_ping=True, future=True)



