---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (the client = the CONFIRMED APK bf5114a2's sources; B11 uncommitted)
---

# B11 — the client's self-restart: it is a lost surface, not the link recovery; the old session now ends first, and the audio is rebuilt after the host restarts it

**Classification: SETTLED + BUILT** behind `debug.privyhub.restart_guard=1` (client only).
- 8 JVM tests, including the real `RtpH264Receiver` on loopback across the restart and the real `OpusReorder`; the
  suite is **107 / 107**.
- Property absent = the CONFIRMED client: only added lines (44), all in the allowed forms.
- The APK comes with B13 / B14 (this item is in it). NOT ADOPTED; no live run; nothing committed.

Design `b11_2026-10-23/design_written_before_code.md`, sha256 `9c9096b9…5a5477`, hashed **17:12:20Z, before any B11
code**.

## 0. Settled from the code, beside UX-R4 §1.3

**What starts a new stream by itself.**
- A session starts only in `startSession`, called only from `surfaceCreated`.
- **The client's own link recovery never restarts.** `enterLinkRecovery` (output or RTP silence ≥ 1,000 ms) re-enters
  the "Reconnecting" gate with the decoder, receiver, audio and controller sender all running. It posts one
  `native-stream-desync`.
- So a new client session (heartbeat sequence 1, a new client clock) means **the activity's surface was destroyed and
  created again**: the activity stopped and restarted.
  - A destroy would have gone through `onDestroy` → `stopSession`, which posts the report and the stop.
- **`surfaceDestroyed`:** the report is built and cached, **not posted**. Then `stopLocalPipeline()` stops **the
  controller sender**, the audio receiver, the RTP receiver and the decoder. **No `native-stream-stop`.**
- **`startSession`:** `cachedSessionReport = null` (**the old report is discarded**), then new objects and a new
  `native-stream-start`.
- **UX-R4's event 2 is that path:**
  - the last heartbeat at 05:03:39 (23 fps in the interval, output age 166 ms: the pipeline torn down mid-interval);
  - 4.9 s with no controller packets, then a new session at 05:03:44.73 and the start at 05:03:46.67;
  - no stop, no report.
- **A correction to the reading of event 2:** while the surface was gone, **the client's own controller sender was
  stopped**. So that 4.9-s "uplink silence" is at least partly the client's own, not necessarily the link.
- **What stopped the activity, the code cannot say.** It could be a window in front, the launcher, or a lifecycle event
  the logs do not carry. B11's `restart_cause` records the loss's timing (§1).

**Why the new session's audio underran ~170 / s.**
- **The host restarts its audio at sequence 0.** `native-stream-start` runs `_stop_locked()` and starts everything
  again; the audio sender begins at sequence 0.
- **On a cold start that is fine:** the client's receiver exists before the host's audio does, so its first packet is
  sequence 0.
- **On a self-restart it breaks:**
  - the host's **old** audio is still flowing when the new receiver starts;
  - the receiver (the adopted Opus path, `OpusReorder`) locks `next` onto the old sequence N;
  - after the host's restart, every new frame reads `ahead(0, N) > 32767` → **`Kind.LATE`, dropped**, and `next` never
    moves back;
  - the queue starves: concealment every slot, AudioTrack underruns;
  - **until the new sequence reaches N.** N ≈ the old session's age / 10 ms; session 4 was ~58 s old, so ~58 s.
- The user's load (a stop and a start) ended it.
- **The start-up hold (D-BASE-P2a) was armed but met at once** by the old stream. The host's cushion arrived 2 s later,
  after the first PCM. The PCM path has the same rule (`gap > 32767` → late).

## 1. Built (`b11.diff`): `RestartGuard.kt` new (114 lines); `NativeStreamActivity.kt` +44, added lines only

1. **The old session ends first.**
   - At the surface's loss (a session was started), the guard keeps the cached report and the cause.
   - At the next start, in the session thread **before** `native-stream-start`: the old report is POSTed (as
     `stopSession` does), then `native-stream-stop`, then the start. So the host's recovery sees `session_ended` and
     the record keeps the report.
   - If the activity ends instead, today's `stopSession` posts the cached report and the stop, and the guard's pending
     is cleared: one stop, not two.
2. **The audio is rebuilt with its start-up hold re-armed.**
   - On a self-restart, the receiver created at the top of `startSession` is stopped and replaced after the host's
     start response, when the host's audio restarts at 0.
   - The new receiver has fresh reorder / sequence state, and D-BASE-P2a's hold waits for the host's new stream.
   - The response's cushion and redundancy are applied **before** it starts.
3. **`restart_cause`** in the new session's report: `away_ms`, `last_frame_age_ms`, `rtp_silence_ms`,
   `recovery_active`, `paused_before_loss_ms`, `old_report_posted`, `stop_posted`, `restarts`.
   - *Deviation from the design:* the design named one `Log.i` line. The activity imports no `Log`, so the cause is in
     the report only.

## 2. Tests (`tests_jvm.txt`, `tests_restart_guard.xml`)

**`RestartGuardTest`, 8:**
- the flag;
- **a simulated 5-s two-way drop:** session A's real receiver on loopback, torn down at the loss; session B's built
  on the same port at the restart; a fake decoder each; a fake host:
  - **with the guard:** `start`, `report(A)`, `stop`, `start`, in that order; `away_ms` 5,000; frames 5 / 5;
  - **absent:** `start`, `start` (today: no stop, the report lost);
- an ended activity → no second stop; failed posts recorded, never thrown; a normal start clears the cause; the pause
  before the loss measured;
- **the audio, the real `OpusReorder`:**
  - locked on the old stream (5,800-5,899), then the host's restart (0-299): **0 frames to the fake sink**. That is
    the storm;
  - **rebuilt:** all 300 in order.
- The suite is **107 / 107** (99 unchanged + 8), offline in `/tmp/b_q23e` with `--no-configuration-cache`, only
  `privyhub-companion` and `privyhub-link-n1` active.

**Proof** `proof_flag_absent_client.md`: **PROVEN**, 0 removed / 44 added. Kotlin's `?.` does not evaluate the
arguments of a call on null, so the new calls cost nothing without the property.

## 3. For CL-B10 (A)

- `setprop debug.privyhub.restart_guard 1`.
- **A forced self-restart:** press Home on the onn for ~5 s mid-game, then return. Expected:
  - the host's log shows the old report, `native-stream-stop` (`session_ended`), then `native-stream-start`;
  - the new report's `restart_cause` (`away_ms` ≈ 5,000);
  - **the new session's audio underruns ≈ the other sessions' (0-13 per interval), not ~170 / s.**
- **Absent:** the same press reproduces UX-R4's event 2 (no stop, the report lost, the storm). Run it only if the user
  wants the before.

## 4. Files

- **`b11_2026-10-23/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b11.diff`, `proof_flag_absent_client.py` / `.md`, `tests_jvm.txt`, `tests_restart_guard.xml`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `PrivyHub/app/src/main/java/streaming/RestartGuard.kt` (new), `NativeStreamActivity.kt`,
    `PrivyHub/app/src/test/java/streaming/RestartGuardTest.kt` (new);
  - `docs/memory/patches/B11_CLIENT_RESTART_GUARD.md`, `logs/b11_git_status.txt`.
- **Disclosed:** a stray `rm -rf /dev/null` ran once in a setup command line (as the user, no sudo). It failed on
  permission and changed nothing; `/dev/null` was checked intact.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of `privyhub-link-n1`
  touched; nothing fetched, deleted, adopted or committed.
