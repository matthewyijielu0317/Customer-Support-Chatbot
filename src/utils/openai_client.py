from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from openai import OpenAI

from src.config.settings import settings


def _resolve_api_key() -> str:
    return settings.openai_api_key or os.getenv("OPENAI_API_KEY", "")


@lru_cache(maxsize=1)
def get_openai_client() -> Optional[OpenAI]:
    api_key = _resolve_api_key()
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


__all__ = ["get_openai_client"]
