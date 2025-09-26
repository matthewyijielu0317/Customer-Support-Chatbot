from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from app.api.routes import auth, chat, ingest_docs, ingest_tabular, sessions
from src.config.logging import configure_logging
from src.config.settings import settings
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.persistence.mongo import Mongo
from src.persistence.redis import RedisKV, RedisSessionStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize external clients
    redis_kv = RedisKV(settings.redis_url)
    redis_session_store = RedisSessionStore(
        settings.redis_url,
        recent_window=settings.recent_messages_window,
        ttl_days=settings.session_redis_ttl_days,
        kv_client=redis_kv,
    )
    semantic_cache = PineconeSemanticCache(
        index_name=settings.pinecone_index,
        namespace=settings.semantic_cache_namespace,
        similarity_threshold=settings.semantic_cache_similarity_threshold,
    )
    mongo = Mongo(settings.mongodb_uri, db_name="ecomm")

    app.state.redis_kv = redis_kv
    app.state.redis_session_store = redis_session_store
    app.state.semantic_cache = semantic_cache
    app.state.mongo = mongo

    try:
        yield
    finally:
        try:
            redis_kv.client.close()
        except Exception:
            pass
        try:
            mongo.client.close()
        except Exception:
            pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    app = FastAPI(title="Customer Support RAG API", version="0.1.0", lifespan=lifespan)

    # Routers
    app.include_router(auth.router, prefix="/v1")
    app.include_router(chat.router, prefix="/v1")
    app.include_router(ingest_docs.router, prefix="/v1")
    app.include_router(ingest_tabular.router, prefix="/v1")
    app.include_router(sessions.router, prefix="/v1")

    @app.get("/health")
    async def health(request: Request) -> dict:
        status: dict = {"status": "ok"}
        # Redis
        try:
            request.app.state.redis_kv.client.ping()
            status["redis"] = "ok"
        except Exception as e:
            status["redis"] = f"error:{e.__class__.__name__}"
            status["status"] = "degraded"
        # Mongo
        try:
            request.app.state.mongo.client.admin.command("ping")
            status["mongo"] = "ok"
        except Exception as e:
            status["mongo"] = f"error:{e.__class__.__name__}"
            status["status"] = "degraded"
        return status

    return app


app = create_app()
