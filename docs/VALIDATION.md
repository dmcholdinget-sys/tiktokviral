# Validation evidence · October 9, 2026

- 39 application tests passed against PostgreSQL, including role isolation, canonical deduplication, missing metrics, velocity/scoring, review/assignment/publishing, rights-gated media, delivery retry/reconciliation, Telegram linking, trends, reminders, CSV reports, model configuration and evidence-gated learning proposals.
- 2 additional webhook configuration command tests passed; no real Telegram calls were made.
- Chromium launched and extracted candidate links from a representative rendered HTML page. Hydration parsing and relevance filtering were tested with synthetic source records.
- Real TikTok page navigation failed: HTTP proxy tunnel returned 403 Forbidden, and Chromium returned net::ERR_TUNNEL_CONNECTION_FAILED. No live candidate extraction is claimed. The Playwright provider is enabled and scheduled; network additions are persisted in the draft and await application.
- PostgreSQL/Redis health, Django login rendering, and a real Celery broker/worker/result round trip passed. Stop/restart and repeated startup passed.
- A real local HTTP flow passed with CSRF-protected approval, assignment, publisher acceptance, publication URL submission, metric submission, and report reconciliation. Temporary accounts/data were removed afterward.
- Django system checks and migration consistency passed. Deployment checks passed with DJANGO_DEBUG=0; the running loopback development instance intentionally uses DJANGO_DEBUG=1.
- Pinned dependency consistency, Python formatting, shell syntax, static collection, and fresh private local configuration generation passed.
- Database backup and restoration into a separate new database passed; the restored fixture candidate count matched. The verification database was removed afterward.
- Saved install_script, start_skill, repository mount/unborn state, TikTok web/asset domain additions, and the Telegram token requirement. Token saving also added api.telegram.org to the draft's network destinations.

Saving the draft does not apply network changes or publish the filesystem snapshot. Publication, fresh-task restoration, real bot delivery/callbacks, operational provider coverage, prediction quality, production load targets, and remaining extensions in STATUS.md are unverified.
