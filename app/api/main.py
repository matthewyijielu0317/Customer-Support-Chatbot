from fastapi import FastAPI

from app.api.routes import chat, ingest_docs, ingest_tabular
from src.config.logging import configure_logging


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    configure_logging()
    app = FastAPI(title="Customer Support RAG API", version="0.1.0")

    # Routers
    app.include_router(chat.router, prefix="/v1")
    app.include_router(ingest_docs.router, prefix="/v1")
    app.include_router(ingest_tabular.router, prefix="/v1")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()


