---
memory_schema: 1
as_of: 2026-09-16
patch: D-096R1_STORAGE_DEVICE_DISCOVERY
durable_memory_updated: true
---

# D-096R1 storage-device discovery

Purpose:
fix the D-096 root storage configurator after the first real run encountered a
systemd automount pseudo-source.

Observed failure:
`blkid -s UUID -o value systemd-1`

Correction:
- filesystem `stat().st_dev`;
- major:minor mapping through `lsblk`;
- real `/dev/...` partition used for UUID;
- mountpoint derived from that real device's mountpoints.

Production code changed:
none.

Operational tool changed:
`tools/storage/configure_vod_storage.py`

D-096 remains development-only pending runtime storage migration and onn
acceptance.
