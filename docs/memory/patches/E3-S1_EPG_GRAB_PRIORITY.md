---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
durable_memory_updated: true
---

# E3-S1: the EPG grabber at the lowest CPU and I/O priority, behind `PRIVYHUB_EPG_GRAB_PRIORITY=idle`

## Purpose

E3's first item (`handoffs/E3-S1_EPG_GRAB_PRIORITY_TASK.md`, record
`evidence/E3_S1_EPG_GRAB_PRIORITY_2026-10-06.md`): test E2's hypothesis
that each grab's start-up burst delays the stream's send threads.

**One change, behind a flag; absent = today's argv, byte for byte. NOT
ADOPTED.**

## Change

**`companion/plugins/epg.py`, `_grab_from_candidate`** (the grab's spawn
site only, +17 / −11 lines, `e3_s1_2026-10-06/e3_s1_epg_grab_priority.diff`):

- the `npm run grab …` argv is built into `args` (same list as before);
- with `PRIVYHUB_EPG_GRAB_PRIORITY=idle` in the companion's environment
  it is prefixed with `/usr/bin/chrt -i 0 /usr/bin/nice -n 19
  /usr/bin/ionice -c 3`. Each wrapper execs the next, so the pid is the
  companion's direct child as before, and npm, sh and both node processes
  inherit SCHED_IDLE, nice 19 and the idle I/O class (probe smoke:
  all eight processes of a two-attempt grab).

**Tools (measurement only):**

- `tools/e1_suite.py`: a 4th `--plan` field `KEY=VAL[+KEY=VAL]` — the
  run's flag(s), written to the unit drop-in `e3_flag.conf` before the
  run's restart and removed + `daemon-reload` + restart at its teardown
  (checked: the file gone, the flag not in the environ, the environ
  exactly the live default); flagged runs go to `<ID>_flag/`; preflight
  and the final state require the drop-in absent; `--check` covers the
  `_flag` directories.
- `tools/e3_probe.py` (new): `tree` (a forced grab's process tree every
  ~50-80 ms: policy, nice, I/O class, CPU-seconds, RSS/PSS, first TCP
  socket) and `threads` (a process's per-thread context switches and
  schedstat).
- `tools/e3_table.py` (new): E2's table rows over any runs, plus the
  companion's PSS first/last, its thread roles and the EPG cost per grab.

## Validation

- `py_compile`; `e1_suite.py --self-test`.
- The probe smoke with the flag set (not data), then the drop-in removed:
  environ back to the live default only.
- The benchmark: see the evidence record.

## Rollback

Unset the flag (delete the drop-in line, `daemon-reload`, restart). To
remove the code, revert `companion/plugins/epg.py` to `d9fdbdd`
(sha256 `342a179c…14ee`).
