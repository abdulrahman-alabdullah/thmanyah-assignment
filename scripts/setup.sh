#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p secrets docs/evidence
umask 077
chmod 700 secrets
for name in db_password smb_password; do
  if [ ! -s "secrets/$name.txt" ]; then openssl rand -hex 24 > "secrets/$name.txt"; fi
done
# Compose file secrets are read-only bind mounts. A readable file inside an
# owner-only host directory supports non-root containers on Linux and macOS.
chmod 444 secrets/db_password.txt secrets/smb_password.txt
echo 'Local secrets prepared. These files are ignored by Git.'
