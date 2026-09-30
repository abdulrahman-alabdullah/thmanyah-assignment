# Submission checklist

- Read `docs/REPORT.md`, the PDF, and `docs/TRACEABILITY.md`; confirm you can explain each design choice, status, and limitation.
- Submit the candidate's repository, `abdulrahman-alabdullah/thmanyah-assignment`, through the company's requested channel. Choose repository visibility according to the hiring instructions. The public reference repository is someone else's work and is not this submission.
- Include the PDF report and redacted evidence. Keep local-only, AWS, failed, and unverified checks labeled accurately.
- Do not upload `secrets/` contents, `.env`, `*.tfvars`, `.terraform/`, state, plan files, private keys, backups or local video test files. Font licenses should remain included.
- Remaining acceptance gaps: resolve the Windows drive mapping after reboot and complete an OBS-to-MediaLive broadcast with a verified S3 archive object. The temporary AWS stack was deleted; deploying again requires a cost review and cleanup plan. Do not describe either gap as passed unless new evidence is added.
- Record the local demonstration following `DEMO.md` and confirm the recording contains no credentials.
- Share the repository/report/recording with the assessment recipient using the requested submission channel. Keep access available for at least their seven-day review window.
- Stop local services when no longer needed. The README's `docker compose down` commands preserve named volumes; add `-v` only when you intend to erase local demo data. Any cloud deployment has a separate billing and cleanup obligation.
