# Optional MSSQL task

This implements the assessment's optional Microsoft SQL Server task: create a database and table, insert a representative broadcast row, take a compressed/checksummed backup, verify the backup, restore it under a separate name, and read back the seed row.

## Run on a supported host

Microsoft supports SQL Server Linux containers on x86-64 Linux hosts ([Microsoft container deployment requirements](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-deployment?view=sql-server-ver17)). This Compose setup pins the SQL Server major version to 2022, runs Developer edition for this non-production assessment, keeps the SQL port private, caps the container at two CPUs and 2 GiB RAM, and persists the SQL data and backups in a named Docker volume. Apple Silicon Docker emulation is not a supported SQL Server host; use the included GitHub Actions workflow or a real x86-64 Linux machine. Azure SQL Edge was retired in 2025 and is not used ([Microsoft lifecycle notice](https://learn.microsoft.com/en-us/lifecycle/products/azure-sql-edge)).

On an x86-64 Linux host with Docker Compose v2:

```sh
export MSSQL_SA_PASSWORD='Use-a-unique-strong-password-here-42!'
docker compose -f compose.mssql.yaml up -d
docker compose -f compose.mssql.yaml exec -T mssql \
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -b -i /assessment/init.sql
bash mssql/backup.sh
```

`init.sql` is safe to rerun: it creates the table only if absent and inserts its stable-key sample row only once. The backup script creates a UTC timestamped `.bak`, enables compression and checksum, then runs `RESTORE VERIFYONLY` with checksum validation. Keep `MSSQL_SA_PASSWORD` out of shell history and logs; for a long-running host, inject it from the host's secret manager.

## Automated schedule

For unattended daily backups on the supported Linux host, the repository includes a systemd service and timer. The unit files assume the repository is installed at `/opt/thmanyah-assignment`; change that path in the service if needed. Create `/etc/thmanyah/mssql.env` with `MSSQL_SA_PASSWORD='...'`, restrict it to root (`chmod 600`), then install and enable the units:

```sh
sudo install -m 0644 mssql/thmanyah-mssql-backup.service /etc/systemd/system/
sudo install -m 0644 mssql/thmanyah-mssql-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now thmanyah-mssql-backup.timer
systemctl list-timers thmanyah-mssql-backup.timer
```

The timer runs daily at 02:00 UTC and catches up a missed run after host downtime. The named Docker volume preserves database and backup files across container replacement. Production use should additionally copy encrypted backups to a separate failure domain and regularly test restore procedures.

## Acceptance test and Mac workflow

The test starts an isolated SQL Server container, applies the schema and seed, creates and verifies a backup, restores it as `AssessmentMSSQL_RestoreCheck`, checks the expected row, then removes all test containers and volumes. Run it locally on supported x86-64 Linux:

```sh
export MSSQL_SA_PASSWORD='Use-a-unique-strong-password-here-42!'
bash mssql/acceptance.sh
```

On this Apple Silicon Mac, the supported run is the GitHub Actions workflow `.github/workflows/mssql.yml`, which executes on GitHub's x86-64 Ubuntu runner without AWS resources or credentials. The acceptance run passed on 2026-09-30; see [the recorded run](evidence/mssql-actions.log). The acceptance script destroys its isolated test volume on exit. A manual/local SQL Server deployment uses a persistent named volume; remove it only when its database and backups are no longer needed:

```sh
docker compose -f compose.mssql.yaml down
# Destructive to local MSSQL data and backups:
docker compose -f compose.mssql.yaml down --volumes
```
