from typing import Callable

from src.config.settings import Settings, settings


def get_settings() -> Settings:
    """FastAPI dependency to access app settings."""
    return settings


