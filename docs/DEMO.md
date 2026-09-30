# Demonstration and interview preparation

## Five-minute recording

1. Open the README status table and state which checks ran locally and which require AWS/Windows access. This avoids suggesting that a schema check is a deployed system.
2. Open `http://localhost:8080`, save a note, reload and show it persists. Explain the path: Nginx → private backend → private PostgreSQL. Show `docker compose ps` and `docs/evidence/app-recovery.json`.
3. Show the network and resource declarations in `compose.yaml`. Explain why the database has no published port, why it needs a persistent volume, and how the app returns a temporary 503 if it loses its database.
4. Open Node-RED at port 1880 and trigger the copy. Show the debug output, three part completions and the SHA-256 test. Explain why server-side `UploadPartCopy` avoids downloading a large broadcast asset.
5. Open Prometheus at port 9090. Show the `share_probe_success` query and the saved firing/resolved evidence. Show the negotiated SMB dialect and the sparse-file result, including zero allocated blocks.
6. Show the local HEVC probe and the three-VPC diagram in the report. Finish with the exact AWS/Windows checks still needed. Do not show secrets, a real SRT URL containing its passphrase, private keys or Terraform state.

## Decisions to explain in your own words

- A share exports files over SMB. iSCSI exports blocks and introduces a different ownership/concurrent-mount problem.
- Both share permissions and filesystem permissions must authorize the user.
- A sparse 1 TiB file is a file-size test. It is not a test that writes 1 TiB or proves available physical capacity.
- `restart: unless-stopped` recovers an exited container after the daemon is running. It does not start Docker Desktop when macOS boots, guarantee availability during host failure, restart merely unhealthy containers, or restore lost data.
- Compose file secrets are local mounts. They do not provide a managed vault, encryption at rest or automatic rotation.
- A multipart ETag is not a universal whole-file MD5 checksum. The local integration check separately verifies SHA-256 equality.
- VPC peering is non-transitive, so all required tier-to-tier paths have direct peers/routes. NAT placement must respect that restriction.
- WireGuard establishes authenticated private access. Security groups still restrict which services that access can reach.
- HEVC is a codec, MPEG-TS a container, SRT a transport, and S3 the archive destination. MediaLive's RTMP input supports H.264; this design uses SRT for HEVC.
- BPP expresses bitrate per pixel per frame, not a guarantee of picture quality. Keep the assessment's 12 Mbps floor.

## Completion order before the deadline

First review and understand the local application, S3 worker and evidence. Record the working local demo. If an AWS account becomes available in time, run the reviewed Terraform deployment, bootstrap the VPN, configure the private hosts and perform the live broadcast/real archive checks. Obtain Windows access to complete the bidirectional mount and reboot checks. Add the resulting evidence and revise the status table only after those tests pass.
