# B11 — the client's self-restart after a two-way drop: design, written before any B11 code

Baseline HEAD 3eb900c (the client = the CONFIRMED APK `bf5114a2…`'s sources). Queue: `handoffs/QUEUE_2026-10-23E.md`
§B11. Data: UX-R4 §1.3 (event 2, 05:03:38-05:03:54Z).

## 0. Settled from the code, with UX-R4's timeline beside it

**What starts a new stream by itself.** In `NativeStreamActivity.kt` a session starts only in `startSession`, called only
from `surfaceCreated`. The client's own link recovery (`maybeEnterLinkRecovery` → `enterLinkRecovery`, output or RTP
silence ≥ 1,000 ms) **tears nothing down and never restarts**: it re-enters the "Reconnecting" gate with the decoder,
receiver, audio and controller sender all running, posts one `native-stream-desync`, and waits for the host. So a new
client session (heartbeat sequence 1, a new client clock — UX-R4 05:03:45) means **the activity's surface was destroyed
and created again** (the activity stopped and restarted; a destroy would have gone through `onDestroy` → `stopSession`,
which posts the report and `native-stream-stop`).
- `surfaceDestroyed`: `cacheSessionReport()` (the report built and **kept in memory, not posted**), then
  `stopLocalPipeline()` — **the controller sender, the audio receiver, the RTP receiver and the decoder stopped** — and
  `sessionStarted = false`. **No `native-stream-stop`, no report POST.**
- `surfaceCreated` → `startSession`: `cachedSessionReport = null` (**the old session's report is discarded**), new
  pipeline objects, then `native-stream-start` from the session thread.
- **So, in UX-R4's event 2:** the client's last heartbeat at 05:03:39 (the interval's 23 fps, output age 166 ms: the
  pipeline torn down mid-interval), then 4.9 s with **no controller packets** — while the surface was gone the client's
  own controller sender was stopped, so this "uplink silence" is at least partly the client's own; the code cannot say
  what stopped the activity (a window in front, the launcher, a lifecycle event the logs do not carry). Then a new
  session at 05:03:44.73 and `native-stream-start` at 05:03:46.67, no stop, no report. Exactly the code's path.

**Why the new session's audio underran ~170 / s.** The host's `native-stream-start` runs `_stop_locked()` then starts
everything again: its audio sender begins at **sequence 0** (`native_session_io`, `sequence = 0` per sender start).
On a cold start the client's audio receiver is created before the host's audio exists, so its first packet is
sequence 0. On a self-restart the host's **old** audio is still flowing when the new receiver starts (05:03:44.73), so
the receiver (the Opus path, adopted: `OpusReorder`) locks `next` onto the old sequence N. When the host restarts at
05:03:46.67 every new frame reads `ahead(0, N) > 32767` → **`Kind.LATE`, dropped**, and `next` never moves back; the
playback queue starves (concealment every slot, AudioTrack underruns ~200 / s at most) **until the new sequence catches
up with N** — N ≈ the old session's age / 10 ms (session 4 was 58 s old: ~58 s). The user's load (stop + start) ended
it. D-BASE-P2a's start-up hold (wait for the first real PCM) was armed, but met at once by the old stream; the host's
cushion arrived 2 s later, after the first PCM (`cushion_applied_before_first_pcm` false). The PCM path has the same
rule (`gap > 32767` → late).

## 1. The design, behind `debug.privyhub.restart_guard=1` (absent = today: no object, every hook a no-op)

New `RestartGuard.kt` (pure, JVM-tested); hooks are added lines only in `NativeStreamActivity.kt`.
1. **The old session ends properly first.** At `surfaceDestroyed` (a session was started) the guard keeps the cached
   report and the cause. At the next `startSession`, in the session thread **before** `native-stream-start`: the old
   report POSTed (`DecoderReportUpload`, as `stopSession`), then `native-stream-stop` — so the host's recovery sees
   `session_ended` and the record keeps the report — then the start. If the activity ends instead (`onDestroy` →
   `stopSession`), today's stop path posts the cached report and the stop; the guard's pending is cleared.
2. **The audio rebuilt with the start-up hold re-armed.** On a self-restart the audio receiver created at the top of
   `startSession` is stopped and replaced **after** the host's start response (the host's audio then restarts at
   sequence 0): a fresh `NativeAudioReceiver` (fresh reorder / sequence state, D-BASE-P2a's hold armed for the host's
   new stream), the response's cushion and redundancy applied **before** it starts (so the whole session runs on the
   host's cushion), then started.
3. **`restart_cause`** in the new session's report: `away_ms` (surface lost → restart), `last_frame_age_ms` and
   `rtp_silence_ms` at the loss, `recovery_active` at the loss, `paused_before_loss_ms` (the last `onPause` → the loss,
   −1 if none), `old_report_posted`, `stop_posted`. One `Log.i` line too.

## 2. Tests (JVM)

- `RestartGuardTest`: the flag; a simulated 5-s two-way drop with the real `RtpH264Receiver` on loopback and a fake
  decoder (session A's receiver torn down at the loss, B's built at the restart on the same port, frames to B) and a
  fake host transport: **with the guard → report(A), stop, start (one each), in that order; the cause's `away_ms` ≈
  5,000**; **absent → start only (today: no stop, report lost)**; `stopSession` after a loss → the guard's pending
  cleared (one stop, not two).
- **The audio:** the receiver's sequence state (the real `OpusReorder`) locked on the old stream, then the host's
  restart at 0: **today → every frame LATE (the fake sink gets nothing: the underrun storm)**; **rebuilt → every frame
  in order to the fake sink.**
- The suite unchanged otherwise; the client textual proof (added lines only, allowed forms).
