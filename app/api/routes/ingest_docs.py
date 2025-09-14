from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_settings


router = APIRouter(tags=["ingestion"])


class IngestDocsRequest(BaseModel):
    sources: List[str]
    namespace: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    chunks_indexed: int = 0


@router.post("/ingest/docs", response_model=IngestResponse)
async def ingest_docs(payload: IngestDocsRequest, settings=Depends(get_settings)) -> IngestResponse:
    """Stub for document ingestion. Will call ingestion pipeline in later steps."""
    # TODO: wire to src/ingestion/documents/pipeline.py and Pinecone store
    return IngestResponse(status="accepted", chunks_indexed=0)


