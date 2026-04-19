from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class CacheRecord:
    value: Any
    expires_at: datetime


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheRecord] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> Any | None:
        record = self._store.get(key)
        if not record:
            return None
        if record.expires_at <= datetime.now(timezone.utc):
            self._store.pop(key, None)
            return None
        return record.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> Any:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        self._store[key] = CacheRecord(value=value, expires_at=expires_at)
        return value


CACHE = InMemoryCache()

