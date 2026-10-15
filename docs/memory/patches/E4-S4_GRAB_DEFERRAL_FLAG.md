---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
durable_memory_updated: true
---

# E4-S4: EPG grabs deferred while a stream is live, behind `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1` (REJECTED; dormant)

## Purpose

E4-S4 (`handoffs/E4-S4_GRAB_DEFERRAL_TASK.md`, record
`evidence/E4_S4_GRAB_DEFERRAL_2026-10-10.md`): no grab runs while a
native stream session is live. The goal is the stack's CPU-time floor
from 400 % to a stream's 150 %.

## Change

**`companion/plugins/epg.py`** (predecessor `d176e142…eb68` = HEAD, now
`707bda2d…c3c2`):

- `DeferredGrabs`;
- the hook in `_guide(force=True)` (the refresh endpoint and the
  background warmer) when the games plugin's recovery state is PLAYING
  or PAUSED_*;
- the drain on ENDED; the 60-min cap;
- `status()["deferred"]`, present only with the flag.

Absent = today.

**`tools/e1_suite.py`** (predecessor `95b3e6d7…b842`, E4-S3's; now
`e35e3053…6269`):

- the CONC cycle's 5-s wait on a `refresh_deferred` reply and its
  `deferred` rows;
- `epg_figures`' `deferred_in_window`;
- `wait_deferred_drain()` in the teardown of a run carrying the flag.

The diff is `evidence/e4_s4_2026-10-10/e4_s4_change.diff`; it was applied
by `apply_e4_s4.py` (anchor and predecessor checked, predecessors kept).

## Validation

The smoke (flag on: 6/6 deferred then drained; flag off: today), then
`e1_suite.py --self-test`, `py_compile` and `git diff --check`. The 4
runs ran on it. **Verdict REJECTED** (clause a on the link; d
link-INCONCLUSIVE; b, c, e hold).

## Rollback

Restore `companion/plugins/epg.py` from HEAD (`git show
7331184:companion/plugins/epg.py`; the file had no uncommitted change
before this). The runner's three hunks can stay: they are inert without
the flag.

With the flag absent, the companion's behaviour is today's.
