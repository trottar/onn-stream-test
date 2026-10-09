---
memory_schema: 1
as_of: 2026-10-08
status: TASK HANDOFF — E3-S7B, queue B item 2 (the user's go, 2026-10-08, "Both"): E3-S7's grab network pacing at a shorter delay. First measure the grabber's effective per-request spacing today and at 1.0 / 1.5 / 4.0 s; then one value behind the same flag; benchmark E1-CONC ×2 against a same-night control under E3-S7's bar unchanged. Nothing adopted; nothing committed
---

# E3-S7B — the grab's network pacing, shorter

**Where E3-S7 left it.** The loss at each grab's start is the child's
network traffic (arm C: the CPU burst with no network made no peak).
`--delay=4000` cut CONC loss from 1,312 to 60-67/min, rendered 57.6 →
59.8, resyncs 52 → 1-3, the per-grab peak ~27 → ~3.7 lost/s — and
slowed the guide cycle 3× (12 refreshes per channel, median grab
14.8-15.1 s), which the bar forbids (needs ≥ 20 and ≤ 11.8 s). The
pre-registration's inference that today's grabs already sleep 3 s per
request was wrong; the effective spacing is not known.

**Narrow hypothesis.** The damage comes from requests sent
back-to-back; a spacing of ~1-1.5 s keeps most of the gain while the
cycle stays within the bar.

Read first: `evidence/E3_S7_CONC_GRAB_SPAWN_2026-10-08.md`,
`e3_s7_2026-10-08/` (`probe.md`, `e3_s7_grab_net_paced.diff`,
`e3_s7_analysis.py`, `e3_s7_preregistration.txt`); the grabber's
invocation (`companion/plugins/epg.py`, `_grab_from_candidate`) and the
grabber's own options.

## 1. Probe: the spacing itself (before the choice)

With the stream idle, one forced grab of one channel at each of: today
(no flag), `--delay=1000`, `1500`, `4000`; `eno1` tx/rx bytes per
100 ms and the child's wall time per grab. Report, per setting: the
number of requests (from the grabber's own log or the byte bursts),
the median and max inter-request gap, the grab's wall time. **State
before the runs** which of 1,000 / 1,500 keeps the median grab ≤ 11.8 s
with margin; if neither, the task's value is the larger one that does
(and say so); if both, **1,500** (the pre-registered preference:
spacing is the lever).

## 2. The one change

E3-S7's flag, one value: **`PRIVYHUB_EPG_GRAB_NET=paced`** with the
delay chosen in §1 (the code reads the value from a second variable
`PRIVYHUB_EPG_GRAB_DELAY_MS`, defaulting to S7's 4000, so both results
stay reproducible; absent flag = today, byte for byte). Nothing else.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-PS1-STREAM ×1 (control), E1-CONC ×2 with the flag (E2's
  windows and gaps; drop-in for those runs only). Task 1's flag present
  in all three if E3-R2 was ACCEPTED (the queue's exception; said in
  every table).
- **Comparability (else INCONCLUSIVE):** the control within E1's bands
  of E2's PS1-STREAM.
- **Bar — E3-S7's, unchanged, ACCEPTED only if all hold in both CONC
  runs:** loss/min ≤ 100 and ≤ 3 × the control's; rendered ≥ 59.5;
  resyncs ≤ 10; the aligned 0-2 s mean ≤ 3 × the control's baseline
  loss/s; grabs failed 0, every channel ≥ 20 refreshes, median grab
  ≤ 11.8 s; the guide serves (6 channels; programmes ± 5 % of a pre-run
  read taken ≥ 60 s after any background refresh).
- **Reported:** the probe's spacing table; the aligned frame beside
  S7's and S6A's; the child's CPU and PSS; `eno1` rx per second; the
  companion's PSS and CPU; socket W.

## 4. The record

`evidence/E3_S7B_GRAB_PACING_SHORT_<date>.md` + `e3_s7b_<date>/` per
the queue; `patches/`; `logs/e3_s7b_git_status.txt`; the one-line
adoption (two drop-in lines: the flag and the delay) and its revert; if
REJECTED, the table of loss vs cycle speed across today / 1,500 / 4,000
so the user can choose a point. Flag absent; the adopted state
restored; then the queue's close.
