---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S1, queue item 1 (the user's go, 2026-10-06): the EPG grab's start-up burst vs the live stream. One change behind a flag: the grabber child at the lowest CPU priority. Benchmark E1-CONC ×2 with the flag, E1-META ×1 with the flag, E1-PS1-STREAM ×1 as the same-night control. Accept/reject by the pre-registered bar. Nothing adopted; nothing committed
---

# E3-S1 — the EPG grab's start-up vs the live stream

**Measured bottleneck (E2-S1 §3).** During each grab body the busiest
core rises first (offset 0 s) and most (~75 % at 1-2 s, +5.2 sd), the
stream's loss peaks at 1 s (~65 packets/s vs 0.55 baseline), with no
host tx drops, no encoder dup/drop and a flat relay thread. E1-CONC:
loss ~1,600/min vs ~30, rendered 56.5 fps, ~200 resyncs and ~300-450
underruns per 20 min.

**Narrow hypothesis (E2's, one sentence).** The grab's start-up (npm,
then node) saturates one core for ~1-3 s and delays the stream's
send-side threads at sub-second scale; the resulting send bursts are
lost on the wireless hop.

**The one change.** The grabber child runs at the lowest CPU priority:
`SCHED_IDLE` (`chrt -i 0`, or `os.sched_setscheduler` on the child
before exec) plus `nice 19` and `ionice -c 3`, applied to the `npm run
grab` process tree the companion spawns — **behind
`PRIVYHUB_EPG_GRAB_PRIORITY=idle`** (absent = today's spawn, byte for
byte). No core pinning, no deferral: those are separate hypotheses for
later tasks if this one is rejected.

Read first: `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` §3 and §8,
`e2_s1_2026-10-05/e2_conc.md`, `e2_preregistration.txt`, the companion's
EPG plugin (the spawn site of the grabber child; `TOOLS.md` ~line 1673),
`architecture/E1_WORKLOAD_SUITE.md`, `tools/e1_suite.py --e2`,
`QUEUE_2026-10-06.md`.

## 1. Probe (measurement, before the change)

One forced grab with the stream idle, the per-second per-thread sampler
on: confirm the spawn chain (companion → `npm` → `node`), its policy and
nice as spawned today, and the CPU-seconds of the first 3 s of the grab
by process. Record in `e3_s1_<date>/probe.md`. If the chain is not what
E2 inferred, the record says so and the change is applied to what is
actually spawned.

## 2. Pre-registration (hashed before any run)

`e3_s1_<date>/e3_s1_preregistration.txt`:

- **Runs, in order, E2's windows (20 min) and gaps**: E1-PS1-STREAM ×1
  (flag absent; the control), E1-CONC ×2 (flag set), E1-META ×1 (flag
  set; the grabs must still get done). The flag is set in the companion's
  environment for those runs only (a drop-in that is removed and
  `daemon-reload`ed at the run's teardown; the environ check is part of
  the teardown), absent after.
- **Bar, ACCEPTED only if all hold:**
  - E1-CONC video loss/min ≤ **100** in both runs **and** ≤ 3× the
    control's loss/min;
  - E1-CONC rendered fps ≥ **59.5** in both runs;
  - E1-CONC sequence resyncs ≤ 10 per run (E2: ~200);
  - E1-META and E1-CONC grabs failed = 0, grabs ok ≥ 90 % of E2's count
    for that row (META ≥ 205; CONC ≥ 187), median grab ≤ 1.5× E2's (META
    ≤ 7.8 s; CONC ≤ 8.8 s) — the cost of the priority, bounded;
  - the control's own row within E1's bands of E2's PS1-STREAM (host CPU
    ± 2, rendered ± 0.5) — otherwise the night is not comparable and the
    task is **INCONCLUSIVE**, not rejected.
- **Reported, not gated:** the busiest-core-per-second p95 (E2: 96-97),
  the aligned 0-5 s frame from E2's analysis re-run on the new CONC runs
  (`e2_analysis.py`'s CONC section pointed at the new dir), audio
  underruns, max output gap, the ladder's decisions.

## 3. The change

The spawn site only. A diff of ≤ ~20 lines. Unit tests if the plugin
has them. Recorded in `patches/E3-S1_EPG_GRAB_PRIORITY.md`.

## 4. The runs, the record

`tools/e1_suite.py --e2 --plan ...` with the pre-registration hash
checked. Record `evidence/E3_S1_EPG_GRAB_PRIORITY_<date>.md` per the
queue's "Per task, the record": the probe's finding, the change, the
table (control / CONC r1 / CONC r2 / META, with E2's columns beside),
the aligned frame, **ACCEPTED / REJECTED / INCONCLUSIVE** by the bar, the
one-line adoption the user would be saying yes to (the drop-in line) and
its revert. `logs/e3_s1_git_status.txt`. Flag absent; E2's final state
restored; then queue item 2.
