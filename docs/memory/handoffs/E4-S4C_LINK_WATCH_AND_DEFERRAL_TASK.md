---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S4C, queue item 2: a LINK WATCH until 2026-10-15T04:00Z (Wednesday midnight US Eastern; the user is home Thursday). A 5-min PS1 stream probe every 45 min, around the clock, with a continuous ping trace between probes and the air/client readings O1 and D-BASE P4 used; the deferral re-verification (E4-S4B's gate, runs and bar, verbatim) launched on the first clean window and finished on clean windows; the probing continues after the verdict until the cap. Two products: the deferral verdict (or INCONCLUSIVE if no window is ever clean) and **the link history by hour and day** — why clean nights are inconsistent. Nothing adopted; nothing committed
---

# E4-S4C — the link watch, and grab deferral on the first clean window

**Why.** No stream run since 10-09 has met D-BASE's loss row (< 10/min;
reference 8.4): E4-S4's four, E4-S5's five, E4-S3B..S4B's eleven, all
between 39 and 2,459/min, with no obvious time pattern in a dozen points.
E4-S4B waited 3.5 h and never saw a clean control. A clean window cannot
be scheduled; it has to be caught. And the history of a link sampled
every 45 min for four and a half days is itself the finding the user
wants: when it is clean, when it is not, and what else moves with it.

Read first: `evidence/E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_2026-10-10.md`,
`e4_s4b_2026-10-10/e4_s4b_run.py` (the gate and its retry),
`e4_s4b_preregistration.txt`, `E4_S4_…` (the bar), `O1_OPAL_AIR_VIEW_…`
(what the Opal's status pages give, read-only), `D_BASE_P4_AIR_TELEMETRY_…`
(the client's RSSI / link rate as read then), `LINK_L1_…` / `LINK_L2_…`
(the loss row's history), `docs/KNOWN_ISSUES.md` LINK.

## 1. Pre-registration (hashed before the first probe)

**The probe.** E1-PS1-STREAM with E2's warm-up and a **300-s window**
(`--window 300`), every **45 min start-to-start**, from the hash to the
cap. Per probe (`link_watch.jsonl`, one row): UTC and US-Eastern time,
hour-of-day, day; loss/min, rendered, resyncs, stale/min, spikes/min, the
client's pauses, underruns; host CPU, socket W, host and client temps;
**the air**: the Opal's status readings as O1 took them (channel, width,
utilisation, client count, the client's RSSI / rate / retries if shown —
read-only, nothing changed, no identifiers written); **the client**: RSSI
/ link speed as D-BASE P4 read them; **the ping trace's** loss % and RTT
median / p99 over the 40 min before the probe. A probe that never reaches
PLAYING is retried once, then recorded as `no_play` and skipped.

**The ping trace.** From the hash to the cap, 1 echo/s from the host to
the client (no sudo: the unprivileged `ping` as installed; if it is not
permitted, say so and skip the trace), `ping.jsonl` in 60-s bins (sent,
lost, RTT min / median / p99). It runs through probes and runs alike and
is tagged with what was running.

**Clean** (the gate; E4-S4B's reading): a probe with loss/min < 10 **and**
rendered ≥ 59.5 **and** resyncs ≤ 2 (a 5-min window). A control (20 min)
is clean by E4-S4B's gate (loss < 10, rendered ≥ 59.5, resyncs ≤ 10).

**The deferral runs, launched by the watch:**
- on the first clean probe → the **control** (E1-PS1-STREAM, 20 min, no
  flag). If the control is not clean: back to probing (the next probe 45
  min after the control started).
- after a clean control → **E1-CONC ×2 with the flag, then E1-CONC ×1 with
  the flag at `CPUQuota=150%`**, E2's gaps, each teardown draining the
  deferred queue and recording it; the drop-in as E4-S2, removed at
  teardown; the pre-run guide read taken ≥ 60 s after any background
  refresh, before the first flagged run.
- a flagged run whose link goes bad (loss/min > 3 × the control's **and**
  > 100) is marked `link_voided`, its host-side clauses recorded on their
  own, and it is **re-run on the next clean probe** — at most 2 re-runs
  per flagged run, then the set is judged with what it has (a voided run
  = INCONCLUSIVE on its link clauses, its host clauses still read).
- **Bar = E4-S4's, verbatim** (clauses (a)-(e); comparability of the
  control to E4-S1's PS1-STREAM; ACCEPTED only if all hold on a clean
  set). Written once, judged once, when the set is complete.
- **After the verdict, the probing continues** until the cap; no further
  flagged run. If no probe is ever clean: INCONCLUSIVE (link), with the
  history.

**Storage.** A probe's run directory goes **outside the repo**
(`~/privyhub_link_watch/<probe>/`, not under git; the path named in the
record, no identifiers in it); only its `summary.json`, `encoder.jsonl`
and `title.txt` are copied into `e4_s4c_<date>/probes/<n>/`. The control
and flagged runs are kept in full under `e4_s4c_<date>/runs/`. Nothing is
deleted.

**Flags.** `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1` only during the flagged
runs (via `e3_flag.conf`, removed at each teardown); every probe runs on
the four-line adopted state with `flags_absent` read back; no
`e4_constraint.conf` except during the 150 % run.

**The cap:** `2026-10-15T04:00:00Z`. No probe starts after it; a run in
flight finishes; then the close.

## 2. The record

`evidence/E4_S4C_LINK_WATCH_AND_DEFERRAL_<date>.md` + `e4_s4c_<date>/`:

- **the link history**: `link_watch.jsonl`, `ping.jsonl`, and the tables —
  every probe in time order (local time, loss, rendered, resyncs, RSSI,
  air utilisation, ping loss / RTT); **loss by hour-of-day** (median,
  min, max, count, clean count) and **by day**; the clean windows (start,
  length, what ran in them); ping loss by hour; and in words what moves
  with the loss (air utilisation? RSSI? time of day? the probe's own
  pauses?) — correlation stated as seen, not as cause;
- the deferral: the pre-registration + `.sha256`, the control(s), the
  flagged runs (full), `manifest.sha256`, `--check`, `validity.json`, the
  table, **the verdict**, the alpha spec with the deferral (E4-S4B §2)
  and the one-line adoption (`epg-defer.conf`) and its revert, written,
  not applied;
- `redact_check.txt`; `patches/` if a tool changed (a `--window 300`
  probe mode, the watch driver `e4_s4c_watch.py` in the task's
  directory); `logs/e4_s4c_git_status.txt`;
- `docs/KNOWN_ISSUES.md` LINK rewritten from the history; then the
  queue's close (ROADMAP, `CURRENT_HANDOFF.md`, the redactor, `CURRENT.md`
  last). Final state: the four adopted lines, no flag, no constraint, no
  game, PS1 files identical, APK CONFIRMED.
