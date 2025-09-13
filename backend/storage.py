from __future__ import annotations

import os
from urllib.parse import urlparse
from typing import Optional

import redis

from .config import get_settings


class RedisStorage:
    def __init__(self):
        settings = get_settings()
        # Prefer broker DB for lightweight key-value, else backend
        url = settings.CELERY_BROKER_URL or settings.CELERY_RESULT_BACKEND
        parsed = urlparse(url)
        db = int((parsed.path or "/0").lstrip("/"))
        self.r = redis.Redis(host=parsed.hostname or "localhost", port=parsed.port or 6379, db=db, username=parsed.username, password=parsed.password, decode_responses=True)

    def set_watcher(self, key: str, task_id: str):
        self.r.hset("watchers", key, task_id)

    def get_watcher(self, key: str) -> Optional[str]:
        return self.r.hget("watchers", key)

    def del_watcher(self, key: str) -> int:
        return self.r.hdel("watchers", key)

    def list_watchers(self) -> dict:
        return self.r.hgetall("watchers")

