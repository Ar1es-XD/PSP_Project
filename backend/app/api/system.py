from fastapi import APIRouter, Request

import redis.asyncio as redis
from sqlalchemy import text

from app.core.metrics import metrics_response

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict:
    engine = request.app.state.db_engine
    settings = request.app.state.settings
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    redis_client = redis.from_url(settings.redis_url)
    await redis_client.ping()
    await redis_client.close()
    return {"status": "ready"}


@router.get("/metrics")
def metrics():
    return metrics_response()


@router.get("/health/distributed")
async def distributed_health(request: Request) -> dict:
    engine = request.app.state.db_engine
    settings = request.app.state.settings
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    redis_client = redis.from_url(settings.redis_url)
    await redis_client.ping()
    heartbeat = await redis_client.get(settings.worker_heartbeat_key)
    await redis_client.close()
    return {
        "status": "ok",
        "worker_heartbeat": bool(heartbeat),
    }
