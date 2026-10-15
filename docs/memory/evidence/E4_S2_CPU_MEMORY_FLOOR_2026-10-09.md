---
memory_schema: 1
as_of: 2026-10-09
baseline_commit: 7331184
---

# E4-S2 — the CPU-time and memory floor

> **CPUQuota= is CFS bandwidth.** The stack gets at most N % of one
> core's time per period, on full-speed cores. **This is a CPU-TIME
> floor, not a slow-core floor.** A machine with fewer, equally fast
> cores behaves like this; a machine with slower cores does not, exactly.
> **No lower-tier hardware claim.**

**Classification: FLOOR MEASURED.**

- **The stack's CPU-time floor: 400 %**, set by CONC (a PS1 stream with
  the EPG grab cycle).
- **Without the grab cycle under a stream:** PS1-STREAM 150 %;
  SNES-STREAM and META ≤ 100 %.
- **Memory: ≤ 1G for every row.** 1G passed everywhere, so the memory
  floor was not reached by this ladder. CONC was pinned at 1G with
  swap use.
- 30 runs, all valid; `--check` OK; the decisions are pre-registered.
- Measurement only; nothing adopted, nothing committed.

**Context:**

- Task: `handoffs/E4-S2_CPU_MEMORY_FLOOR_TASK.md`, under
  `handoffs/QUEUE_2026-10-09.md`.
- The reference: `E4_S1_REFERENCE_ON_ADOPTED_STATE_2026-10-09.md`.
- **Baseline commit: `7331184`** (the user's E3-close commit).
- Files: `e4_s2_2026-10-09/`.
- **Timeline (UTC, 2026-10-09):**

  | time | what |
  | --- | --- |
  | 09:17-09:19 | probe A: the 60-s idle check under a drop-in |
  | 09:19-09:21 | probe B, first attempt: a runner bug (below); 6 failed attempts, clean teardowns |
  | 09:21-09:36 | probe B: two 180-s PS1-STREAM runs at 100 % (default vs 10-ms period) |
  | **09:36:17** | **pre-registration hashed** (`f5065ced…314c`) |
  | 09:36-16:48 | the CPU ladder, 18 runs, plus 1 repeat |
  | 16:48-21:37 | the memory ladder, 12 runs |
  | 21:37 | analysis; manifest; `--check` OK; final state clean |

## 1. The floor table

| row | CPU-time floor | the step below: first failing metric | at the floor: CPU used / throttled | memory floor (CPU quota held) | peak at 1G |
| --- | --- | --- | --- | --- | --- |
| PS1-STREAM | **150 %** | 100 %: **encoder dup+drop 0.65/min** (host); rendered 55.1 | 1.12 cores / 0.008 s | **≤ 1G** (200 %) | 221 MB, no events |
| SNES-STREAM (Snes9x) | **≤ 100 %** (100 % passed) | — | 0.61 cores / 0 s | **≤ 1G** (150 %) | 197 MB, no events |
| CONC (PS1 + EPG grabs) | **400 %** | 300 %: **RetroArch 59.872 fps** and **encoder dup+drop 7.5/min** (host) | 2.18 cores / 21 s (1.5 % of periods) | **≤ 1G** (CPU unset) | **1,024 MB, 204 `memory.max` events, 127.5 MB swapped**, 0 OOM kills |
| META (EPG grab cycle) | **≤ 100 %** (100 % passed) | — | 0.71 cores / 793 s (73 % of periods) | **≤ 1G** (150 %) | 966 MB, no events |

- **The stack's CPU-time floor is 400 %**, the maximum over the rows.
  It is set by the grab cycle running under a stream.
  - At 400 %, CONC still had 21 s of throttling: the grab start-up
    bursts exceed four cores of time within a 100-ms period.
  - At 300 % it had 125 s. RetroArch then fell to 59.87 fps and the
    encoder duplicated or dropped 7.5 frames/min. That is the stack
    being starved, not the link.
- **Without concurrent grabs, a stream needs 150 %** (PS1). At 100 %,
  PS1-STREAM used its whole quota and was throttled in 4 % of periods.
  The encoder duplicated or dropped 0.65 frames/min, and the live
  ladder stepped down once (7000 → 5000 kbps, the controller doing its
  job). Loss rose to 1,949/min and rendered fell to 55.1. Probe B saw
  the same at 100 % (dup+drop 2.0/min).
- **SNES on Snes9x needs ≤ 1 core of time**: 0.61 cores, never
  throttled.
- **META alone passes at 100 %.** It is throttled in 73 % of periods, and
  the cycle slows (median grab 7.6 s vs 4.8 s; 26 refreshes per channel
  vs 43), but it still holds every gate (≥ 20 per channel, 0 failed, the
  guide serves).
- **Memory: no row failed at 1G.** The cgroup's own peaks (page cache
  included) were PS1 221 MB, SNES 197 MB, META 966 MB and CONC 1,024 MB.
  - CONC was held at the limit, with reclaim (204 `memory.max` events)
    and 127.5 MB of anon pushed to swap.
  - `MemorySwapMax=` was unset, the task's form, pre-registered. **With
    no swap allowed, CONC at 1G might fail.** Not measured; the next
    step down for memory would answer it (§5).

The full figures:

- `e4_s2_floor.md` (generated);
- `e4_s2_ladder_table.md` (every run, every gate);
- `e4_s2_throttle.md` (the cgroup per run);
- `e4_s2_tables.md` (E2's full table per row: the E4-S1 reference, then
  every step);
- `e4_s2_verdict.json`.

## 2. The ladder, run by run

The control is the 400 % PS1-STREAM run: **40.7 lost/min**. It fails
D-BASE's loss row (< 10), so the link-INCONCLUSIVE clause was live
throughout.

| step | PS1-STREAM | SNES-STREAM | CONC | META |
| --- | --- | --- | --- | --- |
| 400 % | PASS (59.80 fps, 1.07 cores, 0 throttled) | PASS* (capture 58.99, dup+drop 59.9/min, the reference's pattern) | PASS (58.75, 2.18 cores, 21 s) | PASS (43 per channel, 3 s) |
| 300 % | PASS | PASS (capture 59.99) | **FAIL** (RetroArch 59.872, dup+drop 7.5/min; 125 s throttled) | PASS (17 s) |
| 200 % | PASS | PASS | — | PASS (91 s; 40 per channel) |
| 150 % | PASS (0.008 s throttled) | INCONCLUSIVE → repeat **PASS** | — | PASS (326 s; 35 per channel) |
| 100 % | **FAIL** (dup+drop 0.65; rendered 55.08; loss 1,949; 7000 → 5000) | PASS | — | PASS (793 s; 26 per channel; median grab 7.6 s) |
| 4G | PASS (CPU 200 %) | PASS* (CPU 150 %) | PASS (CPU unset; 1,168 MB peak) | PASS (CPU 150 %) |
| 2G | PASS | PASS | PASS (1,163 MB peak) | PASS |
| 1G | PASS (221 MB) | PASS (197 MB) | PASS (**1,024 MB pinned**, 127.5 MB swap) | PASS (966 MB) |

- **The SNES 150 % INCONCLUSIVE.** Only rendered fps failed: 58.21
  against its reference-relative bar of 58.24. Loss was 582/min with 0
  throttling. The repeat at the end of the CPU ladder PASSED: 59.69
  fps, capture 60.02, dup+drop 0.1.
- **\* The SNES reference-relative clause.** E4-S1 found the SNES
  encoder output exactly 59 fps with a drop every second (E4-S1 §4), so
  the pre-registration judges SNES capture and dup+drop against that
  reference.
  - It recurred at 400 % (58.99 fps, 59.9/min).
  - It recurred partly at 150 % (original run) and at 4G (dup+drop
    3.5/min, capture 59.93-59.96).
  - The other SNES runs were clean (60.0, 0.1).
  - **Without the clause, SNES would have FAILED at 400 %.** That failure
    would have been this capture fault, not a CPU limit: SNES uses
    0.61 cores with 0 throttling at every step.
  - The fault is intermittent: 4 of 10 SNES windows today (2 whole
    windows, 2 partly), 0 of 3 in E3. It is a real open item.
- **Validity** (`validity.json`):
  - 30 / 30 valid; 0 replaced attempts.
  - Every run's read-back under the drop-in matched it.
  - After every teardown: `CPUQuotaPerSecUSec=infinity`,
    `MemoryMax=infinity`, `memory.max max`, the drop-in absent.
  - RetroArch and the encoder were in the unit's cgroup at every
    window's start and end.
- **Recovery:** 0 controller pauses in 30 runs; 11 client pauses
  reported.
- **The re-judge** in `e4_s2_analysis.py` agrees with every recorded
  verdict.

## 3. The probe (before the pre-registration)

- **A — the drop-in is accepted and takes effect**
  (`probe/idle_check.json`). At `CPUQuota=100%` + `MemoryMax=4G`:
  - the unit reads `CPUQuotaPerSecUSec=1s`, `MemoryMax=4294967296`;
  - the cgroup gains the cpu controller, with `cpu.max 100000 100000`
    and `memory.max 4294967296`;
  - idle for 60 s: 0.0003 cores, 0 throttled periods.
  - Removed + `daemon-reload` + restart: everything back to
    `infinity` / `max`, the cpu controller off again, the state check
    ok.
- **B — the period** (`probe/period_decision.json`, 180-s smoke runs, not
  data). Both settings stuttered at 100 %:
  - default period: dup+drop 2.0/min;
  - 10-ms period: RetroArch 59.75, rendered 59.37, 63 % of periods
    throttled.
  - By the rule written before B, **the default period** (100 ms) was
    used throughout.
  - Membership: RetroArch and the encoder were inside the constrained
    cgroup in both runs.
- **A runner bug, found and fixed in the probe.** A plan item with a
  constraint and no env flag carried `dropin=None`; `.get("dropin", [])`
  returned None. The first probe B invocation failed 6 attempts before
  launch, each torn down clean (`probe/runs_smoke/`). Fixed before the
  pre-registration; the hashes are in
  `tools_at_preregistration_sha256.txt`.

## 4. Deviations and disclosures

- **Capture fps and dup+drop are segment-aware.** The sampler's own
  figure is first-to-last over the window, and an encoder restart breaks
  it. E3-A3B's PS1 window reads 12.3 fps by it. This was found while
  drafting, before any run, and the pre-registration says so. The
  sampler figure is reported beside, in the ladder table.
- **One control for the session**, as pre-registered. The link varied
  over the 12 h: PS1-STREAM's loss was 34-81/min at the steps it
  passed, and CONC's 515-622/min.
- **E2's 600-s gap before SNES** is not used; the rows interleave.
- **The memory ladder's CPU quotas** follow the CPU floors: PS1 200 %,
  SNES 150 %, META 150 % and CONC unset. CONC's floor is the ladder's
  top step, so nothing above it was constrained.
- **No run was repeated for INCONCLUSIVE on the memory ladder**; none was
  INCONCLUSIVE there.
- A gitignored bytecode cache (`tools/__pycache__`) was removed by me
  early in the session. Python regenerates it; it holds no data.

## 5. A recommended alpha — a proposal, the user's call

The ROADMAP asks for the floor plus reliability, update and concurrency
headroom. Read against this host's per-core speed (the caveat above):

| | floor (measured) | proposed alpha | why |
| --- | --- | --- | --- |
| CPU time for the stack | 400 % (CONC); 150 % for a stream with no grabs | **≥ 6 cores of this speed class** (this host's 4650G class), or 4 cores if the guide grabs are deferred while a stream is live | the grab bursts already exceed 4 cores of time per 100-ms period at 400 %. The stack's cgroup excludes Xorg (~10 % of a core, needed for capture) and pulseaudio. An update or a library scan has no measured slice, so a ~50 % margin |
| memory for the stack | ≤ 1 GB (CONC pinned at 1 GB, swapping 127 MB) | **2 GB for the stack** (no events at 2G); **8 GB system** | the host shows ~4 GB used at IDLE outside the stack (desktop, X, services). 2G was clean in every row |
| GPU | not constrained here | VAAPI H.264 encode at 720p60 (iGPU 18-23 % busy in E4-S1) | the encoder is hardware; a host without VAAPI H.264 is out of scope |

- The proposal is **this host's class with the margin stated**, not a
  lower tier. E4 measured no slower core, no smaller iGPU, and no
  4-core or 4-GB machine.
- **What would lower the CPU floor most** is the grab-under-stream case.
  Its cost is the grabber's start-up burst (E3-S3, E3-S6). Deferring
  grabs while a stream is live would take the stack's floor from 400 %
  to PS1-STREAM's 150 %. That is a design choice for the user, not an
  E4 result.
- **To close the memory floor:** the ladder ended at 1G with every row
  passing. A 768M / 512M step with `MemorySwapMax=0` would find it. Not
  run; it was not in the task's ladder.

## 6. State at the end; files

- **Final state** (`runs/final_state.json`, 21:37:18Z;
  `state_at_end.json`):
  - the four `PRIVYHUB_*` lines in four drop-ins (`adaptive.conf`,
    `epg-index.conf`, `snes-core.conf`, `recovery.conf`);
  - **no `e4_constraint.conf`**; the unit's `CPUQuotaPerSecUSec=infinity`,
    `MemoryMax=infinity`;
  - no `e3_flag.conf`; the manager none;
  - no game, no RetroArch or encoder; the PS1 files identical; **APK
    CONFIRMED**.
- No `sudo`, no `nft`, the Opal untouched. Nothing fetched; no data
  deleted.
- No other task's script was run. E4-S1's table code was copied as
  `e4_s2_tablecopy.py`, with one comment line added.
- **Files** (`e4_s2_2026-10-09/`):
  - `tools_predecessor_sha256.txt`, `tools_at_preregistration_sha256.txt`,
    `e4_s2_tools.diff`;
  - the probe: `e4_s2_probe_idle.py`, `probe/` (`idle_check.json`, the
    probe pre-registration + `.sha256`, `runs_smoke/` (the bug's
    attempts), `runs_smoke2/`, `period_decision.json`);
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`;
  - `e4_s2_ladder.py` (the driver and the pass rule), `ladder.json`,
    `ladder_console.log`, `ladder_stdout.log`;
  - `runs/` (30 runs + the repeat, `manifest.sha256`, `check.txt`,
    `final_state*.json`), `runs_console.log`;
  - `e4_s2_analysis.py`, `e4_s2_tablecopy.py`, `analysis_console.txt`;
  - the outputs: `e4_s2_floor.md`, `e4_s2_ladder_table.md`,
    `e4_s2_throttle.md`, `e4_s2_tables.md`, `validity.json`,
    `e4_s2_verdict.json`;
  - `state_at_end.json`, `redact_check.txt`.
- The tool change: `patches/E4-S2_CONSTRAINT_DROPIN_AND_CGROUP_RUNNER.md`.
- Git status: `logs/e4_s2_git_status.txt`.
