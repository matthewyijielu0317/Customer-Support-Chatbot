from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_settings
from src.graph.graph import build_graph
from src.graph.state import RAGState


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


_graph = build_graph()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, settings=Depends(get_settings)) -> ChatResponse:
    state = RAGState(query=payload.query)
    out = _graph.invoke(state)

    # Serialize citations for response model
    resp_citations: List[Citation] = []
    for c in out.citations or []:
        resp_citations.append(Citation(source=c.source, title=c.title))

    return ChatResponse(
        answer=out.answer or "",
        citations=resp_citations,
        should_escalate=bool(out.should_escalate),
        trace_id=out.trace_id or "",
    )


