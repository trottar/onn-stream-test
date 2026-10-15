---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
durable_memory_updated: true
---

# E4-S5: the x11grab encoder's output rate set explicitly, behind `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` (REJECTED; dormant)

## Purpose

E4-S5 (`handoffs/E4-S5_SNES_CAPTURE_59FPS_TASK.md`, record
`evidence/E4_S5_SNES_CAPTURE_59FPS_2026-10-10.md`) found the SNES 59-fps
fault. The encoder inherits x11grab's probed input rate (`tbr`), which
the SNES window sometimes probes at 59 or 59.94.

## Change

**`companion/native_stream.py`** (predecessor `3f02447d…e598` = HEAD,
now `b1a71fe1…4057`):

- With the flag, `["-r", str(self.FPS)]` is inserted before `"-an"` in
  the x11grab / VAAPI encoder command, an output rate.
- Absent = today.
- Applied by `evidence/e4_s5_2026-10-10/apply_e4_s5.py` (anchor checked,
  predecessor kept); diff `e4_s5_change.diff`.

**`tools/e1_suite.py`** (predecessor `e35e3053…6269`, E4-S4's; now
`33b60f01…3e61`):

- `E1_COUNTER_EXTRA` (escaped `\n`-separated lines) is appended to the
  per-run counter override, which is removed at teardown as before.
- Absent = today.
- Used for RetroArch's verbose log in E4-S5's sessions.

## Validation

- `e1_suite.py --self-test` OK; `git diff --check` clean.
- 3 unflagged sessions and 2 flagged runs ran on it.
- The flagged encoders carried `-r 60` (5 / 5) with no drop pattern.
- **Verdict REJECTED** (rendered fps on the link; the fix was not
  exercised by a bad probe).

## Rollback

- Restore `companion/native_stream.py` from HEAD (it had no uncommitted
  change before this).
- The runner's hook is inert without its variable.
