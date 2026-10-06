---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
---

# E3-S3 — the EPG grabber's own cost: node started directly (no `npm run`)

**Classification:**

- **REJECTED by the pre-registered bar**, on clause (a). The EPG CPU-s per
  channel-grab was 3.32 / 3.38 against ≤ 2.25 (0.7 × E2's 3.21, by the
  same method).
- Clauses (b)-(d) hold.
- One change behind `PRIVYHUB_EPG_DIRECT_NODE=1`. **NOT ADOPTED; nothing
  committed.** The flag is absent at the end; E2's final state is
  restored.

**Context:**

- Task: `handoffs/E3-S3_GRABBER_COST_TASK.md`, queue item 3.
- Baseline commit: `d9fdbdd`.
- Files: `e3_s3_2026-10-06/`.
- E3-S1's and E3-S2's flags are absent (no compounding).
- Timeline (UTC, 2026-10-06):

  | time | what |
  | --- | --- |
  | 05:48:49 | preconditions held (`precondition.json`) |
  | 05:49 | the probe |
  | 05:50 | the change, a smoke (not data), the guide read before |
  | **05:50:55** | **pre-registration hashed** (`0474a3bd…f79d`) |
  | 05:51:05-06:37:27 | E1-META ×2 with the flag, both OK first time, with the exact children-CPU log alongside |

## 1. The probe (`probe.md`)

Three single-attempt grabs of one channel, the stream idle.

| share of one grab's CPU-s (3.57-3.76) | CPU-s |
| --- | --- |
| (a) the npm wrapper | 0.08-0.09 |
| the tsx cli | 0.06-0.07 |
| **(b) the grabber node before its first TCP socket** | **3.23-3.41** |
| (c) the grabber node after it (fetch, parse, exit) | 0.17-0.20 |

- (a) + (b) = **95 %**, above 40 %, so the rule picks
  `PRIVYHUB_EPG_DIRECT_NODE=1`.
- **The record said before the data:** ~91 % of the cost is inside the
  grabber node's own start-up. That is ~2 s at ~170 % of a core: tsx's
  TypeScript transform and the module load, reaching ~595 MB PSS before
  any network. Direct invocation keeps all of it. The expected saving
  was the npm + tsx-cli share (~4 % CPU-s, ~95 MB PSS).

## 2. The change (`patches/E3-S3_EPG_DIRECT_NODE.md`)

- `companion/plugins/epg.py`, the grab's argv only.
- With the flag the companion runs `<toolchain node> --require
  <tsx>/dist/preflight.cjs --import <tsx>/dist/loader.mjs
  scripts/commands/epg/grab.ts <the same grab arguments>`. That is what
  the tsx cli spawns, in the same cwd with the same environment.
- Absent = `npm run grab`, byte for byte.
- Diff: `e3_s3_direct_node_change.diff`.
- Smoke: the tree is one process; same programme count.

## 3. The runs and the bar

From `e3_s3_table.md`; the verdict is in `e3_s3_verdict.json`
(`e3_s3_analysis.py`).

| | META r1 (flag) | META r2 (flag) | E2 META |
| --- | --- | --- | --- |
| **EPG CPU-s per grab (1-s sampler, window total / grabs)** | **3.32** | **3.38** | 3.21 |
| EPG CPU-s per grab, median (1-s sampler) | 3.1 | 3.1 | 2.8 |
| exact children CPU-s per grab (`children_cpu.jsonl`) | 4.92 | 4.93 | (no log) |
| EPG peak PSS per grab, median MB | **615** | **615** | 651 |
| EPG child CPU % / PSS mean MB | 74 / 459 | 72 / 464 | 67 / 486 |
| grabs ok / failed; median s | 247 / 0; 4.85 | 238 / 0; 4.87 | 228 / 0; 5.2 |
| ok refreshes per channel (min) | 41 | 39 | 38 |
| host CPU mean % | 10.2 | 9.9 | 9.8 |
| companion PSS at the window's end MB | 160 | 166 | 161 |

| clause | needed | got | holds |
| --- | --- | --- | --- |
| a. CPU-s per channel-grab | ≤ 0.7 × 3.21 = 2.25, both runs | 3.32 / 3.38 | **no** |
| b. peak PSS per invocation | ≤ 660 MB | 615 / 615 | yes |
| c. grabs failed 0; each channel ≥ 34 | — | 0; 41 / 39 min | yes |
| d. the guide serves | 6; 342 ± 5 % | 6; 343 | yes |

**Verdict: REJECTED.**

- **Per grab, the CPU is unchanged within noise**: +3-5 % by the
  sampler, which undercounts short-lived processes either way.
- **What did change:**
  - each grab is ~0.35 s shorter (4.85 vs 5.2 s median), so the cycle
    fits 8-10 % more grabs;
  - the per-grab peak PSS is ~36 MB lower (no npm, no tsx cli process);
  - the mean EPG CPU % is a little higher, because the grabs are
    denser.
- **The exact figure:** the companion's reaped-children CPU is
  **4.9 CPU-s per channel-grab**. The 1-s sampler's 3.3 misses about a
  third. That is the honest cost of today's grab cycle:
  - 3.5-3.8 per source attempt;
  - more on channels whose first source returns nothing (two attempts).

**What would move this number (not tested; for the user's list):**

- The node grabber's start-up: tsx compiling the TypeScript on each run.
  A precompiled JS build of the grabber, or tsx's cache, would cut the
  ~3.3 CPU-s before the first network byte.
- The multi-attempt channels: a remembered working source per channel
  would skip the empty first attempt.
- The batch mode the task named for the other branch: one grabber start
  per cycle. It was not chosen, because the probe's rule picked start-up.

## 4. What the user would be adopting, and the revert

- **Adoption, if wanted despite the verdict:** one drop-in line,
  `Environment=PRIVYHUB_EPG_DIRECT_NODE=1`. It is a ~7 % shorter grab
  and ~36 MB less per grab, not a CPU saving.
- **Revert:** delete the line, `daemon-reload`, restart.

## 5. State at the end; files

- **Final state** (06:37:27Z):
  - manager none; environ exactly the live default;
  - the e3 drop-in absent;
  - no game; the PS1 files identical; **APK CONFIRMED**.
- The children logger was stopped.
- No `nft`, no `sudo`, the Opal untouched.
- Files (`e3_s3_2026-10-06/`):
  - `precondition.json`, `probe.md`, `probe/` (tree, sampler, smoke);
  - the pre-registration and its `.sha256`; the diff;
  - `guide_read_before.json` / `guide_read_after.json`;
  - `children_cpu.jsonl`;
  - `runs/` (2 runs, `manifest.sha256`, `--check` OK);
  - `e3_s3_analysis.py`, `e3_s3_table.md/.json`, `e3_s3_verdict.json`,
    `redact_check.txt`.
- Git status: `logs/e3_s3_git_status.txt`.
