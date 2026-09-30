#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MSSQL_SA_PASSWORD:?Set MSSQL_SA_PASSWORD in the shell}"

export COMPOSE_PROJECT_NAME=thmanyah-mssql-acceptance
compose=(docker compose -p "$COMPOSE_PROJECT_NAME" -f compose.mssql.yaml)
cleanup() { "${compose[@]}" down --volumes --remove-orphans; }
trap cleanup EXIT
"${compose[@]}" up -d

run_sqlcmd() {
  SQLCMDPASSWORD="$MSSQL_SA_PASSWORD" "${compose[@]}" exec -T -e SQLCMDPASSWORD mssql \
    /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -C -b "$@"
}

ready=0
for _ in $(seq 1 60); do
  if run_sqlcmd -Q 'SELECT 1' >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 5
done
if [[ "$ready" != 1 ]]; then
  "${compose[@]}" logs mssql
  echo 'SQL Server did not become ready within 5 minutes.' >&2
  exit 1
fi

run_sqlcmd -i /assessment/init.sql
bash mssql/backup.sh

backup_path="$("${compose[@]}" exec -T mssql /bin/bash -lc 'ls -1t /var/opt/mssql/data/AssessmentMSSQL_*.bak | head -n 1' | tr -d '\r')"
[[ -n "$backup_path" ]]
restore_sql="IF DB_ID(N'AssessmentMSSQL_RestoreCheck') IS NOT NULL BEGIN ALTER DATABASE AssessmentMSSQL_RestoreCheck SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE AssessmentMSSQL_RestoreCheck; END; RESTORE DATABASE [AssessmentMSSQL_RestoreCheck] FROM DISK = N'${backup_path}' WITH MOVE N'AssessmentMSSQL' TO N'/var/opt/mssql/data/AssessmentMSSQL_RestoreCheck.mdf', MOVE N'AssessmentMSSQL_log' TO N'/var/opt/mssql/data/AssessmentMSSQL_RestoreCheck_log.ldf', REPLACE, CHECKSUM; IF NOT EXISTS (SELECT 1 FROM AssessmentMSSQL_RestoreCheck.dbo.BroadcastEvents WHERE event_key = N'assessment-seed-001') THROW 51001, 'Restored database is missing its seed row.', 1; SELECT 'RESTORE_OK' AS result, COUNT(*) AS restored_event_count FROM AssessmentMSSQL_RestoreCheck.dbo.BroadcastEvents; DROP DATABASE AssessmentMSSQL_RestoreCheck;"
run_sqlcmd -Q "$restore_sql"
echo 'MSSQL acceptance passed: schema, idempotent seed, backup checksum, and restore/readback.'
