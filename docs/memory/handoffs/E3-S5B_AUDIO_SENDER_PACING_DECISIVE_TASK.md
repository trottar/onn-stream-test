---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S5B, queue B item 1 (the user's go, 2026-10-06): decide E3-S5. The same change (`PRIVYHUB_AUDIO_SENDER_PACING=frame`, already in the tree), no code change; five interleaved 20-min runs of E1-PS1-STREAM (control, flag, control, flag, flag) and a send-timing probe, under a new pre-registered bar that separates a link episode from an effect of the change. Nothing adopted; nothing committed
---

# E3-S5B — the audio sender's pacing, decided

**Where E3-S5 left it.** The change cut the sender from 13.1 to 2.5 %
of a core and the companion from 24.8 to 14.6 %, −1-2 W, underruns and
fps fine. Flag run 1 had bursty loss (106.5/min, 7 minutes > 100);
flag run 2 was clean (22.9/min, 1 minute). One control (29.6/min, 1
minute). REJECTED on clause (c) in run 1; two runs could not say
whether the bursts were the link or the change. The record notes the
change alters **when** the 400 audio datagrams per second leave.

**The question, in one sentence.** Does `=frame` make the stream's
loss burstier than the unchanged sender on the same night, or not?

**No new change.** The flag and its code are E3-S5's, unchanged
(`companion/native_session_io.py`, the diff in `e3_s5_2026-10-06/`).
Read first: `evidence/E3_S5_AUDIO_SENDER_COST_2026-10-06.md`,
`e3_s5_2026-10-06/probe.md`, `loss_per_minute.txt`,
`e3_s5_preregistration.txt`, `e3_s5_analysis.py`.

## 1. Probe: the send timing itself (before the runs)

The bursts, if the change causes them, come from how the datagrams are
spaced. With a PS1 stream PLAYING, 60 s without the flag and 60 s with
it (a flagged restart of the unit between, drop-in removed after):

- the sender's inter-send gaps (a timestamp per `sendto`, through the
  existing probe hook or a 60-s `PRIVYHUB_AUDIO_SEND_TRACE=<path>` the
  task adds and leaves off): count, median, p99, max gap, and the count
  of gaps > 10 ms and > 20 ms;
- the number of datagrams sent back-to-back (< 0.2 ms apart) — the
  bunching the one timed wait could cause if it oversleeps.

`e3_s5b_<date>/probe.md`, reported beside the bar. If the flagged
sender shows gaps > 20 ms or bunches ≥ 4 datagrams at a rate ≥ 10× the
unflagged one, say so before the runs: it is the mechanism the bar will
then be testing.

## 2. Pre-registration (hashed before any benchmark run)

- **Runs, in this order, E2's window and gaps, all E1-PS1-STREAM:**
  C1 (no flag), F1 (flag), C2 (no flag), F2 (flag), F3 (flag). The flag
  through the drop-in for F runs only, removed at each teardown, the
  environ checked.
- **Comparability (else INCONCLUSIVE):** both controls within E1's
  bands of E2's PS1-STREAM (host CPU 11.7 ± 2; rendered 59.81 ± 0.5), and
  the two controls within ± 0.5 fps of each other.
- **Bar, ACCEPTED only if all hold:**
  - (a) in every F run: sender ≤ 4 % and companion ≤ 17 % of a core;
  - (b) in every F run: audio underruns ≤ max(control) + 5 and ≤ 20;
  - (c) in every F run: rendered ≥ 59.5, RetroArch 60 ± 0.5;
  - (d) **loss, the deciding clause, on the pooled minutes:** the three
    F runs' 60 minutes against the two C runs' 40 minutes —
    - median loss/min of F ≤ 3 × median of C, **and**
    - the share of minutes with > 100 lost packets in F ≤ the share in
      C + 0.10 (i.e. at most ~6 extra bursty minutes in 60 beyond the
      controls' own rate);
  - (e) D-BASE: spikes ≥ 20 ms/min < 200 and stale drops/min < 20 in
    every F run (the loss row reported, not gated, as in E3-S5).
- **Reported:** the per-run loss table and the per-minute lists, the
  probe's gap statistics, socket W, max output gap, the C2 block, the
  ladder's decisions (any FALLBACK during an F run is reported with its
  minute).

The pooled form is chosen because one run's bursts are what E3-S5 could
not interpret; it is written here before the data and not changed after.

## 3. The runs, the record

`tools/e1_suite.py --e2 --plan ...` with the hash checked. Record
`evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_<date>.md` +
`e3_s5b_<date>/` (probe, pre-registration + `.sha256`, 5 runs,
`manifest.sha256`, `--check`, `e3_s5b_table.md/.json`,
`e3_s5b_verdict.json`, `loss_per_minute.txt`, `redact_check.txt`):
the verdict, the one-line adoption
(`Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame`) and its revert, and
— if REJECTED — whether the probe's mechanism explains it.
`logs/e3_s5b_git_status.txt`. Flag absent; E2's final state restored;
then queue item 2.
