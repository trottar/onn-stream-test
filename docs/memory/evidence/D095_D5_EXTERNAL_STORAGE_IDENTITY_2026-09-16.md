---
memory_schema: 1
as_of: 2026-09-16
status: diagnosed
classification: D5_STORAGE_STABLE_ID_READY_DESKTOP_AUTOMOUNT_CONFIRMED
---

# D-095 external-storage identity evidence

Probe:
`logs/d5_storage_mount_identity_probe.txt`

Synchronized checkpoint:
`7c029de7ff7d569bce07d26c23f0bcfbb1147e8d`

Measured:
- current VOD symlink available;
- backing filesystem detected;
- filesystem type: exFAT;
- mount class: desktop/user automount;
- backing block device identified;
- hotplug: true;
- stable filesystem UUID present;
- raw UUID intentionally not logged;
- systemd and systemd-mount available;
- current `/etc/fstab` does not reference that UUID.

Classification:
`D5_STORAGE_STABLE_ID_READY_DESKTOP_AUTOMOUNT_CONFIRMED`

This supports deterministic UUID-based appliance mounting without encoding the
current desktop label/path into PrivyHub architecture.
