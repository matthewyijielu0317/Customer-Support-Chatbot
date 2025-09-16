from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Citation(BaseModel):
    source: str
    title: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None


class RAGState(BaseModel):
    """Typed state used across LangGraph nodes."""

    query: str
    intent: Optional[str] = None
    should_retrieve: bool = True
    entities: Dict[str, Any] = {}
    docs: List[Dict[str, Any]] = []
    sql_rows: List[Dict[str, Any]] = []
    citations: List[Citation] = []
    answer: Optional[str] = None
    should_escalate: bool = False
    cache_key: Optional[str] = None
    trace_id: Optional[str] = None
    grounded: Optional[bool] = None
    grounded_explanation: Optional[str] = None
    grounded_retry_count: int = 0


