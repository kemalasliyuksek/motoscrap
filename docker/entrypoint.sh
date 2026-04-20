#!/usr/bin/env bash
set -euo pipefail

echo "[motoscrap] Running database migrations..."
alembic upgrade head

echo "[motoscrap] Starting: $*"
exec "$@"
