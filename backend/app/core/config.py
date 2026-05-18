from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"
    default_charset: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 _+=~!@#$%^&*(){}[]|;:<>,.?/"
    update_every: int = Field(default=50, ge=1, le=10000)
    step_delay: float = Field(default=0.0, ge=0.0, le=5.0)
    max_target_length: int = Field(default=256, ge=1, le=2048)
    max_charset_length: int = Field(default=512, ge=1, le=4096)
    max_body_bytes: int = Field(default=4096, ge=256, le=65536)
    max_active_simulations: int = Field(default=200, ge=1, le=10000)
    rate_limit_rps: int = Field(default=10, ge=1, le=1000)
    rate_limit_burst: int = Field(default=20, ge=1, le=2000)
    websocket_heartbeat_interval: int = Field(default=15, ge=5, le=300)
    websocket_max_missed: int = Field(default=3, ge=1, le=10)
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "password-evolver"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/password_evolver"
    redis_url: str = "redis://localhost:6379/0"
    redis_channel_prefix: str = "simulation:"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=1, le=120)
    db_pool_recycle: int = Field(default=1800, ge=300, le=7200)
    alembic_ini_path: str = "backend/alembic.ini"
    worker_heartbeat_interval: int = Field(default=10, ge=5, le=300)
    worker_heartbeat_channel: str = "workers:heartbeat"
    worker_heartbeat_key: str = "workers:heartbeat:last"
    worker_heartbeat_ttl: int = Field(default=30, ge=10, le=600)
    worker_metrics_pushgateway: str = ""
    worker_metrics_job: str = "password-evolver-worker"
    celery_task_soft_time_limit: int = Field(default=20, ge=5, le=600)
    celery_task_time_limit: int = Field(default=30, ge=10, le=900)
    celery_task_max_retries: int = Field(default=3, ge=0, le=10)
    celery_retry_backoff_base: float = Field(default=0.2, ge=0.05, le=5.0)
    celery_retry_backoff_cap: float = Field(default=5.0, ge=0.5, le=60.0)
    celery_queue_backlog_limit: int = Field(default=10000, ge=0, le=1000000)
    celery_queue_key: str = "simulations"
    dlq_redis_key: str = "dlq:simulations"
    redis_circuit_failures: int = Field(default=5, ge=1, le=50)
    redis_circuit_recovery_seconds: int = Field(default=10, ge=1, le=300)
    worker_max_tasks_per_child: int = Field(default=1000, ge=0, le=100000)
    worker_max_memory_per_child_mb: int = Field(default=512, ge=0, le=8192)

    model_config = SettingsConfigDict(env_prefix="EVOLVER_")

    @field_validator("default_charset")
    @classmethod
    def validate_default_charset(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("default charset must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_limits(self) -> "Settings":
        if len(self.default_charset) > self.max_charset_length:
            raise ValueError("default charset exceeds max_charset_length")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
