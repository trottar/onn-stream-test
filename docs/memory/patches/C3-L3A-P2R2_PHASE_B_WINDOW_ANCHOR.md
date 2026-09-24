---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 4e82298
durable_memory_updated: true
---

# C3-L3A-P2R2 — per-transition windows anchor on the matched SSRC change

## Purpose

Record the 2026-09-24 `C3.L3a` smoke session (the fixed probe's first run on
the adopted build) and fix the one report defect it exposed: the
per-transition decoder view started each transition's 1 s slow-event window
at `fire + offset`, which misses the decoder's restart by the row's
residual. Task: `handoffs/C3-L3A-P2R2_TASK.md`, authorized by the user
2026-09-24. Record: `evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`.

**Tools and documentation only.** No companion, client, profile, route or
environment change; no session run.

## Expected predecessor

`4e82298` plus the uncommitted `C3-L3A-P2R1` working tree (probe SHA-256
`4057e769…24c5`).

## Changed scope

| file | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `tools/probe_c3_l3a_gameplay_acceptance.py` | `4057e7697c9280ad45d77b5bfe2ecbb171d77015598e478949f230cf4ba724c5` | `b1e69245a2c70d00d27f18027d7124bd951b6768822e1269336baa6c2769719c` |

Also in `evidence/c3_l3a_p2r2_2026-09-24/{pre,post}_patch_sha256.txt`.

`decoder_view`: every row — Phase A, parks, restores — takes its window
from its own matched `ssrc_change` (`window_from: "ssrc_change"`); the fire
time and residual stay beside it. Slow-event rows now carry `codec_ms`; each
transition row adds `max_gap_codec_ms` and `max_gap_after_ssrc_ms` for the
largest gap in its window. Report: two new columns (`at +ms`, `codec ms`),
the anchoring stated under the table, and the "before that point" coverage
note printed only when the slow-event buffer is saturated. Nothing else in
scoring, alignment, settling or the schedule changed.

Memory: `investigations/ACTIVE.md`, `CURRENT.md`, `2026-09-24.md` (new),
`handoffs/CURRENT_HANDOFF.md`, `evidence/RUNTIME_VALIDATION.md`; generated
`patches/PATCH_INDEX.md`.

## Validation performed

- `py_compile`;
- smoke re-finalized (`--state` / `--decoder`): rows 125 / 198 / 154 / 187 /
  211 / 166 / 203 / 189 ms, `codec_ms` 7-11 (the 6000 park was 72, the 5500
  park "–");
- 2026-09-20 copy re-finalized: per-transition values unchanged; the partial
  window's coverage boundary moved 0.593 → 0.551 s (the anchor moved by the
  row's residual); all other analysis keys identical;
- inputs' SHA-256 unchanged; `--aggregate` runs;
- `tools/check_memory_health.py` healthy; LF, trailing newline.

## Negative results

- **`--aggregate` still pools the 2026-09-20 run.** P2R1's skip keys on the
  analysis schema and its re-finalize wrote that file as `_v2`. Not changed
  here (one-fix scope; the files stay where P2R1 left them); to be resolved
  before the rerun is pooled — the user's decision.
- The task's premise that Phase A already anchored on the SSRC change was
  wrong; Phase A values happen to be unchanged on both runs.

## Result

INSTALLED SUCCESSFULLY (tools, documentation). The smoke is not a gate
observation; the rerun pre-registration is unchanged; `C3.L4` stays BLOCKED.
