from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_mongo, get_session_store
from src.persistence.mongo import Mongo
from src.persistence.redis import RedisSessionStore
from src.utils.summarize import summarize_messages
from src.config.settings import settings
from src.utils.ids import generate_readable_session_id


router = APIRouter(tags=["sessions"])


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return parsed.isoformat()


def _parse_datetime(value: Optional[Any]) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _serialize_session(doc: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "session_id": doc.get("session_id"),
        "user_id": doc.get("user_id"),
        "status": doc.get("status"),
        "created_at": _serialize_datetime(doc.get("created_at")),
        "updated_at": _serialize_datetime(doc.get("updated_at")),
        "closed_at": _serialize_datetime(doc.get("closed_at")),
        "last_message_at": _serialize_datetime(doc.get("last_message_at")),
        "summary": doc.get("session_summary"),
        "summary_updated_at": _serialize_datetime(doc.get("summary_updated_at")),
    }
    excluded = {"_id", "session_summary", "summary_updated_at"}
    metadata = {k: v for k, v in doc.items() if k not in out and k not in excluded}
    if metadata:
        out["metadata"] = metadata
    return out


def _serialize_message(doc: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
        "session_id": doc.get("session_id"),
        "role": doc.get("role"),
        "content": doc.get("content"),
        "created_at": _serialize_datetime(doc.get("created_at")),
    }
    if doc.get("user_id") is not None:
        out["user_id"] = doc.get("user_id")
    if doc.get("metadata") is not None:
        out["metadata"] = doc.get("metadata")
    return out


class SessionCreateRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    created_at: Optional[str] = None
    user_id: Optional[str] = None
    summary: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: List[Dict[str, Any]] = Field(default_factory=list)


class SessionMessagesResponse(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    next_cursor: Optional[str] = None


class SessionCloseRequest(BaseModel):
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionCloseResponse(BaseModel):
    session_id: str
    status: str
    closed_at: Optional[str] = None


@router.post("/sessions", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    payload: SessionCreateRequest,
    session_store: RedisSessionStore = Depends(get_session_store),
    mongo: Mongo = Depends(get_mongo),
) -> SessionCreateResponse:
    if not payload.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

    session_id = payload.session_id or generate_readable_session_id(payload.user_id)
    redis_meta = session_store.read_session_meta(session_id)
    if redis_meta and redis_meta.get("user_id") not in (None, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session ID already in use")

    existing = mongo.get_session(session_id)
    if existing and existing.get("user_id") not in (None, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session ID already in use")

    now = datetime.now(timezone.utc)
    meta = {
        "user_id": payload.user_id,
        "status": "active",
        "created_at": now.isoformat(),
        **({} if not payload.metadata else payload.metadata),
        "message_count": 0,
        "summary_message_count": 0,
    }
    session_store.write_session_meta(session_id, meta)
    session_store.register_session(session_id, payload.user_id)

    return SessionCreateResponse(
        session_id=session_id,
        status="active",
        created_at=_serialize_datetime(now),
        user_id=payload.user_id,
        summary=None,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions_endpoint(
    user_id: str = Query(..., description="Filter by user id"),
    limit: int = Query(20, ge=1, le=100),
    include_closed: bool = Query(False),
    session_store: RedisSessionStore = Depends(get_session_store),
    mongo: Mongo = Depends(get_mongo),
) -> SessionListResponse:
    active_metas = session_store.list_sessions(user_id)
    active_docs: List[Dict[str, Any]] = []
    for meta in active_metas[:limit]:
        session_id = meta.get("session_id")
        created_at = _parse_datetime(meta.get("created_at"))
        last_updated = _parse_datetime(meta.get("last_updated"))
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "status": meta.get("status", "active"),
            "created_at": created_at,
            "updated_at": last_updated,
            "closed_at": None,
            "last_message_at": last_updated,
            "session_summary": meta.get("session_summary"),
            "summary_updated_at": last_updated,
        }
        extra_keys = {
            k: v
            for k, v in meta.items()
            if k
            not in {
                "session_id",
                "user_id",
                "status",
                "created_at",
                "last_updated",
                "updated_at",
                "closed_at",
                "session_summary",
                "summary_message_count",
                "message_count",
            }
        }
        doc.update(extra_keys)
        active_docs.append(doc)

    remaining = max(limit - len(active_docs), 0)
    closed_docs: List[Dict[str, Any]] = []
    if include_closed and remaining >= 0:
        closed = mongo.list_sessions(user_id, limit=remaining, include_closed=True)
        closed_docs = closed

    combined = [_serialize_session(doc) for doc in active_docs]
    if include_closed:
        combined.extend(_serialize_session(doc) for doc in closed_docs)

    return SessionListResponse(sessions=combined[:limit])


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages_endpoint(
    session_id: str,
    user_id: str = Query(..., description="Must match the session owner"),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None),
    mongo: Mongo = Depends(get_mongo),
    session_store: RedisSessionStore = Depends(get_session_store),
) -> SessionMessagesResponse:
    meta = session_store.read_session_meta(session_id)
    if meta:
        stored_user = meta.get("user_id")
        if stored_user != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")
        history = session_store.get_all_messages(session_id)
        if limit:
            history = history[-limit:]
        serialized = [
            {
                "id": None,
                "session_id": session_id,
                "role": msg.get("role"),
                "content": msg.get("content"),
                "created_at": msg.get("created_at"),
            }
            for msg in history
        ]
        return SessionMessagesResponse(messages=serialized, next_cursor=None)

    session_doc = mongo.get_session(session_id)
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_doc.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")

    messages = mongo.get_messages(session_id, limit=limit, cursor=cursor)
    serialized = [_serialize_message(doc) for doc in messages]
    next_cursor = None
    if len(messages) == limit:
        tail = messages[0]
        created_at = tail.get("created_at")
        if isinstance(created_at, datetime):
            next_cursor = created_at.isoformat()
        else:
            msg_id = tail.get("_id")
            if msg_id is not None:
                next_cursor = str(msg_id)
    return SessionMessagesResponse(messages=serialized, next_cursor=next_cursor)


@router.post("/sessions/{session_id}/close", response_model=SessionCloseResponse)
async def close_session_endpoint(
    session_id: str,
    payload: SessionCloseRequest,
    user_id: str = Query(..., description="Must match the session owner"),
    mongo: Mongo = Depends(get_mongo),
    session_store: RedisSessionStore = Depends(get_session_store),
) -> SessionCloseResponse:
    meta = session_store.read_session_meta(session_id)
    if meta:
        stored_user = meta.get("user_id")
        if stored_user != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")
        history = session_store.get_all_messages(session_id)
        agent_id = meta.get("agent_id")
        summary_text = payload.summary or meta.get("session_summary")
        if not summary_text and history:
            summary_payload = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                for msg in history
                if msg.get("content")
            ]
            if summary_payload:
                summary_text = summarize_messages(
                    summary_payload,
                    max_length=settings.session_summary_max_chars,
                )

        meta_metadata = {
            k: v
            for k, v in meta.items()
            if k
            not in {
                "session_id",
                "user_id",
                "status",
                "created_at",
                "last_updated",
                "session_summary",
                "summary_message_count",
                "message_count",
            }
        }
        combined_metadata = {**meta_metadata, **(payload.metadata or {})}
        mongo.create_session(session_id, user_id, metadata=combined_metadata or None)
        for msg in history:
            created_at = None
            raw_ts = msg.get("created_at")
            if isinstance(raw_ts, str):
                try:
                    created_at = datetime.fromisoformat(raw_ts)
                except ValueError:
                    created_at = None
            mongo.append_message(
                session_id,
                msg.get("role", "user"),
                msg.get("content", ""),
                user_id=user_id,
                created_at=created_at,
            )
        if summary_text:
            mongo.upsert_session_summary(
                session_id,
                summary_text,
                user_id=user_id,
                message_count=len(history),
            )
        mongo.close_session(session_id, summary=summary_text, metadata=combined_metadata or None)
        session_store.dequeue_escalation(session_id)
        if agent_id:
            session_store.unassign_agent_session(session_id, agent_id)
        session_store.delete_session(session_id)
        session_store.unregister_session(session_id, user_id)
        updated = mongo.get_session(session_id)
        closed_at = _serialize_datetime(updated.get("closed_at")) if updated else None
        return SessionCloseResponse(session_id=session_id, status="closed", closed_at=closed_at)

    session_doc = mongo.get_session(session_id)
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_doc.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")

    mongo.close_session(session_id, summary=payload.summary, metadata=payload.metadata or None)
    updated = mongo.get_session(session_id)
    closed_at = _serialize_datetime(updated.get("closed_at")) if updated else None
    return SessionCloseResponse(session_id=session_id, status="closed", closed_at=closed_at)
