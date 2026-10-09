---
memory_schema: 1
as_of: 2026-10-09
status: TASK HANDOFF — E4-S1, queue item 1: the known-good reference, re-measured once on the adopted state (live, the guide index, Snes9x, recovery v2) with E2's instrumentation, every runnable row of the frozen suite at the 20-min window; the E4 reference table with E2's numbers beside. Measurement only; nothing adopted; nothing committed
---

# E4-S1 — the reference on the adopted state

**Why.** E2 measured this host (the EliteDesk 4650G/16 GB) before any
E3 change. Since then the system changed in ways that move the
reference: the guide index (companion 161 → 34 MB in META, 7.6 → 0.2 %
of a core), Snes9x (SNES host CPU 43-50 → 8 %, ~−6.5 W), recovery v2
(no false pauses; a gap log). The ROADMAP's E4 "known-good reference"
must describe the system as it is. No floor claim here.

Read first: `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` (§2 the table,
§6 the reference), `e2_s1_2026-10-05/e2_preregistration.txt` and
`e2_analysis.py`, `architecture/E1_WORKLOAD_SUITE.md`, `tools/e1_suite.py
--e2`, `CURRENT.md` (the four-line adopted state and its state checks).

## 1. Pre-registration (hashed before any run)

- **Runs**: E2's order and gaps — IDLE, PS1-LOCAL, PS1-STREAM,
  PS1-1080P (its rung flag for that row only, entry injected after
  ≥ 60 s, confirmed 1920×1080, unset after — as E2 did), META, VOD,
  SNES-STREAM, CONC; **one run each**, 20-min windows, E2's warm-ups and
  teardowns. The adopted defaults run; no E3 task flag anywhere.
- **The table**: every E2 metric (host CPU mean/p95, per-core p95,
  PSI, per-process CPU and PSS, GPU, encoder headroom, disk, `eno1`,
  the C2 block and decoder rows, Tctl/throttle, socket/CPU/SoC W),
  **plus** the gap log's count / > 1 s / max per stream row and the
  recovery events (client pauses reported with resume times;
  controller pauses expected 0). E2's column beside each row.
- **No bar.** This is a reference, reported. Two things are checked
  and said: (a) the D-BASE close-out table on PS1-STREAM (spikes < 200,
  stale < 20, rendered ≥ 59.5; the loss row by this night's own
  numbers, reported); (b) each row's validity.
- **Stated in the record, verbatim:** "the known-good reference for
  this host on the adopted state, 2026-10-09; no floor and no
  lower-tier claim."

## 2. Analysis

`e2_analysis.py`'s table section, copied and pointed at these runs
(`e4_s1_analysis.py`), with the E2 columns from `e2_s1_2026-10-05/`
beside; the CONC aligned frame as before. **Drift from E2 is itself the
finding**: list every metric that moved by more than E1's bands and say
which adoption explains it (or that nothing does).

## 3. The record

`evidence/E4_S1_REFERENCE_ON_ADOPTED_STATE_<date>.md` + `e4_s1_<date>/`
(the pre-registration + `.sha256`, 8 runs, `manifest.sha256`, `--check`,
`validity.json`, the gap logs, `e4_s1_table.md/.json`, the drift list,
`redact_check.txt`): the E4 reference table in the ROADMAP's four-row
form (idle / streaming / contended / heaviest) with the full table
behind it; `docs/ROADMAP.md` E4: "reference re-measured";
`logs/e4_s1_git_status.txt`. The final state is the four-line adopted
state; no game; PS1 files identical; APK CONFIRMED; then queue item 2.
