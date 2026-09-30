#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

: "${MSSQL_SA_PASSWORD:?Set MSSQL_SA_PASSWORD in the shell}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="/var/opt/mssql/data/AssessmentMSSQL_${stamp}.bak"
sql="BACKUP DATABASE [AssessmentMSSQL] TO DISK = N'${backup_path}' WITH INIT, COMPRESSION, CHECKSUM; RESTORE VERIFYONLY FROM DISK = N'${backup_path}' WITH CHECKSUM;"

docker compose -f compose.mssql.yaml exec -T mssql \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -b -Q "$sql"
printf 'Backup created and verified: %s\n' "$backup_path"
