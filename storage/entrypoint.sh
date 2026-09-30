#!/bin/sh
set -eu
case "${1:-server}" in
  server)
    useradd -M media || true
    mkdir -p /srv/media
    chown media:media /srv/media
    { cat /run/secrets/smb_password; cat /run/secrets/smb_password; } | smbpasswd -s -a media >/dev/null
    exec smbd --foreground --no-process-group --debug-stdout
    ;;
  client)
    mkdir -p /mnt/media
    umask 077
    { printf 'username=media\npassword='; cat /run/secrets/smb_password; } > /tmp/smb-credentials
    # A failure is visible in logs and the probe. The container retries on restart.
    attempt=0
    until mount -t cifs //samba/media /mnt/media -o credentials=/tmp/smb-credentials,vers=3.1.1,seal,uid=0,gid=0,nosuid,nodev,noexec; do
      attempt=$((attempt+1))
      [ "$attempt" -lt 30 ] || exit 1
      sleep 2
    done
    prometheus-node-exporter --web.listen-address=:9100 >/tmp/node-exporter.log 2>&1 &
    exec python /lab/probe.py
    ;;
  xfs) exec /lab/xfs-demo.sh ;;
  *) exec "$@" ;;
esac
