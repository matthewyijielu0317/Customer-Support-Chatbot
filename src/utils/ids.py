import hashlib


def cache_key_for_query(q: str) -> str:
    return hashlib.sha256(q.encode("utf-8")).hexdigest()


