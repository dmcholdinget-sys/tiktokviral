# Operations, deployment, backup, and troubleshooting

## Development processes

`scripts/install.sh` installs pinned Python packages, generates private local defaults if absent, starts digest-pinned PostgreSQL 16 and Redis 7 containers, applies migrations, and checks Django. `scripts/start.sh` starts web, Celery worker (concurrency 2), and Beat. It can be repeated without starting duplicate processes. `scripts/stop.sh` stops the tracked application processes while retaining database/cache containers. Process state does not survive cloud snapshots: run start.sh in each new task.

Scheduled jobs: discovery every 15 minutes, delivery every 30 seconds, expiration/reminders hourly. Feed discovery reimports available observations; separate provider-specific priority refresh APIs are not assumed. Feed outages are recorded without exposing credential values or response bodies. Inspect System health and `.local/web.log`, `.local/worker.log`, `.local/beat.log`.

## Telegram

Create a bot with Telegram's BotFather, then set TELEGRAM_BOT_TOKEN and a strong TELEGRAM_WEBHOOK_SECRET securely. Use an externally reachable HTTPS application deployment for webhooks; local onboarding cannot receive Telegram callbacks. Register `https://YOUR_HOST/telegram/webhook/` with Telegram's setWebhook API and include `secret_token` matching TELEGRAM_WEBHOOK_SECRET. Do not paste credentials into shell history or chat. Share publisher-specific one-time link commands privately. Real send reliability remains unmeasured until the bot and chats are configured.

Register without putting credentials in command arguments: `.venv/bin/python manage.py configure_telegram --webhook-url https://YOUR_HOST/telegram/webhook/`. The generated development webhook secret must be replaced with your production secret for deployment.

Only links are sent by the current bot workflow. Media remains private on the site, gated by rights. 429/server rejection uses bounded retries and retry_after. Network exceptions become unknown rather than automatic duplicate sends. A crashed sending record is also reconciled manually from the assignment page. An administrator can revoke queued content; revocation cannot retract a Telegram message already accepted by Telegram.

## Backup and restore

```bash
bash scripts/backup.sh
# Restore into a NEW database; the script refuses an existing target.
bash scripts/restore.sh .local/backups/database-TIMESTAMP.dump tiktokviral_restore
```

Back up `.env` through your secret manager, private media with access controls, and database dumps. Dumps contain user and assignment data; use encrypted restricted storage and a retention policy. A restore target can be validated separately with POSTGRES_DB set to that new database. Switch the deployed application only after maintenance planning. Never delete the live database merely to make restoration work.

`.local/postgres` and `.local/redis` are persisted bind mounts. These container-managed directories have restricted ownership. Keep the database dump in the workspace for a portable snapshot backup. Fresh-task restoration is not claimed until publication and validation in a new cloud task.

## Production checklist

Use Python 3.12+, the pinned requirements, PostgreSQL, Redis, and a supervised Gunicorn/Celery/Beat deployment. Bind the application to a private interface and terminate TLS at Nginx. Set DJANGO_DEBUG=0, a unique secret, explicit allowed hosts, secure database credentials, and trusted HTTPS origin settings. Run `manage.py check --deploy` under production configuration. Run migrations as a release step, collectstatic, and serve only staticfiles through the proxy. Never expose MEDIA_ROOT directly: downloads must pass application permission/rights checks. Do not expose PostgreSQL/Redis ports publicly.

Example application command: `.venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2`. Proxy requests must preserve Host. Forwarded HTTPS headers are trusted only when the reverse proxy strips incoming client values; configure that trust explicitly for your deployment. Use separate live secrets from generated development defaults.

## Troubleshooting

- Missing secret error: set DJANGO_SECRET_KEY or run install.sh to create private local development defaults.
- Database refusal: run `docker compose up -d --wait`; confirm configured host/port and credential binding without printing secrets.
- Failed Playwright discovery: the provider remains enabled; apply the saved TikTok allowed domains, inspect browser network error codes, and retry. Access challenges or metadata changes require supported source changes rather than bypass.
- Failed feed discovery: check the approved endpoint, network allowlist, credential binding, 200 JSON response, and documented schema. Never disable TLS verification.
- Pending Telegram: configure the token and link a publisher chat. For unknown/sending, inspect the chat before reconciliation.
- Low/insufficient score confidence: inspect missing metrics, observation times, and freshness. Do not fill missing data with zero.
- Unavailable media: candidate must be approved with nonexpired documented rights.
- No model proposal: obtain at least 30 distinct verified outcomes at comparable 12–36h windows and varied historical signals.
