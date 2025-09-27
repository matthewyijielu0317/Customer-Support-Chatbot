from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_session_store
from src.persistence.redis import RedisSessionStore


router = APIRouter(tags=["escalations"])


class EscalationSummary(BaseModel):
    session_id: str
    user_id: str
    status: str
    created_at: str | None = None
    last_updated: str | None = None
    escalated_at: str | None = None
    escalation_reason: str | None = None
    agent_id: str | None = None
    last_query: str | None = None
    last_response: str | None = None


class EscalationListResponse(BaseModel):
    escalations: List[EscalationSummary] = Field(default_factory=list)


class ClaimEscalationRequest(BaseModel):
    agent_id: str


class AgentMessageRequest(BaseModel):
    agent_id: str
    content: str


class AgentMessageResponse(BaseModel):
    session_id: str
    status: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class EscalationDetailResponse(BaseModel):
    escalation: EscalationSummary
    messages: List[Dict[str, Any]] = Field(default_factory=list)


def _serialize_meta(meta: Dict[str, Any]) -> EscalationSummary:
    return EscalationSummary(
        session_id=str(meta.get("session_id")),
        user_id=str(meta.get("user_id")),
        status=str(meta.get("status", "active")),
        created_at=meta.get("created_at"),
        last_updated=meta.get("last_updated") or meta.get("updated_at"),
        escalated_at=meta.get("escalated_at"),
        escalation_reason=meta.get("escalation_reason"),
        agent_id=meta.get("agent_id"),
        last_query=meta.get("last_query"),
        last_response=meta.get("last_response"),
    )


@router.get("/escalations", response_model=EscalationListResponse)
async def list_escalations(
    agent_id: str | None = Query(default=None),
    session_store: RedisSessionStore = Depends(get_session_store),
) -> EscalationListResponse:
    metas = session_store.list_escalations()
    if agent_id:
        agent_metas = session_store.list_agent_sessions(agent_id)
    else:
        agent_metas = []

    combined: Dict[str, Dict[str, Any]] = {}
    for meta in metas + agent_metas:
        sid = str(meta.get("session_id"))
        combined[sid] = meta
    summaries = [_serialize_meta(meta) for meta in combined.values()]
    return EscalationListResponse(escalations=summaries)


@router.get("/escalations/{session_id}", response_model=EscalationDetailResponse)
async def get_escalation(
    session_id: str,
    session_store: RedisSessionStore = Depends(get_session_store),
) -> EscalationDetailResponse:
    meta = session_store.read_session_meta(session_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = session_store.get_all_messages(session_id)
    return EscalationDetailResponse(escalation=_serialize_meta(meta), messages=messages)


@router.post("/escalations/{session_id}/claim", response_model=EscalationSummary)
async def claim_escalation(
    session_id: str,
    payload: ClaimEscalationRequest,
    session_store: RedisSessionStore = Depends(get_session_store),
) -> EscalationSummary:
    if not payload.agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="agent_id is required")

    meta = session_store.read_session_meta(session_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    status_value = meta.get("status")
    if status_value not in {"pending_handoff", "live_agent"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not escalated")

    now = datetime.now(timezone.utc).isoformat()
    meta.update(
        {
            "status": "live_agent",
            "agent_id": payload.agent_id,
            "claimed_at": now,
            "last_updated": now,
        }
    )
    session_store.write_session_meta(session_id, meta)
    session_store.dequeue_escalation(session_id)
    session_store.assign_agent_session(session_id, payload.agent_id)
    return _serialize_meta(meta)


@router.post("/escalations/{session_id}/messages", response_model=AgentMessageResponse)
async def agent_send_message(
    session_id: str,
    payload: AgentMessageRequest,
    session_store: RedisSessionStore = Depends(get_session_store),
) -> AgentMessageResponse:
    if not payload.agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="agent_id is required")
    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="content is required")

    meta = session_store.read_session_meta(session_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if meta.get("status") not in {"pending_handoff", "live_agent"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not escalated")

    assigned_agent = meta.get("agent_id")
    if assigned_agent and assigned_agent != payload.agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session claimed by another agent")
    if not assigned_agent:
        meta["agent_id"] = payload.agent_id

    now = datetime.now(timezone.utc)
    message = {
        "role": "agent",
        "content": content,
        "created_at": now.isoformat(),
        "session_id": session_id,
        "agent_id": payload.agent_id,
    }
    session_store.append_message(session_id, message)

    meta.update(
        {
            "status": "live_agent",
            "agent_id": payload.agent_id,
            "last_updated": now.isoformat(),
            "last_response": content,
            "last_agent_message_at": now.isoformat(),
            "message_count": int(meta.get("message_count", 0)) + 1,
        }
    )
    session_store.write_session_meta(session_id, meta)
    session_store.touch_session(session_id)
    session_store.assign_agent_session(session_id, meta.get("agent_id", ""))

    messages = session_store.get_all_messages(session_id)
    return AgentMessageResponse(session_id=session_id, status=meta["status"], messages=messages)
