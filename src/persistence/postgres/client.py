"""PostgreSQL engine creation utilities.

Provides both async and sync engine creation for different use cases:
- Async engines for FastAPI endpoints and async operations
- Sync engines for synchronous operations like SQL retrieval nodes
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.engine import Engine


def create_async_engine_from_dsn(dsn: str) -> AsyncEngine:
    """Create an async SQLAlchemy engine from a DSN.
    
    Args:
        dsn: Database connection string
        
    Returns:
        Configured async SQLAlchemy engine
    """
    return create_async_engine(dsn, pool_pre_ping=True, future=True)


def create_sync_engine_from_dsn(dsn: str) -> Engine:
    """Create a sync SQLAlchemy engine from a DSN.
    
    Uses psycopg driver. DSN should be in format:
    postgresql+psycopg://user:password@host:port/database
    
    Args:
        dsn: Database connection string
        
    Returns:
        Configured sync SQLAlchemy engine
    """
    return create_engine(dsn, pool_pre_ping=True, future=True)


# Backward compatibility aliases
create_async_engine = create_async_engine_from_dsn
create_sync_engine = create_sync_engine_from_dsn
