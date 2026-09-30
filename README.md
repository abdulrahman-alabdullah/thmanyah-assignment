# Thmanyah broadcast infrastructure assessment

An English report and reproducible implementation of the assessment, prepared on an Apple Silicon Mac. See [the PDF report](docs/Thmanyah-Infrastructure-Assessment.pdf), [report source](docs/REPORT.md), and [actual local evidence](docs/evidence/).

## Validation status

| Requirement | Implementation and evidence |
| --- | --- |
| Storage mounts, monitoring and large files | AWS Windows/Linux SMB 3.1.1 encrypted read/write passed in both directions; Windows read the logical length of a 1 TiB sparse file. Its mapped drive did not reconnect after reboot. |
| Docker application | Working Nginx/frontend, Python backend and PostgreSQL on separate networks; crash recovery, persistence, database outage, backup restore and isolated OOM checks executed. |
| Multipart S3 transfer | Three-part AWS S3 copy and SHA-256 match passed; test buckets and objects were deleted. |
| Terraform and Ansible | Three-VPC AWS stack deployed; VPN/private access, API read/write, database restore, and zero-change second Ansible run passed. The stack was destroyed afterward. |
| HEVC broadcast and S3 archive | Local Full HD HEVC validation passed; AWS accepted MediaLive configuration, but the channel was not started and no archive was verified. |
| Optional MSSQL | Omitted. PostgreSQL backup/restore is demonstrated for the required stack; it is not represented as MSSQL. |

## Run the local demonstration

Prerequisites: Docker Desktop running, Compose v2, Python 3 for the host-side verification scripts, about 4 GB of spare Docker RAM and internet access for the first image builds. Commands below run from the repository root.

```sh
bash scripts/setup.sh
docker compose up -d --build
python3 scripts/smoke.py
docker compose -f compose.s3.yaml up -d --build
docker compose -f compose.storage.yaml up -d --build
docker build -t thmanyah-streaming streaming
```

- Application: <http://localhost:8080>
- Node-RED: <http://localhost:1880>
- Prometheus: <http://localhost:9090>

Seed the local S3 object and verify the copy:

```sh
python3 scripts/verify.py s3
```

In Node-RED, click the small inject button beside **Copy configured object**. Its debug panel shows the result. The script's transfer uses server-side multipart copying and never loads the large object's bytes into the worker.

## Run the remaining checks

```sh
python3 scripts/verify.py app storage alerts streaming
```

`app` briefly stops/recreates this assessment's containers. `alerts` briefly unmounts and restores this lab's share. `storage` creates and removes a temporary 2 TiB sparse loop image inside Docker's Linux VM and tests a 1 TiB sparse file; it does not write 1 TiB or format a physical disk. These storage demonstrations use privileged containers and belong in an isolated lab.

For Terraform, download the tool and provider without AWS credentials, then validate:

```sh
docker run --rm -v "$PWD/infra:/work" -w /work \
  hashicorp/terraform:1.14.7 init -backend=false
python3 scripts/verify.py terraform
```

With Ansible installed, `python3 scripts/extra-checks.py` checks syntax, restores PostgreSQL into a temporary database, triggers the actual Node-RED flow and proves an isolated 64 MB OOM limit. Backups remain private under the ignored `backups/` directory.

## Deployment and submission

- [AWS infrastructure and VPN deployment](infra/DEPLOY.md)
- [MediaLive provisioning and archive checks](streaming/AWS.md)
- [OBS encoder settings](streaming/OBS.md)
- [Windows/Linux storage walkthrough](storage/README.md)
- [Demonstration and interview notes](docs/DEMO.md)
- [Final submission checklist](docs/SUBMISSION.md)

The report distinguishes cloud tests from local demonstrations. Remaining gaps are Windows mapping recovery after reboot and a real OBS-to-MediaLive ingest/archive check. Temporary AWS resources have been cleaned up; see the report evidence index.

Local credential files are in an owner-only directory and are ignored by Git. Compose file secrets are read-only mounts, not an encrypted secret manager. Use an IAM role for AWS S3 and an encrypted Ansible vault for server credentials. Do not publish state, plan files, credentials, private keys or database backups.

Stop the demo without deleting its data:

```sh
docker compose stop
docker compose -f compose.s3.yaml stop
docker compose -f compose.storage.yaml stop
```

## References

The supplied [public assessment repository](https://github.com/Alkhathami1/devops-tasks) was reviewed to compare scope and identify deployment considerations. Its code, report and execution evidence were not copied into this implementation. The supplied [Drive archive](https://drive.google.com/file/d/1P_T2nciGlpGpV2j-qM3Js4vdCLGwguEP/view) provided IBM Plex Sans Arabic fonts; their license is preserved under `docs/assets/`. Technical sources are linked in the report.
