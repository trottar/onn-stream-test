---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 05aac43
durable_memory_updated: true
---

# C3-L3A-R1 — `--finalize` across a split client session; every run keeps its state

## Purpose

Rerun session 1 (run `20260924_115810`) could not be put on the decoder
axis: the user's accidental BACK mid-run split the client stream into two
decoder sessions (9 + 15 = 24 SSRC changes), and `--finalize` looked only
for one session with all 24. Teach it to use the sessions together, and
keep each run's state file so the next run cannot overwrite it. Task:
`handoffs/C3-L3A-R1_TASK.md`, authorized by the user 2026-09-24. Record:
`evidence/C3_L3A_R1_SESSION1_2026-09-24.md`.

**Tools and documentation only.** No companion, client, profile, route or
environment change; no session run.

## Expected predecessor

`05aac43` (probe SHA-256 `f574c256…3641`, = `C3-L3A-P2R3`'s after).

## Changed scope

| file | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `tools/probe_c3_l3a_gameplay_acceptance.py` | `f574c2563e0b5f45578f51677177c294effc55d245c4a7befddaa0dabe903641` | `5ec6be72640b6a57e839b8280c2ce18f0bad11f51f707edea9cbd9a874977e2c` |

Also in `evidence/c3_l3a_r1_2026-09-24/{pre,post}_patch_sha256.txt`.

- `STATES_ROOT` (`c3_l3a_runs/states/`); `run_session()` writes
  `<run_id>_state.json` there beside the shared state file;
  `default_state_path()` prefers the newest copy when the shared file
  holds a different, older run.
- `run_started()`, `select_split_sessions()` — sessions posted after the
  run's start, in order, until their `ssrc_changes` reach the expected
  count; used only on an exact sum.
- `decoder_summary()` (factored out of `finalize()`), `split_decoder()` —
  each session aligned on its own slice of the expected transitions; marks
  checked in the covering session; `client_restarts`; per-session
  close-out rows.
- `decoder_view(..., split=)` — places only the marks inside the session's
  span; a slice with no Phase-A fire aligns on its v2 park / restore fire
  times; every view gains `session_probe_span_s`.
- `--decoder` takes one or more files (same exact-sum rule).
- Report: CLIENT RESTARTS section; `sess` columns; per-session alignment,
  coverage and decoder fields; close-out rows side by side
  (`_coverage_lines()`, `DECODER_FIELDS`). Single-session output unchanged.

Scoring, windows, prompts and the pooling rule are unchanged.

Created: `logs/streaming/c3_l3a_runs/states/20260924_115810_state.json`
(byte copy of the shared state). Regenerated:
`c3_l3a_runs/20260924_115810.{json,txt}`, the latest-run report and the
aggregate.

Memory: `evidence/C3_L3A_R1_SESSION1_2026-09-24.md`, `CURRENT.md`,
`TOOLS.md`, `2026-09-24.md`, `investigations/ACTIVE.md`,
`handoffs/CURRENT_HANDOFF.md`; generated `patches/PATCH_INDEX.md`.

## Validation performed

- `py_compile`;
- smoke and 2026-09-20 runs re-finalized with the old and new probe: text
  reports identical but for `Generated:`, JSON differs by the additive
  `session_probe_span_s` only;
- scratch directory: auto split found (2 sessions, sum 24); a 25-expected
  state refused with the counts, auto and with `--decoder`; state-copy
  preference both ways;
- run `20260924_115810` re-finalized with both sessions: both alignments OK
  (spread 0.231 / 0.255 s), 24 rows, 19 marks placed, restart at probe
  202.192 → 204.135 s; the hand check confirmed independently
  (`mark_check.py`);
- `--aggregate`: 1 pooled, detection unchanged;
- state file and decoder sessions SHA-256 unchanged;
  `tools/check_memory_health.py` healthy.

**Not exercised:** the run-path state copy (interactive; no session run).
The next run will be its first use.

## Negative results

- `--aggregate`'s Phase B table prints this session's defaulted answers as
  recorded; an annotation mechanism was out of scope, so the record carries
  the annotated row.

## Result

INSTALLED SUCCESSFULLY (tools, documentation). `C3.L4` stays BLOCKED.
