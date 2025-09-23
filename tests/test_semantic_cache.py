from __future__ import annotations

from src.cache.pinecone_semantic import PineconeSemanticCache
from tests.utils.pinecone_stubs import FakeOpenAI, FakePineconeClient


def build_cache() -> PineconeSemanticCache:
    return PineconeSemanticCache(
        index_name="test-index",
        namespace="semantic_cache",
        similarity_threshold=0.75,
        pinecone_client=FakePineconeClient(),
        openai_client=FakeOpenAI(),
    )


def test_semantic_cache_upsert_and_hit():
    cache = build_cache()
    key = cache.build_key("Where is my order")
    cache.upsert(
        key,
        {
            "answer": "Your order is on the way",
            "citations": [{"source": "doc#1"}],
            "query_type": "order_lookup",
        },
        query="Where is my order?",
    )

    hit = cache.similar("Where is my order?")
    assert hit is not None
    assert hit["answer"] == "Your order is on the way"
    assert hit["citations"][0]["source"] == "doc#1"
    assert hit["query_type"] == "order_lookup"


def test_semantic_cache_respects_user_scope():
    cache = build_cache()
    cache.upsert(
        cache.build_key("Hi"),
        {"answer": "hello"},
        query="Hi",
    )

    assert cache.similar("Hi") is not None
