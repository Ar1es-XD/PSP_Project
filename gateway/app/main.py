from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.core.config import get_gateway_settings
from app.core.logging import configure_logging
from app.core.redis import build_redis
from app.services.connection_manager import ConnectionManager
from app.services.event_bus import RedisEventBus
from app.services.event_cache import EventCache
from app.services.presence import PresenceStore
from app.services.metrics import record_connect_limited, record_message_limited
from app.services.rate_limit import RateLimiter
from app.services.subscriber import RedisSubscriber
from app.services.sharding import is_local_shard
from app.utils.id import generate_id


def create_app() -> FastAPI:
    settings = get_gateway_settings()
    configure_logging(settings.log_level)

    redis_client = build_redis(settings.redis_url)
    presence = PresenceStore(redis_client, settings.presence_ttl_seconds)
    event_cache = EventCache(redis_client, settings.event_cache_ttl_seconds)
    event_bus = RedisEventBus(settings.redis_url, settings.redis_channel_prefix)

    connection_manager = ConnectionManager(
        presence=presence,
        shard_id=settings.shard_id,
        max_outbound_queue=settings.max_outbound_queue,
        max_connections=settings.max_connections,
        heartbeat_interval=settings.heartbeat_interval,
        heartbeat_max_missed=settings.heartbeat_max_missed,
    )

    subscriber = RedisSubscriber(
        event_bus=event_bus,
        connection_manager=connection_manager,
        event_cache=event_cache,
        channel_prefix=settings.redis_channel_prefix,
        shard_id=settings.shard_id,
        shard_count=settings.shard_count,
        backoff_base=settings.subscriber_backoff_base,
        backoff_cap=settings.subscriber_backoff_cap,
        circuit_failures=settings.redis_circuit_failures,
        circuit_recovery_seconds=settings.redis_circuit_recovery_seconds,
    )

    connect_limiter = RateLimiter(settings.connect_rate_rps, settings.connect_rate_burst)
    message_limiter = RateLimiter(settings.message_rate_rps, settings.message_rate_burst)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await connection_manager.start()
        await subscriber.start()
        yield
        await subscriber.stop()
        await connection_manager.stop()
        await redis_client.close()

    app = FastAPI(title="Password Evolver Gateway", version="1.0.0", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/ready")
    async def ready() -> dict:
        await redis_client.ping()
        return {"status": "ready"}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.websocket("/ws/simulations/{simulation_id}")
    async def simulation_ws(websocket: WebSocket, simulation_id: str, request: Request) -> None:
        client_ip = request.headers.get("x-forwarded-for")
        if client_ip:
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        session_id = websocket.query_params.get("session_id")
        resume = websocket.query_params.get("resume") == "1"
        if resume and session_id:
            resolved = await presence.resolve_session(session_id)
            if resolved:
                simulation_id = resolved

        if session_id:
            allowed = await presence.throttle_reconnect(
                session_id,
                cooldown_seconds=settings.reconnect_cooldown_seconds,
            )
            if not allowed:
                await websocket.close(code=4429)
                return

        if not connect_limiter.allow(client_ip):
            record_connect_limited()
            await websocket.close(code=4429)
            return

        if not is_local_shard(simulation_id, settings.shard_id, settings.shard_count):
            await websocket.close(code=4404)
            return

        connection_id = generate_id()
        try:
            await connection_manager.connect(
                connection_id=connection_id,
                websocket=websocket,
                simulation_id=simulation_id,
                session_id=session_id,
            )
        except RuntimeError:
            await websocket.close(code=4429)
            return

        if resume:
            payload = await event_cache.get_last(simulation_id)
            if payload:
                await websocket.send_json(payload)

        try:
            while True:
                message = await websocket.receive_text()
                if not message_limiter.allow(client_ip):
                    record_message_limited()
                    await websocket.close(code=4408)
                    break
                if message == "pong":
                    await connection_manager.mark_heartbeat(connection_id)
                elif message == "ping":
                    await websocket.send_text("pong")
                else:
                    await connection_manager.mark_heartbeat(connection_id)
        except Exception:
            pass
        finally:
            await connection_manager.disconnect(connection_id)

    return app


app = create_app()
