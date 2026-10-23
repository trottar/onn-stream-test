---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11-B13 uncommitted)
---

# B14 — the "any house" link notice behind `debug.privyhub.link_notice=1`

**Result: BUILT; client 7 JVM tests (114 / 114), host 4 (B3's 9 unchanged); APK (B5 + B7 + B10 + B11 + B13 + B14)
`da09e154…6cf` pinned, NOT installed; NOT ADOPTED; no live run.** Record: `evidence/B14_LINK_NOTICE_2026-10-23.md`.
Nothing committed.

- **Client:** on 2.4 GHz at once, or RSSI ≤ −72 dBm / tx ≤ 54 Mbps held 10 s, a small notice on the stream ("Wi-Fi:
  2.4 GHz — Use your router's 5 GHz Wi-Fi for this box.") and a line on the diagnostics page; cleared after 30 s good;
  once a session unless the band changes; no network call, no stream change; `link_notice=<bits>` in the heartbeat.
- **Host** (`PRIVYHUB_LINK_REPORT=1`): the heartbeat field recorded; `link_notice_shown` / `link_notice_cleared` in the
  recovery log.
- **Files:** `LinkNotice.kt` (new), `NativeStreamActivity.kt` +55, `DiagnosticsActivity.kt` +15, `LinkNoticeTest.kt`
  (new); `companion/link_notice.py` (new), `plugins/games.py` +16, `games/native_stream_heartbeat.py` +4,
  `tests/link_notice/` (new).
- **Validation performed:** JVM and host tests, the regression set from the /tmp copy, the client and host proofs, the
  APK build (tree untouched), the signer compared, `git diff --check`, the redact check.
- **Rollback:** clear the property; or revert the files and remove the new ones.
