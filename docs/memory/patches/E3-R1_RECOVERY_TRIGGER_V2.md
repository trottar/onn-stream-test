---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: def1ad1
durable_memory_updated: true
---

# E3-R1: the host's controller-silence trigger, 5 s on two checks, behind `PRIVYHUB_RECOVERY_TRIGGER=v2` (dormant)

## Purpose

E3-R1 (`handoffs/E3-R1_RECOVERY_FALSE_PAUSE_TASK.md`, record
`evidence/E3_R1_RECOVERY_FALSE_PAUSE_2026-10-08.md`). Link-drop recovery
paused running games with the link up. The probe located the harmful
case: the host's `controller_silence` trigger fires on a 1-3-s
client→host stall while the client keeps playing, and the pause has no
way back.

**INCONCLUSIVE: the pre-registered replay of today's rule was not
faithful, so the task stopped before any run.** NOT ADOPTED.

## Change

- **`companion/native_session_io.py`**:
  - `set_client_silence_callback(callback, threshold_ms, confirm_ms=0)`;
  - `_silence_confirmed(now)`: with a confirm interval, the silence must
    be over the threshold on two checks that far apart with no packet
    between;
  - the receive loop's silence condition calls it;
  - with `confirm_ms` 0, the first check fires, as today.
- **`companion/plugins/games.py`**: with
  `PRIVYHUB_RECOVERY_TRIGGER=v2`, the callback is wired at 5,000 ms and
  `confirm_ms=250`. Absent: `DESYNC_MS` (1,000), confirm 0.
- Diff: `evidence/e3_r1_2026-10-08/e3_r1_trigger_v2.diff`. The client's
  desync post, the give-up timer, the restart path and the
  save-and-prompt flow are unchanged.

## Validation

- `py_compile`.
- A unit check of `_silence_confirmed`: today fires on the first check;
  v2 arms, then fires ≥ 250 ms later; a packet between re-arms it.
- `tools/test_c3_f1_recovery_restart.py` 7/8. The one error predates the
  change: its source probe fails at `def1ad1` too.
- No run (the replay stop).

## Rollback

The flag is absent everywhere. To remove the code, reverse the diff.
