---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: efa4240
---

# B15 — the restart guard on every path, behind the same `debug.privyhub.restart_guard=1`

**Result: SETTLED + BUILT; 8 JVM tests (122 / 122 with B11's 8 unchanged); client textual proof (14 added lines, 0
changed); NOT ADOPTED; no live run.** Record: `evidence/B15_RESTART_GUARD_ALL_PATHS_2026-10-24.md`. Nothing committed.

- **Settled:** CL-B10 cell 1's start ran in a **new activity instance** whose guard was empty: B11 kept the pending in
  the activity object only. The old instance never posted its report or a stop, not even later, so it ended without
  `onDestroy`: its process died while the launcher was in front, and Android re-created the stream activity in a new
  process on the return. The property was read (`1`); the guard held nothing.
- **Built:** the pending is also written at the surface's loss to a private file (`noBackupFilesDir/
  restart_guard_pending.properties`), so every start takes it: `restart_cause.trigger` = `surface` / `recreate` /
  `process`; B11's flush (report, stop, start) and audio rebuild unchanged. A recreation (`isChangingConfigurations`)
  hands the session to the next start instead of racing its stop; a pending another instance already flushed is not
  posted twice.
- **Files:** `RestartGuard.kt` (+B15), `NativeStreamActivity.kt` +14, `RestartGuardAllPathsTest.kt` (new).
- **Validation performed:** the JVM suite offline in the /tmp copy, the textual proof, the redact check.
- **Rollback:** clear the property; or revert the 14 lines and `RestartGuard.kt` to B11's, and remove the new test.
