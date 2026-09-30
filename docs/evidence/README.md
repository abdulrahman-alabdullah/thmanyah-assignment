# Evidence interpretation

These files record this implementation's actual local commands and results on 30 September 2026. They are not copied from the public reference repository.

The `verify.py` and `extra-checks.py` scripts capture commands, UTC times and outputs. JSON summaries record specific assertions. Linux services run inside Docker Desktop's VM; Moto emulates S3. `input.json` and `channel.json` contain illustrative identifiers and are validated request templates, not deployed AWS resources.

The report explains the Windows, AWS, host-reboot, physical-capacity and external-paging checks that have not been performed. File-size planning and sparse-file tests do not transmit or allocate multi-terabyte payloads. Emulator throughput should not be used to estimate AWS performance.

Large reproducible `.ts` samples and private database dumps are excluded from the source archive. Regenerate the sample with `python3 scripts/verify.py streaming` and regenerate the backup with `bash scripts/backup.sh`.
