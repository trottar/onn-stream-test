---
memory_schema: 1
as_of: 2026-11-03
status: STATUS INDEX of every file in `docs/memory/patches/` (241 files = 239 notes + this index + PATCH_PROTOCOL.md) — APPLIED 230, PREPARED-UNAPPLIED 1 (G-A8), SUPERSEDED 8; the notes stay in place (DOCS-APPLY 2026-11-03, the audit's option (b))
---

# Patch Index

One note per change. The notes stay in place: the records under `../evidence/` link them by these paths, and no code reads
this directory. `PATCH_PROTOCOL.md` describes the workflow and is not a patch record.

Each note is authoritative for what it changed. Its own status line is as of the day it was written; **this index gives
the status today** (2026-11-03), from `../evidence/DOCS_AUDIT_2026-11-02.md` §1.6 and the records written since. Where
the two differ, the table below says so. The notes themselves are not edited.

The adopted lines are the fourteen in `tools/e1_suite.py` `ADOPTED` (the audit's §0): 1 `ADAPTIVE_BITRATE_MODE=live`
(C3-L4), 2 `EPG_GUIDE_INDEX=cached` (E3-S6A), 3 `SNES_CORE=snes9x` (E3-A2), 4 `RECOVERY_TRIGGER=v2` (E3-A3B),
5 `SNES_CAPTURE_FIX=output_rate` (E4-S5D), 6 `OVERLAY_PROVIDER` (G-A1), 7 `SESSION_IDENTITY=v2` (G-A1),
8 `AUDIO_CODEC=opus` (G-A2), 9 `LINK_REPORT=1` (G-A3), 10 `LINK_RECOVERY=1` (G-A4), 11 `RESTART_FAST=1` (G-A5),
12 `RESTART_FAST_UNLOCK=1` (G-A7), 13 `REMOTE=1` (G-A9), 14 `STEP_IN_PLACE=1` (G-A10); each `PRIVYHUB_`-prefixed.
The confirmed APK is `fcd924c2…` (B25's build: B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 +
B25, per B25's note). Queue M's APK `0132b944…` (B5 … B25 + B32 + B34 + B35 + B38 + B39) is pinned, NOT installed.

## Live

- **`G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`** — `PRIVYHUB_LOSS_GUARD=1` (B27's adoption). Prepared, never applied; the
  loss guard is out. The only live adoption candidate.

## Status lines that are wrong today

| Note | Its status line says | Today |
|---|---|---|
| G-A4_LINK_RECOVERY_ADOPTION_PREPARED | PREPARED, nothing applied | adopted, line 10 (`evidence/G_A4_LINK_RECOVERY_ADOPTION_2026-10-24.md`) |
| G-A9_REMOTE_ADOPTION_PREPARED | PREPARED, nothing applied | adopted, line 13 (`evidence/TRIP_PREP_2026-10-29.md`) |
| E4-S5_SNES_CAPTURE_OUTPUT_RATE_FLAG | REJECTED; dormant | adopted, line 5, via E4-S5D (`evidence/E4_S5D_SNES_CAPTURE_FIX_ADOPTION_2026-10-15.md`; no note) |
| E3-R1_RECOVERY_TRIGGER_V2, E3-R2_RECOVERY_PAUSE_EXIT | dormant | adopted, line 4, via E3-A3B (`evidence/E3_A3B_RECOVERY_V2_READOPTION_2026-10-09.md`) |
| C3-L2C-R1_LOW_LATENCY_DECODE_REINSTATED | decision pending | in the tree |
| most B / G notes (53 notes carry the phrase, with some C3, C5, CL-B, D-BASE and LAN notes) | "Nothing committed" | since committed |

## No note exists for

B31, B37 (a read), G-A6 (shelved), CL-B6, CL-B8 to CL-B16, E4-S5D. Their records are under `../evidence/`.

## Every note

Status today: **APPLIED** (in the tree; the change may sit behind a flag that is off), **PREPARED-UNAPPLIED**,
**SUPERSEDED by X**, **INDEX**, **PROTOCOL**. Sorted by family, then by name. The last column gives the adopted line the
note feeds, or its gate / flag, where the records say; "—" where none applies.

| Note | Family | Status today | Adopted line or gate |
|---|---|---|---|
| ADB_ENDPOINT_DEBUG_PROBE_V1_2026-09-15.md | adb | APPLIED | dev diagnostic |
| ADB_ENDPOINT_DEBUG_WATCH_PORT_V1_2026-09-15.md | adb | APPLIED | dev diagnostic |
| ADB_EPHEMERAL_PORT_RECOVERY_PROBE_2026-09-15.md | adb | SUPERSEDED by ADB_EPHEMERAL_PORT_RECOVERY_PROBE_V2_2026-09-15 | — |
| ADB_EPHEMERAL_PORT_RECOVERY_PROBE_V2_2026-09-15.md | adb | APPLIED | dev diagnostic |
| ADB_RECOVERY_PROBE_LINUX_PARITY_2026-09-15.md | adb | APPLIED | dev diagnostic |
| B10_CLIENT_LOSS_GUARD.md | b-series | APPLIED | client `loss_guard`, off; in `fcd924c2…`; its default-on (B27) and adoption (G-A8) are out |
| B11_CLIENT_RESTART_GUARD.md | b-series | APPLIED | client `restart_guard`; in `fcd924c2…` (on by default since B19) |
| B12_STATE_FOR_ALL_AND_STALL_RESUME.md | b-series | APPLIED | `STALL_RESUME` / `INPUT_HOLD_REWIND`: implied by line 10 |
| B13_LINK_REPORT_DEFAULT_ON.md | b-series | APPLIED | client `link_report` on by default, in `fcd924c2…`; host half via line 9 (G-A3) |
| B14_LINK_NOTICE.md | b-series | APPLIED | client `link_notice`; in `fcd924c2…` (on by default since B25) |
| B15_RESTART_GUARD_ALL_PATHS.md | b-series | APPLIED | inside client `restart_guard`; in `fcd924c2…` |
| B16_STALL_RESUME_SPEED.md | b-series | APPLIED | inside `STALL_RESUME` + `INPUT_HOLD_REWIND`: line 10 |
| B17_GUARD_AUDIO_ORDER.md | b-series | APPLIED | inside client `restart_guard`; in `fcd924c2…` |
| B18_NO_SAVE_AT_SESSION_END.md | b-series | APPLIED | inside `INPUT_HOLD_REWIND`: line 10 |
| B19_CLIENT_DEFAULTS_ON.md | b-series | APPLIED | client `stall_signal` / `restart_guard` on by default; in `fcd924c2…` |
| B1B_SHIM_GATE.md | b-series | APPLIED | test shim (`PRIVYHUB_IMPAIRMENT`), not adopted |
| B1_SHIM_BLACKOUT_BOTH.md | b-series | APPLIED | test shim (`PRIVYHUB_IMPAIRMENT`), not adopted |
| B20_LINK_RECOVERY_UMBRELLA.md | b-series | APPLIED | line 10 (the umbrella over the six stack lines) |
| B21_LINK_RECOVERY_CONFIG_LOG.md | b-series | APPLIED | line 10's `link_recovery_config` row |
| B22_RESTART_FAST.md | b-series | APPLIED | line 11; client half in `fcd924c2…` |
| B23_LINK_RECOVERY_WAN_THRESHOLDS.md | b-series | APPLIED | `PRIVYHUB_LINK_RECOVERY_WAN=1`, off (G-A6 shelved) |
| B24_RESTART_FAST_UNLOCK.md | b-series | APPLIED | line 12 |
| B25_LINK_NOTICE_DEFAULT_ON.md | b-series | APPLIED | client `link_notice` on by default; its APK is `fcd924c2…` (CONFIRMED) |
| B26_RELAY_STOP_STRAY_PACKET.md | b-series | APPLIED | inside line 12 |
| B27_LOSS_GUARD_DEFAULT_ON.md | b-series | APPLIED | in the tree, NOT in the confirmed APK; adoption G-A8 unapplied |
| B28_REMOTE_UMBRELLA.md | b-series | APPLIED | line 13 (G4-S4's four WAN lines, remote-class sessions only) |
| B29_GUARD_QUIET_STALL.md | b-series | APPLIED | in the tree, NOT in the confirmed APK |
| B2_INPUT_HOLD.md | b-series | APPLIED | `INPUT_HOLD`: implied by line 10 |
| B30_TRIP_LOG_KEEPER.md | b-series | APPLIED | tools; the trip keeper ended 2026-11-01 |
| B32_SURFACE_HOLD_AND_STEP_IN_PLACE.md | b-series | APPLIED | host step in place: line 14 (G-A10); client `surface_hold` off, in `0132b944…` only |
| B33_NO_REWIND_WITHOUT_LOSS.md | b-series | APPLIED | live inside line 10 (off switch `PRIVYHUB_REWIND_NEEDS_LOSS=0`) |
| B34_STABLE_PAD_SLOTS.md | b-series | APPLIED | client `pad_slots=stable`, off; in `0132b944…` only |
| B35_VOD_RETRY.md | b-series | APPLIED | client `vod_retry`, off; in `0132b944…` only |
| B36_DIAG_KEEPER.md | b-series | APPLIED | tools; `privyhub-diag` running |
| B38_VIRTUAL_REMOTE_NO_SLOT.md | b-series | APPLIED | inside client `pad_slots=stable`, off; in `0132b944…` (pinned, NOT installed) |
| B39_HOLD_COUNTER.md | b-series | APPLIED | inside client `surface_hold`, off; in `0132b944…` (pinned, NOT installed) |
| B3_CLIENT_LINK_REPORT.md | b-series | APPLIED | line 9 (host `PRIVYHUB_LINK_REPORT=1`) |
| B40_VOD_DROP_TEST.md | b-series | APPLIED | host per-run test flag `PRIVYHUB_VOD_DROP_TEST=1`, never adopted |
| B4_INPUT_HOLD_REWIND.md | b-series | APPLIED | `INPUT_HOLD_REWIND`: implied by line 10 |
| B5_CLIENT_WIFI_LOCK.md | b-series | APPLIED | client `wifi_lock`, off (property empty); in `fcd924c2…` |
| B6_INPUT_HOLD_TRIGGER.md | b-series | APPLIED | `INPUT_HOLD_B6`: implied by line 10 |
| B7_CLIENT_STALL_SIGNAL.md | b-series | APPLIED | host `STALL_SIGNAL`: implied by line 10; client half in `fcd924c2…` |
| B8_HOLD_STALL_OWNERSHIP.md | b-series | APPLIED | `INPUT_HOLD_B8`: implied by line 10 |
| B9_STALL_THRESHOLD_AND_REWIND_CORES.md | b-series | APPLIED | the `STALL_SIGNAL` / `INPUT_HOLD_REWIND` values: line 10 |
| CL-B1_DECODER_REPORT_BODY.md | cl-b | APPLIED | — |
| CL-B2_IDENTITY_APK_HASH.md | cl-b | APPLIED | APK pin, since replaced (`fcd924c2…` today) |
| CL-B3_HARDENED_APK_HASH.md | cl-b | APPLIED | APK pin, since replaced |
| CL-B4_OPUS_APK_HASH.md | cl-b | APPLIED | APK pin, since replaced |
| CL-B5_DECODE_THREAD_APK_HASH.md | cl-b | APPLIED | APK pin, since replaced |
| CL-B7P_OPUS_DRAIN_LEAN_FLAG.md | cl-b | APPLIED | client `opus_decode` `lean` mode |
| CL-B7_LEAN_APK_HASH.md | cl-b | APPLIED | APK pin, since replaced |
| D-BASE-C5A_IDR_REJECTION_COUNTERS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P10_AUDIO_REDUNDANCY.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P1_STALE_THRESHOLD_PROBE_KNOB.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P2A_AUDIO_STARTUP_HOLD.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P2_AUDIO_TICK_SERIES_PROBE.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P3_FEC_RELAY_SENDER_PACING.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P5_RELAY_FRAME_SIZE_COUNTERS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT.md | d-base | APPLIED | the frame cap as a profile field (`evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`) |
| D-BASE-P6_FRAME_BYTE_COUNTERS_AND_ENCODER_KNOBS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P7_AUDIO_HEARTBEAT_COUNTERS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P8_AUDIO_HOLE_RING.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-P9_AUDIO_CUSHION_SETTING.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R1_GROUP_A_LIVE_AND_RESYNC_LOSS_COUNTER.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R2_STALL_VISIBILITY_AND_LAUNCHER_RECONCILE.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R3C2_RECOVERY_FLOW.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R3_LINK_DROP_SELF_RECOVERY.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R4_SESSION_REPORT_VISIBILITY.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-R5_HEARTBEAT_LOSS_COUNTERS.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-T1_THERMAL_TELEMETRY.md | d-base | APPLIED | D-BASE (closed) |
| D-BASE-T2_P0_AUDIO_CUSHION_ADOPTED.md | d-base | APPLIED | the 12 / 17 audio cushion as the profile default (the user, 2026-09-23) |
| D-BASE_BASELINE_STREAM_HEALTH.md | d-base | APPLIED | D-BASE (closed) |
| D-074_LINUX_NATIVE_VIDEO_BACKEND.md | d-series | APPLIED | — |
| D-075R1_LINUX_NATIVE_AUDIO_RT_PACER.md | d-series | APPLIED | — |
| D-075_LINUX_NATIVE_AUDIO_BACKEND.md | d-series | SUPERSEDED by D-075R1_LINUX_NATIVE_AUDIO_RT_PACER | — (original cadence rejected) |
| D-076R1_LINUX_AUTOCONFIG_SESSION_PATH.md | d-series | APPLIED | — |
| D-076R2_LINUX_AUTOCONFIG_SYS_IMPORT.md | d-series | APPLIED | — |
| D-076_LINUX_UINPUT_CONTROLLER_BACKEND.md | d-series | APPLIED | — |
| D-077_LINUX_PLATFORM_RUNTIME_SELECTION.md | d-series | APPLIED | — |
| D-078_LINUX_COMPANION_MEDIA_SERVER_STARTUP.md | d-series | APPLIED | — |
| D-084_LINUX_A8_PLATFORM_ADAPTER.md | d-series | APPLIED | — |
| D-085_LINUX_UDEV_HAT_MAPPING.md | d-series | APPLIED | — |
| D-086_CONTROLLER_PARITY_CHECKPOINT.md | d-series | APPLIED | — |
| D-087R1_LINUX_PS1_MULTITAP_METADATA_PATH.md | d-series | APPLIED | — |
| D-087_LINUX_PS1_MULTITAP_CONFIG_PATH.md | d-series | APPLIED | — |
| D-088R1_MULTITAP_RUNTIME_VALIDATION.md | d-series | APPLIED | — |
| D-089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT.md | d-series | APPLIED | D5 (closed by D-139) |
| D-090_D4_LINUX_GAMES_ACCEPTANCE.md | d-series | APPLIED | D4 |
| D-091_D5_MEDIA_BASELINE_AND_CLIENT_BOUNDARY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-092_DYNAMIC_VOD_SYMLINK_HEALTH.md | d-series | APPLIED | — |
| D-093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-094_D5_EXTERNAL_STORAGE_REMOUNT_EVIDENCE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-096R1_STORAGE_DEVICE_DISCOVERY.md | d-series | APPLIED | — |
| D-096R2R1_PROBE_INSTALLER_PRESTATE.md | d-series | APPLIED | — |
| D-096R3_PROBE_LISTENER_LIFECYCLE.md | d-series | APPLIED | — |
| D-096_CONFIGURABLE_VOD_STORAGE_BOUNDARY.md | d-series | APPLIED | — |
| D-097_VOD_APPLIANCE_MODE.md | d-series | APPLIED | — |
| D-098_ABSENT_VOD_CATALOG_RESILIENCE.md | d-series | APPLIED | — |
| D-099R1_PRESTATE_RECEIPT_ORDER.md | d-series | APPLIED | — |
| D-099_NONBLOCKING_VOD_PRESENCE.md | d-series | APPLIED | — |
| D-100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-101R1_BROWSER_CAMERA_C6_RECLASSIFICATION.md | d-series | APPLIED | — |
| D-103_D5_EPG_INGESTION_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-104R2_D5_EPG_GZIP_SOURCE_SUPPORT.md | d-series | APPLIED | D5 (closed by D-139) |
| D-105_D5_EPG_LOCAL_SOURCE_VIABILITY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-106_D5_EPG_PROVIDER_IDENTITY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-107_D5_EPG_FEED_IDENTITY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-108_D5_EPG_LOCAL_GRABBER_VIABILITY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-109_D5_EPG_PORTABLE_NODE_GRABBER_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-110_D5_LINUX_EPG_SERVICE_SEAM.md | d-series | APPLIED | D5 (closed by D-139) |
| D-111_D5_ANDROID_COMPANION_EPG_INTEGRATION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-112_D5_PROGRAM_GUIDE_NEWLINE_POLISH.md | d-series | APPLIED | D5 (closed by D-139) |
| D-113_D5_STREAM_IDENTITY_AUDIT.md | d-series | APPLIED | D5 (closed by D-139) |
| D-114_D5_STREAM_IDENTITY_POLICY_CHECKPOINT.md | d-series | APPLIED | D5 (closed by D-139) |
| D-115_D5_LINUX_TV_STATE_AUTHORITY.md | d-series | APPLIED | D5 (closed by D-139) |
| D-116_D5_ANDROID_TV_STATE_SYNC.md | d-series | APPLIED | D5 (closed by D-139) |
| D-117_D5_LINUX_AUTHORITY_PULL_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-118_D5_PULL_CLASSIFIER_ACCEPTANCE_CHECKPOINT.md | d-series | APPLIED | D5 (closed by D-139) |
| D-119_D5_TV_ENTRY_SYNC_TRIGGER_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-120_D5_TV_STATE_SYNC_DIAGNOSTICS.md | d-series | APPLIED | D5 (closed by D-139) |
| D-121_D5_TV_STATE_CONFLICT_DIAGNOSTICS_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-122_D5_TV_MEDIA_REGRESSION_GATE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-123_D54_CLOSURE_TV_UX_FOLLOWUP.md | d-series | APPLIED | D5 (closed by D-139) |
| D-124A_TV_EPG_LATENCY_PROBE_SPLIT_DB_FIX.md | d-series | APPLIED | D5 (closed by D-139) |
| D-124_TV_EPG_LATENCY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-125_EPG_NONBLOCKING_BACKGROUND_WARMER.md | d-series | APPLIED | D5 (closed by D-139) |
| D-126_ANDROID_EPG_PREFETCH_INTEGRATION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-127_D5_INCORRECT_GUIDE_INTENT.md | d-series | APPLIED (its note: "validation pending") | D5 (closed by D-139) |
| D-128_GUIDE_STYLE_CATEGORY_PRESENTATION.md | d-series | APPLIED (its note: "validation pending") | D5 (closed by D-139) |
| D-129_SINGLE_COLUMN_TV_GUIDE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-130_TV_ENTRY_LATENCY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md | d-series | APPLIED | D5 (closed by D-139) |
| D-132_FAVORITES_EPG_COVERAGE_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-133_EPG_STATUS_ACCURACY.md | d-series | APPLIED | D5 (closed by D-139) |
| D-134_FAVORITES_LOAD_LATENCY_PROBE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-135_TV_STATE_EXECUTOR_ISOLATION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-136_FOCUSED_TV_MEDIA_REGRESSION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-137_TV_STATE_PROBE_V2_PROJECTION.md | d-series | APPLIED | D5 (closed by D-139) |
| D-138_D136_AUTOMATED_REGRESSION_ACCEPTANCE.md | d-series | APPLIED | D5 (closed by D-139) |
| D-139_D5_TV_MEDIA_CLOSEOUT.md | d-series | APPLIED | the D5 closeout |
| D4_LINUX_GAME_HANDOFF_FIX_01_2026-09-15.md | d-series | APPLIED | D4 |
| D4_MEMORY_RECONCILIATION_2026-09-16.md | d-series | APPLIED | memory reconcile |
| G-A10_STEP_IN_PLACE_ADOPTION.md | g-track | APPLIED | line 14 (`evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`) |
| G-A1_OVERLAY_AND_IDENTITY_ADOPTED.md | g-track | APPLIED | lines 6 and 7 |
| G-A2_OPUS_ADOPTED.md | g-track | APPLIED | line 8 |
| G-A3_LINK_REPORT_ADOPTED.md | g-track | APPLIED | line 9 |
| G-A3_LINK_REPORT_ADOPTION_PREPARED.md | g-track | SUPERSEDED by G-A3_LINK_REPORT_ADOPTED | — |
| G-A4_LINK_RECOVERY_ADOPTION_PREPARED.md | g-track | APPLIED (its status line still says PREPARED) | line 10 |
| G-A5_RESTART_FAST_ADOPTION.md | g-track | APPLIED | line 11 |
| G-A7_RESTART_FAST_UNLOCK_ADOPTION.md | g-track | APPLIED | line 12 |
| G-A8_LOSS_GUARD_ADOPTION_PREPARED.md | g-track | PREPARED-UNAPPLIED | `PRIVYHUB_LOSS_GUARD=1`: the only live adoption candidate |
| G-A9_REMOTE_ADOPTION_PREPARED.md | g-track | APPLIED (its status line still says PREPARED) | line 13 |
| G1-S1_OVERLAY_PROVIDER_BOUNDARY.md | g-track | APPLIED | the code behind line 6 |
| G3-S1_SESSION_IDENTITY_HOST_SIDE.md | g-track | APPLIED | the code behind line 7 |
| G3-S2_SESSION_IDENTITY_CLIENT_SIDE.md | g-track | APPLIED | client `identity_v2` (on) |
| G3-S3_HARDENING_AND_HUB_HOST.md | g-track | APPLIED | inside line 7 / `identity_v2` |
| G4-P1_E1_SUITE_REMOTE_ROW.md | g-track | APPLIED | tools (`e1_suite.py run --remote`) |
| G4-P2_REMOTE_ROW_GATE3.md | g-track | APPLIED | tools (the remote row's gate 3) |
| G4-W2_OPUS_AUDIO_PATH.md | g-track | APPLIED | the code behind line 8 |
| G5-S1_WAN_TELEMETRY_CLASSIFICATION.md | g-track | APPLIED | `WAN_TELEMETRY`: one of G4-S4's four, under line 13 |
| G5-S2_WAN_ADAPTATION_RULES.md | g-track | APPLIED | `WAN_ADAPTATION=1`, not adopted; its live smoke G5-S2-L never ran |
| G5-S3_REMOTE_LADDER.md | g-track | APPLIED | `REMOTE_LADDER`: one of G4-S4's four, under line 13 |
| G5-S4_REMOTE_RUNG_CAP.md | g-track | APPLIED | `REMOTE_RUNG_CAP`: one of G4-S4's four, under line 13 |
| G8-P1_IMPAIRMENT_SHIM.md | g-track | APPLIED | test shim `PRIVYHUB_IMPAIRMENT`, not adopted |
| G8-S1_SHIM_NONE_PROFILE.md | g-track | APPLIED | the shim's `none` profile |
| G8-S2_START_RUNG.md | g-track | APPLIED | `START_RUNG`: one of G4-S4's four, under line 13 |
| G8-S4_ENCODER_RATE_HEADROOM.md | g-track | APPLIED | `ENCODER_RC`, not adopted; G8-S6 never ran |
| PATCH_INDEX.md | index | INDEX | this file |
| PATCH_PROTOCOL.md | index | PROTOCOL | the patch workflow |
| MEM-TOOLS_LINUX_TOOL_INVENTORY_REFRESH.md | memory | APPLIED | — |
| MEMORY_MAINTENANCE_2026-09-17.md | memory | APPLIED | — |
| MEMORY_NORMALIZATION_2026-09-15.md | memory | SUPERSEDED by MEMORY_MAINTENANCE_2026-09-17 | — |
| ANDROID-FLAT_SOURCE_LAYOUT.md | misc | APPLIED | — |
| BUDGET_EXECUTION_BUDGET_AND_TIERING.md | misc | APPLIED | — |
| LAN-R1_LOSS_STEPDOWN_RULE.md | misc | APPLIED | `PRIVYHUB_LAN_LOSS_RULE=1`, not adopted |
| LAN_R2_LOSS_RULE_RETHOUGHT.md | misc | APPLIED | `PRIVYHUB_LAN_LOSS_RULE=bidir`, not adopted |
| STREAMLINE_REPOSITORY_LAYOUT.md | misc | APPLIED | — |
| C3-CTX_PHASE_C_CONTINUATION_CONTEXT.md | phase-c | APPLIED | — |
| C3-F1_RECOVERY_RESTART_LADDER.md | phase-c | APPLIED | — |
| C3-HO_PHASE_C_HANDOFF_SYNC.md | phase-c | APPLIED | — |
| C3-L0R1_CURRENT_STRUCTURE_AND_HEALTH_GATE.md | phase-c | APPLIED | — |
| C3-L0_LINUX_ACTUATOR_BOUNDARY_MEMORY_RECONCILIATION.md | phase-c | APPLIED | — |
| C3-L1R1_RTP_BASELINE_MEASUREMENT_CORRECTION.md | phase-c | APPLIED | — |
| C3-L1_LINUX_ACTUATOR_CONTINUITY_PROBE.md | phase-c | APPLIED | — |
| C3-L2A-E1_FIRST_IDR_EVIDENCE_PASS.md | phase-c | SUPERSEDED by C3-L2A-E2_ACTUATOR_IDR_RESOLVED | — |
| C3-L2A-E2_ACTUATOR_IDR_RESOLVED.md | phase-c | APPLIED | — |
| C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md | phase-c | APPLIED | — |
| C3-L2C-R1_LOW_LATENCY_DECODE_REINSTATED.md | phase-c | APPLIED (its note: "decision pending") | in the tree |
| C3-L2C_LOW_LATENCY_DECODE_ENABLE.md | phase-c | SUPERSEDED by C3-L2C-R1_LOW_LATENCY_DECODE_REINSTATED | — (rolled back) |
| C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md | phase-c | APPLIED | — |
| C3-L3A-P1R1_LADDER_RUNTIME_EVIDENCE.md | phase-c | APPLIED | — |
| C3-L3A-P1_LINUX_VALIDATED_LADDER_TRANSITION.md | phase-c | APPLIED | — |
| C3-L3A-P2R1_PROBE_DEFECTS_AND_RESCORE.md | phase-c | APPLIED | — |
| C3-L3A-P2R2_PHASE_B_WINDOW_ANCHOR.md | phase-c | APPLIED | — |
| C3-L3A-P2R3_POOLING_RULE.md | phase-c | APPLIED | — |
| C3-L3A-P2_GAMEPLAY_ACCEPTANCE_PROBE.md | phase-c | APPLIED | — |
| C3-L3A-R1_SPLIT_SESSION_FINALIZE.md | phase-c | APPLIED | — |
| C3-L3A-R2B_DECODER_REPORT_CAP.md | phase-c | APPLIED | — |
| C3-L3R1_CHARACTERIZATION_CORRECTION.md | phase-c | APPLIED | — |
| C3-L3R2_GATE_DEFINITION_AND_DECISION_SYNC.md | phase-c | APPLIED | — |
| C3-L3_LINUX_FIXED_BITRATE_PORT.md | phase-c | APPLIED | — |
| C3-L4-D1_LIVE_DEFAULT_PREFLIGHTS.md | phase-c | APPLIED | line 1's preflights (gate C3-L4) |
| C3-L4-L1_LIVE_CONTROLLER.md | phase-c | APPLIED | the code behind line 1 (gate C3-L4) |
| C3-L4-L2B_NFT_HARNESS_ONE_WINDOW.md | phase-c | APPLIED | gate C3-L4 (the night harness) |
| C3-L4-L2_INCREASE_RULE_AND_SAMPLES.md | phase-c | APPLIED | gate C3-L4 |
| C3-L4-N1_CAPACITY_TRIGGER_AND_BACKSTOP.md | phase-c | APPLIED | gate C3-L4 |
| C3-L4-N2_MILD_CAPACITY.md | phase-c | APPLIED | gate C3-L4 |
| C3-L4-S1_SHADOW_CONTROLLER.md | phase-c | APPLIED | shadow mode, flag default off |
| C4-M1_FEC_XOR8_2_ARM.md | phase-c | APPLIED | default off; its note: "NOT SHOWN; nothing adopted" |
| C5-CLOSE_RUNG_WINDOW_RULE_AND_ATTRACT_FIX.md | phase-c | APPLIED | — |
| C5-M1_1080P60_CANDIDATE_PROFILE.md | phase-c | APPLIED | behind `PRIVYHUB_NATIVE_PROFILE_ID` |
| C5-M2_1080P60_FOLLOWUP_PROFILES.md | phase-c | APPLIED | behind a flag |
| C5-M3_LOW_RUNG_PROFILES.md | phase-c | APPLIED | behind a flag |
| C5-M5B_RUNG_ENTRY_AND_PS1_LOOK.md | phase-c | APPLIED | behind a flag |
| C5-M5_1080P_RUNG.md | phase-c | APPLIED | behind its flag |
| C6-D1_SOURCE_CONTRACT.md | phase-c | APPLIED | new files only |
| E1-S1_WORKLOAD_SUITE_RUNNER_AND_SAMPLER.md | phase-e | APPLIED | tools (E1 frozen) |
| E2-S1_SAMPLER_THREADS_ENCODER_AND_VOD_ROW.md | phase-e | APPLIED | tools |
| E3-A2_ADOPTED_STATE_CHECKS.md | phase-e | APPLIED | line 3 (gate E3-A2; its `frame_spin` reverted) |
| E3-A3B_RECOVERY_V2_READOPTION.md | phase-e | APPLIED | line 4 (gate E3-A3B) |
| E3-A3_RECOVERY_V2_ADOPTION.md | phase-e | SUPERSEDED by E3-A3B_RECOVERY_V2_READOPTION | — (adopted, then reverted) |
| E3-R1_RECOVERY_TRIGGER_V2.md | phase-e | APPLIED (its note: "dormant") | the code behind line 4 |
| E3-R2_RECOVERY_PAUSE_EXIT.md | phase-e | APPLIED (its note: "dormant") | the code behind line 4 |
| E3-S1_EPG_GRAB_PRIORITY.md | phase-e | APPLIED | `PRIVYHUB_EPG_GRAB_PRIORITY=idle`, not one of the fourteen |
| E3-S2_EPG_MALLOC_TRIM.md | phase-e | APPLIED | `PRIVYHUB_EPG_MALLOC_TRIM=1`, not one of the fourteen |
| E3-S3_EPG_DIRECT_NODE.md | phase-e | APPLIED | `PRIVYHUB_EPG_DIRECT_NODE=1`, not one of the fourteen |
| E3-S4_SNES_CORE_FLAG.md | phase-e | APPLIED | the code behind line 3 |
| E3-S4_SNES_CORE_RUNNER_SUPPORT.md | phase-e | SUPERSEDED by E3-S4_SNES_CORE_FLAG | — |
| E3-S5B_AUDIO_SEND_TRACE.md | phase-e | APPLIED | measurement only |
| E3-S5C_AUDIO_SENDER_FRAME_SPIN.md | phase-e | APPLIED | `PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`, not one of the fourteen |
| E3-S5_AUDIO_SENDER_PACING.md | phase-e | APPLIED | `PRIVYHUB_AUDIO_SENDER_PACING=frame`, not one of the fourteen |
| E3-S6A_GUIDE_INDEX_ADOPTION_STATE_CHECK.md | phase-e | APPLIED | line 2 (gate E3-S6A) |
| E3-S6_GUIDE_INDEX.md | phase-e | APPLIED | the code behind line 2 |
| E3-S7B_GRAB_DELAY_VALUE.md | phase-e | APPLIED | `PRIVYHUB_EPG_GRAB_DELAY_MS`, dormant |
| E3-S7_GRAB_NET_PACED.md | phase-e | APPLIED | `PRIVYHUB_EPG_GRAB_NET=paced`, not one of the fourteen |
| E4-S2_CONSTRAINT_DROPIN_AND_CGROUP_RUNNER.md | phase-e | APPLIED | tools |
| E4-S3B_RUNNER_REFRESH_BACKOFF.md | phase-e | APPLIED | tools |
| E4-S3_SWAP_AND_MEMORY_READINGS_RUNNER.md | phase-e | APPLIED | tools |
| E4-S4_GRAB_DEFERRAL_FLAG.md | phase-e | APPLIED | `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`, rejected, dormant |
| E4-S5_SNES_CAPTURE_OUTPUT_RATE_FLAG.md | phase-e | APPLIED (its note: "REJECTED; dormant") | line 5, via E4-S5D |

**Count:** 241 rows = `git ls-files docs/memory/patches | wc -l` (241): APPLIED 230, PREPARED-UNAPPLIED 1, SUPERSEDED 8,
INDEX 1, PROTOCOL 1. By family: adb 5, b-series 39, cl-b 7, d-base 22, d-series 70, g-track 25, index 2, memory 3,
misc 5, phase-c 39, phase-e 24.
