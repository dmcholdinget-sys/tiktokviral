#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -ne 2 ]; then echo 'Usage: scripts/restore.sh BACKUP.dump NEW_DATABASE_NAME' >&2; exit 2; fi
file="$1"; database="$2"
[[ "$database" =~ ^[a-z][a-z0-9_]{0,62}$ ]] || { echo 'Invalid database name' >&2; exit 2; }
test -s "$file"
# createdb intentionally fails if the target already exists. Never overwrite a database.
docker compose exec -T db sh -c 'createdb -U "$POSTGRES_USER" "$1"' sh "$database"
docker compose exec -T db sh -c 'pg_restore --exit-on-error --no-owner -U "$POSTGRES_USER" -d "$1"' sh "$database" < "$file"
printf 'Restored into new database: %s\n' "$database"
