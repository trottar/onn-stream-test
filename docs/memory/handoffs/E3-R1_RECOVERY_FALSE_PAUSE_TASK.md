---
memory_schema: 1
as_of: 2026-10-08
status: TASK HANDOFF — E3-R1, queue item 1 (the user's go, 2026-10-08): link-drop recovery pauses a running game with the link up. Reconstruct what the trigger saw at every recorded false pause and at R3's real drops; one change to the trigger rule behind a flag; prove it offline on the recorded timelines (fires on every real drop, on no false one), then on the suite (PS1-STREAM ×2, CONC ×2). The real-drop check on the air is the user's nft night afterwards. Nothing adopted; nothing committed
---

# E3-R1 — recovery's false pause

**Measured problem (E3-A2 §3, `prior_runs_validity.txt`).** With the
link up and nobody touching anything, the companion's link-drop
recovery left PLAYING inside a 20-min window five times across four
nights: E2's PS1-1080P run 1 (10-05, `controller_silence`); E3-S1's
control (10-06, `client_output_silence`) and both its CONC runs
(`client_output_silence` then `controller_silence`, with an
`encoder_restart` between); E3-A2's PS1-STREAM run 1 (10-07,
`controller_silence`, then `gave_up_saved` two minutes later and
`PAUSED_SAVED` for the rest of the window). The recovery logs for
10-05 and 10-06 carry more of the same event type outside the suite.
D-BASE-R3 (09-20) noted the `controller_silence` path was **never
exercised** in testing; it is now firing in ordinary sessions.

**Why it matters to the user.** A game that pauses itself, saves and
waits during play is worse than any loss figure in this phase; and a
pause mid-window silently invalidates measurements (E3-A2's rule).

**Hypothesis space (the probe decides which is the narrow one).** Each
trigger compares an age (the newest controller packet; the client's
newest output heartbeat) with a threshold. The false pauses come from
one of: (a) the threshold is shorter than the link's ordinary loss
bursts, so one burst looks like a dead client; (b) the client stops
sending the signal while idle (no input → no controller packets;
or a heartbeat that pauses), so the age grows with the link fine; (c) a
single check reads a stale value (the R3 note's "newest value, not
still rising" defect, on the restart path, has a sibling here).

Read first: `evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md` (the
trigger table, the F-rows, the "not made here" corrections),
`D_BASE_R3C_…`, `D_BASE_R3C2_…` and the decision
`decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`; the recovery
code (the controller receive loop's silence check, the heartbeat age
check, the thresholds, the give-up timer); `tools/test_c3_f1_recovery_restart.py`;
`e3_a2_2026-10-07/e3_a2_validity.py`; `TOOLS.md` "Link-drop recovery".

## 1. Probe: what the trigger saw (measurement, before the change)

For **every** false pause above and for **every real drop** in
`d_base_r3_2026-09-20/` (the nft-injected outages, with their known
start times) and the R3b/R3d hand runs: from the recovery log, the
controller receive log, the heartbeat/telemetry archive and the
per-second sampler where one ran, reconstruct a per-second timeline
of **±60 s around the event**: controller-packet age, client-output
age, lost packets/s, the heartbeat's own gap, the ladder's decisions,
and which check fired with what age against what threshold.

Then, with a PS1 stream PLAYING and nobody at the controller, 10 min
of the same two ages sampled at 1 s (a measurement hook if the
companion does not already expose them; off afterwards): their
distributions idle, and whether the client's controller packets keep
coming with no input (a yes/no with the packet interval).

`e3_r1_<date>/probe.md`, with the timelines as tables. **Reading
rule, written here:** the probe names (a), (b) or (c) by which fact
holds — (b) if the controller age grows without loss during idle; (a)
if every false pause sits on a loss burst whose length exceeds the
threshold while real drops exceed it by a margin; (c) if the fired
age was stale against the neighbouring seconds.

## 2. The one change (chosen by the probe; pre-registered either way)

Behind **`PRIVYHUB_RECOVERY_TRIGGER=v2`** (absent = today's rule, byte
for byte); the give-up timer, the restart path, the save-and-prompt
flow (R3c2) unchanged:

- (b) → the controller-silence trigger requires **both** signals
  (controller age *and* client-output age over threshold), since a
  live client keeps producing output even with no input; or the
  client's keepalive is counted as a controller packet if one exists
  and is simply not counted today — whichever the code shows, one of
  them;
- (a) → the threshold becomes the measured real-drop floor minus
  margin, above the false pauses' burst lengths (state the numbers);
  the age must exceed it on **two consecutive** checks;
- (c) → the two-consecutive-non-decreasing-age rule R3 proposed for
  the restart path, applied to the trigger.

## 3. Offline replay (the first half of the bar, before any run)

`e3_r1_replay.py`: today's rule and `v2` run over every reconstructed
timeline (§1). **Pre-registered, hashed before the replay is run:**

- `v2` fires on **every** real drop (R3's injected outages and the
  hand runs), each within **+2 s** of today's rule's firing time;
- `v2` fires on **none** of the five false pauses;
- today's rule, replayed, reproduces every recorded event (the replay
  is faithful) — otherwise the task stops here, INCONCLUSIVE, with the
  replay's disagreement recorded.

## 4. The runs (the second half of the bar)

- E1-PS1-STREAM ×2 and E1-CONC ×2 with the flag (E2's windows and
  gaps; drop-in for those runs only; environ checked against the
  adopted three lines + the flag).
- **Bar, ACCEPTED only if all hold:** (i) the replay bar (§3) held;
  (ii) **no recovery event leaves PLAYING in any of the four windows**
  (the validity rule itself, now a clause — with the flag a run that
  pauses is a failure, not an invalid attempt); (iii) each row within
  E1's bands of its E2 numbers for the things the trigger does not
  touch (host CPU ± 2; rendered ± 0.5 of E2's PS1-STREAM / of E3-S6's
  CONC) — loss, underruns, resyncs reported; (iv) the companion's
  stream cost unchanged (± 2 points of a core).
- **What this cannot show:** that a **real** link drop still triggers
  recovery on the air. That is the user's nft night with the flag on
  (`tools/c3_l4_nft_night.py`, which E3-A2 extended for the adopted
  environ; the task writes the exact drop-in line and the one-paste
  hand step with what the reply must contain). **Adoption waits for
  it.** The record says so.

## 5. The record

`evidence/E3_R1_RECOVERY_FALSE_PAUSE_<date>.md` + `e3_r1_<date>/`
(the timelines, the probe, the pre-registration + `.sha256`, the diff,
`e3_r1_replay.py` and its output, 4 runs, `manifest.sha256`, `--check`,
`validity.json`, table, verdict, `redact_check.txt`); `patches/`;
`docs/KNOWN_ISSUES.md` gains the false pause (open until the nft
night); `investigations/ACTIVE.md`; `logs/e3_r1_git_status.txt`. Flag
absent; the adopted state restored; then queue item 2.
