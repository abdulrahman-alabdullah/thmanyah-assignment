#!/bin/sh
# This formats only a newly created temporary loop image, never a host disk.
set -eu
image=$(mktemp /tmp/assessment-xfs-XXXXXX.img)
mountpoint=$(mktemp -d /tmp/assessment-xfs-mount-XXXXXX)
loop=''
cleanup() {
  umount "$mountpoint" 2>/dev/null || true
  [ -z "$loop" ] || losetup -d "$loop"
  rm -f "$image"
  rmdir "$mountpoint"
}
trap cleanup EXIT INT TERM
truncate -s 2T "$image"
loop=$(losetup --find --show "$image")
mkfs.xfs -f "$loop"
mount "$loop" "$mountpoint"
xfs_info "$mountpoint"
truncate -s 1T "$mountpoint/one-tib-sparse.bin"
stat -c 'logical_bytes=%s allocated_blocks=%b' "$mountpoint/one-tib-sparse.bin"
du -h "$mountpoint/one-tib-sparse.bin"
echo 'PASS: 1 TiB logical file on XFS. This is a sparse metadata test, not 1 TiB of written data.'
