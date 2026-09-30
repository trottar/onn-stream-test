---
memory_schema: 1
as_of: 2026-09-29
baseline_commit: f01c3b2
status: C3-L4-N2 DONE — night 2 scored WORKS UNDER LOSS (F1, F3), with the finding that 6000 under the cap sat degraded 3 min 56 s below every bar (own record C3_L4_NFT_NIGHT2_2026-09-29.md). The user's capacity_mild (2026-09-29, "Go") BUILT in LIVE only — ROUTINE one rung down on fps < 57 on >= 4/5 and lost >= 50 on >= 3/5, strict capacity first, ROUTINE hold-downs and deferral as built; the stale status level after BACK fixed. Tests 102/102 live, 21/21 shadow, 23/23 harness; mutations caught. Replays: night 2 reproduced as recorded, then capacity_mild 6000 -> 5500 at 119 s into 6000 (bar at 46 s, refused hold_down until the 60-report reversal hold-down); night 1: strict still first (13.6-19.7 s; mild bar at ~10 s deferred); 0 firings on any adopted clean-link series (4 guard-refused decisions only on C5-M1's non-adopted 1080p candidate at session start, listed) -> the stop rule PASS. 30-min live hold: controller silent (0 transitions, 0 mild windows) but NOT SILENT on the close-out loss row (33.99/min, isolated link bursts). Night 3 pre-registered (--only F1, sha256 cf0ce814...; the handoff's "within 90 s" is not reachable with the ROUTINE hold-down it requires -- flagged, bound set to the hold-down) and the harness defaults to it; fake-sudo --only F1 PASS. Flags unset and absent; nothing adopted; nothing committed
---

# C3-L4-N2 — the mild-capacity rule

Task: `handoffs/C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md`,
under `QUEUE_2026-09-29B.md`'s rules.

- §1, night 2 scored, is `C3_L4_NFT_NIGHT2_2026-09-29.md`: **WORKS UNDER
  LOSS (F1, F3)**, with the finding that 6000 sat degraded under the cap
  for 3 min 56 s and nothing fired.
- Patch: `patches/C3-L4-N2_MILD_CAPACITY.md`.
- Evidence: `c3_l4_n2_2026-09-29/` (manifest).
- The decision is appended to
  `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`.

**Classifications.**

- **The rule: BUILT** (live only; the shadow byte-identical).
- **Tests: PASS.** 102/102 live, 21/21 shadow, 23/23 harness; mutations
  caught.
- **Replays: the stop rule PASSES** on the adopted profile.
  - `capacity_mild` fires nowhere outside nights 1-2.
  - It met its bar only on C5-M1's non-adopted 1080p candidate, 11 s into
    four sessions, where the session-age guard refused it. It could never
    act there (the reference-profile guard too). This is listed with its
    samples below.
- **Silent hold: NOT SILENT, on the close-out loss row.**
  - 0 transitions, and the new rule's bar never came near (0 windows).
  - Post-FEC loss was 33.99/min, from isolated link bursts (the onn's
    link rate was down to a median 195 Mbit/s).
- **Night 3's pre-registration: WRITTEN** (sha256 `cf0ce814…`), with one
  **deviation from the handoff flagged**: the mild step can come only
  after the 120 s reversal hold-down, not within 90 s.

## 2. The rule, as built (`companion/adaptive_bitrate_live.py`)

The user's decision, 2026-09-29: **"Go"**.

**Mild capacity** — class ROUTINE, reason and trigger `capacity_mild`,
**one rung down** from the stream's level.

- The steps: 7000 → 6000, 6000 → 5500, 5500 → 5000. At 5000 it is
  `at_floor`, logged.
- **The bar**: over the last 5 evaluated reports, **fps < 57 on ≥ 4 of 5
  and `lost_packets_delta` ≥ 50 on ≥ 3 of 5**. A stale report or a missing
  delta does not count: the window holds only evaluated reports.
- Constants: `CAPACITY_MILD_FPS_BELOW 57.0`, `CAPACITY_MILD_FPS_OF 4`,
  `CAPACITY_MILD_LOSS_AT_LEAST 50`, `CAPACITY_MILD_LOSS_OF 3`.
- **Precedence** in `LivePolicy._evidence()`:
  1. the queue/gap FALLBACK;
  2. **strict capacity** (FALLBACK → 5000; it keeps precedence when both
     hold);
  3. **`capacity_mild`**;
  4. the queue ROUTINE (→ 6000, fixed target, unchanged).
- **Why mild comes before the queue ROUTINE.** From 7000 both name 6000.
  Below 7000 the queue ROUTINE's fixed 6000 target is refused
  `at_or_below_target`, so only the mild rule's one-rung step can act
  there. When the mild bar does not hold, the queue ROUTINE is exactly as
  before (tested).
- **Target.** `_decide("ROUTINE")` takes the next rung below the level
  when the trigger is `capacity_mild`; at 5000 the target is the floor
  itself, so the existing check says `at_floor`.
- **Everything else is ROUTINE's, unchanged:**
  - hold-downs 60 reports after a down and 60 after an up;
  - the 3-report blackout, the rate limit 4 / 10 min, the oscillation
    guard, and the guards (recovery PLAYING, age ≥ 60 s, reference
    profile, no override);
  - L1's escalation deferral: while the newest report is under 50 fps, a
    ROUTINE waits up to 4 reports for FALLBACK.
- **Also fixed** (the night-2 check (i)): `LiveController.session_ended()`
  clears the cached stream bitrate. The status `level` now reads the
  policy's 7000 after BACK, not the ended session's last rung.
- **Visible:** `policy.capacity_mild` (the rule); `trigger` /
  `reason: capacity_mild` on its rows.

## 3. Tests and replays — before any session

### Tests

**`tools/test_adaptive_bitrate_live.py`: 102/102.**

**The 16 new tests:**

- **`MildCapacityTrigger`** (15):
  - It fires at 4/5 fps < 57 with 3/5 loss ≥ 50, one rung, from 7000,
    6000 and 5500.
  - Boundaries: 56.99/50 fires; 57.0, 49 and 45 do not.
  - It does not fire at 3/5 fps, at 2/5 loss, on loss alone (fps ≥ 57),
    or on fps alone. The queue ROUTINE (→ 6000, `fps_queue_gap`) is
    unchanged.
  - Strict wins when both hold.
  - One rung, never two: the ROUTINE hold-down refuses at 59 reports and
    allows at 60.
  - At 5000 it is `at_floor`, logged.
  - The blackout, the rate limit and the recovery guard bind. Missing or
    stale reports do not count.
  - Night 3's oscillation shape: 5500 → 6000 → mild → HOLD at 5500.
  - The shadow does not act.
- **`NightTwoShape`** (1): night 2's 6000 figures step to 5500 once.
- **A wrapper test**: the status level after session end is 7000.

**Three N1 tests narrowed** (declared):

- `test_boundaries…`, `test_not_at_4_of_5_fps` and `test_not_on_loss_alone`
  asserted "no transition at all" on shapes (fps 50-55 with heavy loss)
  that **now meet the mild bar by design**.
- They now assert that the **strict** rule neither fires nor is refused.
  The loss-alone test adds a fps ≥ 57 case that must stay silent.

**Mutations**, each restored after:

| mutation | failures |
| --- | --- |
| fps-of 4 → 3 | 2 |
| loss 50 → 40 | 1, after a boundary test was added (it was not caught at first) |
| a fixed 6000 target instead of one rung | 6 failures, 2 errors |
| mild before strict | 11 failures, 2 errors |
| no status clear | 1 |

**Other suites:** `test_adaptive_bitrate_shadow.py` 21/21 (unchanged);
`test_c3_l4_nft_night.py` 23/23 (night 3 is the default pre-registration).

### Replays

`tools/c3_l4_n2_replay.py` is N1's tool with the stop rule on
`capacity_mild`, night 2 as a fault window, and N1's hold and fake runs as
clean sessions. Output: `c3_l4_n2_replays.txt`.

**One improvement to the exact replay.**

- Rows the live wrapper dropped while actuating are skipped.
- A replayed transition that matches the recorded one (same from → to,
  within 3 s) is confirmed at the recorded `transition_done`.
- So the replay follows the real controller until it **diverges**, and
  only rows after that are marked counterfactual.
- **On night 2 it reproduced every real transition at the same time**
  (13.9 s, 17:49:30.9, 17:53:59.9, 18:05:58.2), which validates the
  method.

**Parity.** The S1 shadow night gives 0 actions. With its logged loss
(3,590 of 3,594 reports), 0 decisions.

**Night 2, exact:**

| time | event | note |
| --- | --- | --- |
| 17:46:11.8 | capacity 7000 → 5000 | as recorded |
| 17:49:30.9 | INCREASE → 5500 | as recorded |
| 17:53:59.9 | INCREASE → 6000 | as recorded; arrived at 6000 at 17:54:01 |
| **17:54:46.2** | `capacity_mild` 6000 → 5500 **refused `hold_down`** | **46 s into 6000**: the bar met, but it is the reversal after an up, which needs 60 reports |
| 17:55:14, 17:55:44 | refused `hold_down` | |
| **17:56:00.5** | **`capacity_mild` 6000 → 5500** | **119 s into 6000**; the replay diverges from the real night here |
| 17:56:16-17:57:37 | 5500 → 5000 refused `hold_down` ×3 | counterfactual: the data are still 6000's |
| 18:00:53.8 | INCREASE 5500 → 6000 | counterfactual, cap off |
| F3 | capacity 7000 → 5000 at 16.7 s | as recorded; nothing else |

- Nothing fired at 5000 or 5500 under the cap, with the cap off, or in
  F3.
- **Correction to the handoff.** Cowork's "fires 45 s into the 6000 rung"
  is where the **bar** is met (46 s). The rule **acts** at 119 s, because
  the ROUTINE reversal hold-down the handoff requires applies.
- **The prediction beyond that is counterfactual.** Cowork asked for:
  the increase to 6000 ≥ 93 reports later, mild back after the hold-down,
  then HOLD. As built, the next increase after the mild step *is* the
  third direction change (up at 17:49:30, down at 17:56:00, up next).
  - In the recorded night it would fall at ~+790 s, 9.6 min after the
    first change. That is inside 10 min, so **HOLD at 5500**.
  - It would come after the 12-minute cap had ended.

**Night 1, exact.**

- The mild bar is met at 9.6 s (F1), 10.7 s (F3) and 11.7 s (K) after the
  caps. Cowork read ~8 s.
- Each time the newest report is already under 50 fps, so L1's 4-report
  ROUTINE deferral holds it for FALLBACK.
- **The strict capacity FALLBACK fires first**, at 13.6 / 16.7 / 19.7 s
  (N1's figures, unchanged).
- **In K the margin was zero.** The strict bar was met exactly at the 4th
  deferred report. One report later and the mild rule would have stepped
  7000 → 6000 first; strict would then have waited out the 30-report
  hold-down to reach 5000.
- After the strict FALLBACK, mild is refused `hold_down` / `at_floor` at
  5000 (counterfactual).
- Nothing fires in F2 (2 % loss) or in any baseline.

**Every recorded series.**

- **Exact** (every live sample row: 5,896 rows in 59 sessions). This
  covers B2, the L2 dry run, the L2B and N1 fake runs, **N1's silent
  hold**, and nights 1 and 2. **0 `capacity_mild` decisions outside
  nights 1-2.**
- **Heartbeats** (153 series, 63,919 reports, 82.7 % with a loss delta):
  - on the adopted profile, outside recorded faults: **0 firings, 0
    refusals, 0 raw mild windows**;
  - the closest any adopted session came, in any 5 reports, was 3/5
    under 57 with 3/5 at loss ≥ 50. That was in D-BASE-P6's uncapped A0
    holds of 2026-09-22, before the frame cap.
- **On a non-adopted profile**, C5-M1's 1080p60 candidate (smoke SA and
  holds A1-A3, 2026-09-28): the bar was met **4 times**, each **11 s
  into the session** during its start-up resyncs. All were refused by the
  60 s session-age guard (samples below).

| session | window fps | window lost | resyncs |
| --- | --- | --- | --- |
| SA 17:22:38Z | 26.6, 32.1, 38.8, 54.5, 62.0 | 504, 1009, 633, 195, 22 | 1, 4, 3, 0, 0 |
| A1 18:28:55Z | 22.0, 27.5, 31.1, 47.5, 59.1 | 4, 2040, 885, 187, 144 | 0, 5, 3, 1, 0 |
| A2 19:11:33Z | 24.4, 31.3, 33.9, 50.1, 55.3 | 0, 1542, 982, 223, 186 | 0, 4, 4, 0, 1 |
| A3 19:54:10Z | 26.5, 38.3, 46.1, 55.4, 60.2 | 656, 986, 623, 167, 16 | 2, 3, 1, 0, 0 |

- In live the reference-profile guard would also refuse on that profile.
  There were 6 raw windows there in all, all in those first seconds.
- **This is not a firing**: no transition, no `would_act`.
- **The tool's first pass printed STOP.** It counted these refusals, and
  also counted them against "clean link". The verdict now separates
  firings from refusals and adopted from non-adopted sessions, and prints
  both.
- **The user may read these as they choose.** The rule stands as
  approved either way.

**Recovery restarts:** 43 pairs within 180 s, all in recorded faults
(N1's backstop, unchanged). Night 2 had one restart.

**The stop rule: PASS.**

## 4. Session — the silent live hold

**NOT SILENT, on the close-out loss row only.** The controller itself was
silent: 0 transitions.

- Pre-registration: `c3_l4_n2_hold_preregistration.txt`, sha256
  `dd62f4ae…`, written after the replays passed and before the hold.
- Harness: N1's (`c3_l4_n2_night.sh`, `c3_l4_n2_run.sh`).
- Scorer: `c3_l4_n2_score_hold.py` (N1's, plus the mild near misses).
  Output: `c3_l4_n2_hold_score.txt`.

**The session.**

- 2026-09-29 18:33:41 → 19:03:41Z, 30 min in attract mode on a clean
  link, T2 on, zero input. Live flag only; the final module
  (`7e03ee1b…`).
- `any_override` false. The status showed `capacity_mild`, capacity and
  the backstop.

**The controller: silent.**

- **0 transitions**: no `transition`, `would_act`, `hold`, `refused` or
  `escalation_armed` row.
- The status poller read 7000 on 359 of 359 rows.
- 901 sample rows: 900 evaluated and 1 resync. 833/900 clean.
- **The `capacity_mild` bar**, in 896 windows of 5:
  - ≥ 4 under 57 fps: **0** windows;
  - ≥ 3 at loss ≥ 50: **0**;
  - both: **0**.
- **The strict bar** at its most: 2/5 under 50, and 1/5 at loss ≥ 50.
- No recovery event, no SSRC change, no resync.

**Close-out rows** (30.18 min):

| row | value | target | result |
| --- | --- | --- | --- |
| spikes_20/min | 35.95 | < 200 | met |
| rendered fps | 59.85 | ≥ 59.5 | met |
| stale drops/min | 1.42 | < 20 | met |
| **post-FEC loss/min** | **33.99** | **< 10** | **MISSED** |
| audio underruns/min | 0.50 | < 5 | met |
| max output gap | 452 ms | reported; bound ≤ 250 | over the bound |

**Where the loss came from.**

- 1,026 packets, in isolated single-report bursts spread over the half
  hour: 143, 98, 108, 103, 61, 57 and 52, plus smaller ones.
- The decoder report: 167 forward-gap events, max gap 114 packets; FEC
  recovered 279 packets, 91 groups unrecoverable.
- Queue 0 throughout; no freeze long enough for recovery.
- **No rule could fire on these.** Each burst is one report, and each
  rule needs ≥ 3 of 5.
- **T2:** the onn's link rate ran at a median 195 Mbit/s, against 260
  in N1's clean hold at 16:46Z. Signal −73 dBm against −74, and the Opal's
  tx retries the same order.
- This is the link's warm-state burst loss (D-BASE's residual, which
  B2's close-out also missed on), not the controller.
- The pre-registered classification is kept as written: **NOT SILENT
  (close-out loss row)**, controller silent.

**A defect found and worked around.**

- `c3_l4_n2_run.sh` (L2's) slices the decision log by byte offset.
- The controller log rotated at 4 MiB during the hold (18:48Z), so the
  slice came back empty.
- The slice was rebuilt by time, from the rotated file plus the live one
  (1,022 rows, `runs/decision_log_H.jsonl`). The scorer reads the
  rebuilt slice.
- Noted for any later live-hold harness: slice by time.

**Teardown** (19:04:42Z):

- Flags unset: manager 0, and 0 in the new MainPID's environ.
- `adaptive_bitrate` mode `off`; the inject route 403.
- Stream 7000, adopted profile, `any_override` false, no game, 0 banners.

## 5. Night 3 — `--only F1`

**The pre-registration:**
`c3_l4_n2_2026-09-29/c3_l4_nft_night3_preregistration.txt`, sha256
`cf0ce814bf686d8f082abccea1102d2f54c65cfad146b05e3215d7db4f3d8b69`,
written before the night. `tools/c3_l4_nft_night.py` now takes it as the
default `--prereg`.

- **F1a** — the strict capacity FALLBACK 7000 → 5000 within 60 s, one
  transition.
- **F1b** — the climb 5000 → 5500 (≥ 93 reports), 5500 → 6000 (≥ 93).
  Then **`capacity_mild` 6000 → 5500 as one transition, no sooner than
  the 60-report reversal hold-down and within 150 s of arriving at 6000**.
  Then the next increase attempt is the third direction change:
  - inside 10 min of the first → **HOLD `oscillation` at 5500** for the
    session (predicted, with ~23 s to spare);
  - later than 10 min → an INCREASE (as built);
  - or "climbed to <rung> and stayed".
- **F1c-f** — as night 2. F1c notes that the prediction puts 4
  transitions inside one 10-min window, which the rate limit allows.
- **F1g** — the time at 6000 under the cap, reported.
- **The all-sessions rows.**

**DEVIATION FROM THE HANDOFF, flagged.**

- The handoff asked for "`capacity_mild` 6000 → 5500 **within 90 s** of
  arriving at 6000". The same handoff requires ROUTINE's hold-downs.
  After an increase the reversal hold-down is 60 reports (120 s), so 90 s
  is **not reachable as built**. Night 2's replay met the bar at 46 s and
  acted at 119 s.
- Pre-registering 90 s would have scored a rule-conforming night as a
  failure. The row uses the hold-down's bound (no sooner than 60 reports;
  within 150 s) and says why.
- **The user may amend it before the night**, or ask for the ROUTINE
  hold-down after an up to be shortened (a rule change, the user's
  call).

**The user's hand steps for night 3** (one PowerShell SSH window, ~25
min). These are L2B.4's with `--only F1`. Run them with no Code queue
running. Nothing is needed on the TV.

1. `tmux new -s nft3`
2. `cd ~/Projects/onn-stream-test && python3 tools/c3_l4_nft_night.py --only F1`
3. Type the sudo password when asked, and press Enter to accept the
   pre-registration. It must show `c3_l4_nft_night3_preregistration.txt`,
   sha256 `cf0ce814…`. Then wait about 25 minutes.
4. To stop early: `Ctrl-C`. The fault is removed automatically.
5. If the SSH connection drops: `tmux attach -t nft3`. If the harness
   asks for the password again, type it.
6. At the end it prints `RUN DIRECTORY: …`. Tell Claude "nft 3 done".

Notes:

- *(Optional)* Amend the pre-registration first:
  `docs/memory/evidence/c3_l4_n2_2026-09-29/c3_l4_nft_night3_preregistration.txt`.
- **REFUSED**: fix the reason it gives, then start again at step 2.
- If the harness is gone and it says `COULD NOT CONFIRM THE FAULT IS
  GONE`, type:
  - `sudo nft delete table inet privyhub_fault`
  - `systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE && systemctl --user restart privyhub-companion`
  - `curl -X POST localhost:8765/plugins/games/stop`

### The harness, checked

`tools/c3_l4_nft_night.py` now defaults to night 3's pre-registration.
Its F1 EXPECT line names the mild step.

- `n2_fake_tests.sh FULL` ran `--only F1` against the fake sudo (--fast):
  **PASS** (`n2_check.py`, which is L2B's checks plus the subset's).
  - Only F1 reached PLAYING. Night 3's pre-registration was hashed.
  - 16 fake-sudo calls. The last delete was followed only by `list
    tables`, which showed no table.
  - The teardown was clean; every file was present.
- ABORT was not re-run. The always-clear paths are unchanged since N1's
  FULL and ABORT.
- The run is in `fake_runs/` (redacted) and
  `logs/streaming/c3_l4_n2_tests/`.

## Files (`c3_l4_n2_2026-09-29/`)

**§1**

- `c3_l4_n2_score_night2.py` → `c3_l4_n2_night2_score.txt` / `.json`.
- The night's copy is `../c3_l4_nft_night2_2026-09-29/`.

**§2**

- `adaptive_bitrate_live.py` (final, `7e03ee1b…`).
- `module_patch.diff` (N1 → N2), `harness_patch.diff`.
- `pre_patch_sha256.txt` / `post_patch_sha256.txt` (`adaptive_bitrate.py`,
  `games.py` and `link_drop_recovery.py` are unchanged).

**§3**

- `test_adaptive_bitrate_live.py`, `unit_tests.txt`.
- `c3_l4_n2_replay.py` → `c3_l4_n2_replays.txt` (and the console copy).

**§4**

- `c3_l4_n2_hold_preregistration.txt`.
- `c3_l4_n2_night.sh`, `c3_l4_n2_run.sh`, `c3_l4_n2_night.log`.
- `t2_sample.py`, `t2_samples.jsonl`.
- `runs/`, including the rebuilt `decision_log_H.jsonl` and
  `recovery_log_H.jsonl`.
- `c3_l4_n2_score_hold.py` → `c3_l4_n2_hold_score.txt` / `_summary.json`.

**§5**

- `c3_l4_nft_night3_preregistration.txt` (+ `.sha256`).
- `c3_l4_nft_night.py`, `test_c3_l4_nft_night.py`.
- `n2_fake_tests.sh`, `n2_check.py`, `n2_fake_tests.log`, `fake_runs/`.

**`sha256_manifest.txt`** covers every file.

**Privacy.** `--check` passes on every record. The run files and code
copies flag only the loopback address, the any-address bind and the
core's version string, as in N1.

Nothing adopted. Nothing committed.
