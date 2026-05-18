import json
from typing import AsyncIterator

import redis.asyncio as redis


class RedisEventBus:
    def __init__(self, redis_url: str, channel_prefix: str) -> None:
        self._redis_url = redis_url
        self._redis = redis.from_url(redis_url)
        self._channel_prefix = channel_prefix

    def channel_for(self, simulation_id: str) -> str:
        return f"{self._channel_prefix}{simulation_id}"

    async def publish(self, simulation_id: str, payload: dict) -> None:
        channel = self.channel_for(simulation_id)
        await self._redis.publish(channel, json.dumps(payload))

    async def subscribe(self, pattern: str) -> AsyncIterator[dict]:
        pubsub = self._redis.pubsub()
        await pubsub.psubscribe(pattern)
        try:
            async for message in pubsub.listen():
                if message.get("type") != "pmessage":
                    continue
                yield message
        finally:
            await pubsub.close()

    async def close(self) -> None:
        await self._redis.close()

    async def reset(self) -> None:
        await self._redis.close()
        self._redis = redis.from_url(self._redis_url)
