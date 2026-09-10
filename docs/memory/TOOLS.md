---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Proven Tools and Entry Points

## Normal development commands

Android build/install:

`\.\tools\build_install_onn.ps1; cd L:\Projects\onn-stream-test`

Companion launch:

`python .\companion\privyhub_service.py`

## Debug harness

Game/video reproduction:

`\.\tools\run_privyhub_debug.ps1 -Mode GameSmear`

Latest game evidence bundle:

`\.\tools\run_privyhub_debug.ps1 -Mode CollectLatest`

Transport history:

`\.\tools\run_privyhub_debug.ps1 -Mode TransportHistory`

Audio history:

`\.\tools\run_privyhub_debug.ps1 -Mode AudioHistory`

Prefer the resulting single privacy-safe share bundle instead of requesting many individual files.

## Repository audit

`tools/audit_repo_checkpoint.py` checks Git whitespace state, critical tracked source, imported Games modules, diagnostic source tracking, runtime/data leakage, game-content candidates, and legacy Sunshine/Moonlight files.

Use it near checkpoints. It supplements, but does not replace, actual build/runtime validation.

## Important game evidence

Existing diagnostics include Save/Load probe output, RetroArch control probe output, native video logs, decoder-session JSON, host telemetry, audio timing, capture diagnostics, and `latest_game_diagnostic_bundle.txt`.

Do not ask for raw network-address-bearing captures when the existing redacted summaries answer the question.
