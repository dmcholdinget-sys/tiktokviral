#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/environment.sh
mkdir -p .local
docker compose up -d --wait db redis
.venv/bin/python manage.py migrate --noinput
start_process() {
  local name="$1"; shift
  if [ -f ".local/$name.pid" ]; then
    local pid; pid=$(cat ".local/$name.pid")
    if kill -0 "$pid" 2>/dev/null && [ "$(readlink "/proc/$pid/cwd")" = "$PWD" ]; then
      return
    fi
  fi
  nohup "$@" > ".local/$name.log" 2>&1 < /dev/null &
  echo $! > ".local/$name.pid"
}
start_process web .venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
start_process worker .venv/bin/celery -A config worker --loglevel=WARNING --concurrency=2
start_process beat .venv/bin/celery -A config beat --loglevel=WARNING --schedule=.local/celerybeat-schedule
.venv/bin/python scripts/readiness.py
