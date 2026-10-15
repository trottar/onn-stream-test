---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
---

# E4-S3 — the memory floor, closed (swap off)

> **`MemorySwapMax=0`: no swap for the stack's cgroup.** The floor is the
> smallest `MemoryMax=` at which the stack runs with page-cache reclaim
> only; a host with swap would degrade more softly below it. It is a
> floor for the **stack's cgroup** (companion, RetroArch, the encoder,
> the grabber children), not for the host: Xorg, pulseaudio, the desktop
> and the OS are outside it.

**Classification: MEMORY FLOOR MEASURED.**

| row | memory floor, swap off | at the floor |
| --- | --- | --- |
| PS1-STREAM (CPU 200 %) | **≤ 384M** | 228 MB peak; anon 191 + file 21 MB; 0 `memory.max` events; PSI 0 |
| SNES-STREAM (CPU 150 %) | **≤ 384M** | 197 MB peak; anon 165 + file 19 MB; 0 events; PSI 0 |
| CONC (CPU unset) | **above 768M** (below 1G with swap: E4-S2) | at 768M the grabber was OOM-killed and the unit restarted, repeatedly |
| META (CPU 150 %) | **above 768M** (below 1G with swap: E4-S2) | the same |

- **The stack's memory floor is between 768M and 1G.** It is set by the
  EPG grabber (node, ~650-850 MB per grab). A stream alone needs under
  ~230 MB.
- 10 runs, all valid; `--check` OK; 0 replaced attempts. Every drop-in
  was read back under load and lifted after (`MemorySwapMax` /
  `memory.swap.max` included).
- Measurement only; nothing adopted, nothing committed.

**Context:**

- Task: `handoffs/E4-S3_MEMORY_FLOOR_CLOSE_TASK.md`, under
  `handoffs/QUEUE_2026-10-10.md`.
- **Baseline: `7331184` plus the uncommitted E4-S1/S2 work**, untouched
  (no stash, reset, checkout or clean).
- Files: `e4_s3_2026-10-10/`.
- **Timeline (UTC):**

  | date | time | what |
  | --- | --- | --- |
  | 10-09 | 22:10-22:17 | the runner extended (below) |
  | 10-09 | **22:18:08** | **pre-registration hashed** (`356c594e…bd21`) |
  | 10-09 → 10-10 | 22:18-02:20 | the ladder: 768M (4 rows), 512M (2), 384M (2), 2 repeats |

## 1. The ladder

| step | PS1-STREAM | SNES-STREAM | CONC | META |
| --- | --- | --- | --- | --- |
| 768M | INCONCLUSIVE (rendered 59.35; loss 185/min) → repeat INCONCLUSIVE (59.34; loss 218) | PASS | **FAIL**: OOM kills, unit restarted (574 kill lines), stream lost | **FAIL**: OOM kills, unit restarted (546), 0 complete cycles |
| 512M | INCONCLUSIVE (59.39; loss 182) → repeat INCONCLUSIVE (58.77; loss 353) | PASS | — | — |
| 384M | **PASS** (59.56; loss 92) | **PASS** | — | — |

- **PS1-STREAM's INCONCLUSIVE steps are the link, not memory.** Only
  rendered fps failed, at 58.77-59.39, with loss 182-353/min.
  - Every host-side gate held: RetroArch 59.999, capture 60.0, dup+drop
    0.1/min, no kill, no restart.
  - Memory never came near any limit: 219-226 MB max, 0 `memory.max`
    events, PSI 0.
  - The control (PS1 at 768M) lost 185/min against D-BASE's < 10, so
    by the pre-registered clause these are INCONCLUSIVE.
  - The floor is ≤ 384M, with 768M / 512M listed as INCONCLUSIVE above
    it (`e4_s3_floor.md`).
- **CONC and META at 768M:**
  - The cgroup hit 765 MB, all of it anon (743 MB), with no page cache
    left to reclaim (0.1-0.2 MB file).
  - The kernel OOM killer killed the grabber (`npm run grab`, node). The
    unit's `OOMPolicy=stop` stopped it ("Failed with result 'oom-kill'"),
    and `Restart=on-failure` restarted it: 17 times in one 5-min stretch.
  - **Why the cgroup's `oom_kill` counter reads 0:** each restart makes
    a fresh cgroup, which resets it. The pre-registered journal and
    MainPID gates caught it.
  - **A runner artifact, reported:** while the unit was down, the suite's
    refresh loop spun on the refused endpoint, logging ~1.4-1.5 M failed
    "grabs" (`epg.jsonl`). It's harmless to the verdict, which was
    already FAIL, but the loop has no back-off.
    - **The two `epg.jsonl` files are ~310 MB and ~296 MB** (CONC and
      META at 768M); the directory is 672 MB.
    - Kept, as nothing is deleted. **The user's call before the commit**
      (e.g. compress them, or keep only their first and last lines); the
      manifest hashes them as they are.
    - A back-off in the runner's refresh loop on a refused call is a
      one-line follow-up, not made here.
- **E4-S2's 1G passed only with swap.** CONC was pinned at 1,024 MB and
  pushed 127.5 MB to swap.
  - The grab cycle's working set is therefore between ~0.75 and ~1.15 GB:
    the stack's ~230 MB plus the grabber's per-grab peak, which reached
    855 MB on its last META grab in E4-S1.
  - The ladder's steps (768M → 1G) are not fine enough to place it more
    exactly.

## 2. The memory per run

`e4_s3_memory.md` (from `cgroup.jsonl`, 5-s samples):

- **The stream rows** hold 214-217 MB mean, 223-228 MB peak (anon
  183-191 MB, file ~20 MB) at every step from 768M to 384M.
  - 0 `memory.high` / `memory.max` events.
  - Memory PSI some / full 0.00 ms/s; 0 major faults.
  - The companion's PSS is 38 MB.
- **The grab rows** reach 742 MB anon within one grab.

## 3. The alpha's memory line, revised (E4-S2 §5 said "2 GB for the stack")

| | measured | proposed |
| --- | --- | --- |
| a stream alone (PS1 or SNES) | ≤ 384M (228 MB peak, no pressure) | — |
| with the guide grabber (CONC / META) | > 768M without swap; ≤ 1G with swap (127 MB swapped) | **1.5 GB for the stack, no swap assumed**: ~1.15 GB working set + ~30 % margin; **2 GB if a second concurrent activity is to be absorbed** |
| system | — | **8 GB** stands (the host shows ~4 GB used at IDLE outside the stack) |

- **The memory floor is the guide grabber's**, the same as the CPU-time
  floor.
- If E4-S4's deferral were adopted, a stream would never share memory
  with a grab, and the stack's peak would be the larger of the two
  (~1.15 GB, the grab), not their sum. The cycle alone still needs > 768M.

## 4. State at the end; files

- **Final state** (`runs/final_state.json`, 02:20Z; `state_at_end.json`):
  - the four adopted lines; no `e4_constraint.conf` (`MemoryMax`,
    `MemorySwapMax`, `CPUQuotaPerSecUSec` read back infinity;
    `memory.max` / `memory.swap.max` read back max);
  - no `e3_flag.conf`; no game;
  - the PS1 files identical; **APK CONFIRMED**.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
- E4-S2's driver was copied (`e4_s3_ladder.py`), not run in its
  directory. Its log lines keep E4-S2's `[e4s2 …]` prefix, a cosmetic
  leftover.
- **The tool change** (`tools/e1_suite.py`, `e4_s3_tools.diff`;
  `patches/E4-S3_SWAP_AND_MEMORY_READINGS_RUNNER.md`):
  - `MemorySwapMax=` accepted in a constraint and read back;
  - `memory.stat` (anon / file / shmem / major faults) and the cgroup's
    memory PSI in `cgroup.jsonl`;
  - the unit's MainPID at the window's start and end;
  - the journal's kill lines over the window (`journal_kills`).
- **Files** (`e4_s3_2026-10-10/`):
  - `precondition.json`, `git_status_at_start.txt`,
    `tools_predecessor_sha256.txt`, `tools_sha256.txt`,
    `tools_at_preregistration_sha256.txt`, `e4_s3_tools.diff`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`;
  - `e4_s3_ladder.py`, `ladder.json`, `ladder_console.log`,
    `ladder_stdout.log`, `runs_console.log`;
  - `runs/` (10 runs, `manifest.sha256`, `check.txt`, `final_state*.json`);
  - `e4_s3_analysis.py`, `analysis_console.txt`, `e4_s3_ladder_table.md`,
    `e4_s3_memory.md`, `e4_s3_floor.md`, `validity.json`,
    `e4_s3_verdict.json`;
  - `state_at_end.json`, `redact_check.txt`.
- Git status (cumulative): `logs/e4_s3_git_status.txt`.
