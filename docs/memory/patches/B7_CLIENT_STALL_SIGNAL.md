---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5 / B6 uncommitted)
---

# B7 — the client's stall signal behind `debug.privyhub.stall_signal` / `PRIVYHUB_STALL_SIGNAL`

**Result: BUILT; host 12 tests (fake client, real receive loop), client 6 JVM tests (91 / 91); APK (B5 + B7)
`cb0935c8…1080` pinned, NOT installed; NOT ADOPTED; no live run.** Record: `evidence/B7_CLIENT_STALL_SIGNAL_2026-10-22.md`.
Nothing committed.

- **Client:**
  - while the output is older than S (`1` = 150) or the recovery gate's black overlay stands, a 24-byte `PHS1` stall
    datagram goes out on the controller socket every 50 ms;
  - then one `stall_end` when gameplay is shown again.
- **Host** (`PRIVYHUB_STALL_SIGNAL=1|<ms>`, the act threshold):
  - a stall pauses through recovery v2 (`client_stall`), with B4's onset = the client's last displayed frame;
  - a stall during a hold takes it over (B2's handover); the hold's release waits ≤ 60 ms for a stall;
  - `stall_end` (or 300 ms quiet) rewinds, then resumes;
  - a later client ready is that recovery's end.
- **The data:** clean sessions have ≥ 14 client output gaps ≥ 150 ms per 11.5 min. BENCH-R2 runs host thresholds 150
  and 400.
- **Files:**
  - `companion/stall_signal.py` (new), `native_session_io.py` +11, `games/link_drop_recovery.py` +10,
    `hold_rewind.py` +5, `plugins/games.py` +9, `tests/stall_signal/` (new);
  - `PrivyHub/.../streaming/StallSignal.kt` (new), `NativeStreamActivity.kt` +21, `NativeControllerSender.kt` +9,
    `AvcLowLatencyDecoder.kt` +3, `StallSignalTest.kt` (new).
- **Validation performed:**
  - the host and JVM tests, B2 / B4 / B6 and the regression set;
  - the host AST proof (4 identical) and the client textual proof (0 lines changed);
  - `assembleDebug` offline with the tree untouched;
  - `git diff --check` clean;
  - the redact check.
