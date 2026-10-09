---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: 969085f
durable_memory_updated: true
---

# E3-R2: the controller-silence pause's exit, and the silence-gap log, behind `PRIVYHUB_RECOVERY_TRIGGER=v2` (dormant)

## Purpose

E3-R2 (`handoffs/E3-R2_RECOVERY_PAUSE_EXIT_TASK.md`, record
`evidence/E3_R2_RECOVERY_PAUSE_EXIT_2026-10-08.md`). It fixes the false
pause E3-R1 located: the host's `controller_silence` trigger fired on 1-3-s
client→host stalls with the client still playing, and the pause had no
exit. Together with R1's v2 threshold, this is one change behind one flag.

**REJECTED by the pre-registered bar** (iii: the CONC rows' rendered fps
was above its band; v: one gap began 41 ms after a gap-log write). The
replay bar held, and no recovery pause fired in the four runs. NOT
ADOPTED. Adoption in any case waits for the user's nft paste.

## Change

- **`companion/native_session_io.py`** (`NativeControllerBridge`):
  - `set_gap_log(path)` starts the gap log with its own writer thread;
  - `_gap_note_packet()` runs per accepted packet, only while the log is
    on;
  - `_gap_flush()` hands one line to the writer: start, end, gap_ms,
    burst_500ms, burst_truncated, plus logged_utc;
  - the receive loop's timeout branch flushes a gap 500 ms after it
    ends. Absent: the per-packet path is today's plus one `is not None`
    test.
- **`companion/games/link_drop_recovery.py`**:
  - `EXIT_CTRL_AGE_MS 500`, `EXIT_CONFIRM_S 0.25`, `EXIT_OUTPUT_AGE_MS 300`;
  - `enable_controller_exit()` and `_maybe_exit_controller_pause()`,
    called from `_tick` after the give-up check, while
    `PAUSED_RECOVERING` from `controller_silence` only;
  - the resume is `resume_game` (`EmulatorManager.resume()`); it logs
    `resumed` with `via: controller_return`, or `controller_exit_failed`.
- **`companion/plugins/games.py`**: with the flag, the exit is enabled
  and the gap log is set to `logs/games/native_stream_ctrl_gaps.log`.
  `PRIVYHUB_RECOVERY_GAP_LOG=1` alone turns on only the log.
- Diff: `evidence/e3_r2_2026-10-08/e3_r2_recovery_exit.diff`.

## Validation

- `py_compile`; `git diff --check`.
- `evidence/e3_r2_2026-10-08/test_e3_r2.py` 17/17 (synthetic
  timelines); the writer thread end to end against a temp file.
- `tools/test_c3_f1_recovery_restart.py` 7/8: the same pre-existing
  error as at `def1ad1`.
- The 10-min gap-log probe; 4 suite runs with the flag (the record).

## Rollback

The flag is absent everywhere. To remove the code, reverse the diff.
