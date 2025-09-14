from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_settings


router = APIRouter(tags=["ingestion"])


class IngestTabularRequest(BaseModel):
    customers_csv_path: Optional[str] = None
    orders_csv_path: Optional[str] = None
    products_csv_path: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    rows_loaded: int = 0


@router.post("/ingest/csv", response_model=IngestResponse)
async def ingest_tabular(payload: IngestTabularRequest, settings=Depends(get_settings)) -> IngestResponse:
    """Stub for tabular ingestion. Will load CSVs into Postgres in later steps."""
    # TODO: wire to src/ingestion/tabular/loader.py
    return IngestResponse(status="accepted", rows_loaded=0)


