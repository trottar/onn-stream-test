---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 65d02012409440d5559c14beb2b28268b0b225bc
---

# Runtime Validation Ledger

This ledger records what is actually runtime validated. Configuration/support
alone is not validation. Newer specific evidence overrides older intermediate
failure states preserved elsewhere.

| Area | Status | Key runtime evidence |
| --- | --- | --- |
| A1 Controller/analog | COMPLETE / runtime validated | Digital/analog behavior, PS1 controller modes and multi-controller routing validated. |
| A2 Save/Load | COMPLETE / runtime validated | Slots, persistent state, integrity checks, RetroArch control path, graceful flush and prior-save preservation. |
| A3 Pause/Resume | COMPLETE / runtime validated | Frozen preview, stream stop/restart, emulator remains alive, controls remain available. |
| A4 Host coexistence/audio | COMPLETE / runtime validated | Process-specific game audio reaches TV, local duplicate suppressed, host remains usable, crash-safe restoration validated. |
| A5 Direct launch | COMPLETE / runtime validated | Companion launch/readiness goes directly to gameplay and fails closed when readiness fails. |
| A6 Metadata/art | COMPLETE / runtime validated | Stable IDs, catalog metadata/art and normal organization path exercised. |
| A7 Cheats | COMPLETE / runtime validated | Exact activation, isolated cheat-profile saves/states, normal namespaces protected. |
| A7 Mods | COMPLETE / runtime validated | Deterministic IPS-derived ROM path, visible mod, Save/Load/reopen, canonical ROM protected. |
| A8 input profiles | COMPLETE / runtime validated | Profile CRUD/assignment, P1-P4 capabilities, generated session binds, Android editor/copy UI, conflict validation and user mapping tests. |
| Four-player transport / ViGEm | COMPLETE / runtime validated | PHI1 v1 preserved; four slots/devices; exact P1->1 through P4->4 routing; neutral release/teardown. |
| Four-player physical Android assignment | COMPLETE / runtime validated | Four real controllers reached four distinct host slots with isolated presses/releases. |
| RetroArch ports 1-4 | COMPLETE / runtime validated | XInput selected; Xbox controllers configured on ports 1-4 with no startup fallback. |
| Four-player gameplay | COMPLETE / runtime validated | Crash Bash four-human Battle Mode; P1-P4 independently controlled intended players; clean teardown. |
| PS1 manual Multitap On/Off | COMPLETE / runtime validated | Port-1-only product rule validated with Crash Bash and CTR; Port 2 remains disabled. |
| A9 Phase A regression/checkpoint | COMPLETE / checkpointed | PS1/SNES exercised, 1P/2P/4P lifecycle and major Phase A features preserved. NES/Genesis had no local fixtures. |
| Phase B health/diagnostics | COMPLETE / runtime/manual validated | Health endpoint, client feedback, decoder/network classifier correction, event history, Diagnostics/Self-Test and support-bundle path validated. |
| Phase B retention | COMPLETE / runtime validated | Bounded/manual retention, protected-file behavior and blocker semantics validated. |
| Sunshine/Moonlight removal | COMPLETE / runtime validated | Production edge, repository artifacts and device package removed; focused native-only regression passed. |
| Native game streaming baseline | COMPLETE / runtime validated | WGC -> H.264 NVENC -> RTP UDP -> 8+1 XOR FEC -> Android hardware AVC; process audio/controller/lifecycle preserved. |
| C1 stream-parameter inventory | COMPLETE / diagnostic | `C1_INVENTORY_COMPLETE`; ownership/duplication captured with no inventory failures. |
| C1 explicit profile implementation | COMPLETE / runtime validated | `C1_STATIC_PROFILE_AND_STATUS_PRIVACY_VALIDATED_2026-09-14.md`; `native_game_720p60_reference` in `companion/native_stream_profiles.py`, reported by `native-stream-status`. The old "next classification is `C1_DESIGN_MINIMAL_EXPLICIT_PROFILE_SCHEMA`" line is superseded. |
| `D-BASE` baseline stream health | **ACTIVE** — loss column closed, target table not yet met | `docs/memory/investigations/BASELINE_STREAM_HEALTH.md`; per-item rows in the 2026-09-20/22 ledger below. |

## Emulator-family coverage boundary

- **PS1:** extensive runtime coverage.
- **SNES:** runtime exercised.
- **NES:** configured/supported but no local A9 fixture; not runtime validated.
- **Genesis:** configured/supported but no local A9 fixture; not runtime validated.

Do not upgrade NES/Genesis status without representative fixture evidence.

## Current native reference

Reference stream behavior:

- 1280x720;
- 60 fps;
- 7000 kbps target;
- GOP 15;
- B-frames 0;
- **max frame size 90,000 bytes** (adopted 2026-09-22, `D-BASE-P6a`;
  Linux `h264_vaapi` path only, NVENC ignores it);
- FEC group size 8;
- RTP payload type 96;
- 1200-byte packet size;
- x11grab capture on Linux / WGC on Windows;
- Android hardware AVC decode.

C1 reproduced this behavior through an explicit static profile (done,
2026-09-14). `max_frame_size_bytes` is the first parameter added to that
profile from transport evidence rather than inherited from the Windows
build (`D-BASE-P6a`, 2026-09-22).

## Deferred transport evidence

The current Windows/network environment can show severe UDP timing
transformation/duplication outside normal application pacing. That investigation
is deferred until representative Linux/network infrastructure exists unless it
becomes a blocker first.

This does not invalidate the native baseline. Do not enlarge production buffers
or otherwise encode the current environment’s pathology as a product
requirement without representative evidence.

## 2026-09-20 to 2026-09-22 — the `D-BASE` ledger

One line per record, newest first. The record named is authoritative; the
longer sections below expand the three that changed the product.

| item | classification | record (`evidence/`) |
| --- | --- | --- |
| `H2-PREP` host display/session/boot inventory | INVENTORY RECORDED — read-only, nothing changed | `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` |
| `H2` headless cutover behind the DisplayPort dummy plug | RUNTIME VALIDATED — checks 1-5 PASS across two plug-only boots; capture unchanged (879x720 window, 60 fps); companion started by hand | `H2_HEADLESS_CUTOVER_2026-09-22.md` |
| `D-BASE-R3c` recovery load in a fresh core (Part 1 probe) | CHARACTERIZED — mid-FMV save loops loaded paused, fresh core or not; plays loaded running; gameplay state loaded paused plays. Fix INDETERMINATE, not implemented (user decision) | `D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md` |
| `D-BASE-R3c2` recovery flow (never into a live core; option A running-core load) | **RUNTIME VALIDATED** — checks 0-6 PASS (fresh running load plays 607 distinct; Resume tile same pid; prompt only without a live session; discard, copy-to-slot, cross-title; gameplay save 1,630 distinct) | `D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md` |
| **`D-BASE` close-out** — the target table on the adopted build | **BASELINE MET** (pre-registered): cold / warm spikes 32.8 / 26.0, fps 59.90 / 59.91, stale 1.1 / 0.8, video loss 8.7 / 8.4, underruns 17 / 14; max gap 163 / 110 ms (transport, open row); client decision not triggered; `D-BASE` CLOSED | `D_BASE_CLOSEOUT_2026-09-23.md` |
| `D-BASE-P10` audio redundancy (2 copies, offset 4) | **ADOPTED by the user** — warm interleaved: audio loss −96.4 / −98.2 %, +1.6 Mbps; pre-registered reading failed one clause on the favourable side (video FEC recoveries below the A range) | `D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md` |
| `D-BASE-T3` where the warm-state audio loss happens | **AIR** (pre-registered) — host sent every packet (0 send errors, 0 `SndbufErrors`), onn socket/UDP stack 0 drops, client lost 649 after the step; no code changed | `D_BASE_T3_AUDIO_LOSS_LOCATION_2026-09-23.md` |
| `D-BASE-T2` Part 1 — streaming-time audio loss | **REPRODUCED, resets with 30 min idle; reading MIXED, not located** — step at ~7 min from cold, all temperatures co-move, radio and video loss flat; thresholds proposed only | `D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md` |
| `D-BASE-T2` Part 0 — 12/17 as profile default | **ADOPTED by the user** (listen: "No issues from playing for a minute or two", user-stated); measured cost +33.5-37.9 ms; `audio_cushion` 12/17 `profile`, no env | `decisions/D-BASE-P9_AUDIO_CUSHION.md` |
| `D-BASE-P9a` 12/17 vs 3/8 interleaved (A3/B2/A4/B3) | **3/8 KEPT, adoption open (user)** — 12/17 passes starvation (-98-99.5 %), residence (+33.5-37.9 ms) and the underrun band (4-20) in both B arms; fails only the hole clause as coded (B3 vs A4, whose own spread is +28 %). Audio loss time-driven | `D_BASE_P9A_CUSHION_INTERLEAVED_2026-09-23.md` |
| `D-BASE-P9` audio cushion as a profile setting (3/8 vs 12/17 vs 12/24) | **FALSIFIED by the pre-registered reading** (underruns 20 → 25) — starvation 42.4 → 0.8/min at +36.0 ms for 12/17; default reverted to 3/8, setting installed | `D_BASE_P9_AUDIO_CUSHION_2026-09-23.md` |
| `H3` companion autostart | DESIGN RECORDED; **installed by the user 2026-09-23** (user-stated: verified across a reboot) | `H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md` |
| `D-BASE-P8` audio arrival-hole origin | CHARACTERIZED — not the heartbeat, not the adb sampler; the path's. Diagnostic build v2 installed | `D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md` |
| `P7` audio heartbeat counters | RUNTIME VALIDATED (instrument) / **CHARACTERIZED** (the counter) | `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md` |
| `S3` three hours on the adopted cap | **SOAK VALIDATED** | `D_BASE_S3_CAP_SOAK_2026-09-22.md` |
| `P6a` the 90 KB cap as profile default | **RUNTIME VALIDATED** | `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md` |
| `P6` frame-tail control — the intervention | **CAUSE ESTABLISHED** by intervention | `D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md` |
| `P5` which queue drops the burst | MEASURED — the onn's receive path **excluded** | `D_BASE_P5_WHICH_QUEUE_2026-09-21.md` |
| `O1` the Opal's read-only view of the air | MEASURED — the air and the Opal **excluded** | `O1_OPAL_AIR_VIEW_2026-09-21.md` |
| `S2` three-hour session (PC path) | RUNTIME VALIDATED; **`C5` FALSIFIED** | `D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md` |
| `S1` overnight soak, four sessions | RUNTIME VALIDATED — no degradation with elapsed time | `D_BASE_S1_OVERNIGHT_SOAK_2026-09-21.md` |
| `T1` thermal telemetry, both ends | RUNTIME VALIDATED; the onn reports **status only** | `D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md` |
| `C5a` IDR rejection count | **FALSIFIED** | `C5A_IDR_REJECTION_COUNT_2026-09-21.md` |
| `B2` host moved onto the production path | MEASURED — the Windows PC **neither implicated nor exonerated** | `B2_HOST_ON_OPAL_2026-09-21.md` |
| `P4` air telemetry from the onn | MEASURED — **no retry/airtime counter exists on this device** | `D_BASE_P4_AIR_TELEMETRY_2026-09-21.md` |
| `P3` sender pacing at 150-400 µs | **NOT ESTABLISHED** — insufficient at the 8 ms budget, not ineffective | `D_BASE_P3_SENDER_PACING_2026-09-21.md` |
| `R5` heartbeat loss counters (schema v2) | RUNTIME VALIDATED — exact between any two heartbeats | `D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md` |
| `P2b` starvation/underrun separation | RUNTIME VALIDATED — promotes `P2a` | `D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md` |
| `P2a` audio startup hold | **DEVELOPMENT-ONLY**, not reverted (next section) | `D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md` |
| `P2` audio underrun burst | CHARACTERIZED — 98.7 % in the first 3 s; read the total, not a rate | `D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md` |
| `P1` stale-output threshold at 60/90/120/200 ms | MEASURED — **nothing changed**, the default stays 60 | `D_BASE_P1_STALE_THRESHOLD_2026-09-20.md` |
| `R4` terminal-stall report fields | RUNTIME VALIDATED | `D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md` |
| `R3a` restart fallback + trigger freshness | RUNTIME VALIDATED — for real loss too since `R3d` (the five nftables runs) | `D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md` |
| `R3b` nftables link drop, real loss | **N05 / N3 / N15 / N15b / N150 all PASS** (N15b and N05 by hand, `R3d`); **E30 PASS** — the set is complete | `D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`, `D_BASE_R3D_HAND_RUNS_2026-09-22.md` |
| `END_MS` graceful end after link loss | **RUNTIME VALIDATED** (`R3d` E30: `PAUSED_SAVED` → `ENDED` 1,801.4 s against 1,800 ± 5; clean RetroArch shutdown; prompt then Discard before the next launch; the recovery file's SHA-256 not captured — recording gap) | `D_BASE_R3D_HAND_RUNS_2026-09-22.md` |
| `R3` link-drop self-recovery | RUNTIME VALIDATED **for the substitute fault**; **RUNTIME VALIDATED for real loss** since `R3d` (2026-09-23: N05, N3, N15, N15b, N150 all PASS) | `D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md` |
| `R2` terminal-stall visibility | RUNTIME VALIDATED | `D_BASE_R2_STALL_VISIBILITY_2026-09-20.md` |
| `R1` resync jumps counted in `lost_packets` | RUNTIME VALIDATED | `D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md` |
| Group A host-side diagnostic audit | **A1 and A3 FALSIFIED on the wire** | `GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md` |
| `C3.L2c` distribution re-score | **FALSIFIED**; the user kept the build | `C3_L2C_DISTRIBUTION_2026-09-20.md` |
| the baseline itself | **NOT HEALTHY** — the target table that opened `D-BASE` | `BASELINE_STREAM_HEALTH_2026-09-20.md` |

**Not run, and why:** `B1`/`B3`; `END_MS`. Superseded 2026-09-22 —
`D-BASE-R3b` ran by hand (the classifier still refuses `nft`, so the user
drove `r3b_run.sh`): **N3, N15 and N150 all PASS**, and `GIVE_UP_MS` with its
recovery save is now exercised. **N05, N15b and E30 were not run**, so `R3` +
`R3a` do not reach RUNTIME VALIDATED. Two post-run defects are open
(`R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`).
**Superseded again 2026-09-23 (Cowork verification note):** N15b and E30 ran
by hand on 2026-09-22 and N05 on 2026-09-23 (`D_BASE_R3D_HAND_RUNS_2026-09-22.md`);
all PASS, so `R3` + `R3a` are RUNTIME VALIDATED for real loss and `END_MS`
is RUNTIME VALIDATED — the table rows above are authoritative, this
paragraph is history. Both post-run defects are closed by `R3c2`.

## 2026-09-21 — `D-BASE-P2a` audio startup hold: DEVELOPMENT, not reverted

The audio underrun burst is removed: `audio.underruns` per session
**0 / 6 / 21 / 20 / 3, median 6**, against a pre-fix median of **207**, with
0-3 in the first three seconds against ~204. `first_write_elapsed_ms` moved
**7 ms** at the median, so the fix delays the AudioTrack's start and not
the audio. Six of eight accepting checks pass.

**It is not RUNTIME VALIDATED.** Two checks miss: rendered fps 59.38
against a >= 59.4 bar — which the control also missed, at 59.16, so video
was not degraded — and `prolonged_starvation_events` 138 → 151, monotonic
in run order and not tracking link quality, which was unresolved.

**Resolved 2026-09-21 by `D-BASE-P2b`, and `D-BASE-P2a` is now RUNTIME
VALIDATED.** Ten sessions, five matched pairs, strictly alternating against
a build with `STARTUP_REAL_PCM_TIMEOUT_MS` compiled to 0. The hold-off arm
measures starvation **125-157, median 151** — the same band — so the rise
is not the fix; pooled Spearman against run index is **-0.036**, so it is
not drift either; the sign test puts hold-on above hold-off in **3 of 5**
pairs with the two largest deltas opposed. `avg_queue_residence_ms` is
27.70 off against 27.62 on, so the shifted-queue mechanism P2a proposed is
absent. On this link both arms clear the fps bar (median **59.53** off,
**59.56** on). The underrun result replicated: median **276** off against
**19** on.

Records: `D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md`,
`D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`.

## D-BASE-P6a — the 90 KB frame cap as the profile default (2026-09-22)

**RUNTIME VALIDATED.** One 20-minute attract-mode session with **no
`PRIVYHUB_ENC_*` variable set** (`env | grep PRIVYHUB_ENC` printed
nothing), after moving the cap from an environment override into
`NativeStreamProfile.max_frame_size_bytes`.

All ten pre-registered gates passed: frames >= 80 packets **0**; max frame
**89,874 bytes** (<= 90,000); video `lost_packets` **249** (bound 600);
the >= 80-packet bucket **absent** from the conditional-loss table;
achieved bitrate **6,929.6 kbps** (6,900-7,050); rendered fps **59.90**
(>= 59.8); sequence resyncs **0**; onn socket drops **0**; relay send
errors **0**; encoder CPU median **26.6 %** (26-28).

Confirmed before the hold, not after: the argv carried
`-max_frame_size 90000`, `encoder_overrides.any_override` was **false**,
`default_max_frame_size_bytes` **90000**, `max_frame_size_source`
**`profile`**, and the launch banner in the host log carried the flag.

One 60 s check with **`PRIVYHUB_ENC_MAX_FRAME_SIZE=0`** then proved the
uncapped path still runs: the flag was **absent** from the argv and a
**90,438-byte** frame appeared — above the cap, so the cap was genuinely
gone. The no-variable environment was restored and the companion left on
the profile default.

**The perceptual half is the user's, not an instrument's**: on 2026-09-22
they played the capped arm for about a minute and reported no stutters and
that they "could barely tell it was over the LAN." Recorded as a
user-stated result and not upgraded.

Records: `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`,
`D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`;
`patches/D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT.md`;
`decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

## D-BASE-S3 — three hours on the adopted cap (2026-09-22)

**SOAK VALIDATED.** 180 minutes, attract mode, zero input, no
`PRIVYHUB_ENC_*` set. **Loss 977 over three hours = 5.4/min** — lower than
any 20-minute capped session (15.4 / 20.3 / 12.4) and ~25x below uncapped.
**0 sequence resyncs, 0 SSRC changes, 0 onn socket drops**, fps **59.96**,
bitrate 6,928.7 kbps, max forward gap 27 packets. Hourly 380 / 340 / 253
(1.50x, under the 2.0 drift flag). Thermals plateau as `T1` found.

**Both bounded logs rotated twice with zero lost rows** — the frame-size
series has **0 discontinuities across 10,801 seconds** and the heartbeat
slice holds 5,382 lines at 2,001-2,031 ms. First multi-hour test of the
`P6` frame-size log.

**The residual tracks nothing**: every Spearman under **0.08** over 1,080
ten-second and 180 per-minute windows, and the bucketed loss table is flat
(0.80 / 1.05 / 0.85 per window). **The loss column is closed at this
level.**

**One finding, reported first as the task required:** two frames in 180
minutes exceeded the cap by **11 and 9 bytes** (90,011 and 90,009). The
driver's `max_frame_size` is a **target, not a hard ceiling** — `P6`'s
60 KB arm already showed 60,092 — and at ~76 packets an 11-byte overshoot
cannot reintroduce the >= 80-packet population. Max packets per frame was
**77**, with zero frames at 80+ in any minute. Future checks should allow
a small tolerance rather than test `<= 90000` exactly.

**`S2`'s memory finding does not fully reproduce.** RetroArch grew
**+140.2 MB** over three hours of which **+34.3 MB anonymous**, against
`S2`'s +119.9 MB with only +6.2 MB anonymous, and the anonymous part was
still rising at the end. Majority file-backed, so "warm-up, not a leak"
survives in its main claim, but it is **not** the clean result `S2`
recorded and should not be cited as one.

Record: `D_BASE_S3_CAP_SOAK_2026-09-22.md`. No code change.

## D-BASE-P7 — the audio counters in the heartbeat (2026-09-22)

**Diagnostic build, RUNTIME CONFIRMED in one session.** APK
`6d25dee0…be96`, hash-verified against `pm path` before the session
counted. Ten audio fields ride the 2 s heartbeat (schema
**`…_heartbeat_v3`**) from the same `audioReceiver.snapshot()` the report
reads, plus a new per-tick **maximum audio inter-arrival gap** taken as one
`max()` on the receive thread. **The starvation counter's semantics are
unchanged.** 597 heartbeats, all ten fields on all, no measurable cost
(fps 59.94, `spike_20_ms` 25.6/min).

**The result: `prolonged_starvation_events` is an arrival-gap counter.**
One increment per hole in the audio arrival stream longer than ~15 ms,
latched so it counts **episodes, not polls**. Rho **+0.684** against the
gap over 596 ticks, **+0.020** against audio loss, and the packet deficit
averages **+0.54 of ~400** — **jitter, not loss**.

**One process finding worth carrying:** the first build sent all ten
fields and the log recorded **none**, because
`plugins/games.py`'s `native-stream-heartbeat` handler carries an
**explicit key whitelist** and silently drops anything not on it. Adding
fields to `native_stream_heartbeat.py` alone is not enough. That session
was abandoned and re-run after the fix.

Record: `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`; patch
`patches/D-BASE-P7_AUDIO_HEARTBEAT_COUNTERS.md`.

## Phase C — `C3.L3a` gameplay acceptance probe (2026-09-24)

| Item | Status | Key runtime evidence |
| --- | --- | --- |
| `C3-L3A-P2R1` probe: telemetry settling path and decoder clock alignment | **RUNTIME VALIDATED on one session** (smoke `20260924_000330`, adopted build) — settling measured 2 of 2 (two distinct fresh snapshots, cadence 2,007 ms, pre-transition snapshot excluded as designed); alignment 4 pairs, spread 0.152 s, 8 of 8 SSRC changes = expected (Phase A + parks + restore); preflight refused a run on a stale stream | `C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md` |
| `C3.L3a-S1` transition soak (60 scheduled transitions, attract mode, adopted build) | **CHARACTERIZED, cost PARTIAL (52 of 60 covered)** — gap median 186.5 ms (128-225; 2 of 60 one extra GOP, 405 / 423), codec ≤ 13 ms, `jump_packets` 0 ×60; settling 30 of 30 ≤ 6.0 s; lifecycle CLEAN; rendered fps −0.24 (ELEVATED by the band rule, above target); baseline in T NO on video loss (not at transitions; no-transition H2 also missed); headless probe path RUNTIME VALIDATED | `C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md` |
| `C3-L3A-R2B` companion decoder-report cap 32,000 → 48,000 + rejection WARNING line | **RUNTIME VALIDATED** (`C3-L3A-R3`, 2026-09-24) — rerun session 3's 24-change report stored (32,435 compact chars, 15,565 under 48,000; would have been refused at 32,000 by 435), POST 200, no WARNING, posted text == stored; off-session validation as before (`C3_L3A_R2B_REPORT_CAP_2026-09-24.md`). Transport ceiling ~41.5K decoded chars stands (client body-POST follow-up) | `C3_L3A_R3_SESSION3_2026-09-24.md` |
| `C3-L4-S1` shadow adaptive-bitrate controller (flag default off) | **RUNTIME VALIDATED — SHADOW SILENT** — 21/21 unit tests; flag off leaves `native-stream-status` unchanged but `adaptive_bitrate: mode off`; four healthy holds (cold 20, warm 20/60/20 min) in shadow: 0 FALLBACK / 0 ROUTINE / 0 up over 3,598 reports, 0 stale, `acted` false; flag unset and confirmed absent. Live use NOT authorized (gate + fault-injection night) | `C3_L4_S1_SHADOW_CONTROLLER_2026-09-24.md` |
| `C4-M1` FEC comparison arm `xor8_2` (8+2, override only) | **RUNTIME VALIDATED as an arm; gain NOT SHOWN** — golden (unset relay byte-identical), codec 9/9 + 6/6, arm APK installed for the night; smokes PASS; 3 B/A pairs: recovered 2-4×, unrecoverable groups halved, post-FEC lower in 1 of 3, A median 69 % of B (rule ≤ 60 %); cost rows within noise; adopted APK reinstalled and confirmed; nothing adopted | `C4_M1_FEC_ARM_2026-09-25.md` |
| `C3-F1` recovery restart at any ladder level | **RUNTIME VALIDATED — WORKING** — 8/8 unit tests; 4 sessions: 7000 (continuity cycle, unchanged) and 6000/5500/5000 (level-preserving restart): HTTP 200, level kept, 1 ssrc_change each, no full start, gap 132-197 ms; the loss-triggered state machine not re-run (needs nft) | `C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md` |
| `CL-B1` decoder report as a POST body (companion both forms; client body) | **RUNTIME VALIDATED on the arm APK; not adopted** — companion 4/4 tests (both forms identical, cap 128,000, 414 path sends 414); Kotlin 4/4; body form stored on arm APK `71d8c3d7…` (29,834 chars, 0 WARNING), target form stored on the adopted APK (0 WARNING); key sets identical to R3's; adopted APK reinstalled | `CL_B1_DECODER_REPORT_BODY_2026-09-25.md` |
| `C3.L3a` gate (perceptibility of repeated transitions) | **ANSWERED 2026-09-28 by the user's reading** — four pre-registered sessions pooled, 0 skipped (the bar reached); W 5.0: jump 6/20 (6 marks vs 3.21 chance), ramp 15/20 (29 vs 8.52), decoys 4/40 (4 vs 5.13) and 13/40 (14 vs 16.99); **`C3.L4` AUTHORIZED, single transition per event; live build pending** (ramps excluded; `nft` night first) | `C3_L3A_R4_SESSION4_2026-09-28.md`; `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` |
| `C5-M1` 1080p60 candidate profile + `PRIVYHUB_NATIVE_PROFILE_ID` (override only) | **RUNTIME VALIDATED as a selector; 1080p60 NOT CAPABLE (stream)** — golden (unset argv byte-identical), 8/8 tests; smokes PLAYING both arms (candidate 58.87 fps, decoded buffers 1920x1080 on the adopted APK); 6 interleaved holds: A missed spikes 517-529/min and post-FEC loss 123-181/min (A1/A3 also gap 407/266 ms), B1/B3 met every row, B2 missed loss 11.25 and gap 522; selector unset and absent, adopted APK confirmed; nothing adopted | `C5_M1_1080P60_PROFILE_2026-09-28.md` |
| `C5-M2` three 1080p60 follow-up arms (selector only) | **SELECTOR VALIDATED; the outcome INCONCLUSIVE (link) twice** — golden unset byte-identical, 11/11 tests; every arm reached PLAYING with 1920x1080 decoded buffers (no client change); screening night 1 3/4 and the re-run 4/4 adopted B holds missed the baseline on loss (12.7-47.2/min), so no outcome and the confirmation night NOT RUN; reported: no arm met the targets (spikes 313-882/min, loss 35-519/min); the 90 KB cap removed the >= 80-packet frames but bound 13-57 s/min; selector unset and absent, adopted APK confirmed | `C5_M2_1080P60_FOLLOWUP_2026-09-29.md` |
| `C5-M3` three low rungs for Phase G (selector only) + offline quality tool | **RUNTIME VALIDATED as selector profiles; transport screened** — golden unset byte-identical, 14/14 tests; 540p decoded at 960x540 on the onn, no client change; offline content SSIM 7000 0.9939 ... 4000 0.9903, 3000 0.9879, 540p/3500 0.9871, no 4 Hz IDR pulse; night 1 INCONCLUSIVE (link, 3/4 B missed), the re-run conclusive (1/4): 720p/4000 PASSES transport (2.24/min, 130 ms; also met every row on night 1), 720p/3000 does not (39.9/min), 540p/3500 does not (10.9/min, narrowly); measured wire 5.02 / 3.84 / 4.42 Mbit/s vs 8.60 at 7000; nothing on the live ladder; selector unset and absent, adopted APK confirmed | `C5_M3_LOW_RUNG_SCREENING_2026-09-29.md` |
| `C3-L3A-R2B` cap and the `CL-B1` companion route, on the adopted APK (session 4) | **RUNTIME VALIDATED again** (2026-09-28) — 24-change report (24 = 20 + 3 + 1) stored through the target form by the adopted APK `f31b1c18…8ae7` on the companion carrying `CL-B1`: 32,689 compact chars, POST 200, 0 WARNING, posted == stored; alignment spread 0.408 s; settling 10/10 (1.0-4.0 s); lifecycle 0/0/0 | `C3_L3A_R4_SESSION4_2026-09-28.md` |
| `C3-L4-L1` live adaptive-bitrate controller (`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, default off; disable route; test-only inject hook) | **RUNTIME VALIDATED — decrease path WIRED on injection; SILENT on a clean link; increase path NOT RUN (rule unreachable)** — 43/43 live + 21/21 shadow (unchanged) tests; parity with the shadow night 0 actions; loss replays max 1 transition / 10 min, never rate-limited; flag-off smoke unchanged; Session A 30 min live: 0 transitions / 898 reports, every close-out row met; Session B: one injected FALLBACK → one transition 7000→5000 (1,225 ms actuation, 171 ms gap), blackout 3, second injection refused `hold_down`, lifecycle clean, reset to 7000 at session end; the 90-consecutive-clean increase rule never reached (max 21 / 32) → PARTIAL (B6); flags unset and confirmed absent. Real loss NOT yet (the user's `nft` night) | `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` |
| `C3-L4-L2` live increase rule (the user's blend) + per-report sample rows + `tools/c3_l4_nft_night.py` | **RUNTIME VALIDATED — the climb WIRED on injection; Session B2 PARTIAL (W4) on the close-out loss row only** — 54/54 live + 21/21 shadow tests; parity 0 actions; loss replays with increases, max 3 transitions / 10 min, never rate-limited; B2: injected FALLBACK 7000→5000 (175 ms gap), 2nd injection refused hold_down, then INCREASE 5000→5500→6000→7000 on windows 90/85, 90/85, 90/86 (117, 120, 93 reports after the previous change; gaps 221/178/211 ms), 7000 held 14 min, 4 SSRC changes, 0 packets lost at the transitions; post-FEC loss 14.60/min from a 160-packet resync 88 s after the last transition and a 94-packet burst at 7000 (5.0/min without them); harness dry run from preflight to teardown; flags unset and absent. Real loss NOT yet (the user's `nft` night) | `C3_L4_L2_INCREASE_RULE_2026-09-29.md` |
| `C3-L4-N1` live capacity trigger + recovery-escalation backstop (the user's rules, 2026-09-29) + `--only` | **RUNTIME VALIDATED on a clean link — SILENT; the triggers shown on night 1's recorded samples, not yet on a live fault** — nft night 1 (the user's, before the rules) scored NOT "WORKS UNDER LOSS": no decrease under a cap (F1a), 16 recovery restarts under the caps; 85/85 live + 21/21 shadow + 23/23 harness tests, mutations caught; parity 0 actions; night 1 replayed exact: capacity FALLBACK +13.6/+16.7/+19.7 s after each cap, none in F2 or baselines; 148 heartbeat series + every live sample row: 0 new-rule decisions and 0 raw capacity windows on a clean link; 43 restart pairs, all in recorded faults (stop rule PASS); 30-min live hold: 0 transitions / 901 reports, every close-out row met (59.94 fps, 7.78 lost/min, gap 182 ms); fake-sudo `--only F1,F3` FULL and ABORT PASS; flags unset and absent. Real loss with the rules NOT yet (the user's nft night 2) | `C3_L4_NFT_NIGHT1_2026-09-29.md`; `C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md` |
| `C3-L4-N2` live `capacity_mild` (the user's "Go", 2026-09-29) + status-level fix + night 3 default | **RUNTIME VALIDATED on a clean link — the controller silent; the rule shown on night 2's recorded samples, not yet on a live fault** — nft night 2 (the user's, with N1's rules) scored WORKS UNDER LOSS (F1, F3): capacity at +13.9/+16.7 s, the climb to 6000, recovery restart at 5000 on real loss, but 6000 under the cap degraded 3 min 56 s below every bar; 102/102 live + 21/21 shadow + 23/23 harness tests, mutations caught; night 2 replayed as recorded, then capacity_mild 6000->5500 at 119 s into 6000 (bar at 46 s, reversal hold-down); night 1: strict first; 0 capacity_mild firings on any adopted clean-link series (stop rule PASS; 4 guard-refused decisions on the non-adopted 1080p candidate at session start); 30-min live hold: 0 transitions, 0 mild windows, close-out loss 33.99/min MISSED (isolated link bursts; onn link rate 195 vs 260 Mbit/s); fake-sudo --only F1 PASS; flags unset and absent. Real loss with capacity_mild NOT yet (the user's nft night 3) | `C3_L4_NFT_NIGHT2_2026-09-29.md`; `C3_L4_N2_MILD_CAPACITY_2026-09-29.md` |
| `C3.L4` live adaptive bitrate — CLOSED (nft night 3, 2026-09-30) | **VALIDATED UNDER REAL LOSS on three nft nights; live behind its flag, off by default** — night 3 (the user's, --only F1) WORKS UNDER LOSS on the pre-registered HOLD branch: capacity 7000->5000 at +15.5 s; INCREASE to 5500 (111 reports) and 6000 (93); capacity_mild met at 43 s, refused hold_down twice, 6000->5500 at 121.3 s (61 reports); the next increase HOLD oscillation at 5500 (496 s after the first change); rate_limited never, 0 escalations, 0 recovery cycles; BACK -> 7000 and the status reads 7000 (the N2 fix); teardown clean. Night 1 NOT, night 2 WORKS UNDER LOSS. The controller as built authorized; adoption (live on by default) the user's call | `C3_L4_NFT_NIGHT3_2026-09-30.md`; `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` |
| `C3-L4-D1` live adaptive bitrate ON BY DEFAULT (unit drop-in `privyhub-companion.service.d/adaptive.conf`, the user's authorization 2026-09-30) | **IN FORCE since 2026-10-01 13:07Z; RUNTIME VALIDATED on a clean link** — environ exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, manager none, status live / configured live / acts true, any_override false, unit file and shadow unchanged; 30-min hold on the default SILENT (0 transitions / refused / HOLD over 901 reports; client rows met; loss 7.59/min, max gap 447 ms); injection session: one FALLBACK 7000→5000 acted, client ssrc_changes 1, level reset at BACK, inject flag gone, route 403 — NOT PASS AS PRE-REGISTERED (I1's "ssrc_change row" is never emitted for an own transition; I3's stream read preceded the client's stop); tools/ preflights accept the one name (32/32, fake-sudo FULL + ABORT PASS) | `C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`; `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md` |
| `LINK-L1` the adopted 720p's loss row over one day (adaptive off) | **MIXED** (pre-registered) — 3 of 6 holds meet loss < 10/min (37.27 / 4.25 / 15.19 / 3.16 / 7.54 / 16.78, 12:40 → 08:41 EDT); history 16/36 since D-BASE; air as O1 (ch 36 / 80 MHz, idle 3.3 %, noise −89/−90; 3-4 strong BSSIDs in the 80 MHz block, 0 on 36) | `LINK_L1_LOSS_ROW_2026-10-01.md` |
| `C5-M4` Part 1 the PS1 source at native 1080p (measurement-only game override + options for Tekken 3; nothing adopted) | **MEASURED; nothing adopted** — window 1920x1080 by RetroArch fullscreen (argv unchanged); 1x/2x/4x HOLD 60 (pre-registered, R1 RetroArch frame counter + R2 capture fps; R3 not evaluable as worded) with no stream, the 7000 stream and the c3 arm; 8x misses R1 by one interval; candidate 4x (GPU 21 % vs 15 % with the stream); offline 3D content SSIM T 0.838 / S720 0.873 / S1080 c3 0.902 (deterministic replay, repeat control bit-identical); proposal written, not applied; launch config and core options byte-identical, selector absent, live default intact, APK confirmed | `C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` |
| `C5-M4A` the PS1 source at 4x / 1920x1080 window (core override + internal_resolution 4x in the base and six per-title .opt) | **ADOPTED 2026-10-01; RUNTIME VALIDATED** (pre-registered V1-V6) — exactly eight files changed; Tekken 3 and Crash Bash (multitap) at 1920x1080 / 4096² through the companion, the multitap write keeps the line; SNES 879x672 and bsnes.opt unchanged; D7 P1 8/9 (discovery: client start-up 0.2 s past the row's window), retry P2 9/9; 20-min adopted 7000 hold met every row (RetroArch 59.999, capture 60, client 59.94 fps, 27 spikes/min, stale 0.25, underruns 0.70/min; loss 4.12/min, gap 141 ms reported; 0 transitions); APK and live default unchanged | `C5_M4A_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`; `decisions/C5-M4_PS1_4X_SOURCE_ADOPTION_2026-10-01.md` |
| `LINK-L2` the loss row on the 40 MHz link over one day (adaptive shadow per session, 4x PS1 source) | **TIME OF DAY as scored, on the boundary** (pre-registered, LINK-L1's rule verbatim) — 2 of 6 meet loss < 10/min (20.80 / 1.64 / 9.47 / 12.84 / 13.21 / 11.49, 20:41 → 16:41 EDT); misses span 08:41-20:41 = 12.00 h at the scorer's minute resolution (12 h 0 min 7 s with seconds → MIXED); shadow confirmed and 0 acted rows on all six; max gap ≤ 100 on none; vs LINK-L1 (80 MHz) 2/6 vs 3/6, link rate halved; air ch 36 / 40 MHz, 0 neighbours on 36-40, 3-7 on 44-48 | `LINK_L2_LOSS_ROW_2026-10-02.md` |
| `C5-M5` the 1080p rung on the live ladder (12,600 kbps / 1920x1080) behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, off by default, NOT adopted | **RUNTIME VALIDATED behind its flag** (pre-registered) — R0: the mid-session size change needs no client change (R0a holds both ways: SurfaceFlinger 1920x1080 within 3 s, back within 5 s, one SSRC change each, no recovery; R0b NOT MET AS PRE-REGISTERED on two clauses: the resync count includes the SSRC changes, 1 stale drop; gaps 315/287 ms); tests 119/119, mutations 10/10, stop rule 0 differences over 377 series with the flag absent; S1 injection PASSES (356/314 ms); S3 2-h night WORKS AS A RUNG (one entry at 111.5 min, 8.5 min at 1080p, loss 2.0/min, 0 recovery); S2 30-min daytime ENTRY NOT REACHED (431 of 450) | `C5_M5_1080P_RUNG_2026-10-03.md`; `patches/C5-M5_1080P_RUNG.md` |
| `C5-M5B` the rung's entry from the data (415 of 450) and the PS1 look behind `PRIVYHUB_PS1_LOOK` (flags off by default, NOT adopted) | **RUNTIME VALIDATED behind its flags** (pre-registered, selection written before code) — entry E415 selected (8 of 10 real-input holds within 20 min); no loss leave met its conditions (the mild bar kept); tests 120/120 + look 13/13 + helper fake-run 8/8, mutations 14/14, stop rule 0 differences over 386 series; S1b injection PASSES (348/346 ms); S2b daytime NOT RUNG SHOWN (recovery paused the game at 4.4 min; the window met 415 at 15.1 min, the guards refused 448 entry decisions); S3b night DOES NOT WORK AS A RUNG by its rows. One entry by its own rule at 15.1 min (434 of 450, one short of the old 435), then 104.9 min at 1080p with no leave, no oscillation and 0 recovery (fps 60.18, stale 0.70/min, loss 2.82/min). The miss is the session's spikes: 317.9/min against < 200, the 1080p decode's known rate on the onn (C5-M4's 1080p holds 328-607/min). The entry switch's gap was 649 ms.; look: session options file loaded (smoke 2048²), adopted .opt/.cfg byte-identical over 14 sessions; `remaster` (bilinear + dither off + PGXP) HOLDS 60 at 720p; xBR / JINC2 miss; at the rung the full preset drops one frame in 4.8 min (not offered) | `C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`; `patches/C5-M5B_RUNG_ENTRY_AND_PS1_LOOK.md` |
| `C5-CLOSE` the rung window skips reports while recovery is not PLAYING (behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, NOT adopted); `tools/ps1_look.sh --attract` fixed; C5 and Phase C CLOSED 2026-10-05 on the user's decisions | **RUNTIME VALIDATED behind its flag** (the rule) and **RUNTIME VALIDATED** (the helper's `--attract`) — tests 126/126, mutations 22/22, stop rule 0 differences over 448 series (flag absent vs `5005615`); flag on vs C5-M5B: 5 series differ, all with not-PLAYING reports; S2b replayed: 451 entry decisions → 0, the window never qualifies during the pause; one short injection check (TOP=1080p + INJECT=1) PASSES (`window_rule` / `skipped_not_playing` in the status; teardown flags absent; APK confirmed); helper fake-run 11/11 and one real `4x --attract` dry pass to PLAYING (`NativeStreamActivity`) and back, ADOPTED STATE VERIFIED. The user's Look 3 was found at 720p (the injected entry refused by the 60-s age guard) | `C5_CLOSE_2026-10-05.md`; `patches/C5-CLOSE_RUNG_WINDOW_RULE_AND_ATTRACT_FIX.md` |
| `CL-B1` client APK (report as POST body, rings 256 + 1,024; C4-M1 v2 decoder inert) | **RUNTIME VALIDATED and ADOPTED 2026-09-30** (pre-registered rule, the user's authorization) — clean build reproducible `de072762…835e`, Kotlin 11/11, the tree unchanged since f01c3b2 (7 client files vs the old APK's 824c9d9, all CL-B1 / C4-M1); device hash on the first read; A3: body form 31,155 chars, 0 WARNING, capacity 1,280, key set identical; A4 20-min hold every client row met, FEC counters in the old APK's range; A5 paired with f31b1c18: loss 10.29 vs 11.81/min, gap 246 vs 205 ms (the link's rows, not gating); the new APK installed and confirmed at the end | `CL_B1_APK_ADOPTION_2026-09-30.md`; `decisions/CL-B1_APK_ADOPTION_2026-09-30.md` |

## Evidence integrity rule

Raw measurements outrank classifiers when they disagree.

A compile/build/install result is not runtime validation. A development patch
remains development-only until the requested runtime/E2E evidence passes.
