---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S4, queue item 2: grab deferral while a stream is live, measured as an E3-style change behind a flag. If the EPG grabber does not run while a native stream session is PLAYING, the CONC row becomes a plain stream and the stack's CPU-time floor falls from 400 % to 150 % — the alpha spec's 6 cores vs 4. One change behind `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`; the control, CONC ×2 with the flag, CONC ×1 with the flag at `CPUQuota=150%`. Pre-registered bar. Nothing adopted; nothing committed
---

# E4-S4 — grab deferral while streaming

**Why.** E4-S2: the stack's CPU-time floor is 400 %, set entirely by
the EPG grab cycle running under a stream (CONC); a stream alone needs
150 %. E3-S7/S7B: the grabs' damage to a live stream is their network
burst, and pacing could not keep both the stream and the guide cycle.
The ROADMAP's E3 list named "concurrency policies" as a lever. The
simplest policy: **no grab while a stream is PLAYING**; deferred grabs
run when the stream ends. The guide goes stale by at most the length
of a play session plus the cycle — for a user playing a game, that is
nothing they see.

**The one change, behind `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`**
(absent = today, byte for byte):

- the EPG plugin checks the native stream recovery state before
  spawning a grabber (the same state E3-R2's trigger reads): if a
  session is PLAYING or PAUSED_*, the grab (forced refresh or
  background cycle) is **queued, not run**, and the refresh endpoint
  answers with a "deferred" status that the client already tolerates
  (say which status; the status endpoint shows `deferred: N`);
- when the session ends (`session_ended`), the queue drains in order,
  one grab at a time, as today's cycle would;
- a grab that is already running when a stream starts is not killed;
- a cap: a deferral older than **60 min** runs anyway (a safety valve;
  reported if it ever fires).

Read first: `evidence/E4_S2_…` §5; `E3_S7_…`, `E3_S7B_…`; the EPG
plugin's refresh and background paths (`companion/plugins/epg.py`),
the recovery state source (`companion/plugins/games.py`,
`native_session_io.py`), `tools/e1_suite.py`'s CONC row (the forced
refresh cycle starts 30 s after PLAYING — with the flag that cycle's
calls return "deferred"; the row then measures a stream with a
deferred queue, and the drain after teardown is part of the run's
teardown record).

## 1. Smoke (before the pre-registration)

With the flag: start a PS1 stream, force six refreshes, confirm all six
are deferred (status shows 6), stop the stream, confirm the six run
and complete within the expected time, the guide serves, the companion's
state is clean. Without the flag: the six run immediately (today). Both
in `smoke.jsonl`.

## 2. Pre-registration (hashed before any benchmark run)

- **Runs**, E2's windows and gaps: E1-PS1-STREAM ×1 (no flag; the
  control), **E1-CONC ×2 with the flag** (unconstrained), **E1-CONC ×1
  with the flag at `CPUQuota=150%`** (the drop-in as E4-S2; removed at
  teardown). Each CONC teardown waits for the deferred queue to drain
  and records it (count, wall time, ok/failed).
- **Comparability (else INCONCLUSIVE):** the control within E1's bands
  of E4-S1's PS1-STREAM (host CPU 10.9 ± 2; rendered 59.53 ± 0.5).
- **Bar, ACCEPTED only if all hold:**
  - (a) CONC with the flag, both runs: video loss/min ≤ 3 × the
    control's and ≤ 100; rendered ≥ 59.5; resyncs ≤ 10; host CPU within
    ± 2 of the control's (it should *be* a plain stream);
  - (b) deferral did what it says: during each CONC window **0 grabber
    processes** were spawned (the per-second sampler; the EPG child
    rows absent), the status showed the queue growing, and after
    teardown the queue drained with **failed 0** and every queued
    channel refreshed, within 2 × the cycle's normal time for that many
    grabs;
  - (c) the guide serves after the drain (6 channels; programmes ± 5 %
    of a pre-run read taken ≥ 60 s after any background refresh);
  - (d) **CONC with the flag at `CPUQuota=150%` passes E4-S2's pass
    rule** (the row behaves as PS1-STREAM did at 150 %: rendered ≥
    59.5, RetroArch ≥ 59.9, dup+drop ≤ 0.2/min, spikes < 200, stale
    < 20), with its throttled time reported;
  - (e) the companion's stream cost within ± 2 points of a core of the
    control's.
- **Reported:** the deferral cap (should never fire), the queue's
  drain times, the client's pauses, the gap log.

## 3. The record

`evidence/E4_S4_GRAB_DEFERRAL_<date>.md` + `e4_s4_<date>/` (the smoke,
the diff, the pre-registration + `.sha256`, 4 runs, `manifest.sha256`,
`--check`, `validity.json`, table, verdict, `redact_check.txt`); the
verdict; **what the alpha spec becomes if adopted** (the stack's
CPU-time floor 150 %; the record restates E4-S2 §5's table with the
deferral line); the one-line adoption
(`Environment=PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`) and its revert;
`patches/`; `logs/e4_s4_git_status.txt`. Flag absent; the adopted state
restored; then queue item 3.
