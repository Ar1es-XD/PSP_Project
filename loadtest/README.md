# Distributed Load Testing

This folder contains k6 and Locust scenarios for stressing the platform.

## Targets

- API: <http://localhost:8000>
- Gateway: ws://localhost:8001

## k6

- HTTP overload: k6 run k6/api_overload.js
- WebSocket floods: k6 run k6/ws_flood.js
- Reconnect storms: k6 run k6/ws_reconnect_storm.js

## Locust

- API + worker throughput: locust -f locust/api_user.py --host=<http://localhost:8000>
- Postgres pool exhaustion: locust -f locust/db_pool_user.py --host=<http://localhost:8000>
- Shard imbalance: locust -f locust/shard_user.py --host=<http://localhost:8000>

## Prometheus

- Use the config in prometheus/prometheus.yml and point to API and gateway metrics endpoints.
