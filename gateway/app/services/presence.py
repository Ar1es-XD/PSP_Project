import json
import time
from typing import Optional

import redis.asyncio as redis


class PresenceStore:
    def __init__(self, client: redis.Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl = ttl_seconds

    async def register(
        self,
        *,
        connection_id: str,
        simulation_id: str,
        session_id: Optional[str],
        shard_id: int,
    ) -> None:
        await self._client.sadd(self._sim_key(simulation_id), connection_id)
        payload = {
            "simulation_id": simulation_id,
            "session_id": session_id or "",
            "shard_id": shard_id,
            "connected_at": int(time.time()),
        }
        await self._client.set(self._conn_key(connection_id), json.dumps(payload), ex=self._ttl)
        if session_id:
            await self._client.set(self._session_key(session_id), simulation_id, ex=self._ttl)

    async def heartbeat(self, connection_id: str) -> None:
        await self._client.expire(self._conn_key(connection_id), self._ttl)

    async def unregister(self, connection_id: str, simulation_id: str, session_id: Optional[str]) -> None:
        await self._client.srem(self._sim_key(simulation_id), connection_id)
        await self._client.delete(self._conn_key(connection_id))
        if session_id:
            await self._client.delete(self._session_key(session_id))

    async def resolve_session(self, session_id: str) -> Optional[str]:
        value = await self._client.get(self._session_key(session_id))
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else str(value)

    async def throttle_reconnect(self, session_id: str, cooldown_seconds: int) -> bool:
        key = self._reconnect_key(session_id)
        if await self._client.exists(key):
            return False
        await self._client.set(key, "1", ex=cooldown_seconds)
        return True

    def _sim_key(self, simulation_id: str) -> str:
        return f"presence:simulation:{simulation_id}"

    def _conn_key(self, connection_id: str) -> str:
        return f"presence:connection:{connection_id}"

    def _session_key(self, session_id: str) -> str:
        return f"presence:session:{session_id}"

    def _reconnect_key(self, session_id: str) -> str:
        return f"presence:reconnect:{session_id}"
