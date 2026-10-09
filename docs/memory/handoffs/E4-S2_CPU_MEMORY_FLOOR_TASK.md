---
memory_schema: 1
as_of: 2026-10-09
status: TASK HANDOFF — E4-S2, queue item 2: the measured floor, approached from inside this host with no sudo — `CPUQuota=` and `MemoryMax=` drop-ins on the companion's unit (which holds the companion, RetroArch and the encoder), stepped down until a suite row fails the pre-registered pass rule. A CPU-time and memory floor, stated as such; no lower-tier hardware claim. Measurement only; nothing adopted; nothing committed
---

# E4-S2 — the CPU-time and memory floor

**What E3-A3 measured** (`e3_a3_2026-10-09/cgroup_*.txt`): the user
manager delegates `cpu`, `memory`, `pids` — **not `cpuset`**; the
companion, RetroArch (with its AppRun wrapper) and the encoder all
live in `app.slice/privyhub-companion.service`, one cgroup. So a
`systemd --user` drop-in on that unit with `CPUQuota=` and `MemoryMax=`
constrains the whole stack. `AllowedCPUs=` cannot (not delegated).

**What this measures, and what it does not.** `CPUQuota=` is CFS
bandwidth: the stack gets at most N % of one core's time per period,
on full-speed cores. That is a **CPU-time floor**, not a slow-core
floor: a machine with fewer, equally fast cores behaves like this; a
machine with slower cores does not, exactly. The record says so in
its first lines, every time the floor is quoted. Memory is closer to
real: `MemoryMax=` is a hard limit with reclaim and OOM.

Read first: the E4-S1 record (the reference on the adopted state —
the pass rule compares against it); `evidence/D_BASE_CLOSEOUT_2026-09-23.md`;
`architecture/E1_WORKLOAD_SUITE.md` §5 (bands); `TOOLS.md` (the unit,
the drop-ins, kill switches); `tools/e1_suite.py`.

## 1. Probe (before the pre-registration)

- Confirm, read-only, that a drop-in with `CPUQuota=` and `MemoryMax=`
  is accepted by the user manager and takes effect on the companion's
  cgroup (`cpu.max`, `memory.max` in the cgroup files) — a 60-s idle
  check at `CPUQuota=100%`, then removed. Also `CPUQuotaPeriodSec=`:
  use the default period unless the probe shows the stream stutters at
  the default and not at a shorter one; say which.
- Confirm RetroArch and the encoder are still inside the cgroup under
  the drop-in (they are spawned by the companion; a re-check).
- The drop-in's name `e4_constraint.conf`, written and removed per run;
  the state check gains "no `e4_constraint.conf`" at every teardown.

## 2. Pre-registration (hashed before any constrained run)

- **Rows**: PS1-STREAM, SNES-STREAM, CONC, META — the streaming row, the
  emulator row, the contended row, the heaviest background row. 20-min
  windows, E2's warm-ups and gaps.
- **The CPU ladder**, descending, each step all four rows: `CPUQuota=`
  **400 %, 300 %, 200 %, 150 %, 100 %** (`MemoryMax=` unset). Stop
  descending a row once it has failed at a step (its floor is the last
  passing step); stop the ladder when every row has failed or 100 % has
  passed.
- **The memory ladder**, after the CPU ladder, at the CPU quota one
  step above each row's CPU floor (so memory is the only constraint
  binding): `MemoryMax=` **4 G, 2 G, 1 G** (the stack's measured PSS at
  the reference is ~0.4-1.2 GB, so 1 G is expected to bind). Same stop
  rule.
- **The pass rule per run**, written here:
  - the row reaches PLAYING (streams) or runs (META) and is valid
    (E3-A3B's reading);
  - **host-side rows** (the ones a weaker host would break): rendered
    fps ≥ 59.5 and RetroArch ≥ 59.9 and capture 60 ± 0.5 (stream rows);
    spikes ≥ 20 ms/min < 200 and stale drops/min < 20 (D-BASE);
    encoder dup+drop ≤ 0.2/min; for META: grabs failed 0 and every
    channel refreshed ≥ 20 times and the guide serves; for CONC: as
    PS1-STREAM plus grabs failed 0;
  - **not gated**: video loss/min, resyncs, underruns (the link's;
    reported with the same-night PS1-STREAM at 400 % as the control),
    and `cpu.stat` throttled time (reported: how much the quota bit).
  - A run that fails only because the link was bad (the control fails
    D-BASE's loss row) is INCONCLUSIVE and repeated once at the end.
- **The floor per row** = the smallest quota (and the smallest
  `MemoryMax=`) at which the row passes. **The floor of the stack** =
  the maximum over rows. Stated with the throttled-time figures beside
  it, so the headroom is visible.
- **Reported throughout**: the full E2 table per run; the ladder's
  decisions (does the adaptive bitrate step down under the quota —
  that is the controller doing its job and is part of the finding);
  socket W; Tctl.

## 3. The runs

`tools/e1_suite.py --e2` with the drop-in written before each run and
removed at its teardown (`daemon-reload` + restart both ways; the unit's
`CPUQuotaPerSecUSec` and `MemoryMax` read back each time). The order:
the CPU ladder top-down, four rows per step, with the 400 % PS1-STREAM
as the control for its night; then the memory ladder. ~8 h; if the
ladder ends early, say where.

## 4. The record

`evidence/E4_S2_CPU_MEMORY_FLOOR_<date>.md` + `e4_s2_<date>/` (the
probe, the pre-registration + `.sha256`, every run, `manifest.sha256`,
`--check`, `validity.json`, the throttle stats, the ladder table,
`e4_s2_verdict.json`, `redact_check.txt`): **the floor table** (per
row: CPU floor, memory floor, the first failing metric at the step
below, throttled time at the floor), the stack's floor, the caveat in
the first lines, and what a **recommended alpha** would need on top
(the ROADMAP: reliability, update and concurrency headroom — a
proposal, the user's call). `docs/ROADMAP.md` E4: floor measured;
`investigations/ACTIVE.md`; `logs/e4_s2_git_status.txt`;
`CURRENT_HANDOFF.md`; the redactor; **`CURRENT.md` last** — Next
Action 1: the user's commit; 2: the user's reading of the floor and
the alpha proposal; 3: E5 (capability detection) as the ROADMAP has
it. The final state is the four-line adopted state, no
`e4_constraint.conf`, no game, PS1 files identical, APK CONFIRMED.
