---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# Proven Tools and Entry Points

Linux is the current platform. Windows-era entry points are listed at the bottom
as history; do not use them on this host.

Inspect an existing tool before creating a new one. Most diagnostic questions in
this project already have a probe, and the answer to "what evidence exists" is
usually a file that is already being written.

## Normal development commands

Companion launch:

`python3 ./companion/privyhub_service.py`

Restart the companion whenever companion Python changes. D-068 durable rule:
stale-process behavior is not evidence.

Android build and install, from the repository root:

```bash
sh ./gradlew :app:assembleDebug --no-daemon
adb install -r PrivyHub/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop com.safeiot.privyhub
```

Patch installers that change Android source run the real Gradle build
themselves and roll back exact tracked bytes if it fails.

## Android source layout

Kotlin sources are **flat**: they sit directly in the Gradle source roots, not
in reversed-domain package directories.

```text
PrivyHub/app/src/main/java/MainActivity.kt
PrivyHub/app/src/main/java/diagnostics/DiagnosticsActivity.kt
PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt
```

Package declarations are unchanged and still read
`package com.safeiot.privyhub[.diagnostics|.streaming]`. Kotlin does not require
a file's directory to match its package; only Java does, and this app has no
Java sources. `namespace` and `applicationId` in `app/build.gradle.kts` are
independent of directory layout, and `AndroidManifest.xml` names classes by
fully-qualified name.

Two consequences worth knowing:

- Android Studio shows a "package directive does not match file location"
  inspection on these files and offers to move them back. **Decline it.** That
  quick-fix would undo the layout.
- If a Java source is ever added, it must live in package-matching directories.
  Do not flatten Java.

Patch `git add` allowlists and probe paths use the flat paths. Records written
before 2026-09-18 name the old `com/safeiot/privyhub/` paths and are history.

## Where dated history lives

One file per date at the memory root: `docs/memory/YYYY-MM-DD.md`.

Until 2026-09-18 there were two locations — the root and `docs/memory/memory/` —
with two different `2026-09-15.md` files. The directory is gone and that date is
merged. Do not recreate `docs/memory/memory/`.

## Memory and repository health

`tools/check_memory_health.py --repo <repo>`

Required gate for any patch that touches `docs/memory/`. It checks required
files, size thresholds, and the seven exact `CURRENT.md` headings. Treat
`maintenance_required` as a validation failure with exact-byte rollback. The
checker is the specification; see `MAINTENANCE.md`.

`tools/audit_repo_checkpoint.py`

Checkpoint audit: Git whitespace state, critical tracked source, imported Games
modules, diagnostic source tracking, runtime/data leakage, game-content
candidates, legacy Sunshine/Moonlight files. Supplements, never replaces, real
build and runtime validation.

## Game session evidence

`tools/collect_game_session_diagnostics.py --root <repo>`

Writes `logs/games/latest_game_diagnostic_bundle.txt`, one privacy-safe file
containing: selected RetroArch runtime, session-critical RetroArch config, the
unified game session trace, the RetroArch network control trace, the latest
RetroArch verbose session log, the native video host log, the latest Android
decoder session JSON, the per-game state slot index, and the savestate
inventory. IPv4 addresses are replaced with `<IP_REDACTED>` on the way in.

Prefer this single bundle over requesting individual files.

Other evidence entry points:

- `tools/privyhub_debug_bundle.py` — broader support bundle;
- `tools/privyhub_audio_history.py` — audio transport/timing history;
- `tools/diagnostic_retention.py` — bounded diagnostic retention;
- `tools/recover_orphan_game_session.py` — recover a session left orphaned;
- `logs/games/save_state_probe.txt`, `logs/games/retroarch_control_probe.txt`,
  `logs/games/native_video_alpha.log`, `logs/games/decoder_sessions/*.json`.

### Reading the bundle — two retention limits that matter

Both limits silently discard the evidence a reader is most likely to want, so
check them before concluding anything from an absence.

- **The native video host log section is the last 500 lines only.** Earlier
  encoder runs in the same file are cut. A missing restart banner is not proof
  that no restart happened.
- **The decoder session's `slow_events_ge_50_ms` list is a fixed-capacity ring.**
  The report carries `slow_event_retained` and `slow_event_capacity`; when they
  are equal the buffer overflowed and only the most recent events survive. A
  cumulative maximum such as `max_output_gap_ms` can therefore name an event
  whose per-event row is gone.

Cumulative session totals and per-event rows answer different questions. Session
fields such as `max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are
whole-session values and cannot be attributed to one moment when the session
recorded more than one resync.

## Streaming probes

- `tools/probe_c1_stream_parameter_inventory.py` — stream parameter inventory;
- `tools/probe_c2_stream_telemetry_runtime.py` — C2 telemetry runtime
  validation;
- `tools/probe_c3_actuator_continuity.py` — actuator continuity cycle. The
  trigger phase takes **no flag**; `--finalize` is the only option and is run
  after a normal Back. It dispatches by platform inside
  `NativeStreamManager.diagnostic_c3_actuator_continuity_cycle()`, so on Linux
  it drives `companion/diagnostics/c3_linux_actuator_probe.py`.

**These C3 probes are Windows-only and fail closed on Linux** with
`wgc_runtime_unavailable` before modifying anything. They require `_wgc_ready()`,
an HWND capture target and `_build_ffmpeg_command`:

- `tools/probe_c3_bidirectional_actuator.py`;
- `tools/probe_c3_fixed_5000_characterization.py`;
- `tools/probe_c3_fixed_5500_characterization.py`;
- `tools/probe_c3_fixed_6000_characterization.py`.

They are correct as written. Linux fixed-envelope work (`C3.L3`) needs a Linux
cycle implementation behind the same probe structure, not a new parallel
actuator.

## Linux subsystem probes

Under `tools/probes/`, named by the work item that created them:

- platform bring-up — `d075r1_linux_native_audio_rt_probe.py`,
  `d076_linux_controller_runtime_probe.py`, `d076r1_managed_retroarch_probe.py`,
  `d077_linux_runtime_selection_probe.py`,
  `d078_linux_companion_startup_probe.py`;
- VOD and storage — `d091_vod_client_request_boundary.py`,
  `d092_dynamic_vod_source_start_probe.py`, `d096_storage_boundary_probe.py`,
  `d097_vod_appliance_mode_probe.py`, `d098_absent_vod_catalog_probe.py`,
  `d099_absent_vod_timing_probe.py`;
- EPG — `d103_epg_ingestion_probe.py`,
  `d105_epg_local_source_viability_probe.py`,
  `d106_epg_provider_identity_probe.py`, `d107_epg_feed_identity_probe.py`,
  `d108_epg_local_grabber_viability_probe.py`,
  `d109_epg_portable_node_grabber_probe.py`, `d110_epg_plugin_runtime_probe.py`,
  `d111_android_companion_epg_probe.py`, `d124_tv_epg_latency_probe.py`,
  `d125_epg_background_warmer_probe.py`,
  `d126_android_epg_prefetch_probe.py`, `d132_favorites_epg_coverage_probe.py`,
  `d133_epg_status_accuracy_probe.py`;
- TV state and guide UX — `d113_stream_identity_audit.py`,
  `d115_tv_state_authority_probe.py`, `d116_android_tv_state_sync_probe.py`,
  `d117_linux_authority_pull_probe.py`, `d119_tv_entry_sync_trigger_probe.py`,
  `d120_tv_state_sync_diagnostics_probe.py`,
  `d121_tv_state_conflict_diagnostics_probe.py`,
  `d127_incorrect_guide_probe.py`, `d128_guide_style_ui_probe.py`,
  `d129_single_column_tv_guide_probe.py`, `d130_tv_entry_latency_probe.py`,
  `d131_tv_entry_nonblocking_probe.py`,
  `d134_favorites_load_latency_probe.py`,
  `d135_tv_state_executor_isolation_probe.py`;
- regression gates — `d122_d5_tv_media_regression_probe.py` and
  `d136_focused_tv_media_regression_probe.py`.

Storage administration lives in `tools/storage/configure_vod_storage.py` and
`tools/storage/enable_vod_appliance_mode.py`.

Games probes for Phase A input, multitap and four-player routing remain at the
top level as `tools/probe_a8_*.py`, `tools/probe_four_player_*.py`,
`tools/probe_ps1_multitap_*.py` and `tools/probe_phase_a_*.py`.

## Windows-era, archived

The Windows-only scripts were moved out of `tools/` on 2026-09-18 and now live
under `archive/windows_tools/`:

```text
archive/windows_tools/
    build_install_onn.ps1
    audit_repo_checkpoint.ps1
    run_privyhub_debug.ps1
    run_udp_transport_probe.ps1
    run_udp_reverse_transport_probe.ps1
    run_udp_loopback_probe.ps1
    probe_a4_minimize_wgc.py
    probe_a4_occluded_background_wgc.py
    a4_audio_mute_probe/
    a4_audio_float_attenuation_probe/
```

`archive/` is gitignored, so these are untracked on disk and out of the working
tree, while git history still holds every version. Do not consult them unless a
Windows question is explicitly raised; none of them run on this host.

The Opal router-boundary scripts — `tools/run_opal_*.sh` and
`tools/analyze_opal_*.py` — stay in `tools/`. They are POSIX shell and Python,
they run on this host, and D-083 allows re-entry for one bounded measurement
that would change a product or roadmap decision.

Windows-only code that is still imported by production dispatch stays where it
is: `companion/native_wgc_bridge.py`, `companion/process_audio/`,
`companion/diagnostics/c3_actuator_probe.py` and
`companion/diagnostics/c3_fixed_bitrate_probe.py` are selected by platform at
runtime and fail closed on Linux. Do not archive or delete them.

## Privacy

Do not ask for raw address-bearing captures when a redacted summary answers the
question, and never ask the user for IP addresses. Shareable diagnostics redact
network identity; keep it that way.
