---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S3B, queue item 1: the one run E4-S3 could not give — the grab rows (CONC, META) at `MemoryMax=1G` with `MemorySwapMax=0`. E4-S2 passed 1G with swap allowed; E4-S3 failed 768M with swap off; the swap-off floor is therefore "between 768M and 1G" only if 1G passes without swap. Ascend to 1.5G / 2G only on failure. Plus the runner's refresh-loop back-off (a tool patch). Measurement only; nothing adopted; nothing committed
---

# E4-S3B — the memory floor at 1G, swap off

**Where E4-S3 left it.** PS1-STREAM and SNES-STREAM passed at 384M swap-off
(peaks 228 / 197 MB, 0 memory events). CONC and META failed at 768M
swap-off: OOM kills, the unit restarted (574 / 546 journal kill lines),
the grab cycle dead. The only 1G evidence is E4-S2's, **with swap
allowed** (CONC pinned at `memory.max` with 204 events and 127 MB in
swap). The ladder stopped at the first failure, so 1G swap-off was never
run. The stack's swap-off floor is undetermined until it is.

**Also.** During the 768M failures the runner's forced-refresh loop kept
calling a refused endpoint, writing ~1.5 M rows (~300 MB) to each run's
`epg.jsonl`. That is a runner fault, not a stack fault: fix it here.

Read first: `evidence/E4_S3_MEMORY_FLOOR_CLOSE_2026-10-10.md`,
`e4_s3_2026-10-10/e4_s3_ladder.py`, `e4_s3_preregistration.txt`,
`e4_s3_floor.md`; `E4_S2_…` §4-5.

## 1. The tool patch (before the pre-registration)

In the suite's forced-refresh cycle (`tools/e1_suite.py`, the CONC/META
rows): when a refresh call fails at the connection (refused, reset,
timeout), back off — 1 s, doubling to 30 s — until a call succeeds, and
write **one** row per failure streak (first failure, count, duration)
instead of one per attempt. Behaviour when every call succeeds is
unchanged (today byte for byte: the same calls at the same cadence). Show
it with a 60-s dry cycle against a stopped companion (rows written ≤ 5)
and a 60-s cycle against the running one (rows as before). `patches/`.

## 2. Pre-registration (hashed before any constrained run)

- **Runs**: E1-CONC (CPU unset) and E1-META (`CPUQuota=150%`) at
  **`MemoryMax=1G` + `MemorySwapMax=0`**, E2's windows and gaps, the
  drop-in per run as E4-S3 (written, read back under load, removed at
  teardown, properties read back `infinity`/`max`). **If a row fails at
  1G**, that row ascends: 1.5G, then 2G; stop at its first pass or at 2G.
  A PS1-STREAM control first (unconstrained, for the link clause only).
- **The pass rule** = E4-S3's, verbatim (E4-S2's per-run rule + no
  `oom_kill`, no journal kill line, the unit's MainPID unchanged).
- **The floor per row** = the smallest `MemoryMax=` that passed swap-off,
  now over E4-S3's and this task's runs together; **the stack's swap-off
  memory floor** = the maximum over the four rows, with the peak figures
  and memory events beside it. If a row fails at 2G: "above 2G" and the
  task ends there.
- **Reported, not gated:** `memory.events`, PSI some/full,
  `memory.current` peak, anon/file at the peak, the grab cycle's speed,
  the companion's PSS, the stream's loss/resyncs/underruns, the
  `epg.jsonl` sizes (they must now stay small even if a row fails).

## 3. The record

`evidence/E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_<date>.md` + `e4_s3b_<date>/`
(driver copy `e4_s3b_ladder.py`, the pre-registration + `.sha256`, every
run, `manifest.sha256`, `--check`, `validity.json`, cgroup stats per run,
**the closed floor table** (all four rows, E4-S3 + this), the alpha
proposal's memory line restated with its margin, `redact_check.txt`);
`docs/ROADMAP.md` E4; `logs/e4_s3b_git_status.txt`. The final state is
the four-line adopted state, no `e4_constraint.conf`, no game, PS1 files
identical, APK CONFIRMED; then queue item 2.
