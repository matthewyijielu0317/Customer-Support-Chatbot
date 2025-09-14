from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_settings


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class Citation(BaseModel):
    source: str
    title: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    should_escalate: bool = False
    trace_id: str = ""


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, settings=Depends(get_settings)) -> ChatResponse:
    """Chat endpoint stub. Wire LangGraph workflow here in subsequent steps."""
    # TODO: replace with LangGraph invocation and real retrieval/citations
    return ChatResponse(
        answer="Template endpoint is live. Wire LangGraph to generate answers.",
        citations=[],
        should_escalate=False,
        trace_id="template",
    )


