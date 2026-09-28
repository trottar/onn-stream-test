---
memory_schema: 1
as_of: 2026-09-24
baseline_commit: 05aac43
durable_memory_updated: true
---

# C3-L3A-R2B: raise the decoder-report size cap to 48,000; log a rejected report

## Purpose

Rerun session 2's decoder report (32,057 characters) was refused by the
companion's `MAX_REPORT_CHARS = 32_000` with an HTTP 400. The client
discards any non-2xx, and the journal recorded only the status, not the
reason (`evidence/C3_L3A_R2_SESSION2_2026-09-24.md`). A 24-transition rerun
session is expected to exceed 32,000 every time, so sessions 3 and 4 would
lose their reports too. Task: `handoffs/C3-L3A-R2B_TASK.md`, authorized by
the user 2026-09-24 ("Go"). Record:
`evidence/C3_L3A_R2B_REPORT_CAP_2026-09-24.md`.

**Companion only: one constant and one log line.** No client (the APK
stays `f31b1c18…8ae7`), profile, encoder, route-shape or environment
change, and no session was run.

## Expected predecessor

`05aac43`. Both companion files match `HEAD` before the patch.

## Changed scope

| file | SHA-256 before | SHA-256 after |
| --- | --- | --- |
| `companion/games/decoder_session_log.py` | `b14fd191fad326785f4c3d600be5e674c4668fc4857a5631125624ccfc8cd74c` | `d9070e68fd96543bf9f2c18ae7a491ccda3944b14db44851c121511cf59b2a98` |
| `companion/privyhub_service.py` | `ae8114804e9f944921599c534bce456940143ad1d67cb5250369372968e4d678` | `a78abf7a460c689ef40f782e92740be9f9e44bd502ada5d1ab29cc41a3a06640` |
| `companion/plugins/games.py` (read, unchanged) | `60184e35…d73d` | `60184e35…d73d` |

The hashes are also in `evidence/c3_l3a_r2b_2026-09-24/{pre,post}_patch_sha256.txt`,
and the diff is in `companion_patch.diff`.

- `decoder_session_log.py`: `MAX_REPORT_CHARS` changes from 32_000 to
  **48_000**. The comment above it records the transport's own ceiling:
  the report travels URL-encoded in the request target at ~1.58 encoded
  characters per decoded one, and `http.server` refuses a request line over
  65,536 bytes, so the ceiling is ~41.4K decoded characters. The comment
  also names the client body-POST as the change that would lift that
  ceiling.
- `privyhub_service.py`, `do_POST`, the plugin `except ValueError` branch
  that produces the 400: for `action == "decoder-session-log"` only, it
  prints one line, `WARNING decoder-session-log rejected (400): <reason>;
  report_chars=<n>`, with no report content. `parse_qs` is added to the
  `urllib.parse` import. The response is unchanged: still 400 with the
  same JSON body.

## Validation

- `py_compile` passes on both files, and `git diff --check` is clean.
- `cap_check.py` calls `write_decoder_session_log` directly into a scratch
  project root:
  - the rebuilt 32,057-character report is accepted and round-trips;
  - 47,000 and 48,000 characters are accepted;
  - 48,001 and 49,000 are refused with "Decoder session report is too
    large";
  - nothing is written under the repository's `logs/games/decoder_sessions/`.
- The companion was restarted through `systemctl --user` at
  18:00:52Z. MainPID 352575 owns 8765, there is no `PRIVYHUB` variable in
  its environment, and `native-stream-status` shows
  `native_game_720p60_reference` with `any_override: false`, cap 90,000,
  cushion 12/17 and redundancy 2/4.
- One POST from localhost (49,000 `x`, not JSON, over the cap: it cannot be
  stored) returned 400, and the journal shows the warning line. Nothing was
  written.

## Not changed / follow-ups

- **The client body-POST** (the report in the request body, not the query
  string) is the real fix for the ~41.4K transport ceiling. It is a client
  change and is registered in `docs/KNOWN_ISSUES.md`.
- **Past the ceiling nothing is logged cleanly.** `http.server`'s 414 path
  calls `log_message` before the request is parsed, and the companion's
  override reads `self.path`, which does not exist yet. The result is an
  `AttributeError` traceback, no 414 is sent, and the client sees an empty
  response. This was checked on a throwaway server of the same shape, not
  on the companion (`request_line_limit_check.{py,txt}`). Recorded, not
  fixed (outside this task's scope).
- Decoder session filenames are millisecond-stamped, so two reports in one
  millisecond would share a name (seen only in the scratch test).
