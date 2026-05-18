import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Set

from fastapi import WebSocket

from app.services.metrics import record_backpressure, record_queue_depth, track_connection
from app.services.presence import PresenceStore

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    id: str
    websocket: WebSocket
    simulation_id: str
    session_id: Optional[str]
    queue: asyncio.Queue
    send_task: asyncio.Task
    missed_heartbeats: int = 0


class ConnectionManager:
    def __init__(
        self,
        *,
        presence: PresenceStore,
        shard_id: int,
        max_outbound_queue: int,
        max_connections: int,
        heartbeat_interval: int,
        heartbeat_max_missed: int,
    ) -> None:
        self._presence = presence
        self._shard_id = shard_id
        self._max_outbound_queue = max_outbound_queue
        self._max_connections = max_connections
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_max_missed = heartbeat_max_missed
        self._connections: Dict[str, Connection] = {}
        self._by_simulation: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._heartbeat_task:
            return
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self) -> None:
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            await asyncio.gather(self._heartbeat_task, return_exceptions=True)
            self._heartbeat_task = None
        await self.close_all()

    async def connect(
        self,
        *,
        connection_id: str,
        websocket: WebSocket,
        simulation_id: str,
        session_id: Optional[str],
    ) -> None:
        async with self._lock:
            if len(self._connections) >= self._max_connections:
                raise RuntimeError("gateway at capacity")
            await websocket.accept()
            queue: asyncio.Queue = asyncio.Queue(maxsize=self._max_outbound_queue)
            send_task = asyncio.create_task(self._send_loop(connection_id, websocket, queue))
            connection = Connection(
                id=connection_id,
                websocket=websocket,
                simulation_id=simulation_id,
                session_id=session_id,
                queue=queue,
                send_task=send_task,
            )
            self._connections[connection_id] = connection
            self._by_simulation.setdefault(simulation_id, set()).add(connection_id)
            track_connection(1)

        await self._presence.register(
            connection_id=connection_id,
            simulation_id=simulation_id,
            session_id=session_id,
            shard_id=self._shard_id,
        )

    async def disconnect(self, connection_id: str) -> None:
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if connection is None:
                return
            group = self._by_simulation.get(connection.simulation_id)
            if group:
                group.discard(connection_id)
                if not group:
                    self._by_simulation.pop(connection.simulation_id, None)
        current_task = asyncio.current_task()
        if connection.send_task is not current_task:
            try:
                connection.send_task.cancel()
                await asyncio.gather(connection.send_task, return_exceptions=True)
            except Exception:
                pass
        await self._presence.unregister(
            connection_id,
            connection.simulation_id,
            connection.session_id,
        )
        track_connection(-1)
        try:
            await connection.websocket.close()
        except Exception:
            pass

    async def mark_heartbeat(self, connection_id: str) -> None:
        connection = self._connections.get(connection_id)
        if connection:
            connection.missed_heartbeats = 0
            await self._presence.heartbeat(connection_id)

    async def broadcast(self, simulation_id: str, payload: dict) -> None:
        async with self._lock:
            targets = list(self._by_simulation.get(simulation_id, set()))
        for connection_id in targets:
            await self._enqueue(connection_id, payload)

    async def close_all(self) -> None:
        async with self._lock:
            connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    async def _enqueue(self, connection_id: str, payload: dict) -> None:
        connection = self._connections.get(connection_id)
        if not connection:
            return
        try:
            connection.queue.put_nowait(payload)
            record_queue_depth(connection.queue.qsize())
        except asyncio.QueueFull:
            logger.warning("backpressure exceeded", extra={"connection_id": connection_id})
            record_backpressure()
            await self.disconnect(connection_id)

    async def _send_loop(self, connection_id: str, websocket: WebSocket, queue: asyncio.Queue) -> None:
        try:
            while True:
                payload = await queue.get()
                await websocket.send_json(payload)
        except asyncio.CancelledError:
            return
        except Exception:
            asyncio.create_task(self.disconnect(connection_id))

    async def _heartbeat_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval)
                async with self._lock:
                    connections = list(self._connections.values())
                for connection in connections:
                    try:
                        await connection.websocket.send_text("ping")
                    except Exception:
                        await self.disconnect(connection.id)
                        continue
                    connection.missed_heartbeats += 1
                    if connection.missed_heartbeats >= self._heartbeat_max_missed:
                        await self.disconnect(connection.id)
        except asyncio.CancelledError:
            return
