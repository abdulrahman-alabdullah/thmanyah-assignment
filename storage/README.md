# Cross-platform storage walkthrough

## Windows share mounted on Linux

1. On a Windows host, use an NTFS data volume with enough real free space for the intended workload. Do not reformat an existing disk. Run `windows/setup-share.ps1 -LinuxClientIP LINUX_IP` as administrator. It creates a dedicated account, applies both filesystem and share permissions, disables SMB1 and permits TCP 445 from the specified client.
2. On Debian/Ubuntu Linux, install `cifs-utils` and create `/mnt/windows-media`. Create `/etc/smb-credentials` with `username=media`, `password=YOUR_PASSWORD` and, when needed, `domain=WINDOWS_HOST`. Make the file root-owned with mode 0600. Enter the password through a secure editor rather than embedding it in a command or repository.
3. Run `sudo mount -t cifs //WINDOWS_IP/media /mnt/windows-media -o credentials=/etc/smb-credentials,vers=3.1.1,seal,uid=1000,gid=1000,nosuid,nodev,noexec`. SMB is file access; the remote Windows filesystem remains owned and managed by Windows.
4. Write a uniquely named file on Linux and read it on Windows, then write from Windows and read on Linux. Compare a SHA-256 digest for a larger file. Inspect `findmnt /mnt/windows-media`, `/proc/fs/cifs/DebugData`, and Windows `Get-SmbConnection` for dialect and encryption.
5. Adapt the example fstab entry in `linux/windows-share.mount.example`. `_netdev` establishes network ordering and `x-systemd.automount` triggers mounting when the path is accessed. `nofail` prevents an unavailable share from blocking system boot; it does not guarantee the share is available to an application. Use `RequiresMountsFor=/mnt/windows-media` on any dependent systemd service and check readiness before writing.
6. Run `sudo systemctl daemon-reload` and access the path. In the temporary AWS lab, SMB 3.1.1 encryption and bidirectional file exchange passed, and Windows read the logical size of a 1 TiB Linux-created sparse file. The Windows `Z:` drive mapping did not reconnect after a full Windows reboot. The Linux fstab mount was not tested across a Linux host reboot. See `docs/evidence/aws-windows-reboot.log` and `docs/evidence/aws-linux-smb.log`.

## Linux share mounted on Windows

1. Install Samba on Linux, create an XFS filesystem on a dedicated data volume, mount it at `/srv/media`, and persist it in fstab using its UUID. Back up data and confirm the exact device before formatting. The delivered `xfs-demo.sh` instead formats a fresh temporary loop image, making the local demonstration reversible.
2. Create the `media` Linux user, set its Samba password with `smbpasswd -a media`, and grant that user access to `/srv/media`. Use `smb.conf` from this directory. Require SMB 3.1.1 and encryption, disable guest fallback, and enable/start the Samba service.
3. Restrict TCP 445 to the Windows client's private or VPN address. Do not expose SMB to the public internet.
4. On Windows, run `windows/map-linux-share.ps1 -LinuxServerIP LINUX_IP`. The script prompts for credentials and uses a persistent `Z:` mapping with saved credentials. Windows Credential Manager stores the credential; no plaintext password is stored in the repository.
5. Confirm `Get-SmbConnection` reports the expected dialect and encryption. Read/write a test file from both hosts, compare hashes, then log out/reboot and test the persistent mapping again.

## Local substitute and large-file interpretation

`compose.storage.yaml` runs Samba and a Linux CIFS client in Docker's VM. This proves real SMB encryption, kernel mounting and monitoring, but neither container is Windows. It is not a completed Windows interoperability test.

XFS was selected for large sequential media files, extent allocation, journaling and online growth. NTFS on the Windows server is also a suitable filesystem for 1 TB files. SMB does not replace the backing filesystem. ext4 can also satisfy this requirement; XFS is a workload choice, not the only valid answer. XFS does not support ordinary shrinking.

The loop filesystem has a 2 TiB logical size and the test file has a 1 TiB logical size, or 1,099,511,627,776 bytes. `allocated_blocks=0` proves this file is sparse. Real 1 TB media requires adequate allocated capacity, headroom, quotas and backup capacity; the local metadata test proves none of those. Formatting a physical production volume must be planned separately.

## Monitoring and alerts

The share probe checks an actual mounted filesystem and performs a write, fsync and read every ten seconds, exporting success, duration and free/total bytes. Node exporter supplies Linux block-device metrics. Prometheus checks availability, two-second probe latency, 15% free capacity, missing exporter and sustained device busy time. The alert drill unmounts the share, waits for `ShareUnavailable` to fire, remounts it and verifies resolution.

Define a production service objective before treating thresholds as operational commitments: for example, 99.9% monthly successful share probes and a separately measured p95 operation-latency target for representative media files. Add burn-rate alerts, growth prediction and an Alertmanager paging receiver. The delivered Prometheus rules produce local alerts; external paging is not configured or tested. Route warnings to a ticket channel and sustained unavailability to the on-call engineer, group duplicates by share/server, send resolved notifications and link the mount/credentials/disk runbook.

On the actual Windows server, collect PhysicalDisk latency/queue metrics, SMB Server Shares metrics and filesystem capacity through Windows exporter or PerfMon. On the actual Linux server use node exporter, `iostat -xz 1`, `/proc/fs/cifs/Stats`, `smbstatus` and a bounded `fio` scratch-file test. Client-side direct I/O alone does not eliminate server-side caching. The Docker VM's device metrics are not measurements of the Mac's physical disk. Record payload size, fsync policy, cache state and latency percentiles alongside throughput.
