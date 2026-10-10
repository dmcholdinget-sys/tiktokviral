# VPS test deployment

Target: `/root/tiktokerviral` on 167.99.34.73. SSH port: 13877. Requested public HTTP port: 16700.

This deployment uses the separate Compose project `tiktokerviral_vps`. Only the Nginx gateway publishes a host port (16700). Database, Redis, Gunicorn, Celery, and Beat remain inside the project's network. It does not edit host Nginx, restart unrelated containers, or replace existing projects.

After inspecting the VPS and transferring source into the requested directory:

```bash
cd /root/tiktokerviral
bash deployment/deploy.sh
```

The script stops if Docker is missing or port 16700 belongs to another service. Configuration is generated once under `.deployment/` and preserved on reruns. Gunicorn runs with Django DEBUG disabled; the explicit testing override permits HTTP login cookies without HTTPS redirects. Static assets are served by this project's Nginx container, and private media still passes through application authorization.

Testing accounts are generated once. Their credentials are stored privately at `.deployment/test-logins.txt` on the server; passwords are never printed by deployment commands. Playwright discovery stays enabled. Demo data is labeled synthetic. Telegram remains unconfigured until a bot is supplied.

Image-build validation in the cloud is limited by container DNS/egress restrictions; deployment has not yet been executed on the VPS. Connection attempts to SSH port 13877 currently fail from this cloud environment, although HTTP access to the VPS now works through the cloud proxy. The proxy closes attempted SSH tunnels. The destination has been added to the saved environment network draft, but that does not apply live access automatically. No files or services on the VPS have been changed.

Use `docker compose -f deployment/compose.yaml logs --tail=100` for this project's logs. Use `docker compose -f deployment/compose.yaml stop` to stop this project without deleting volumes. Do not use `down -v` on a populated deployment.
