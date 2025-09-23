from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    title: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None


class RAGState(BaseModel):
    """Typed state used across LangGraph nodes."""

    query: str
    query_type: Optional[str] = None
    should_retrieve_sql: bool = False
    should_retrieve_docs: bool = False
    order_id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    docs: List[Dict[str, Any]] = Field(default_factory=list)
    sql_rows: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    session_summary: Optional[str] = None
    answer: Optional[str] = None
    should_escalate: bool = False
    cache_key: Optional[str] = None
    cache_hit: bool = False
    should_cache: bool = False
    semantic_cache: Optional[Any] = Field(default=None, exclude=True)
    trace_id: Optional[str] = None
    grounded: Optional[bool] = None
    grounded_explanation: Optional[str] = None
    grounded_retry_count: int = 0
