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
