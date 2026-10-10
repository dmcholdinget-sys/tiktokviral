# Codex CLI deployment handoff

## Authorized task

Deploy this repository to the user's existing VPS. The user authorized root SSH access and publishing for HTTP testing. The VPS hosts many other projects: preserve them and inspect before making changes.

- Repository: https://github.com/dmcholdinget-sys/tiktokviral
- VPS: 167.99.34.73
- SSH username: root
- SSH port: 13877
- Target directory: /root/tiktokerviral (spelling intentional)
- Public HTTP port: 16700
- Expected test URL: http://167.99.34.73:16700

Use the operator's existing SSH authentication. The cloud session's private key is deliberately not included. Never request private keys/passwords in chat, disable SSH host-key verification, or print credentials.

## Current state

No source files or services were changed on the VPS. Cloud HTTP access works, but direct SSH connections are refused and the HTTP proxy closes SSH tunnels. Continue from a local Codex CLI session that can connect directly.

The application has Django/PostgreSQL/Redis/Celery, public-page Playwright discovery (enabled), ranking/review, publisher isolation, assignments, Telegram integration, publishing feedback, metrics, and reports. Demo records are synthetic and labeled. See docs/STATUS.md for remaining PRD extensions; do not claim the entire PRD is production complete.

39 application tests and 2 webhook-registration tests previously passed. Local Docker deployment configuration, shell syntax, and HTTP settings checks passed. The deployment image build failed in the cloud because the build container could not resolve package hosts; the image build and deployment have not passed on the VPS yet.

## Execute and verify

1. Read README.md, deployment/README.md, deployment/compose.yaml, and deployment/deploy.sh. Inspect the VPS OS, Docker/Compose versions, existing containers/services, resource availability, firewall state, and whether port 16700 is free. Do not change global Nginx, stop unrelated services, or reset firewall rules.
2. Check /root/tiktokerviral before uploading/cloning. Preserve any existing files or local work. Clone this repository or transfer source into that exact directory once safe. Do not copy cloud .env, database data, or SSH keys.
3. Run bash deployment/deploy.sh from the checkout. It generates private local runtime/database secrets once, builds an isolated image with Chromium, migrates PostgreSQL, collects static assets, initializes demo data/testing accounts, and starts the dedicated tiktokerviral_vps Compose project. Only its gateway exposes port 16700.
4. Investigate any failed command and rerun after a supported correction. Preserve TLS, checksums, and package verification. If Docker is missing, inspect existing deployment conventions before installing shared host packages.
5. Verify HTTP login both from the VPS and externally, then authenticate and test review -> assignment -> acceptance -> publication -> metrics -> report reconciliation. Confirm Celery and Beat. Run Playwright discovery on the VPS and inspect the actual extracted candidates/errors: Chromium fixture extraction does not prove live TikTok access. Keep discovery enabled and visible when it fails; do not bypass access controls.
6. Testing credentials are generated privately in /root/tiktokerviral/.deployment/test-logins.txt. Share them securely with the user, without printing them in build logs or committing them. HTTP is explicitly requested for testing; Django DEBUG stays false. Telegram needs a bot token and a reachable HTTPS webhook for actual callback testing.
7. Report the tested public URL, deployment status, remaining external blockers, and where test credentials are available. Never claim publishing succeeded based only on a PID or open port.

## Suggested local Codex request

“Read docs/CODEX_CLI_HANDOFF.md and deploy this application to root@167.99.34.73 using SSH port 13877, in /root/tiktokerviral, served over HTTP port 16700. Inspect and preserve the other projects, execute deployment, and verify the application and live discovery.”
