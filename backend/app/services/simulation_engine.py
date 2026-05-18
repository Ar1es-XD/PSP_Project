import asyncio
import logging
import random
import time
from typing import Optional

from app.models.schemas import SimulationStatus
from app.services.metrics_service import MetricsService
from app.services.registry import SimulationRegistry
from app.websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)


class SimulationEngine:
    def __init__(
        self,
        *,
        registry: SimulationRegistry,
        metrics: MetricsService,
        websocket_manager: WebSocketManager,
        default_charset: str,
        update_every: int,
        step_delay: float,
    ) -> None:
        self._registry = registry
        self._metrics = metrics
        self._ws = websocket_manager
        self._default_charset = default_charset
        self._update_every = update_every
        self._step_delay = step_delay
        self._tasks: dict[str, asyncio.Task] = {}

    async def start(self, state_id: str) -> None:
        if state_id in self._tasks:
            return
        task = asyncio.create_task(self._run(state_id))
        self._tasks[state_id] = task

    async def stop(self, state_id: str) -> bool:
        task = self._tasks.pop(state_id, None)
        if task is None:
            return False
        task.cancel()
        return True

    def get_status(self, state_id: str) -> Optional[SimulationStatus]:
        state = self._registry.get(state_id)
        if state is None:
            return None
        return self._build_status(state)

    async def _run(self, state_id: str) -> None:
        state = self._registry.get(state_id)
        if state is None:
            return

        charset = state.charset or self._default_charset
        update_every = state.update_every or self._update_every
        target = list(state.target)
        if not state.current:
            state.current = [random.choice(charset) for _ in target]
        state.start_time = time.time()

        try:
            while state.current != target:
                state.attempts += 1
                for i, wanted in enumerate(target):
                    if state.current[i] != wanted:
                        state.current[i] = random.choice(charset)

                should_update = state.attempts % update_every == 0
                if should_update:
                    await self._publish(state)

                if self._step_delay:
                    await asyncio.sleep(self._step_delay)

            state.completed = True
            await self._publish(state)
        except asyncio.CancelledError:
            logger.info("simulation stopped", extra={"simulation_id": state_id})
        except Exception:
            logger.exception("simulation failed", extra={"simulation_id": state_id})
        finally:
            self._tasks.pop(state_id, None)

    def _build_status(self, state) -> SimulationStatus:
        matched = sum(1 for c, w in zip(state.current, state.target) if c == w)
        elapsed = max(time.time() - state.start_time, 0.0)
        metrics = self._metrics.compute(
            matched=matched,
            total=len(state.target),
            elapsed=elapsed,
            attempts=state.attempts,
        )
        return SimulationStatus(
            id=state.id,
            target=state.target,
            current="".join(state.current),
            attempts=state.attempts,
            matched=metrics.matched,
            progress=metrics.progress,
            elapsed=metrics.elapsed,
            speed=metrics.speed,
            completed=state.completed,
        )

    async def _publish(self, state) -> None:
        status = self._build_status(state)
        await self._ws.broadcast(state.id, status.model_dump())
