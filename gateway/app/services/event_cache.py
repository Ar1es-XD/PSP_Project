import json
from typing import Optional

import redis.asyncio as redis


class EventCache:
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def set_last(self, simulation_id: str, payload: dict) -> None:
        await self._client.set(self._key(simulation_id), json.dumps(payload), ex=self._ttl)

    async def get_last(self, simulation_id: str) -> Optional[dict]:
        value = await self._client.get(self._key(simulation_id))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        try:
            return json.loads(value)
        except Exception:
            return None

    def _key(self, simulation_id: str) -> str:
        return f"simulation:last:{simulation_id}"
