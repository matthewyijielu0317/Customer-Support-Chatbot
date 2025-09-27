from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.deps import get_session_store, get_mongo, get_semantic_cache
from tests.test_chat_flow import _build_session_store, _build_mongo, _build_semantic_cache


def test_escalation_claim_and_message_flow():
    app = create_app()
    session_store = _build_session_store()
    mongo = _build_mongo()
    semantic_cache = _build_semantic_cache()

    app.dependency_overrides[get_session_store] = lambda: session_store
    app.dependency_overrides[get_mongo] = lambda: mongo
    app.dependency_overrides[get_semantic_cache] = lambda: semantic_cache

    session_id = "session-escalated"
    now = datetime.now(timezone.utc).isoformat()
    meta = {
        "user_id": "customer@example.com",
        "status": "pending_handoff",
        "created_at": now,
        "last_updated": now,
        "escalated_at": now,
        "escalation_reason": "User explicitly requested a human",
    }
    session_store.write_session_meta(session_id, meta)
    session_store.register_session(session_id, "customer@example.com")
    session_store.enqueue_escalation(session_id)

    client = TestClient(app)

    list_resp = client.get("/v1/escalations")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["escalations"][0]["session_id"] == session_id
    assert data["escalations"][0]["status"] == "pending_handoff"

    claim_resp = client.post(
        f"/v1/escalations/{session_id}/claim",
        json={"agent_id": "agent@example.com"},
    )
    assert claim_resp.status_code == 200
    claim_data = claim_resp.json()
    assert claim_data["status"] == "live_agent"
    assert claim_data["agent_id"] == "agent@example.com"
    assert session_store.list_escalations() == []

    agent_queue = client.get("/v1/escalations", params={"agent_id": "agent@example.com"})
    assert agent_queue.status_code == 200
    agent_data = agent_queue.json()
    assert agent_data["escalations"][0]["session_id"] == session_id
    assert agent_data["escalations"][0]["agent_id"] == "agent@example.com"

    message_resp = client.post(
        f"/v1/escalations/{session_id}/messages",
        json={"agent_id": "agent@example.com", "content": "Hello, I'm here to help."},
    )
    assert message_resp.status_code == 200
    body = message_resp.json()
    assert body["status"] == "live_agent"
    roles = [msg["role"] for msg in body["messages"]]
    assert "agent" in roles

    detail = client.get(f"/v1/escalations/{session_id}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["escalation"]["agent_id"] == "agent@example.com"

    conflict = client.post(
        f"/v1/escalations/{session_id}/messages",
        json={"agent_id": "other@example.com", "content": "Hi"},
    )
    assert conflict.status_code == 403

    close_resp = client.post(
        f"/v1/sessions/{session_id}/close",
        params={"user_id": "customer@example.com"},
        json={"summary": "closed by test"},
    )
    assert close_resp.status_code == 200
    assert session_store.list_escalations() == []
    assert session_store.list_agent_sessions("agent@example.com") == []
