---
memory_schema: 1
as_of: 2026-09-15
patch: privyhub_adb_ephemeral_port_recovery_probe_02_2026-09-15
durable_memory_updated: true
---

# ADB ephemeral-port recovery probe v5 patch

Purpose: correct the unsuccessful v4 Linux wireless-ADB recovery diagnostic after
manual `adb connect` proved pairing and reachability were healthy.

Changed:
- `tools/probe_adb_wireless_recovery.py`;
- current/durable/daily/handoff/patch-index memory;
- runtime evidence recording the v4 failure and manual-connect discriminator.

Behavioral changes:
- cache the connected onn host privately;
- learn/cache the device's live kernel ephemeral-port range;
- scan only that one host and cached/measured range after endpoint staleness;
- prompt for repair/re-pair only after automatic recovery is exhausted, then
  retry recovery once.

Intentionally unchanged:
- `tools/build_install_onn.ps1` pending runtime validation;
- companion service;
- Android application;
- game/media/video/audio/controller paths;
- UDP/router investigation;
- bitrate/FEC/adaptation policy.

Runtime status: **development patch / validation pending**.
