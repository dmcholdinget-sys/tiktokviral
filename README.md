# TenaTrend · Ethiopian Trend Intelligence

A Django 5.2 application for discovering and reviewing Ethiopian content opportunities, coordinating manual publishing through Telegram, and recording outcomes. Built from [the PRD](docs/PRD.md).

## Development setup

Requires Python 3.12+, Docker Engine, and Docker Compose. Use the existing checkout; cloud tasks are already isolated and do not require a Git worktree.

```bash
cd /workspace/tiktokviral
bash scripts/install.sh
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py createsuperuser
bash scripts/start.sh
```

The setup creates a private `.env` with random local Django and database secrets only if absent. Existing files and injected environment bindings are preserved. Dependencies are pinned in `requirements.txt`; container images are pinned by digest. PostgreSQL and Redis persist in `.local/`. Web, worker, and Beat logs/PIDs are also in `.local/`. `scripts/start.sh` verifies database access, Redis, the login response, and a real Celery task. `scripts/stop.sh` stops only the application processes this checkout started.

`seed_demo` creates a labeled fixture, enabled Playwright discovery, optional disabled live-feed configuration, an initial ranking version, and four publishers with unusable passwords. Set publisher passwords in Django administration or with `manage.py changepassword publisher1` (repeat for the other users). It never invents external credentials. Create the administrator with `createsuperuser`; no default login/password is shipped.

```bash
.venv/bin/python manage.py test intelligence --noinput
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
```

## Implemented workflows

- Session login, administrator review dashboard, family publishers restricted to their assignments, and read-only Analyst group.
- Enabled Playwright public trend/search discovery with Ethiopian topic/language queries and dynamically observed hashtags; replaceable authorized JSON feed and manual import; explicitly labeled fixture provider; periodic discovery, provenance, nullable counters, and canonical ID deduplication.
- Weighted explainable ranking with velocity, acceleration, engagement, relevance, freshness, propagation, novelty, missing-data completeness, separate confidence, and score/version history.
- Source topics/hashtags/sounds, topic clusters, heuristic lifecycle and expiration.
- Review notes, safety flags, rights evidence and expiration, private media downloads gated by approval and valid rights.
- Individual/multiple assignments, daily publisher limits, duplicate prevention, revocation, in-app notifications, and publishing reminders.
- Telegram one-time account binding, link-only packages, accept/decline callbacks, `/published ID HTTPS_URL`, delivery logs, bounded backoff, and explicit reconciliation of ambiguous sends.
- Manual publication and metrics reporting, administrator verification, publisher performance, CSV export, and inactive ranking proposals from verified outcomes.
- PostgreSQL migrations, Redis/Celery/Beat, backup and safe restore scripts, and a session-authenticated REST API.

Playwright discovery is enabled by default and attempts public TikTok Creative Center/search pages. The current cloud proxy blocks those destinations, so live runs currently fail visibly with no extracted candidates. The saved network domain additions must be applied in environment settings before retrying. Actual Telegram sends require bot configuration. The fixture is a development test, not evidence of real TikTok access. See [provider feasibility](docs/PROVIDERS.md), [API](docs/API.md), [operations](docs/OPERATIONS.md), [user guide](docs/USER_GUIDE.md), and [delivery status](docs/STATUS.md).

## Configuration

Use `.env.example` as the list of configuration names. The file format is literal `NAME=value` without shell quoting or interpolation. Set secrets securely in environment settings or the private local `.env`; do not commit them. Injected variables take precedence over local defaults.

For development, `DJANGO_DEBUG=1` and loopback bindings are intentional. Deployment requires `DJANGO_DEBUG=0`, explicit `DJANGO_ALLOWED_HOSTS`, HTTPS reverse proxy, secure secret management, and backups. Do not expose the development server publicly.
