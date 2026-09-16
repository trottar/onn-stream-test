# Patch — ADB endpoint debug probe v1 — 2026-09-15

Patch: `privyhub_adb_endpoint_debug_probe_01_2026-09-15`

Purpose: expose the exact private host/port endpoints selected by the current
wireless-ADB recovery diagnostic so the failing endpoint-discovery path can be
observed directly.

Status: development diagnostic / runtime validation pending.

Changed:
- `tools/probe_adb_wireless_recovery.py`
- durable memory only

Intentionally unchanged:
- `tools/build_install_onn.ps1`
- Android app
- companion service
- game/media/video/audio/controller code
- UDP/router diagnostics

Privacy: literal network endpoints are emitted only when the local operator
passes `--debug-endpoints`. The normal diagnostic log remains redacted.
