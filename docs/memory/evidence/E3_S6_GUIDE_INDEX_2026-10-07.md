---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: bf2120c
---

# E3-S6 — the guide-metadata parse: a cached slim index

**Classification (two verdicts, pre-registered):**

- **MEMORY: ACCEPTED.** Every clause holds in both E1-META runs. The
  companion's PSS is **33.6 / 34.1 MB** at the window's end (E2: 161), it
  does not grow, and its CPU in the grab cycle is **0.22 %** of a core
  (E2: 7.6 %). Grabs are faster and the guide serves the same.
- **STREAM: REJECTED.** In both E1-CONC runs, loss/min, rendered fps,
  resyncs and the aligned frame all miss the bar. Every one of them
  improved on E2's CONC: loss 773 / 1,273 vs ~1,600 per minute, 10 vs
  300-450 underruns, and the +1 s peak cut by half to two thirds.
- **The probe located the CONC loss:** the parse alone reproduces it
  (318 × baseline); the grabber child alone is ~5 × smaller (63 ×).
- One change behind `PRIVYHUB_EPG_GUIDE_INDEX=cached`. **NOT ADOPTED;
  nothing committed.** The flag is absent at the end; E2's final state is
  restored.

**Context:**

- Task: `handoffs/E3-S6_GUIDE_INDEX_TASK.md`, queue B item 2.
- Baseline commit: `bf2120c`.
- Files: `e3_s6_2026-10-07/`.
- E3-S1..S5's flags are absent (no compounding).
- Timeline (UTC, 2026-10-07):

  | time | what |
  | --- | --- |
  | 01:32 | preconditions held; the guide read before (6 channels, 343 programmes) |
  | 01:33-01:52 | the probe |
  | 01:52 | the change, the smoke, the index's cost |
  | **01:53:17** | **pre-registration hashed** (`375b5b0e…0ffc`) |
  | 01:53-03:52:58 | the control, META ×2 and CONC ×2 flagged; all OK on their first attempt |

## 1. The probe (`probe.md`)

The grab's two halves were triggered separately against a live PS1
stream, using this task's extension of the dormant probe hook.

| op | lost packets/s at +0 / +1 / +2 s | mean 0-2 s ÷ baseline (0.174/s) | busiest core peak | the companion's own CPU per op |
| --- | --- | --- | --- | --- |
| **parse only** (×40) | 40.8 / **80.5** / 44.9 | **318 ×** | 33 % | 0.42 s (one thread) |
| spawn only (×20) | 4.7 / 15.7 / 12.6 | 63 × | 83 % | ~0 |

- By the task's reading rule the probe **names both**, so the stream half
  was gated.
- **The parse is the larger cause by ~5 ×.** It is 0.42 s of one Python
  thread in the companion's process: it holds the GIL against the stream
  threads, and the host CPU barely moves.
- The spawn is the smaller part, despite driving a core to 83 %.
- This explains why E3-S1, which only took the child's priority, left the
  peak in place.

## 2. The change (`patches/E3-S6_GUIDE_INDEX.md`)

`companion/plugins/epg.py`; diff: `e3_s6_guide_index.diff`.

- With the flag, the candidate loop reads the channel's rows from a slim
  index instead of parsing the whole 25.6 MB file per grab.
- **The index:**
  - per channel: channel, feed, site, site_id, lang, site_name, packed as
    one string;
  - 13,555 channels; **3.7 MB in memory**, 3.1 MB on disk;
  - **built once in 0.95 s**, keyed by the metadata file's size + mtime,
    with the parse's heap trimmed once after;
  - saved as `data/epg/metadata/guides_index.json` and reloaded in 14 ms.
- `_candidate_mappings` itself is unchanged.
- **The smoke** (six channels): **the candidates are identical by both
  paths** for every channel, and every refresh was ok.

## 3. The runs and the two bars

From `e3_s6_table.md`; the verdicts are in `e3_s6_verdict.json`
(`e3_s6_analysis.py`).

| | control (no flag) | META r1 | META r2 | CONC r1 | CONC r2 | E2 PS1-STREAM | E2 META | E2 CONC r1 / r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| companion PSS first → last MB | 35.8 → 41.9 | **32.5 → 33.6** | **32.5 → 34.1** | 43.5 → 49.2 | 43.3 → 47.2 | 36.3 → 40.2 | 133.7 → 161.0 | 147 → 158; 193 → 200 |
| companion CPU, % of a core | 24.8 | **0.22** | **0.22** | 26.0 | 24.5 | 24.3 | 7.6 | 33.1 / 33.5 |
| grabs ok / failed, median s | — | 248/0, 4.8 | 249/0, 4.9 | 217/0, 5.9 | 222/0, 5.8 | — | 228/0, 5.2 | 208/0, 5.9; 214/0, 5.8 |
| host CPU % | 11.5 | 10.2 | 10.2 | 22.2 | 21.4 | 11.7 | 9.8 | 20.5 / 21.9 |
| EPG child CPU % / PSS MB | — | 70 / 490 | 74 / 491 | 81 / 490 | 81 / 487 | — | 67 / 486 | 79 / 484, 82 / 478 |
| busiest-core-per-second p95 % | 39 | 97 | 97 | 98 | 98 | 38.5 | 96 | 97 / 96 |
| rendered fps | 59.97 | — | — | **58.65** | **57.64** | 59.81 | — | 56.5 / 56.6 |
| video loss/min | 4.8 | — | — | **773** | **1,273** | 32 | — | 1,622 / 1,602 |
| resyncs | 0 | — | — | 14 | 27 | 0 | — | 199 / 204 |
| audio underruns | 10 | — | — | **10** | **10** | 11 | — | 448 / 312 |

**MEMORY, both META runs:**

| clause | needed | got | holds |
| --- | --- | --- | --- |
| a. PSS at the window's end; not keeps growing | ≤ 60 MB; ≤ 5 % | 33.6 / 34.1; 3.8 / 3.7 % | yes |
| b. grabs | failed 0, ok ≥ 205, median ≤ 6.8 s | 248/0, 4.8; 249/0, 4.9 | yes |
| c. the guide serves; candidates identical | 6; 343 ± 5 %; identical | 6; 343; identical (smoke) | yes |
| d. host CPU | ≤ 11.8 | 10.2 / 10.2 | yes |

**MEMORY: ACCEPTED.**

**STREAM, both CONC runs** (gated: the probe named both; comparability
holds, control 11.5 % / 59.97 fps):

| clause | needed | got | holds |
| --- | --- | --- | --- |
| e. loss/min | ≤ 100 and ≤ 3 × control (14.4) | 773 / 1,273 | no |
| f. rendered; resyncs | ≥ 59.5; ≤ 10 | 58.65 / 57.64; 14 / 27 | no |
| g. aligned frame, mean 0-2 s | ≤ 3 × the control's 0.080 lost/s = 0.24 | 16.6 / 24.9 | no |

**STREAM: REJECTED.**

**The aligned frame** (`aligned_ctl/e2_conc.md`), mean lost packets/s by
second after each grab's start:

| s | 0 | 1 | 2 | 3 | 4 | 5 | 6-10 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CONC r1 (index) | 11.9 | 21.0 | 17.1 | 9.6 | 8.8 | 9.0 | 0.2-20 |
| CONC r2 (index) | 15.8 | 28.4 | 30.5 | 19.3 | 17.3 | 14.4 | 6.7-13 |
| *E2 CONC r1 (today)* | *34* | *65* | *43* | *6* | *10* | *7* | *19-23* |
| *E3-S1 CONC (today's parse, child idle-priority)* | *38-44* | *56-65* | *48-55* | *26-31* | *24-32* | *23-32* | — |
| busiest core % r1 / r2 (index) | 41 / 44 | 60 / 73 | 78 / 68 | 51 / 45 | 52 / 59 | 56 / 46 | 25-42 |

**Read beside the bars:**

- **With the parse gone, the +1 s peak fell from 56-65 to 21-28 lost
  packets/s.** The companion's CPU in CONC fell by 7-9 points (26.0 /
  24.5 vs 33.1 / 33.5), and underruns fell from 300-450 to 10.
- **What remains is the grabber child's share**, as the probe predicted
  (spawn-only: 11-16 lost/s at +1-2 s on a quiet link). The busiest core
  still reaches 73-78 % at +1-2 s.
- The pre-registered stream bar asks the CONC row to look like plain
  streaming. One change does not get there.
- No unflagged CONC ran tonight (the plan did not call for one), so the
  improvement over E2's CONC is across nights. The control (4.8/min) says
  tonight's link was, if anything, quieter than E2's (32/min).

## 4. What the user would be adopting, and the revert

- **Adoption — MEMORY ACCEPTED:** one drop-in line,
  `Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`.
  - The companion stays ~34 MB through a grab cycle (not ~160).
  - Its grab-cycle CPU goes from ~7.6 % to ~0.2 % of a core.
  - Grabs are ~0.4 s faster.
  - Grabs during a stream are roughly half as damaging; that side is
    REJECTED by its own bar, so the loss is not fixed.
  - The index file is built on the first grab after each metadata
    refresh (0.95 s, once).
- **Revert:** delete the line, `systemctl --user daemon-reload`, restart
  the unit. Optionally delete `data/epg/metadata/guides_index.json`.
  - The runs' index file was deleted at this task's end, so the
    runtime's data is as before.
  - With the flag set, the file is rebuilt on the first grab.

## 5. State at the end; files

- **Final state** (`runs/final_state.json`, 03:52:58Z):
  - manager none; environ exactly the live default;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The guide read after: 6 channels, 343 programmes.
- `guides_index.json` was removed (it is rebuilt if the flag is set).
- The metadata TTL did not expire during the runs.
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s6_2026-10-07/`):
  - `precondition.json`, `probe.md`, `e3_s6_probe.py`;
  - `probe_triggers.jsonl`, `probe_aligned.json`, `probe_run.json`,
    `probe_sampler/`, `e3_s6_probe_hook.diff`;
  - `smoke.sh`, `smoke.jsonl`, `index_cost.py`, `index_cost.json`;
  - `guide_read_before.json` / `guide_read_after.json`;
  - the pre-registration and its `.sha256`; `e3_s6_guide_index.diff`;
  - `runs/` (5 runs, `manifest.sha256`, `--check` OK);
  - `e3_s6_analysis.py`, `e3_s6_table.md/.json`, `e3_s6_verdict.json`,
    `aligned_ctl/`, `aligned_e2/`, `redact_check.txt`.
- Git status: `logs/e3_s6_git_status.txt`.
