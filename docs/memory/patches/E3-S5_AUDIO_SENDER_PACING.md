---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
durable_memory_updated: true
---

# E3-S5: the Linux audio sender's pacer as one timed wait per packet, behind `PRIVYHUB_AUDIO_SENDER_PACING=frame`

## Purpose

E3's fifth item (`handoffs/E3-S5_AUDIO_SENDER_COST_TASK.md`, record
`evidence/E3_S5_AUDIO_SENDER_COST_2026-10-06.md`). The probe measured
85.8 wake-ups per audio packet.

**NOT ADOPTED (REJECTED by the bar on one run's loss).**

## Change

`companion/native_session_io.py`:

- `_linux_sender_loop` sets `self._linux_pacing_frame` from the flag once,
  after the SCHED_RR setup.
- `_linux_wait_until`: when it is set, `self._linux_stop_event.wait(remaining)`
  and re-check, instead of the 1-ms waits, yields and the final spin.
- Absent: today's wait.

## Validation

- `py_compile`.
- The probe and a flagged smoke (not data): 13.7 → 2.25 % of a core,
  17,167 → 277 wake-ups/s, 200 packets/s, 0 underflows.
- The benchmark: see the record.

## Rollback

Unset the flag. To remove the code, revert `companion/native_session_io.py`
to `d9fdbdd`.
