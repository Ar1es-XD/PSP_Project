import time
from dataclasses import dataclass
from typing import Dict


@dataclass
class TokenBucket:
    rate: float
    capacity: float
    tokens: float
    last_refill: float

    def consume(self, amount: float) -> bool:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens < amount:
            return False
        self.tokens -= amount
        return True


class RateLimiter:
    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate
        self._capacity = capacity
        self._buckets: Dict[str, TokenBucket] = {}

    def allow(self, key: str, amount: float = 1.0) -> bool:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                rate=self._rate,
                capacity=self._capacity,
                tokens=self._capacity,
                last_refill=time.time(),
            )
            self._buckets[key] = bucket
        return bucket.consume(amount)
