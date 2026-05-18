import time
from dataclasses import dataclass


@dataclass
class CircuitBreakerState:
    failures: int = 0
    opened_at: float = 0.0


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int, recovery_seconds: int) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_seconds = recovery_seconds
        self._state = CircuitBreakerState()

    def allow(self) -> bool:
        if self._state.failures < self._failure_threshold:
            return True
        if time.time() - self._state.opened_at >= self._recovery_seconds:
            self._state.failures = 0
            self._state.opened_at = 0.0
            return True
        return False

    def record_success(self) -> None:
        self._state.failures = 0
        self._state.opened_at = 0.0

    def record_failure(self) -> None:
        self._state.failures += 1
        if self._state.failures >= self._failure_threshold:
            if self._state.opened_at == 0.0:
                self._state.opened_at = time.time()
