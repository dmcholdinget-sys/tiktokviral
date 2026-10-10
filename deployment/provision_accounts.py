"""One-time testing accounts; credentials are stored privately, never logged."""

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.deployment")
import django

django.setup()
from django.contrib.auth.models import User
from intelligence.models import PublisherProfile

credentials = Path("/app/.local/test-logins.txt")
if credentials.exists():
    print("Existing testing credentials preserved.")
else:
    records = []
    admin, created = User.objects.get_or_create(
        username="testadmin", defaults={"is_staff": True, "is_superuser": True}
    )
    if created:
        password = secrets.token_urlsafe(24)
        admin.set_password(password)
        admin.save()
        records.append(("testadmin", password))
    for index in range(1, 5):
        user, created = User.objects.get_or_create(username=f"publisher{index}")
        PublisherProfile.objects.get_or_create(
            user=user, defaults={"display_name": f"Family publisher {index}"}
        )
        if created or not user.has_usable_password():
            password = secrets.token_urlsafe(24)
            user.set_password(password)
            user.save()
            records.append((user.username, password))
    if records:
        fd = os.open(credentials, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as file:
            file.write("HTTP test deployment: use only testing data.\n\n")
            for username, password in records:
                file.write(f"Username: {username}\nPassword: {password}\n\n")
        print("Testing accounts created; credentials stored privately.")
