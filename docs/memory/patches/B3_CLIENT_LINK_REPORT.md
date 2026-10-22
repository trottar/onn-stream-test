---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3 (on top of B1 / B2's uncommitted edits)
---

# B3 — the client's Wi-Fi link quality in its reports (`debug.privyhub.link_report=1` / `PRIVYHUB_LINK_REPORT=1`)

**Result: BUILT; APK `e4d02354…7903` built offline and pinned, NOT INSTALLED; NOT ADOPTED.** Session B, 2026-10-22
(`handoffs/QUEUE_2026-10-22B.md` B3). Record: `evidence/B3_CLIENT_LINK_REPORT_2026-10-22.md`. Nothing committed.

- **The client:** RSSI, tx / rx link speed, frequency and Wi-Fi standard from `WifiManager` (`ACCESS_WIFI_STATE`,
  already declared, no prompt). They are read at most once a second on the two existing 2-s report threads, and
  appear as heartbeat keys `link_*` and a client-health `link` object. Absent = no read, no key.
- **The host:** `client_feedback.py` normalizes the `link` object (tolerant). The ladder's telemetry gains `link.*`
  (with band), and the heartbeat log records `link_*`. The ladder reads nothing new. Absent = the parsers as today.
- **Files** (`evidence/b3_2026-10-22/b3.diff`):
  - `PrivyHub/…/streaming/LinkReport.kt` (new), `NativeStreamActivity.kt` (+11 / −1), `LinkReportTest.kt` (new);
  - `companion/diagnostics/client_feedback.py` (+23), `stream_telemetry.py` (+18),
    `games/native_stream_heartbeat.py` (+18), `plugins/games.py` (+11);
  - `tests/link_report/test_link_report.py` (new).

  After-hashes in `after_sha256.txt`.
- **Validation:** APK unit tests 78 / 78; link_report 9 OK; all host suites green but C3-F1's pre-existing error.
  Flag absent: the host functions' AST identical to the predecessors'.
- **Rollback (written, not applied):** copy the predecessors back from `evidence/b3_2026-10-22/predecessors/` and
  remove the three new files. Nothing is installed, so the onn needs nothing.
