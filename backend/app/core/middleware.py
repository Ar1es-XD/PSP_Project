import time
import uuid
from dataclasses import dataclass
from typing import Callable, Dict

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import Settings
from app.core.metrics import record_request
from app.core.observability import set_request_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_bytes: int) -> None:
        super().__init__(app)
        self._max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > self._max_body_bytes:
            raise HTTPException(status_code=413, detail="payload too large")

        body = await request.body()
        if len(body) > self._max_body_bytes:
            raise HTTPException(status_code=413, detail="payload too large")
        request._body = body
        return await call_next(request)


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


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._rate = float(settings.rate_limit_rps)
        self._capacity = float(settings.rate_limit_burst)
        self._buckets: Dict[str, TokenBucket] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in {"/health", "/ready", "/metrics"}:
            return await call_next(request)
        forwarded_for = request.headers.get("x-forwarded-for")
        client_host = forwarded_for.split(",")[0].strip() if forwarded_for else None
        if not client_host:
            client_host = request.client.host if request.client else "unknown"
        bucket = self._buckets.get(client_host)
        if bucket is None:
            bucket = TokenBucket(
                rate=self._rate,
                capacity=self._capacity,
                tokens=self._capacity,
                last_refill=time.time(),
            )
            self._buckets[client_host] = bucket

        if not bucket.consume(1.0):
            raise HTTPException(status_code=429, detail="rate limit exceeded")

        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        record_request(request.method, request.url.path, response.status_code, duration)
        return response


class ResilienceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if response.status_code in {429, 503}:
            response.headers.setdefault("Retry-After", "5")
        return response
