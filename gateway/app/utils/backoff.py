import random


def exponential_backoff(attempt: int, *, base: float, cap: float, jitter: float = 0.2) -> float:
    value = min(cap, base * (2 ** max(attempt, 0)))
    return value * (1 - jitter + random.random() * jitter)
