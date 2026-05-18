from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    redis_channel_prefix: str = "simulation:"
    shard_id: int = Field(default=0, ge=0)
    shard_count: int = Field(default=1, ge=1)
    heartbeat_interval: int = Field(default=15, ge=5, le=300)
    heartbeat_max_missed: int = Field(default=3, ge=1, le=10)
    presence_ttl_seconds: int = Field(default=60, ge=10, le=600)
    event_cache_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    max_outbound_queue: int = Field(default=256, ge=32, le=2048)
    max_connections: int = Field(default=20000, ge=1000, le=100000)
    connect_rate_rps: int = Field(default=20, ge=1, le=1000)
    connect_rate_burst: int = Field(default=40, ge=1, le=2000)
    message_rate_rps: int = Field(default=30, ge=1, le=2000)
    message_rate_burst: int = Field(default=60, ge=1, le=4000)
    reconnect_cooldown_seconds: int = Field(default=3, ge=1, le=60)
    redis_circuit_failures: int = Field(default=5, ge=1, le=50)
    redis_circuit_recovery_seconds: int = Field(default=10, ge=1, le=300)
    subscriber_backoff_base: float = Field(default=0.2, ge=0.05, le=5.0)
    subscriber_backoff_cap: float = Field(default=5.0, ge=0.5, le=60.0)

    model_config = SettingsConfigDict(env_prefix="GATEWAY_")

    @field_validator("redis_channel_prefix")
    @classmethod
    def validate_prefix(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("redis_channel_prefix must not be empty")
        return cleaned

    @model_validator(mode="after")
    def validate_shard(self) -> "GatewaySettings":
        if self.shard_id >= self.shard_count:
            raise ValueError("shard_id must be less than shard_count")
        return self


@lru_cache
def get_gateway_settings() -> GatewaySettings:
    return GatewaySettings()
