---
memory_schema: 1
as_of: 2026-11-03
---

# Repository Code Map

Checked against the tree on 2026-11-03 (`ls`, `git ls-files`).

## Root (tracked)

- `companion/` — the Linux hub: control API, games / native stream, TV / EPG,
  VOD, overlay and session identity. Runs as the systemd user unit
  `privyhub-companion`.
- `PrivyHub/` — the Android TV client (Gradle project; the wrapper is
  `PrivyHub/gradlew`).
- `tools/` — the live tools, harnesses, replays and historical probes.
- `tests/` — host tests, one directory per feature.
- `data/` — the four RetroArch autoconfig files for the PrivyHub virtual
  gamepads.
- `docs/` — product docs and `docs/memory/`.
- `_cowork_prompt*.txt` — the user's prompt files for sessions A / B / C.
- Untracked and ignored: `logs/`, `runtime/`, `media/`, `games/`, the
  repo-root `archive/`, `docs_flat/`, build output and the APK copies under
  `PrivyHub/app/build/`.

## Companion

- **Entry point:** `companion/privyhub_service.py` — the HTTP service
  (port 8765) and the plugin lifecycle.
- **Plugins:** `plugins/games.py` (games and the native stream API),
  `plugins/epg.py`, `plugins/iptv_org.py`, `plugins/tv_state.py`.
- **Games stack:** `games/` (`emulator_manager.py`, `link_drop_recovery.py`,
  `native_stream_heartbeat.py`, `decoder_session_log.py`, `log_rotation.py`,
  `host_resource_sampling.py`, …) and `native_stream.py`,
  `native_stream_profiles.py`, `native_fec_relay.py`, `native_fec_rs.py`,
  `native_source_contract.py`, `native_session_io.py`, `encoder_rc.py`,
  `audio_codec.py`.
- **Adaptive bitrate and the remote lines:** `adaptive_bitrate.py`,
  `adaptive_bitrate_live.py`, `remote_ladder.py`, `remote_cap.py`,
  `start_rung.py`, `remote_umbrella.py`, `wan_telemetry.py`,
  `wan_adaptation.py`, `step_in_place.py`.
- **Link recovery and restarts:** `link_recovery.py`, `link_recovery_wan.py`,
  `restart_fast.py`, `restart_fast_unlock.py`, `rewind_needs_loss.py`,
  `rewind_cores.py`, `hold_*.py`, `input_hold.py`, `stall_owner.py`,
  `stall_signal.py`, `keyframe_request.py`, `lan_loss_rule.py`,
  `link_notice.py`, `pad_slots.py`, `surface_lost_row.py`.
- **Remote trust:** `overlay/` (`provider.py`, `none.py`, `tailscale.py`) and
  `session_identity.py` (`docs/REMOTE_TRUST.md`).
- **Media:** `range_server.py`, `vod_log.py`, `vod_drop_test.py`,
  `storage_presence.py`; `impairment.py`.
- **Diagnostics:** `diagnostics/` (`self_test.py`, `support_bundle.py`,
  `runtime_health.py`, `stream_telemetry.py`, …).
- **Windows-only, kept:** `native_wgc_bridge.py`, `process_audio/`,
  `diagnostics/c3_actuator_probe.py`, `diagnostics/c3_fixed_bitrate_probe.py`
  are selected by platform and fail closed on Linux; do not delete them.

## Android (`PrivyHub/app/src/`)

- Kotlin sources are flat under `main/java/` (`TOOLS.md`, "Android source
  layout"): `MainActivity.kt` (still the main orchestration),
  `Tv*.kt`, `NflRepository.kt`, `TvStateSyncClient.kt`, `GameCheatUiState.kt`,
  `identity/` (the identity v2 client), `streaming/` (the decoder, receivers,
  Opus, FEC, link report / notice, restart, loss guard, pad slots, surface
  hold, …), `diagnostics/`.
- Tests: `test/java/` (`identity/`, `streaming/`, `vod/`) and
  `androidTest/java/`.

## Tools and tests

- The live tools and their usage: `docs/memory/TOOLS.md`. The `probe_*`
  scripts and `tools/probes/` are historical (named by their records).
- `tests/<feature>/test_<feature>.py` (43 directories) and
  `tools/test_*.py`; a task runs the suites it touches and records the output
  (e.g. `evidence/g_a10_2026-11-02/tests.txt`).

## Durable memory

`docs/memory/`: `CURRENT.md` (authoritative active state), `MEMORY.md`
(durable facts), `MAINTENANCE.md` (policy), `handoffs/CURRENT_HANDOFF.md`
(pointer), `evidence/` (the records and the chronology, never moved),
`architecture/`, `decisions/`, `investigations/`, `patches/`, `handoffs/`,
`history/` (superseded sections, verbatim) and `archive/` (retired files,
`archive/INDEX.md`).
