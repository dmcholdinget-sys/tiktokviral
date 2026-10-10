import os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
import requests, redis
from django.db import connection
from django.conf import settings
from intelligence.tasks import readiness_probe

for attempt in range(30):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
        assert redis.Redis.from_url(settings.CELERY_BROKER_URL).ping()
        response = requests.get("http://127.0.0.1:8000/accounts/login/", timeout=2)
        assert (
            response.status_code == 200 and "Sign in to your workspace" in response.text
        )
        assert readiness_probe.delay().get(timeout=3) == "celery-ready"
        print("Ready: PostgreSQL, Redis, Django login, and Celery round trip passed.")
        break
    except Exception:
        if attempt == 29:
            raise
        time.sleep(1)
