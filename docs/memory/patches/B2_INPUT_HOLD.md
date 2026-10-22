---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3 (on top of B1's uncommitted edits)
---

# B2 — the fast input hold behind `PRIVYHUB_INPUT_HOLD=<H ms>`

**Result: BUILT, unit-tested; NOT ADOPTED; no live run.** Session B, 2026-10-22 (`handoffs/QUEUE_2026-10-22B.md` B2).
Record: `evidence/B2_INPUT_HOLD_2026-10-22.md`. Nothing committed.

- **Settled first:** the client sends its whole controller state ~430 times a second, unconditionally
  (`NativeControllerSender.sendLoop`), so a silence is the link.
- **What it does:** a controller silence ≥ H (100-4000; `1` / `on` = 250) during play pauses the core through
  recovery v2's own `_enter_recovery` (reason `input_hold`, one `desync_pause` row, `EmulatorManager.pause()`). The
  first packet back resumes it (`resumed`, `via: input_release`, `held_ms`).
  - Another trigger during a hold (v2's 5.35-s `controller_silence`, the client's desync) takes it over with no
    second pause.
  - Limits: a 50-ms minimum hold, ≤ 6 holds per 60 s, and the user's pause wins.
- **Files** (`evidence/b2_2026-10-22/b2.diff`):
  - `companion/input_hold.py` (new);
  - `companion/games/link_drop_recovery.py` (+85: two methods, a constant, the handover statement);
  - `companion/native_session_io.py` (+15: a class attribute, a setter, two guarded statements);
  - `companion/plugins/games.py` (+9: a guarded import, one guarded call);
  - `tests/input_hold/test_input_hold.py` (new), `tools/unattended_frames.py` (new).

  After-hashes in `after_sha256.txt`.
- **Validation:** input_hold 18 OK; the recovery suite 17 OK; all regression suites green but C3-F1's pre-existing
  error. Flag absent: the hooked functions' AST identical to the predecessors'; not imported.
- **The measure:** `tools/unattended_frames.py`, which gives a raw count and the core-running count (recovery's
  paused spans subtracted; the frozen picture keeps streaming while paused). Baseline, core running: Sunday 684 per
  10 min, last night 142, the death 84.
- **Rollback (written, not applied):** copy the three predecessors back from `evidence/b2_2026-10-22/predecessors/`
  (B1's files for two of them), and remove `companion/input_hold.py`, `tests/input_hold/` and
  `tools/unattended_frames.py`.
