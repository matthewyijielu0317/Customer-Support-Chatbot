from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:  # pragma: no cover - runtime dependency
    from bson import ObjectId
    from bson.errors import InvalidId
except ImportError:  # pragma: no cover - fallback for tests when bson isn't installed
    from uuid import uuid4

    class InvalidId(Exception):
        """Fallback InvalidId when bson is unavailable."""

        pass

    class ObjectId(str):
        """Minimal ObjectId replacement sufficient for unit tests."""

        def __new__(cls, value: Optional[str] = None):
            return str.__new__(cls, value or uuid4().hex)

try:  # pragma: no cover - runtime dependency
    from pymongo import IndexModel, MongoClient, ReturnDocument
    from pymongo.collection import Collection
except ImportError:  # pragma: no cover - lightweight fallbacks for tests
    Collection = Any  # type: ignore[misc]

    class IndexModel:  # type: ignore[misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.args = args
            self.kwargs = kwargs

    class ReturnDocument(Enum):  # type: ignore[misc]
        BEFORE = "before"
        AFTER = "after"

    class MongoClient:  # type: ignore[misc]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("pymongo is required unless a custom client is provided")


class Mongo:
    def __init__(self, uri: str, db_name: str = "ecomm", *, client: Optional[MongoClient] = None):
        self.client = client or MongoClient(uri)
        self.db = self.client[db_name]

        self._sessions = self.db["sessions"]
        self._messages = self.db["messages"]
        self._summaries = self.db["session_summaries"]

        self._ensure_indexes()

    def conversations(self) -> Collection:
        return self.db["conversations"]

    def logs(self) -> Collection:
        return self.db["retrieval_logs"]

    def sessions(self) -> Collection:
        return self._sessions

    def messages(self) -> Collection:
        return self._messages

    def session_summaries(self) -> Collection:
        return self._summaries

    def _ensure_indexes(self) -> None:
        session_indexes = [
            IndexModel("session_id", unique=True),
            IndexModel([("user_id", 1), ("created_at", -1)]),
        ]
        message_indexes = [
            IndexModel([("session_id", 1), ("created_at", 1)]),
        ]
        summary_indexes = [
            IndexModel("session_id", unique=True),
            IndexModel([("user_id", 1), ("updated_at", -1)]),
        ]

        self._sessions.create_indexes(session_indexes)
        self._messages.create_indexes(message_indexes)
        self._summaries.create_indexes(summary_indexes)

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    def create_session(self, session_id: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = self._utc_now()
        insert_doc: Dict[str, Any] = {
            "created_at": now,
        }

        update_set: Dict[str, Any] = {
            "user_id": user_id,
            "updated_at": now,
            "status": "active",
        }
        if metadata:
            update_set.update(metadata)

        self._sessions.update_one(
            {"session_id": session_id},
            {"$setOnInsert": insert_doc, "$set": update_set},
            upsert=True,
        )

        doc = self._sessions.find_one({"session_id": session_id})
        if doc is None:
            raise RuntimeError(f"Failed to upsert session {session_id}")
        return doc

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        *,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> str:
        ts = created_at or self._utc_now()
        doc: Dict[str, Any] = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": ts,
        }
        if user_id is not None:
            doc["user_id"] = user_id
        if metadata:
            doc["metadata"] = metadata

        result = self._messages.insert_one(doc)
        self._sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": ts, "last_message_at": ts}},
        )
        return str(result.inserted_id)

    def list_sessions(self, user_id: str, limit: int = 20, include_closed: bool = False) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"user_id": user_id}
        if not include_closed:
            query["status"] = {"$ne": "closed"}

        cursor = self._sessions.find(query).sort("updated_at", -1).limit(limit)
        return list(cursor)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.find_one({"session_id": session_id})

    def count_messages(self, session_id: str) -> int:
        return int(self._messages.count_documents({"session_id": session_id}))

    def get_messages(
        self,
        session_id: str,
        *,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"session_id": session_id}
        if cursor:
            cursor_applied = False
            try:
                ts = datetime.fromisoformat(cursor)
                query["created_at"] = {"$lt": ts}
                cursor_applied = True
            except ValueError:
                pass

            if not cursor_applied:
                try:
                    oid = ObjectId(cursor)
                    query["_id"] = {"$lt": oid}
                except (InvalidId, TypeError):
                    pass

        cursor_docs = (
            self._messages.find(query)
            .sort([("created_at", -1), ("_id", -1)])
            .limit(limit)
        )
        docs = list(cursor_docs)
        docs.reverse()
        return docs

    def close_session(
        self,
        session_id: str,
        *,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = self._utc_now()
        update: Dict[str, Any] = {"status": "closed", "closed_at": now, "updated_at": now}
        if metadata:
            update.update(metadata)

        session_doc = self._sessions.find_one_and_update(
            {"session_id": session_id},
            {"$set": update},
            return_document=ReturnDocument.AFTER,
        )

        if summary is not None:
            extra_meta = metadata or {}
            session_user = session_doc.get("user_id") if session_doc else None
            self.upsert_session_summary(
                session_id,
                summary,
                user_id=session_user,
                message_count=None,
                extra_metadata=extra_meta,
            )

    def get_session_summary_doc(self, session_id: str) -> Optional[Dict[str, Any]]:
        doc = self._summaries.find_one({"session_id": session_id})
        return doc

    def get_session_summary(self, session_id: str) -> Optional[str]:
        doc = self.get_session_summary_doc(session_id)
        if not doc:
            return None
        return doc.get("summary")

    def upsert_session_summary(
        self,
        session_id: str,
        summary: str,
        *,
        user_id: Optional[str] = None,
        message_count: Optional[int] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        now = self._utc_now()
        update_doc: Dict[str, Any] = {
            "summary": summary,
            "updated_at": now,
        }
        if message_count is not None:
            update_doc["message_count"] = message_count
        if user_id is not None:
            update_doc["user_id"] = user_id
        if extra_metadata:
            update_doc["metadata"] = extra_metadata

        self._summaries.update_one(
            {"session_id": session_id},
            {
                "$set": update_doc,
                "$setOnInsert": {"session_id": session_id, "created_at": now},
            },
            upsert=True,
        )
        session_update: Dict[str, Any] = {"session_summary": summary, "summary_updated_at": now}
        if user_id is not None:
            session_update.setdefault("user_id", user_id)
        self._sessions.update_one({"session_id": session_id}, {"$set": session_update})
