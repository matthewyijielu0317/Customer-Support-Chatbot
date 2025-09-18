"""Tabular data ingestion utilities for loading synthetic CSV fixtures."""

from .loader import create_engine_from_dsn, load_csvs

__all__ = [
    "create_engine_from_dsn",
    "load_csvs",
]
