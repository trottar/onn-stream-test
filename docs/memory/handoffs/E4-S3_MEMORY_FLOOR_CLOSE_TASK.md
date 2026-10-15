---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S3, queue item 1: close the memory floor E4-S2 left open. `MemoryMax=` 768M / 512M / 384M with `MemorySwapMax=0`, on the four rows at their E4-S2 CPU quotas, E4-S2's pass rule plus "no OOM kill". Measurement only; nothing adopted; nothing committed
---

# E4-S3 — the memory floor, closed

**Where E4-S2 left it.** Every row passed at `MemoryMax=1G`; CONC sat
pinned at 1,024 MB with 204 `memory.max` events and 127.5 MB pushed to
swap (`MemorySwapMax=` was unset). PS1-STREAM peaked at 221 MB, SNES
197 MB, META 966 MB. The floor is below 1G for the stream rows and
near it for the grab rows; with swap allowed, "passed" at 1G is soft.

Read first: `evidence/E4_S2_CPU_MEMORY_FLOOR_2026-10-09.md` (§1, §4,
§5), `e4_s2_2026-10-09/e4_s2_ladder.py` (the driver and pass rule),
`e4_s2_preregistration.txt`, `e4_s2_throttle.md`, `patches/E4-S2_…md`.

## 1. Pre-registration (hashed before any constrained run)

- **The ladder**, descending, with `MemorySwapMax=0` in the same
  drop-in: `MemoryMax=` **768M, 512M, 384M**. Rows and their CPU
  quotas as E4-S2's memory ladder: PS1-STREAM at 200 %, SNES-STREAM at
  150 %, META at 150 %, CONC unconstrained in CPU. Stop descending a
  row at its first failure; stop the ladder when every row has failed
  or 384M has passed.
- **The pass rule** = E4-S2's per-run rule (valid; the host-side gates:
  rendered ≥ 59.5, RetroArch ≥ 59.9, capture 60 ± 0.5 with the SNES
  reference-relative clause, spikes < 200, stale < 20, dup+drop ≤
  0.2/min; META/CONC grabs failed 0, each channel ≥ 20 refreshes, the
  guide serves) **plus**: no `oom_kill` in the cgroup's `memory.events`
  during the window, and no process of the stack restarted by the
  companion because of a kill (the companion's log). The link-INCONCLUSIVE
  clause as E4-S2 (the control is the first PS1-STREAM run at 768M,
  compared to D-BASE's loss row; reported).
- **Reported, not gated:** `memory.events` (max, high, oom), memory PSI
  some/full, `memory.current` peak, page-cache vs anon split
  (`memory.stat` file / anon), the grab cycle's speed under pressure,
  the companion's own PSS.
- **The floor per row** = the smallest `MemoryMax=` that passed; **the
  stack's memory floor** = the maximum over rows, stated with the
  swap-off caveat and the peak figures beside it.

## 2. The runs

`e4_s2_ladder.py` extended for the swap setting (a copy here,
`e4_s3_ladder.py`; the tool patch if `e1_suite.py` needs anything).
Each run: drop-in written, read back under load (`memory.max`,
`memory.swap.max`, `cpu.max`), removed at teardown, properties read
back as `infinity`/`max`. ~3-4 h if nothing fails early.

## 3. The record

`evidence/E4_S3_MEMORY_FLOOR_CLOSE_<date>.md` + `e4_s3_<date>/` (the
pre-registration + `.sha256`, every run, `manifest.sha256`, `--check`,
`validity.json`, the cgroup stats per run, the ladder table, the floor
table, `redact_check.txt`): **the memory floor table** (per row: floor,
the first failing metric at the step below, peak and events at the
floor, anon vs file at the floor), the stack's memory floor, and the
alpha proposal's memory line revised (E4-S2 §5: "2 GB for the stack")
with the margin stated. `docs/ROADMAP.md` E4; `logs/e4_s3_git_status.txt`.
The final state is the four-line adopted state, no `e4_constraint.conf`,
no game, PS1 files identical, APK CONFIRMED; then queue item 2.
