from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_mongo, get_session_store
from src.cache.redis_kv import RedisSessionStore
from src.db.mongo import Mongo


router = APIRouter(tags=["sessions"])


def _serialize_datetime(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


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

    session_id = payload.session_id or str(uuid4())
    existing = mongo.get_session(session_id)
    if existing and existing.get("user_id") not in (None, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session ID already in use")

    doc = mongo.create_session(session_id, payload.user_id, metadata=payload.metadata or None)

    session_store.write_session_meta(
        session_id,
        {
            "user_id": payload.user_id,
            **({} if not payload.metadata else payload.metadata),
        },
    )

    return SessionCreateResponse(
        session_id=session_id,
        status=str(doc.get("status", "active")),
        created_at=_serialize_datetime(doc.get("created_at")),
        user_id=doc.get("user_id"),
        summary=doc.get("session_summary"),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions_endpoint(
    user_id: str = Query(..., description="Filter by user id"),
    limit: int = Query(20, ge=1, le=100),
    include_closed: bool = Query(False),
    mongo: Mongo = Depends(get_mongo),
) -> SessionListResponse:
    sessions = mongo.list_sessions(user_id, limit=limit, include_closed=include_closed)
    return SessionListResponse(sessions=[_serialize_session(doc) for doc in sessions])


@router.get("/sessions/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages_endpoint(
    session_id: str,
    user_id: str = Query(..., description="Must match the session owner"),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[str] = Query(None),
    mongo: Mongo = Depends(get_mongo),
) -> SessionMessagesResponse:
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
    session_doc = mongo.get_session(session_id)
    if not session_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session_doc.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to user")

    mongo.close_session(session_id, summary=payload.summary, metadata=payload.metadata or None)
    session_store.touch_session(session_id)

    updated = mongo.get_session(session_id)
    closed_at = _serialize_datetime(updated.get("closed_at")) if updated else None

    return SessionCloseResponse(session_id=session_id, status="closed", closed_at=closed_at)
