from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"
    default_charset: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890 _+=~!@#$%^&*(){}[]|;:<>,.?/"
    update_every: int = 50
    step_delay: float = 0.0

    model_config = SettingsConfigDict(env_prefix="EVOLVER_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
