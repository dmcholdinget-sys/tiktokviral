#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for name in beat worker web; do
  file=".local/$name.pid"
  if [ -f "$file" ]; then
    pid=$(cat "$file")
    if kill -0 "$pid" 2>/dev/null && [ "$(readlink "/proc/$pid/cwd")" = "$PWD" ]; then
      kill "$pid"
      for attempt in {1..50}; do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        sleep 0.2
      done
      if kill -0 "$pid" 2>/dev/null && [ "$(readlink "/proc/$pid/cwd")" = "$PWD" ]; then
        kill -KILL "$pid"
      fi
    fi
    rm "$file"
  fi
done
# Keep PostgreSQL and Redis running; docker compose stop stops them without deleting data.
