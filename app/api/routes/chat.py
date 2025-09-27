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
from src.integrations.slack import send_escalation_alert


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
    session_status: str = "active"


_graph = build_graph()

ESCALATION_MESSAGE = (
    "I'm escalating this conversation to a human support specialist. "
    "Please stay with me while I connect you."
)


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

    session_status = meta.get("status", "active")
    if session_status in {"pending_handoff", "live_agent"}:
        user_ts = datetime.now(timezone.utc)
        session_store.append_message(
            session_id,
            {"role": "user", "content": payload.query, "created_at": user_ts.isoformat()},
        )
        meta.update(
            {
                "last_query": payload.query,
                "last_updated": user_ts.isoformat(),
                "message_count": int(meta.get("message_count", 0)) + 1,
            }
        )
        session_store.write_session_meta(session_id, meta)
        session_store.touch_session(session_id)
        return ChatResponse(
            session_id=session_id,
            answer="",
            citations=[],
            should_escalate=False,
            trace_id="",
            cache_hit=False,
            session_status=session_status,
        )

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

    should_escalate = bool(out_dict.get("should_escalate", False))
    escalation_reason = out_dict.get("escalation_reason")
    answer = str(out_dict.get("answer") or "")
    if should_escalate:
        answer = answer.strip()
        if answer:
            answer = f"{answer}\n\n{ESCALATION_MESSAGE}"
        else:
            answer = ESCALATION_MESSAGE

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

    notify_slack = False
    if should_escalate:
        previous_status = meta.get("status") or "active"
        if previous_status not in {"pending_handoff", "live_agent"}:
            meta["status"] = "pending_handoff"
            meta["escalated_at"] = assistant_ts.isoformat()
            meta["escalation_reason"] = escalation_reason or "User requested human assistance."
            meta["escalated_query"] = payload.query
            meta["escalated_answer"] = answer
            notify_slack = True
        else:
            meta["status"] = previous_status
    elif not meta.get("status"):
        meta["status"] = "active"

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

    if notify_slack:
        session_store.enqueue_escalation(session_id)
        session_link = ""
        if settings.frontend_base_url:
            session_link = f"{settings.frontend_base_url.rstrip('/')}/?session_id={session_id}&view=agent"
        await send_escalation_alert(
            session_id=session_id,
            user_email=payload.user_id,
            user_query=payload.query,
            assistant_answer=answer,
            escalation_reason=meta.get("escalation_reason"),
            ui_url=session_link or None,
        )

    cache_hit = bool(out_dict.get("cache_hit", False))

    session_status = meta.get("status", "active")

    response = ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=resp_citations,
        should_escalate=should_escalate,
        trace_id=str(out_dict.get("trace_id") or ""),
        cache_hit=cache_hit,
        session_status=session_status,
    )

    return response
