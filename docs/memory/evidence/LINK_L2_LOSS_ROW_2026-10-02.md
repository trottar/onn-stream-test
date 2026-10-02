---
memory_schema: 1
as_of: 2026-10-02
baseline_commit: 598cb61
status: LINK-L2 DONE — the 40 MHz day is TIME OF DAY by LINK-L1's rule as scored (LINK-L1's scorer, unchanged), ON THE BOUNDARY - 2 of 6 holds meet loss < 10/min (00:40 and 04:40 local); the four misses (08:41, 12:40, 16:41, 20:41) span exactly 12.00 h at the scorer's minute resolution and 12 h 0 min 7 s at second resolution, which would read MIXED; both readings are reported, neither chosen after the data. Six valid 20-min holds on the adopted profile at 7000 with the 4x PS1 source, adaptive switched to shadow per session (shadow confirmed every hold, 0 acted rows), 2026-10-01 20:41 → 2026-10-02 16:41 EDT; loss 20.80 / 1.64 / 9.47 / 12.84 / 13.21 / 11.49 per min; max gap ≤ 100 on none. Against LINK-L1 (80 MHz) - meets 2/6 vs 3/6, loss median 12.17 vs 11.37, the onn's link rate halved (median 135 vs 260). Air read-only - channel 36 / 40 MHz; 0 neighbours on 36 and 0 in the 36-40 pair; the 3-7 neighbours (3-4 strong) all in the 44-48 pair now. Nothing adopted; nothing committed
---

# LINK-L2 — the loss row at 40 MHz

Task: `handoffs/LINK-L2_LOSS_ROW_AT_40MHZ_TASK.md`, run unattended under
`handoffs/QUEUE_2026-09-29B.md`'s rules, 2026-10-01 18:17 EDT →
2026-10-02 17:03 EDT. Evidence: `link_l2_2026-10-02/` (manifest).

**The question.** It is LINK-L1's question, asked again after the user
changed the Opal's 5 GHz width from 80 to 40 MHz, keeping channel 36.
On the adopted profile, with adaptive bitrate not acting, does post-FEC
video loss < 10/min hold? If not, does it depend on the time of day?

## 0. The air view first (`access_check.jsonl`)

- The first read-only snapshot (18:17 EDT, LINK-L1's `link_l1_air.py`,
  to `/tmp`) **timed out** on its ssh round (25 s).
- One bare `iw dev wlan1 info` answered in 0.9 s. The snapshot was then
  repeated once (18:18) and read cleanly:
  - channel 36, **width 40 MHz**;
  - noise −89, one 5 GHz station;
  - the onn at −70 dBm.
- **The width is 40 MHz, so the task continued.**

## 1. The pre-registration (`link_l2_preregistration.txt`, sha256 `cc755e1b…`)

Written at 18:22 EDT, before any hold, air sample or score of this task.
It records the access check above.

- **The rule is LINK-L1's, copied verbatim** from LINK-L1's
  pre-registration (sha256 `02a0e047…`):
  - six holds, one per local 4-hour block, ≥ 30 min idle before each;
  - STILL MET ≥ 5 of 6;
  - TIME OF DAY = every miss inside one contiguous ≤ 12-hour window, with
    ≥ 2 meets and ≥ 2 misses, judged on each hold's PLAYING time in local
    hours;
  - MOVED ≤ 1 meet;
  - otherwise MIXED.
- **What it adds:**
  - **adaptive bitrate in shadow for every hold**, through the D1
    per-session disable route called after PLAYING;
  - the exclusion and one re-run of any hold where shadow was not
    confirmed or the controller acted;
  - the frame-size columns and the side-by-side, both reported only.
- **One harness smoke before H1**: a 60-s session (`smoke/`), not a hold.
  - The disable route answered ok. The status then read `shadow` /
    `acts false` with 0 transitions to the end.
  - The teardown came back live by default, with the APK confirmed and 0
    banners.
  - The smoke ended at 18:24 EDT, 2 h 16 min before H1.

**The harness** (headers in each script):

- C5-M4A's `c5_m4a_hold.sh` / `c5_m4_run.sh`, copied as `link_l2_hold.sh` /
  `link_l2_run.sh`, with three changes:
  - the hold's name is an argument;
  - LINK-L1's 30-min cold start;
  - the disable step after the "at PLAYING" profile check (which requires
    mode `live`, so each new session read live before its own disable).
- `link_l2_day.sh` is LINK-L1's day-driver pattern.
- `link_l2_valid.py` checks the shadow clause.
- `link_l2_air.py` is `link_l1_air.py` plus counts by 40 MHz pair.
- The helpers are byte-identical copies of C5-M4A's (`t2_sample.py`,
  `c5_m4_sampler.py`, `c5_m4a_counter.sh`).

## 2. The six holds (`runs/`, `score.txt`, `score.json`)

**How they ran.**

- Attract mode, zero input, Tekken 3.
- The adopted profile `native_game_720p60_reference` at 7000;
  `any_override` false.
- **The 4x PS1 source**: the capture target was 1920×1080 on every hold.
- In the manager, no `PRIVYHUB_*`. In the environ, exactly the live
  default.
- T2 at 10 s, the air loop at 30 s.
- **Every hold was VALID** (`runs/validity.txt`):
  - the disable answered ok;
  - the status read `shadow` / `acts false` after it and at the end of
    the hold;
  - 0 transitions;
  - 0 acted rows in the decision log.
- No retry, re-run or exclusion was needed.
- **Every teardown left:**
  - the unit restarted, live by default (mode live / acts true);
  - manager empty, stream 7000, no game;
  - the counter override cleared;
  - APK `de072762…835e` confirmed;
  - the stale NOW PLAYING banner cleared by one force-stop and relaunch,
    leaving 0.

**One harness defect, found and handled.** H4's decision-log slice came
out **empty**.

- The cause: the companion rotated `adaptive_bitrate_shadow.jsonl` (4 MiB)
  at 08:50, mid-hold, and the harness slices the log by byte offset.
- So H4's first validity check passed on 0 rows. That pass was vacuous.
- The fix: the hold's rows were recovered by time from the rotated and
  live files (`link_l2_recover_decision_log.py`: 701 rows, the shape of
  the other holds). They were checked again: **VALID**, with 0 acted rows
  and 0 transitions.
- The empty slice is kept as `decision_log_H4.byteslice_empty.jsonl`.
- H5 and H6 could not rotate: the live log was at 188 KB.

**Local times** are EDT (UTC−4), as `runs/clock_H*.txt` records.

| hold | local start | block | UTC PLAYING | spikes/min | fps | stale/min | **loss/min** | underruns/min | **max gap ms** | onn link (median) | Opal signal | tx retries / hold | retry % | channel util. mean (max) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| H1 | 10-01 20:41 | 20-24 | 00:41:09 | 40.8 | 59.81 | 1.32 | **20.80** ✗ | 2.84 | 219 | 150 | −71 | 241,278 | 14.9 | 22.6 (31.0) |
| H2 | 10-02 00:40 | 00-04 | 04:40:59 | 30.5 | 59.95 | 0.60 | **1.64** ✓ | 1.19 | 225 | 180 | −69 | 8 | 0.0 | 7.75 (13.3) |
| H3 | 10-02 04:40 | 04-08 | 08:40:53 | 39.8 | 59.91 | 1.39 | **9.47** ✓ | 1.54 | 201 | 135 | −74 | 119,857 | 7.4 | 5.73 (23.3) |
| H4 | 10-02 08:41 | 08-12 | 12:41:02 | 40.0 | 59.88 | 0.84 | **12.84** ✗ | 0.35 | 109 | 135 | −75 | 278,193 | 17.2 | 3.56 (6.8) |
| H5 | 10-02 12:40 | 12-16 | 16:40:56 | 47.8 | 59.90 | 0.99 | **13.21** ✗ | 0.30 | 192 | 120 | −73 | 147,009 | 9.1 | 5.38 (16.6) |
| H6 | 10-02 16:41 | 16-20 | 20:41:05 | 45.3 | 59.91 | 0.99 | **11.49** ✗ | 0.35 | 114 | 135 | −76 | 161,566 | 10.0 | 3.98 (6.8) |

**The other rows.**

- Spikes, fps, stale and underruns are met on all six.
- **The max output gap (≤ 100) is met on none** (109-225). LINK-L1 met it
  on one.

**The decision log** (the shadow's view): per hold, 1 `controller_start`,
1 `disabled`, 80-142 `state` rows and 4-5 `session_ended_reset`.

- There were **0 `transition`, `would_act`, `refused` or `hold`** rows.
- A disabled live controller logs `would_act` where it would have logged
  `transition` (`companion/adaptive_bitrate_live.py:397`). So the
  controller, had it been acting, would have made no decision on any
  of the six.

## 3. Classification: **TIME OF DAY as scored — on the boundary**

**How it was scored.** `link_l2_score.py` carries LINK-L1's
`shortest_arc` / `in_arc` / `classify` unchanged (diffed) and LINK-L1's
`local_hour` (hour + minute).

**What it gives:**

- **2 of 6 meet**: H2 00:40 and H3 04:40. **4 miss**: H4 08:41, H5 12:40,
  H6 16:41 and H1 20:41.
- STILL MET (≥ 5) and MOVED (≤ 1) do not apply.
- The shortest arc holding every miss runs **08:41 → 20:41, 12.00 h**,
  which is ≤ 12. Both meets lie outside it, and there are ≥ 2 meets and
  ≥ 2 misses. **TIME OF DAY.**

**The margin, stated plainly.**

- The misses' arc is exactly the rule's limit at the scorer's minute
  resolution.
- With seconds, H4's PLAYING is 08:41:02 and H1's is 20:41:09: an arc of
  **12 h 0 min 7 s**, just over the limit. By the same rule the day would
  then read **MIXED** (2 meets, not ≤ 1).
- The pre-registration says "PLAYING time in local hours" without a
  resolution, and the scorer it adopted verbatim uses minutes.
- This record reports the scored class and does not re-score at another
  resolution after seeing the data. **Read it as TIME OF DAY by 7
  seconds.** The schedule (:40 slots, 4 h apart) put any four
  consecutive misses on the boundary by construction.

## 4. Side by side with LINK-L1 (reported; the classification above is this day's alone)

| block | LINK-L1 (80 MHz, 1x, adaptive off) | loss/min | max gap | retries (%) | onn link | LINK-L2 (40 MHz, 4x, shadow) | loss/min | max gap | retries (%) | onn link |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | --- | ---: |
| 00-04 | H4 10-01 00:40 | **3.16** ✓ | 93 | 56,222 (3.5) | 260 | H2 10-02 00:40 | **1.64** ✓ | 225 | 8 (0.0) | 180 |
| 04-08 | H5 10-01 04:40 | **7.54** ✓ | 108 | 213,538 (13.2) | 292 | H3 10-02 04:40 | **9.47** ✓ | 201 | 119,857 (7.4) | 135 |
| 08-12 | H6 10-01 08:41 | 16.78 ✗ | 255 | 109,566 (6.8) | 260 | H4 10-02 08:41 | 12.84 ✗ | 109 | 278,193 (17.2) | 135 |
| 12-16 | H1 09-30 12:40 | 37.27 ✗ | 204 | 100,212 (6.2) | 195 | H5 10-02 12:40 | 13.21 ✗ | 192 | 147,009 (9.1) | 120 |
| 16-20 | H2 09-30 16:40 | **4.25** ✓ | 171 | 75,502 (4.7) | 260 | H6 10-02 16:41 | 11.49 ✗ | 114 | 161,566 (10.0) | 135 |
| 20-24 | H3 09-30 20:40 | 15.19 ✗ | 310 | 111,300 (6.9) | 195 | H1 10-01 20:41 | 20.80 ✗ | 219 | 241,278 (14.9) | 150 |
| **day** | | **3/6**, median 11.37 | ≤ 100 on 1 | median 104,889 | 260 | | **2/6**, median 12.17 | ≤ 100 on 0 | median 154,288 | 135 |

**What the two days share.**

- **The 00-04 and 04-08 holds met on both days** (4 of 4).
- 08-12 and 20-24 missed on both (4 of 4).
- They differ at 12-16, a 37.27 miss then 13.21 now, and at 16-20, a
  4.25 meet then 11.49 now.
- LINK-L1's history (36 holds) had 00-04 at 5/7 (median 4.87, but a 32.68
  in it) and no 04-08 holds before its H5.

**What the width did, as far as one day shows.**

- **The loss is no better**: 2/6 against 3/6, median 12.17 against 11.37.
  The worst hold is milder (20.80 against 37.27). The max gap is no
  better.
- **The onn's link rate halved** (median 135 against 260 Mbit/s), as a
  40 MHz channel would.
- **The retries are not lower** (median 154k against 105k), and they still
  do not order the holds.
  - H3 met at 120k while H6 missed at 162k.
  - H2's 8 retries are the one near-zero hold: it met at 1.64, the day's
    best.
- **This is two days, one per width.** The width, the source (1x → 4x) and
  the date all changed together. This record does not attribute the
  difference, or its absence, to the width.

**The frame-size columns** (C5-M4's formulas, per hold; `score.txt`):

| | per-s largest frame p50 / p90 / max (B) | cap hits s/min | ≥ 80-pkt frames/min |
| --- | --- | ---: | ---: |
| LINK-L1, 1x source (median of 6) | 47,845 / 86,311 / 89,498-89,885 | 9.8 | 0 |
| LINK-L2, 4x source (median of 6) | 49,622 / 86,906 / 89,408-89,608 | 9.9 | 0 |

The 4x source adds about 1.8 KB (+4 %) to the median per-second peak and
0.6 KB to the p90. Cap hits are the same, and there are no ≥ 80-packet
frames, as C5-M4A's V5 read. **It is too small to account for a
day-level difference.**

## 5. The air view, then and now (`air.jsonl`, `air_loop.jsonl`, `air_table.txt`)

**How it was read.**

- Read-only, `ssh opal`: `iw` info, survey and station dumps, and the GL
  daemon's **cached** scan list, with no scan triggered.
- Counts only, with identifiers never written.
- The salted-hash and endpoint files in `/tmp` were deleted.
- **12 snapshots**: at the start of each hold, between holds and after H6.
  Plus 44 loop rounds per hold, with 0 errors after the access check.

| | LINK-L1 (09-30/10-01, 80 MHz) | LINK-L2 (10-01/02, 40 MHz) |
| --- | --- | --- |
| channel / width | 36 / 80 | 36 / **40** |
| idle utilization (snapshots) | 3.3 % (one 0.0, one 10.0) | **0.0-3.4 %**; 23.3 and 16.6 at 20:40 / 22:40 on 10-01 |
| streaming utilization (loop mean per hold) | 6.0-10.4 % | **3.2-7.7 %**; H1 **22.8 %** (max 43.3) |
| noise | −89 / −90 | −88 / −90 |
| the onn at the Opal (signal) | −71 to −75 | −69 to −77; −73 to −77 from 06:40 on (−69 to −74 before) |
| the onn's link rate (T2, median per hold) | 195-292 | **120-180** |
| Opal → onn tx rate / MCS (station dump) | 90-351 Mbit/s, MCS 1-4 | **6.5 Mbit/s, MCS 0 at every sample**: see below |
| onn → Opal rx rate / MCS | 195-293, MCS 4-6 | 120-150, MCS 5-7 |
| 5 GHz entries in the cached list | 3-7 | 3-7 |
| on primary 36 | 0 | **0** |
| in the in-use 80 MHz block 36-48 (≥ −70 dBm) | 3-5 (3-4) | 3-7 (3-4) |
| in the in-use **40 MHz pair 36-40** (≥ −70) | — | **0 (0) at every snapshot** |
| in the **44-48 pair** (≥ −70) | (not split) | **3-7 (3-4)**: every neighbour of the block |
| 52-64 | 0 | **0** |
| set changes between snapshots | +1..+9 / −0..−6 | +2..+7 / −0..−9 (live) |

**What it says.**

- **The width change did what it was meant to, by count.** The strong
  neighbours LINK-L1 found on the 80 MHz block's secondaries all sit on
  44-48. Nothing is on 36 or 40, so the 40 MHz channel no longer
  overlaps them.
  - **The loss row did not improve with it.** So on this day, sharing
    secondaries with those neighbours does not look like what drives the
    misses.
  - That is one day. It narrows the question; it does not settle it.
- **H1 ran with more than the stream on the channel.** Utilization was
  23.3 % at its snapshot and 22.8 % mean during it (the other holds read
  3.2-7.7 %), with 16.6 % idle two hours later. H1 was the day's worst
  hold (20.80).
  - LINK-L1's worst (37.27) read 6.7 %. As before, utilization does not
    order the rest.
- **The Opal's reported tx rate is not the data rate at 40 MHz.**
  - From the width change on, `station dump` reported "6.5 MBit/s, MCS 0"
    for the onn at every one of 277 samples (12 snapshots, 264 loop rounds, the access check), with no width field.
  - The stream carried 7.09-7.18 Mbit/s at 59.8-59.95 fps through it, which a 6.5
    Mbit/s PHY rate cannot. The field shows a fixed basic rate here, not
    the data frames' rate.
  - So the tx MCS columns (and LINK-L1's post-hoc MCS-1 share) **cannot be
    compared across the two days**.
  - The rx rate (onn → Opal: MCS 5-7 at 120-150) and the onn's own link
    rate are comparable, and both are about half of LINK-L1's, as the
    width predicts.
- **The tx retries counter tracks tx failed almost one-for-one** on both
  days (e.g. H4 282,237 / 282,241). It is reported as it reads; it does
  not order the holds on either day.

## 6. What it means for the user — options, not a decision

The day is **TIME OF DAY as scored, on the boundary by 7 seconds**. Both
readings are laid out.

**TIME OF DAY (as scored).**

- **The window:** the misses lie in **08:41-20:41 local**. The meets were
  at **00:40 and 04:40**.
- The quiet stretch is **after about 21:00 and before about 08:30**,
  sampled by exactly two holds. H1 at 20:41 missed at its edge, and
  LINK-L1's H3 at 20:40 missed too.
- So a screening night would go in **00:00-08:00**:
  - Part 2's 1080p-rung screening would be scheduled there, with
    INCONCLUSIVE (link) nights read against it;
  - LINK-L1 also met at 00:40 and 04:40 (4 of 4 over the two days);
  - but the history's 00-04 block holds a 32.68 (C5-M3's re-run B3), so
    the window lowers the odds of a link miss; it does not remove them.

**MIXED (the second-resolution reading).**

- No change from the width. The levers left, each with what the air view
  says:
  - **The channel.** 52-64 read 0 neighbours at every snapshot on both
    days. 36/40 is clear now too, but the loss did not follow. 52-64 is
    DFS: radar checks and possible channel moves are the trade-off.
  - **The onn's placement.** The signal at the Opal sagged to −75/−77 in
    this day's second half, where the misses were. But RSSI has not
    ordered loss across nights (+0.02 over LINK-L1's history).
  - **A wired hop**, to an access point next to the onn or to the onn
    itself. It is the one lever that removes the 5 GHz hop rather than
    moving it.

**On the width itself, under either reading.**

- 40 MHz did not improve the row: 2/6 against 3/6, the max gap no
  better.
- It halved the link rate the 7 Mbit/s stream sits on, without cost
  visible in these rows. A 1080p rung (about 2.25× the frame size, C5-M1)
  would use more of that rate.
- **Whether to keep 40 MHz or revert to 80 is the user's call, by hand.**
  This day does not show 40 MHz as worse in the MOVED sense (it is not
  ≤ 1 of 6).

## Files (`link_l2_2026-10-02/`)

- **Pre-registration:** `link_l2_preregistration.txt` (+ `.sha256`).
- **The harness:**
  - `link_l2_day.sh`, `link_l2_hold.sh`, `link_l2_run.sh`;
  - `link_l2_valid.py`, `link_l2_air.py`;
  - `t2_sample.py`, `c5_m4_sampler.py`, `c5_m4a_counter.sh` (copied);
  - `link_l2_recover_decision_log.py` (written after H4);
  - `day.log`.
- **The smoke:** `smoke/` (S0).
- **The holds:** `runs/`. Per hold: `armcheck`, `disable`,
  `abr_after_disable`, `status_end`, `status`, `report`, `decision_log`,
  `frames`, `heartbeat`, `companion` (redacted), `alpha`, `*_host`,
  `*_telemetry`, `*_title`, `surfaceflinger`, `hold_H*_try0.log`,
  `clock_H*.txt`. Shared: `index.txt`, `validity.txt`, `t2_samples.jsonl`.
- **Scores:** `link_l2_score.py` → `score.txt` / `score.json`;
  `link_l2_air_table.py` → `air_table.txt`.
- **Air:** `access_check.jsonl`, `air.jsonl`, `air_loop.jsonl`.
- **End state:** `link_l2_final_state.txt`:
  - manager empty; the environ exactly the live default; mode live,
    acts true;
  - stream 7000, `any_override` false, no game;
  - APK `de072762…835e`; the counter override absent; no samplers;
    `/tmp` cleaned.
- **Checks:** `sha256_manifest.txt`; `redact_check.txt` (`link_l2_redact_check.py`: 106 PASS, the rest FLAG on loopback / bind / the core version only, 0 FAIL).

No code changed. Nothing was written outside `docs/memory/` and `logs/`
(the companion's own logs, and `logs/link_l2_git_status.txt`). Nothing
was adopted, and nothing was committed.
