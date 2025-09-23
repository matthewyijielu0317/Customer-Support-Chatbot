from typing import Callable

from fastapi import Request
from src.config.settings import Settings, settings
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.persistence.mongo import Mongo
from src.persistence.redis import RedisKV, RedisSessionStore


def get_settings() -> Settings:
    """FastAPI dependency to access app settings."""
    return settings


def get_redis_kv(request: Request) -> RedisKV:
    return request.app.state.redis_kv


def get_session_store(request: Request) -> RedisSessionStore:
    return request.app.state.redis_session_store


def get_semantic_cache(request: Request) -> PineconeSemanticCache:
    return request.app.state.semantic_cache


def get_mongo(request: Request) -> Mongo:
    return request.app.state.mongo
