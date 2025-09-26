from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_settings
from src.ingestion.tabular.loader import create_engine_from_dsn, load_csvs, close_engine


router = APIRouter(tags=["ingestion"])


class IngestTabularRequest(BaseModel):
    dsn: str
    customers_csv_path: Optional[str] = None
    orders_csv_path: Optional[str] = None
    products_csv_path: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    rows_loaded: int = 0


@router.post("/ingest/csv", response_model=IngestResponse)
async def ingest_tabular(payload: IngestTabularRequest, settings=Depends(get_settings)) -> IngestResponse:
    """Load CSV data into Postgres database."""
    try:
        engine = create_engine_from_dsn(payload.dsn)
        rows = await load_csvs(
            engine, 
            payload.customers_csv_path, 
            payload.orders_csv_path, 
            payload.products_csv_path
        )
        await close_engine(engine)
        return IngestResponse(status="success", rows_loaded=rows)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ingestion failed: {str(e)}")


