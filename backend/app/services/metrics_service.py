from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    matched: int
    progress: float
    elapsed: float
    speed: float


class MetricsService:
    def compute(self, *, matched: int, total: int, elapsed: float, attempts: int) -> Metrics:
        progress = matched / total if total else 0.0
        speed = attempts / elapsed if elapsed > 0 else 0.0
        return Metrics(matched=matched, progress=progress, elapsed=elapsed, speed=speed)
