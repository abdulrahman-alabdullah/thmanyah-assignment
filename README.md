# Thmanyah infrastructure engineering assessment

English implementation and evidence for the supplied broadcast infrastructure assessment. The report summarizes the design and results; the traceability guide maps each requested item to its code, run instructions, evidence, and current status.

## Start here

For a first review, read these in order:

1. [Assessment report](docs/Thmanyah-Infrastructure-Assessment.pdf) for the design, results, limitations, and remaining acceptance checks.
2. [Requirement-to-code traceability](docs/TRACEABILITY.md) to find the exact implementation and evidence for every task.
3. [Local demonstration](docs/DEMO.md) for a short walkthrough, then use the task guides below to reproduce a specific test.

The cloud stack was temporary and has been destroyed. The report is explicit about checks that passed, the Windows reboot mapping failure, and the incomplete OBS-to-MediaLive archive test.

## Task map

| Assessment task | Start with | Code and evidence | Current result |
| --- | --- | --- | --- |
| Windows/Linux storage, persistence, monitoring, alerts, and 1 TiB files | [Storage walkthrough](storage/README.md) | `storage/`, `docs/evidence/smb-*`, `docs/evidence/xfs-sparse.log`, and `docs/evidence/aws-*.log` | Local SMB/monitoring tests passed. AWS SMB worked both ways and Windows read a logical 1 TiB sparse file. Windows `Z:` mapping did not reconnect after reboot. |
| Docker application, automation, secrets, recovery, and resource allocation | [Local run steps](#run-the-local-demonstration) and [traceability map](docs/TRACEABILITY.md#task-2-docker-application) | `compose.yaml`, `app/`, `nginx/`, `scripts/`; `docs/evidence/app-*`, `backend-*`, `database-*`, `oom-*`, `resource-limits.log` | Local functional, recovery, persistence, resource-limit, and PostgreSQL restore checks passed. |
| Optional MSSQL database, backup, and restore | [Traceability map](docs/TRACEABILITY.md#optional-task-mssql) | No MSSQL implementation or evidence is included. | Optional task not implemented; PostgreSQL evidence is clearly identified as PostgreSQL. |
| S3 multipart bucket-to-bucket copy and logs | [S3 implementation and status](docs/TRACEABILITY.md#task-3-s3-multipart-copy-through-node-red) | `s3/`, `tests/test_s3.py`, `docs/evidence/s3-tests.log`, `nodered-flow.log`, `aws-s3-multipart.log` | Local Moto and real three-part AWS copy checks passed; temporary AWS buckets and objects were removed. |
| Three-VPC Terraform infrastructure, Ansible configuration, and VPN | [AWS deployment guide](infra/DEPLOY.md) | `infra/`, `infra/ansible/`; `docs/evidence/terraform-*`, `ansible-syntax.log`, `aws-acceptance.log`, `aws-ansible-idempotence.log`, `aws-database-restore.log` | Temporary AWS deployment, VPN/private access, app request, DB restore, and zero-change second Ansible run passed. The stack was destroyed. |
| OBS/vMix HEVC broadcast to Elemental with S3 archive | [MediaLive guide](streaming/AWS.md) and [OBS settings](streaming/OBS.md) | `streaming/`, `docs/evidence/hevc-*`, `medialive-schema.log`, and report section 6 | Local HEVC/AAC generation passed and AWS accepted the channel configuration. No live ingest or S3 archive was verified. |

The [traceability guide](docs/TRACEABILITY.md) has the detailed sub-requirement breakdown, exact commands, evidence filenames, and qualifications for every status.

## Run the local demonstration

Prerequisites: Docker Desktop, Docker Compose v2, Python 3, about 4 GB of Docker memory, and internet access for the first image builds. Run commands from the repository root.

```sh
bash scripts/setup.sh
docker compose up -d --build
python3 scripts/smoke.py
```

The application is at <http://localhost:8080>. Start the independent S3 and storage labs when needed:

```sh
docker compose -f compose.s3.yaml up -d --build
docker compose -f compose.storage.yaml up -d --build
```

When the S3 lab is running, Node-RED is at <http://localhost:1880>; when the storage lab is running, Prometheus is at <http://localhost:9090>. To run the S3 integrity test, run `python3 scripts/verify.py s3` after starting the S3 lab. In Node-RED, trigger **Copy configured object** to see the flow result. The worker uses S3-side multipart copy so object bytes do not pass through the worker.

Run the other local acceptance checks after starting the related services:

```sh
python3 scripts/verify.py app storage alerts
docker build -t thmanyah-streaming streaming
python3 scripts/verify.py streaming
```

The `storage` check creates and removes a temporary sparse loop image in Docker's Linux VM. It does not write 1 TiB or format a physical disk. These storage tests require a privileged container and an isolated lab. `streaming` builds a local HEVC test clip and verifies the encoded streams; it does not send a live broadcast to AWS.

## Validate Terraform and Ansible locally

These checks do not create AWS resources:

```sh
docker run --rm -v "$PWD/infra:/work" -w /work \
  hashicorp/terraform:1.14.7 init -backend=false
python3 scripts/verify.py terraform
```

With the application and S3 labs running, and Ansible plus its required collections installed, `python3 scripts/extra-checks.py` runs syntax checks, a PostgreSQL restore check, the Node-RED flow, and an isolated 64 MB OOM test. The actual AWS deployment procedure is in [infra/DEPLOY.md](infra/DEPLOY.md); its deployment commands create billable resources and require deliberate cleanup.

## Stop the local demonstration

These commands stop and remove the demo containers and networks while preserving named data volumes:

```sh
docker compose down
docker compose -f compose.s3.yaml down
docker compose -f compose.storage.yaml down
```

Add `-v` only if you intentionally want to delete the local demo data volumes. AWS cleanup is separate; do not leave a test deployment running after acceptance checks.

## Submission and security

- [Final submission checklist](docs/SUBMISSION.md)
- [Interview walkthrough](docs/DEMO.md)
- [Timestamped and summarized evidence](docs/evidence/README.md)

Local credentials are stored in the ignored, owner-only `secrets/` directory. They are not managed or encrypted by Compose. Use IAM roles for AWS workloads and Ansible Vault for deployment secrets. Never commit credentials, `.tfvars`, Terraform state/plans, private keys, backups, SRT URLs containing passphrases, or unredacted host output. Check `git status` and inspect the generated archive before submission.

The supplied [public assessment repository](https://github.com/Alkhathami1/devops-tasks) was reviewed as a reference; its code, report, and evidence were not copied. The supplied [Drive archive](https://drive.google.com/file/d/1P_T2nciGlpGpV2j-qM3Js4vdCLGwguEP/view) provided the IBM Plex Sans Arabic fonts; the font license is preserved under `docs/assets/`.
