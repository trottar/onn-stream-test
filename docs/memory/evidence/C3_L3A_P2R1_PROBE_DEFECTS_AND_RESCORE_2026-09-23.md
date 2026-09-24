---
memory_schema: 1
as_of: 2026-09-23
status: C3.L3a PART 2 R1 — probe defects FIXED (five), retained 2026-09-20 session RE-SCORED without replaying; the re-score corrects the record and does NOT answer the C3.L4 gate in either direction; RERUN REQUIRED (pre-registered below), not run; C3.L4 stays BLOCKED
---

# C3-L3A-P2R1 — the probe's defects, fixed; the 2026-09-20 session, re-scored

Task: `handoffs/C3-L3A-P2R1_TASK.md` (authorized by the user 2026-09-23).
Patch: `patches/C3-L3A-P2R1_PROBE_DEFECTS_AND_RESCORE.md`. Evidence:
`c3_l3a_p2r1_2026-09-23/`, SHA-256 of every file in
`c3_l3a_p2r1_2026-09-23/sha256_manifest.txt`.

**Tools and documentation only.** Changed: `tools/probe_c3_l3a_gameplay_acceptance.py`,
`tools/manual_checkout.py`. No companion, client, profile, route or
environment change; no stream or session started; the companion not
restarted. The retained state file was read, never written: SHA-256
`ed4c241a…0463` before and after every `--finalize`.

## The run re-scored

`logs/streaming/c3_l3a_gameplay_acceptance_state.json` — run
`20260920_010023`, 2026-09-20 01:00-01:10 local, seed 857553307, 8
traversals (4 jump, 4 ramp), 16 transitions, 8 decoys, 15 marks, phase A
415.247 s, not aborted. Decoder session
`native_decoder_20260920_051218_321.json` (received 05:12:18Z, 744,858 ms,
20 SSRC changes, 24 discontinuities, 2,518 lost packets, max output gap
558 ms, client profiler 0.12.2 — the pre-cap build). Both copied byte for
byte into the evidence directory.

**The 2026-09-20 finalize never read a decoder session at all.** It ran at
01:11:48 local, 30 s before the client posted at 01:12:18, and printed "No
new decoder session found" (`as_installed_2026-09-20/c3_l3a_gameplay_acceptance.txt`).
The SSRC cross-check and the gate's requirement 4 were not performed by the
probe; the "client saw 20" figure came from reading the file by hand.

## The five defects and their fixes

**1. The mark window anchored on sequence start.** `[at_s, at_s + 2.5]`
closed before a ramp's second rung (+5 s) fired. **Fix:** a sequence's
window is `[first fire, end_s + W]`, `end_s` being when the last transition
call returned. Decoys are scored through two windows, reported separately:
jump-matched `[d, d + W]` and ramp-matched `[d, d + ramp_span + W]`,
`ramp_span` = the run's median ramp `end_s − at_s` (this run **11.573 s**).
Each class reports events, marked, marks, **exposure seconds** (union of its
windows), marks per exposed second and the chance-expected marks (chance
rate × exposure), beside the chance rate = marks / phase-A seconds. W is a
parameter; every finalize reports 2.5, 5.0 and 8.0 side by side. Classes are
scored independently, so a mark inside two classes' windows counts in both
(the as-installed code gave each mark to one anchor). Each mark also gets its
lag from the nearest preceding fire and from the nearest preceding decoy.

**2. The telemetry field paths were wrong.** `measurements.receiver_recent_fps`
and `checks.fresh` do not exist on the endpoint. **Fix:** the paths
`stream_telemetry.py` serves — top-level `fresh`, `age_ms`, `available`,
`session_elapsed_ms`, `sample_interval_ms`; `receiver.recent_fps`,
`receiver.recent_mbps`, `receiver.waiting_for_idr`;
`latency.output_gap_ms`; `decoder.queue_depth`. Settled = **two distinct
snapshots** (`session_elapsed_ms` advanced; the first snapshot read never
counts, since it may predate the transition), both `fresh`,
`waiting_for_idr` not true, `recent_fps` ≥ 54. The settling record carries
`sample_interval_ms`, the measured snapshot cadence, distinct-snapshot
count and `budget_ok` (budget ≥ 3 client intervals). Preflight now refuses
to start if telemetry is not fresh or the 12 s budget is under three
intervals, so a run cannot repeat this defect silently.

*Verified against the endpoint, stream idle* (`native-stream-status`
`active: false`; `telemetry_paths_idle_check.txt`): all ten paths present,
both old paths absent, `sample_interval_ms` **2000** → the 12 s budget is
**6.0 intervals** (≥ 3: holds). The idle endpoint answered **`available:
true, fresh: false`**, `age_ms` ~2.5-3.1 million, not the `available: false`
the task expected: the store keeps the last client report (here the
close-out's session W, `session_elapsed_ms` 1,207,110) until the companion
restarts. The real `sample_settling()` run against it for its 12 s budget
returned `settled_s: null`, 0 distinct snapshots, 24 samples, `budget_ok:
true` — correct for no session. **Settling itself cannot be measured without
a session and was not measured**; nothing here fakes it.

**3. The picture rating was unanchored.** **Fix:** `ask_int` takes
`anchors`, printed above the prompt; the probe asks 1-10 with 10 = looks the
same as 7000, 5 = clearly softer, still playable, 1 = unplayable, and stores
`rating_scale: {low, high, anchors}` in the state. Every report line that
prints a rating prints its scale. The retained answers carry the user's
stated scale through a keyed legacy entry (`LEGACY_RATING_SCALES`), not a
rescale.

**4. The decoder cross-check counted the wrong thing, and picked the wrong
file.** `expected_ssrc_changes = len(transitions)` ignored the parks and
restores. **Fix:** `expected_transitions()` lists every transition in
order — Phase A, the Phase-A restore if the stream was off-reference, the
parks, the Phase-B restore — from the state (v2 state now records every
restore with `transitioned` and `at_s`, and each park's `fired_at_s`; for v1
the Phase-A restore is derived from where Phase A left the stream). This run:
**16 + 0 + 3 + 1 = 20**, the client saw **20** — no warning. **`--state`
and `--decoder`** added; without `--decoder`, the earliest decoder session
not in `decoder_sessions_before`, received after the run's `generated` time,
with `ssrc_changes` ≥ the expected count. Auto-selection on this run chose
`native_decoder_20260920_051218_321.json` (the only candidate), the same
file `--decoder` names.

**5. Requirement 4 was never performed.** **Fix:** Phase-A fires matched in
order to the first N `ssrc_change` entries give the probe-to-decoder offset;
spread > 1 s stops the decoder-axis analysis and says so. Then each mark's
nearest preceding discontinuity (type, `jump_packets`, lag, within each W),
and per transition the SSRC time, residual, first-IDR time and the largest
`output_gap_ms` among retained slow events in `[fire, fire + 1 s]` with
coverage stated as full, partial or none.

Also changed, because the rerun needs it: the schedule places each decoy at
a fixed offset (below), `--window` defaults to 5.0, `--traversals` to 10,
dwell to 55-90 s; `--finalize` writes a per-run text report beside the per-run
JSON; the report adds the decoder session's close-out rows; `--aggregate`
pools the new per-window scoring and skips pre-v2 run files by name.

## Old scoring beside the corrected one

From `rescore_20260920_010023.txt`. Cells: marked/events, marks, exposure.

| scoring | jump | ramp | decoy, jump-matched | decoy, ramp-matched | marks in no sequence window |
| --- | ---: | ---: | ---: | ---: | ---: |
| as installed (anchor = sequence start, W 2.5) | 0/4 | 0/4 | 1/8 | — | 14 of 15 |
| **corrected, W 2.5** (primary for this file) | 2/4, 2, 15.1 s | 3/4, 4, 56.1 s | 1/8, 1, 20.0 s | 5/8, 5, **112.6 s** | 9 |
| corrected, W 5.0 | 2/4, 2, 25.1 s | 3/4, 4, 66.1 s | 5/8, 5, 40.0 s | 6/8, 7, **132.6 s** | 9 |
| corrected, W 8.0 | 2/4, 2, 37.1 s | 3/4, 4, 78.1 s | 5/8, 5, 64.0 s | 6/8, 9, **156.6 s** | 9 |

Chance rate 15 / 415.247 s = **0.0361 per s**: a 2.5 s window catches a
random mark 8.6 % of the time, a 14.0 s ramp window 39.7 %. Chance-expected
marks per class (rate × exposure):

| W | jump | ramp | decoy, jump-matched | decoy, ramp-matched |
| --- | ---: | ---: | ---: | ---: |
| 2.5 | 2 vs 0.54 | 4 vs 2.03 | 1 vs 0.72 | 5 vs 4.07 |
| 5.0 | 2 vs 0.91 | 4 vs 2.39 | 5 vs 1.44 | 7 vs 4.79 |
| 8.0 | 2 vs 1.34 | 4 vs 2.82 | 5 vs 2.31 | 9 vs 5.66 |

**Cowork's re-score: confirmed, with one correction.** Every marked/events
count, mark count and the jump, ramp and jump-matched exposures reproduce
exactly. The ramp-matched decoy exposures are **112.6 / 132.6 / 156.6 s, not
112.8 / 132.8 / 156.8** — Cowork rounded `ramp_span` to 11.6 s before
multiplying by 8; the probe uses 11.573 s. No count changes.

## Mark lags

Probe clock, every mark (`x` = inside that class's window at W 2.5):

| mark s | sev | from fire | from decoy | jump | ramp | decoy-j | decoy-r |
| ---: | ---: | ---: | ---: | :-: | :-: | :-: | :-: |
| 57.033 | – | 57.03 | 16.13 | | | | |
| 83.482 | – | **3.03** | 42.58 | | x | | |
| 105.715 | – | 25.27 | **4.66** | | | | x |
| 163.003 | 3 | 30.93 | **3.28** | | | | x |
| 175.596 | 6 | **4.26** | 15.87 | | x | | |
| 184.668 | 4 | **2.98** | 24.95 | | x | | |
| 203.588 | 6 | 21.90 | **2.72** | | | | x |
| 219.606 | 3 | **2.96** | 18.74 | x | | | |
| 279.701 | 2 | **3.42** | 25.99 | | x | | |
| 292.558 | 3 | 11.11 | 38.84 | | | | |
| 302.295 | 2 | 20.84 | 48.58 | | | | |
| 307.822 | 4 | 26.37 | **0.98** | | | x | x |
| 356.839 | 2 | 26.34 | **4.93** | | | | x |
| 370.983 | 6 | **2.91** | 19.08 | x | | | |
| 411.736 | 2 | 43.66 | 23.77 | | | | |

Histogram (s): from the nearest preceding fire — 2-3: 3, 3-4: 2, 4-5: 1,
8-15: 1, 15-30: 5, 30-60: 3; from the nearest preceding decoy — 0-1: 1,
2-3: 1, 3-4: 1, 4-5: 2, 15-30: 7, 30-60: 3. No mark fell 0-2 s after a fire.

**Correction to the task's lag list.** It gave seven lags ("2.7, 2.8, 2.9,
3.0, 3.0, 3.4, 4.3 s"); there are **six** marks within 5 s of a fire:
2.91, 2.96, 2.98, 3.03, 3.42, 4.26 s on the probe clock, and on the decoder
axis (from the SSRC change itself) 2.71, 2.77, 2.97, 3.04, 3.43, 4.26 s. The
list appears to mix the two clocks. The conclusion it supported stands: all
six sit past 2.5 s. The decoy lags are exactly as stated: four of the nine
marks outside every sequence window sit 2.72-4.93 s after a decoy, one 0.98 s
after.

## Decoy placement in the retained run

The ramp-matched window vs the next sequence's first fire (slack, s):

| decoy | at s | next fire | W 2.5 | W 5.0 | W 8.0 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 40.907 | 70.295 | 15.31 | 12.81 | 9.81 |
| 1 | 101.057 | 132.070 | 16.94 | 14.44 | 11.44 |
| 2 | 159.723 | 171.337 | **−2.46** | **−4.96** | **−7.96** |
| 3 | 200.866 | 216.644 | 1.71 | **−0.80** | **−3.79** |
| 4 | 253.715 | 270.956 | 3.17 | 0.67 | **−2.33** |
| 5 | 306.846 | 320.094 | **−0.82** | **−3.33** | **−6.33** |
| 6 | 351.905 | 368.076 | 2.10 | **−0.40** | **−3.40** |
| 7 | 387.965 | — | — | — | — |

Negative = the decoy's ramp-matched window overlaps the next sequence's. At
W 5.0 and 8.0, marks 175.596 (W 5.0, 8.0), 219.606 and 370.983 (W 8.0)
count in both a sequence class and the ramp-matched decoy class. The
2026-09-20 schedule could not have prevented this: it drew decoys as a
fraction of the post-settling remainder. **Fixed for new runs**
(`build_schedule`): the decoy offset is fixed up front at ≥ settling budget +
one poll timeout (14 s) after the sequence end, and its ramp-matched window
at the **widest reported W (8.0)** with the planned ramp span (11.9 s) must
end ≥ 3 s before the next fire; a dwell too short for that is refused, not
squeezed (minimum 36.9 s). The runtime records each decoy's `planned_at_s`
and `late_s`, and the report prints every decoy's actual slack at each W.
`--plan` for 8 and 10 traversals (`plan_output.txt`): the rule holds on
every dwell (min slack 10.5 / 8.1 s); a sweep of seeds 1-2000 for both
counts: min slack 5.82 s; the 2026-09-20 dwell (30-75 s) is refused.

## Clock alignment

Phase-A fires matched in order to the first 16 `ssrc_change` entries:
median offset **35.017 s**, spread **0.457 s**, max |residual| 0.255 s —
under 1 s, pairing accepted. (The task's ≈ 35.02 / 0.46: confirmed.)

## Per transition, on the decoder axis

| transition | to | fire s | SSRC ms | resid s | 1st IDR ms | max output gap in 1 s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| jump 0 | 5000 | 0.000 | 34,907 | −0.110 | 20 | not covered |
| ramp 1 (3 rungs) | 5500/6000/7000 | 70.295 / 75.279 / 80.450 | 105,110 / 110,329 / 115,462 | −0.202 / +0.033 / −0.005 | 26 / 22 / 30 | not covered |
| jump 2 | 5000 | 132.070 | 167,136 | +0.049 | 23 | not covered |
| ramp 3 | 5500/6000/7000 | 171.337 / 176.511 / 181.686 | 206,349 / 211,519 / 216,714 | −0.005 / −0.008 / +0.011 | 21 / 25 / 29 | not covered |
| jump 4 | 5000 | 216.644 | 251,916 | +0.255 | 17 | not covered |
| ramp 5 | 5500/6000/7000 | 270.956 / 276.279 / 281.451 | 306,112 / 311,285 / 316,456 | +0.139 / −0.010 / −0.012 | 26 / 30 / 30 | not covered |
| ramp 6 | 6000/5500/5000 | 320.094 / 325.319 / 330.502 | 355,152 / 360,330 / 365,523 | +0.041 / −0.006 / +0.005 | 25 / 23 / 24 | **68 partial** / 182 / 212 |
| jump 7 | 7000 | 368.076 | 403,230 | +0.137 | 28 | 227 |
| park 6000 | 6000 | ~415.5 | 450,495 | — | 28 | 241 |
| park 5500 | 5500 | ~461.6 | 496,654 | — | 25 | 164 |
| park 5000 | 5000 | ~507.8 | 542,835 | — | 22 | 181 |
| restore after B | 7000 | ~554.0 | 589,020 | — | 34 | 223 |

`jump_packets` 0 on all 20. **Coverage, stated honestly:** the session
retained 128 of 128 slow events (64 marked + 64 recent), the earliest at
decoder 355.703 s = probe 320.686 s. Both segments are saturated FIFOs, so
**the first ~320 s of Phase A — 12 of its 16 transitions — have
discontinuities only.** Correction to the task's "last 4 Phase-A
transitions": ramp 6's first rung fired at decoder ~355.11 s, 0.59 s before
coverage begins, so its 68 ms is from the covered 0.41 s of its window only;
the fully covered Phase-A windows are the last three (182-227 ms). Phase B's
four: 164-241 ms (confirmed). Phase B has no probe fire time in a v1 state;
its windows start at the SSRC change (≈ fire + offset). All on the
2026-09-20 build, first IDR accepted in 17-30 ms (Phase A) and 17-34 ms (all
20); the gap is the codec hold that `C3.L2c` later addressed, and it is **not
measured on the adopted build.** (The task cites the retention defect as
open in `docs/KNOWN_ISSUES.md`; that file records the `C3.L2b` segmentation,
not saturation of the marked segment itself as an open item — this session
shows it: 64 of 64 marked, earlier cycle windows evicted.)

Other discontinuities in the session: three `sequence_resync`s at decoder
25.2-29.1 s (probe −9.8 to −5.9 s, before Phase A; IDR 235-404 ms) and one at
474.2 s (probe ~439.2, during the 6000 park; 199 packets, IDR 242 ms).

## The marks on the decoder axis (requirement 4)

Each mark at probe time + 35.017 s; nearest preceding discontinuity: **all
fifteen are `ssrc_change`s** (no loss resync fell in Phase A). Within W:

| W | marks with a discontinuity within W before them |
| --- | --- |
| 2.5 | **0** |
| 5.0 | 6 — lags 2.71, 2.77, 2.97, 3.04, 3.43, 4.26 s |
| 8.0 | the same 6 |

The other nine sit 11.1-57.1 s after their nearest discontinuity.

## Picture quality — on the user's stated scale

| kbps | acceptable | rating | scale |
| ---: | --- | ---: | --- |
| 6000 | no | 5 | 1-10 (prompt showed 1-5; user's stated scale) |
| 5500 | no | 3 | 1-10 (prompt showed 1-5; user's stated scale) |
| 5000 | no | 2 | 1-10 (prompt showed 1-5; user's stated scale) |

Recorded as the user stated them on 2026-09-20. Not rescaled.

## Lifecycle — a real result

Over 16 Phase-A transitions: **0** FEC send-error, **0** audio send-error,
**0** controller bad-packet deltas; 20 clean SSRC changes (`jump_packets` 0,
first IDR 17-34 ms). Settling: **0 of 8 sequences measured** — every one of
the 192 fps samples was `None`; "8/8 never settled" is withdrawn, not
converted to a finding.

## The decoder session beside the close-out table

Context for a session with 20 deliberate restarts, not a gate:

| row | target | 2026-09-20 C3.L3a session | close-out C / W |
| --- | ---: | ---: | ---: |
| spikes ≥ 20 ms / min | < 200 | **2,562** | 32.8 / 26.0 |
| rendered fps | ≥ 59.5 | **56.14** | 59.90 / 59.91 |
| stale output drops / min | < 20 | **170.9** | 1.14 / 0.80 |
| video loss / min (post-FEC) | < 10 | **202.8** | 8.67 / 8.40 |
| max output gap (ms) | ≤ 100 | **558** | 163 / 110 |

## Pre-registered reading, written against the noise, not the table

With 4 events per shape, 15 marks at a chance rate of 0.036 per second, and
the window itself shorter than the observed reaction lag, this session
cannot separate any shape from the decoys at any window — at W 2.5 the
window is shorter than the measured reaction lag, and at W 5.0 the decoys
are marked as often as the sequences. The table shows that, and nothing
more. **The re-score corrects the record; it does not answer the gate**, in
either direction. Lifecycle stands as a real result: 0 FEC / 0 audio / 0
controller deltas over 16 transitions, and 20 clean SSRC changes
(`jump_packets` 0, first IDR 17-34 ms).

## Rerun decision — RERUN REQUIRED

On two independent grounds, either sufficient:

- **(a)** the session predates the adopted build — before the 90 KB cap
  (`P6a`), the 12/17 cushion, the 2/4 redundancy, the headless host — and
  ran on a baseline then failing every row (its own decoder session: 2,562
  spikes/min, 56.1 fps, 202.8 lost/min, above), so both the marks and the
  picture ratings were taken on a stream that was already unhealthy;
- **(b)** n = 4 per shape against the design's own bar of ~20 pooled.

**The rerun's pre-registration** (the probe is left ready; **not run** —
the rerun is the user's play session, and Cowork hands them the steps):

- `python3 tools/probe_c3_l3a_gameplay_acceptance.py --traversals 10
  --dwell-min 55 --dwell-max 90 --window 5.0` (these are now the defaults);
  then `--finalize` per session, `--aggregate` over them;
- **primary W = 5.0 s**, chosen from the measured 2.7-4.3 s lags; 2.5 and
  8.0 reported beside it; the choice is fixed now, before the data;
- decoys scored through both matched windows; decoy placement enforced by
  `build_schedule` (ramp-matched window at W 8.0 ends ≥ 3 s before the next
  fire);
- **≥ 4 sessions pooled to ≥ 20 per shape** (10 traversals = 5 jumps + 5
  ramps per session); shape order randomized per run (fresh seed each);
- Phase B at 6000 / 5500 / 5000 on the anchored 1-10 scale;
- on the adopted build and profile, as the close-out scored it;
- for each session the record also carries the decoder session's close-out
  rows (spikes/min, rendered fps, stale drops/min, video loss/min post-FEC,
  max output gap) beside `D_BASE_CLOSEOUT_2026-09-23.md` — context for a
  session with 20+ deliberate restarts, not a gate. `--finalize` now prints
  them.

**`C3.L4` stays BLOCKED on the gate.**

## Validation performed

- `py_compile` on both tools;
- `--plan` for 8 and 10 traversals and a 2,000-seed sweep: the decoy rule
  holds on every dwell; the 2026-09-20 dwell refused (`plan_output.txt`);
- the re-score reproduces 16 transitions, 8 decoys, 15 marks, 20 expected
  SSRC changes (= 20 seen); alignment spread 0.457 s, max residual 0.255 s;
- the as-installed column reproduces the 2026-09-20 report exactly (0/4,
  0/4, 1/8, 14 unattributed);
- `--finalize` with and without `--decoder` chose the same decoder file;
- `--aggregate` over the one run file works; header convention unchanged
  (`Classification: C3_L3A_GAMEPLAY_ACCEPTANCE_RECORDED`, `Production files
  modified by probe: NONE`, `Network addresses collected/logged: NONE`);
  `manual_checkout.Report` untouched;
- telemetry paths checked against the live endpoint, stream idle;
- state file SHA-256 identical before and after.

**Not performed:** no session, no settling measurement, no self-test that
fakes a companion, no synthetic state.

## Files (`c3_l3a_p2r1_2026-09-23/`)

- `c3_l3a_gameplay_acceptance_state.json` — byte copy of the retained state;
- `native_decoder_20260920_051218_321.json` — copy of the decoder session;
- `as_installed_2026-09-20/` — the 2026-09-20 finalize outputs, byte copies
  (the re-score overwrote `logs/streaming/`'s, which is gitignored);
- `rescore_20260920_010023.{json,txt}` — the re-score;
- `aggregate_one_run.{json,txt}` — `--aggregate` over it;
- `plan_output.txt`; `telemetry_paths_idle_check.txt`,
  `telemetry_endpoint_idle.json.txt`, `native_stream_status_idle.json`;
- `pre_patch_sha256.txt`, `post_patch_sha256.txt`,
  `retained_state_sha256_before.txt`, `retained_state_sha256_after.txt`;
- `sha256_manifest.txt` — every file above.

## Privacy

Loopback only. No network address or device identifier in any file here;
the idle endpoint captures carry none.
