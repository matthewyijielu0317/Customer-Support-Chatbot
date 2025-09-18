from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional

from src.cache.redis_kv import RedisKV, RedisSessionStore
from src.db.mongo import Mongo, ObjectId, ReturnDocument


class FakePipeline:
    def __init__(self, client: "FakeRedis") -> None:
        self.client = client

    def lpush(self, key: str, value: str) -> "FakePipeline":
        self.client.lpush(key, value)
        return self

    def ltrim(self, key: str, start: int, end: int) -> "FakePipeline":
        self.client.ltrim(key, start, end)
        return self

    def expire(self, key: str, ttl: int) -> "FakePipeline":
        self.client.expire(key, ttl)
        return self

    def execute(self) -> List[Any]:
        return []

    def __enter__(self) -> "FakePipeline":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # No transactional behaviour to emulate
        return None


class FakeRedis:
    def __init__(self) -> None:
        self.kv: Dict[str, str] = {}
        self.lists: Dict[str, List[str]] = {}
        self.expirations: Dict[str, int] = {}
        self.sets: Dict[str, set] = {}

    # Redis client interface -------------------------------------------------
    def get(self, key: str) -> Optional[str]:
        return self.kv.get(key)

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        self.kv[key] = value
        if ex is not None:
            self.expirations[key] = ex

    def lpush(self, key: str, value: str) -> int:
        items = self.lists.setdefault(key, [])
        items.insert(0, value)
        return len(items)

    def ltrim(self, key: str, start: int, end: int) -> None:
        items = self.lists.get(key, [])
        if end == -1:
            end = len(items) - 1
        end = min(end, len(items) - 1)
        self.lists[key] = items[start : end + 1] if items else []

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        items = self.lists.get(key, [])
        if end == -1:
            end = len(items) - 1
        if end < start:
            return []
        return items[start : end + 1]

    def expire(self, key: str, ttl: int) -> None:
        self.expirations[key] = ttl

    def delete(self, *keys: str) -> None:
        for key in keys:
            self.kv.pop(key, None)
            self.lists.pop(key, None)
            self.expirations.pop(key, None)
            self.sets.pop(key, None)
            # remove from sets containing key entries
        for s_key, values in list(self.sets.items()):
            if not values:
                continue
            before = len(values)
            values.difference_update(keys)
            if not values or len(values) != before:
                self.sets[s_key] = values

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    def sadd(self, key: str, *values: str) -> int:
        current = self.sets.setdefault(key, set())
        before = len(current)
        current.update(values)
        return len(current) - before

    def smembers(self, key: str):
        return set(self.sets.get(key, set()))

    def srem(self, key: str, value: str) -> None:
        values = self.sets.get(key)
        if values is not None:
            values.discard(value)

    # Compatibility with FastAPI teardown ------------------------------------
    def close(self) -> None:
        pass


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, key, direction: int | None = None) -> "FakeCursor":
        if isinstance(key, list):
            for field, dir_value in reversed(key):
                reverse = dir_value < 0
                self._docs.sort(key=lambda doc, f=field: doc.get(f), reverse=reverse)
            return self

        if direction is None:
            raise ValueError("Direction is required when key is not a list")

        reverse = direction < 0
        self._docs.sort(key=lambda doc: doc.get(key), reverse=reverse)
        return self

    def limit(self, count: int) -> "FakeCursor":
        if count >= 0:
            self._docs = self._docs[:count]
        return self

    def __iter__(self):
        for doc in self._docs:
            yield deepcopy(doc)


class FakeCollection:
    def __init__(self) -> None:
        self.docs: List[Dict[str, Any]] = []

    # Indexes ----------------------------------------------------------------
    def create_indexes(self, indexes: Iterable[Any]) -> None:
        return None

    # Helpers ----------------------------------------------------------------
    def _clone(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return deepcopy(doc)

    def _matches(self, doc: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        for key, expected in criteria.items():
            value = doc.get(key)
            if isinstance(expected, dict):
                if "$ne" in expected and value == expected["$ne"]:
                    return False
                if "$lt" in expected:
                    compare = expected["$lt"]
                    if value is None or not value < compare:
                        return False
            else:
                if value != expected:
                    return False
        return True

    def _find_doc(self, criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.docs:
            if self._matches(doc, criteria):
                return doc
        return None

    def _apply_update(self, doc: Dict[str, Any], update: Dict[str, Any]) -> None:
        for op, payload in update.items():
            if op == "$set":
                for key, value in payload.items():
                    doc[key] = value
            elif op == "$setOnInsert":
                for key, value in payload.items():
                    doc.setdefault(key, value)
            else:
                raise NotImplementedError(f"Unsupported update operator: {op}")

    # CRUD -------------------------------------------------------------------
    def insert_one(self, doc: Dict[str, Any]):
        record = self._clone(doc)
        record.setdefault("_id", ObjectId())
        self.docs.append(record)
        return SimpleNamespace(inserted_id=record["_id"])

    def find_one(self, criteria: Dict[str, Any]):
        doc = self._find_doc(criteria)
        return self._clone(doc) if doc else None

    def find_one_and_update(self, criteria: Dict[str, Any], update: Dict[str, Any], *, return_document: ReturnDocument = ReturnDocument.BEFORE):
        doc = self._find_doc(criteria)
        if doc is None:
            return None
        if return_document == ReturnDocument.BEFORE:
            original = self._clone(doc)
            self._apply_update(doc, update)
            return original
        self._apply_update(doc, update)
        return self._clone(doc)

    def update_one(self, criteria: Dict[str, Any], update: Dict[str, Any], *, upsert: bool = False):
        doc = self._find_doc(criteria)
        if doc:
            self._apply_update(doc, update)
            return SimpleNamespace(matched_count=1, upserted_id=None)
        if not upsert:
            return SimpleNamespace(matched_count=0, upserted_id=None)

        record: Dict[str, Any] = {
            key: value
            for key, value in criteria.items()
            if not isinstance(value, dict)
        }
        if "$setOnInsert" in update:
            record.update(self._clone(update["$setOnInsert"]))
        record.setdefault("_id", ObjectId())
        self.docs.append(record)
        remaining = {op: payload for op, payload in update.items() if op != "$setOnInsert"}
        if remaining:
            self._apply_update(record, remaining)
        return SimpleNamespace(matched_count=0, upserted_id=record["_id"])

    def find(self, criteria: Dict[str, Any]):
        results = [self._clone(doc) for doc in self.docs if self._matches(doc, criteria)]
        return FakeCursor(results)

    def count_documents(self, criteria: Dict[str, Any]) -> int:
        return sum(1 for doc in self.docs if self._matches(doc, criteria))


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: Dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


class FakeAdmin:
    def command(self, _: str) -> Dict[str, Any]:
        return {"ok": 1}


class FakeMongoClient:
    def __init__(self) -> None:
        self.databases: Dict[str, FakeDatabase] = {}
        self.admin = FakeAdmin()

    def __getitem__(self, name: str) -> FakeDatabase:
        if name not in self.databases:
            self.databases[name] = FakeDatabase()
        return self.databases[name]

    def close(self) -> None:
        self.databases.clear()


def _build_session_store(recent_window: int = 3, ttl_days: int = 1) -> RedisSessionStore:
    fake_client = FakeRedis()
    kv = RedisKV("redis://localhost:6379/0", client=fake_client)
    store = RedisSessionStore(
        "redis://localhost:6379/0",
        recent_window=recent_window,
        ttl_days=ttl_days,
        kv_client=kv,
    )
    return store


def test_redis_session_store_keeps_recent_messages():
    store = _build_session_store(recent_window=3, ttl_days=1)
    redis_client: FakeRedis = store.kv.client  # type: ignore[assignment]

    store.write_session_meta("sess-1", {"user_id": "user-1"})
    meta = store.read_session_meta("sess-1")
    assert meta is not None
    assert meta["user_id"] == "user-1"
    assert redis_client.expirations["session:sess-1"] == 86400

    for idx in range(4):
        store.append_message(
            "sess-1",
            {"role": "user" if idx % 2 == 0 else "assistant", "content": f"msg-{idx}"},
        )

    recent = store.get_recent_messages("sess-1")
    assert [msg["content"] for msg in recent] == ["msg-1", "msg-2", "msg-3"]
    assert redis_client.expirations["session:sess-1:messages"] == 86400

    store.delete_session("sess-1")
    assert store.read_session_meta("sess-1") is None
    assert redis_client.lists.get("session:sess-1:messages") is None


def test_redis_touch_session_refreshes_ttl():
    store = _build_session_store(recent_window=2, ttl_days=2)
    redis_client: FakeRedis = store.kv.client  # type: ignore[assignment]

    store.write_session_meta("sess-2", {"user_id": "u"})
    store.append_message("sess-2", {"role": "user", "content": "hello"})

    # Simulate TTL decay then touch to refresh
    redis_client.expirations["session:sess-2"] = 10
    redis_client.expirations["session:sess-2:messages"] = 10

    store.touch_session("sess-2")
    assert redis_client.expirations["session:sess-2"] == 172800
    assert redis_client.expirations["session:sess-2:messages"] == 172800


def _build_mongo() -> Mongo:
    fake_client = FakeMongoClient()
    return Mongo("mongodb://localhost:27017", client=fake_client)


def test_mongo_session_crud_and_messages():
    mongo = _build_mongo()

    session = mongo.create_session("sess-A", "user-123", metadata={"channel": "support"})
    assert session["status"] == "active"
    assert session["user_id"] == "user-123"
    fetched = mongo.get_session("sess-A")
    assert fetched is not None and fetched["session_id"] == "sess-A"

    mongo.append_message("sess-A", "user", "Hi", user_id="user-123")
    mongo.append_message("sess-A", "assistant", "Hello!", user_id="user-123")

    history = mongo.get_messages("sess-A")
    assert [msg["role"] for msg in history] == ["user", "assistant"]

    # Cursor pagination should return only earlier messages
    cursor = history[-1]["created_at"].isoformat()
    earlier = mongo.get_messages("sess-A", cursor=cursor)
    assert len(earlier) == 1
    assert earlier[0]["content"] == "Hi"

    open_sessions = mongo.list_sessions("user-123")
    assert open_sessions[0]["session_id"] == "sess-A"

    mongo.close_session("sess-A", summary="Issue resolved")

    assert mongo.list_sessions("user-123") == []
    closed = mongo.list_sessions("user-123", include_closed=True)
    assert closed[0]["status"] == "closed"

    summary_doc = mongo.session_summaries().find_one({"session_id": "sess-A"})
    assert summary_doc is not None
    assert summary_doc["summary"] == "Issue resolved"
    assert summary_doc["user_id"] == "user-123"
    assert mongo.get_session_summary("sess-A") == "Issue resolved"
