---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1..S5 work)
durable_memory_updated: true
---

# E4-S3B: the runner's refresh loop backs off on a refused call (tools only)

## Purpose

E4-S3's CONC and META runs at 768M wrote ~1.4-1.5 M rows (~300 MB) each to
`epg.jsonl`. While the OOM-killed unit was down, the suite's forced-refresh
loop re-called the refused endpoint at once, one row per attempt. That was a
runner fault, not a stack fault. E4-S3B (`handoffs/E4-S3B_MEMORY_FLOOR_1G_SWAPOFF_TASK.md`,
record `evidence/E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_2026-10-10.md`) fixes it
before its own runs.

## Change

**`tools/e1_suite.py`** (predecessor `33b60f01…3e61`, E4-S5's runner; after
`76e1aa13…a147`; diff `evidence/e4_s3b_2026-10-10/e4_s3b_tools.diff`):

- **`EpgCycle.run`** (the CONC / META grab cycle): a refresh call that gets
  no HTTP reply at all (refused, reset, timeout; `http()` returns code
  `None`) starts or extends a failure streak.
  - The loop backs off 1 s, doubling to 30 s, until a call is answered.
  - The streak is written as **one** row, `kind: grab_fail_streak` (first
    channel, start / end, first error, attempt count, duration), when a
    call is answered or the cycle stops.
  - Every answered call (any HTTP status) takes today's path unchanged:
    the same calls at the same cadence, the same rows.
- **`epg_figures`**: a streak overlapping the window counts, and its
  attempts count as failed grabs (`grabs_failed` still gates). New fields:
  `fail_streaks`, `fail_streak_attempts`, `fail_streak_s`.

## Validation

`evidence/e4_s3b_2026-10-10/backoff_demo/` (`demo_cycle.py` runs one
`EpgCycle` for N seconds, from the patched runner or the predecessor copy):

| cycle | companion | rows | kinds |
| --- | --- | --- | --- |
| predecessor, 60 s | running | 15 | 14 grabs (all HTTP 200), 1 scan |
| patched, 60 s | running | 14 | 13 grabs (all HTTP 200), 1 scan |
| **patched, 60 s** | **stopped** | **2** | 1 `grab_fail_streak` (6 attempts at 0/1/3/7/15/31 s, 31.0 s), 1 scan |
| predecessor, 5 s | stopped | 22,585 | 22,585 failed grabs |

- The two running cycles match in kinds, HTTP codes and cadence (median
  grab 4.79 / 4.78 s).
- `e1_suite.py --self-test` OK.
- The E4-S3B runs ran on it.
- The 5-s predecessor file is 4.4 MB; it is kept (nothing is deleted).

## Rollback

Restore the predecessor bytes (`33b60f01…`, kept as
`evidence/e4_s3b_2026-10-10/backoff_demo/e1_suite_predecessor.py`). That is
E4-S5's runner, itself uncommitted.
