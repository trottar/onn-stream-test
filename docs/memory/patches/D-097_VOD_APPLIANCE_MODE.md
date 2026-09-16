---
memory_schema: 1
as_of: 2026-09-16
patch: D-097_VOD_APPLIANCE_MODE
durable_memory_updated: true
---

# D-097 VOD appliance mode

Purpose:
make removable external VOD suitable for headless/server operation without
manual Linux mount/eject commands.

Changes:
- future D-096 storage configuration defaults to `ro`;
- one-time `enable_vod_appliance_mode.py` updates the existing managed fstab
  entry to read-only while preserving `x-systemd.automount` and `nofail`;
- ensures the automount unit is active;
- validates actual filesystem read-only status when storage is present;
- adds a read-only appliance-mode probe.

Production application code:
unchanged.

Normal user procedure after runtime validation:
`stop playback -> unplug -> later plug in -> open/refresh VOD`.

Future:
controlled writable maintenance mode and client-accessible safe disconnect for
ingest/ripping workflows.
