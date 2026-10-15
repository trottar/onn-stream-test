---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 7331184
durable_memory_updated: true
---

# E4-S2: the runner writes a per-run constraint drop-in and records the cgroup (tools only)

## Purpose

E4-S2 (`handoffs/E4-S2_CPU_MEMORY_FLOOR_TASK.md`, record
`evidence/E4_S2_CPU_MEMORY_FLOOR_2026-10-09.md`) constrains the
companion's unit one run at a time, with `CPUQuota=` and `MemoryMax=`
in a `systemd --user` drop-in. Nothing in the companion changes.

## Change

**`tools/e1_suite.py`** (measurement tool; predecessor `334528a3…b186`,
now `1b3570f7…0e72`; diff `evidence/e4_s2_2026-10-09/e4_s2_tools.diff`):

- **The constraint.** A `--plan` item's 5th field
  (`ID:runs:gap:flags:CPUQuota=N%[+MemoryMax=X][+CPUQuotaPeriodSec=Nms]`;
  nothing else is accepted) is the run's constraint.
  - It is written to `privyhub-companion.service.d/e4_constraint.conf`
    before the run's restart.
  - The unit's `CPUQuotaPerSecUSec` / `CPUQuotaPeriodUSec` /
    `MemoryMax` and the cgroup's `cpu.max` / `memory.max` are read back
    before, under (the run is refused if they don't match) and after.
  - It is removed + `daemon-reload` + restart at the teardown, on every
    exit path.
  - The run directory is `<ID>_cpuN[_memX]`.
- **The state check gains "no `e4_constraint.conf`"**: the preflight
  (so `tools/e3_state.py` too), the teardown's `flags_absent`, and the
  final state, which also records the unit's properties.
- **`--e2` additions:**
  - `cgroup.jsonl`: the unit's cgroup every 5 s (`cpu.stat` throttling,
    `memory.current/peak/swap.current`, `memory.events`);
    `key.cgroup` holds the window's deltas.
  - RetroArch's and the encoder's cgroup membership at the window's
    start and end.
  - Per stream run, the window's slices of the gap log and the recovery
    log (`gaps.jsonl`, `recovery.jsonl`; `key.gaps`, `key.recovery`).
  - META / CONC read the guide at the window's end (`guide_at_end`, as
    `tools/e3_guide_read.py`).
  - `key.epg.grabs_ok_per_channel`.
- A later invocation into the same `--out` continues the run numbers
  (it never overwrites a run).
- Fixed during the probe: a plan item with a constraint and no flag
  carried `dropin=None`. The first probe B attempts failed on it, with
  clean teardowns (`probe/runs_smoke/`).

**`tools/e3_state.py`:** docstring only.

## Validation

`e1_suite.py --self-test` OK; `git diff --check` clean. Probe A (idle)
and probe B (two 180-s runs): the drop-in takes effect and is lifted
both ways, and the environ stays the four adopted lines.

## Rollback

`git checkout 7331184 -- tools/e1_suite.py tools/e3_state.py`. No
companion file was touched.
