# Evidence interpretation

Use [the requirement traceability guide](../TRACEABILITY.md) to map each assessment item to its implementation, run steps, and evidence.

These files record this implementation's actual local and short-lived AWS acceptance results on 30 September 2026. They are not copied from the public reference repository.

The `verify.py` and `extra-checks.py` scripts capture local commands and outputs. JSON summaries record specific assertions. Linux services run inside Docker Desktop's VM; Moto emulates S3. The `aws-*` files summarize actual AWS tests. The AWS S3 transfer, application acceptance, Ansible idempotence, database restore and encrypted SMB checks ran on temporary resources that have since been deleted. The MediaLive input and channel were provisioned but never started, so there is no live ingest or archive evidence. `input.json` and `channel.json` are illustrative request templates, not deployed resources.

`mssql-actions.log` records the successful GitHub Actions SQL Server backup/restore acceptance run on an x86-64 Ubuntu runner. Its linked run is the source for the job-level result; no SQL Server runtime was run on the Apple Silicon Mac.

The report explains the remaining Windows reboot-mapping and live-stream/archive gaps, as well as physical-capacity and external-paging limits. Sparse-file tests do not allocate multi-terabyte payloads. Emulator throughput should not be used to estimate AWS performance.

Large reproducible `.ts` samples and private database dumps are excluded from the source archive. Regenerate the sample with `python3 scripts/verify.py streaming` and regenerate the backup with `bash scripts/backup.sh`.
