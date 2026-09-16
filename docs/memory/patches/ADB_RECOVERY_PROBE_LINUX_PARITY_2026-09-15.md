---
memory_schema: 1
as_of: 2026-09-15
---

# Patch — Linux wireless-ADB recovery probe parity

Patch name: `privyhub_adb_recovery_probe_linux_parity_01_2026-09-15`

Status: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**

Purpose: align the existing Linux-capable wireless-ADB diagnostic with the
accepted D-053 cached-target/mDNS/reconnect/server-restart recovery sequence
already implemented and runtime validated in the onn installer workflow.

Changed production-adjacent diagnostic:

- `tools/probe_adb_wireless_recovery.py`

Durable memory installed/updated:

- `docs/memory/evidence/ADB_RECOVERY_PROBE_LINUX_PARITY_DEVELOPMENT_2026-09-15.md`
- this patch record;
- additive marker updates to `CURRENT.md`, `MEMORY.md`,
  `memory/2026-09-15.md`, `handoffs/CURRENT_HANDOFF.md`, and
  `patches/PATCH_INDEX.md`.

Intentionally unchanged:

- `companion/` runtime code;
- Android application code;
- `tools/build_install_onn.ps1` D-053 recovery implementation;
- game/video/audio/controller paths;
- UDP/router investigation state;
- adaptive bitrate/FEC policy.

Runtime acceptance: run the patched probe on the Linux host. A recovery
classification such as cached, mDNS, reconnect, or post-server-restart recovery
is success. If automatic recovery is exhausted, the probe should explicitly
classify the preserved-pairing Wireless-debugging toggle as the next human step.
