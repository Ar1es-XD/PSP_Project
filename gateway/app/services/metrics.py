from prometheus_client import Counter, Gauge, Histogram

ACTIVE_CONNECTIONS = Gauge("gateway_active_connections", "Active websocket connections")
BACKPRESSURE_DROPS = Counter("gateway_backpressure_drops_total", "Dropped connections due to backpressure")
OUTBOUND_QUEUE_DEPTH = Histogram(
    "gateway_outbound_queue_depth",
    "Outbound queue depth samples",
    buckets=(1, 4, 8, 16, 32, 64, 128, 256, 512),
)
CONNECT_RATE_LIMIT = Counter("gateway_connect_rate_limited_total", "Connection rate limited")
MESSAGE_RATE_LIMIT = Counter("gateway_message_rate_limited_total", "Message rate limited")


def track_connection(delta: int) -> None:
    ACTIVE_CONNECTIONS.inc(delta)


def record_backpressure() -> None:
    BACKPRESSURE_DROPS.inc()


def record_queue_depth(depth: int) -> None:
    OUTBOUND_QUEUE_DEPTH.observe(depth)


def record_connect_limited() -> None:
    CONNECT_RATE_LIMIT.inc()


def record_message_limited() -> None:
    MESSAGE_RATE_LIMIT.inc()
