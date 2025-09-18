from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_mongo, get_session_store, get_semantic_cache
from src.cache.redis_kv import RedisSessionStore
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.db.mongo import Mongo
from src.graph.graph import build_graph
from src.graph.state import RAGState
from src.config.settings import settings
from src.utils.summarize import summarize_messages


router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    user_id: str
    query: str
    session_id: Optional[str] = None


class Citation(BaseModel):
    source: str
    title: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    should_escalate: bool = False
    trace_id: str = ""
    cache_hit: bool = False


_graph = build_graph()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    session_store: RedisSessionStore = Depends(get_session_store),
    mongo: Mongo = Depends(get_mongo),
    semantic_cache: PineconeSemanticCache = Depends(get_semantic_cache),
) -> ChatResponse:
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    if not payload.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

    session_id = payload.session_id or str(uuid4())

    existing_session = mongo.get_session(session_id)
    if existing_session and existing_session.get("user_id") not in (None, payload.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")

    mongo.create_session(session_id, payload.user_id)

    meta = session_store.read_session_meta(session_id)
    if meta:
        stored_user = meta.get("user_id")
        if stored_user and stored_user != payload.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")
    else:
        session_store.write_session_meta(session_id, {"user_id": payload.user_id})

    recent_messages = session_store.get_recent_messages(session_id)
    summary_doc = mongo.get_session_summary_doc(session_id)
    session_summary = summary_doc.get("summary") if summary_doc else None
    summary_message_count = summary_doc.get("message_count", 0) if summary_doc else 0

    state = RAGState(
        query=payload.query,
        user_id=payload.user_id,
        session_id=session_id,
        recent_messages=recent_messages,
        session_summary=session_summary,
        semantic_cache=semantic_cache,
    )
    out = _graph.invoke(state)

    # Normalize graph output to a dict
    out_dict = {}  # type: ignore[var-annotated]
    try:
        if isinstance(out, dict):
            out_dict = out
        elif hasattr(out, "model_dump"):
            out_dict = out.model_dump()  # pydantic v2
        elif hasattr(out, "dict"):
            out_dict = out.dict()  # pydantic v1
    except Exception:
        out_dict = {}

    # Serialize citations for response model
    resp_citations: List[Citation] = []
    for c in (out_dict.get("citations") or []):
        try:
            if isinstance(c, dict):
                resp_citations.append(Citation(source=str(c.get("source", "")), title=c.get("title")))
            else:
                resp_citations.append(Citation(source=str(getattr(c, "source", "")), title=getattr(c, "title", None)))
        except Exception:
            continue

    now = datetime.now(timezone.utc)
    session_store.append_message(
        session_id,
        {"role": "user", "content": payload.query, "created_at": now.isoformat()},
    )
    mongo.append_message(session_id, "user", payload.query, user_id=payload.user_id, created_at=now)

    answer = str(out_dict.get("answer") or "")
    assistant_ts = datetime.now(timezone.utc)
    session_store.append_message(
        session_id,
        {"role": "assistant", "content": answer, "created_at": assistant_ts.isoformat()},
    )
    mongo.append_message(session_id, "assistant", answer, user_id=payload.user_id, created_at=assistant_ts)

    session_store.write_session_meta(
        session_id,
        {
            "user_id": payload.user_id,
            "last_query": payload.query,
            "last_response": answer,
            "last_updated": assistant_ts.isoformat(),
        },
    )

    total_messages = mongo.count_messages(session_id)
    if total_messages >= settings.session_summary_min_messages and total_messages > summary_message_count:
        history_limit = settings.session_summary_history_limit
        history_docs = mongo.get_messages(session_id, limit=history_limit)
        summary_payload = [
            {
                "role": doc.get("role", "user"),
                "content": (doc.get("content") or ""),
            }
            for doc in history_docs
            if doc.get("content")
        ]
        if summary_payload:
            summary_text = summarize_messages(summary_payload, max_length=settings.session_summary_max_chars)
            if summary_text:
                mongo.upsert_session_summary(
                    session_id,
                    summary_text,
                    user_id=payload.user_id,
                    message_count=total_messages,
                )

    cache_hit = bool(out_dict.get("cache_hit", False))

    response = ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=resp_citations,
        should_escalate=bool(out_dict.get("should_escalate", False)),
        trace_id=str(out_dict.get("trace_id") or ""),
        cache_hit=cache_hit,
    )

    return response
