"""Create deployment configuration once without exposing credentials in logs."""

import os
import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
private = root / ".deployment"
private.mkdir(mode=0o700, exist_ok=True)
runtime = private / "runtime.env"
database = private / "database.env"
if runtime.exists() or database.exists():
    if not runtime.exists() or not database.exists():
        raise SystemExit(
            "Partial deployment configuration; preserve it and investigate before proceeding."
        )
    print("Existing deployment credentials preserved.")
else:
    password = secrets.token_hex(32)
    db = f"POSTGRES_DB=tiktokerviral\nPOSTGRES_USER=tiktokerviral\nPOSTGRES_PASSWORD={password}\n"
    env = (
        db
        + f"DJANGO_SECRET_KEY={secrets.token_hex(48)}\nTELEGRAM_WEBHOOK_SECRET={secrets.token_hex(32)}\n"
    )
    env += "DJANGO_DEBUG=0\nDJANGO_ALLOWED_HOSTS=167.99.34.73,127.0.0.1,localhost,web\nDJANGO_CSRF_TRUSTED_ORIGINS=http://167.99.34.73:16700\nALLOW_HTTP_TESTING=1\nTELEGRAM_BOT_TOKEN=\n"
    for path, content in [(runtime, env), (database, db)]:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as file:
            file.write(content)
    print("Private deployment configuration created.")
