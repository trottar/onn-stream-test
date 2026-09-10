---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Repository Code Map

## Root

- `PrivyHub/`: Android TV application.
- `companion/`: Windows companion/control/media/native-stream implementation.
- `scripts/`: setup/start helpers, including deferred Sunshine/Moonlight legacy.
- `tools/`: build/install helpers, probes, audit and diagnostics.
- `docs/`: feature documentation, investigations, and durable memory.

Generated runtime/data/log/archive/media/game-content paths are intentionally outside normal source tracking.

## Android

`MainActivity.kt` currently contains a large amount of application/UI orchestration. Native stream components are separated under `streaming/`: decoder, RTP/FEC receive, audio receive, controller sender, and stream Activity. UDP diagnostic Activities are under `diagnostics/`.

## Companion

- `privyhub_service.py`: HTTP control/service entry point and plugin lifecycle.
- `plugins/games.py`: Games API/orchestration and launch preflight.
- `games/emulator_manager.py`: substantial RetroArch/game/profile/save/mod/cheat lifecycle logic.
- `native_stream.py`: native streaming session orchestration.
- `native_session_io.py`: process audio and controller bridge.
- `native_wgc_bridge.py`: WGC capture integration.
- `native_fec_relay.py`: video FEC relay.
- `process_audio/`: Windows process-loopback helper.

## Maintainability note

Several central files are large (`MainActivity.kt`, `emulator_manager.py`, and `plugins/games.py`). This is real modularization debt, but it is not a reason to refactor them during the four-player extension. Preserve working boundaries through Phase A; split only with a dedicated, testable objective later.
