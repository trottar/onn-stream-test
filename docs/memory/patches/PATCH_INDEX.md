---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Patch / Checkpoint Index

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
