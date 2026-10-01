---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: 4e45a4f
status: LINK-L1 DONE — the day is MIXED by the pre-registered rule (3 of 6 holds meet loss < 10/min; the misses at 12:40, 20:40 and 08:41 local bracket a meet at 16:40, so no <= 12 h window separates them). Six 20-min holds on the adopted profile at 7000, adaptive off, any_override false, APK de072762…835e, one per local 4-hour block, 4 h apart, 2026-09-30 12:40 to 2026-10-01 08:41 EDT; loss 37.27 / 4.25 / 15.19 / 3.16 / 7.54 / 16.78 per min; max gap met (≤ 100) on H4 only. History since D-BASE (36 holds): 16 meet, every 4-hour block has both meets and misses. Air view read-only: channel 36 / 80 MHz unchanged, idle utilization 3.3 % (O1: 2.9-3.3), noise −89/−90, 3-5 neighbour BSSIDs in the in-use 80 MHz block and 0 on primary 36. No conclusion drawn (MIXED); nothing committed
---

# LINK-L1 — the adopted 720p's loss row, looked at

Task: `handoffs/LINK-L1_LOSS_ROW_LOOK_AND_LIVE_DEFAULT_TASK.md`, Part A,
under `handoffs/QUEUE_2026-09-29B.md`'s rules. The user's authorization,
2026-09-30: "do the loss row look first and then the live default".

**The question.** On the adopted profile with adaptive off, does
post-FEC video loss < 10/min still hold? If not, does it depend on the
time of day?

**The pre-registration**
(`link_l1_2026-10-01/link_l1_preregistration.txt`, sha256 `02a0e047…`)
was written and hashed at 15:59Z on 2026-09-30, before any hold, air
sample or history figure.

- One access check came before it: `iw dev` (the channel line) and the
  shape of the cached scan list, with no counts kept.
- It took one access-test snapshot to `/tmp`, which is not used here.

## Classification: **MIXED**

- **3 of 6 holds meet** loss < 10/min.
- **STILL MET** (≥ 5) and **MOVED** (≤ 1) do not apply.
- **TIME OF DAY** does not apply either.
  - The misses are at 12:40, 20:40 and 08:41 local.
  - The shortest arc that holds all three runs from 08:41 to 20:40
    (12.0 h), and it contains the meet at 16:40 (H2). The other arc is
    16 h.
  - So no ≤ 12-hour window separates the misses from the meets.
- By the rule, MIXED is reported with the table, and **no conclusion is
  drawn.**
- After H5 the day could no longer reach STILL MET or TIME OF DAY,
  whatever H6 did. H6 ran anyway, as pre-registered.

## A3 — the six holds (`runs/`, `score.txt`, `score.json`)

**How they ran.**

- CL-B1's harness, copied byte-identical (`cl_b1_night.sh`,
  `c5_m2_run.sh`, `t2_sample.py`).
- One hold per invocation, driven by `link_l1_day.sh`, with
  `EXPECT_SHA` set to the adopted APK and `COLD_MIN=30`.
- Every hold:
  - ran on the adopted profile at 7000, `any_override` false, adaptive
    `off`, with 0 `PRIVYHUB_*` in the manager and the companion's
    environ;
  - had the profile check AS EXPECTED both before the launch and at
    PLAYING;
  - ran with T2 at 10 s and the air loop at 30 s.
- **Every teardown** left 0 `PRIVYHUB_*`, the profile adopted at 7000, no
  game and the APK `de072762…` confirmed.
  - The stale NOW PLAYING banner showed after each hold. The harness
    cleared it with one force-stop and a relaunch, leaving 0.
- No retries were needed, and none of the six was NOT RUN.
- The local clock is America/New_York (EDT, UTC−4), as `clock_H*.txt`
  records.

| hold | local start | block | UTC PLAYING | spikes/min | fps | stale/min | **loss/min** | underruns/min | **max gap ms** | onn link (median) | Opal signal | tx MCS (median) | tx retries / hold | retry % | channel util. mean (max) |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| H1 | 09-30 12:40 | 12-16 | 16:40:54 | 25.3 | 59.89 | 0.79 | **37.27** ✗ | 0.69 | 204 | 195 | −74 | 1 | 100,212 | 6.2 | 6.70 (10.0) |
| H2 | 09-30 16:40 | 16-20 | 20:40:55 | 30.4 | 59.95 | 0.94 | **4.25** ✓ | 0.54 | 171 | 260 | −72 | 3 | 75,502 | 4.7 | 6.44 (10.0) |
| H3 | 09-30 20:40 | 20-24 | 00:40:55 | 28.1 | 59.91 | 0.45 | **15.19** ✗ | 0.59 | 310 | 195 | −74 | 1 | 111,300 | 6.9 | 6.46 (6.8) |
| H4 | 10-01 00:40 | 00-04 | 04:40:59 | 26.1 | 59.95 | 0.74 | **3.16** ✓ | 0.49 | **93** | 260 | −73 | 3 | 56,222 | 3.5 | 6.61 (6.8) |
| H5 | 10-01 04:40 | 04-08 | 08:40:59 | 27.2 | 59.92 | 0.94 | **7.54** ✓ | 0.60 | 108 | 292 | −74 | 3 | 213,538 | 13.2 | 7.05 (10.3) |
| H6 | 10-01 08:41 | 08-12 | 12:41:01 | 39.2 | 59.89 | 1.78 | **16.78** ✗ | 0.94 | 255 | 260 | −75 | 2 | 109,566 | 6.8 | 11.15 (36.6) |

**The other close-out rows.**

- Spikes, fps, stale and underruns are met on all six holds.
- The **max output gap (≤ 100)** is met on **H4 only**. It is the
  transport's open row, as it has been since the close-out (163 / 110
  then).

**The retries do not order the holds.**

- H5 met the loss row at the day's *highest* retry count (213k, 13.2 %).
- H1 missed it worst at 100k (6.2 %).
- This repeats C5-M2's correction.

## A1 — the history since D-BASE closed (`history.txt`, `history.json`)

**What is in it.** Every ≥ 15-min hold on the adopted profile with
adaptive off or silent: **36 holds**, 2026-09-23 to 2026-09-30.

- The close-out's C and W.
- CTRL-L1's C, W1 and W2.
- The C3-L4-S1 shadow night's H1-H4 (the shadow is silent by
  construction). The handoff's "S3" is read as this night;
  `D-BASE-S3` (2026-09-22) predates the close and the adopted cushion and
  redundancy.
- C4-M1's B1-B3.
- The live-but-silent 30-min holds: L1 A, N1 H and N2 H.
- C5-M1, C5-M2 (nights 1 and 1r) and C5-M3 (night and re-run) B holds.
- CL-B1's N1 and O1.

**What is excluded, with the reason** (in the script):

- L1 B and L2 B2: the controller acted.
- C3.L3a R2-R4: the probe's transitions.
- The `nft` nights: the faults.
- The non-adopted arms.
- Everything before the close.

**Loss/min by local 4-hour block (EDT):**

| block | n | median | min | max | meets < 10 |
| --- | ---: | ---: | ---: | ---: | --- |
| 00-04 | 7 | 4.87 | 3.16 | 32.68 | 5/7 |
| 04-08 | 0 | — | — | — | — |
| 08-12 | 2 | 11.05 | 10.29 | 11.81 | 0/2 |
| 12-16 | 6 | 9.52 | 3.11 | 33.99 | 3/6 |
| 16-20 | 15 | 9.17 | 1.04 | 24.97 | 8/15 |
| 20-24 | 6 | 20.55 | 2.88 | 47.21 | 2/6 |

**By local date:**

| date | n | median | min | max | meets |
| --- | ---: | ---: | ---: | ---: | --- |
| 09-23 | 2 | 8.53 | 8.40 | 8.67 | 2/2 |
| 09-24 | 8 | 9.08 | 2.88 | 24.01 | 5/8 |
| 09-25 | 2 | 4.67 | 4.47 | 4.87 | 2/2 |
| 09-28 | 4 | 5.68 | 3.11 | 11.25 | 3/4 |
| 09-29 | 13 | 18.62 | 1.04 | 47.21 | 3/13 |
| 09-30 | 7 | 10.29 | 3.16 | 32.68 | 3/7 |

**What the table shows.**

- The adopted 720p met its loss row on **16 of 36** holds since the
  close. It met on every hold of 09-23 and 09-25, and on 3 of 4 on
  09-28. It met on only 3 of 13 on 09-29 and 3 of 7 on 09-30.
- **Every block that has more than two holds has both meets and
  misses.** The 00-04 block is the best (5/7, median 4.87), and 20-24 the
  worst (2/6, median 20.55). But both contain the other outcome:
  - 00-04 has C5-M3 re-run B3 at 32.68;
  - 20-24 has C4-M1 B1 at 2.88.
- **The loss is wide inside an hour, not only between days.** C5-M3's
  re-run held 3.16, 5.84, **32.68** and 4.12 in consecutive 40-minute
  slots.

**What it cannot show.**

- **The sample is evenings-heavy.** Fifteen of 36 holds are in 16-20 and
  none in 04-08 (this day's H5 is the first). The blocks are not
  comparable samples.
- **Dates and blocks are confounded.** The 00-04 meets are mostly
  C5-M3's re-run and C4-M1's night.
- **The radio counters do not separate meets from misses across
  nights.**
  - Tx retries per hold track loss weakly over the 36 (Spearman +0.45;
    retry share +0.53). But C5-M3's misses ran at 66-81k retries and its
    meet at 77k, and this day's best-but-one hold ran at 213k. This is
    C5-M2's correction again: **retries did not predict loss across
    nights**.
  - The onn's link rate: −0.09.
  - RSSI: +0.02.
- **Channel utilization was never sampled** in those runs. T2 does not
  read it.

**Post hoc, not pre-registered** (`link_l1_mcs_posthoc.py`,
`mcs_posthoc.txt`).

- Within this day the misses spent more of the hold with the Opal
  sending to the onn at MCS 1: 92 %, 62 % and 45 % for the misses,
  against 35 %, 23 % and 7 % for the meets. Spearman over the six is
  +0.77.
- **Over the 36 history holds it is −0.05.** 7 of 21 holds at ≥ 50 % MCS
  1 met, and 11 of 15 below 50 % met.
- So the day's ordering does not carry across nights, like the retries
  before it. It is recorded so that nobody rediscovers it as a
  predictor.

## A2 — the Opal's air view, read-only (`air.jsonl`, `air_loop.jsonl`, `link_l1_air.py`)

**How it was read.**

- `ssh opal`, read-only, with `iw dev wlan1 info`, `survey dump` and
  `station dump`, `iw dev wlan0 info` and `/proc/loadavg`.
- For the neighbour counts: `ubus call repeater scan {"cached":true}`,
  the GL repeater daemon's cached scan list, read without triggering a
  scan.
- **Nothing was set, committed, installed or written on the Opal.**
- **Counts only**:
  - SSIDs and BSSIDs were counted in memory and never written;
  - the onn's hardware address was held in memory only, to find its
    station row;
  - the "set changed" counts came from a salted hash in `/tmp`, deleted
    at the end.

**Twelve snapshots**: before H1, at the start of each hold, between each
pair and after H6. Plus a 30 s loop during each hold, 40 rounds per hold,
0 errors.

| snapshot (local) | util % | noise | onn signal / MCS | 5 GHz entries | on primary 36 | in the 36-48 80 MHz block (≥ −70 dBm) | adjacent block 52-64 | 2.4 GHz entries (same ch. 1) | 2.4 util % | +added / −removed |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: | --- | ---: | --- |
| B0 09-30 12:01 | 3.3 | −90 | −74 / 1 | 5 | 0 | 5 (3) | 0 | 11 (3) | 20.0 | (vs access test) |
| H1 12:40 | 3.3 | −90 | −74 / 1 | 3 | 0 | 3 (3) | 0 | 12 (6) | 26.6 | +5 / −6 |
| btw 14:40 | 3.3 | −90 | −71 / 1 | 3 | 0 | 3 (3) | 0 | 9 (4) | 30.0 | +1 / −4 |
| H2 16:40 | 3.3 | −89 | −71 / 3 | 3 | 0 | 3 (3) | 0 | 9 (4) | 30.0 | +4 / −4 |
| btw 18:40 | 3.3 | −90 | −72 / 2 | 4 | 0 | 4 (4) | 0 | 16 (8) | 40.0 | +9 / −1 |
| H3 20:40 | 3.3 | −90 | −74 / 2 | 4 | 0 | 4 (4) | 0 | 13 (6) | 26.6 | +2 / −5 |
| btw 22:40 | 3.3 | −89 | −73 / 1 | 4 | 0 | 4 (4) | 0 | 12 (6) | 23.3 | +1 / −2 |
| H4 10-01 00:40 | 3.3 | −90 | −72 / 1 | 4 | 0 | 4 (4) | 0 | 11 (5) | 30.0 | +1 / −2 |
| btw 02:40 | 3.3 | −90 | −74 / 1 | 3 | 0 | 3 (3) | 0 | 11 (3) | 76.6 | +5 / −6 |
| H5 04:40 | 0.0 | −89 | −74 / 1 | 5 | 0 | 3 (3) | 0 | 10 (4) | 23.3 | +4 / −3 |
| btw 06:40 | 3.3 | −90 | −74 / 2 | 3 | 0 | 3 (3) | 0 | 11 (2) | 20.0 | +3 / −4 |
| H6 08:40 | 3.3 | −90 | −74 / 4 | 5 | 0 | 5 (3) | 0 | 8 (3) | 26.6 | +4 / −5 |
| after H6 09:02 | 10.0 | −89 | −75 / 3 | 7 | 0 | 5 (3) | 0 | 12 (5) | 20.0 | +6 / −0 |

**What it says.**

- **The channel is where O1 left it.** 36 at 80 MHz (`iw dev`), tx power
  23 dBm, one 5 GHz station. Idle utilization reads 3.3 %, one quantum of
  the 30 ms window (O1: 2.9-3.3 % idle). Noise is −89 to −90 dBm (O1: −89
  to −90).
- **Streaming utilization.** H1-H5 means were 6.44-7.05 % (O1: 6.86 and
  6.90). **H6 was the exception**: mean 11.15 %, max 36.6 %, with more
  than the stream on the channel that morning. But H1, which missed
  worst, read 6.70 %.
- **The onn's signal** at the Opal was −71 to −75 dBm (O1: −70 to −71).
  That is 2-4 dB weaker than O1's evening, though the medians during the
  holds (−72 to −75) do not order the holds.
- **Neighbours, as counts.**
  - On primary 36: **0** at every snapshot.
  - In the in-use 80 MHz block (36-48): **3-5**, of which **3-4 are at ≥
    −70 dBm** at the Opal. These are strong neighbours sharing the 80 MHz
    block on its secondary channels.
  - The adjacent block (52-64): **0**.
  - On 2.4 GHz: 8-16 entries, 2-8 on channel 1. The Opal's 2.4 GHz radio
    is not on the stream's path. Its utilization ran 20-77 %.
  - The cached set changed between every pair of snapshots (+1 to +9 /
    −0 to −6), so the daemon refreshes it. It is a live view, not a stale
    one.
- **Compared with O1 (2026-09-21).** O1 did not count neighbours; it read
  no scan list. So "what is on the channel now that was not then" cannot
  be answered as counts: there is no O1 count to subtract.
  - What can be compared is unchanged: channel, width, idle and streaming
    utilization, noise. The signal is 2-4 dB weaker.
  - What is new is the count itself: 3-4 strong BSSIDs in the 80 MHz
    block, none on 36.

## What each classification would mean for the user — options, not a decision

The day is **MIXED**: no conclusion is drawn from it. For completeness,
the four readings the task asked for:

- **STILL MET** (not this day): nothing to do; the recent evenings were
  the outliers.
- **TIME OF DAY** (not this day): screening nights would be scheduled in
  the quiet window, and INCONCLUSIVE (link) nights read against it. On
  this day and the history there is **no window to name**. The best
  block, 00-04 (5/7 history, H4 3.16), also holds a 32.68.
- **MOVED** (not this day): the baseline would need re-establishing
  before any further arm is judged.
- **MIXED (this day).** The loss row is met on about half the holds, at
  every hour sampled: 3/6 today and 16/36 since the close. The misses are
  bursts inside a hold, not a level that moves by clock. Practically:
  - an arm judged on this link against the < 10 row will keep coming back
    INCONCLUSIVE (link) about half the time, whenever it runs;
  - the close-out's 8.7 / 8.4 were two holds from one evening that
    happened to meet.

**The levers, all the user's, with what the air view says about each:**

- **The Opal's channel.** Primary 36 is clear (0 BSSIDs), but the 80 MHz
  block shares its secondaries with 3-4 strong neighbours. The adjacent
  block 52-64 is empty in the cached list.
  - UNII-3 (149-161) is on the Opal's allowed list. Its count is not
    split out here: 0-2 entries outside the two blocks above.
  - **Read-only to Code.**
- **The width.** 80 → 40 MHz on 36/40 would step off the secondaries
  where the strong neighbours sit (44/48 or 40/44/48; the counts do not
  split them further). O1 also named 40 MHz as the one width change with
  a rationale: more per-MCS robustness at −70 dBm, for ceiling the 7 Mbps
  stream does not use.
  - **Read-only to Code.**
- **The onn's placement.** The signal at the Opal is −71 to −75 dBm, 2-4
  dB weaker than O1's evening. MCS 1-3 is a mediocre link. Placement buys
  margin, but on the history neither RSSI (+0.02) nor the MCS share
  (−0.05) predicts the loss across nights.
- **A wired hop** (wired to an access point next to the onn, or wired to
  the onn) takes the 5 GHz hop out entirely. It is the one lever that
  removes the variable rather than moving it.

## Files (`link_l1_2026-10-01/`)

- **Pre-registration:** `link_l1_preregistration.txt` (+ `.sha256`).
- **The harness:**
  - `cl_b1_night.sh`, `c5_m2_run.sh`, `t2_sample.py`, `c5_m2_score.py`:
    byte-identical copies of CL-B1's;
  - `link_l1_day.sh`: the day driver;
  - `link_l1_air.py`: the air view;
  - `day.log`.
- **The holds:** `runs/` (per hold: `armcheck`, `status`, `report`,
  `frames`, `heartbeat`, `companion` (redacted), `sys`, `surfaceflinger`,
  `night_H*_try0.log`, `clock_H*.txt`; `index.txt`, `t2_samples.jsonl`).
- **Scores:** `link_l1_score.py` → `score.txt` / `score.json`;
  `radio_by_hold.txt`.
- **History:** `link_l1_history.py` → `history.txt` / `history.json`.
- **Post hoc:** `link_l1_mcs_posthoc.py` → `mcs_posthoc.txt`.
- **Air:** `air.jsonl`, `air_loop.jsonl`.
- **Checks:** `sha256_manifest.txt`; `redact_check.txt`.

No code changed for Part A, and nothing was written outside
`docs/memory/` and `logs/` (the companion's own logs).
