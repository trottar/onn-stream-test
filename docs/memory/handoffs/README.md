---
memory_schema: 1
as_of: 2026-11-03
status: STATUS INDEX of every file in `docs/memory/handoffs/` (249 files, this README not counted) — done 234, superseded 10, held 2, live 3; the files stay in place (DOCS-APPLY 2026-11-03, the audit's option (b))
---

# Handoffs — status index

This directory holds the task handoffs (`*_TASK.md`), the session queues (`QUEUE_*`, `OVERNIGHT_*`, `WEEKEND_*`), session B's
done reports (`SESSION_B_DONE_*`) and its step log (`SESSION_B_STATUS.txt`), the runbooks (`G4_RUNBOOK_HOTSPOT.md`,
`TRIP_RUNBOOK_2026-10-30.md`), the cowork summaries (`COWORK_HANDOFF_*`) and the living handoff file (`CURRENT_HANDOFF.md`).

- **The files stay where they are.** The records under `../evidence/` link them by these paths; nothing here is moved
  (the user's choice, option (b) of `../evidence/DOCS_AUDIT_2026-11-02.md`).
- **The verdicts are as of 2026-11-03.** They come from the audit's §1.5, updated for the files written or closed since.
  The record named in each row is authoritative, not this index.
- The docs archived elsewhere are listed in `../archive/INDEX.md`.
- Authoritative state: `../CURRENT.md`.

## Live now

- **`DOCS-APPLY_2026-11-03_TASK.md`** — running now (session C, docs only; the audit's plan, option (b)). Its report is
  to be `../evidence/MEMORY_MAINTENANCE_REPORT_2026-11-03.md` (named by the task).
- **`SESSION_B_STATUS.txt`** — B's append-only step log. Its last line (2026-11-03T03:11:36Z): queue M done.
- **`CURRENT_HANDOFF.md`** — the living handoff file; it points to `../CURRENT.md` as authoritative.
- **`SESSION_B_DONE_2026-11-02M.md` §A — HOME-2**, A's next task (the user at the TV for the hand steps): install the
  queue M APK `0132b944…` (pinned, NOT installed), restart the companion, then the re-run cells. Not yet run: no
  HOME-2 task file or record exists.

## Every file

Status: **done** (its record exists), **superseded** (replaced by the file named), **held** (never run; see below),
**live**. Closing records are under `../evidence/` unless another path is given; `…` abbreviates a record name.

| File | Status | Closing record or superseding file | Group |
|---|---|---|---|
| B4_INPUT_HOLD_REWIND_TASK.md | done | B4_INPUT_HOLD_REWIND_2026-10-22 | bench |
| BENCH-R1_BLACKOUT_AND_LOSS_CELLS_TASK.md | done | BENCH_R1_…_2026-10-22 | bench |
| BENCH-R2_LOCK_HOLD_STALL_CELLS_TASK.md | done | BENCH_R2_…_2026-10-23 | bench |
| BENCH-R3_SNES_STACK_AND_LOSS_GUARD_TASK.md | done | BENCH_R3_…_2026-10-23 | bench |
| C3-L3A-P2R1_TASK.md | done | C3_L3A_P2R1_…_2026-09-23 | phase-c |
| C3-L3A-P2R2_TASK.md | done | C3_L3A_P2R2_SMOKE_SESSION_2026-09-24 | phase-c |
| C3-L3A-P2R3_TASK.md | done | C3_L3A_P2R3_POOLING_RULE_2026-09-24 | phase-c |
| C3-L3A-R1_TASK.md | done | C3_L3A_R1_SESSION1_2026-09-24 | phase-c |
| C3-L3A-R2B_TASK.md | done | C3_L3A_R2B_REPORT_CAP_2026-09-24 | phase-c |
| C3-L3A-R2_TASK.md | done | C3_L3A_R2_SESSION2_2026-09-24 | phase-c |
| C3-L3A-R3_TASK.md | done | C3_L3A_R3_SESSION3_2026-09-24 | phase-c |
| C3-L3A-R4_GATE_RECORD_TASK.md | done | C3_L3A_R4_SESSION4_2026-09-28 | phase-c |
| C3-L3A-S1_TRANSITION_SOAK_TASK.md | done | C3_L3A_S1_TRANSITION_SOAK_2026-09-24 | phase-c |
| C3-L4-L1_LIVE_CONTROLLER_TASK.md | done | C3_L4_L1_LIVE_CONTROLLER_2026-09-28 | phase-c |
| C3-L4-L2B_NFT_HARNESS_NO_COPY_TASK.md | superseded | withdrawn for C3-L4-L2B_NFT_HARNESS_ONE_WINDOW_TASK.md | phase-c |
| C3-L4-L2B_NFT_HARNESS_ONE_WINDOW_TASK.md | done | the L2B section of C3_L4_L2_…_2026-09-29 | phase-c |
| C3-L4-L2_INCREASE_RULE_AND_NFT_HARNESS_TASK.md | done | C3_L4_L2_INCREASE_RULE_2026-09-29 | phase-c |
| C3-L4-N1_NFT_NIGHT1_SCORE_AND_CAPACITY_TRIGGER_TASK.md | done | C3_L4_N1 + C3_L4_NFT_NIGHT1 | phase-c |
| C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md | done | C3_L4_N2 + C3_L4_NFT_NIGHT2 | phase-c |
| C3-L4-N3_NFT_NIGHT3_SCORE_AND_C3L4_CLOSE_TASK.md | done | C3_L4_NFT_NIGHT3_2026-09-30 | phase-c |
| C3-L4-S1_SHADOW_CONTROLLER_TASK.md | done | C3_L4_S1_SHADOW_CONTROLLER_2026-09-24 | phase-c |
| C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md | done | C4_D1_FEC_EVIDENCE_2026-09-24 | phase-c |
| C4-M1_FEC_MEASURED_ARM_TASK.md | done | C4_M1_FEC_ARM_2026-09-25 | phase-c |
| C5-CLOSE-A_LOOK3_AMEND_TASK.md | done | C5_CLOSE_2026-10-05 (amended) | phase-c |
| C5-CLOSE_PHASE_C_CLOSE_TASK.md | done | C5_CLOSE_2026-10-05 | phase-c |
| C5-M1_1080P60_PROFILE_TASK.md | done | C5_M1_…_2026-09-28 | phase-c |
| C5-M2_1080P60_FOLLOWUP_ARMS_TASK.md | done | C5_M2_…_2026-09-29 | phase-c |
| C5-M3_LOW_RUNG_SCREENING_TASK.md | done | C5_M3_…_2026-09-29 | phase-c |
| C5-M4A_PS1_4X_SOURCE_ADOPTION_TASK.md | done | C5_M4A_…_2026-10-01 | phase-c |
| C5-M4_PS1_NATIVE_1080P_SOURCE_TASK.md | done | C5_M4_…_2026-10-01 | phase-c |
| C5-M5B_RUNG_RULES_AND_LOOK_TASK.md | done | C5_M5B_…_2026-10-03 | phase-c |
| C5-M5_1080P_RUNG_TASK.md | done | C5_M5_1080P_RUNG_2026-10-03 | phase-c |
| C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md | done | C6_D1_SOURCE_CONTRACT_2026-09-25 | phase-c |
| CL-B10_PART2_ATTENDED_TASK.md | done | CL_B10_…_2026-10-23 | cl-b |
| CL-B11_GUARD_AND_FAST_READY_TASK.md | done | CL_B11_…_2026-10-24 | cl-b |
| CL-B12_DEFAULTS_AND_UMBRELLA_TASK.md | done | CL_B12_…_2026-10-24 | cl-b |
| CL-B13_RESTART_FAST_AND_WAN_CLASS_TASK.md | done | CL_B13_…_2026-10-25 | cl-b |
| CL-B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_TASK.md | done | CL_B14_…_2026-10-26 (APK `fcd924c2…` CONFIRMED) | cl-b |
| CL-B15_LOSS_GUARD_DEFAULT_TASK.md | done | CL_B15_…_2026-10-27 | cl-b |
| CL-B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_TASK.md | done | CL_B16_…_2026-10-29 | cl-b |
| CL-B1_APK_ADOPTION_TASK.md | done | CL_B1_APK_ADOPTION_2026-09-30 | cl-b |
| CL-B2_IDENTITY_APK_INSTALL_AND_LAN_SMOKE_TASK.md | done | CL_B2_…_2026-10-16 | cl-b |
| CL-B4_APK_OPUS_DECODE_TASK.md | done | CL_B4_…_2026-10-18 | cl-b |
| CL-B5_OPUS_DECODE_THREAD_AND_AB_TASK.md | done | CL_B5_…_2026-10-18 | cl-b |
| CL-B6_AB_REPEAT_AFTER_RESTART_TASK.md | done | CL_B6_…_2026-10-19 | cl-b |
| CL-B7P_OPUS_CLIENT_COST_TASK.md | done | CL_B7P_…_2026-10-19 | cl-b |
| CL-B7_OPUS_CLIENT_THREADS_AB_TASK.md | done | CL_B7_…_2026-10-19 | cl-b |
| COWORK_HANDOFF_2026-09-22.md | superseded | COWORK_HANDOFF_2026-09-23.md (this one: cowork context 09-20..22) | cowork |
| COWORK_HANDOFF_2026-09-23.md | superseded | COWORK_HANDOFF_2026-09-29.md | cowork |
| COWORK_HANDOFF_2026-09-29.md | superseded | COWORK_HANDOFF_2026-10-05.md | cowork |
| COWORK_HANDOFF_2026-10-05.md | superseded | `../CURRENT.md` and the records; its "how we work" section is the audit's source for `../COMMUNICATION.md` | cowork |
| CTRL-L1_CONTROLLER_LOSS_LOCATION_TASK.md | done | CTRL_L1_…_2026-09-24 | phase-c |
| CURRENT_HANDOFF.md | live | living file; `../CURRENT.md` is authoritative | living |
| D-BASE-B2_TASK.md | done | B2_HOST_ON_…_2026-09-21 | d-base |
| D-BASE-C5A_TASK.md | done | C5A_IDR_REJECTION_COUNT_2026-09-21 | d-base |
| D-BASE-C5_TASK.md | done | `../investigations/`C5_RESYNC_…_2026-09-20 | d-base |
| D-BASE-CLOSE_TASK.md | done | D_BASE_CLOSEOUT_2026-09-23 | d-base |
| D-BASE-H2_TASK.md | done | H2_HEADLESS_CUTOVER_2026-09-22 | d-base |
| D-BASE-N05_CLOSE_TASK.md | done | the N05 section of D_BASE_R3D_HAND_RUNS | d-base |
| D-BASE-O1_TASK.md | done | O1_…_AIR_VIEW_2026-09-21 | d-base |
| D-BASE-P10_TASK.md | done | D_BASE_P10_…_2026-09-23 | d-base |
| D-BASE-P1_TASK.md | done | D_BASE_P1_…_2026-09-20 | d-base |
| D-BASE-P2A_TASK.md | done | D_BASE_P2A_…_2026-09-21 | d-base |
| D-BASE-P2B_TASK.md | done | D_BASE_P2B_…_2026-09-21 | d-base |
| D-BASE-P2_TASK.md | done | D_BASE_P2_…_2026-09-20 | d-base |
| D-BASE-P3_TASK.md | done | D_BASE_P3_…_2026-09-21 | d-base |
| D-BASE-P4_TASK.md | done | D_BASE_P4_…_2026-09-21 | d-base |
| D-BASE-P5_TASK.md | done | D_BASE_P5_…_2026-09-21 | d-base |
| D-BASE-P6A_TASK.md | done | D_BASE_P6A_CAP_ADOPTED_2026-09-22 | d-base |
| D-BASE-P6_TASK.md | done | D_BASE_P6_…_2026-09-21 | d-base |
| D-BASE-P7_TASK.md | done | D_BASE_P7_…_2026-09-22 | d-base |
| D-BASE-P8_TASK.md | done | D_BASE_P8_…_2026-09-22 | d-base |
| D-BASE-P9A_TASK.md | done | D_BASE_P9A_…_2026-09-23 | d-base |
| D-BASE-P9_TASK.md | done | D_BASE_P9_…_2026-09-23 | d-base |
| D-BASE-R3A_TASK.md | done | D_BASE_R3A_…_2026-09-20 | d-base |
| D-BASE-R3B_TASK.md | done | D_BASE_R3B_…_2026-09-22 | d-base |
| D-BASE-R3C2_TASK.md | done | D_BASE_R3C2_…_2026-09-23 | d-base |
| D-BASE-R3C_TASK.md | done | D_BASE_R3C_… (part 2 via R3C2) | d-base |
| D-BASE-R3D_TASK.md | done | D_BASE_R3D_HAND_RUNS_2026-09-22 | d-base |
| D-BASE-R3_TASK.md | done | D_BASE_R3_…_2026-09-20 | d-base |
| D-BASE-R4_TASK.md | done | D_BASE_R4_…_2026-09-20 | d-base |
| D-BASE-R5_TASK.md | done | D_BASE_R5_…_2026-09-21 | d-base |
| D-BASE-S1_TASK.md | done | D_BASE_S1_…_2026-09-21 | d-base |
| D-BASE-S2_TASK.md | done | D_BASE_S2_…_2026-09-21 | d-base |
| D-BASE-S3_TASK.md | done | D_BASE_S3_…_2026-09-22 | d-base |
| D-BASE-T1_TASK.md | done | D_BASE_T1_…_2026-09-21 | d-base |
| D-BASE-T2_TASK.md | done | D_BASE_T2_…_2026-09-23 | d-base |
| D-BASE-T3_TASK.md | done | D_BASE_T3_…_2026-09-23 | d-base |
| D6-R1_UDP_SUITE_REPLAY_TASK.md | done | D6_R1_…_2026-09-24 | phase-c |
| D7-R1_LINUX_REGRESSION_TASK.md | done | D7_R1_…_2026-09-25 (named in a tool docstring) | phase-c |
| DOCS-APPLY_2026-11-03_TASK.md | live | running now; its report is to be MEMORY_MAINTENANCE_REPORT_2026-11-03 | docs |
| DOCS-AUDIT_2026-11-02_TASK.md | done | DOCS_AUDIT_2026-11-02 | docs |
| E1-S1_WORKLOAD_SUITE_FREEZE_TASK.md | done | E1_S1_…_2026-10-05 | phase-e |
| E2-S1_WHOLE_SYSTEM_MEASUREMENTS_TASK.md | done | E2_S1_…_2026-10-06 | phase-e |
| E3-A2_FRAME_SPIN_AND_SNES9X_ADOPTION_TASK.md | done | E3_A2_…_2026-10-07 | phase-e |
| E3-A3B_RECOVERY_V2_READOPTION_TASK.md | done | E3_A3B_…_2026-10-09 | phase-e |
| E3-A3_RECOVERY_V2_ADOPTION_TASK.md | done | E3_A3_… (reverted, redone by A3B) | phase-e |
| E3-R1_RECOVERY_FALSE_PAUSE_TASK.md | done | E3_R1_…_2026-10-08 | phase-e |
| E3-R2_RECOVERY_PAUSE_EXIT_TASK.md | done | E3_R2_…_2026-10-08 | phase-e |
| E3-S1_EPG_GRAB_PRIORITY_TASK.md | done | E3_S1_…_2026-10-06 | phase-e |
| E3-S2_COMPANION_GUIDE_RETENTION_TASK.md | done | E3_S2_…_2026-10-06 | phase-e |
| E3-S3_GRABBER_COST_TASK.md | done | E3_S3_…_2026-10-06 | phase-e |
| E3-S4_SNES_LIGHTER_CORE_TASK.md | done | E3_S4_…_2026-10-06/07 | phase-e |
| E3-S5B_AUDIO_SENDER_PACING_DECISIVE_TASK.md | done | E3_S5B_…_2026-10-06 | phase-e |
| E3-S5C_AUDIO_SENDER_PACING_SPIN_TASK.md | done | E3_S5C_…_2026-10-07 | phase-e |
| E3-S5_AUDIO_SENDER_COST_TASK.md | done | E3_S5_…_2026-10-06 | phase-e |
| E3-S6A_GUIDE_INDEX_ADOPTION_TASK.md | done | E3_S6A_…_2026-10-07 | phase-e |
| E3-S6_GUIDE_INDEX_TASK.md | done | E3_S6_…_2026-10-07 | phase-e |
| E3-S7B_GRAB_PACING_SHORT_TASK.md | done | E3_S7B_…_2026-10-08 | phase-e |
| E3-S7_CONC_GRAB_SPAWN_TASK.md | done | E3_S7_…_2026-10-08 | phase-e |
| E4-C1_CLOSEOUT_AND_E5_S1_CAPABILITY_PROBE_TASK.md | done | E4_CLOSEOUT + E5_S1_…_2026-10-15 | phase-e |
| E4-S1_REFERENCE_ON_ADOPTED_STATE_TASK.md | done | E4_S1_…_2026-10-09 | phase-e |
| E4-S2_CPU_MEMORY_FLOOR_TASK.md | done | E4_S2_…_2026-10-09 | phase-e |
| E4-S3B_MEMORY_FLOOR_1G_SWAPOFF_TASK.md | done | E4_S3B_…_2026-10-10 | phase-e |
| E4-S3_MEMORY_FLOOR_CLOSE_TASK.md | done | E4_S3_…_2026-10-10 | phase-e |
| E4-S4B_GRAB_DEFERRAL_CLEAN_LINK_TASK.md | done | E4_S4B_…_2026-10-10 | phase-e |
| E4-S4C_LINK_WATCH_AND_DEFERRAL_TASK.md | done | E4_S4C_LINK_WATCH_2026-10-16 (ran via S4D) | phase-e |
| E4-S4C_WATCH_RECORD_TASK.md | done | E4_S4C_LINK_WATCH_2026-10-16 | phase-e |
| E4-S4D_LINK_WATCH_DETACHED_TASK.md | done | E4_S4D_…_LAUNCH_2026-10-15 | phase-e |
| E4-S4_GRAB_DEFERRAL_TASK.md | done | E4_S4_…_2026-10-10 | phase-e |
| E4-S5B_SNES_CAPTURE_PROBE_BENCH_TASK.md | done | E4_S5B_…_2026-10-10 | phase-e |
| E4-S5C_SNES_CAPTURE_PROBE_BENCH_CFR_TASK.md | done | E4_S5C_…_2026-10-10 | phase-e |
| E4-S5D_SNES_CAPTURE_FIX_ADOPTION_TASK.md | done | E4_S5D_…_2026-10-15 | phase-e |
| E4-S5_SNES_CAPTURE_59FPS_TASK.md | done | E4_S5_…_2026-10-10 | phase-e |
| G-A10_STEP_IN_PLACE_ADOPTION_TASK.md | done | G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02 | g-track |
| G-A1_ADOPTION_AND_CL-B3_TASK.md | done | G_A1_…_2026-10-16 + CL_B3_… | g-track |
| G-A2_OPUS_ADOPTION_TASK.md | done | G_A2_…_2026-10-19 | g-track |
| G-A3_AND_CL-B10_TASK.md | done | G_A3_…_2026-10-23 + CL_B10_… | g-track |
| G-A4_LINK_RECOVERY_ADOPTION_TASK.md | done | G_A4_…_2026-10-24 | g-track |
| G-A5_RESTART_FAST_ADOPTION_TASK.md | done | G_A5_…_2026-10-26 | g-track |
| G-A7_RESTART_FAST_UNLOCK_ADOPTION_TASK.md | done | G_A7_…_2026-10-27 | g-track |
| G1-S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_TASK.md | done | G1_S1_…_2026-10-15 | g-track |
| G1-S2_OVERLAY_PROVIDER_LIVE_SMOKE_TASK.md | done | G1_S2_…_2026-10-16 | g-track |
| G3-S1_SESSION_IDENTITY_HOST_SIDE_TASK.md | done | G3_S1_…_2026-10-15 | g-track |
| G3-S2_SESSION_IDENTITY_CLIENT_SIDE_TASK.md | done | G3_S2_…_2026-10-16 | g-track |
| G3-S3_HARDENING_AND_HUB_HOST_TASK.md | done | G3_S3_…_2026-10-16 | g-track |
| G4-P1_OFFSITE_TEST_PREP_TASK.md | done | G4_P1_…_2026-10-16 | g-track |
| G4-P2_REMOTE_ROW_GATE3_TASK.md | done | G4_P2_…_2026-10-17 | g-track |
| G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md | superseded | G4-S1_OFFSITE_FIRST_SESSION_TASK.md (this is its draft) | g-track |
| G4-S1_OFFSITE_FIRST_SESSION_TASK.md | done | G4_S1_…_2026-10-16 | g-track |
| G4-S2_OFFSITE_REMOTE_LADDER_TASK.md | done | G4_S2_…_2026-10-17 | g-track |
| G4-S3_OFFSITE_4000_OPUS_TASK.md | done | G4_S3_…_2026-10-19 | g-track |
| G4-S4_OFFSITE_FREE_PLAY_TASK.md | done | G4_S4_…_2026-10-24 | g-track |
| G4-W1_WIRE_OVERHEAD_BREAKDOWN_TASK.md | done | G4_W1_…_2026-10-18 | g-track |
| G4-W2_OPUS_AUDIO_PATH_TASK.md | done | G4_W2_…_2026-10-18 | g-track |
| G4_RUNBOOK_HOTSPOT.md | done | runbook: G4-S1's hotspot choreography, and G4-S1 ran (its §A, the one-time overlay onboarding, is the audit's source for `docs/RUNBOOK.md`) | g-track |
| G5-S1_WAN_TELEMETRY_CLASSIFICATION_TASK.md | done | G5_S1_…_2026-10-16 | g-track |
| G5-S2_WAN_ADAPTATION_RULES_TASK.md | done | G5_S2_…_2026-10-16 | g-track |
| G5-S3_LAN_SMOKE_TASK.md | done | G5_S3_LAN_SMOKE_2026-10-17 | g-track |
| G5-S3_REMOTE_LADDER_TASK.md | done | G5_S3_REMOTE_LADDER_2026-10-17 | g-track |
| G5-S4_REMOTE_RUNG_CAP_TASK.md | done | G5_S4_…_2026-10-17 | g-track |
| G8-P1_IMPAIRMENT_SHIM_TASK.md | done | G8_P1_…_2026-10-16 | g-track |
| G8-S1_ADVERSE_NETWORK_ENVELOPE_TASK.md | done | G8_S1_…_2026-10-17 | g-track |
| G8-S1_FINAL_RECORD_TASK.md | done | G8_S1_…_2026-10-17 | g-track |
| G8-S1_RESUME_TASK.md | done | G8_S1_RESUME_2026-10-17 | g-track |
| G8-S1_STOP_AND_PARTIAL_RECORD_TASK.md | done | G8_S1_… partial, 2026-10-16 | g-track |
| G8-S2_START_RUNG_TASK.md | done | G8_S2_…_2026-10-17 | g-track |
| G8-S3_CAP_CELLS_START_RUNG_TASK.md | done | G8_S3_LAUNCH_2026-10-17 | g-track |
| G8-S3_RECORD_TASK.md | done | G8_S3_…_2026-10-17 | g-track |
| G8-S4_ENCODER_RATE_HEADROOM_TASK.md | done | G8_S4_…_2026-10-18 | g-track |
| G8-S5_CAP_CELL_ENCODER_RC_TIGHT_TASK.md | done | G8_S5_…_2026-10-19 | g-track |
| H1_VERIFY_TASK.md | done | H1_VERIFY_…_2026-09-22 | overnight |
| H2_CLOSE_TASK.md | done | H2_HEADLESS_CUTOVER_2026-09-22 | overnight |
| H2_PREP_TASK.md | done | H2_PREP_…_2026-09-22 | overnight |
| H3_COMPANION_AUTOSTART_TASK.md | done | H3_…_DESIGN_2026-09-23 | overnight |
| HOME-1_TRIP_CLOSE_AND_QUEUE_L_CELLS_TASK.md | done | HOME_1_…_2026-11-02 | trip |
| LAN-R1_LOSS_STEPDOWN_REPLAY_AND_DESIGN_TASK.md | done | LAN_R1_…_2026-10-21 | ux-reads |
| LINK-L1_LOSS_ROW_LOOK_AND_LIVE_DEFAULT_TASK.md | done | LINK_L1_… + C3_L4_D1_… | phase-c |
| LINK-L2_LOSS_ROW_AT_40MHZ_TASK.md | done | LINK_L2_…_2026-10-02 | phase-c |
| LINK-R1_5GHZ_CHECK_AND_NIGHTLY_WATCH_TASK.md | done | LINK_R1_… + LINK_N1_LAUNCH (the watch ended 10-31; no nights record found) | ux-reads |
| M1_DOCS_RECONCILE_TASK.md | done | CHECKPOINT_PROPOSAL_2026-09-22 | overnight |
| ML-R1_HITCH_EARLY_WARNING_TASK.md | done | ML_R1_…_2026-10-23 | ux-reads |
| OVERNIGHT_2026-09-22_QUEUE.md | done | the P6A, S3, P7, H2-PREP, M1 records | overnight |
| OVERNIGHT_2026-09-23B_QUEUE.md | done | the N05, R3C2, H3 records | overnight |
| OVERNIGHT_2026-09-23_QUEUE.md | done | the P8, R3C records | overnight |
| OVERNIGHT_2026-09-24_QUEUE.md | done | the C3_L3A_S1 record | overnight |
| PHASE_C_PRECONDITIONS_2026-09-25_TASK.md | done | C3_F1, D7_R1 §R2, CL_B1 | phase-c |
| PLAN_WEEK_2026-09-21.md | superseded | a week plan, overtaken by the later queues (no single successor recorded) | overnight |
| PREPUSH_AUDIT_TASK.md | done | PREPUSH_AUDIT_2026-10-05 | phase-c |
| QUEUE_2026-09-28.md | done | C3_L3A_R4, C5_M1 | queues |
| QUEUE_2026-09-28B.md | superseded | QUEUE_2026-09-29.md | queues |
| QUEUE_2026-09-29.md | superseded | QUEUE_2026-09-29B.md | queues |
| QUEUE_2026-09-29B.md | done | C3_L4_N1, C5_M2, C5_M3 | queues |
| QUEUE_2026-10-06.md | done | E3_S1..S5 | queues |
| QUEUE_2026-10-06B.md | done | E3_S5B, E3_S6 | queues |
| QUEUE_2026-10-07.md | done | E3_S4, S5C, S6A | queues |
| QUEUE_2026-10-08.md | done | E3_R1, S7 | queues |
| QUEUE_2026-10-08B.md | done | E3_R2, S7B | queues |
| QUEUE_2026-10-09.md | done | E4_S1, S2 | queues |
| QUEUE_2026-10-10.md | done | E4_S3, S4, S5 | queues |
| QUEUE_2026-10-10B.md | done | E4_S3B, S4B, S5B | queues |
| QUEUE_2026-10-10C.md | done | E4_S4C, S5C | queues |
| QUEUE_2026-10-15.md | done | SESSION_B_DONE_2026-10-15.md + E4_S5D | queues |
| QUEUE_2026-10-15B.md | done | SESSION_B_DONE_2026-10-15B.md | queues |
| QUEUE_2026-10-16.md | done | CL_B2, E4_S4C, G1_S2 | queues |
| QUEUE_2026-10-16B.md | done | SESSION_B_DONE_2026-10-16B.md | queues |
| QUEUE_2026-10-16C.md | done | SESSION_B_DONE_2026-10-16C2.md | queues |
| QUEUE_2026-10-17.md | done | SESSION_B_DONE_2026-10-17.md | queues |
| QUEUE_2026-10-18.md | done | SESSION_B_DONE_2026-10-18.md | queues |
| QUEUE_2026-10-19B.md | held | none: never run (no report, draft, logs or DONE file); see "Held" | queues |
| QUEUE_2026-10-19N.md | held | none: never run (no launch, record or unit); see "Held" | queues |
| QUEUE_2026-10-22B.md | done | SESSION_B_DONE_2026-10-22.md | queues |
| QUEUE_2026-10-22C.md | done | SESSION_B_DONE_2026-10-22C.md | queues |
| QUEUE_2026-10-22D.md | done | SESSION_B_DONE_2026-10-22D.md | queues |
| QUEUE_2026-10-23E.md | done | SESSION_B_DONE_2026-10-23E.md | queues |
| QUEUE_2026-10-24F.md | done | SESSION_B_DONE_2026-10-24F.md | queues |
| QUEUE_2026-10-24G.md | done | SESSION_B_DONE_2026-10-24G.md | queues |
| QUEUE_2026-10-24H.md | done | SESSION_B_DONE_2026-10-24H.md | queues |
| QUEUE_2026-10-26I.md | done | SESSION_B_DONE_2026-10-26I.md | queues |
| QUEUE_2026-10-27J.md | done | SESSION_B_DONE_2026-10-27J.md | queues |
| QUEUE_2026-10-28K.md | done | SESSION_B_DONE_2026-10-28K.md | queues |
| QUEUE_2026-10-31L.md | done | SESSION_B_DONE_2026-10-31L.md | queues |
| QUEUE_2026-11-02M.md | done | SESSION_B_DONE_2026-11-02M.md; records B38_VIRTUAL_REMOTE_NO_SLOT_2026-11-02, B39_HOLD_COUNTER_2026-11-02, B40_VOD_DROP_TEST_2026-11-02 | queues |
| SESSION_B_DONE_2026-10-15.md | done | closes QUEUE_2026-10-15 (B's part) | session-b-done |
| SESSION_B_DONE_2026-10-15B.md | done | closes QUEUE_2026-10-15B | session-b-done |
| SESSION_B_DONE_2026-10-16.md | done | closes G3-S2 | session-b-done |
| SESSION_B_DONE_2026-10-16B.md | done | closes QUEUE_2026-10-16B | session-b-done |
| SESSION_B_DONE_2026-10-16C.md | done | closes G3-S3 | session-b-done |
| SESSION_B_DONE_2026-10-16C2.md | done | closes QUEUE_2026-10-16C | session-b-done |
| SESSION_B_DONE_2026-10-17.md | done | closes QUEUE_2026-10-17 | session-b-done |
| SESSION_B_DONE_2026-10-17B.md | done | closes G8-S2 | session-b-done |
| SESSION_B_DONE_2026-10-18.md | done | closes QUEUE_2026-10-18 | session-b-done |
| SESSION_B_DONE_2026-10-19.md | done | closes CL-B7P (not QUEUE_2026-10-19B) | session-b-done |
| SESSION_B_DONE_2026-10-21.md | done | closes LAN-R1 | session-b-done |
| SESSION_B_DONE_2026-10-22.md | done | closes QUEUE_2026-10-22B | session-b-done |
| SESSION_B_DONE_2026-10-22B.md | done | closes B4 | session-b-done |
| SESSION_B_DONE_2026-10-22C.md | done | closes QUEUE_2026-10-22C | session-b-done |
| SESSION_B_DONE_2026-10-22D.md | done | closes QUEUE_2026-10-22D | session-b-done |
| SESSION_B_DONE_2026-10-23E.md | done | closes QUEUE_2026-10-23E | session-b-done |
| SESSION_B_DONE_2026-10-24F.md | done | closes QUEUE_2026-10-24F | session-b-done |
| SESSION_B_DONE_2026-10-24G.md | done | closes QUEUE_2026-10-24G | session-b-done |
| SESSION_B_DONE_2026-10-24H.md | done | closes QUEUE_2026-10-24H | session-b-done |
| SESSION_B_DONE_2026-10-26I.md | done | closes QUEUE_2026-10-26I | session-b-done |
| SESSION_B_DONE_2026-10-27J.md | done | closes QUEUE_2026-10-27J | session-b-done |
| SESSION_B_DONE_2026-10-28K.md | done | closes QUEUE_2026-10-28K | session-b-done |
| SESSION_B_DONE_2026-10-31L.md | done | closes QUEUE_2026-10-31L; holds the HOME-1 strings that queue M's HOME-2 builds on | session-b-done |
| SESSION_B_DONE_2026-11-02M.md | done; holds the live HOME-2 sketch | closes QUEUE_2026-11-02M (§A: HOME-2, not yet run) | session-b-done |
| SESSION_B_STATUS.txt | live | B's append-only step log (B writes it) | session-b |
| TRIP-PREP_2026-10-29_TASK.md | done | TRIP_PREP_2026-10-29 | trip |
| TRIP-R1_MULTIPLAYER_BLITZ_READ_TASK.md | superseded | TRIP-R2_FRIDAY_GAMEPLAY_READ_TASK.md (folded in; never run) | trip |
| TRIP-R2_FRIDAY_GAMEPLAY_READ_TASK.md | done | TRIP_R2_…_2026-10-31 | trip |
| TRIP_RUNBOOK_2026-10-30.md | done | runbook: the user's trip steps A–F; the trip ran and was closed by HOME-1 (HOME_1_…_2026-11-02) | trip |
| UX-R1_EXTENDED_SESSION_REGRESSION_READ_TASK.md | done | UX_R1_…_2026-10-20 | ux-reads |
| UX-R2_SECOND_EVENING_READ_TASK.md | done | UX_R2_…_2026-10-21 | ux-reads |
| UX-R3_FIND_THE_DEATHS_TASK.md | done | UX_R3_…_2026-10-21 | ux-reads |
| UX-R4_SAVED_AT_THE_LAG_TASK.md | done | UX_R4_…_2026-10-23 | ux-reads |
| WAN-R1_OFFSITE_GAP_DISTRIBUTION_TASK.md | done | WAN_R1_…_2026-10-24 | ux-reads |
| WEEKEND_2026-09-24_QUEUE.md | done | all five of its records exist | overnight |
| WEEKEND_2026-09-25_QUEUE.md | done | C4_M1, C6_D1, D7_R1 | overnight |

**Count:** 249 rows = `git ls-files docs/memory/handoffs | wc -l` (249) before this README was added. Done 234,
superseded 10, held 2, live 3.

## Held

- **`QUEUE_2026-10-19B.md`** (session B: M-2 memory maintenance, then G9-D1, the Phase G checkpoint draft). Never run.
  - **M-2, the memory maintenance:** done by DOCS-APPLY 2026-11-03 (CURRENT.md under its limit; the report is
    `../evidence/MEMORY_MAINTENANCE_REPORT_2026-11-03.md`). The queue's own specifics ("the eight lines", the newest
    blocks it names) are overtaken.
  - **G9-D1, the G9 checkpoint draft:** still wanted, as its own later task (audit §2.7); not part of the cleanup.
- **`QUEUE_2026-10-19N.md`** (session A night driver). Never run; its preconditions ("the eight lines") are stale.
  - **G8-S6** (three paired cap-6000 cells, control vs `PRIVYHUB_ENCODER_RC=tight`: does `tight` keep a capped
    stream from going silent?) and **G5-S2-L** (the first live LAN smoke of the WAN adaptation rules) were never run.
  - Both questions are still open; DOCS-APPLY carries them into `docs/KNOWN_ISSUES.md`'s open index (its step 4).
