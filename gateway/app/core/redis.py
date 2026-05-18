import redis.asyncio as redis


def build_redis(url: str) -> redis.Redis:
    return redis.from_url(url)
