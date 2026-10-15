---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5 work)
---

# E4-S3B — the memory floor at 1G, swap off

> **`MemorySwapMax=0`: no swap for the stack's cgroup.** The floor is the
> smallest `MemoryMax=` at which the stack runs with page-cache reclaim
> only; a host with swap would degrade more softly below it. It is a
> floor for the **stack's cgroup** (companion, RetroArch, the encoder,
> the grabber children), not for the host: Xorg, pulseaudio, the desktop
> and the OS are outside it.

**Classification: MEMORY FLOOR CLOSED (four rows), CONC's on a hashed
addendum.**

| row | swap-off memory floor | at the floor (peak; anon / file) |
| --- | --- | --- |
| PS1-STREAM (CPU 200 %) | **≤ 384M** (E4-S3) | 228 MB; 191 / 21 MB |
| SNES-STREAM (CPU 150 %) | **≤ 384M** (E4-S3) | 197 MB; 165 / 19 MB |
| META (CPU 150 %) | **1G** (768M failed, E4-S3; 1G PASS) | 976 MB; 940 / 0.2 MB |
| CONC (CPU unset) | **1536M**, an addendum reading (768M failed, E4-S3; 1G OOM-killed twice before the window; 1536M PASS) | 1,166 MB; 1,088 / 21 MB |

- **The stack's swap-off memory floor is 1536M (1.5G).** It rests on the
  addendum reading for CONC. The true value lies between 1G (fails) and
  1.5G (holds). The steps between were not run.
- At every floor: 0 `memory.high` / `memory.max` events, memory PSI 0, 0
  major faults, 0 swap.
- **The floor is the grabber's.** A grab alone peaks at ~976 MB (META, or
  CONC after its stream was lost). With a stream beside it, CONC peaks at
  ~1,166 MB.
- The pre-registered verdicts stand as judged: control INCONCLUSIVE (link),
  META 1G PASS, CONC 1G INCONCLUSIVE ×2. `--check` OK; 0 replaced attempts.
- The runner's refresh loop now backs off (the tool patch). Every
  `epg.jsonl` stayed at 53-62 KB, including the two runs whose unit was
  OOM-killed.
- Measurement only; nothing adopted, nothing committed.

**Context:**

- Task: `handoffs/E4-S3B_MEMORY_FLOOR_1G_SWAPOFF_TASK.md`, under
  `handoffs/QUEUE_2026-10-10B.md` (queue item 1).
- **Baseline: `7331184` plus the uncommitted E4-S1..S5 work**, untouched
  (no stash, reset, checkout or clean).
- Files: `e4_s3b_2026-10-10/`.
- **Timeline (UTC, 10-10):**

  | time | what |
  | --- | --- |
  | 07:01-07:07 | the tool patch and its two 60-s cycles (`backoff_demo/`) |
  | **07:08:25** | **pre-registration hashed** (`fad9e114…9eaf`) |
  | 07:08-07:32 | the control (PS1-STREAM, unconstrained) |
  | 07:33-07:34 | the driver's control lookup fixed (`ladder_fix.md`; no rule changed) |
  | 07:33-08:21 | CONC and META at 1G |
  | 08:21-08:45 | the CONC repeat at 1G |
  | **08:47:05** | **addendum hashed** (`e4_s3b_addendum.txt`, `f2dae9ce…`; the file on disk and `addendum_hashed_at.txt`; corrected 2026-10-10 by queue C, the record had quoted `7f468f64…` / 08:46:49Z) |
  | 08:47-09:11 | CONC at 1536M (addendum) |

## 1. The tool patch (before the pre-registration)

In `tools/e1_suite.py` (`patches/E4-S3B_RUNNER_REFRESH_BACKOFF.md`, diff
`e4_s3b_tools.diff`), the forced-refresh cycle now backs off when a call
gets no HTTP reply at all (refused, reset, timeout):

- it waits 1 s, doubling to 30 s, until a call is answered;
- each failure streak is written as **one** row, giving the first failure,
  the attempt count and the duration;
- every answered call takes the predecessor's path, unchanged.

The two 60-s cycles it was shown with (`backoff_demo/`):

| cycle | companion | rows written |
| --- | --- | --- |
| predecessor | running | 15 (14 grabs, all HTTP 200; 1 scan) |
| patched | running | 14 (13 grabs, all HTTP 200; 1 scan) — the same kinds and cadence (median grab 4.79 / 4.78 s) |
| **patched** | **stopped** | **2** (one streak: 6 attempts over 31 s; 1 scan) — the bound was ≤ 5 |
| predecessor, 5 s only | stopped | 22,585 |

**In the runs:** each OOM restart of the unit produced one streak row (3
and 4 attempts over 3.0 and 7.0 s).

## 2. The runs

| run | verdict (pre-registered) | run-span kills | what happened |
| --- | --- | --- | --- |
| control, PS1-STREAM unconstrained | INCONCLUSIVE (rendered 59.48; link) | 0 | **loss 218/min**: the link fails D-BASE's row, so the link clause is live |
| CONC, 1G | INCONCLUSIVE | **3** | **OOM-killed at 07:36:01, 47 s before the window**: the stream was lost, and the window ran on the restarted unit with the grab cycle alone |
| META, 1G (CPU 150 %) | **PASS** | 0 | peak 976 MB; 232 grabs, ≥ 38 per channel, 0 failed; the guide served |
| CONC, 1G, repeat | INCONCLUSIVE | **3** | the same: OOM-killed at 08:24:43, 47 s before the window |
| CONC, 1536M (addendum) | **PASS** | 0 | peak 1,166 MB; 242 grabs, 0 failed; RetroArch 59.999, capture 59.99, dup+drop 0.05/min; rendered 58.29 (passes by E4-S1's reference-relative clause), **loss 863/min** |

Tables: `e4_s3b_ladder_table.md` (every gate), `e4_s3b_memory.md` (the
cgroup per run).

### Why CONC at 1G is INCONCLUSIVE as judged, and what the addendum does

- The cycle's first grab starts 30 s after PLAYING. It took the cgroup to
  1G, and the kernel OOM killer killed it, about 45 s before the 20-min
  window opened. The journal reads: "A process of this unit has been killed
  by the OOM killer", then "Failed with result 'oom-kill'", then "restart
  counter is at 1".
- The pre-registered kill gates (`no_oom_kill`, `no_journal_kill`,
  `unit_not_restarted`, E4-S3's verbatim) are **window-scoped**, so all
  three read clean.
- The window itself had no stream: rendered 0.0, and RetroArch, capture and
  dup+drop could not be read. The judge returned INCONCLUSIVE (the link
  clause, plus gates that could not be read). The repeat did the same.
- **No verdict was changed.** The addendum (`e4_s3b_addendum.txt`,
  `f2dae9ce…`, hashed 08:47:05Z before its run, the same second the run's suite started — `addendum_hashed_at.txt`; corrected by queue 2026-10-10C from `7f468f64…` / 08:46:49Z, which matched no file on disk) does three things:
  - reports the **run-span kill reading**: the unit's journal kill lines
    from the idle-gap start to the window's end, on every run (CONC 1G:
    3, 3; all others: 0);
  - runs CONC on up the ladder: 1536M, then 2G only if 1536M did not
    hold;
  - defines "holds" as the pre-registered judge's PASS (or a link-only
    INCONCLUSIVE with every gate readable), with 0 run-span kills.
- 1536M held, so 2G was not run.

## 3. The memory per run

From `cgroup.jsonl`, 5-s samples:

| run | max / peak MB | anon / file at the peak | events high / max / oom_kill | PSI some / full | companion PSS |
| --- | --- | --- | --- | --- | --- |
| control | 227 / 229 | 194 / 21 | 0 / 0 / 0 | 0 / 0 | 39 MB |
| CONC 1G (after its kill) | 971 / 976 | 942 / 0.7 | 0 / 0 / 0 (the counter reset with the restarted cgroup) | 0 / 0 | 34 MB |
| META 1G | 970 / 976 | 940 / 0.2 | 0 / 0 / 0 | 0 / 0 | 33 MB |
| CONC 1536M | 1,147 / 1,166 | 1,088 / 21 | 0 / 0 / 0 | 0 / 0 | 49 MB |

- A grab with no stream sits at ~976 MB, with no page cache left to
  reclaim. At 1G that is 95 % of the limit, and it passed only because no
  stream shared it.
- With the stream's ~230 MB beside it, CONC needs ~1.17 GB: E4-S3's
  "~1.15 GB working set", now measured.

## 4. The alpha's memory line, restated (E4-S3 §3)

| | measured (swap off) | proposed |
| --- | --- | --- |
| a stream alone (PS1 or SNES) | ≤ 384M (≤ 230 MB peak) | — |
| the guide grabber alone (META) | 1G holds (976 MB peak, 0 events; 4.7 % headroom) | — |
| stream + grabber (CONC) | 1G OOM-kills; 1.5G holds (1,166 MB peak, 0 events) | **1.5 GB for the stack, no swap assumed** (E4-S3's proposal, now measured: 1,166 MB × ~1.3 = 1.5 GB) |
| system | — | **8 GB** stands |

- With E4-S4's grab deferral (not adopted), a stream never shares memory
  with a grab. The stack's peak would then be the grab's ~976 MB, and
  1G would hold with ~5 % headroom; 1.25 GB would restore a ~30 % margin.
- **Margin at 1.5 GB:** 1,536 − 1,166 = 370 MB (24 % of the limit, 32 %
  over the peak).

## 5. State at the end; files

- **Final state** (`state_at_end.json`, 09:12Z):
  - the four adopted lines; no `e4_constraint.conf`;
  - every constrained run's properties read back infinity / max at its
    teardown;
  - no `e3_flag.conf`; no game; the PS1 files identical; **APK
    CONFIRMED**.
- **Read back under load** (`runs/constraint_readback.jsonl`, every 60 s):
  `memory.max` / `memory.swap.max` held the step's values in every row
  while its run was live.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
- E4-S3's driver was copied (`e4_s3b_ladder.py`), not run in its
  directory.
- **Files** (`e4_s3b_2026-10-10/`):
  - `precondition.json`, `git_status_at_start.txt`,
    `tools_predecessor_sha256.txt`, `tools_at_preregistration_sha256.txt`,
    `e4_s3b_tools.diff`, `backoff_demo/` (the demo script, the
    predecessor copy, the four cycles' rows and results);
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`;
  - the addendum + `.sha256` + `addendum_hashed_at.txt`,
    `e4_s3b_addendum_run.py`, `addendum.json`;
  - the drivers:
    - `e4_s3b_ladder.py` (fixed);
    - `e4_s3b_ladder_as_preregistered.py`;
    - `e4_s3b_ladder_vs_e4_s3.diff`;
    - `ladder_fix.md`;
    - `readback_standin.py`;
    - `resume_after_suite.sh`;
  - `ladder.json` and the console logs;
  - `runs/` (5 runs, `manifest.sha256` (86 files), `check.txt` OK,
    `final_state*.json`, `constraint_readback.jsonl`);
  - `e4_s3b_analysis.py`, `analysis_console.txt`,
    `e4_s3b_ladder_table.md`, `e4_s3b_memory.md`, **`e4_s3b_floor.md`
    (the closed four-row table)**, `validity.json`, `e4_s3b_verdict.json`;
  - `state_at_end.json`, `redact_check.txt`.
- The 5-s predecessor demo file (`backoff_demo/stopped_predecessor_5s.jsonl`,
  4.4 MB) is kept. It joins E4-S3's two ~300 MB `epg.jsonl` files on the
  user's list before the commit.
- Git status (cumulative): `logs/e4_s3b_git_status.txt`.
