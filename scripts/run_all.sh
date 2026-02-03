#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

start_bot() {
  echo "Starting bot..."
  (cd "$ROOT_DIR/services/bot" && PYTHONPATH=. python -m app.main) &
  BOT_PID=$!
}

start_admin() {
  echo "Starting admin..."
  (cd "$ROOT_DIR/services/admin" && PYTHONPATH=. uvicorn app.main:app --port 8001) &
  ADMIN_PID=$!
}

stop_all() {
  echo "Stopping services..."
  kill "${BOT_PID:-0}" "${ADMIN_PID:-0}" 2>/dev/null || true
}

trap stop_all EXIT INT TERM

start_bot
start_admin

wait "$BOT_PID" "$ADMIN_PID"
