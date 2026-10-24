---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d
---

# B17 — the guard's audio order and the fast flush, behind `debug.privyhub.restart_guard=1` (+ the request-gated `guard_end`)

**Result: SETTLED + BUILT; JVM 5 new (130 / 130), host 2 (`tests/guard_end`); absent proven (host AST, client lines);
NOT ADOPTED; no live run.** Record: `evidence/B17_GUARD_AUDIO_ORDER_2026-10-24.md`. Nothing committed.

- **Settled:**
  - CL-B11's 221 underruns: the new instance's receiver started on the host's old audio, then starved when the stop
    tore it down, until B11's rebuild after the start.
  - The 3.4 s: sequential posts, and the host's stop waiting on the encoder's teardown (~2.3 s). The host's start runs
    the same teardown itself.
- **Built:**
  - the pending taken before the audio, so the receiver stays unstarted until the start is answered;
  - `native-stream-start?…&guard_end=1` first, with the host running the stop's bookkeeping at the start's entry. No
    separate stop;
  - the old report after the start;
  - `restart_cause.create_to_start_ms` / `flush` / `host_ended_session`.
- **Files:** `RestartGuard.kt`, `NativeStreamActivity.kt` (+9, 3 changed), `RestartGuardAudioOrderTest.kt` (new),
  `companion/plugins/games.py` (+7), `tests/guard_end/` (new).
- **Rollback:** clear the property, or revert the files above.
