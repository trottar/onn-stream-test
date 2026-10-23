---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c
---

# B11 — the client's self-restart guard behind `debug.privyhub.restart_guard=1`

**Result: SETTLED + BUILT; 8 JVM tests (107 / 107); client textual proof (44 added lines, 0 changed); NOT ADOPTED; no
live run.** Record: `evidence/B11_CLIENT_RESTART_GUARD_2026-10-23.md`. Nothing committed.

- **Settled:** the client starts a new stream only from `surfaceCreated`. A lost surface caches the report (never
  posted) and stops the whole pipeline, including the controller sender; the next start discards the report and posts
  no stop. The host's start restarts its audio at sequence 0 while the new receiver had locked onto the old stream, so
  every frame read LATE until the sequences met (the underrun storm).
- **Built:** the next start first posts the old report and `native-stream-stop`; the audio receiver is rebuilt after
  the host's start response (fresh state, hold re-armed, the cushion applied before it starts); `restart_cause` in the
  new report.
- **Files:** `RestartGuard.kt` (new), `NativeStreamActivity.kt` +44, `RestartGuardTest.kt` (new).
- **Validation performed:** the JVM suite offline in the /tmp copy, the textual proof, the redact check.
- **Rollback:** clear the property; or revert the activity and remove the two new files.
