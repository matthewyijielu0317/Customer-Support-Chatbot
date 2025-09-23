from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_session_store, get_semantic_cache
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.persistence.redis import RedisSessionStore
from src.graph.graph import build_graph
from src.graph.state import RAGState
from src.config.settings import settings
from src.utils.summarize import summarize_messages
from src.utils.names import derive_name_from_email
from src.utils.ids import generate_readable_session_id


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
    semantic_cache: PineconeSemanticCache = Depends(get_semantic_cache),
) -> ChatResponse:
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")
    if not payload.query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query is required")

    session_id = payload.session_id or generate_readable_session_id(payload.user_id)

    meta = session_store.read_session_meta(session_id)
    now = datetime.now(timezone.utc)
    if meta:
        stored_user = meta.get("user_id")
        if stored_user and stored_user != payload.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")
    else:
        meta = {
            "user_id": payload.user_id,
            "status": "active",
            "created_at": now.isoformat(),
            "message_count": 0,
            "summary_message_count": 0,
            "greeting_sent": False,
        }
        session_store.write_session_meta(session_id, meta)
        session_store.register_session(session_id, payload.user_id)

    first_name = meta.get("first_name")
    last_name = meta.get("last_name")
    meta_dirty = False
    if not first_name and not last_name:
        derived_first, derived_last = derive_name_from_email(payload.user_id)
        if derived_first:
            meta["first_name"] = derived_first
            first_name = derived_first
            meta_dirty = True
        if derived_last:
            meta["last_name"] = derived_last
            last_name = derived_last
            meta_dirty = True

    if not meta.get("greeting_sent"):
        greeting_name = first_name or "there"
        greeting_text = f"Hello {greeting_name}, how can I assist you today!"
        greeting_ts = datetime.now(timezone.utc)
        session_store.append_message(
            session_id,
            {
                "role": "assistant",
                "content": greeting_text,
                "created_at": greeting_ts.isoformat(),
            },
        )
        meta.update(
            {
                "greeting_sent": True,
                "last_response": greeting_text,
                "last_updated": greeting_ts.isoformat(),
                "message_count": int(meta.get("message_count", 0)) + 1,
            }
        )
        meta_dirty = True

    if meta_dirty:
        session_store.write_session_meta(session_id, meta)

    recent_messages = session_store.get_recent_messages(session_id)
    session_summary = meta.get("session_summary")
    summary_message_count = int(meta.get("summary_message_count") or 0)

    state = RAGState(
        query=payload.query,
        user_id=payload.user_id,
        session_id=session_id,
        recent_messages=recent_messages,
        session_summary=session_summary,
        semantic_cache=semantic_cache,
        first_name=meta.get("first_name"),
        last_name=meta.get("last_name"),
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

    answer = str(out_dict.get("answer") or "")
    assistant_ts = datetime.now(timezone.utc)
    session_store.append_message(
        session_id,
        {"role": "assistant", "content": answer, "created_at": assistant_ts.isoformat()},
    )
    meta_message_count = int(meta.get("message_count", 0)) + 2
    meta.update(
        {
            "user_id": payload.user_id,
            "last_query": payload.query,
            "last_response": answer,
            "last_updated": assistant_ts.isoformat(),
            "message_count": meta_message_count,
        }
    )

    if (
        meta_message_count >= settings.session_summary_min_messages
        and meta_message_count > summary_message_count
    ):
        history_limit = settings.session_summary_history_limit * 2
        history_messages = session_store.get_all_messages(session_id, limit=history_limit)
        summary_payload = [
            {
                "role": msg.get("role", "user"),
                "content": (msg.get("content") or ""),
            }
            for msg in history_messages
            if msg.get("content")
        ]
        if summary_payload:
            summary_text = summarize_messages(summary_payload, max_length=settings.session_summary_max_chars)
            if summary_text:
                meta["session_summary"] = summary_text
                meta["summary_message_count"] = meta_message_count

    session_store.write_session_meta(session_id, meta)
    session_store.touch_session(session_id)

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
