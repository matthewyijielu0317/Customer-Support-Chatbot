import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set

try:  # pragma: no cover - runtime dependency
    import redis
except ImportError:  # pragma: no cover - lightweight fallback for tests
    class _MissingPipeline:
        ...

    class _MissingRedis:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("redis-py is required unless a client override is supplied")

        @classmethod
        def from_url(cls, *args: Any, **kwargs: Any) -> "_MissingRedis":
            raise RuntimeError("redis-py is required unless a client override is supplied")

    redis = SimpleNamespace(Redis=_MissingRedis, client=SimpleNamespace(Pipeline=_MissingPipeline))  # type: ignore[attr-defined]


def _json_default(obj: Any) -> str:
    """Serialize datetimes to ISO strings for Redis payloads."""

    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


class RedisKV:
    """Thin wrapper for Redis key-value operations (sessions, rate limit)."""

    def __init__(self, url: str, client: Optional[redis.Redis] = None):
        self.client = client or redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.client.set(key, value, ex=ex)

    def lpush(self, key: str, *values: str) -> int:
        return self.client.lpush(key, *values)

    def ltrim(self, key: str, start: int, end: int) -> None:
        self.client.ltrim(key, start, end)

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        return list(self.client.lrange(key, start, end))

    def expire(self, key: str, ttl_seconds: int) -> None:
        self.client.expire(key, ttl_seconds)

    def delete(self, *keys: str) -> None:
        if keys:
            self.client.delete(*keys)

    def pipeline(self) -> redis.client.Pipeline:
        return self.client.pipeline()

    def sadd(self, key: str, *values: str) -> int:
        return self.client.sadd(key, *values)

    def smembers(self, key: str) -> Set[str]:
        members = self.client.smembers(key)
        # redis-py returns set of bytes/str depending on decode
        if isinstance(members, set):
            return {str(m) for m in members}
        return set()

    def srem(self, key: str, value: str) -> None:
        self.client.srem(key, value)


class RedisSessionStore:
    """Redis-backed storage for session metadata and recent message buffers."""

    def __init__(
        self,
        url: str,
        *,
        recent_window: int,
        ttl_days: int,
        kv_client: Optional[RedisKV] = None,
    ) -> None:
        self.kv = kv_client or RedisKV(url)
        self.recent_window = max(recent_window, 0)
        ttl_seconds = int(ttl_days * 86400)
        self.ttl_seconds = ttl_seconds if ttl_seconds > 0 else 0

    @staticmethod
    def _meta_key(session_id: str) -> str:
        return f"session:{session_id}"

    @classmethod
    def _messages_key(cls, session_id: str) -> str:
        return f"{cls._meta_key(session_id)}:messages"

    @staticmethod
    def _escalations_key() -> str:
        return "escalations:pending"

    @staticmethod
    def _agent_sessions_key(agent_id: str) -> str:
        return f"agent_sessions:{agent_id}"

    def write_session_meta(self, session_id: str, data: Dict[str, Any]) -> None:
        meta = {**data, "session_id": session_id}
        meta.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        payload = json.dumps(meta, default=_json_default)
        if self.ttl_seconds:
            self.kv.set(self._meta_key(session_id), payload, ex=self.ttl_seconds)
        else:
            self.kv.set(self._meta_key(session_id), payload)

    def read_session_meta(self, session_id: str) -> Optional[Dict[str, Any]]:
        raw = self.kv.get(self._meta_key(session_id))
        if raw is None:
            return None
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return data

    def append_message(self, session_id: str, message: Dict[str, Any]) -> None:
        serialized = json.dumps(message, default=_json_default)
        messages_key = self._messages_key(session_id)
        meta_key = self._meta_key(session_id)
        with self.kv.pipeline() as pipe:
            pipe.lpush(messages_key, serialized)
            if self.ttl_seconds:
                pipe.expire(messages_key, self.ttl_seconds)
                pipe.expire(meta_key, self.ttl_seconds)
            pipe.execute()

    def get_recent_messages(self, session_id: str) -> List[Dict[str, Any]]:
        end = self.recent_window - 1 if self.recent_window else -1
        raw_items = self.kv.lrange(self._messages_key(session_id), 0, end)
        messages: List[Dict[str, Any]] = []
        for item in raw_items:
            try:
                messages.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        # Redis LPUSH stores newest first; reverse to chronological order
        return list(reversed(messages))

    def get_all_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if limit is not None and limit <= 0:
            return []
        end = -1 if limit is None else limit - 1
        raw_items = self.kv.lrange(self._messages_key(session_id), 0, end)
        messages: List[Dict[str, Any]] = []
        for item in raw_items:
            try:
                messages.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return list(reversed(messages))

    @staticmethod
    def _user_sessions_key(user_id: str) -> str:
        return f"user_sessions:{user_id}"

    def register_session(self, session_id: str, user_id: str) -> None:
        if not user_id:
            return
        self.kv.sadd(self._user_sessions_key(user_id), session_id)

    def unregister_session(self, session_id: str, user_id: str) -> None:
        if not user_id:
            return
        self.kv.srem(self._user_sessions_key(user_id), session_id)

    def list_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        session_ids = sorted(self.kv.smembers(self._user_sessions_key(user_id)))
        metas: List[Dict[str, Any]] = []
        for sid in session_ids:
            meta = self.read_session_meta(sid)
            if meta:
                metas.append(meta)
        return metas

    def touch_session(self, session_id: str) -> None:
        if not self.ttl_seconds:
            return
        messages_key = self._messages_key(session_id)
        meta_key = self._meta_key(session_id)
        with self.kv.pipeline() as pipe:
            pipe.expire(messages_key, self.ttl_seconds)
            pipe.expire(meta_key, self.ttl_seconds)
            pipe.execute()

    def delete_session(self, session_id: str) -> None:
        self.kv.delete(self._meta_key(session_id), self._messages_key(session_id))

    # Escalation queue helpers -----------------------------------------------

    def enqueue_escalation(self, session_id: str) -> None:
        self.kv.sadd(self._escalations_key(), session_id)

    def dequeue_escalation(self, session_id: str) -> None:
        self.kv.srem(self._escalations_key(), session_id)

    def list_escalations(self) -> List[Dict[str, Any]]:
        session_ids = sorted(self.kv.smembers(self._escalations_key()))
        metas: List[Dict[str, Any]] = []
        for sid in session_ids:
            meta = self.read_session_meta(sid)
            if meta:
                metas.append(meta)
        return metas

    def assign_agent_session(self, session_id: str, agent_id: str) -> None:
        if not agent_id:
            return
        self.kv.sadd(self._agent_sessions_key(agent_id), session_id)

    def unassign_agent_session(self, session_id: str, agent_id: str) -> None:
        if not agent_id:
            return
        self.kv.srem(self._agent_sessions_key(agent_id), session_id)

    def list_agent_sessions(self, agent_id: str) -> List[Dict[str, Any]]:
        if not agent_id:
            return []
        session_ids = sorted(self.kv.smembers(self._agent_sessions_key(agent_id)))
        metas: List[Dict[str, Any]] = []
        for sid in session_ids:
            meta = self.read_session_meta(sid)
            if meta:
                metas.append(meta)
        return metas
