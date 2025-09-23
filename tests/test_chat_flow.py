from __future__ import annotations

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api.main import create_app
from app.api.deps import get_mongo, get_session_store, get_semantic_cache
from app.api.routes import chat as chat_module
from src.cache.pinecone_semantic import PineconeSemanticCache
from src.persistence.redis import RedisKV, RedisSessionStore
from src.graph.state import Citation
from src.persistence.mongo import Mongo
from tests.test_session_memory import FakeMongoClient, FakeRedis
from tests.utils.pinecone_stubs import FakeOpenAI, FakePineconeClient


class DummyGraph:
    def __init__(self) -> None:
        self.states = []

    def invoke(self, state):  # type: ignore[no-untyped-def]
        # Simulate router decision: docs only
        state.query_type = "policy_only"
        state.should_retrieve_docs = True
        state.should_retrieve_sql = False

        cache = getattr(state, "semantic_cache", None)
        if cache:
            hit = cache.similar(state.query)
            if hit:
                state.cache_hit = True
                state.answer = hit["answer"]
                state.citations = [Citation(source="synthetic", title="synthetic")]
                return state

        state.cache_hit = False
        state.should_cache = True
        state.cache_key = PineconeSemanticCache.build_key(state.query)
        state.answer = f"Echo: {state.query}"
        state.citations = [Citation(source="synthetic://doc", title="synthetic")]
        state.trace_id = "dummy-trace"

        cache = getattr(state, "semantic_cache", None)
        if cache and state.cache_key:
            cache.upsert(
                state.cache_key,
                {
                    "answer": state.answer,
                    "citations": [c.model_dump() for c in state.citations],
                    "query_type": state.query_type,
                    "trace_id": state.trace_id,
                },
                query=state.query,
            )

        self.states.append(state)
        return state


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


def test_chat_endpoint_creates_and_updates_session():
    with patch("src.utils.summarize.summarize_messages", return_value="summary"):
        app = create_app()
        graph = DummyGraph()
        chat_module._graph = graph

        session_store = _build_session_store()
        mongo = _build_mongo()
        semantic_cache = _build_semantic_cache()

        app.dependency_overrides[get_session_store] = lambda: session_store
        app.dependency_overrides[get_mongo] = lambda: mongo
        app.dependency_overrides[get_semantic_cache] = lambda: semantic_cache

        client = TestClient(app)

        query = "What is the return policy?"
        response = client.post("/v1/chat", json={"user_id": "alice", "query": query})
        assert response.status_code == 200
        payload = response.json()
        assert payload["answer"] == f"Echo: {query}"
        assert payload["session_id"]
        assert payload["trace_id"] == "dummy-trace"
        assert payload["cache_hit"] is False

        session_id = payload["session_id"]
        assert graph.states[0].user_id == "alice"
        assert graph.states[0].session_id == session_id
        assert len(graph.states[0].recent_messages) == 1
        assert graph.states[0].recent_messages[0]["role"] == "assistant"

        redis_messages = session_store.get_recent_messages(session_id)
        assert len(redis_messages) == 3
        assert redis_messages[0]["role"] == "assistant"
        assert redis_messages[0]["content"] == "Hello Alice, how can I assist you today!"
        assert redis_messages[1]["role"] == "user"
        assert redis_messages[2]["role"] == "assistant"

        mongo_history = mongo.get_messages(session_id)
        assert mongo_history == []

        response_two = client.post(
            "/v1/chat",
            json={"user_id": "alice", "session_id": session_id, "query": query},
        )
        assert response_two.status_code == 200
        payload_two = response_two.json()
        assert payload_two["session_id"] == session_id
        assert payload_two["cache_hit"] is True
        assert len(graph.states) == 1

        redis_messages_after = session_store.get_recent_messages(session_id)
        assert len(redis_messages_after) == 5

        history_after = mongo.get_messages(session_id)
        assert history_after == []

        # Session reuse by different user should be denied
        forbidden = client.post(
            "/v1/chat",
            json={"user_id": "bob", "session_id": session_id, "query": "Hi"},
        )
        assert forbidden.status_code == 403
