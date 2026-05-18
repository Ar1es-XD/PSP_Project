import json
import logging
import time

import redis

from app.core.config import Settings

logger = logging.getLogger(__name__)


def push_dlq(simulation_id: str, reason: str, detail: str, settings: Settings) -> None:
    try:
        client = redis.Redis.from_url(settings.redis_url)
        payload = {
            "simulation_id": simulation_id,
            "reason": reason,
            "detail": detail,
            "timestamp": time.time(),
        }
        client.rpush(settings.dlq_redis_key, json.dumps(payload))
    except Exception:
        logger.exception("failed to push dlq", extra={"simulation_id": simulation_id})
