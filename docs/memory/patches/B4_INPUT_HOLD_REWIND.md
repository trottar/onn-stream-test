---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: d4c9870
---

# B4 — rewind on the hold's release behind `PRIVYHUB_INPUT_HOLD_REWIND=1`

**Result: BUILT, unit-tested against a fake core; NOT ADOPTED; no live run.** Session B, 2026-10-22
(`handoffs/B4_INPUT_HOLD_REWIND_TASK.md`). Record: `evidence/B4_INPUT_HOLD_REWIND_2026-10-22.md`. Nothing committed.

- **What it does:** with B2's hold on, the release (and v2's controller-return exit after a handover) first rewinds
  RetroArch by the frames the core ran between the last controller packet and the confirmed pause.
  - The count is clock × 60, less a measured 4-frame confirmation lag, capped at 30
    (`PRIVYHUB_INPUT_HOLD_REWIND_CAP` 5-120).
  - The rewind: the input masked, `REWIND` + `PAUSE_TOGGLE`, `REWIND` per half frame, `GET_STATUS` `PLAYING`
    within 2 frames.
  - Then B2's resume as today.
  - Rows `input_release` / `rewind_failed`. The resume never depends on the rewind.
- **The launch config, flag on only:** `rewind_enable`, `rewind_granularity = 1`, `rewind_buffer_size` (bytes:
  ceil_MiB(raw state × (cap + 2)): snes9x 26 MiB, bsnes 9 MiB, Beetle PSX HW 513 MiB), and `audio_rewind_mute`
  (a fourth key, disclosed).
- **Flag absent:** whole-module AST identical, the config's masked hash identical (`91afed62…`), the tool's output
  identical. B2's 19 tests unchanged and green.
- **Files** (`evidence/b4_2026-10-22/b4.diff`):
  - `companion/hold_rewind.py` (new, 311);
  - `companion/input_hold.py` +9, `companion/games/link_drop_recovery.py` +11, `companion/native_session_io.py`
    +10, `companion/plugins/games.py` +9, `companion/games/emulator_manager.py` +15;
  - `tools/unattended_frames.py` (`--net`, +54 / −2);
  - `tests/input_hold_rewind/test_hold_rewind.py` (new, 22 tests).
- **Validation performed:**
  - the tests (22 + B2's 19 + the regression set, C3-F1's pre-existing error aside);
  - `proof_flag_absent.md`, `config_hashes.txt`, `unattended_noflag_equal.txt`;
  - `git diff --check` clean;
  - `redact_check.txt`.
- **Next (session A, BENCH-R2):** the blackout cell with hold + rewind (net unattended ≈ 0), E1 CPU per core with
  rewind on / off, Beetle PSX HW's renderer.
