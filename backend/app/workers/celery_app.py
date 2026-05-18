from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "password-evolver",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
    task_default_retry_delay=settings.celery_retry_backoff_base,
    broker_connection_retry_on_startup=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=settings.worker_max_tasks_per_child or None,
    worker_max_memory_per_child=settings.worker_max_memory_per_child_mb or None,
    task_default_queue="simulations",
    broker_transport_options={"visibility_timeout": 3600},
    beat_schedule={
        "worker-heartbeat": {
            "task": "app.workers.tasks.emit_worker_heartbeat",
            "schedule": settings.worker_heartbeat_interval,
        }
    },
)

celery_app.autodiscover_tasks(["app.workers"])
