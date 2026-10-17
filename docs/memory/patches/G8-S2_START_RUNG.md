---
memory_schema: 1
as_of: 2026-10-17
baseline_commit: 80f3fc4
durable_memory_updated: true
---

# G8-S2: the start rung, behind `PRIVYHUB_START_RUNG=<floor|cap|kbps>`

## Purpose

Today a stream starts at 7000 (≈ 8.25 Mbit/s on the video hop). G8-S1's cap profiles
never reached PLAYING. With the flag a stream starts low, and the ladder's own
increase rule brings it up. Record: `evidence/G8_S2_START_RUNG_2026-10-17.md`.

## Change

- **New** `companion/start_rung.py`: the parsing, the active list per start, the
  choice (`floor` / `cap` / a rung, invalid → today's 7000, each problem logged once),
  the encoder kwargs (none for 7000), the record (`annotate`).
- **`companion/native_stream.py`** (predecessor and after sha256 in
  `g8_s2_2026-10-17/`):
  - a module global `START_RUNG`, built only under the flag, with the import
    inside the `if`;
  - one `if` in `_start_linux_locked`, at the first-target argv call: the start
    rung's `bitrate_kbps / max_bitrate_kbps` and `_active_bitrate_kbps`.
  - Absent: the same call, unchanged.
- **`companion/adaptive_bitrate_live.py`:** a module global `START_RUNG`, and one
  `if` in `LiveController._write`. It writes the start rung, its source, the
  request, the active list and the path class on the session's first `sample`
  row after each start. It annotates only; no decision changes.
- **New tests:** `tests/start_rung/test_start_rung.py` (17) and its helper
  `stub_manager.py`.
- **Docs:** ROADMAP §G8, the G8-S2 line.

## Validation

See the record:

- `tests/start_rung` 17 OK; the suites green (C3-F1's pre-existing error aside);
- flag absent (`flag_absent_proof.py`):
  - the first-target handler is identical to HEAD;
  - G5-S2's and G5-S3's replays re-run identical over the sessions the ladder's
    log still holds (one of G5-S2's four rotated out, disclosed);
  - HEAD's vs today's controller over 70 sessions: identical;
- the cap proof (`cap_proof.py`);
- the floor replay (`replay.py`).

## Result

BUILT behind the flag; NOT ADOPTED; unvalidated live (G8-S3 is the proposed live
re-run); nothing committed. `PATCH_INDEX.md` was not updated (not session B's file).
