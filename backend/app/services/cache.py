import json
from pathlib import Path
from typing import Any, Optional

from app.config import get_settings


class Cache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis_client = self._create_redis()
        self.cache_dir = Path(self.settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Any]:
        if self.redis_client:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None

        path = self._path_for_key(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, key: str, value: Any, ttl_seconds: int = 86400) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=_json_default)
        if self.redis_client:
            self.redis_client.setex(key, ttl_seconds, payload)
            return
        self._path_for_key(key).write_text(payload, encoding="utf-8")

    def _path_for_key(self, key: str) -> Path:
        safe_key = key.replace(":", "_").replace("/", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _create_redis(self):
        if not self.settings.redis_url:
            return None
        try:
            import redis

            client = redis.from_url(self.settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None


def _json_default(value):
    if hasattr(value, "model_dump"):
        return value.model_dump()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
