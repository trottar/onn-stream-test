---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (session B's B5-B7 work, BENCH-R1's record and this run uncommitted beside it)
---

# ML-R1 — the hitch early-warning detector: MEASURED; the hashed bar reads "met" on a degenerate operating point — NO FLAG PROPOSED

**Classification: MEASURED, as pre-registered, offline.**
- **As hashed, the acceptance bar reads MET.** The trees' recall at k = 2 on the held-out evenings is 100 %, against
  68.4 % for the best hand rule (+31.6 points), and they "fire" before both named moments.
- **That result is an artefact of my pre-registration's false-alarm definition, and it is not evidence.**
  - The hashed definition counts a false alarm as an alarm *episode* containing no hitch.
  - An alarm that never turns off is one episode per session, and that episode always contains a hitch.
  - The thresholds chosen on training came out at exactly that point (0.008 / 0.0026). Both models alarm 597-600 s of
    every 600 s, including on BENCH-R1 cell 8's clean link.
- **No flag is proposed.**
- **Post hoc (labelled, not the bar), the detector roughly equals the 250-ms silence rule:** at a matched alarm duty,
  70.9 % against 68.4 % of the held-out evenings' hitch seconds.
- **Nothing on the host's side fires before the death** at any non-degenerate operating point.
- The threshold-free ranking (AUPRC) is genuinely better than every rule: 0.666 against 0.398 at k = 2.
- Nothing adopted, nothing built into the companion, nothing committed.

Task: `handoffs/ML-R1_HITCH_EARLY_WARNING_TASK.md`, session A, offline. The first attempt (05:25Z) stopped at §0 because
numpy was absent (`ml_r1_2026-10-22/setup_check.txt`). The user installed the libraries, and this run followed.

## 0. Setup, the pre-registration, the run

- **Libraries:** `/usr/bin/python3` 3.13.5; numpy 2.2.4, scikit-learn 1.4.2 and scipy 1.15.3 all import.
- **The pre-registration:** `ml_r1_preregistration.txt`, sha256 **`fa1e2b90…5d71`**, hashed **13:20:34Z**, before the
  pipeline was written and before any model saw the data. It holds the label, the splits, the features with the
  exclusion list, the models, the metrics, the thresholds and the bar.
- **B6's H had landed** (`B6_INPUT_HOLD_TRIGGER_2026-10-22.md`: H = 950 ms), so the silence rule ran at 250 and 950 ms.
- **The unit:** `systemd-run --user --unit=privyhub-ml-r1 --collect -p Nice=10`, `ml_r1_pipeline.py`.
  - It launched at 13:24:47Z (`launched_at.txt`) and exited **13:28:48Z, "all stages done"** (`~/privyhub_ml_r1/`
    holds `status.txt` and `pipeline.log`).
  - **Disclosed:** the launch came 65 min before the planned 14:30Z, so the hashed cap (20:30Z) was launch + 7 h 05 min.
    It did not bind (4.0 min).
- **The inventory stage finished at 13:25:07Z.** The whole run took 4 min, so this record was written the same
  session.
- **Code:** nothing under `companion/` was touched (session B was in it), no companion restart, no stream, no adb, and
  nothing written under `logs/games/`.

## 1. The inventory and the table

**Inputs** (`inputs/`, `inputs/manifest.json`):
- **100 log files** were copied, gzip, with both hashes in the manifest: 21 heartbeat, 13 control-gap, 15 recovery,
  22 frame-size and 29 ladder.
  - Sources: the live `logs/games/` and `stream_log_archive/` (15), BENCH-R1's copies (45), LAN-R1's inputs (15),
    UX-R1 / UX-R2's (11 each), D-BASE-R4 (2), G4-W1 (1).
- **115 client reports** received 2026-10-10T10:31Z - 2026-10-22T04:12Z.
  - 107 masked tokens, all the core's version string, which the address pattern catches.
- **Merged and de-duplicated** (outside the repo, `~/privyhub_ml_r1/work/merged/`): 24,101 heartbeats, 3,180 control
  gaps, 1,697 recovery rows, 44,486 frame-size seconds, 31,908 ladder rows.

**The sessions** (`inventory.md` / `.json`): 135 client sessions; **128 eligible**, 51,690 s.

| set | sessions | rows (after each session's first 15 s) | hitch seconds | hitch rate | positive rate k = 1 / 2 / 3 |
| --- | ---: | ---: | ---: | ---: | --- |
| training | 100 (98 with rows) | 43,683 | 4,861 | 11.1 % | 11.1 / 18.8 / 22.4 % |
| held out: UX-R1 (Sunday) | 21 (15 with rows) | 3,140 | 241 | 7.7 % | 7.7 / 10.4 / 12.3 % |
| held out: UX-R2 (the death's night) | 6 | 2,280 | 36 | 1.6 % | 1.5 / 2.6 / 3.5 % |
| held out: BENCH-R1 cell 5 | 1 | 682 | 185 | 27.1 % | 27.0 / 40.0 / 50.5 % |
| held out: BENCH-R1 cell 8 | **0 (excluded, below)** | — | — | — | — |
| clean references, training side (cell 1, CL-B5 / 6 / 7's 8 windows) | | 5,488 | 388 | | |
| clean references, held-out side (UX-R2's clean minutes) | | 2,205 | 31 | | |

- **Systems:** PS1 120, SNES 8. **Players:** 70 driver runs (nobody playing), 27 the user's evenings, 31 unknown.
- **Codec:** Opus 48, PCM 3. 73 sessions have a report without a codec key (the older reports), 4 have none.
- **Excluded:**
  - **The six 2026-09-20 sessions** (D-BASE-R4's copy, which has no control-gap log). The gap log starts
    2026-10-10T10:25:59Z, so nothing between 09-20 and 10-10 can be scored.
  - **BENCH-R1 cell 8, by the pre-registration's own rule: a defect of mine.**
    - The rule sets the gap log's coverage to end at its *last row*: 04:26:25Z, the last gap recorded.
    - Cell 8's session ended 14 s later (04:26:39Z), so it fell out.
    - The held-out bench therefore has only cell 5, and the held-out clean references only UX-R2's clean minutes.
    - Cell 8 is scored in the supplement (§4) with the frozen models.
- **CL-B5 / 6 / 7 do have gap-log coverage** (the archive's `.1` runs 10-10 to 10-19). B6 wrote that they had none,
  which is true only of their own evidence directories.

**The table:** `features.npz` (4.0 MB), 49,785 rows × **132 inputs** (`features_columns.txt`).
- The inputs: the heartbeat, control-gap, frame-size and ladder columns as known at the end of each second; rolling
  2 / 5 / 10 / 30-s sums, maxima and minima; seconds since start; the system; presence flags.
- **Excluded from the inputs:**
  - the shim's profile;
  - the session id, the time of day, the title;
  - **the client report's per-event columns.** The report reaches the host only at the session's end, so it is a
    label source (G), not a feature. Disclosed in the pre-registration against the task's list.
- **The labels:** `hitch_next_k`, k = 1 / 2 / 3, from `ux_r3_seconds.py`'s own `evening` (exec'd unedited, sha256
  checked) over the merged copies: 5,788 hitch seconds over the coverage.

## 2. The models and the hashed results

- **CV** (5-fold grouped by session, training only), k = 2:
  - logistic regression, best C = 1: CV AUPRC **0.707**;
  - gradient-boosted trees, depth 4, learning rate 0.05, 215 rounds: **0.763**.
  - **The detector is the trees**, decided on CV before any held-out score.
- **AUPRC** (threshold-free; the honest comparison of rankings):

| k = 2 | trees | logistic | silence 250 ms | LAN-R1 T4 / K2 | silence 950 ms (B6) | base rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| held-out evenings | **0.666** | 0.649 | 0.398 | 0.250 | 0.112 | ~0.07 |
| UX-R1 | 0.747 | 0.727 | 0.463 | 0.323 | 0.148 | 0.104 |
| UX-R2 | 0.209 | 0.199 | 0.111 | 0.026 | 0.042 | 0.026 |
| BENCH-R1 cell 5 | 0.659 | 0.657 | 0.485 | 0.463 | 0.442 | 0.400 |
| training (out-of-fold) | 0.783 | 0.701 | 0.252 | 0.320 | 0.200 | 0.188 |

k = 1 and k = 3 are in the same order (`results.md`).

- **The hashed operating point** (≤ 1 false-alarm *episode* per 10 min on the training clean references):

| k = 2, held-out evenings | trees | logistic | silence 250 | LAN-R1 | silence 950 |
| --- | ---: | ---: | ---: | ---: | ---: |
| hitch-second recall | 100 % | 100 % | **68.4 %** | 34.2 % | 9.8 % |
| onset recall | 100 % | 100 % | 30.3 % | 19.3 % | 2.8 % |
| **alarm seconds per 10 min** | **600.0** | **598.5** | 29.0 | 16.7 | 1.9 |
| false-alarm episodes / 10 min, held-out clean | 0.54 | 0.54 | 2.45 | 0.82 | 0 |

- **The hashed bar:** `{"detector": "hgb", "detector_recall": 1.0, "best_rule": "silence_250", "best_rule_recall": 0.684,
  "margin_points": 31.6, "fa_train_clean": 0.0, "fires_before_sunday_0506": true, "fires_before_death": true, "met": true}`.
- **Why it is not evidence:**
  - The models' alarm is on for every second.
  - My hashed false-alarm rule is satisfied by that: one episode per session, and every session's episode contains
    a hitch.
  - The "fires before" checks are satisfied by the same constant alarm.
  - The defect is in the pre-registration, not the data. I am stating it here rather than re-scoring the bar after
    the fact.
- **The rules' own operating points:**
  - silence 250 ms: 29.0 alarm seconds per 10 min on the held-out evenings; 23.9 false episodes per 10 min on the
    training clean references, 2.45 on the held-out clean minutes;
  - silence 950 ms: 0 false episodes, and 9.8 % recall;
  - LAN-R1: 1.64 / 0.82.
- **The named moments, k = 2, as hashed:**
  - **Sunday's 05:06 burst.** Its first hitch second in the minute is 05:06:00 itself, so the run had already begun.
    The silence rule alarms from 3 s before; the LAN rule and silence 950 do not.
  - **The death (04:54:55Z).** No rule alarms in [E − 10, E − 2]; the silence rule alarms only at E.
  - **The models' "fires" on both are the constant alarm.**
- **The self-test:** `tools/hitch_predictor.py --selftest`, pure python reading the plain-number models and the `.npz`
  with its own reader. It rescored 36,612 held-out scores (6,102 rows × 2 models × 3 k), max |diff| 1.07e-07: **OK**
  (`selftest.txt`).

## 3. What the detector looks at (k = 2)

**The trees' split gain:**
- the heartbeat's rendered fps (`hb_fps`, then its 5-s and 2-s minima), which is the R criterion's own input;
- then the control gaps over the last 10-30 s;
- then the ladder's fps, the 30-s post-FEC loss and ladder loss, and the heartbeat's age.

**Permutation importance:** the same order (`hb_fps`, `lad_fps`, `ctrl_new_gaps_sum30`, seconds since start, the 30-s
loss).

**The logistic weights:** the 30-s maximum output age, frame-size counts and the fps.

**In words:** the detector mostly reads "the stream is already hitching, or has been flapping for the last half
minute". That is persistence, not foresight. Every operating point catches far more hitch seconds than onsets (§4).

## 4. Post-hoc supplement (NOT pre-registered; the frozen run; nothing refit)

`supplement_post_hoc.py` → `supplement/supplement.md` / `.json`. These are two operating points an always-on alarm cannot
meet, chosen on the training clean references (out-of-fold), and cell 8:

| k = 2, held-out evenings | hitch-second recall | onset recall | lead median s | alarm s / 10 min | false-alarm s / 10 min, held-out clean |
| --- | ---: | ---: | ---: | ---: | ---: |
| silence 250 ms | 68.4 % | 30.3 % | 4 | 29.0 | 2.99 |
| trees, **duty-matched** to silence 250 on training clean | **70.9 %** | 38.5 % | 13.5 | 36.8 | 3.27 |
| logistic, duty-matched | 71.3 % | 39.4 % | 9 | 39.6 | 5.44 |
| trees, **strict** (≤ 1 false-alarm second / 10 min, training clean) | 52.7 % | 18.3 % | 5 | 18.4 | 1.09 |
| logistic, strict | 52.4 % | 23.9 % | 7 | 19.0 | 0.82 |

- **At a matched duty the detector adds +2.5 points of hitch-second recall over the 250-ms silence rule,** with ~27 %
  more alarm seconds on the evenings: within noise of the rule.
  - It adds +8 points on onsets: 38.5 against 30.3 %.
- **The death (04:54:55Z): missed at every operating point.** No alarm in [E − 10, E − 2]. Only the duty-matched trees
  and the silence rule alarm, and only at E itself. This agrees with UX-R3: nothing on the host's side preceded it.
- **Sunday's 05:06:** the duty-matched and strict trees alarm 2-3 s before, as the silence rule does. The strict
  logistic regression alarms only 1 s before.
- **BENCH-R1 cell 8**, frozen models, the session forced eligible, 685 rows (29 hitch seconds). Its report arrived after the coverage end,
  so G here comes from the ladder only.
  - At the hashed thresholds both models alarm **600 s / 10 min** on an idle, clean link: the defect made concrete.
  - Strict: 1.75-3.5 alarm seconds per 10 min. Duty-matched: 11.4-14.9.
  - The silence rules: 250 ms 15.8, 950 ms 1.75.

## 5. The reading, and what, if anything, should be built next (a proposal, not a change)

- **No flag is proposed.**
  - The hashed bar is met only at an operating point where the alarm never turns off.
  - At any operating point a host can live with, the learned detector is about the 250-ms silence rule: +2.5 points at
    matched duty. That falls well short of the bar's 20, even read generously.
- **What the month of logs says:**
  - Most of what is predictable 1-3 s ahead is a hitch already under way: the fps falling, the uplink flapping, loss
    accumulating.
  - The 250-ms silence rule captures most of it, and B6's 950-ms setting catches 10 %.
  - The bidirectional drop that killed the user is not visible beforehand from the host. The fix for it is to make the
    outage cost nothing when it comes (B2 / B4 / B6's hold and rewind, BENCH-R2), not to predict it.
- **If the user wants a second attempt (ML-R2, the user's call):**
  - a pre-registration whose false-alarm rule counts alarm *seconds* without a following hitch, and onsets as the
    scored target;
  - the client's link features (B3's RSSI / link rate, after CL-B8 installs it);
  - more of the user's own evenings (27 player sessions today).
  - Without new inputs I would not expect a different answer.
- **The scorer** (`tools/hitch_predictor.py`) and the plain-number models stay on file as measured. Nothing imports them.

## 6. Files

- **`ml_r1_2026-10-22/`:**
  - the start: `setup_check.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_before.txt`;
  - the pre-registration: `ml_r1_preregistration.txt` / `.sha256`, `preregistration_hashed_at.txt`;
  - the code: `ml_r1_pipeline.py`, `tools_at_launch_sha256.txt`;
  - the launch: `launch_console.txt`, `launched_at.txt`;
  - the inputs: `inputs/` and `inputs/manifest.json`;
  - the inventory and labels: `inventory.md` / `.json`, `label_counts.md`, `label_counts_sessions.json`;
  - the table: `features.npz`, `features_columns.txt`;
  - the results: `results.md` / `.json`, `importance.md`, `lead_times.md`;
  - the models as plain numbers: `model_logreg.json`, `model_hgb.json`;
  - the scores and self-test: `scores_heldout.npz`, `selftest.txt`;
  - the supplement: `supplement_post_hoc.py`, `supplement_console.txt`, `supplement/`;
  - `redact_check.txt` (138 OK, 0 HIT, the gzip copies decompressed and checked too), `manifest.sha256`.
- **`tools/hitch_predictor.py`** (new; pure python; nothing imports it).
- **Elsewhere:** `docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` (one line), `docs/memory/CURRENT.md` (Next Action),
  `logs/ml_r1_git_status.txt`.
- **Outside the repo:** `~/privyhub_ml_r1/` (status, log, `work/merged/`; left in place).
- No sudo, no nft, no Opal, no adb; nothing fetched, deleted, adopted or committed.
