---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
durable_memory_updated: true
---

# E4-S3: the runner takes `MemorySwapMax=` and records memory pressure and kills (tools only)

## Purpose

E4-S3 (`handoffs/E4-S3_MEMORY_FLOOR_CLOSE_TASK.md`, record
`evidence/E4_S3_MEMORY_FLOOR_CLOSE_2026-10-10.md`) runs the memory ladder
with swap off and adds "no OOM kill" to the pass rule.

## Change

**`tools/e1_suite.py`** (predecessor `1b3570f7…0e72`, E4-S2's; after
`95b3e6d7…b842`; diff `evidence/e4_s3_2026-10-10/e4_s3_tools.diff`):

- **The constraint:**
  - a plan constraint may carry `MemorySwapMax=X`, read back as the
    cgroup's `memory.swap.max`;
  - the run directory gains `_swapX`;
  - "lifted" now also requires `MemorySwapMax=infinity` /
    `memory.swap.max max`.
- **`cgroup.jsonl` gains:**
  - `memory.stat` (anon, file, shmem, file_mapped, pgmajfault);
  - the cgroup's `memory.pressure` totals.
  - `key.cgroup` gains anon / file at the window's peak, the anon max,
    memory PSI some / full in ms per s, and major faults.
- **The summary gains:**
  - `mainpid_window_start` / `_end`;
  - `kills_in_window`: the unit's journal over the window, lines naming
    an OOM / SIGKILL / signal 9 / "killed". This returned 0 over E4-S2's
    12 h.

## Validation

`e1_suite.py --self-test` OK. The helpers were checked against live
values. The 10 E4-S3 runs ran on it.

## Rollback

Restore the predecessor bytes (`1b3570f7…`). That is E4-S2's runner,
itself uncommitted; see `E4-S2_CONSTRAINT_DROPIN_AND_CGROUP_RUNNER.md`.
