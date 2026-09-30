#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
umask 077
filename="backups/broadcast-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T db pg_dump -U broadcast -d broadcast -Fc > "$filename"
echo "Created $filename"
# On a Linux deployment, schedule at 02:00 daily with systemd/cron and upload
# encrypted backups to a separate bucket. Verify a restore before deleting old copies.
