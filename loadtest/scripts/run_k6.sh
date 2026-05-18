#!/usr/bin/env bash
set -euo pipefail

SCRIPT=${1:-k6/api_overload.js}
API_BASE_URL=${API_BASE_URL:-http://localhost:8000/api/v1}
WS_BASE_URL=${WS_BASE_URL:-ws://localhost:8001}

k6 run -e API_BASE_URL="$API_BASE_URL" -e WS_BASE_URL="$WS_BASE_URL" "$SCRIPT"
