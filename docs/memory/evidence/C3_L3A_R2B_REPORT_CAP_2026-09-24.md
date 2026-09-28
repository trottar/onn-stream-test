---
memory_schema: 1
as_of: 2026-09-24
status: C3-L3A-R2B DONE — companion decoder-report cap raised 32,000 → 48,000 with a WARNING line on rejection (validated off-session; RUNTIME VALIDATION PENDING until session 3's report is stored); companion restarted through systemd 18:00:52Z, adopted profile confirmed; rerun session 2 finalized against the report rebuilt from the journal (24 = 24, spread 0.441 s) and its decoder-axis check appended to the R2 record; transport ceiling ~41.4K decoded chars remains (client body-POST follow-up open); C3.L4 stays BLOCKED
---

# C3-L3A-R2B: store the report; finish session 2

Task: `handoffs/C3-L3A-R2B_TASK.md` (authorized by the user 2026-09-24,
"Go"). Patch: `patches/C3-L3A-R2B_DECODER_REPORT_CAP.md`. Evidence:
`c3_l3a_r2b_2026-09-24/`, with the SHA-256 of every file in
`c3_l3a_r2b_2026-09-24/sha256_manifest.txt`. Predecessor:
`C3_L3A_R2_SESSION2_2026-09-24.md`, to which the decoder-axis section was
appended.

**Scope.** The companion change is one constant
(`companion/games/decoder_session_log.py`) and one log line where the 400
is produced (`companion/privyhub_service.py`). There was no client change
(the APK stays `f31b1c18…8ae7`) and no profile, encoder, route-shape or
environment change. No stream session ran.

## 1. The cap

**The change.** `MAX_REPORT_CHARS` is now **48,000**, up from 32,000. The
comment above the constant gives the arithmetic:

- The client sends the report URL-encoded in the request target. The
  journal's rejected request carried 50,717 encoded characters for 32,057
  decoded, a ratio of 1.582.
- `http.server` answers 414 to a request line over 65,536 bytes before any
  handler runs.
- So the transport's own ceiling is **~41.4K decoded characters**
  (`cap_check.txt`: 65,536 − 58 fixed bytes, ÷ 1.582, ≈ 41,385). The ratio
  depends on content.
- 48,000 sits above that ceiling, so the check never refuses what the
  transport can carry.
- A 24-change session is ~32K, and each further SSRC change adds ~270-310,
  leaving ~9K of room.

**The warning line.** In `do_POST`'s plugin `except ValueError`, for
`decoder-session-log` only, the companion now prints one line:
`WARNING decoder-session-log rejected (400): <reason>; report_chars=<n>`.
It carries no report content. The response is unchanged.

**Validation.**

- `py_compile` passes and `git diff --check` is clean.
- `cap_check.py` calls `write_decoder_session_log` directly. Its
  `project_root` is a parameter, so everything went to a scratch root:

| case | chars | result |
| --- | ---: | --- |
| (a) session 2's rebuilt report | 32,057 | **accepted**, round-trips byte-exact |
| (b) synthetic JSON object | 47,000 | **accepted** |
| at the cap | 48,000 | accepted |
| cap + 1 | 48,001 | refused: "Decoder session report is too large" |
| (c) synthetic JSON object | 49,000 | **refused**: "Decoder session report is too large" |

Three files were written, all in the scratch root, which was deleted
afterwards. The repository's `logs/games/decoder_sessions/` was not
touched; its newest file is still `native_decoder_20260924_161558_087.json`.
The first pass of the scratch run exposed something unrelated: two writes
in the same millisecond share a filename, and the second replaces the
first. The final `cap_check.py` spaces its cases apart. This is noted in
the patch record and does not happen in practice, where reports arrive
minutes apart.

**Restart** (`systemctl --user restart privyhub-companion`, **18:00:52Z**
= 14:00:52 local). Before it, no game or stream was active.

- The new **MainPID 352575 owns 8765**, and its environment has no
  `PRIVYHUB_*` variable.
- The journal shows a clean stop and start (`Listening on …:8765`,
  metadata reconciliation `SKIPPED_CURRENT`) with no error
  (`companion_journal_restart_and_warning_1800Z_redacted.txt`).
- `native-stream-status` (`native_stream_status_after_restart.json`):
  `native_game_720p60_reference`, `encoder_overrides.any_override:
  false`, `max_frame_size_bytes` 90,000 (source `profile`), audio queue
  target / capacity 12 / 17, redundancy 2 / 4, 7000 kbps, inactive.
  **The adopted profile stays adopted.**

**Live check of the warning line.** One POST from localhost, beyond what
the task asked: 49,000 `x`, not JSON and over the cap, so it could not be
stored under any outcome. It got **400** `"Decoder session report is too
large"`, and the journal shows
`WARNING decoder-session-log rejected (400): Decoder session report is too
large; report_chars=49000`. Nothing was written.

**Past the transport ceiling** (`request_line_limit_check.{py,txt}`). This
was run on a throwaway `http.server` with a `log_message` of the companion's
shape, not on the companion. On an over-long request line, `http.server`
calls `send_error(414)`, which logs before `self.path` exists. The
companion's override reads `self.path`, so it raises **`AttributeError`**.
The traceback goes to the journal, **no 414 is sent**, and the client sees
an empty response and swallows it. A report over ~41.4K would therefore be
lost with a traceback, not a clean line. This is recorded and not fixed:
`log_message` is outside this task's scope. It is registered with the
body-POST follow-up.

## 2. Session 2's decoder axis

- **Wrapped**: `c3_l3a_r2_2026-09-24/native_decoder_20260924_171642_rebuilt.json`
  holds `schema` `privyhub_native_decoder_session_log_v1`,
  `received_at_utc` 2026-09-24T17:16:42.799Z, the report (round-trips
  byte-exact), an empty `host` block (never captured) and a
  `rebuilt_from_journal` note. It is in the evidence directory, not in
  `logs/games/decoder_sessions/`. The R2 manifest was regenerated for it;
  every earlier file there re-verified OK.
- **Finalized**: `--finalize --state
  logs/streaming/c3_l3a_runs/states/20260924_130016_state.json --decoder
  <that file>` exited 0 (`c3_l3a_finalize_r2b_20260924_140204.log`).
  `c3_l3a_runs/20260924_130016.{json,txt}` and the latest-run report were
  regenerated (copies in `after_decoder/`). Both state files and session
  1's run files are SHA-256 unchanged (`files_sha256_{before,after}_finalize.txt`).
- **Result**: expected **24 = 24** SSRC changes (20 + 3 parks + 1 restore);
  20 pairs, offset 21.041 s, **spread 0.441 s**, max |residual| 0.245 s,
  alignment OK.
- **Transition cost**: gap 172-239 ms, median 185, `codec_ms` 6-12, first
  IDR 1-32 ms, `jump_packets` 0 on all 24.
- **Marks**: 10 of the 11 transition-window marks sit 1.68-2.59 s behind a
  measured 176-239 ms restart gap. The 15 unattributed marks had no gap
  over 183 ms before them. Smaller events there were evicted: the buffer
  saturated, and the client's off-transition ring holds only the last 64
  events, from probe 941 s. `mark_check.py` handles the two rings and the
  never-evicted top-gap list explicitly.
- **Close-out rows**: 40.1 spikes/min, 59.74 fps, 1.26 stale/min, 1.32
  loss/min, max gap 239 ms (a transition).

The full section is in `C3_L3A_R2_SESSION2_2026-09-24.md` §"Decoder axis —
DONE 2026-09-24 (R2B)".

- **`--aggregate`** still pools **2** runs. `c3_l3a_aggregate.txt` differs
  from R2's copy only in `Generated:`, and `c3_l3a_aggregate.json` is
  unchanged. The detection table does not change.

## What remains

- **The client body-POST** (report in the request body): lifts the ~41.4K
  transport ceiling. A client change, open in `docs/KNOWN_ISSUES.md`.
  Also open there: the client swallowing a non-2xx on the report post, and
  the `log_message` traceback past the ceiling.
- **Runtime validation of the cap: PENDING** until a real 24-change
  session's report is stored (session 3). Check that session's journal
  for its `Native decoder session log:` line and no WARNING.
- **A limit of the report, not of the cap**: with a saturated slow-event
  buffer, off-transition events before the recent ring's window are
  evicted. Every pre-registered 24-transition session will saturate. From
  session 3 on, unattributed marks will be checkable only against the
  top-gap bound unless the client's rings grow. That is a client question,
  recorded here and not acted on.
- Sessions 3-4 await the user. No verdict. **`C3.L4` stays BLOCKED.**

## Files (`c3_l3a_r2b_2026-09-24/`)

- `pre_patch_sha256.txt`, `post_patch_sha256.txt` and
  `companion_patch.diff`
- `cap_check.py`, `cap_check.txt`, `request_line_limit_check.py` and
  `request_line_limit_check.txt`
- `companion_journal_restart_and_warning_1800Z_redacted.txt` and
  `native_stream_status_after_restart.json`
- `c3_l3a_finalize_r2b_20260924_140204.log`,
  `after_decoder/20260924_130016.{json,txt}`, `c3_l3a_aggregate.{txt,json}`
  and `c3_l3a_aggregate_stdout.log`
- `mark_check.py` and `mark_check.txt`
- `files_sha256_{before,after}_finalize.txt` and `sha256_manifest.txt`

Redacted with `h2_prep_redact.py`, `--check` 0 residual matches on the
journal, status and check outputs. No network address, adb endpoint, MAC
or device identifier appears in any file. The loopback address in the
throwaway-server traceback is written `<loopback>`.
