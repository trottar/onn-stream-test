---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
status: C3-L4-N1 DONE — night 1 scored NOT "WORKS UNDER LOSS" (F1a and the lifecycle row not held; F1b/F1d N/A; F3b NOT TESTED; own record C3_L4_NFT_NIGHT1_2026-09-29.md). The user's two rules (2026-09-29, "Yes, add both") BUILT in LIVE only — capacity (fps < 50 on 5/5 and lost >= 50 on >= 3/5 -> FALLBACK 5000) and recovery_escalation (two recovery encoder restarts at one level within 180 s -> one FALLBACK after PLAYING and the blackout; at_floor at 5000); recovery and the shadow unchanged. Tests 85/85 live, 21/21 shadow, 23/23 harness; mutations caught; one logging defect found by the replay and fixed. Replays: night 1's caps fire capacity at +13.6 / +16.7 / +19.7 s, nothing in F2 or any baseline; 0 new-rule decisions and 0 raw capacity windows on every clean-link series; all 43 restart pairs inside recorded faults -> the stop rule PASS. 30-min live hold SILENT (0 transitions, every close-out row met). Harness --only F1,F3 built; fake-sudo FULL and ABORT PASS. Night 2's pre-registration written (sha256 3cdcfa2e...); hand steps in section 5. Flags unset and absent; adopted profile and APK; nothing adopted; nothing committed
---

# C3-L4-N1 — the capacity trigger and the recovery-escalation backstop

Task: `handoffs/C3-L4-N1_NFT_NIGHT1_SCORE_AND_CAPACITY_TRIGGER_TASK.md`,
queue `QUEUE_2026-09-29B.md`, task 1 only. Code stopped after it. The
user runs `nft` night 2 next.

- §1, the scoring of night 1, is its own record:
  `C3_L4_NFT_NIGHT1_2026-09-29.md`.
- Patch: `patches/C3-L4-N1_CAPACITY_TRIGGER_AND_BACKSTOP.md`.
- Evidence: `c3_l4_n1_2026-09-29/` (manifest `sha256_manifest.txt`).
- The decision is appended to
  `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`.

**Classifications.**

- **The rules: BUILT** (live only; the shadow is byte-identical).
- **Tests: PASS.** 85/85 live, 21/21 shadow, 23/23 harness; mutations
  caught.
- **Replays: the stop rule PASSES.** Neither rule fires on any clean-link
  series. Night 1's faults fire the capacity trigger 13.6 / 16.7 / 19.7 s
  after the cap.
- **Silent hold: SILENT.** 30 min live on a clean link: 0 transitions, every
  close-out row met.
- **Harness `--only`: BUILT.** The fake-sudo `--only F1,F3` FULL and ABORT
  runs PASS.
- **Night 2's pre-registration: WRITTEN** (sha256 `3cdcfa2e…`).

## 1. Night 1

In brief (full record `C3_L4_NFT_NIGHT1_2026-09-29.md`): **NOT "WORKS
UNDER LOSS"**.

- **Not held:** F1a (no decrease under the cap) and the all-sessions
  lifecycle row (recovery cycles under the caps).
- **NOT APPLICABLE:** F1b and F1d. **NOT TESTED:** F3b.
- Everything else MET.

## 2. The two rules, as built (`companion/adaptive_bitrate_live.py`, `LivePolicy`)

The user's decision, 2026-09-29: **"Yes, add both"**.

### (a) Capacity trigger

- **Class** FALLBACK, **reason** `capacity`, **target** 5000.
- **The bar**: over the last 5 evaluated reports, **fps < 50 on all 5
  and `lost_packets_delta` ≥ 50 on ≥ 3 of 5**.
- **Where**: `LivePolicy._evidence()`, after the shadow's own evidence.
  - The queue/gap FALLBACK is tested first (`trigger: fps_queue_gap`),
    then capacity, then ROUTINE.
  - The decision is the existing `_decide("FALLBACK")`: hold-downs,
    `at_floor`, guards (recovery PLAYING included), the rate limit and
    the oscillation guard, all unchanged.
- **What counts**:
  - The window (`self.window`, 5) holds only evaluated reports.
  - Stale, non-distinct, blackout and resync (`waiting_for_idr`) reports
    return before it.
  - A missing delta (`None`) does not count toward the 3.
- **Constants**: `CAPACITY_FPS_BELOW 50.0`, `CAPACITY_LOSS_AT_LEAST 50`,
  `CAPACITY_LOSS_OF 3`.

**The counter.** `lost_packets_delta` is the companion's per-report delta
(`diagnostics/stream_telemetry.py`, `receiver.lost_packets_delta`, from
the client report's `delta.video.lost_packets`). It is the delta of the
client's `RtpH264Receiver.lostPackets`.

- **What it counts**: gaps in the RTP sequence of video packets in the
  ordered path. FEC-recovered packets re-enter that path (`fecRecovered`),
  so **it is post-FEC**.
- **It also counts resync jumps**: since A2.2 (2026-09-20) the jump of a
  forward sequence resync is added (`beginStreamResync`).
- **SSRC change: no inflation.** `beginStreamResync(jumpPackets = 0)`
  resets `lastSequence`, so the new stream's first packet is not a gap.
- **Sequence resync: one report inflated** by the jump (B2's resync was
  160 packets; F3's drop 12,554).
- **Is the 3-report blackout enough?**
  - It covers what a restart carries over: loss from the old stream in
    the first reports after an SSRC change.
  - It does not cover a client-side sequence resync with no SSRC change;
    nothing tells the controller of one.
  - Such a resync makes at most one report of the five count. The rule
    still needs fps < 50 on all five and two more reports at ≥ 50.
  - **Judged enough**, and borne out: every recorded clean-link series
    (§3) has zero 5-report windows at the bar, resyncs included.

### (b) Recovery-escalation backstop

- **Class** FALLBACK, **reason** `recovery_escalation`, **target** 5000.
- **Input**: `note_ssrc_change(source, clock_ms)`.
  - The games plugin calls `LiveController.note_recovery_restart()` once
    per recovery `encoder_restart`: `_recovery_restart_encoder` →
    `"recovery_restart"`; `_recovery_full_start_encoder` →
    `"recovery_full_start"`.
  - The call comes from recovery's monitor thread, in a `finally`, after
    the restart returned. The wrapper passes `time.monotonic()` in ms,
    the same clock the report path uses.
  - **A desync pause alone never reaches the controller.** Calls without
    a clock (the old signature) record no restart.
- **The level of a restart**: the controller's level for `restart`
  (C3-F1 is level-preserving, and the level cannot change during a
  restart, which holds the stream lock); 7000 for `full_start` (C1).
- **Arming**: two restarts at one level within 180 s (≤ 180,000 ms,
  inclusive) arm one escalation and write an `escalation_armed` row.
  While one is armed, further restarts do not arm another.
- **Firing**: at the first **evaluated** report with `recovery_playing`
  true.
  - "Evaluated" means after the 3-report blackout that every restart
    starts. By construction the blackout has passed.
  - The controller calls `_decide("FALLBACK")` once, with
    `trigger: recovery_escalation`.
  - At 5000 that is the existing `at_floor` refusal, logged.
  - A hold-down, a guard or the rate limit refuses it, logged.
  - It is **consumed whatever the outcome**, and the restart list
    clears, so a new escalation needs two new restarts.
  - **While recovery is not PLAYING it waits**; it is not spent on the
    guard.
- **Scope**: companion session. `end_session()` clears it; a client
  elapsed reset does not.
- **Constants**: `ESCALATION_RESTARTS 2`, `ESCALATION_WINDOW_MS 180000`.
- **Serialization**:
  - The controller only reads recovery: these calls, and
    `current_state()` for the guard.
  - Its own restart runs on its worker under `NativeStreamManager._lock`,
    the lock `recovery_restart_encoder` and the full start take. It
    re-reads recovery's state under that lock and aborts unless it reads
    PLAYING (L1, unchanged).
  - So a backstop FALLBACK cannot overlap a recovery restart. A recovery
    restart after it runs at 5000.
  - **Recovery is unchanged**: `link_drop_recovery.py` and `games.py`
    were not edited (sha256 before = after).

**Unchanged:** the shadow (`adaptive_bitrate.py`, sha256 `d66211b3…`), the
blend's increase rule, blackout 3, the hold-downs, the rate limit 4/10
min, the oscillation guard, the age and recovery guards, and the disable
route.

**Visible:** `policy.capacity_trigger`, `policy.recovery_escalation`
(`restarts_in_window`, `armed`), `trigger` on every decision row, reason
`capacity` / `recovery_escalation` on the transition, and
`escalation_armed` on every `sample` row.

## 3. Tests and replays — before any session

### Tests

**`tools/test_adaptive_bitrate_live.py`: 85/85** (`unit_tests.txt`). The
54 from L2 are unchanged, except that `telemetry()` gains `lost` with
default 0.

**`CapacityTrigger`** (14):

- It fires at exactly 5/5 fps < 50 with 3/5 loss ≥ 50: reason and trigger
  `capacity`, 7000 → 5000.
- Boundaries: 49.99/50 fires; fps 50.0 or loss 49 never does.
- It does not fire at 4/5 fps, at 2/5 loss, or on loss alone (fps 55
  with 400 lost; F2's shape).
- Stale and unavailable reports are skipped. A missing delta does not
  count, resync reports are not evidence, and it waits out the blackout.
- It is refused while recovery is not PLAYING.
- Refused `hold_down` 53 reports after an up, it fires at 60. At 5000 it
  is `at_floor`, logged once.
- RATE_LIMITED binds.
- The queue/gap FALLBACK keeps its own reason.
- The shadow does not act on the capacity shape.

**`RecoveryEscalation`** (14):

- It fires once after the second restart 10 s apart. The 3 blackout
  reports are silent; the 4th decides. Later climbs are only the blend's.
- 181 s apart does not arm; exactly 180 s arms.
- Restarts at different levels (7000, then 5000) do not arm.
- A full start counts at 7000.
- A note without a clock is not a restart.
- It waits while recovery is not PLAYING, with no refusal row, and fires
  once PLAYING.
- It is refused `hold_down` after an up and consumed, with no retry from
  the same pair.
- At 5000 it is `at_floor`, logged, even right after a run of capacity
  `at_floor` refusals (the defect below). RATE_LIMITED binds.
- Disabled, it only `would_act`s. `end_session` clears it.

**Also:** `NightOneShape` (night 1's F1 shape gives one capacity FALLBACK;
the cap then held for 300 reports gives nothing more), and 2 wrapper
tests (capacity through the actuator; the backstop through
`note_recovery_restart`, waiting for PLAYING, then acting once).

**A defect found by the replay, fixed before any session used the fix.**

- `_refuse` writes one row per run of the same (class, reason).
- In night 1's F1 replay, the capacity bar kept refusing FALLBACK
  `at_floor`. So the backstop's own `at_floor` decision was folded into
  that run, and 2 of its 4 decisions were not written.
- The spec says "logged". Now an escalation's refusal is always written,
  and it does not reset the run for the other triggers. The test for
  this fails on the earlier module and passes on the fix.
- **The silent hold (§4) ran the earlier module**:
  - sha256 `3e312681…`, loaded at the unit restart 16:45:56Z, a copy of
    it in `adaptive_bitrate_live.hold.py`;
  - the final module is `7c326e6e…`;
  - the one difference only decides whether an escalation's refusal row
    is written, so it cannot change a hold with no escalation.
- The replays in this record, the fake-sudo runs and night 2 use the
  final module.

**Mutations**, each restored after:

| mutation | failures |
| --- | --- |
| loss-of 3 → 2 | 2 |
| window 180 → 182 s | 1 |
| removing the recovery-PLAYING wait | 2 |

**Other suites:** `tools/test_adaptive_bitrate_shadow.py` 21/21
(unchanged); `tools/test_c3_l4_nft_night.py` 23/23.

### Replays

`tools/c3_l4_n1_replay.py`, output `c3_l4_n1_replays.txt`.

**Parity.** The S1 shadow night through live gives **0 actions** (3,594
reports; L1's `parity()`, unchanged). The same rebuild with the shadow
log's own loss field (3,590 of 3,594 reports carry it) gives **0
decisions**.

**Night 1, exact, open-loop.** These are night 1's own `sample` rows,
with its recovery restarts at their times, the guards from the recovery
log, and the disable where it was called.

| phase | first firing | time after the cap | then (counterfactual: the data are still 7000's) |
| --- | --- | --- | --- |
| F1 cap | **capacity FALLBACK 7000 → 5000** at 15:23:55.2Z | **+13.6 s** | refused `hold_down`, then `at_floor` on every later bar; backstop armed 4× by the recorded restarts, each decision `at_floor`, logged |
| F2 2 % loss | **nothing** (baseline, loss, removal) | — | — |
| F3 cap | **capacity FALLBACK 7000 → 5000** at 16:01:26.1Z | **+16.7 s** | `hold_down` / `at_floor`; backstop armed 2×, `hold_down` / `at_floor`; after the drop, an INCREASE 5000 → 5500 at 16:08:25 (the blend, clean link) |
| K cap | **capacity FALLBACK 7000 → 5000** at 16:11:28.7Z | **+19.7 s** | `hold_down` / `at_floor`; backstop armed 1×, `at_floor` |

No firing in any baseline, after any removal, or in F2. **Correction to
the handoff:**

- It read K as "would act only (K then disabled)".
- In fact the capacity FALLBACK comes at +19.7 s, 100 s *before* the
  disable at +120 s. So it would have **acted** in K, and the disable
  would have found the stream at 5000.

**F1 under the cap: the blend's climb, a prediction, not a result.** The
recorded data after the first firing are 7000's, so this comes from the
rules and L1's rung loads. Those loads are 5000 ~775, 5500 ~850 and
6000 ~930 kB/s, against a cap of 874 kB/s.

- **+14 s**: capacity 7000 → 5000.
- **~+200 s**: INCREASE 5000 → 5500, 93 reports after the SSRC change,
  if ≥ 85/90 are clean. 5500 fits with ~3 % headroom.
- **~+390 s**: INCREASE 5500 → 6000, which is over the cap by ~6 %.
- **Not before ~+510 s**: the capacity FALLBACK 6000 → 5000, after the
  60-report reversal hold-down.
  - During those ~120 s at 6000, recovery may own a freeze and restart
    at 6000.
  - If it restarts twice, the backstop arms. Its one decision is refused
    `hold_down` (consumed), and capacity then acts once the hold-down
    ends.
- **~+700 s**: the next INCREASE is the third direction change within
  10 min of the first (~+200 s) → **HOLD (oscillation)** at 5000. That
  is inside the 720 s cap, barely.
- **Other branches:**
  - If 5500 is not clean enough to climb, or 6000 is only mildly over
    and misses the capacity bar, the shape is "climbed to <rung> and
    stayed".
  - If the third change comes more than 10 min after the first, it is an
    INCREASE, not a HOLD.
- **Night 2's pre-registration** takes every branch as rule-conformance
  (F1b).

**Every recorded series.**

- **Exact** (every live `sample` row ever written; the companion's live
  log, 3,850 rows in 45 sessions): B2, the L2 harness dry run, the L2B
  fake-sudo runs, and night 1.
  - Outside night 1's caps, **0 decisions** by either new rule.
  - F2 and every baseline: none.
- **Heartbeats, with C4-D1's proxies and the loss proxy.** The loss
  proxy is the heartbeat's cumulative `lost_packets` differenced.
  - **148 series, 62,596 reports**, 82.4 % carrying a loss delta. The 17
    series without one are all 2026-09-21, an older schema, where
    capacity cannot fire.
  - The pool: C4-D1's 82 inputs and CTRL-L1's 3; the companion's
    heartbeat log and archives (2026-09-24 17:02Z → now); and every
    evidence heartbeat file.
  - Named series found in it, with loss:
    - the S1 shadow night H1-H4;
    - C3.L3a sessions 2, 3 and 4;
    - C3.L3a-S1 T0-T3 / H1-H3;
    - L1 A and B;
    - L2 B2;
    - C5-M1's 720p B1-B3;
    - C4-M1, C3-F1, D7 and the L2B / dry runs.
  - **C3.L3a session 1 (2026-09-24 15:58Z) is not on disk as a series.**
    Its heartbeats rotated out before any copy, and only its decoder
    report remains.
  - **New-rule decisions: 0** outside night 1.
  - **Raw capacity windows** (5 consecutive reports at the bar,
    whatever the controller's state): **394, all in night 1's three
    capped sessions, 0 elsewhere.**
  - The proxy's own old-rule firings are the same C4-D1 ROUTINEs L1/L2
    listed. There are also four FALLBACK `fps_queue_gap` in the L2B
    forced-abort runs, where the stream had stopped while the client
    kept reporting (fps 0, output age rising, loss 0).
  - Neither is a new rule, and the exact replay of the same sessions
    shows nothing.
- **Recovery restarts** (the companion's recovery log since 2026-09-20
  plus the evidence copies; 683 rows, 63 `encoder_restart` in 20
  sessions).
  - 43 consecutive pairs fall within 180 s, **all inside recorded
    faults**:
    - D-BASE-R3 / R3a / R4's substitute faults (2026-09-20, incl. R4's
      K70 at 21:44);
    - R3b N150 (2026-09-22 15:21);
    - P8 v1 arm B hit by R3b E30 (23:38);
    - R3b E30 (2026-09-23 02:31);
    - night 1.
  - Every restart outside them is a single, e.g. 2026-09-21 08:24.

**The stop rule: PASS.** Neither rule fires on a clean-link session
outside a deliberate fault or a recorded link drop. The rules stand as
approved.

## 4. Session — the silent live hold

**SILENT.**

- Pre-registration: `c3_l4_n1_hold_preregistration.txt`, sha256
  `1f63744e…`, written after the replays passed and before the hold.
- Harness: `c3_l4_n1_night.sh` + `c3_l4_n1_run.sh`, which are L2's with
  arm H only and never INJECT.
- Scorer: `c3_l4_n1_score_hold.py`, output `c3_l4_n1_hold_score.txt`.

**The session.**

- 2026-09-29 16:46:37 → 17:16:37Z, 30 min in attract mode on a clean
  link, T2 sampler on, zero input.
- Live flag only; the adopted profile. `any_override` was false at
  PLAYING.
- Live mode read `live`, with inject off. Both new rules were visible in
  the status.
- **The module was the one before the escalation-logging fix**
  (`3e312681…`, §3).

**Results.**

- **0 transitions**: no `transition`, `would_act`, `hold`, `refused` or
  `escalation_armed` row. `transitions_this_session` 0; the status poller
  read 7000 on all 359 rows.
- **902 sample rows**: 901 evaluated and 1 resync. 834/901 clean by the
  blend.
- **The capacity bar never came close**:
  - in any 5 evaluated reports, at most 1 was under 50 fps and none had
    loss ≥ 50;
  - over the whole hold, 2 reports were under 50 fps (min 45.7) and the
    most lost in a report was 25.
- **Recovery**: `session_started` only. No SSRC change, no resync.

**Close-out rows** (decoder report, 30.21 min): all met.

| row | value | target |
| --- | --- | --- |
| spikes_20/min | 26.61 | < 200 |
| rendered fps | 59.94 | ≥ 59.5 |
| stale drops/min | 0.46 | < 20 |
| post-FEC loss/min | 7.78 | < 10 |
| audio underruns/min | 0.40 | < 5 |
| max output gap | 182 ms | reported; bound ≤ 250 |

**Teardown** (17:17:40Z):

- The flag was unset: manager 0, and 0 in the new MainPID's environ.
- `adaptive_bitrate` mode `off`; the inject route answers 403.
- Stream 7000, adopted profile, `any_override` false, no game, 0
  NOW PLAYING banners.

## 5. The harness for night 2

### `--only`

- `tools/c3_l4_nft_night.py --only F1,F3` takes any subset of F1, F2, F3,
  K and always runs it in that order.
- `parse_only()` refuses an unknown, empty or repeated name in the
  argument parser, before the preflight (exit 2). `--sessions` stays as
  a hidden alias.
- The preflight, setup, teardown, allow-list, keepalive and every
  always-clear path are the same code whatever the subset.
- F3's cap uses F1's calibration when F1 ran, which it does with
  `--only F1,F3`.
- The default `--prereg` is night 2's. The `did` summary adds each
  decision's reason and trigger, the decisions by trigger, and
  `escalation_armed`.
- The EXPECT lines name the capacity trigger.
- Unit tests: 23/23, 5 of them new (`OnlySubset`).

### Fake-sudo tests

`n1_fake_tests.sh` with `n1_check.py`. The checker is L2B's
`l2b_check.py`, unchanged, plus the subset checks. **Never real sudo or
`nft`.** Both runs used the final module and ran real sessions on the
onn with the fake sudo (`--fast`, 60 s holds).

| run | harness exit | result |
| --- | --- | --- |
| **FULL** (`--only F1,F3`, 17:18-17:26Z) | 0 | **PASS** |
| **ABORT** (`--only F1,F3 --test-fail-at F3_drop`, 17:26-17:33Z) | 4 | **PASS** |

**FULL:**

- Only F1 and F3 reached PLAYING, in that order; no F2 or K banner.
- Night 2's pre-registration was hashed (`3cdcfa2e…`).
- 26 fake-sudo calls, all `-v`, `-n -v` or `-n nft`.
- The last delete was followed only by `list tables`, which showed no
  table.
- The teardown was clean: flag absent, mode `off`, 7000, no game, 0
  banners. Every expected file was present.
- With no real fault, the controller stayed silent at 7000. The `did`
  rows carry the new `decisions_by_trigger` and `escalation_armed`
  fields.

**ABORT:**

- F1 ran whole, then an exception was raised during F3's drop.
- 23 calls. The fault was removed and `list tables` confirmed it absent,
  then the teardown ran clean.

Copies are in `fake_runs/` (summary, events, `nft_commands`,
`nft_tables`, harness log, console, the fake's argv; redacted). The full
run dirs are in `logs/streaming/c3_l4_n1_tests/`.

### Night 2's pre-registration

`c3_l4_n1_2026-09-29/c3_l4_nft_night2_preregistration.txt`, sha256
`3cdcfa2e5eb6a021eff258214fefd5ac54541bd0c7c10c56ff3697a382dfb25d`. It
was written before the night, from night 1's rules with the new
triggers. **Its rows:**

- **F1a** — the capacity FALLBACK 7000 → 5000 within 60 s of the cap,
  as one transition.
- **F1b** — the blend's climb under the cap follows the rules, whichever
  way the cap falls:
  - expected: 5500 fits, 6000 does not, capacity back to 5000 after the
    reversal hold-down, then HOLD `oscillation`;
  - or "climbed to <rung> and stayed";
  - or an INCREASE if the third change falls outside 10 min.
- **F1c** — rate limit never; no ramp.
- **F1d** — after removal as night 1.
- **F1e** — the backstop: expected not to fire (capacity acts first);
  recorded either way.
- **F1f** — recovery cycles under the cap, reported (expected ≤ 1).
- **F3pre** — capacity brings the stream to 5000 within 240 s. If not,
  F3b is NOT TESTED.
- **F3a / F3b** — as night 1. The backstop's decision after the drop, if
  any, is `at_floor` and must not move the level.
- **All-sessions rows** — as night 1, with F1f's cycles excepted from
  the lifecycle row.

### The user's hand steps for night 2 (one PowerShell SSH window, ~45 min)

These are L2B.4's, with `--only F1,F3`. Run them with no Code queue
running. Nothing is needed on the TV.

1. `tmux new -s nft2`. Night 1's `nft` tmux session is still open, with
   an idle shell; `tmux kill-session -t nft` first is fine.
2. `cd ~/Projects/onn-stream-test && python3 tools/c3_l4_nft_night.py --only F1,F3`
3. Type the sudo password when asked, and press Enter to accept the
   pre-registration. The first lines must show
   `c3_l4_nft_night2_preregistration.txt`, sha256 `3cdcfa2e…`. Then wait
   about 45 minutes; there is nothing else to type.
4. To stop early: `Ctrl-C`. The fault is removed automatically.
5. If the SSH connection drops: reconnect and `tmux attach -t nft2`. If
   the harness asks for the password again, type it.
6. At the end it prints `RUN DIRECTORY: …`. Tell Claude "nft 2 done".

Notes:

- *(Optional, before step 2)* The pre-registration can be amended:
  `docs/memory/evidence/c3_l4_n1_2026-09-29/c3_l4_nft_night2_preregistration.txt`.
- If it says **REFUSED**, fix the reason it gives and start again at
  step 2. Nothing has been changed.
- If the harness itself is gone and it says `COULD NOT CONFIRM THE FAULT
  IS GONE`, type:
  - `sudo nft delete table inet privyhub_fault`
  - `systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE && systemctl --user restart privyhub-companion`
  - `curl -X POST localhost:8765/plugins/games/stop`

## Files (`c3_l4_n1_2026-09-29/`)

**§1**

- `c3_l4_n1_score_night1.py` → `c3_l4_n1_night1_score.txt` / `.json`.
- The night's copy is `../c3_l4_nft_night1_2026-09-29/` (own README and
  manifest).

**§2**

- `adaptive_bitrate_live.py` (final, `7c326e6e…`).
- `adaptive_bitrate_live.hold.py` (the module the hold ran, `3e312681…`;
  `module_sha256_during_hold.txt`).
- `module_patch.diff` (L2 → final).
- `pre_patch_sha256.txt` / `post_patch_sha256.txt`: `adaptive_bitrate.py`,
  `games.py` and `c3_l4_l1_replay.py` are unchanged;
  `link_drop_recovery.py` `d921aeb1…`, not edited.

**§3**

- `test_adaptive_bitrate_live.py`, `unit_tests.txt`.
- `c3_l4_n1_replay.py` → `c3_l4_n1_replays.txt`.

**§4**

- `c3_l4_n1_hold_preregistration.txt`.
- `c3_l4_n1_night.sh`, `c3_l4_n1_run.sh`, `c3_l4_n1_night.log`.
- `t2_sample.py`, `t2_samples.jsonl`, `t2_sampler.log`.
- `runs/`: `index.txt`, armcheck, status, `status_end`, report,
  `decision_log_H.jsonl` (902 sample rows), `abr_series`, frames,
  heartbeat, alpha, the redacted companion journal, the encoder command,
  the adb monitor, `recovery_log_H.jsonl`.
- `c3_l4_n1_score_hold.py` → `c3_l4_n1_hold_score.txt` / `_summary.json`.

**§5**

- `c3_l4_nft_night.py`, `test_c3_l4_nft_night.py` (as in `tools/`).
- `c3_l4_nft_night2_preregistration.txt` (+ `.sha256`).
- `n1_fake_tests.sh`, `n1_check.py`, `n1_fake_tests.log`, `fake_runs/`.

**`sha256_manifest.txt`** covers every file here.

**Privacy.** `h2_prep_redact.py --check` passes on every Markdown and text
record written. In the run files and code copies it flags only:

- the loopback address (the inject route's `LOOPBACK`, the encoder's
  local target, the journal's local calls);
- the any-address bind;
- the core's own version string (Beetle PSX HW 0.9.x).

That is the same as L2's `runs/`. There is no private address, MAC,
serial or ADB endpoint.

Nothing adopted. Nothing committed.
