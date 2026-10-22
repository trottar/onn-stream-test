---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 0f4b551 (+ B8 / B9 uncommitted)
---

# B10 — the client's loss guard behind `debug.privyhub.loss_guard` / `PRIVYHUB_LOSS_GUARD`

**Result: BUILT; client 8 JVM tests (99 / 99, the real receiver on loopback with a fake decoder); host 10 tests (a fake
encoder control through the real receive loop); APK (B5 + B7 + B10) `bf5114a2…cf73` pinned, NOT installed; NOT
ADOPTED; no live run.** Record: `evidence/B10_CLIENT_LOSS_GUARD_2026-10-22.md`. Nothing committed.

- **Settled:** a dropped access unit today is skipped and the next P-frames are decoded from a lost reference until
  the next IDR (every 15 frames); nothing counts them. The host cannot force an IDR on demand: the ffmpeg encoder's
  GOP is fixed at launch and the only path is a restart (a 287-318-ms gap, longer than the ≤ 250-ms wait).
- **Client** `1`: no non-IDR frame queued after a drop until the next IDR (the last good frame stays), capped at
  600 ms; one 24-byte `PHK1` `keyframe_request` per episode on the controller socket. `count`: the counter only.
  `frames_after_dropped_reference` (+ episodes, held, timeouts, max wait, requests) in the report and the heartbeat.
- **Host** `1`: requests counted, ≤ 1 per 500 ms acted on through `control.force_idr()`; today's `NoRuntimeIdr`
  forces nothing and says why (a per-minute `keyframe_requests` row); a forced IDR would be `keyframe_forced`. The
  heartbeat's loss-guard fields recorded.
- **Files:** `companion/keyframe_request.py` (new), `native_session_io.py` +10, `plugins/games.py` +16,
  `games/native_stream_heartbeat.py` +15, `tests/keyframe_request/` (new); `LossGuard.kt` (new), `RtpH264Receiver.kt`
  +12, `NativeStreamActivity.kt` +20, `NativeControllerSender.kt` +9, `LossGuardTest.kt` (new).
- **Validation performed:** the host and JVM tests, the regression set from the /tmp copy, the host AST proof and the
  client textual proof, `assembleDebug` offline with the tree untouched, the signer compared, `git diff --check`, the
  redact check.
- **Rollback:** clear the property / unset the flag (nothing is constructed); reinstall `cb0935c8…`; or revert the
  files and remove the new ones.
