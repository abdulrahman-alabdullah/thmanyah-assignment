# Assessment requirement traceability

This page maps the supplied assessment wording to the implementation, repeatable checks, evidence, and the result we can support. “Pass” is scoped to the environment named; local simulation is not represented as Windows, AWS, or production validation. The PDF report gives the architecture and reasoning; this page is the reviewer’s index into the repository.

## Task 1: Cross-platform storage

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| Mount a Windows volume on Linux; explain protocol, rationale, steps, and persistence | [Storage walkthrough](../storage/README.md); [Windows share setup](../storage/windows/setup-share.ps1); [Linux mount example](../storage/linux/windows-share.mount.example); [report sections 2.1–2.2](REPORT.md#2-cross-platform-storage-and-large-media-files) | [aws-linux-smb.log](evidence/aws-linux-smb.log): Windows share mounted from Linux with encrypted SMB 3.1.1; Linux-to-Windows file write and read passed. A full Linux-host reboot persistence test was not run. |
| Monitor share and disk performance; alert against a service objective | [Probe](../storage/probe.py), [Prometheus configuration](../storage/prometheus.yml), [alert rules](../storage/alerts.yml), [runbook](../storage/README.md#monitoring-and-alerts) | [storage-probe.log](evidence/storage-probe.log), [alert rules](evidence/storage-alert-rules.log), [firing and resolution results](evidence/alert-firing.json). The local alert drill passed. Windows production counters and external paging were not configured. |
| Choose a filesystem that supports a 1 TB file and justify it | [XFS demonstration](../storage/xfs-demo.sh), [design notes](../storage/README.md#local-substitute-and-large-file-interpretation), [report section 2.1](REPORT.md#2-cross-platform-storage-and-large-media-files) | [xfs-sparse.log](evidence/xfs-sparse.log): Linux/XFS accepted a 1 TiB sparse file. [aws-windows-largefile.log](evidence/aws-windows-largefile.log): Windows read the same logical file length over SMB. Neither test allocated or wrote 1 TiB of real media. |
| Reverse direction: mount a Linux share on Windows | [Samba share](../storage/smb.conf), [AWS lab playbook](../storage/aws-lab.yml), [Windows mapping script](../storage/windows/map-linux-share.ps1), [walkthrough](../storage/README.md#linux-share-mounted-on-windows) | [aws-windows-smb.log](evidence/aws-windows-smb.log): Windows wrote to the Linux share; Windows reported SMB 3.1.1 and encryption. [aws-windows-reboot.log](evidence/aws-windows-reboot.log): persistent `Z:` mapping did not reconnect after Windows reboot. |

Repeat local checks after starting `compose.storage.yaml`:

```sh
python3 scripts/verify.py storage alerts
```

The AWS Windows interoperability check used a temporary instance and has been cleaned up. The reboot mapping failure is an open issue, not a pass.

## Task 2: Docker application

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| Separate database, backend, frontend, and reverse proxy communicating on private Docker networks | [Compose file](../compose.yaml), [backend](../app/server.py), [Nginx frontend and proxy](../nginx/), [report section 3.1](REPORT.md#3-docker-application-automation-and-recovery) | [app-smoke.log](evidence/app-smoke.log): local application checks; DB is not published and its network is internal. |
| Automate setup and handle secrets safely | [Local setup](../scripts/setup.sh), [Compose secrets](../compose.yaml), [backup script](../scripts/backup.sh) | Local generated credentials are ignored and mounted as files. This is a local Compose mechanism, not a managed/encrypted cloud secret store. |
| Explain recovery after process, host, database, and memory failures | [Recovery behavior](REPORT.md#3-docker-application-automation-and-recovery), [verification runner](../scripts/verify.py), [extra checks](../scripts/extra-checks.py) | [app-recovery.json](evidence/app-recovery.json), [backend crash/recreate logs](evidence/), [database stop/start logs](evidence/), and [OOM check](evidence/oom-limit.log): process recovery, DB outage behavior, persistence, and memory isolation passed locally. A whole physical Mac shutdown recovery drill was not run. |
| Explain CPU, storage, and RAM allocation | [Compose limits](../compose.yaml), [report section 3.3](REPORT.md) | [resource-limits.log](evidence/resource-limits.log) records the deployed local container limits. |

Start with `bash scripts/setup.sh`, then `docker compose up -d --build`; run `python3 scripts/verify.py app` while the application stack is up.

## Optional task: MSSQL

The assessment marks MSSQL as optional. This task is implemented separately from the PostgreSQL application database; PostgreSQL evidence is not counted as MSSQL evidence.

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| Create a SQL Server database, table, and representative row | [Idempotent schema and seed](../mssql/init.sql), [private Compose service](../compose.mssql.yaml), [run guide](MSSQL.md) | [GitHub Actions evidence](evidence/mssql-actions.log): x86-64 run passed using the table constraints and stable-key broadcast sample. |
| Automate database backup | [Backup script](../mssql/backup.sh), [daily systemd timer](../mssql/thmanyah-mssql-backup.timer), [service](../mssql/thmanyah-mssql-backup.service) | The successful x86-64 run created a timestamped compressed/checksummed backup, passed `RESTORE VERIFYONLY`, and retained the newest 14 files; an installable daily timer is documented. |
| Restore the backup and verify data | [Acceptance script](../mssql/acceptance.sh), [GitHub Actions workflow](../.github/workflows/mssql.yml) | The successful run restored into a separate database, checked the seeded event, dropped the temporary restore, and destroyed its isolated test volume. |

On Apple Silicon, follow the guide's x86-64 CI path; Microsoft does not support SQL Server Linux containers on Apple Silicon hosts. The local Mac is not claimed as a successful SQL Server runtime.

## Task 3: S3 multipart copy through Node-RED

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| Copy between buckets using multipart upload/copy, use the maximum object/part limits, and log the operation | [Multipart copy worker](../s3/multipart_copy.py), [HTTP worker](../s3/worker.py), [Node-RED flow](../s3/flows.json), [worker image](../s3/Dockerfile), [report section 4](REPORT.md#4-node-red-and-s3-multipart-transfer) | [s3-tests.log](evidence/s3-tests.log) and [nodered-flow.log](evidence/nodered-flow.log): local Moto multipart and flow checks. [aws-s3-multipart.log](evidence/aws-s3-multipart.log): real three-part S3 copy with matching SHA-256. Planner boundary tests enforce S3's documented 10,000-part, 5 MiB–5 GiB part, 48.8 TiB object limits. The maximum-sized object was not transmitted. Temporary AWS objects and buckets were removed. |

Start `compose.s3.yaml`, run `python3 scripts/verify.py s3`, and trigger **Copy configured object** in Node-RED at <http://localhost:1880> to replay the local flow.

## Task 4: Three-tier Terraform and Ansible infrastructure

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| Three public, apps, and database VPCs with tier segmentation and a three-tier request path | [Terraform](../infra/main.tf), [variables](../infra/variables.tf), [deployment guide](../infra/DEPLOY.md), [report section 5](REPORT.md#5-three-tier-aws-infrastructure-and-ansible) | [aws-acceptance.log](evidence/aws-acceptance.log): temporary tagged three-VPC deployment, public API read/write, and private host reachability. No assessment-tagged VPCs or running instances remain. |
| Configure servers with Ansible | [Playbook](../infra/ansible/site.yml), [inventory example](../infra/ansible/inventory.example.yml), [vault example](../infra/ansible/vault.yml.example) | [aws-ansible-idempotence.log](evidence/aws-ansible-idempotence.log): second run had zero changes on all three Linux hosts. |
| Provide private VPN access, including app and database tiers | [WireGuard template](../infra/ansible/templates/wg0.conf.j2), [deployment guide](../infra/DEPLOY.md#bootstrap-the-vpn-before-configuring-private-hosts) | [aws-acceptance.log](evidence/aws-acceptance.log): tunnel and private readiness check passed. Application and database instances had no public addresses. |
| Configure application/database services and validate recovery | [Ansible playbook](../infra/ansible/site.yml), [backup script](../scripts/backup.sh), [restore verification](../scripts/extra-checks.py), [report section 5.2](REPORT.md#5-three-tier-aws-infrastructure-and-ansible) | [aws-database-restore.log](evidence/aws-database-restore.log): restored a temporary database, verified the acceptance marker, then dropped the temporary copy. |

Local syntax and format checks are `python3 scripts/verify.py terraform` and `python3 scripts/extra-checks.py`. The AWS deployment was temporary, had no HA claim, and was destroyed after testing. Review cost and cleanup steps in [infra/DEPLOY.md](../infra/DEPLOY.md) before any future deployment.

## Task 5: HEVC broadcast to AWS Elemental and S3 archive

| Requested item | Implementation and run guide | Evidence and result |
| --- | --- | --- |
| OBS/vMix, Full HD or higher, at least 12 Mbps video, 192 kbps audio, HEVC | [OBS settings](../streaming/OBS.md), [local encoder](../streaming/encode.sh), [report section 6](REPORT.md#6-hevc-broadcast-and-elemental-archive) | [hevc-probe.log](evidence/hevc-probe.log) and [streaming-summary.json](evidence/streaming-summary.json): local 1920×1080, 25 fps HEVC/AAC test clip passed. OBS-to-AWS transmission was not verified. |
| Optional BPP justification | [Formula and assumptions](../streaming/OBS.md) | `12,000,000 / (1920 × 1080 × 25) = 0.23148` bits per pixel per frame. This normalizes bitrate; it does not guarantee visual quality. |
| Record an Elemental output to S3 as `.mxf` or `.ts` and document the steps | [MediaLive procedure](../streaming/AWS.md), [OBS procedure](../streaming/OBS.md), [request generator](../streaming/render-config.py) | AWS accepted the temporary SRT input and HEVC/archive channel configuration. The channel remained IDLE and was deleted without being started; no live ingest or archive object was verified. `medialive-schema.log` is a schema check, not live-stream evidence. |

Run `docker build -t thmanyah-streaming streaming` and `python3 scripts/verify.py streaming` for the local encode/probe. A live test additionally needs an active MediaLive deployment and an installed OBS HEVC output path; do not mark the broadcast complete until a real S3 archive object has been inspected.

## Deliverable and evidence locations

- [Report source](REPORT.md) and [PDF report](Thmanyah-Infrastructure-Assessment.pdf)
- [Evidence index and interpretation](evidence/README.md)
- [Submission checklist](SUBMISSION.md)
- [Five-minute walkthrough](DEMO.md)

Evidence files contain test results only. Do not add AWS credentials, private keys, Terraform state/plans, database passwords, SRT passphrases, or unredacted machine output.
