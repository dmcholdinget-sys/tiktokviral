#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv
.venv/bin/pip install --disable-pip-version-check -r requirements.txt -r requirements-dev.txt
if ! command -v chromium >/dev/null 2>&1; then
  PLAYWRIGHT_BROWSERS_PATH="$PWD/.local/browsers" .venv/bin/playwright install chromium
fi
if [ ! -f .env ]; then
  python3 - <<'PYENV'
import secrets,os
from pathlib import Path
path=Path('.env')
content=Path('.env.example').read_text().replace('DJANGO_SECRET_KEY=\n','DJANGO_SECRET_KEY='+secrets.token_hex(32)+'\n').replace('POSTGRES_PASSWORD=\n','POSTGRES_PASSWORD='+secrets.token_hex(32)+'\n').replace('TELEGRAM_WEBHOOK_SECRET=\n','TELEGRAM_WEBHOOK_SECRET='+secrets.token_hex(32)+'\n')
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write(content)
PYENV
fi
mkdir -p .local
# .env is a private shell-compatible file controlled by the environment owner.
source scripts/environment.sh
docker compose up -d --wait db redis
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py check
