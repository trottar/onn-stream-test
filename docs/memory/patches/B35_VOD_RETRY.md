---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8
---

# B35 — the movie player retries; the hub logs every range request

**Result: BUILT.**
- **Tests:** JVM `VodRetryTest` 8 green (169 / 169 in all); host `tests/vod_log` 9 green ×3; every `tests/` suite in
  the copy; 4 mutations caught.
- **Proof:** absent = today PROVEN for both flags.
- **Not done:** no live run.
- **Record:** `evidence/B35_VOD_RETRY_2026-10-31.md`. **Diff:** `evidence/b35_2026-10-31/b35.diff`. Nothing
  committed.

**Client, `debug.privyhub.vod_retry=1`.** On a load or IO error during VOD playback (Media3 1003 / 2000 / 2001 / 2002
/ 2004; not live):
- reconnect, seek to the first error's position and resume;
- backoff 1, 2, 4, 8, 15 s then 15 s each, bound 150 s, with a "reconnecting…" mark;
- past the bound, today's "Playback error…" plus a new Retry dialog;
- rows `vod_error` / `vod_retry` / `vod_resumed` / `vod_gave_up` to `POST /diagnostics/vod-client` (an opaque media
  id; no title, path or URL).
- New `vod/VodRetry.kt` and `vod/VodRetryAndroid.kt`; `MainActivity.kt` +40 lines, every one a null-safe `vodRetry?.`
  hunk.

**Host, `PRIVYHUB_VOD_LOG=1`.**
- `companion/vod_log.py` (new) writes:
  - `logs/vod_range.jsonl`: one row per range request — at / end UTC, an opaque id, Range, status, length, bytes
    written, duration, and `closed` (complete / short / client_reset / broken_pipe / error / no_body);
  - `logs/vod_client.jsonl`: the client's rows.
- `range_server.py`: one guarded block after the class (the class is untouched).
- `privyhub_service.py`: one guarded import and one guarded `do_POST` branch (the global looked up, so the G3 / G5
  handler replays stay green).

**Apply:**
- `git apply docs/memory/evidence/b35_2026-10-31/b35.diff` from the repo root.
- The client needs the APK with B35 and `adb shell setprop debug.privyhub.vod_retry 1`.
- The host needs `PRIVYHUB_VOD_LOG=1` in the companion's environment and a restart, both at home.

**Rollback:**
- the property empty (`adb shell setprop debug.privyhub.vod_retry ""`) and no host line: today;
- or `git apply -R` the diff.
