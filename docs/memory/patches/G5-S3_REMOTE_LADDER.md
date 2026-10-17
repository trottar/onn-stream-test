---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 1dab25d
durable_memory_updated: true
---

# G5-S3: the remote ladder, behind `PRIVYHUB_REMOTE_LADDER=1`

## Purpose

G5-S2's two findings, closed behind a flag:

- the live ladder learns the session's routing class (`path_class`);
- on a remote path only, the ladder and its actuator can use 720p/4000.

Record: `evidence/G5_S3_REMOTE_LADDER_2026-10-17.md`.

## Change

- **New** `companion/remote_ladder.py`: one shared `RemoteLadder` per process.
  - `note_stream_start` sets the class from G3's overlay test, applied to the
    class-matched target the gate hands the games plugin. Only the class is
    kept.
  - `apply` puts `path_class` in the context and sets the policy's ladder
    `(4000,) + base` on a remote path.
  - `actuator_levels` is `(4000,)` on a remote path.
  - `annotate` adds `path_class` to every row, `remote_rung` to a move to or
    from 4000, and the decision to its actuation result.
  - `floor_actuates` lets G5-S2's `floor_4000` actuate.
- **Guarded hooks** (each a module global built only under the flag, with the
  import inside the `if`, plus one `if` at the site):
  - `companion/adaptive_bitrate_live.py`: `LiveController._ctx` (the context
    builder) and `LiveController._write`. `LivePolicy` is not edited.
  - `companion/plugins/games.py`: `native-stream-start`, after the stream
    started. It reads `adaptive_bitrate_live.REMOTE_LADDER`; there is no new
    import.
  - `companion/diagnostics/c3_linux_actuator_probe.py`: the validated list in
    `_run_c3_linux_bitrate_cycle` becomes a local, extended by
    `actuator_levels()`. It covers the transition and recovery's same-level
    restart. `native_stream.py` is not edited.
  - `companion/wan_adaptation.py`: the forced decrease also runs for
    `floor_4000` when `floor_actuates`.
- Predecessor and after sha256: `g5_s3_2026-10-17/predecessor_sha256.txt`,
  `after_sha256.txt`.
- **New tests:** `tests/remote_ladder/test_remote_ladder.py` (26).
- **Docs:**
  - `docs/WAN_ADAPTATION_RULES.md`: the status line and the G5-S3 lines under
    R3.2 and R5;
  - ROADMAP §G5: the G5-S3 paragraph.

## Validation

- `python3 -m unittest discover -s tests/remote_ladder` → 26 OK.
- Regression:
  - `tests/overlay` 17, `tests/session_identity` 80, `tests/wan_telemetry` 18,
    `tests/wan_adaptation` 23: all OK;
  - `tools/test_adaptive_bitrate_live.py` 126 OK;
  - `tools/test_c3_f1_recovery_restart.py` 7/8. The one error is pre-existing
    at HEAD.
- **Flag absent** (`flag_absent_proof.py`):
  - actuator, HEAD vs edited: 200/200 cases identical;
  - games plugin stream start, HEAD vs edited: 3/3 identical;
  - G5-S2's `replay.py` re-run: exact and identical, and its tables are equal.
- **Flag present** (`replay.py`): 6 runs × rules off/on. No run reaches 4000;
  nothing goes below 4000; 4000 is never used on the LAN; every row carries
  `path_class`.

## Result

BUILT behind the flag; NOT ADOPTED; unvalidated live; nothing committed.
`PATCH_INDEX.md` was not updated (not session B's file).
