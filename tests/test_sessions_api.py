from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.deps import get_mongo, get_session_store, get_semantic_cache
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.persistence.redis import RedisKV, RedisSessionStore
from src.persistence.mongo import Mongo
from tests.test_session_memory import FakeMongoClient, FakeRedis
from tests.utils.pinecone_stubs import FakeOpenAI, FakePineconeClient


def _build_session_store() -> RedisSessionStore:
    fake_client = FakeRedis()
    kv = RedisKV("redis://localhost:6379/0", client=fake_client)
    return RedisSessionStore(
        "redis://localhost:6379/0",
        recent_window=5,
        ttl_days=1,
        kv_client=kv,
    )


def _build_mongo() -> Mongo:
    fake_client = FakeMongoClient()
    return Mongo("mongodb://localhost:27017", client=fake_client)


def _build_semantic_cache() -> PineconeSemanticCache:
    return PineconeSemanticCache(
        index_name="test-index",
        namespace="semantic_cache",
        similarity_threshold=0.8,
        pinecone_client=FakePineconeClient(),
        openai_client=FakeOpenAI(),
    )


def test_session_crud_endpoints():
    app = create_app()
    session_store = _build_session_store()
    mongo = _build_mongo()
    semantic_cache = _build_semantic_cache()

    app.dependency_overrides[get_session_store] = lambda: session_store
    app.dependency_overrides[get_mongo] = lambda: mongo
    app.dependency_overrides[get_semantic_cache] = lambda: semantic_cache

    client = TestClient(app)

    create_resp = client.post(
        "/v1/sessions",
        json={"user_id": "alice", "metadata": {"channel": "web"}},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    session_id = created["session_id"]
    assert created["status"] == "active"
    assert "summary" in created

    list_resp = client.get("/v1/sessions", params={"user_id": "alice"})
    assert list_resp.status_code == 200
    sessions = list_resp.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == session_id
    assert sessions[0]["metadata"]["channel"] == "web"
    assert sessions[0]["status"] == "active"

    session_store.append_message(
        session_id,
        {"role": "user", "content": "Hi", "created_at": "2024-01-01T00:00:00+00:00"},
    )
    session_store.append_message(
        session_id,
        {"role": "assistant", "content": "Hello", "created_at": "2024-01-01T00:00:01+00:00"},
    )

    messages_resp = client.get(
        f"/v1/sessions/{session_id}/messages",
        params={"user_id": "alice", "limit": 10},
    )
    assert messages_resp.status_code == 200
    messages_payload = messages_resp.json()
    assert len(messages_payload["messages"]) == 2
    assert messages_payload["messages"][0]["role"] == "user"

    unauthorized = client.get(
        f"/v1/sessions/{session_id}/messages",
        params={"user_id": "bob"},
    )
    assert unauthorized.status_code == 403

    close_resp = client.post(
        f"/v1/sessions/{session_id}/close",
        params={"user_id": "alice"},
        json={"summary": "resolved"},
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    assert session_store.read_session_meta(session_id) is None
    archived_messages = mongo.get_messages(session_id)
    assert len(archived_messages) == 2
    assert archived_messages[0]["role"] == "user"

    closed_list = client.get(
        "/v1/sessions",
        params={"user_id": "alice", "include_closed": True},
    )
    closed_sessions = closed_list.json()["sessions"]
    assert closed_sessions[0]["status"] == "closed"
    assert "summary" in closed_sessions[0]

    # Session ID reuse by another user should conflict
    conflict = client.post(
        "/v1/sessions",
        json={"user_id": "bob", "session_id": session_id},
    )
    assert conflict.status_code == 409
