---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11 / B12 uncommitted)
---

# B13 — `debug.privyhub.link_report` absent = ON in the client; the ninth adopted line prepared

**Result: BUILT (client) + PREPARED (host, `G-A3_LINK_REPORT_ADOPTION_PREPARED.md`, not applied); JVM 107 / 107 (B3's
two flag tests changed to the new meaning); APK `df185d25…5d63` pinned, NOT installed (superseded by B14's); NOT
ADOPTED.** Record: `evidence/B13_LINK_REPORT_DEFAULT_ON_2026-10-23.md`. Nothing committed.

- `LinkReportFlag.parse`: on unless `0`; a failed property read is on. Cost: one `getConnectionInfo()` a second at most,
  ≤ 5 keys per heartbeat; no permission change.
- **Files:** `LinkReport.kt` (2 lines + the comment), `LinkReportTest.kt` (the two flag tests).
- **Validation performed:** the JVM suite, the APK build (tree untouched), the signer compared, the G-A3 diff tested on
  a scratch copy and `git apply --check`ed, the redact check.
- **Rollback:** `setprop debug.privyhub.link_report 0` on the onn; or revert the two files.
