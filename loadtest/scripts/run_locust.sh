#!/usr/bin/env bash
set -euo pipefail

LOCUST_FILE=${1:-locust/api_user.py}
HOST=${HOST:-http://localhost:8000}

locust -f "$LOCUST_FILE" --host="$HOST"
