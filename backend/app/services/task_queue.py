import redis

from app.core.config import get_settings
from app.utils.circuit_breaker import CircuitBreaker
from app.workers.celery_app import celery_app
_queue_breaker: CircuitBreaker | None = None


def _get_breaker() -> CircuitBreaker:
    global _queue_breaker
    settings = get_settings()
    if _queue_breaker is None:
        _queue_breaker = CircuitBreaker(
            failure_threshold=settings.redis_circuit_failures,
            recovery_seconds=settings.redis_circuit_recovery_seconds,
        )
    return _queue_breaker



def enqueue_simulation(simulation_id: str) -> str:
    settings = get_settings()
    breaker = _get_breaker()
    if not breaker.allow():
        raise RuntimeError("queue unavailable")
    if settings.celery_queue_backlog_limit > 0:
        try:
            client = redis.Redis.from_url(settings.celery_broker_url)
            backlog = client.llen(settings.celery_queue_key)
            if backlog >= settings.celery_queue_backlog_limit:
                raise RuntimeError("queue backlog exceeded")
        except Exception:
            pass
    try:
        result = celery_app.send_task("app.workers.tasks.run_simulation", args=[simulation_id])
        breaker.record_success()
    except Exception as exc:
        breaker.record_failure()
        raise RuntimeError("queue unavailable") from exc
    return result.id


def revoke_task(task_id: str) -> None:
    celery_app.control.revoke(task_id, terminate=False)
