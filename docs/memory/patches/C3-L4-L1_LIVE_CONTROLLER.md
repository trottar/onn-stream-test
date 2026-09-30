---
memory_schema: 1
as_of: 2026-09-28
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C3-L4-L1: the live adaptive-bitrate mode (flag `live`, default off)

## Purpose

This builds the acting mode `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`
authorizes: one `video_only_restart` per adaptation event, straight to the
target, with the existing hold-downs as the minimum spacing, the blackout
kept, and no ramp. Task: `handoffs/C3-L4-L1_LIVE_CONTROLLER_TASK.md` (queue
2026-09-28B item 1, authorized by the user 2026-09-28). Design note:
`evidence/c3_l4_l1_2026-09-28/c3_l4_l1_design.txt`. Record:
`evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`.

## Change

- **New** `companion/adaptive_bitrate_live.py`:
  - `LivePolicy`, the pure live decision path. It subclasses the shadow's
    `ShadowPolicy` for the evidence rules and adds:
    - the mapping table: FALLBACK → 5000, ROUTINE → 6000, an increase is
      one rung;
    - the hold-down table;
    - the ROUTINE escalation deferral;
    - the guards, including a session age of at least 60 s;
    - the rate limit (4 per 10 min);
    - `inject()`, `actuation_done()` and `note_ssrc_change()`;
    - the companion-session reset.
  - `LiveController`, the wrapper:
    - the guard inputs;
    - one actuator worker, which takes `NativeStreamManager._lock` and
      re-reads the recovery state under it;
    - the decision log (the existing
      `logs/games/adaptive_bitrate_shadow.jsonl`; state rows only on a
      state change);
    - the status field;
    - `disable()` and `inject()`.
  - `get_controller()`: `live` gives the `LiveController`; any other value
    gives the shadow module's own instance, unchanged.
  - `handle_route()` serves `POST /plugins/games/adaptive-bitrate/disable`
    and `/inject?class=FALLBACK|ROUTINE`.
- `companion/plugins/games.py`:
  - the controller is taken from `get_controller()`. In live mode it is
    bound to the actuator the loopback `c3-validated-bitrate-transition`
    route calls (`diagnostic_c3_validated_bitrate_transition`), to the
    stream manager's lock and to recovery's state;
  - recovery's restart and full start are wrapped, and they notify the
    controller (the blackout);
  - `session_ended` resets it on stop, on `native-stream-stop`, on
    recovery's `END_MS` end and on a fresh (non-recovery) gameplay
    release;
  - `native-stream-status.adaptive_bitrate` comes from the controller.
- `companion/privyhub_service.py`:
  - the client-health path passes the native status to the live
    controller as its guard inputs; the shadow call is unchanged;
  - the four-part POST route `plugins/games/adaptive-bitrate/<verb>` is
    added before the three-part plugin dispatch.
- `companion/games/link_drop_recovery.py`: `current_state()`, a lock-held
  read of the state.
- **New** `tools/test_adaptive_bitrate_live.py`: 43 tests.
- **New** `tools/c3_l4_l1_replay.py`: parity against the `C3-L4-S1` night,
  and the would-fire lists over `C4-D1` + `CTRL-L1`.

**Not changed:**

- `companion/adaptive_bitrate.py` and `tools/test_adaptive_bitrate_shadow.py`
  are byte-identical;
- the profile, the encoder flags, the cap, cushion, redundancy and FEC;
- the client.

## Validation

- `py_compile` is clean. `git diff --check` is clean, and so is a
  trailing-whitespace scan of the new files.
- The live suite passes **43 / 43**.
- The shadow suite passes **21 / 21, unchanged**
  (`evidence/c3_l4_l1_2026-09-28/unit_tests.txt`).
- **Parity:** 3,594 rebuilt reports of the shadow night. The control
  check reproduces all 1,048 logged changes. Shadow and live both take
  **zero actions**.
- **Loss replays:** 88 sessions and 44,634 reports. There are **8**
  transitions (proxy) or **9** (bound). There is at most **1**
  transition in any 10-minute window, and **RATE_LIMITED never trips**
  (`c3_l4_l1_replays.txt`).
- **Flag off**, after a restart through the unit: `adaptive_bitrate` reads
  `{schema, mode: off, acted: false}`, exactly as before. The routes
  return:
  - disable: 200, a no-op;
  - inject: 403;
  - enable: 404
  (`smoke_flag_off.txt`).
- **Live**: Session A and Session B, in the record.

## Files (SHA-256 after)

`evidence/c3_l4_l1_2026-09-28/post_patch_sha256.txt`; before:
`pre_patch_sha256.txt`. The diff of the three edited files is
`companion_patch.diff`. The new module, the tests and the replay tool are
copied into the same directory.

## Rollback

Unset `PRIVYHUB_ADAPTIVE_BITRATE_MODE` (and `_INJECT`), then
`systemctl --user restart privyhub-companion`. Off and shadow never build
the live controller. To remove the code, delete
`companion/adaptive_bitrate_live.py`, revert the three hunks
(`companion_patch.diff`) and restart.
