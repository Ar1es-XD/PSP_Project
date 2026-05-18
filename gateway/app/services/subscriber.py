import asyncio
import json
import logging
from typing import Optional

from app.services.connection_manager import ConnectionManager
from app.services.event_cache import EventCache
from app.services.sharding import is_local_shard
from app.services.event_bus import RedisEventBus
from app.utils.backoff import exponential_backoff
from app.utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class RedisSubscriber:
    def __init__(
        self,
        *,
        event_bus: RedisEventBus,
        connection_manager: ConnectionManager,
        event_cache: EventCache,
        channel_prefix: str,
        shard_id: int,
        shard_count: int,
        backoff_base: float,
        backoff_cap: float,
        circuit_failures: int,
        circuit_recovery_seconds: int,
    ) -> None:
        self._event_bus = event_bus
        self._manager = connection_manager
        self._event_cache = event_cache
        self._pattern = f"{channel_prefix}*"
        self._shard_id = shard_id
        self._shard_count = shard_count
        self._task: Optional[asyncio.Task] = None
        self._attempt = 0
        self._backoff_base = backoff_base
        self._backoff_cap = backoff_cap
        self._breaker = CircuitBreaker(
            failure_threshold=circuit_failures,
            recovery_seconds=circuit_recovery_seconds,
        )

    async def start(self) -> None:
        if self._task:
            return
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        await self._event_bus.close()

    async def _run(self) -> None:
        try:
            while True:
                try:
                    async for message in self._event_bus.subscribe(self._pattern):
                        channel = message.get("channel")
                        if not channel:
                            continue
                        if isinstance(channel, bytes):
                            channel = channel.decode("utf-8")
                        simulation_id = channel.split(":")[-1]
                        if not is_local_shard(simulation_id, self._shard_id, self._shard_count):
                            continue
                        data = message.get("data")
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        try:
                            payload = json.loads(data)
                        except Exception:
                            continue
                        await self._event_cache.set_last(simulation_id, payload)
                        await self._manager.broadcast(simulation_id, payload)
                        self._attempt = 0
                        self._breaker.record_success()
                    await asyncio.sleep(0)
                except Exception:
                    logger.exception("redis subscriber failed")
                    await self._handle_failure()
        except asyncio.CancelledError:
            logger.info("redis subscriber stopped")

    async def _handle_failure(self) -> None:
        self._breaker.record_failure()
        if not self._breaker.allow():
            await asyncio.sleep(1)
            return
        self._attempt += 1
        delay = exponential_backoff(self._attempt, base=self._backoff_base, cap=self._backoff_cap)
        try:
            await self._event_bus.reset()
        except Exception:
            pass
        await asyncio.sleep(delay)
