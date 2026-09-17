---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 45ef51f9e583b459752dd5ea83163f54171e68c7
---

# Patch / Checkpoint Index

<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:PATCH_INDEX:BEGIN -->
### D-119 — D5 TV-entry sync-trigger probe — 2026-09-17

Diagnostic-only.

Measures whether selecting TV from the true top-level PrivyHub source list
pulls a newer Linux revision without Refresh.

The temporary runtime marker changes only the country display name and is
restored before final cleanup.

No Android or companion production change.
<!-- PRIVYHUB_D119_TV_ENTRY_TRIGGER:PATCH_INDEX:END -->

<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:PATCH_INDEX:BEGIN -->
### D-118 — D5 pull classifier / acceptance checkpoint — 2026-09-17

Diagnostic correction only.

Corrects D-117 final classification so restored-authority pull parity is not
reported as failure merely because the temporary marker revision was not
observed.

Records D5.4 Linux-to-onn pull as runtime accepted from revision/hash parity.

No Android or companion production change.
<!-- PRIVYHUB_D118_PULL_ACCEPTANCE:PATCH_INDEX:END -->

<!-- PRIVYHUB_D117_PULL_VALIDATION:PATCH_INDEX:BEGIN -->
### D-117 — D5 Linux-authority pull probe — 2026-09-17

Diagnostic-only checkpoint after D-116 runtime acceptance.

Temporarily changes only Linux `country_name`, verifies Android pulls the newer
authority, restores original Linux user-state content, and verifies Android
pulls the restoration.

No production code changes.

Final evidence:
`logs/tv/d117_linux_authority_pull_probe.txt`.
<!-- PRIVYHUB_D117_PULL_VALIDATION:PATCH_INDEX:END -->

<!-- PRIVYHUB_D116_TV_STATE_SYNC:PATCH_INDEX:BEGIN -->
### D-116 — D5 Android TV-state synchronization — 2026-09-17

Android production integration.

Adds durable projection/import to `TvRepository`, revision-aware
`TvStateSyncClient`, and fail-soft seed/pull/push wiring in `MainActivity`.

Real Android build is an installer gate.

Runtime evidence next:
`logs/tv/d116_android_tv_state_sync_probe.txt`.
<!-- PRIVYHUB_D116_TV_STATE_SYNC:PATCH_INDEX:END -->

<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:PATCH_INDEX:BEGIN -->
### D-115 — D5 Linux TV-state authority — 2026-09-16

Companion production-seam patch.

Adds revisioned durable TV-state JSON persistence and opt-in JSON-body plugin
POST routing.

Android is unchanged.

Runtime evidence next:
`logs/tv/d115_tv_state_authority_probe.txt`.
<!-- PRIVYHUB_D115_TV_STATE_AUTHORITY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:PATCH_INDEX:BEGIN -->
### D-114 — D5 stream identity policy checkpoint — 2026-09-16

Memory/decision-only checkpoint.

Records D-113 runtime result and closes the stream-identity audit without adding
a noisy generic production heuristic.

Policy:
- manual Hide for user-confirmed semantically bad streams;
- no playback-failure conflation;
- no current-source URL hardcoding;
- `manual_hidden` included in D5.4 durable TV-state sync.

Next: D5.4 Linux-authoritative TV-state synchronization.
<!-- PRIVYHUB_D114_STREAM_IDENTITY_POLICY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:PATCH_INDEX:BEGIN -->
### D-113 — D5 stream identity audit — 2026-09-16

Diagnostic-only patch.

Audits current onn built-in IPTV-org rows against official feed/stream metadata
after a known 10 Bold stream mismatch.

No production code, TV DB, EPG DB, or cache mutation.

Runtime evidence next:
`logs/tv/d113_stream_identity_audit.txt`.
<!-- PRIVYHUB_D113_D5_STREAM_IDENTITY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:PATCH_INDEX:BEGIN -->
### D-112 — D5 Program Guide newline polish — 2026-09-16

Android presentation-only patch after D-111 runtime acceptance.

Changes one Program Guide separator:
literal `\n` -> actual newline.

Records D-111/D5.3 runtime acceptance in durable memory.

No EPG acquisition/cache/identity logic changes.

Runtime validation:
visually confirm `10 Bold` Program Guide rows no longer display literal `\n`.
<!-- PRIVYHUB_D112_D5_GUIDE_NEWLINE:PATCH_INDEX:END -->

<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:PATCH_INDEX:BEGIN -->
### D-111 — D5 Android companion EPG integration — 2026-09-16

Android production integration patch.

Changes only `TvEpgRepository.kt` in Android production source:
fresh local cache -> companion refresh -> existing fallback.

Adds a read-only D-111 onn EPG DB probe and records D-110 runtime acceptance.

Real Android `assembleDebug` is an installer success gate.

Runtime evidence next:
`logs/tv/d111_android_companion_epg_probe.txt`.
<!-- PRIVYHUB_D111_D5_ANDROID_COMPANION_EPG:PATCH_INDEX:END -->

<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:PATCH_INDEX:BEGIN -->
### D-110 — D5 Linux EPG service/cache seam — 2026-09-16

Production-seam development patch.

Adds:
- `companion/plugins/epg.py`;
- EPG plugin registration;
- D-110 runtime probe;
- D-109 success evidence;
- D-110 architecture/decision/investigation memory.

No Android change.

Runtime evidence next:
`logs/tv/d110_epg_plugin_runtime_probe.txt`.
<!-- PRIVYHUB_D110_D5_LINUX_EPG_SERVICE:PATCH_INDEX:END -->

<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:PATCH_INDEX:BEGIN -->
### D-109 — D5 EPG portable-Node grabber probe — 2026-09-16

Diagnostic-only patch.

Records D-108 as environment-blocked before acquisition and adds a portable-Node
wrapper that reuses the exact D-108 probe.

The runtime is official Node 24.21.0, downloaded into temporary state and
verified against pinned SHA-256 before use.

No host package installation and no production code changes.

Runtime evidence next:
`logs/tv/d109_epg_portable_node_grabber_probe.txt`.
<!-- PRIVYHUB_D109_D5_EPG_PORTABLE_NODE:PATCH_INDEX:END -->

<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:PATCH_INDEX:BEGIN -->
### D-108 — D5 EPG local-grabber viability probe — 2026-09-16

Diagnostic-only patch.

Records the D-107 feed-aware runtime result and adds a disposable Linux-local
programme-acquisition probe pinned to upstream `iptv-org/epg` commit
`78e94adb76841a63d94a53e80dbd0d52bb7c2c5c`.

No production code changes and no host toolchain installation.

Runtime evidence next:
`logs/tv/d108_epg_local_grabber_viability_probe.txt`.
<!-- PRIVYHUB_D108_D5_EPG_LOCAL_GRABBER:PATCH_INDEX:END -->

<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:PATCH_INDEX:BEGIN -->
### D-107 — D5 EPG feed-aware identity probe — 2026-09-16

Diagnostic-only patch.

Supersedes D-106's sparse built-in guide-coverage classification after source
review established that playlist IDs can encode `channel@feed` while guide API
records carry `channel` and `feed` separately.

Adds a read-only canonical identity probe and durable-memory correction.

No production code changes.

Runtime evidence next:
`logs/tv/d107_epg_feed_identity_probe.txt`.
<!-- PRIVYHUB_D107_D5_EPG_FEED_IDENTITY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:PATCH_INDEX:BEGIN -->
### D-106 — D5 EPG provider/identity probe — 2026-09-16

Diagnostic-only patch.

Records the completed D-105 result and adds a read-only provider/identity probe.

The probe distinguishes meaningful channel IDs from generated `tv_stream_*`
fallback IDs, partitions guide coverage by provider, and measures guide metadata
coverage of the built-in IPTV-org English playlist independently.

No production code changes.

Runtime evidence next:
`logs/tv/d106_epg_provider_identity_probe.txt`.
<!-- PRIVYHUB_D106_D5_EPG_PROVIDER_IDENTITY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:PATCH_INDEX:BEGIN -->
### D-105 — D5 EPG local-source viability probe — 2026-09-16

Diagnostic-only patch.

Adds a read-only probe that measures IPTV-org guide metadata coverage against
the effective onn catalog before current hosted-source availability is applied.

Also records the corrected D5.3 diagnosis:
D-104R2 did not increase the 2-mapping/0-programme state, and official upstream
public guide-worker availability currently covers only 2 channels.

Production Android/companion/media/game code is unchanged.

Runtime evidence next:
`logs/tv/d105_epg_local_source_viability_probe.txt`.
<!-- PRIVYHUB_D105_D5_EPG_LOCAL_SOURCE_VIABILITY:PATCH_INDEX:END -->

<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:PATCH_INDEX:BEGIN -->
### D-104 — D5.3 EPG GZIP source support — 2026-09-16

Development patch based on D-103 runtime evidence.

Production change:
- Android EPG mapping source selection accepts XML first, GZIP second;
- gzip-compressed XML is transparently decoded before the existing XMLTV parser;
- mapping-source version meta forces refresh of the old 2-row parser cache.

Diagnostic change:
- D-103 now models the post-D-104 XML/GZIP source rule.

No JSON EPG parser, fuzzy guide matching, TV catalog redesign, or unrelated
media behavior is changed.

Runtime validation pending.

D-104 installer history: the first D-104 package rolled back before build,
commit, push, or APK installation because its post-patch validator searched
for a literal escaped `\\n` sequence in Kotlin. D-104R2 corrects only that
installer validation defect; the intended Kotlin compatibility change is
unchanged.

D-104R1 installer history: R1 also rolled back before commit, push, or APK
installation because the repository tracks `PrivyHub/gradlew` as mode `100644`,
so direct `./gradlew` execution is not permitted on Linux. D-104R2 preserves
that tracked mode and invokes the wrapper with `sh ./gradlew` instead.
<!-- PRIVYHUB_D104R2_D5_EPG_GZIP_SOURCE_SUPPORT:PATCH_INDEX:END -->


<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:PATCH_INDEX:BEGIN -->
### D-103 — D5.2 EPG ingestion probe — 2026-09-16

Diagnostic-only patch. Adds a read-only EPG stage probe and durable D5.2
handoff/roadmap state. Production TV/EPG behavior is unchanged.

Initial D-103 delivery rolled back before commit when `git diff --check` caught
an extra blank line at EOF in the daily-memory append. D-103R1 fixes only the
installer append/validation path and keeps the probe payload unchanged. Runtime
evidence remains pending.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:PATCH_INDEX:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:PATCH_INDEX:BEGIN -->
## 2026-09-16 D5 TV memory checkpoint

`privyhub_d102r1_d5_tv_memory_checkpoint_01_2026-09-16` — documentation-only
checkpoint. Records D5.1 Live TV catalog/playback runtime acceptance, classifies
EPG as not accepted at 2 mappings / 0 programmes, defines D5.1-D5.9, and records
Linux-authoritative TV user-state synchronization as D-102. No production code
change. R1 supersedes the first failed-before-modification delivery wrapper and safely tolerates the pre-existing untracked `_patches/` and `_probes/` directories.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:PATCH_INDEX:END -->

This index records durable checkpoints and major patch lines; it does not invent hashes for historical ZIPs that were not retained in the current audit.

| Checkpoint / line | Date | Status / significance |
| --- | --- | --- |
| `9cb17e0` Baseline working PrivyHub prototype | 2026-09-04 | Initial pushed working prototype. |
| `c0c6dee` Add PrivyHub games and streaming prototype | 2026-09-05 | Games/native streaming enters repo. |
| `b9ab616` Stabilize native game streaming with FEC and audio smoothing | 2026-09-06 | Native streaming stability work. |
| `6a2272b` Fix dynamic WGC sizing | 2026-09-06 | Capture sizing correction. |
| `0dd7b99` Checkpoint stable native streaming with two-player support | 2026-09-07 | Proven two-player baseline. |
| `5ff6da0` Stabilize native process audio baseline | 2026-09-07 | Audio baseline checkpoint. |
| `5d3ffc7` Document UDP transport investigation and preserve diagnostics | 2026-09-08 | Transport investigation frozen/deferred with tools. |
| `550ed7b` Checkpoint Phase A through A7 games subsystem | 2026-09-09 | A1-A7 checkpoint. |
| A4 lifecycle recovery patch line | 2026-09-09 | Runtime validated after several installer/probe corrections; closed. |
| A8.1-A8.3 patch line | 2026-09-09 to 10 | Profiles, adapter, preflight, directional/Xbox UI; runtime validated. |
| `25e9a14` Checkpoint: complete A8 input mapping and profiles | 2026-09-10 | Current immutable pre-four-player baseline. |
| `privyhub_memory_bootstrap_2026-09-10` | 2026-09-10 | Documentation-only durable-memory bootstrap; no production behavior change. |
| `privyhub_phase_a_four_player_base_01_2026-09-10` | 2026-09-10 | Base PHI1/ViGEm/XInput layer runtime validated: four slots, exact synthetic P1-P4 routing, zero packet errors, neutral release, clean teardown. |
| `privyhub_phase_a_four_player_android_assignment_probe_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve base runtime evidence and add real Android four-controller assignment probe; no production behavior change. |
| `privyhub_phase_a_four_player_retroarch_ports_probe_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve real Android four-controller assignment evidence and add RetroArch P1-P4 startup enumeration probe; no production behavior change. |
| `privyhub_phase_a_a8_four_player_profiles_01_2026-09-10` | 2026-09-10 | Runtime validated: schema-1 A8 backend/editor/session mapping extends P1/P2 to P1-P4; legacy profiles preserved; Android four-player editing/copy confirmed. |
| `privyhub_phase_a_1p_regression_probe_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve A8 four-player runtime evidence and add isolated single-player gameplay/session-teardown regression probe; no production behavior change. |
| `privyhub_phase_a_2p_regression_probe_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve successful post-extension 1P regression and add guided 2P independence/session-teardown regression probe; no production behavior change. |
| `privyhub_phase_a_4p_gameplay_probe_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve successful post-extension 2P regression and add guided representative four-player gameplay/multitap diagnostic; no production behavior change. |

| `privyhub_phase_a_ps1_multitap_core_options_audit_01_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve representative 4P host-routing evidence and inspect exact RetroArch core-option storage/current source for a game-specific PS1 multitap fix; no production behavior change. |

| `privyhub_phase_a_ps1_multitap_source_context_audit_02_2026-09-10` | 2026-09-10 | Diagnostic/memory update: preserve exact core-option storage result and capture post-A8 source context needed for a game/session-specific PS1 multitap patch; no production behavior change. |
| `privyhub_phase_a_ps1_multitap_game_override_01_2026-09-10` | 2026-09-10 | Development patch: generic per-game PS1 multitap via existing controller override store and native RetroArch content-specific `.opt`; Crash Bash Port-1 validation record; runtime 4P gameplay pending. |

- `privyhub_phase_a_ps1_multitap_rollback_test_01_2026-09-10` — diagnostic rollback of the first PS1 multitap patch after the immediate post-patch controller-connectivity regression; restores exact prepatch production bytes, removes generated Crash Bash game `.opt`, and records rollback evidence. Runtime comparison required.

- `privyhub_phase_a_ps1_multitap_reapply_02_2026-09-10` — re-enables the same game-specific Crash Bash Port-1 multitap implementation after exact rollback showed the fourth physical-controller dropout persists without it; durable memory separates the Android/controller-stability investigation from the PS1 core-option path.

- `privyhub_phase_a_a9_regression_probe_02_2026-09-10` — diagnostic-only A9 checkpoint probe plus durable preservation of final P1-P4 assignment/Crash Bash 4P success. No production behavior change. Runtime A9 validation required.

- `privyhub_phase_a_a9_regression_probe_01_2026-09-10` — **FAILED BEFORE MODIFICATION**: exact-byte runtime-log preflight was too strict; no project files changed.
- `privyhub_phase_a_a9_regression_probe_02_2026-09-10` — corrected A9 diagnostic package; validates authoritative local runtime evidence semantically rather than by byte identity. Runtime A9 validation required.

- `privyhub_phase_a_ps1_multitap_flag_audit_01_2026-09-10` — diagnostic-only exact source/context and live PS1 metadata candidate audit before generalizing the validated Crash Bash Port-1 multitap into a per-game On/Off UI/API. Also records the first A9 NOT_CONFIRMED result.

- `privyhub_phase_a_ps1_multitap_onoff_01_2026-09-10` — production PS1 per-game Multitap On/Off control; On maps to Beetle Port 1 only, Port 2 forced disabled; Games API + Android Options UI; metadata auto-checker deferred after zero-candidate 80-game audit.

- `privyhub_adb_wireless_recovery_audit_01_2026-09-10` — diagnostic-only audit for persistent wireless ADB target disappearance during `build_install_onn.ps1`; captures exact local script hash/context and redacted ADB/mDNS/device state; no production behavior change.

- `privyhub_adb_wireless_recovery_audit_02_2026-09-10` — corrected diagnostic-only replacement for v1 ADB recovery probe; fixes `sdk.dir` discovery, records v1 failed diagnostic, no production/ADB pairing changes.

- `privyhub_adb_wireless_recovery_01_2026-09-10` — hardens `tools/build_install_onn.ps1` for paired wireless-ADB dropouts using private LocalAppData target caching, bounded reconnect/mDNS/server-restart recovery, a final Wireless-debugging toggle retry, and target redaction.

- `privyhub_adb_wireless_recovery_runtime_checkpoint_01_2026-09-10` — memory/evidence checkpoint recording successful runtime validation of the persistent wireless-ADB recovery path; no production code changes.

- `privyhub_phase_a_a9_finish_probe_01_2026-09-10` — diagnostic-only A9 finish probe: records successful CTR Multitap On/Off runtime evidence, fixes NES/Genesis identity fallback to fresh RetroArch logs, and reruns only the two previously unconfirmed A9 family checks plus repository audit.

- `privyhub_phase_a_a9_coverage_correction_01_2026-09-10` — diagnostic-only correction: invalidates NES/Genesis A9 prompt responses made without actual games, makes finish mode coverage-aware, and records zero-game systems as `SKIPPED_NO_LOCAL_FIXTURE` rather than pass/fail.

- `privyhub_phase_a_final_checkpoint_push_01_2026-09-10` — final Phase A checkpoint/push package: records A9 checkpoint-ready state, adds repository evidence policy, ignores live raw evidence, creates sanitized compressed Phase A evidence snapshot, stages only approved Phase A source/memory/probe changes, validates, commits, and pushes.

- `privyhub_roadmap_v2_push_01_2026-09-10` — docs-only roadmap update after Phase A checkpoint: replaces `docs/ROADMAP.md`, curates current/handoff/roadmap memory, and defines Diagnostics, adaptive streaming, VOD artwork, Linux scaling, OpenBIOS and future expansion phases.

- `privyhub_b1_diagnostics_inventory_01_2026-09-10` — diagnostic-only Phase B1.1 inventory package. Adds a local
  diagnostics-inventory probe and durable-memory handoff; no production behavior
  change. The probe inventories existing telemetry/probes/harness/privacy/schema
  surfaces before B1.2 architecture design.

- `privyhub_b1_health_model_foundation_01_2026-09-10` — B1.2 development foundation. Adds the pure
  `privyhub_diagnostics_health_v1` / `privyhub_resource_snapshot_v1` model and a
  runtime health-snapshot probe, records B1.1 evidence, and defines
  resource-aware diagnostics architecture. No service API, Android or native
  streaming behavior change.

- `privyhub_b1_health_endpoint_01_2026-09-10` — B1.3 read-only health endpoint. Adds a small runtime adapter,
  exposes `GET /diagnostics/health`, adds endpoint probe, records B1.2 runtime
  validation, and preserves resource-aware/zero-new-sampler semantics. No
  Android or native streaming pipeline changes.

- `privyhub_b1_client_feedback_source_audit_01_2026-09-10` — B1.4 diagnostic-only source-context audit. Records B1.3
  endpoint runtime validation and adds a probe that inventories exact current
  Android native-stream metrics, scheduler/cadence primitives, HTTP/JSON request
  infrastructure, lifecycle methods and companion health source hashes before
  any client-feedback implementation.

- `privyhub_b1_client_feedback_01_2026-09-10` — B1.5 client-feedback development patch. Reuses Android's
  existing metrics tick for a 2-second privacy-minimized report, adds a
  latest-only companion receiver/delta baseline, integrates fresh feedback into
  network/decoder health, and adds runtime validation. No new timer/resource
  sampler or persistent client-health log.

- `privyhub_b1_decoder_stale_semantics_audit_01_2026-09-10` — B1.6 diagnostic-only classifier audit. Records the successful
  B1.5 client-feedback runtime result and adds a multi-interval probe comparing
  rendered cadence, stale-output shedding, ordinary decoder drops, queue state,
  timing and network/FEC measurements before any decoder health rule is changed.

- `privyhub_b1_decoder_classifier_01_2026-09-10` — B1.7 health-classifier correction based on the B1.6
  multi-interval measurements. Stale-only low-latency shedding is informational
  rather than degraded; direct decoder-local faults remain degraded. Adds
  runtime validation and durable evidence. No Android/streaming changes.

- `privyhub_b1_gui_retention_context_audit_01_2026-09-10` — B1.8 diagnostic-only GUI/Self-Test + retention context audit.
  Records B1.7 classifier runtime validation, inventories exact Android UI and
  diagnostic-activity anchors, confirms the live health endpoint/self-test
  inputs, and measures log-family retention pressure without deleting evidence.

- `privyhub_b1_diagnostics_gui_retention_foundation_01_2026-09-10` — B1.9 development patch. Adds the standalone Android
  Diagnostics/Self-Test activity, a narrow PrivyHub Settings navigation entry,
  and a manual dry-run-first retention utility for the measured
  transport/debug-bundle pressure. Automatic deletion remains off. Records
  B1.8 evidence and updates durable memory.

- `privyhub_b1_retention_blocker_audit_01_2026-09-10` — B1.10 diagnostic-only protected-footprint audit. Records B1.9 GUI runtime validation, preserves production and retention behavior, and inventories why forward retention is blocked.

- `privyhub_b1_retention_rule_refinement_01_2026-09-10` — B1.11 retention classifier refinement. Treats only
  `pktmon_full.txt` as raw capture for extension-protection purposes, keeps
  newest/failure/general `.txt` protections, adds a dry-run validation probe,
  records B1.10 evidence, and performs no retention deletion.

- `privyhub_b1_b2_completion_gap_audit_01_2026-09-10` — diagnostic-only B1/B2 completion-gap audit. Records the
  successful B1.12 real retention apply and checks exact current source for the
  roadmap's remaining bounded event-history, GUI support-bundle and Self-Test
  requirements before B3. No production changes or deletions.

- `privyhub_b1_b2_completion_source_context_01_2026-09-10` — diagnostic-only exact source-context audit for the remaining
  B1/B2 completion requirements. Records the completion-gap result, inspects
  local Self-Test/service/health/client-feedback/bundle hooks, and searches for
  reusable ADB/storage/event-history candidates. No production changes.

- `privyhub_b1_b2_completion_01_2026-09-10` — B1.13 development patch.
  Completes the explicit B1/B2 diagnostics requirements with a bounded
  128-event history, storage/ADB/emulator-runtime Self-Test checks, GUI
  `COLLECT DIAGNOSTICS`, and a support-bundle bridge that reuses and revalidates
  the existing sanitized bundler. Streaming/session paths intentionally
  unchanged. Runtime validation pending.

- `privyhub_b1_b2_gui_action_feedback_01_2026-09-10` — UI-only B2 polish. Adds immediate button-local busy labels
  (`REFRESHING...`, `RUNNING...`, `COLLECTING...`) in the existing Diagnostics
  busy gate and records the successful B1/B2 completion runtime evidence.
  Companion/API/streaming behavior unchanged.

- `privyhub_b3_sunshine_moonlight_inventory_01_2026-09-10` — B3 diagnostic-only Sunshine/Moonlight dependency inventory. Records final B2 manual GUI validation, scans current source/config/docs plus privacy-safe Windows process/service/task/firewall/software state, classifies legacy occurrences, and emits a MUST PRESERVE native-path guard. No production or system-state changes.

- `privyhub_b3_active_legacy_edge_trace_01_2026-09-10` — B3.1 diagnostic-only active legacy-edge trace. Records the
  broad B3 runtime result, then traces exact current `games.py -> StreamManager`
  calls, Android Moonlight/com.limelight functions/call sites, manifest
  visibility, current-tree artifact references, and grouped legacy runtime
  footprint. No production/system-state changes.

- `privyhub_b4_1_games_source_context_01_2026-09-11` — diagnostic-only recovery after the first B4.1 installer was
  correctly rejected before modification. Captures exact `games.py` source
  encoding/newline state, semantic AST spans, and surrounding source blocks for
  rebuilding B4.1 without inferred whitespace anchors.

- `privyhub_b4_1_server_legacy_edge_removal_02_2026-09-11` — corrected B4.1 production patch. Uses exact predecessor hash
  plus AST-selected whole-line spans to remove the Games StreamManager edge,
  preserving CRLF, NativeStreamManager, Android, stream_manager.py and all
  Sunshine artifacts. Supersedes the rejected original B4.1 ZIP.

- `privyhub_b4_2_android_source_context_01_2026-09-11` — diagnostic-only B4.2 exact Android source-context capture
  after successful B4.1 runtime validation. Captures MainActivity function
  bodies/callers, legacy terms and manifest com.limelight context before any
  Android production edit.

- `privyhub_b4_2_android_moonlight_edge_removal_01_2026-09-11` — removes the exact evidenced Android Moonlight/com.limelight
  launcher/query and stale stream_host UI/response edge while preserving native
  streaming. Runs Kotlin compilation and rolls back source bytes on failure.

- `privyhub_b4_3_orphan_reference_audit_01_2026-09-11` — diagnostic-only orphan-reference audit after successful
  B4.1/B4.2 runtime validation. Separates production references, scripts,
  diagnostics/tools and physical legacy artifact groups before cleanup.

- `privyhub_b4_4_code_orphan_cleanup_01_2026-09-11` — removes the two exact-hash orphan Android stream-host helper
  functions and deletes the exact-hash orphan `stream_manager.py`. Preserves all
  physical Sunshine/Moonlight runtime/download/setup artifacts pending a hash
  manifest.

- `privyhub_b4_5_physical_legacy_hash_manifest_01_2026-09-11` — diagnostic-only exact hash manifest for remaining physical
  Sunshine/Moonlight artifacts after B4.4 runtime validation, including
  process/service/task/firewall state and com.limelight presence on
  already-connected Android targets without logging identifiers.

- `privyhub_b4_6_physical_legacy_cleanup_01_2026-09-11` — deletes exactly the nine B4.5-hashed project legacy groups after canonical digest revalidation and a verified backup archive. Preserves RetroArch name collisions and leaves Android package verification separate.

- `privyhub_b4_6_physical_legacy_cleanup_01_2026-09-11` — superseded. It was
  **FAILED BEFORE MODIFICATION** because the package's canonical-manifest
  separator bytes did not match B4.5.
- `privyhub_b4_6_physical_legacy_cleanup_02_2026-09-11` — corrected B4.6
  physical cleanup. Canonical group hashing exactly matches B4.5 and is covered
  by a direct cross-version equivalence regression fixture.

- `privyhub_b4_6_physical_legacy_cleanup_02_2026-09-11` — superseded. It was
  **FAILED BEFORE MODIFICATION** after falsely classifying the nine known
  RetroArch name-collision non-targets because its regex literal-dot escapes
  were doubled.
- `privyhub_b4_6_physical_legacy_cleanup_03_2026-09-11` — corrected physical
  cleanup. It matches both B4.5 canonical hashing and B4.5 non-target discovery,
  and hard-preserves the exact nine authoritative non-target paths.

- `privyhub_b4_7_device_moonlight_package_check_01_2026-09-11` — diagnostic-only device package verification using the
  established private ADB discovery/recovery pattern. Verifies PrivyHub on the
  resolved target, then checks `com.limelight`; performs no package changes.

- `privyhub_b4_8_device_moonlight_removal_01_2026-09-11` — installs the package-only B4.8 device cleanup action. The
  action privately resolves the established onn, verifies PrivyHub, uninstalls
  only `com.limelight`, and verifies the final package state.

- `privyhub_b4_8_device_moonlight_final_verify_02_2026-09-11` — diagnostic-only correction for the B4.8 post-uninstall
  verifier. Uses package-list semantics so missing Moonlight is a valid absence
  state. Performs no Android package changes.

- `privyhub_b5_native_only_regression_01_2026-09-11` — installs the focused B5 native-only regression harness.
  Diagnostic/runtime-validation only; no production-source change. On a fully
  confirmed PASS it writes B5 runtime evidence and advances durable memory to
  B6 clean-native checkpoint work.

- `privyhub_b5_classifier_correction_01_2026-09-11` — corrects the B5 diagnostic harness so post-profile native
  client activity is informational rather than a required pass gate. The
  installer adjudicates the existing failed B5 run against the fresh sanitized
  game diagnostic bundle, records B5 as runtime validated, and advances durable
  memory to B6. No production-source change.

- `privyhub_b6_clean_native_repository_audit_01_2026-09-11` — installs the read-only B6 clean-native repository audit. It
  captures exact source-control status, legacy production references, durable
  memory consistency, build readiness and remote predecessor state. No staging,
  commit or push.

- `privyhub_b6_clean_native_repository_audit_01_2026-09-11` — superseded;
  **FAILED BEFORE MODIFICATION** because it incorrectly exact-hash-gated the
  working `docs/ROADMAP.md`.
- `privyhub_b6_clean_native_repository_audit_02_2026-09-11` — corrected audit:
  preserves the current working roadmap, verifies the committed roadmap baseline
  separately, and classifies substantive working roadmap diffs in the audit.

- `privyhub_b6_clean_native_repository_audit_02_2026-09-11` — superseded;
  **FAILED BEFORE MODIFICATION** because it still looked for nonexistent
  repository-root `ROADMAP.md`.
- `privyhub_b6_clean_native_repository_audit_03_2026-09-11` — corrected to use
  the actual authoritative `docs/ROADMAP.md` path throughout installer, probe,
  Git HEAD lookup, Git diff classification, reports, and memory.

- `privyhub_b6_final_checkpoint_push_01_2026-09-11` — final Phase B checkpoint.
  Corrects the two B6 audit-model false positives, installs the corrected audit
  probe, removes the manifest self-entry convention, updates `docs/ROADMAP.md`
  to Phase B complete / Phase C next, selectively stages the exact audited
  scope, commits, pushes, and verifies remote main.


- `privyhub_roadmap_v3_linux_first_merge_01_2026-09-11` — roadmap-only checkpoint. Replaces the post-C roadmap with the
  accepted Linux-first sequence; expands Live TV work; retires OpenBIOS;
  formalizes user-supplied game-content import; and records local-first,
  privacy-aware optional external AI providers. No production/runtime code
  changes.


- `privyhub_c1_stream_parameter_inventory_01_2026-09-11` — C1 diagnostic-only stream parameter/ownership inventory.
  Installs `tools/probe_c1_stream_parameter_inventory.py` and advances durable
  memory to the C1.1 inventory step. No production streaming behavior changes.

- `privyhub_docs_memory_part1_repair_02_2026-09-11` — docs/durable-memory Part 1 repair after the mis-scoped
  checkpoint at `a6dbf627dd32`. Exact preflight proved the three C1 local files
  were intact and uncommitted. Installer preserves those files byte-for-byte,
  replaces only the current-state surfaces, appends durable repair history,
  rebuilds manifest semantics/registry against the authoritative local tree,
  validates the full manifest registry plus targeted Git whitespace state, and
  performs no staging/commit/push.

- `privyhub_docs_memory_part1_checkpoint_finalizer_01_2026-09-11` — exact-scope Part 1 + completed C1 inventory checkpoint finalizer.
  Gates the nine `PART1_CHECKPOINT_READY` paths by SHA-256, preserves C1
  `MEMORY.md`, `ACTIVE.md`, and the inventory probe byte-for-byte, updates only
  checkpoint-state durable memory, validates the full manifest and staged diff,
  stages no other paths, commits, pushes, and verifies remote `main`.

- `privyhub_docs_memory_part2_curation_01_2026-09-11` — Part 2 durable-memory curation. Exact-gates clean checkpoint
  `fa79d4f5feba`, snapshots the prior `MEMORY.md` byte-for-byte into
  `history/`, installs curated current `MEMORY.md` and `AGENTS.md`, defines
  deep-memory trust ordering, updates current/handoff/manifest/date/patch memory,
  validates the complete durable-memory registry, and performs no staging,
  commit or push.

- `privyhub_docs_memory_part2_checkpoint_finalizer_01_2026-09-11` — exact-scope Part 2 checkpoint finalizer. Gates the nine
  `PART2_CHECKPOINT_READY` paths by SHA-256, preserves the superseded MEMORY
  snapshot, advances current/handoff/manifest state to Part 2 checkpointed,
  validates the full durable-memory registry and staged diff, stages only the
  reviewed nine paths, commits, pushes, and verifies `origin/main == HEAD`.

- `privyhub_docs_memory_part3_normalization_01_2026-09-11` — Part 3 durable-memory normalization. Exact-gates checkpoint
  `db59209578fc`, renumbers only colliding decision headings to D-047
  through D-057, adds explicit normalization/supersession status, preserves the
  complete predecessor `ACTIVE.md` byte-for-byte in deep memory, replaces live
  ACTIVE with current work only, summarizes resolved Phase A/B/C1 inventory work
  in CLOSED, updates deferred roadmap-v3 wording, validates the full durable
  memory registry, and performs no staging/commit/push.

- `privyhub_docs_memory_part3_checkpoint_finalizer_01_2026-09-11` — exact-scope Part 3 checkpoint finalizer. Gates the ten
  `PART3_CHECKPOINT_READY` paths by SHA-256, preserves the superseded ACTIVE
  snapshot, advances current/handoff/ACTIVE/manifest state to Part 3
  checkpointed, validates unique decision IDs and the full durable-memory
  registry, stages only the reviewed ten paths, commits, pushes, and verifies
  `origin/main == HEAD`.

- `privyhub_docs_memory_part4_top_level_refresh_01_2026-09-11` — Part 4 top-level docs/ledgers refresh. Exact-gates
  checkpoint `65d020124094` and the audited Part 4 candidates, keeps
  `docs/ROADMAP.md` byte-identical, refreshes README/PROJECT_STATUS/KNOWN_ISSUES,
  runtime validation, CODE_MAP, DEBT, CHAT_INDEX and current/handoff state,
  validates the full durable-memory registry, and performs no staging/commit/push.

- `privyhub_docs_memory_part4_checkpoint_finalizer_01_2026-09-11` — exact-scope Part 4 checkpoint finalizer. Gates the thirteen
  `PART4_CHECKPOINT_READY` paths by SHA-256, verifies `docs/ROADMAP.md` remains
  byte-identical, advances Part 4/docs-cleanup state to complete, revalidates
  current content and the full durable-memory registry, stages only the reviewed
  thirteen paths, commits, pushes, and verifies `origin/main == HEAD`.

- `privyhub_minor_cleanup_game_library_startup_alpha_02_2026-09-11` — minor Games cleanup development patch. Adds
  background startup metadata/art reconciliation keyed to discovered stable game
  IDs, bounded retry for old incomplete metadata/art, count-only startup logs,
  and Games cache invalidation after successful reconciliation. Removes only the
  player-facing `Native Streaming Alpha` catalog node while preserving native
  stream endpoints/Activity. No Android source change. Runtime validation
  pending.

- `privyhub_minor_cleanup_checkpoint_finalizer_01_2026-09-11` — exact-scope checkpoint finalizer for the runtime-validated minor
  Games cleanup. Records `RECONCILED` and subsequent `SKIPPED_CURRENT` startup
  evidence, marks the cleanup runtime validated, stages only the reviewed eight
  paths, commits, pushes, verifies a clean tree and `origin/main == HEAD`, and
  returns the active technical step to `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`.

- `privyhub_c1_design_memory_patch_01_2026-09-11` — memory-only C1 design update. Corrects stale native-stream source paths, records D-058, fixes the minimal explicit profile schema/C1.1 boundary, and advances the next technical classification to `C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION`. No production/runtime source change.

- `privyhub_c1_design_memory_checkpoint_finalizer_01_2026-09-11` — exact-scope checkpoint finalizer for the C1 design durable-memory
  update. Stages only the reviewed ten memory paths, records the design memory
  checkpoint, commits/pushes it, verifies a clean tree and `origin/main == HEAD`,
  and leaves `C1_IMPLEMENT_STATIC_REFERENCE_PROFILE_EXTRACTION` as the active
  technical step.

- `privyhub_c1_static_reference_profile_01_2026-09-11` — C1.1 production development patch. Adds an immutable validated
  `NativeStreamProfile` and the `native_game_720p60_reference` profile, makes
  `companion/native_stream.py` derive the existing reference stream constants
  from it, uses explicit max-bitrate/B-frame profile fields, and exposes
  `profile_id`/profile data in native-stream status. Android, capture/audio/
  controller paths and RTP/FEC wire mechanics remain unchanged. Runtime
  validation pending.

- `privyhub_native_status_privacy_hotfix_01_2026-09-14` — privacy hotfix on top of the runtime-validated C1.1 development
  state. Sanitizes `NativeAudioStreamer.status()` so public native-stream status
  no longer publishes helper network identifiers or absolute local paths. Raw
  helper JSON remains local and unchanged. Includes a bounded validator that
  prints counts/classification only. No audio/video/controller/Android/C1 profile
  behavior changes. Runtime privacy validation pending.

- `Checkpoint: validate C1 static profile and status privacy` — checkpoints the runtime-validated C1.1 static
  reference-profile extraction together with the live-endpoint-validated
  native-stream public-status privacy hotfix. Checkpoint scope is the exact
  twelve-path reviewed working tree. No new production behavior is introduced
  by finalization. Next work is the remote-foundation architecture/roadmap
  documentation update.

- `privyhub_remote_foundation_roadmap_memory_02_2026-09-14` — documentation/durable-memory architecture update on clean checkpoint
  `0c31c100ec721d687aff6aedbd79bc0cf9343810`. Corrects the home Opal trust topology, makes Phase C
  explicitly future-remote-aware without adding WAN implementation, promotes
  Secure Remote Access / Portable Client Foundation to Phase G, renumbers later
  phases H/I/J, records D-059, adds the planned remote-access architecture
  record, and adds curated C1.1/privacy evidence. No production/runtime source
  changes.

- `Checkpoint: promote remote foundation roadmap` — checkpoints the documentation-only remote-foundation
  architecture promotion on predecessor `0c31c100ec721d687aff6aedbd79bc0cf9343810`. Establishes the home
  Opal trust boundary, Phase C future-WAN design constraint, Phase G secure
  remote/portable-client foundation, H/I/J phase reorder, D-059, provider-neutral
  overlay boundary and explicit remote identity/auth rules. No production/runtime
  source changes.

- `privyhub_c2_telemetry_contract_design_03_2026-09-14` — documentation/durable-memory-only Phase C2 design update on
  synchronized checkpoint `45ef51f9e583b459752dd5ea83163f54171e68c7`. Records the C2.1 telemetry
  inventory, adds the `privyhub_stream_telemetry_v1` architecture design,
  accepts D-060, normalizes CURRENT/HANDOFF/roadmap state from C1 to C2, and
  sets `C2_IMPLEMENT_STREAM_TELEMETRY_V1` as the next production step. No
  production/runtime source changes.

- `Checkpoint: define C2 telemetry contract` — checkpoints the documentation-only C2.1 telemetry
  inventory and C2.2 minimal `privyhub_stream_telemetry_v1` design on predecessor
  `45ef51f9e583b459752dd5ea83163f54171e68c7`. D-060 and the four missing measurement classes are now
  durable. No production/runtime source changes.

- `privyhub_c2_stream_telemetry_v1_03_2026-09-14` — development implementation of
  `C2_IMPLEMENT_STREAM_TELEMETRY_V1` on synchronized checkpoint
  `47d3cf54220146c1d727e2a0491111f6d7dea6c9`. Adds measurement-only receiver jitter, health-POST control
  round trip, signed queue-depth delta, relay send-pressure metrics, companion
  telemetry assembly, read-only diagnostics endpoint and runtime validator. No
  adaptive bitrate/FEC or packet/wire behavior change. **Runtime validated
  2026-09-14; checkpoint pending.**

- `privyhub_adb_stale_cache_recovery_fix_01_2026-09-14` — fixes the stale cached wireless-ADB failure branch in
  `tools/build_install_onn.ps1` while preserving the exact reconciled C2
  candidate. Exploratory step-2 ADB commands become fail-soft so a stale target
  can fall through to the already-accepted D-053 mDNS/reconnect/server-restart
  recovery sequence. Final device/install/launch checks remain fail-hard.
  **Runtime validated 2026-09-14 through `cached-after-server-restart`.**

- `privyhub_c2_adb_runtime_acceptance_memory_01_2026-09-14` — docs/evidence-only acceptance update for
  runtime-validated C2 telemetry and the stale-cache wireless-ADB recovery fix.
  Production/runtime bytes are exact-gated and unchanged. Promotes C2 to
  COMPLETE / RUNTIME VALIDATED / CHECKPOINT PENDING and advances the next
  development step to C3 adaptive bitrate.

- `privyhub_c3_adaptive_bitrate_design_02_2026-09-14` — documentation/design-only C3.1 source/policy audit on synchronized
  checkpoint `da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0`. Adds D-062, adaptive-bitrate architecture, and
  the active actuator-feasibility investigation. Production/runtime behavior is
  unchanged.

- `privyhub_c3_actuator_continuity_probe_01_2026-09-14` — C3 diagnostic-only development patch on synchronized
  checkpoint `f7962f667dfcbd80425db0d0ed8bff0e3c44ec4c`. Adds a loopback-only unchanged-7000
  capture+encoder cycle, keeps FEC/audio/controller ownership intact, and adds a
  two-stage evidence tool using C2 telemetry plus the existing Android
  decoder-session report. No adaptive controller, bitrate ladder, FEC change or
  Android change. **Runtime validated 2026-09-14; `video_only_restart` accepted
  as the initial backend-neutral C3 actuator strategy.**

- `privyhub_c3_actuator_runtime_acceptance_02_2026-09-14` — docs/evidence-only runtime acceptance update on exact
  post-probe state at checkpoint `f7962f667dfcbd80425db0d0ed8bff0e3c44ec4c`. Records D-063, closes the
  actuator-feasibility investigation, accepts backend-neutral
  `video_only_restart` for initial C3, records Windows-only runtime validation
  and Linux revalidation requirement, and advances C3 to fixed-bitrate
  characterization. Production diagnostic source bytes are unchanged.

- `privyhub_c3_fixed_6000_characterization_01_2026-09-14` — development-only C3 fixed-bitrate characterization
  patch on synchronized checkpoint `20a1112831f47b0c44104d547123395a89964b8a`. Adds one loopback-only
  6000 kbps candidate using the accepted video-only restart boundary, reports
  actual active bitrate separately from the 7000 reference, and adds two-stage
  telemetry/decoder evidence capture. No Android change, production ladder,
  minimum bitrate or automatic controller. Runtime evidence pending.

- `privyhub_c3_fixed_6000_runtime_acceptance_01_2026-09-14` — docs/evidence-only acceptance update on the exact
  post-characterization state from checkpoint `20a1112831f47b0c44104d547123395a89964b8a`. Records D-064,
  validates 6000 kbps as the first lower candidate, preserves decoder/audio
  findings, explicitly keeps the existing burst/gap audio pathology separate
  and deferred to Linux + Home-Opal replay, and advances characterization to
  5000 kbps. Runtime characterization source bytes are unchanged.

- `privyhub_c3_fixed_6000_runtime_acceptance_02_2026-09-14` — corrected C3 6000-kbps acceptance package.
  Supersedes `privyhub_c3_fixed_6000_runtime_acceptance_01_2026-09-14`, which rolled back because its installer treated
  successful `git diff --check` warning output as failure. v2 makes exit code
  authoritative, logs warnings separately, regression-tests exit-0-with-warning
  vs nonzero failure, records the hardening rule in durable memory, and keeps
  the intended D-064/6000 validation scope unchanged.

- `privyhub_c3_fixed_5000_characterization_01_2026-09-14` — development-only C3 fixed-5000 characterization patch on
  synchronized checkpoint `6e4563f7109f6dd1b4227a264e96e2acbd7e112d`. Generalizes the checkpointed
  fixed-bitrate video-cycle body for shared 6000/5000 use, preserves the
  existing 6000 wrapper/route, adds one loopback-only 5000 wrapper/route and
  two-stage evidence tool, and automatically reports detailed deferred-audio
  counters. No Android/FEC/controller/automatic-adaptation change. Runtime
  evidence pending.

- `privyhub_c3_fixed_5000_runtime_disposition_01_2026-09-14` — docs/evidence-only C3 5000-kbps runtime
  disposition update on the exact post-characterization state from checkpoint
  `6e4563f7109f6dd1b4227a264e96e2acbd7e112d`. Records D-065, preserves the positive clarity/recovery
  observations and all decoder findings, withholds ladder acceptance because
  extended focused play showed definitely more visual stutters than 6000/7000,
  brackets the lower boundary at 5000–6000 kbps, and advances the next single
  test point to 5500 kbps. Runtime characterization source is unchanged.

- `privyhub_c3_fixed_5500_characterization_01_2026-09-14` — development-only C3 fixed-5500 midpoint
  characterization patch on synchronized checkpoint `0f0f58ef24646a72ff1aa6b769395d8d8dd06a1b`. Extends
  the existing shared fixed-bitrate actuator target set to 6000/5000/5500,
  preserves the existing 6000 and 5000 wrappers/routes/tools, adds one
  loopback-only 5500 wrapper/route and two-stage evidence tool, and updates
  durable memory to 5500 runtime-evidence-pending. No Android/audio/FEC/
  controller/automatic-adaptation change.

- `privyhub_c3_fixed_5500_runtime_acceptance_01_2026-09-14` — docs/evidence-only C3 5500-kbps runtime acceptance on
  the exact post-characterization state from checkpoint `0f0f58ef24646a72ff1aa6b769395d8d8dd06a1b`.
  Records D-066, validates 5500 as the current Windows lower ladder level,
  preserves both the 57 whole-session decoder drops/overflows and the six
  clean post-cycle telemetry intervals, freezes the Windows controller ladder
  at 5500/6000/7000, excludes 5000, and advances C3 to adaptive bitrate
  controller implementation. Runtime characterization source is unchanged.

- `privyhub_c3_startup_stabilization_ui_01_2026-09-14` — C3 startup stabilization + shared
  stream-status UI development patch on synchronized checkpoint
  `b2f752223d0bd7617a7f7ef75c9618202d2372fa`. Keeps game paused during native startup, adds explicit
  ready/release action, evidence-driven Android overlay/readiness, gameplay
  input gating, and shared compact metadata in existing paused Game Session UI.
  Does not enable automatic bitrate switching. Runtime validation required.

- `privyhub_c3_startup_stabilization_runtime_acceptance_01_2026-09-14` — docs/evidence-only D-068 runtime
  acceptance for D-067 on checkpoint `b2f752223d0bd7617a7f7ef75c9618202d2372fa` plus the exact installed
  D-067 development working tree. Records successful stabilization/release with
  no initial lag after companion restart, preserves the stale-companion
  mixed-version diagnosis, and promotes companion restart after Python changes
  to a durable runtime-validation rule. Production source bytes unchanged.

- `privyhub_c3_bidirectional_actuator_probe_01_2026-09-14` — diagnostic-only C3 bidirectional
  actuator patch on synchronized checkpoint `9d7da2ccc47cc78a19f7128161859a1c5f308174`. Generalizes the
  already-validated shared video-only restart primitive for validated-ladder
  diagnostic transitions, preserves existing fixed-characterization semantics,
  adds a loopback-only 5500/6000/7000 transition route, and adds a two-stage
  `7000 -> 6000 -> 7000` evidence tool. No Android/FEC/audio/controller or
  automatic-adaptation change. Runtime evidence pending.

- `privyhub_c3_bidirectional_actuator_runtime_disposition_01_2026-09-14` — docs/evidence-only D-070 disposition on
  exact installed D-069 development state from checkpoint `9d7da2ccc47cc78a19f7128161859a1c5f308174`.
  Records successful bidirectional `7000 -> 6000 -> 7000` recovery, preserves
  transition-local telemetry and the ~1 s visible freeze, rejects
  `video_only_restart` for seamless automatic gameplay adaptation, retains it as
  diagnostic/startup/manual/fallback capability, and advances C3 to live bitrate
  reconfiguration investigation. Runtime source unchanged.

- `privyhub_linux_first_phase_reorder_01_2026-09-14` — docs/roadmap-only D-071 update on exact
  installed D-070 development state from checkpoint `9d7da2ccc47cc78a19f7128161859a1c5f308174`. Stops
  Windows/NVENC-specific adaptation work, reorders old phases E/F/D into new
  D Linux Migration, E Linux Characterization/Optimization, F Media/VOD/Live TV,
  preserves working media during migration without requiring polish first,
  defers adaptation/FEC continuation to Linux, and leaves G+ unchanged. No
  runtime source changes.

- `privyhub_phase_c_resume_after_linux_boundary_01_2026-09-14` — docs-only D-072 sequencing clarification
  on synchronized checkpoint `3280644bba1d6d1fe0179311b837ced29cdb9752`. Records that Phase C is paused
  rather than complete, keeps Phase D Linux migration as the immediate next
  step, then resumes unfinished C3/C4/C5/C6/C7 work on Linux before Phase E.
  No runtime source changes.

| D-074 Linux native-video backend | 2026-09-15 | Development patch: managed PID -> exact X11 window -> single FFmpeg VAAPI -> existing RTP/FEC; Windows path preserved. |

| D-075 Linux native-audio backend | 2026-09-15 | Development patch: managed PID -> isolated PulseAudio sink/monitor -> PCM16 -> hybrid 5 ms PHA1 sender; Windows audio preserved. |
| D-075R1 Linux native-audio RT pacer | 2026-09-15 | Runtime validated: sender-thread-only SCHED_RR/1 restores stable 5 ms PHA1 pacing under active RetroArch; production Linux PulseAudio route/capture/send/restore path passed. |
| D-076 Linux uinput controller backend | 2026-09-15 | Development patch: Linux PHI1/XUSB -> four evdev.UInput pads plus project-owned RetroArch udev autoconfig; Windows ViGEm preserved; runtime validation pending. |

- D-076R1 — Linux managed RetroArch autoconfig session-path correction; runtime revalidation pending.

- D-076R2 — add missing `sys` import required by D-076R1 Linux session-path branch; managed runtime revalidation pending.

## 2026-09-15 D-076 controller checkpoint status

- D-076 Linux uinput controller backend: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**.
- D-076R1 managed autoconfig session-path correction: **HOST-SIDE RUNTIME VALIDATED**.
- D-076R2 missing `sys` import correction: **HOST-SIDE RUNTIME VALIDATED**.
- The managed probe's final false classification is superseded by raw RetroArch/lifecycle evidence; see `docs/memory/evidence/linux_baseline_2026-09-15/d076_managed_retroarch_runtime_validation.txt`.

| D-077 Linux platform-aware RetroArch runtime selection | 2026-09-15 | Normal product-path runtime selector: preserve Windows base descriptor, select validated Linux AppImage/cores through an effective config; installer requires fixture + live normal-path readiness validation; onn E2E pending. |

- `D-078_LINUX_COMPANION_MEDIA_SERVER_STARTUP.md` — platform-aware companion media-server launch; Linux direct Python range server, Windows PowerShell path preserved; host startup seam validated, onn E2E pending.

- `MEMORY_NORMALIZATION_2026-09-15` — durable-memory-only normalization after
  Phase-D Linux migration and D083 closeout. Replaces stale current/handoff/
  active/roadmap summaries, updates deferred/closed/chat ledgers, marks the
  Linux UDP investigation paused, adds D073-D083 central decision summaries,
  updates the 2026-09-15 dated log, and regenerates the memory manifest. Runtime
  behavior intentionally unchanged.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:PATCH_INDEX:BEGIN -->
- `privyhub_adb_recovery_probe_linux_parity_01_2026-09-15` — development-only
  diagnostic patch aligning the Linux wireless-ADB probe with D-053
  cached-target/mDNS/reconnect/server-restart recovery. No companion, Android,
  game, media, transport, bitrate/FEC, or router production path changes.
  **Runtime validation pending.**

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:PATCH_INDEX:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:PATCH_INDEX:BEGIN -->
- `privyhub_adb_ephemeral_port_recovery_probe_01_2026-09-15` — development-only
  ADB diagnostic extending D-053 with single-private-host ephemeral TLS-port
  refresh after stale endpoint failure. Preserves no-address/no-port shareable
  logging and leaves the production onn installer unchanged pending runtime
  validation.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:PATCH_INDEX:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:PATCH_INDEX:BEGIN -->
- `privyhub_adb_ephemeral_port_recovery_probe_02_2026-09-15` — development-only
  correction after v4 failed at runtime but manual `adb connect` succeeded.
  Seeds private host/range state from an online onn, restricts stale endpoint
  search to the measured/cached device range, and adds a final repair/re-pair
  prompt plus one retry. Production installer remains unchanged pending runtime
  validation.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:PATCH_INDEX:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:PATCH_INDEX:BEGIN -->
- `privyhub_adb_endpoint_debug_probe_01_2026-09-15` — development-only endpoint
  observability after v5 recovery failed but manual `adb connect` still worked.
  Adds opt-in terminal-only literal host/port debugging; shareable logs remain
  redacted and production installer behavior is unchanged.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:PATCH_INDEX:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:PATCH_INDEX:BEGIN -->
- `privyhub_adb_endpoint_debug_watch_port_01_2026-09-15` — development-only
  targeted observability for the concurrent ADB endpoint scanner. Adds
  `--debug-watch-port` markers without changing production recovery behavior.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:PATCH_INDEX:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_INDEX -->
- `PRIVYHUB_D4_LINUX_HANDOFF_FIX_01` — Android-only D4 Linux handoff correction. v1/v2/v3 rolled back; v4 retains build-environment preflight and replaces the failed regex redaction helper with exact configured-host replacement. Runtime validation pending.
