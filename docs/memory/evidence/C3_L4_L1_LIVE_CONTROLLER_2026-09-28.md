---
memory_schema: 1
as_of: 2026-09-28
baseline_commit: f01c3b2
status: C3-L4-L1 DONE — live mode BUILT (PRIVYHUB_ADAPTIVE_BITRATE_MODE=live, default off, shadow byte-identical); 43/43 live + 21/21 shadow tests; parity with the shadow night (0 actions); loss replays never rate-limited (max 1 transition per 10 min); Session A (30 min live, clean link) SILENT; Session B (injected FALLBACK) PARTIAL (B6) — one transition 7000 -> 5000 (171 ms gap), blackout 3, the second injection refused by the hold-down, lifecycle clean, but the increase path never fired: the pre-registered increase rule (90 consecutive clean reports) is not reachable in attract mode (longest clean run 21 / 32); flags unset and confirmed absent; nothing adopted, nothing committed
---

# C3-L4-L1 — the live controller, built and proven as far as a clean link allows

Task: `handoffs/C3-L4-L1_LIVE_CONTROLLER_TASK.md` (queue
`QUEUE_2026-09-28B.md` item 1, authorized by the user 2026-09-28, "Go").

**Authority.** `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`: one
`video_only_restart` per event, no ramp, the hold-downs as the minimum
spacing, the blackout kept.

**Documents.**

- Patch: `patches/C3-L4-L1_LIVE_CONTROLLER.md`.
- Design note, written before the build:
  `c3_l4_l1_2026-09-28/c3_l4_l1_design.txt`.
- Pre-registration, written before either session:
  `c3_l4_l1_2026-09-28/c3_l4_l1_preregistration.txt`.

**Classifications.**

- **Build: BUILT.** Every constraint is in code and in tests.
- **Offline gates: PASS.** Parity is zero actions; the rate limit never
  trips on a recorded night.
- **Session A: SILENT.**
- **Session B: PARTIAL (B6).** The decrease half is wired and behaved
  exactly as pre-registered. The increase path did not fire in 15
  minutes; the cause is a finding about the increase rule, not the
  wiring (§ The finding).

**Next.** The user's `nft` night, the hand-step list at the end. Before
it, the user's call on the increase rule.

## 1. Design, and the mapping table

The shadow policy (`adaptive_bitrate.py`, unchanged) names a TARGET for
FALLBACK (5000) and a STEP for ROUTINE (one rung) and for increases. Live
names every decrease's target from one table (`TARGET_KBPS`), so each
event is one restart:

| trigger | evidence (the shadow's, unchanged) | target | transitions |
| --- | --- | --- | --- |
| FALLBACK | 5 fresh reports: fps < 50 on 5/5 and (queue ≥ 2 on ≥ 3/5 or gap > 250 ms on ≥ 2/5) | **5000** | 1 |
| ROUTINE | fps < 57 on ≥ 4/5 and queue ≥ 1 on ≥ 3/5 | **6000** | 1 |
| INCREASE | below 7000: 90 consecutive clean reports (fps ≥ 59, queue 0, gap ≤ 150) after the blackout | one rung up | 1 per event |

**A decrease whose target is not below the level is refused** (`at_floor`
or `at_or_below_target`). So ROUTINE acts at most once.

**ROUTINE waits for FALLBACK.** While the newest report is itself under
50 fps, ROUTINE waits up to 4 reports. A queue-driven failure onset meets
ROUTINE one report before FALLBACK (the `S1` note). Without the wait it
would cost two restarts, 7000 → 6000 → 5000.

**Hold-downs**, in reports since the last transition, by its direction
(2 s per report):

| next | after a down | after an up |
| --- | --- | --- |
| FALLBACK | 30 (60 s) | 60 (120 s) |
| ROUTINE | 60 (120 s) | 60 (120 s) |
| INCREASE | 60 (120 s) | 30 (60 s) |

An increase also needs the 90 clean reports, so it comes at least 93
reports (186 s) after the previous transition. The hold-down is checked
before the floor.

**The other rules:**

- **Blackout**: 3 reports after any SSRC change, the controller's own or
  recovery's restart or full start.
- **Guards**, all required:
  - the stream is active;
  - the game is active and not paused;
  - recovery reads PLAYING;
  - the reference profile is in force at 7000;
  - `any_override` is false;
  - the actuator is bound;
  - the session is at least 60 s old.
- **Rate limit**: 4 per 10 minutes.
- **Oscillation / ACTUATOR_FAILED**: as the shadow.
- **Reset**: on every session end.

**Actuator: the same code path.** The controller calls
`NativeStreamManager.diagnostic_c3_validated_bitrate_transition(target)`,
the method the loopback `c3-validated-bitrate-transition` route calls. It
runs on one worker thread.

**Where recovery and the controller are serialized:**
`NativeStreamManager._lock`.

- The worker holds the lock, re-reads recovery's state under it, and
  restarts only if the state is PLAYING.
- Recovery's restart (`recovery_restart_encoder`, C3-F1) and its full
  start take the same lock, so the two never overlap.
- Recovery can still enter PAUSED_RECOVERING during a transition. Its
  first restart then comes ≥ 2 s later, at the new level
  (level-preserving).

**Kill switch.**

- The flag: unset it and restart the unit.
- `POST /plugins/games/adaptive-bitrate/disable` gives shadow for the
  rest of the session. It is idempotent, and there is no enable route.
- Test-only: `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` enables `.../inject`.
  It answers 403 unless the caller is loopback, the mode is live and the
  flag is set.

Full reasoning is in the design note. The architecture is in
`architecture/ADAPTIVE_BITRATE.md` §"C3.L4 live mode — as built".

## 2. Offline — all before any session

**Tests** (`unit_tests.txt`):

- `py_compile` is clean.
- The live suite passes **43 / 43**. There is at least one synthetic
  sequence per constraint:
  - one transition per event (FALLBACK, ROUTINE, the onset, the bounded
    deferral);
  - the blackout: own, recovery's, and an injection inside it;
  - each hold-down, with its seconds;
  - the increase cadence and the consecutive-clean rule;
  - the guards: `any_override`, recovery not idle, game inactive or
    paused, profile, stream, age < 60 s;
  - the rate limit: the 5th in a window is refused `RATE_LIMITED`, and
    the fastest legal return is 4 in 558 s, never limited;
  - oscillation and actuator failure;
  - the session reset and `level_sync`;
  - Session B's shape, offline;
  - the wrapper: the actuator is called under the stream lock; the
    recovery interlock re-read under the lock aborts; reports during
    actuation are dropped; `ACTUATOR_FAILED`; the disable route is
    idempotent and gives shadow; inject answers 403 unless flag, live and
    loopback; the routes; off and shadow never build the live controller.
- The shadow suite passes **21 / 21**, unchanged: `adaptive_bitrate.py`
  and its test file are byte-identical (`d66211b3…`, `62e1a011…`).

**Parity** (`c3_l4_l1_replays.txt` §1).

- *Why a rebuild*: the `C3-L4-S1` night did not store every report. Its
  log holds the 1,048 (state, reason) changes, each with its sample.
  Between two lines the (state, reason) did not change.
- *The rebuild*: each logged sample is held until the next line, which
  gives **3,594** reports: 598 / 601 / 1,796 / 599 per hold, against the
  night's counters of 602 / 600 / 1,796 / 600. The rebuild starts at each
  session's first logged line and rounds the gaps between lines to the
  2 s cadence.
- **Control**: the unchanged shadow engine, run on the rebuild,
  reproduces all 167 / 167 / 525 / 189 logged changes: MATCH in all four
  holds.
- **Shadow would-acts 0, live transitions 0, live refusals 0 → the same
  decisions, zero actions.**

**Recorded loss** (`c3_l4_l1_replays.txt` §2).

- *The data*: the `C4-D1` heartbeat set (82 files) and the three
  `CTRL-L1` holds, with rows de-duplicated. The companion's own logs are
  cut at `C4-D1`'s analysis time, because they have rotated since. That
  gives 88 sessions and 44,634 reports.
- *The substitutes*: per-report queue depth and output gap were not
  logged, so the replay uses stand-ins. **Proxy** is `C4-D1`'s own
  substitutions. **Bound** scores every report under 57 fps as queue 2,
  and every report under 50 fps as gap 300: the most the recorded fps
  could make the policy do.
- **The rate limit never trips.** In both variants there is **at most
  1 transition in any 10-minute window, and RATE_LIMITED 0**.

The would-fire list:

| session (start, UTC) | series | proxy | bound |
| --- | --- | --- | --- |
| 2026-09-21 03:10 | `d_base_s1` S1 | — | ROUTINE 7000→6000 at 1,624 s |
| 2026-09-21 03:43 | `d_base_s1` S2 | ROUTINE 7000→6000 at 341 s | ROUTINE at 339 s |
| 2026-09-21 04:16 | `d_base_s1` S3 | ROUTINE at 739 s | ROUTINE at 739 s |
| 2026-09-21 05:51 | `d_base_s2` L1 | ROUTINE at 134 s | ROUTINE at 134 s |
| 2026-09-21 08:24 | `d_base_s2` L1 (long) | ROUTINE at 9,588 s | ROUTINE at 9,588 s |
| 2026-09-21 23:26 | `o1` B | ROUTINE at 136 s | ROUTINE at 136 s |
| 2026-09-22 15:21 | `r3b` N150 (link drop) | FALLBACK 7000→5000 at 60 s | same |
| 2026-09-22 23:37 | `p8` v1 B (hit by the R3b E30 drop) | FALLBACK at 62 s | same |
| 2026-09-23 02:30 | `r3b` E30 (link drop) | FALLBACK at 62 s | same |

**How to read the list:**

- **Every ROUTINE row is a 2026-09-21 session.** That was before the
  adopted cap, cushion and redundancy.
- **Every FALLBACK row is a link drop.** It fires at 60-62 s because the
  age guard ends then. Live, recovery's guards (not PLAYING, game paused)
  block those.
- Outside the link drops, the longest run of reports under 50 fps is 3
  (FALLBACK needs 5).
- **No INCREASE fired in any series.** This was the first sign of the
  finding below, and was not recognized before the sessions.

**Flag-off smoke** (`smoke_flag_off.txt`), after a restart through the
unit with no `PRIVYHUB_*` set:

- `adaptive_bitrate` reads `{schema, mode: off, acted: false}`, exactly
  as before;
- disable answers 200 (not live, a no-op);
- inject answers 403;
- enable answers 404;
- GET on the new path answers 404.

## 3. Session A — silent live hold: **SILENT**

**Setup.**

- Run 21:58:33-22:28:33Z, 30 min of attract mode, zero input, the `T2`
  sampler at 10 s.
- The flag was `live`, the only `PRIVYHUB_*` in the manager and the
  environ. `adaptive_bitrate` read `live live` before the launch.
- At PLAYING: `any_override` **false**, the profile adopted (cap 90,000,
  cushion 12/17, redundancy 2/4, all `profile`), 7000 kbps.

**Numbers** (`c3_l4_l1_analysis.txt`):

| row | value | target |
| --- | --- | --- |
| spikes ≥ 20 ms /min | 32.70 | < 200 PASS |
| rendered fps | 59.91 | ≥ 59.5 PASS |
| stale drops /min | 0.56 | < 20 PASS |
| video loss /min post-FEC | 5.22 | < 10 PASS |
| audio underruns /min | 0.83 | < 5 PASS |
| max output gap | 130 ms | ≤ 250 (reported) |

**What the controller did.**

- The decoder session lasted 30.25 min, with **0 `ssrc_changes`**.
- The controller evaluated **898 reports**: **0 transitions, 0
  refusals**, 0 stale, `rate_limited` false.
- The decision log has 98 lines: 95 state changes (REFERENCE ↔
  PRESSURE, as fps crosses 57), 2 session resets and the start line.
- The status series (359 polls at 5 s) saw only (7000, 7000).
- The recovery log shows only `session_started` and `session_ended`.
- The onn ran at 58.0-72.7 °C.

→ **SILENT**: zero transitions, and every close-out row met.

## 4. Session B — injected trigger: **PARTIAL (B6)**

**Setup.**

- Live mode and `INJECT=1`. PLAYING at 22:30:14Z, `any_override`
  **false**, the profile adopted, 7000.
- The session ran until BACK at 22:48:18Z (18.21 min).

**The timeline** (`runs/decision_log_B.jsonl`, the `inject*_B.json`
files, `abr_series_B.jsonl` and `report_B.json`):

| UTC | event |
| --- | --- |
| 22:32:14.364 | injection 1 (120 s after PLAYING) → `transition` FALLBACK 7000 → 5000, `injected: true`, elapsed 126,073 ms |
| 22:32:15.589 | `transition_done`: actuation 1,225 ms (spawn 315.9 ms, first RTP resume 468.8 ms, RTP silence after spawn **152.9 ms**) |
| (client) | one `ssrc_change` at elapsed 126,934 ms; largest output gap in [ssrc, +1 s] **171 ms** (−15.5 vs the S1 median 186.5) |
| 22:32:16-22 | blackout: 3 reports suppressed, no decision row |
| 22:32:22.043 | state → RECOVERY_PROBATION (counting clean reports) |
| 22:32:44.483 | injection 2 (30 s later) → **`refused`, reason `hold_down`**, 15 reports left of 30; no transition, no SSRC change |
| 22:32:46 → 22:48:18 | at 5000, RECOVERY_PROBATION throughout; **no increase**; the clean counter's maximum was 32 |
| 22:48:21.305 | BACK → `session_ended_reset` (level 5000 → **7000**, transitions 1 → 0); recovery `session_ended` |

The pre-registered rows:

| row | result |
| --- | --- |
| B1: exactly one `ssrc_change` from injection 1 | **MET** (1) |
| B2: the level after = 5000 (FALLBACK → 5000) | **MET** |
| B3: the output gap, against 186.5 ms | **171 ms** (reported) |
| B4: the blackout observed | **MET** (`suppressed.blackout` 3; no decision row inside it) |
| B5: the second injection refused by the hold-down | **MET** |
| B6: the increase path back to 7000, one rung per event, ≥ 93 reports apart | **NOT MET**: no increase in 15.9 min at 5000 |
| B7: BACK → report stored, lifecycle clean, controller back at 7000 | **MET** (report stored; `session_started`/`session_ended` only; the reset put the controller to 7000; the level *before* BACK was 5000, because of B6) |

**The close-out rows over B** are reported only: spikes 41.57, fps 59.93,
stale 0.77, loss 9.33, underruns 2.25, max gap 235 ms. All five targets
pass. There was 1 SSRC change in B (4 were expected if WIRED). The onn
ran at 69.3-72.3 °C.

→ **PARTIAL (B6).** The decrease half is wired:

- one event, one transition, straight to the mapped target;
- the gap at the soak's cost;
- the blackout;
- the hold-down refusing a second trigger;
- a clean lifecycle and the reset.

The increase half did not run.

## 5. The finding — the increase rule is not reachable on a clean link

The increase rule is pre-registered in `C3-L4-S1` and kept unchanged
here: 90 **consecutive** reports with fps ≥ 59, queue 0 and gap ≤ 150.
In attract mode on the adopted build, runs of such reports do not last
anywhere near 90. The evidence is `increase_rule_check.txt`.

**The direct measure** is the controller's own clean counter, polled
every 5 s:

| session | polls | max | ≥ 30 | ≥ 60 | ≥ 90 |
| --- | --- | --- | --- | --- | --- |
| A, at 7000 | 359 | **21** | 0 | 0 | 0 |
| B, at 5000, after the blackout | 190 | **32** | 2 | 0 | 0 |

**The cause** shows in the S1 night's logged client samples. Of 1,045
samples outside a resync, 470 were under 59 fps alone, 60 had queue > 0,
and 15 had both. The client's 2 s `recent_fps` wanders 57-62 on a healthy
stream, and one report under 59 restarts the count.

**Alternatives**, measured by proxy from the heartbeats (the per-report
client values are not logged; the queue proxy is noisier than the
client's own). Longest run, 90 needed:

| definition of "clean" | A (at 7000) | B (at 5000) |
| --- | --- | --- |
| the rule (fps ≥ 59, queue 0, gap ≤ 150) | 8 | 8 |
| fps ≥ 59 alone | 51 | 62 |
| fps ≥ 57, queue ≤ 1, gap ≤ 150 (no ROUTINE-level sample) | **116** | **110** |
| fps ≥ 50, gap ≤ 250 (no FALLBACK-level sample) | 896 | 337 |

**Consequence as built.** A stream the controller steps down stays down
for the rest of the session, then resets to 7000 at the session end. That
is the safe side: it never climbs back into trouble. But it is not the
slow-up the design describes. The constraint forbids a ramp; it does not
forbid the return.

**Not changed.** It is a pre-registered constant, and the queue forbids
loosening a rule after seeing data. **The choice is the user's**:

- (a) "clean" = no ROUTINE-level sample (fps ≥ 57, queue ≤ 1, gap ≤
  150), 90 consecutive;
- (b) ≥ 85 of the last 90 reports clean by the current definition;
- (c) keep the rule; a stepped-down session stays down.

The proxies favour (a). Either change would be one constant or one
function in `LivePolicy`, plus its tests, and a repeat of Session B. The
shadow can keep its own.

**What else to carry forward:**

- **Log per-report samples in live.** The telemetry the controller
  decides on is not stored per report, which is why this took proxies to
  size. A per-report `sample` row (≈ 1 line / 2 s, rotated) would let
  the `nft` night be re-scored offline under any rule.
- **The controller log is still chatty.** In live it writes state
  changes only (`S1` finding 1): 95 lines in 30 min, REFERENCE ↔ PRESSURE
  as fps crosses 57. That is bounded by the rotation, but a state
  hysteresis would cut it.
- **The authorization's item 6** ("no live run before a fault-injection
  night"). This task's two clean-link sessions were ordered by the user's
  queue ("Go"). No live run has met real loss yet; that is the `nft`
  night.

## 6. Teardown (22:48:46-22:49:30Z)

- Both flags were unset in the user manager.
- The companion was restarted through its unit. MainPID 751040 owns 8765.
- `PRIVYHUB_*` reads **0** in the manager and **0** in the MainPID's
  environ. `PRIVYHUB_ADAPTIVE_BITRATE_*` reads **0**.
- `adaptive_bitrate` reads `{mode: off, acted: false}`.
- Inject answers **403**.
- Stream 7000; profile `native_game_720p60_reference`, cap 90,000,
  cushion 12/17, redundancy 2/4 (`profile`); `any_override` false.
- No game is active. The launcher shows no NOW PLAYING banner.
- The sampler has stopped.
- The APK was not touched: no install happened in this task. The
  installed APK's hash (`pm path` on the onn) was confirmed 22:55Z as the
  adopted `f31b1c18…8ae7`.

## 7. The `nft` night — the hand-step list for the user

The fault is the user's (`sudo nft`), in the `R3b` shape: host
**output** hook, video port only (`udp dport 48100`; audio 48101 and adb
untouched). Everything around it can be scripted when the user queues
it.

**The rows below assume the increase rule AS BUILT** (§5: a
stepped-down session stays down). Where the answer changes if the user
first adopts option (a) or (b), it is marked **[if (a)/(b)]**.

**Measured load** (`rung_load.txt`, Session B's host frame series;
estimated wire rate = payload + 40 B/packet + ~16 % FEC parity):

| rung | wire rate |
| --- | --- |
| 7000 | ≈ 1,083 kB/s (8.7 Mbit/s) |
| 5000 | ≈ 775 kB/s (6.2 Mbit/s) |
| 5500 (interpolated) | ≈ 850 kB/s |
| 6000 (interpolated) | ≈ 930 kB/s |

**Before.**

1. **Idle host.** No game. No `PRIVYHUB_*` in the manager. No
   `privyhub_fault` table (`sudo nft list tables`).
2. **Set the flag.**
   `systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`
   (never `INJECT`), then `systemctl --user restart privyhub-companion`.
   Confirm `adaptive_bitrate`: `mode live`, `level 7000`,
   `transitions_this_session 0`.
3. **Start the recorders.** The `T2` sampler, and the 5 s
   `native-stream-status` poller (as in `c3_l4_l1_run.sh`).
4. **Launch.** The attract-mode title, to PLAYING. Record
   `any_override` (must be false). Wait ≥ 120 s: the age guard is 60 s,
   and the rest is baseline.
5. **Calibrate the cap.** Add a counter-only rule:

   ```
   sudo nft add table inet privyhub_fault
   sudo nft add chain inet privyhub_fault flt '{ type filter hook output priority 0; }'
   sudo nft add rule inet privyhub_fault flt udp dport 48100 counter
   ```

   Read `sudo nft list table inet privyhub_fault` twice, 60 s apart. The
   byte delta / 60 is the real wire rate at 7000. Scale the table above
   by it.
   - **CAP** = the midpoint of the calibrated 5500 and 6000 rates, about
     890 kB/s if the estimate holds.

**Fault 1 — the capacity cap** (the controller's main case).

6. **Replace the counter with the cap.**
   `sudo nft flush chain inet privyhub_fault flt`, then
   `sudo nft add rule inet privyhub_fault flt udp dport 48100 limit rate over CAP kbytes/second burst 64 kbytes drop`.
   Note the time. Save `nft list table`.
   - **Expect**: within ~10-20 s, one `transition` FALLBACK 7000 → 5000,
     then `transition_done`, one `ssrc_change` and a 3-report blackout.
   - **If the cap only slows the stream** (fps 50-57 with a queue), expect
     one ROUTINE 7000 → 6000 instead. FALLBACK → 5000 follows ≥ 30 reports
     later if 6000 still fails.
   - **Record**: the time from the cap to the first transition, and the
     gap at the SSRC change (against 186.5 ms).
7. **Keep the cap for 12 minutes.**
   - **Expect, as built**: the stream stays at 5000 under the cap and
     meets the close-out rows. There is no further transition;
     `rate_limited` stays false.
   - **[if (a)/(b)]**:
     - ~186 s later, INCREASE 5000 → 5500, which fits under the cap;
     - ~186 s after that, INCREASE 5500 → 6000, which exceeds the cap;
     - after the 60-report reversal hold-down, FALLBACK 6000 → 5000;
     - the next increase would be the third direction change inside 10
       min, so it becomes a **`HOLD` (`oscillation`)** at 5000 for the
       session.

     Never two transitions closer than the hold-down table, never more
     than 4 in 10 min, never a ramp.
8. **Delete the table** (`sudo nft delete table inet privyhub_fault`) and
   note the time. Hold 5 minutes.
   - **Expect, as built**: the stream stays at 5000.
   - **[if (a)/(b)]**: one rung per ~186 s back to 7000, unless the
     `HOLD` was reached.
   - Then BACK. Expect a `session_ended_reset` to 7000. The next session
     starts at 7000.

**Fault 2 — random loss** (the controller must not chase it).

9. **Apply 2 % random loss.** New session, ≥ 120 s PLAYING. Make the
   table as in 5, then add
   `sudo nft add rule inet privyhub_fault flt udp dport 48100 numgen random mod 1000 < 20 drop`.
   Hold 10 minutes.
   - **Expect**: FEC recovers part of the loss. Loss alone is never
     evidence.
   - **Either** no transition, **or** at most one decrease (ROUTINE →
     6000, or FALLBACK → 5000), and then only `at_or_below_target` /
     `at_floor` / `hold_down` refusals. **No second decrease, and never a
     ramp.**
   - Then delete the table, hold 5 minutes, and BACK.

**Fault 3 — a link drop while off the reference** (recovery and the
controller together).

10. **Drop everything for 15 s at 5000.** New session. Bring the stream
    to 5000 with Fault 1's cap (step 6). Then flush the chain and add the
    `R3b` drop, `udp dport { 48100, 48101 } drop`, for **15 s**. Delete
    the table.
    - **Expect, from recovery**: `desync_pause`, then `encoder_restart`
      **at 5000** (C3-F1, level-preserving), then `resumed`.
    - **Expect, from the controller**: **no action while recovery is not
      PLAYING**. You will see either a `refused` row naming the guard
      `recovery_playing`, or nothing at all (the client's reports stop).
      Then `ssrc_change` (source `recovery_restart`) and a 3-report
      blackout.
    - **After**: the level is still 5000 (`level_sync` must not appear).
      BACK then resets to 7000.

**The kill switch.**

11. **Disable twice during a fault.** In any session above,
    `curl -X POST localhost:8765/plugins/games/adaptive-bitrate/disable`,
    two times.
    - **Expect**: `already_disabled` false, then true. The status reads
      `mode shadow`, `configured_mode live`, `acts false`.
    - Further decisions are logged as `would_act`, acted false. The
      stream stays where it is. The next session is live again.

**After.**

12. **Remove the fault.** Delete the table. Confirm no `privyhub_fault`
    in `sudo nft list tables`.
13. **Tear down.** Unset the flag and restart the unit. Confirm
    `PRIVYHUB_ADAPTIVE_BITRATE_*` is absent from the manager and the
    MainPID's environ, `adaptive_bitrate.mode` reads off, the stream is at
    7000, no game is active, and the banner is cleared.

**What is recorded, per session:**

- the decision-log slice;
- the status series;
- the decoder report: `ssrc_changes`, `stream_discontinuities`, and the
  gap at each change;
- heartbeats and the host frame series;
- the recovery-log lines;
- each `nft` table as applied, with its on and off times;
- `T2`;
- the redacted journal.

**Proposed pre-registration** (the user may amend it before the night):

- **WORKS UNDER LOSS** if all of these hold:
  - Fault 1 gives exactly one decrease per event, to the mapped target;
    then, as built, no further transition under the cap, or **[if
    (a)/(b)]** the increase / `HOLD` sequence of step 7; `rate_limited`
    is never true and there is no ramp;
  - Fault 2 gives at most one decrease;
  - Fault 3 gives no controller action while recovery is not PLAYING, and
    recovery restarts at the held level;
  - step 11 behaves as described.
- **Anything else** is recorded row by row.

## Files (`c3_l4_l1_2026-09-28/`)

- **Design and rules**: `c3_l4_l1_design.txt`,
  `c3_l4_l1_preregistration.txt`.
- **Code**:
  - copies of `adaptive_bitrate_live.py`, `test_adaptive_bitrate_live.py`
    and `c3_l4_l1_replay.py`;
  - `companion_patch.diff` (the three edited companion files);
  - `pre_patch_sha256.txt` and `post_patch_sha256.txt`.
- **Offline**: `unit_tests.txt`, `c3_l4_l1_replays.txt`,
  `smoke_flag_off.txt`.
- **Sessions**:
  - the harness: `c3_l4_l1_night.sh` (its log `c3_l4_l1_night.log`) and
    `c3_l4_l1_run.sh`;
  - the sampler: `t2_sample.py`, `t2_samples.jsonl`, `t2_sampler.log`.
- **Scoring**:
  - `c3_l4_l1_analyze.py`, `c3_l4_l1_analysis.txt`,
    `c3_l4_l1_summary.json`;
  - `increase_rule_check.txt` (the finding);
  - `rung_load.txt` (the `nft` cap).
- **`runs/`**, per session (A, B):
  - `decision_log_*` (the controller log's slice) and `abr_series_*`
    (status every 5 s);
  - `report_*`, `heartbeat_*`, `frames_*` and `alpha_*`;
  - `armcheck_*` (PLAYING), `status_end_*` (before BACK) and `status_*`
    (after);
  - `companion_*.log` (the redacted journal), `encoder_cmd_*` and
    `adb_during_hold_*`;
  - `inject1_B.json` and `inject2_B.json`;
  - `recovery_log.jsonl`, and `index.txt`.
- `sha256_manifest.txt`.

**Privacy check.** `h2_prep_redact.py --check` passes on every Markdown
and text record written. The code files, JSON status files and journals
match its IPv4 pattern only for non-identifying literals:

- the loopback address and the bind-all address;
- the RetroArch core's version string (four dotted numbers);
- an RFC 5737 documentation address in two route tests.

No device address, MAC, SSID, ADB endpoint, credential or device
identifier appears anywhere.
