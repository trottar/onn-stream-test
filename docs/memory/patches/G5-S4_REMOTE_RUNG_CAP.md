---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d (with G5-S3 uncommitted beside it)
durable_memory_updated: true
---

# G5-S4: the remote rung cap, behind `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>`

## Purpose

A data saver for remote sessions, set by the user, never automatic. Record:
`evidence/G5_S4_REMOTE_RUNG_CAP_2026-10-17.md`.

## Change

- **New** `companion/remote_cap.py`:
  - `parse`: valid only at 4000 / 5000 / 5500 / 6000 / 7000.
  - `RemoteCap`: inactive when the value is invalid or G5-S3's flag is absent.
  - `config_row` (once).
  - `clamp`, in the ladder's target selection: a decrease aimed above the cap
    goes to the cap; an increase aimed above it is refused `remote_cap`.
  - `after_feed`, the move to the cap: one ROUTINE decision, trigger
    `remote_cap`, through every gate.
- **`companion/adaptive_bitrate_live.py`** (predecessor = G5-S3's after,
  `b7ff0acb…`). Four guarded places, each `if REMOTE_CAP is not None`:
  - the module global, with the import inside the flag's `if`;
  - the controller's start (the config row);
  - `LivePolicy._decide`, after the target is chosen (the clamp);
  - `LiveController.observe`, after the feed (the move).
- **`companion/remote_ladder.py`** (G5-S3's): `annotate` lifts a clamp's
  `source` / `wish_kbps` / `capped_kbps` / `cap_kbps` from the measurements to
  the row, and carries them into the actuation's `decision`.
- **New tests:** `tests/remote_cap/test_remote_cap.py` (16).
- **Docs:**
  - `docs/WAN_ADAPTATION_RULES.md`: the G5-S4 line under R3;
  - ROADMAP §G5: the G5-S4 paragraph.

## Validation

- `tests/remote_cap` 16 OK.
- Regression: `tests/remote_ladder` 26, `tests/wan_adaptation` 23,
  `tests/wan_telemetry` 18, `tests/session_identity` 80, `tests/overlay` 17 and
  the ladder's 126, all OK. C3-F1 is 7/8; its one error is pre-existing at HEAD.
- **Flag absent:**
  - G5-S3's `flag_absent_proof.py` re-run: PASS;
  - G5-S3's replay re-run (the cap absent): its tables and output are identical.
- **Flag present** (`replay.py`): G4-S1's runs 1 and 2 at 4000 and 5000.
  Every remote session moves to the cap about 60 s in and never goes above it.
  The LAN is untouched. The data per hour is given as arithmetic.

## Result

BUILT behind the flag; NOT ADOPTED; unvalidated live; nothing committed.
`PATCH_INDEX.md` was not updated (not session B's file).
