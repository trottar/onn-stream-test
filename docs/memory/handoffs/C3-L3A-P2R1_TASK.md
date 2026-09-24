---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — C3.L3a Part 2, revision 1: fix the gameplay-acceptance probe's recorded defects (plus two found on re-reading it), re-score the retained 2026-09-20 session without replaying, state the pre-registered rerun decision; tools + documentation only, no companion / client / profile change, no session run; authorized by the user 2026-09-23
---

# C3-L3A-P2R1 — fix the probe, re-score the retained session

**Why.** Phase C resumed at `C3.L3a` Part 2 (`CURRENT.md`, `handoffs/CURRENT_HANDOFF.md`).
The probe `tools/probe_c3_l3a_gameplay_acceptance.py` ran once, 2026-09-20
01:00-01:10 local, and its report's headline numbers were probe defects, not
findings (`2026-09-20.md`, "C3.L3a Part 2 ran, and the probe has three
defects"; `investigations/BASELINE_STREAM_HEALTH.md`, "Suspended, not
failed"). The raw marks and per-cycle timings are retained in
`logs/streaming/c3_l3a_gameplay_acceptance_state.json` (run `20260920_010023`,
seed 857553307, 8 traversals, 16 transitions, 15 marks, not aborted). Fix the
probe, re-score that file, and write down what the re-score can and cannot say.

Read first: `patches/C3-L3A-P2_GAMEPLAY_ACCEPTANCE_PROBE.md` (what the probe
is and the line it must not cross — it is not a controller),
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` §"The `C3.L4` gate, stated
so it can be satisfied" (the four requirements; the gate observation is
checked **after the fact against `stream_discontinuities` `elapsed_ms`**),
`investigations/ACTIVE.md` §C3.L3a, `companion/diagnostics/stream_telemetry.py`
(the real shape of `/diagnostics/stream-telemetry`), `tools/manual_checkout.py`,
`evidence/D_BASE_CLOSEOUT_2026-09-23.md` (the table every Phase C change is
measured against).

**Scope.** Change only `tools/probe_c3_l3a_gameplay_acceptance.py` and
`tools/manual_checkout.py`. **No companion, client, profile or route change;
nothing in the environment; do not start a stream or a session; do not
restart the companion.** The retained state file is read-only — never
overwrite it; every output of the re-score goes to new files.

## The defects, and the fixes

**1. Mark-association window anchors on sequence start.** `_attribute` uses
`[sequence.at_s, at_s + 2.5]`; a ramp's rungs fire at +0, +5, +10 s, so the
window closes before the second rung. Fix: a sequence's window runs from its
**first fire** (`at_s`) to its **end + W** (`end_s`, the moment the last
transition call returned — the visible restart happens between fire and
return), and each mark also records its lag from the nearest preceding fire.
Decoys must stay comparable, so score each decoy through **two** windows,
reported separately: jump-matched `[decoy, decoy + W]` and ramp-matched
`[decoy, decoy + ramp_span + W]` where `ramp_span` is that run's median
`end_s − at_s` of its ramps (this run: 11.6 s).
Report per class: events, marked, marks, **exposure seconds**, and marks per
exposed second; beside them the session's chance rate = total marks /
phase-A seconds (the 2026-09-20 session: 15 / 415.2 s = 0.036 per s, so a
2.5 s window catches a random mark ~9 % of the time and a 14 s ramp window
~40 %). Keep W a parameter; the re-score reports W = 2.5 (the value
pre-registered before the run — primary for this file), 5.0 and 8.0 side by
side, and the lag histogram of every mark from the nearest preceding fire and
from the nearest preceding decoy. Do not pick the window that makes the table
look best.

**2. Telemetry field paths are wrong.** `sample_settling` reads
`measurements.receiver_recent_fps`, `receiver.waiting_for_idr`, `checks.fresh`
— those came from the C2 probe's output artifact. The endpoint
(`stream_telemetry.py`) serves top-level `fresh`, `age_ms`, `available`,
`session_elapsed_ms`, `sample_interval_ms`; `receiver.recent_fps`,
`receiver.recent_mbps`, `receiver.waiting_for_idr`; `latency.output_gap_ms`;
`decoder.queue_depth`. Every 2026-09-20 sample was `None`, so "8/8 never
settled" measured nothing. Fix the paths, and fix the test with them:
"settled" must be two **distinct** snapshots (`session_elapsed_ms` advanced —
polling at 0.5 s re-reads the same client report otherwise), both `fresh`,
`waiting_for_idr` not true, `recent_fps ≥ 54`. Record `sample_interval_ms`
and the snapshot cadence in the settling record; the budget (12 s) must be
at least three client intervals — check, don't assume. Verify the paths
against the endpoint with the stream idle (`curl -s
http://127.0.0.1:8765/diagnostics/stream-telemetry` → `available: false`, the
key set present); settling itself cannot be measured without a session — say
so in the record, do not fake it.

**3. Unanchored 1-5 rating.** `ask_int(low=1, high=5)` with no anchors; the
user answered out of 10. Fix: 1-10 with the anchors printed in the prompt
(10 = looks the same as 7000; 5 = clearly softer, still playable; 1 =
unplayable), and store `rating_scale: {low, high, anchors}` in the state and
in every report line that prints a rating. The retained answers are recorded
**as the user stated them on 2026-09-20**: 6000 → 5/10, 5500 → 3/10, 5000 →
2/10, all three "acceptable: no"; the re-score's park table says
`scale: 1-10 (prompt showed 1-5; user's stated scale)`. Do not rescale.

**4. Found on re-reading — the decoder cross-check counts the wrong thing.**
`expected_ssrc_changes = len(transitions)` ignores Phase B's three parks and
the restore, so the warning would misfire on every complete run (this run:
16 + 3 + 1 = **20** SSRC changes, and the client saw 20). Count them all.
And `--finalize` takes the **newest** decoder session, which is wrong for any
re-score: add `--state <path>` and `--decoder <path>` arguments; without
`--decoder`, choose the **earliest** decoder session not in
`decoder_sessions_before` whose `received_at_utc` is after the run's
`generated` time and whose `ssrc_changes` ≥ the expected count. For this run
that is `logs/games/decoder_sessions/native_decoder_20260920_051218_321.json`
(received 05:12:18Z; duration 744,858 ms; 20 SSRC changes; 24
discontinuities; 2,518 lost packets; max output gap 558 ms — pre-cap build).

**5. Found on re-reading — requirement 4 of the gate was never performed.**
The analysis only counted discontinuities; it never put the marks and the
decoder's clock on one axis. Fix: align the probe clock to the decoder's
`elapsed_ms` by matching the Phase-A fires, in order, to the first N
`ssrc_change` entries (N = Phase-A transitions); report the median offset and
the spread (this run: offset ≈ 35.02 s, spread 0.46 s across 16 pairs —
anything over 1 s means the pairing is wrong, stop and say so). Then, for
every mark, report the nearest preceding decoder event within W: the
discontinuity (type, lag) and the largest `output_gap_ms` among retained slow
events in `[fire, fire + 1 s]` for each transition. State the slow-event
retention coverage honestly: this session retained 128 of 128 (64 "marked" +
64 "recent"), covering decoder 355.7 s onward = probe 320.7 s onward, so the
first ~320 s of Phase A have discontinuities only (the `C3.L2b` retention
defect, `docs/KNOWN_ISSUES.md`, still open).

## The re-score — run it, print it, do not interpret past the noise

Run the fixed `--finalize --state logs/streaming/c3_l3a_gameplay_acceptance_state.json --decoder <the file above>`;
outputs to `logs/streaming/c3_l3a_runs/20260920_010023.json` and a text
report. Put the old scoring beside the corrected one.

Cowork's own re-score from the retained file, to be **confirmed or corrected**
(it is a check on your arithmetic, not a target):

| scoring | jump | ramp | decoy, jump-matched | decoy, ramp-matched | not in any sequence window |
| --- | ---: | ---: | ---: | ---: | ---: |
| as installed (anchor = sequence start, W 2.5) | 0/4 | 0/4 | 1/8 | — | 14 of 15 |
| corrected, W 2.5 (`at_s` … `end_s` + W) | 2/4, 2 marks, 15.1 s exposure | 3/4, 4 marks, 56.1 s | 1/8, 1 mark, 20.0 s | 5/8, 5 marks, 112.8 s | 9 |
| corrected, W 5.0 | 2/4, 2, 25.1 s | 3/4, 4, 66.1 s | 5/8, 5, 40.0 s | 6/8, 7, 132.8 s | 9 |
| corrected, W 8.0 | 2/4, 2, 37.1 s | 3/4, 4, 78.1 s | 5/8, 5, 64.0 s | 6/8, 9, 156.8 s | 9 |

Lags of marks from the nearest preceding fire, corrected clock: 2.7, 2.8,
2.9, 3.0, 3.0, 3.4, 4.3 s cluster just past the 2.5 s window; four of the
marks in no sequence window sit 2.7-4.9 s after a **decoy**, one 0.98 s
after a decoy. At W 5.0 the decoys are marked as often as the sequences. Per-transition
output gap where slow-event coverage exists (the last 4 Phase-A transitions
and all 4 Phase-B): 68-227 and 164-241 ms — on the 2026-09-20 build, with
first IDR accepted in 17-30 ms; the gap is the codec hold that `C3.L2c`
later addressed, and it is **not** measured on the adopted build.

**Pre-registered reading, written against the noise, not the table.** With 4
events per shape, 15 marks at a chance rate of 0.036 per second, and the
window itself shorter than the observed reaction lag, this session cannot
separate any shape from the decoys at any window — at W 2.5 the window is
shorter than the measured reaction lag, and at W 5.0 the decoys are marked
as often as the sequences. The table shows that, and nothing more. The re-score **corrects the record; it does not answer the
gate**, in either direction. Lifecycle stands as a real result: 0 FEC / 0
audio / 0 controller deltas over 16 transitions, and 20 clean SSRC changes
(`jump_packets 0`, first IDR 17-34 ms).

**Rerun decision, pre-registered here so the record carries it:** RERUN
REQUIRED, on two independent grounds, either sufficient: (a) the session
predates the adopted build — before the 90 KB cap (`P6a`), the 12/17 cushion,
the 2/4 redundancy, the headless host, and on a baseline then failing every
row (spikes ~2,500/min), so both the marks and the picture ratings were taken
on a stream that was already unhealthy; (b) n = 4 per shape against the
design's own bar of ~20 pooled. Record the rerun's pre-registration in the
record and in `ACTIVE.md`, and leave the probe ready: `--traversals 10`,
`--dwell-min 55 --dwell-max 90` (the dwell must hold settling + the
ramp-matched decoy window + the next sequence's window without overlap —
place each decoy so `decoy + ramp_span + W` ends ≥ 3 s before the next
sequence fires; enforce it in `build_schedule`), primary **W = 5.0 s** chosen
from the measured 2.7-4.3 s lags (2.5 and 8.0 reported beside it), decoys
scored through both matched windows, ≥ 4 sessions pooled to ≥ 20 per shape,
shape order randomized per run, Phase B at 6000/5500/5000 on the anchored
1-10 scale. **Do not run it.** The rerun is the user's play session and
Cowork hands them the steps after this task is verified. For each rerun
session the record will also carry the decoder session's close-out rows
(spikes/min, rendered fps, stale drops/min, video loss/min post-FEC, max
output gap) beside `D_BASE_CLOSEOUT_2026-09-23.md` — context for a session
with 20+ deliberate restarts, not a gate.

## Validation

`py_compile` both tools; `--plan` for 8 and 10 traversals showing the decoy
placement constraint holds on every dwell; the re-score reproduces the
retained run's 16 transitions, 8 decoys, 15 marks, 20 expected SSRC changes;
the clock alignment residual; `--aggregate` over the one run file still
works; the report's `Classification:` header convention unchanged
(`manual_checkout.Report` is load-bearing for other probes — do not change
its header). No self-test that fakes a companion. Never retry a failing
action more than twice.

## Record and memory

`evidence/C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md` — the five
defects and fixes, the old-vs-corrected table, the W sensitivity, the lag
histograms, the clock alignment, the per-transition gaps with the coverage
caveat, the park table on the stated scale, the pre-registered reading, the
rerun decision with its pre-registration; evidence under
`evidence/c3_l3a_p2r1_2026-09-23/`: a byte copy of the retained state file,
a copy of the decoder session, the re-score json + text, the `--plan` output,
`sha256sum` manifest of every file. `patches/C3-L3A-P2R1_*.md` with the
per-file SHA-256s before and after; regenerate `patches/PATCH_INDEX.md`.
Update `investigations/BASELINE_STREAM_HEALTH.md` "Suspended, not failed"
(probe fixed; rerun pre-registered), `investigations/ACTIVE.md` §C3.L3a (the
"[event, event + 2.5 s]" design line and "8/8 never settled" are superseded),
`CURRENT.md` (Current Work Item → the rerun, awaiting the user; fixed
headings; `python3 tools/check_memory_health.py` healthy), `TOOLS.md` (the new
arguments), `2026-09-23.md`, `handoffs/CURRENT_HANDOFF.md` one line.
`C3.L4` stays BLOCKED on the gate; say so. No addresses or device identifiers
in any file. Nothing committed.
