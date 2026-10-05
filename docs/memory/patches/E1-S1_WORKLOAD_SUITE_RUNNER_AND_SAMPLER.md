---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: f60234e
durable_memory_updated: true
---

# E1-S1: the Phase E workload suite runner and sampler set

## Purpose

E1 needs a repeatable workload suite: one command, no hands, the same
inputs, a defined warm-up and window, and one sampler set
(`handoffs/E1-S1_WORKLOAD_SUITE_FREEZE_TASK.md`; record
`evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`; the frozen definition is
`architecture/E1_WORKLOAD_SUITE.md`).

**Nothing in the adopted system changed.**

- No companion code.
- No client code.
- No profile, config or unit change.

## Change

New tools only:

- **`tools/e1_sampler.py`**: the 1-s sampler set and per-run summary
  (mean, p95, max, min per metric).
  - Host data:
    - per-CPU busy, iowait, PSI;
    - memory, swap and swap rates;
    - `/proc/diskstats` for the repository's disk;
    - `/proc/net/dev`;
    - `gpu_busy_percent`;
    - amdgpu `gpu_metrics` v2.x: gfx / VCN activity, socket / CPU / SoC
      power, clocks, temperatures, `throttle_status`;
    - hwmon PPT / Tctl / nvme;
    - cpufreq.
  - Per process category: % of a core, RSS, PSS, RssAnon, threads, IO.
  - Options: `--telemetry` (C2 every 2 s) and `--title` (RetroArch's
    frame counter).
  - Also `--coverage`, `--once`, `summarize`, `--self-test`.
- **`tools/e1_suite.py`**: the runner.
  - It covers the seven pre-registered rows, the ABSENT list, `compare`
    (the repeatability bar), `manifest`, `--check` and `--self-test`.
  - It refuses to run unless the pre-registration's SHA-256 matches.
  - It reuses C5's harness pieces.
  - It writes into the RetroArch config tree only the measurement-only
    counter override, and removes it on every exit path.

**Defects found by the runner smoke, fixed before the real runs:**

- RetroArch's working process is `AppRun`;
- the class cache re-keys on exec (`comm`);
- `gpu_metrics` activities are in hundredths of a percent;
- the title regex.

## Validation

- `E1_SAMPLER_SELF_TEST_OK`, `E1_SUITE_SELF_TEST_OK`.
- The smoke (`runs_smoke/`, not data).
- **The suite**: 14 runs, all OK; 0 missed samples; teardowns clean;
  flags absent at the end; APK confirmed; the adopted PS1 files
  byte-identical.
- **RUNTIME VALIDATED as a repeatable suite for 6 of 7 rows.** E1-CONC is
  NOT YET REPEATABLE, a property of the workload (see the record).

## Rollback

Delete the two tools. Nothing else depends on them.
