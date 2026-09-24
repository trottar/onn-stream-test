---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 4e82298
durable_memory_updated: true
---

# C3-L3A-P2R1 — gameplay acceptance probe: five defects fixed, retained run re-scored

## Purpose

Fix `tools/probe_c3_l3a_gameplay_acceptance.py`'s three recorded defects
(`2026-09-20.md`) and the two found on re-reading it, re-score the retained
2026-09-20 session without replaying, and pre-register the rerun. Task:
`handoffs/C3-L3A-P2R1_TASK.md`, authorized by the user 2026-09-23. Record:
`evidence/C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md`.

**Tools and documentation only.** No companion, client, profile, route or
environment change; no stream or session started; the companion not
restarted.

## Expected predecessor

`4e82298` (D-BASE closed; Phase C resumed at `C3.L3a` Part 2).

## Changed scope

| file | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `tools/probe_c3_l3a_gameplay_acceptance.py` | `7b1d5c2425806466ddd2ca6d661c2c9f79e5a113becae0fd8f4d24ba63ffb8a7` | `4057e7697c9280ad45d77b5bfe2ecbb171d77015598e478949f230cf4ba724c5` |
| `tools/manual_checkout.py` | `1e2980b80cc97dc67b16fc05dbb520caf1363f6645025a2df5577b675ec77cbc` | `282e1bd2144a136e7a38cb909e22dec702605e20bdd3aa2ae99093c10bd85030` |

Also in `evidence/c3_l3a_p2r1_2026-09-23/{pre,post}_patch_sha256.txt`.

**`tools/manual_checkout.py`** — `ask_int(..., anchors=None)`: a
`{point: meaning}` map printed above the prompt, highest first. Additive;
`Report`, `yes`, `MarkCapture` untouched, so the `Classification:` header
convention is byte-identical.

**`tools/probe_c3_l3a_gameplay_acceptance.py`**:

1. **Windows** — sequence `[first fire, end_s + W]`; decoys jump-matched
   `[d, d + W]` and ramp-matched `[d, d + ramp_span + W]` (median ramp
   span of the run); per class events / marked / marks / exposure (union) /
   marks per s / chance-expected marks, beside the chance rate; W at 2.5,
   5.0, 8.0 always; lag of every mark from the nearest preceding fire and
   decoy, with histograms. The pre-fix attribution is kept as
   `score_as_installed` and printed only for pre-v2 state, for comparison.
2. **Telemetry** — endpoint paths from `stream_telemetry.py`; settled = two
   distinct (`session_elapsed_ms` advanced) fresh snapshots,
   `waiting_for_idr` not true, `recent_fps` ≥ 54; the first snapshot never
   counts; record carries `sample_interval_ms`, snapshot cadence, distinct
   count, `budget_ok` (≥ 3 intervals); poll timeout 2 s. Preflight refuses if
   telemetry is not fresh or the budget is under three intervals.
3. **Rating** — 1-10 with anchors (10 = looks the same as 7000; 5 = clearly
   softer, still playable; 1 = unplayable), `rating_scale` stored in state
   and printed on every rating line; `LEGACY_RATING_SCALES` carries the
   2026-09-20 run's stated scale, never a rescale.
4. **SSRC accounting** — `expected_transitions()`: Phase A + restores that
   transitioned + parks (v1: Phase-A restore derived). State v2 records
   every restore (`restores`, `transitioned`, `at_s`) and each park's
   `fired_at_s`, and each step's `returned_at_s`. `--state`, `--decoder`;
   auto-selection = earliest session not in `decoder_sessions_before`,
   received after `generated`, `ssrc_changes` ≥ expected.
5. **Requirement 4** — clock alignment (Phase-A fires ↔ first N
   `ssrc_change`s, median offset, spread; > 1 s stops the decoder view),
   per-transition SSRC / residual / first IDR / max `output_gap_ms` in
   `[fire, fire + 1 s]` with full / partial / no slow-event coverage, and each
   mark's nearest preceding discontinuity and lag.

Also: decoy offset fixed by `build_schedule` (≥ 14 s after the sequence end;
ramp-matched window at the widest reported W ends ≥ 3 s before the next
fire; too-short dwell refused); runtime records `planned_at_s` / `late_s`;
defaults `--traversals 10 --dwell-min 55 --dwell-max 90 --window 5.0`;
`--plan` prints per-dwell placement and whether the rule holds; `--finalize`
writes `c3_l3a_runs/<run_id>.txt` beside the JSON and prints the decoder
session's close-out rows; `--aggregate` pools the per-window scoring
(`privyhub_c3_l3a_aggregate_v2`) and skips pre-v2 run files by name. State
schema `_v2`, analysis `_v2`. The shape shuffle precedes the dwell draws, so
a seed reproduces the same shape order as before.

Memory: `investigations/BASELINE_STREAM_HEALTH.md`,
`investigations/ACTIVE.md`, `CURRENT.md`, `TOOLS.md`, `2026-09-23.md`,
`handoffs/CURRENT_HANDOFF.md`; generated `patches/PATCH_INDEX.md`.

## Validation performed

- `py_compile` both tools;
- `--plan --traversals 8` and `10`: rule holds on every dwell (min slack
  10.5 / 8.1 s); seeds 1-2000 × {8, 10}: min slack 5.82 s; 30-75 s dwell
  refused;
- `--finalize --state logs/streaming/c3_l3a_gameplay_acceptance_state.json
  --decoder logs/games/decoder_sessions/native_decoder_20260920_051218_321.json`:
  16 transitions, 8 decoys, 15 marks, 20 expected = 20 seen SSRC changes;
  alignment offset 35.017 s, spread 0.457 s; as-installed column equals the
  2026-09-20 report; auto-selection picks the same decoder file;
- `--aggregate` over the one run file: works;
- telemetry paths against the live endpoint, stream idle: all present;
  `sample_settling()` for its 12 s budget: not settled, 0 distinct
  snapshots, `budget_ok` true (interval 2000 ms);
- retained state SHA-256 `ed4c241a…0463` unchanged;
- `tools/check_memory_health.py`: healthy;
- LF line endings, trailing newline.

**Not performed:** no session; settling not measured; no mock companion or
synthetic state.

## Negative results

- **The 2026-09-20 finalize never read a decoder session** — it ran 30 s
  before the client posted.
- **The handoff's figures needed three small corrections**: ramp-matched
  exposures 112.6 / 132.6 / 156.6 s (not 112.8 / 132.8 / 156.8 — rounding);
  six marks within 5 s of a fire, not seven; ramp 6's first rung is only
  partly inside slow-event coverage. The idle endpoint answers `available:
  true, fresh: false` (last report retained), not `available: false`.
- **The retained run's decoy windows overlapped sequences** (4 of 7
  ramp-matched windows at W 5.0), which the old schedule could not prevent.

## Result

INSTALLED SUCCESSFULLY (tools, documentation). The re-score corrects the
record and does not answer the `C3.L4` gate. RERUN REQUIRED, pre-registered;
not run. `C3.L4` stays BLOCKED.
