---
memory_schema: 1
as_of: 2026-10-08
status: TASK HANDOFF — E3-S7, queue item 2 (the user's go, 2026-10-08): the CONC remainder after the index — the grabber child's own share of the stream's loss at each grab's start. A probe that separates its CPU from its network traffic; one change behind a flag; benchmark E1-CONC ×2 against a same-night control. Nothing adopted; nothing committed
---

# E3-S7 — the grab's spawn share of the CONC loss

**Measured bottleneck (E3-S6 §1, §3; E3-S6A §2).** With the parse gone
(the adopted index), E1-CONC still loses ~800-1,300 packets/min against
~5-30 for plain streaming, rendered 57.6-58.7, and the aligned frame
still peaks 1-2 s after each grab starts (21-30 lost/s vs 0.08
baseline). The spawn-only probe reproduced that remainder (11-16
lost/s at +1-2 s, busiest core 83 %). E3-S1 showed that taking the
child's CPU priority away, with the parse still present, left the peak
in place; whether CPU priority matters **now** is untested.

**Two hypotheses the probe separates.**

- **CPU**: the child's ~1.7-core, ~2-s start-up (tsx compiling the
  grabber) delays the stream's send threads — the companion's own
  threads or the encoder.
- **Network**: the child's download burst (DNS, TLS, the guide fetch)
  on the same path as the stream — `eno1` → the Opal → the air — costs
  the stream on the router or the air, not on the host. The host has
  no tx drops (E2), which fits.

Read first: `evidence/E3_S6_GUIDE_INDEX_2026-10-07.md` §1 and §3,
`e3_s6_2026-10-07/e3_s6_probe.py` and `probe_aligned.json`,
`evidence/E3_S1_EPG_GRAB_PRIORITY_2026-10-06.md` (the priority flag's
code, dormant), `evidence/E3_S3_GRABBER_COST_2026-10-06.md` (the
start-up split; the grabber's invocation and its options),
`e2_s1_2026-10-05/e2_analysis.py`.

## 1. Probe (measurement first; decides the change)

With a PS1 stream PLAYING, the per-second sampler on, `eno1` tx/rx
bytes per second recorded, three spawn-only arms of ≥ 20 triggers
each at ≥ 15-s spacing, aligned as E3-S6 did:

- **A** — the child as today;
- **B** — the child at `SCHED_IDLE` / nice 19 / idle I/O (E3-S1's flag,
  reused): CPU removed, network as today;
- **C** — the child with its network removed: the grab run against a
  channel whose fetch cannot leave the host (the grabber pointed at an
  unreachable or local-only source so it fails fast after its start-up;
  say exactly how), CPU as today.

**Reading rule, written here:** the arm whose 0-2 s loss falls to
≤ 25 % of A's names the cause: **B** → CPU; **C** → network; both →
both (the change is then the network one, since E3-S1 already measured
the CPU one); neither → report and the change is the network one by
default, said so.

## 2. The one change (by the probe; pre-registered either way)

Behind **`PRIVYHUB_EPG_GRAB_NET=paced`** / **`PRIVYHUB_EPG_GRAB_PRIORITY=idle`**
(one of them; absent = today, byte for byte):

- **Network** → the grabber's own throttle options (the iptv-org
  grabber's connection limit and per-request delay, at their most
  conservative — state the values) and, if the index already answers
  the channel's source list, no metadata download inside the grab;
  the grab's result and status contract unchanged;
- **CPU** → E3-S1's priority flag as the adopted-state candidate, now
  without the parse confound.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-PS1-STREAM ×1 (control), E1-CONC ×2 with the flag
  (E2's windows and gaps; drop-in for those runs only). Task 1's flag
  present in all three if E3-R1 was ACCEPTED (the queue's stated
  exception; said in every table).
- **Comparability (else INCONCLUSIVE):** the control within E1's bands
  of E2's PS1-STREAM.
- **Bar, ACCEPTED only if all hold in both CONC runs:**
  - video loss/min ≤ **100** and ≤ 3 × the control's;
  - rendered ≥ 59.5; resyncs ≤ 10;
  - the aligned frame's 0-2 s mean ≤ 3 × the control's baseline loss/s;
  - grabs failed 0; **every configured channel refreshed ≥ 20 times in
    the window** (a paced grab is slower; the cycle still turns);
    median grab ≤ 2 × E2's (≤ 11.8 s);
  - the guide serves (6 channels; programmes within ± 5 % of a pre-run
    read taken ≥ 60 s after any background refresh — E3-A2's lesson).
- **Reported:** the probe's three arms; the child's CPU and PSS; `eno1`
  tx/rx per second around grabs; underruns; the companion's PSS and CPU.

## 4. The record

`evidence/E3_S7_CONC_GRAB_SPAWN_<date>.md` + `e3_s7_<date>/` per the
queue; `patches/`; `logs/e3_s7_git_status.txt`; the one-line adoption
and its revert. Flag absent; the adopted state restored; then the
queue's close.
