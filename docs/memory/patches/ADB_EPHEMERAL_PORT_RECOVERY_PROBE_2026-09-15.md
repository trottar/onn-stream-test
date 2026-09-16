---
memory_schema: 1
as_of: 2026-09-15
patch: privyhub_adb_ephemeral_port_recovery_probe_01_2026-09-15
durable_memory_updated: true
---

# ADB ephemeral-port recovery probe patch

Purpose: extend the Linux/portable D-053 diagnostic so a stale cached wireless
ADB endpoint can recover when the onn keeps its pairing/address but restarts its
TLS listener on a new random port.

Changed:
- `tools/probe_adb_wireless_recovery.py`;
- current/durable/daily/handoff/patch-index memory;
- development evidence for the ADB 34.0.5 / 37.0.1 and ephemeral-port findings.

Intentionally unchanged:
- `tools/build_install_onn.ps1` (production parity waits for runtime evidence);
- companion service;
- Android application;
- game/media/video/audio/controller paths;
- UDP/router investigation;
- bitrate/FEC/adaptation policy.

Validation before delivery:
- replacement Python compiles;
- probe self-test passes;
- single-host scanner self-test detects only a temporary localhost listener;
- installer fixture clean install and idempotent reinstall;
- wrong-state rejection before modification;
- forced post-write rollback restores exact predecessor bytes;
- `git diff --check` on installed fixture;
- ZIP integrity and manifest checks.

Runtime status: **pending** until executed against the paired onn.
