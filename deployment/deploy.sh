#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Docker is required; no host packages were changed.' >&2; exit 1; }
docker compose version >/dev/null
project_gateway=$(docker compose -f deployment/compose.yaml ps -q gateway 2>/dev/null || true)
if ss -ltn | awk 'NR>1 {print $4}' | grep -Eq '(^|:)16700$' && [ -z "$project_gateway" ]; then
  echo 'Port 16700 is occupied by an existing service. Deployment stopped.' >&2
  exit 1
fi
python3 deployment/prepare.py
docker compose -f deployment/compose.yaml build web
docker compose -f deployment/compose.yaml up -d --wait db redis
docker compose -f deployment/compose.yaml run --rm --no-deps web python manage.py migrate --noinput
docker compose -f deployment/compose.yaml run --rm --no-deps web python manage.py collectstatic --noinput
docker compose -f deployment/compose.yaml run --rm --no-deps web python manage.py seed_demo
docker compose -f deployment/compose.yaml run --rm --no-deps web python deployment/provision_accounts.py
docker compose -f deployment/compose.yaml up -d --wait web worker beat gateway
web_container=$(docker compose -f deployment/compose.yaml ps -q web)
docker cp "$web_container:/app/.local/test-logins.txt" .deployment/test-logins.txt
chmod 600 .deployment/test-logins.txt
curl --fail --silent --show-error http://127.0.0.1:16700/accounts/login/ -o .deployment/login-response.html
python3 - <<'PY'
from pathlib import Path
assert 'Sign in to your workspace' in Path('.deployment/login-response.html').read_text()
print('HTTP login response verified on port 16700.')
PY
docker compose -f deployment/compose.yaml exec -T worker python -c 'import django; django.setup(); from intelligence.tasks import readiness_probe; assert readiness_probe.delay().get(timeout=20)=="celery-ready"; print("Celery round trip verified.")'
echo 'Deployment running. Testing credentials: .deployment/test-logins.txt (private).'
