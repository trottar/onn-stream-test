---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
durable_memory_updated: true
---

# E3-S5C: the Linux audio sender's pacer as one timed wait plus the final spin, behind `PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`

## Purpose

E3-S5C (`handoffs/E3-S5C_AUDIO_SENDER_PACING_SPIN_TASK.md`, record
`evidence/E3_S5C_AUDIO_SENDER_PACING_SPIN_2026-10-07.md`): E3-S5B's
`=frame` was REJECTED by 2 underruns in one run. Its probe found only a
wider tick jitter, from the timed wait's oversleep.

**ACCEPTED by the bar. NOT ADOPTED (the user's decision).**

## Change

`companion/native_session_io.py` (+7 lines; diff
`evidence/e3_s5c_2026-10-07/e3_s5c_frame_spin.diff`):

- `_linux_sender_loop` sets `self._linux_pacing_frame_spin` from the flag
  once, beside E3-S5's `_linux_pacing_frame`.
- `_linux_wait_until`, when it is set:
  `self._linux_stop_event.wait((remaining − 250 µs))` while more than
  250 µs remain, then the loop spins to the deadline, as today's final
  spin does.
- `=frame` is unchanged. Absent: today's wait.

## Validation

- `py_compile`.
- The probe, three ways (`probe.md`): sd 0.102 ms (today 0.076,
  `=frame` 0.181); 1.51 wake-ups per packet; sender 6.3 % of a core.
- The benchmark, 5 interleaved runs: sender 5.9-6.1 %, companion
  17.5-17.6 %, underruns 13 / 9 / 5 against controls 17 / 14.

## Rollback

Unset the flag. To remove the code, revert the two hunks
(`e3_s5c_frame_spin.diff`).
