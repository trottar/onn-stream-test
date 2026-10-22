---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7
---

# B5 — the stream's Wi-Fi lock behind `debug.privyhub.wifi_lock=<low_latency|high_perf>`

**Result: SETTLED (no Wi-Fi lock, no wake lock during a stream today); BUILT, 85/85 JVM tests; APK `8a69a480…b767`
pinned, NOT installed; NOT ADOPTED.** Record: `evidence/B5_CLIENT_WIFI_LOCK_2026-10-22.md`. Nothing committed.

- **What it does:**
  - one non-reference-counted `WifiLock` per stream activity: `WIFI_MODE_FULL_LOW_LATENCY` (API ≥ 29) or
    `WIFI_MODE_FULL_HIGH_PERF`;
  - acquired at session start and on resume during a session;
  - released at the session's end (`stopLocalPipeline`) and on pause;
  - the report gains `wifi_lock_mode` / `wifi_lock_held`.
  - `WAKE_LOCK` is already declared.
- **Absent:** proven textually: 0 lines changed, all 25 added lines null-safe.
- **Files:** `PrivyHub/app/src/main/java/streaming/StreamWifiLock.kt` (new), `NativeStreamActivity.kt` (+25),
  `PrivyHub/app/src/test/java/streaming/StreamWifiLockTest.kt` (new).
- **Validation performed:**
  - the JVM suite (78 unchanged + 7) and `assembleDebug`, offline, in the copy;
  - the proof;
  - `git diff --check` clean;
  - the redact check.
- **Incident, disclosed:** the first build in the copy reused a configuration cache pointing at the tree and rebuilt
  the tree's gitignored build outputs. They were restored byte-equal (289 files), and 24 new intermediates are left.
  All later builds use `--no-configuration-cache`.
- **Next (A, BENCH-R2):** the idle-LAN silence count with the property empty / `low_latency` / `high_perf`.
