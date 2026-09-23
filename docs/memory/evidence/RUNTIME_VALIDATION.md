---
memory_schema: 1
as_of: 2026-09-22
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

## Evidence integrity rule

Raw measurements outrank classifiers when they disagree.

A compile/build/install result is not runtime validation. A development patch
remains development-only until the requested runtime/E2E evidence passes.
