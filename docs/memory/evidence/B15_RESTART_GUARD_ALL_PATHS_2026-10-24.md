---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: efa4240 (the client = `da09e154…`'s sources; B15 uncommitted)
---

# B15 — why the guard did not run on the Home press: a new activity instance, an empty guard; the guard now keeps its pending beyond the instance and the process

**Classification: SETTLED + BUILT** behind the same `debug.privyhub.restart_guard=1` (client only).
- 8 JVM tests on B10's / B11's harness (the real `RtpH264Receiver` on loopback, a fake decoder, the real
  `OpusReorder`, a temp file as the store). The suite is **122 / 122** (114 unchanged, B11's 8 among them, + 8).
- Property absent = today: only added lines in the activity (14), all in the allowed forms.
- In the APK **`e2db0aa0…6b33`** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16; `b16_2026-10-24/apk_sha256.txt`),
  built and pinned, **NOT installed**. NOT ADOPTED; no live run; nothing committed.

Design `b15_2026-10-24/design_written_before_code.md`, sha256 `b06bcddd…4eac459`, hashed **06:09:16Z, before any B15
code**.

## 0. Settled from the code and cell 1's logs

**The rows (cell 1, the host's own logs and the client's reports):**

| UTC | row |
| --- | --- |
| 03:34:54 / 03:35:03 | `native-stream-start`, `native-stream-ready` (the first session) |
| ~03:38:37.6 | the Home press (the controller goes silent: the client's surface lost, its sender stopped) |
| 03:38:37.6 → 03:38:43.6 | **no request of any kind** from the client: no report, no `native-stream-stop` |
| ~03:38:43.5 | a new client session (`startSession`; its heartbeat sequence 1 at 03:38:44, `elapsed_ms` 473) |
| 03:38:43.687 | `native-stream-start` arrives (`client_stream_restart`; the response 03:38:45) |
| 03:39:12 | the back-out: **one** report (the new session's, 28.4 s) and **one** `native-stream-stop` |
| never | the first session's report |

- **The new session's report:** `stall_signal_ms` and `link_notice_*` present, so that code read
  `debug.privyhub.stall_signal` and `link_notice` by the same `SystemProperties` reflection `RestartGuardFlag` uses.
  **No `restart_cause`.**
- **Its audio:** the first PCM at 133 ms, ~1.4 s before the host's start response, then 2,418 underruns in 28 s. That
  is B11's mechanism: the receiver locked onto the host's old stream, so every frame of the restarted one read `LATE`.

**The path, from the code:**
- `native-stream-start` is posted from one place: `startSession`'s session thread.
- `startSession` is called from one place: `surfaceCreated`.
- **B11's guard sits at that choke point** (`restartGuard?.takePending()` before the start).
- **In the same activity instance** (the surface lost, then created again), `takePending()` returns the pending that
  `surfaceDestroyed` stored. Then `flush` posts the report and the stop, and **sets `restart_cause` even if both posts
  fail**. None of the three arrived. **So the start did not run in the instance whose surface was lost.**
- **In another instance,** `restartGuard` is `by lazy` per activity object, so a new instance builds a new, empty
  guard. `takePending()` returns null, giving a normal start: no flush, no `restart_cause`, no audio rebuild. **That is
  every row of cell 1.**
- **Which other instance.** An old instance destroyed in a live process runs `onDestroy` → `stopSession`, which posts
  its cached report and `native-stream-stop` (the journal shows both whenever that path runs: 03:39:12, 03:42:21).
  - They never came.
  - No second start came when the user backed out of the new instance either. An old instance still alive beneath it
    would have got its surface back and started again.
  - **So the old instance ended without `onDestroy`: its process died.**
- **The likely story** (the kill itself is not in the host's logs, and no logcat was taken):
  - the launcher came to the front on Home, and the system reclaimed the backgrounded PrivyHub process;
  - on the return, Android re-created the task's top activity in a new process, from its saved intent (the companion
    host extra);
  - `onCreate` → `surfaceCreated` → `startSession` → `native-stream-start`. **To the code, a cold start.**

**Why B11's guard was not on it:**
- B11 kept the pending (the cached report, the loss time) **only in the activity object's memory**. Its flush,
  `restart_cause` and audio rebuild were reachable only from a return to the same instance.
- **The property was not skipped.** It is read lazily in each instance (here at the new session's `takePending()`)
  and read `1`. The guard simply held nothing.
- **The three named ways are two code paths.** B11 settled that UX-R4's "silence self-restart" is the same surface
  path; the link recovery never restarts. So the paths are:
  - the same instance's surface return;
  - a new instance: in the same process (a configuration change, or a second launch from the app) or in a new process
    (the old one died with the session open).

**The other new-instance cases, today, in a live process** (read from the code; no row yet):
- **A recreation.** The manifest declares no `configChanges`, so a gamepad's `keyboard` / `navigation` change or an
  HDMI mode change recreates the activity. The old `onDestroy` → `stopSession` posts its report and stop on a
  background thread while the new instance's start goes out on its own. **The stop can land after the new start and
  end the new stream.**
- **A second launch from the app** (`openNativeGameStream`, standard launch mode) while a stopped stream instance stays
  in the back stack. The new instance starts with no stop. When the old one is destroyed later, its stop ends the new
  stream.

## 1. Built (`b15.diff`): `RestartGuard.kt` +B15 (B11's file); `NativeStreamActivity.kt` +14, added lines only

1. **The pending is kept beyond the activity object.**
   - At the surface's loss (B11's hook), the guard also writes the pending to a private file,
     `noBackupFilesDir/restart_guard_pending.properties` (`java.util.Properties`).
   - The file holds: the report text, the loss time on the system-wide monotonic clock, B11's cause fields, the writing
     instance's number in its process, and the process's mark (the monotonic time the guard first loaded there). **No
     address, no identifier** (a test checks the key set).
   - It is written synchronously on the UI thread: ~14-16 KB, a few ms. The page cache outlives a process death.
   - A failed write is recorded, never thrown; the in-memory pending (B11) still serves the same instance.
   - `onCreate` attaches the store, the instance number and the process's mark (`restartGuard?.attach(...)`).
2. **Every start takes it** (B11's `takePending()`, the one choke point). The file first:
   - written by this instance → `trigger` **`surface`**;
   - by another instance of this process → **`recreate`**;
   - by another process → **`process`** (cell 1's path).
   - The file is cleared by truncation when taken.
   - If the file is empty but this instance's persisted pending is in memory, another instance has already flushed it,
     so this is a normal start (no second stop).
   - Then B11's flush, unchanged: the old report POSTed, `native-stream-stop` (the host's `session_ended`), then the
     start. The audio receiver is rebuilt after the host's start response, with D-BASE-P2a's hold re-armed and the
     cushion and redundancy applied first.
3. **A recreation hands over instead of racing** (`stopSession`, before today's posts):
   - `isChangingConfigurations` → the pending is kept in the file (created from the cached report if the surface was
     not lost first), and today's posts are skipped. The next instance's start flushes it in order: report, stop,
     start.
   - This instance's pending already taken by another instance's start → today's posts are skipped. That report and
     stop were sent; a second stop would end the new stream.
   - Otherwise B11's `onSessionStopped` clears memory **and the file, if the file holds this instance's own pending**
     (never another's), and today's posts run.
4. **`restart_cause`** gains `trigger` beside B11's fields. `away_ms` is measured across processes on the monotonic
   clock, and is −1 if the clock reads backwards (a reboot).
5. **Limits, stated:**
   - a process killed while the surface stands (no `surfaceDestroyed`) leaves no pending: today's cold start;
   - the property cleared between the loss and the return leaves the file unread;
   - a pending from long ago is flushed at the next start all the same. Its report is kept, and the stop precedes the
     new start, so it can only end the old stream.

## 2. Tests (`tests_jvm.txt`, `tests_restart_guard_all_paths.xml`)

**`RestartGuardAllPathsTest`, 8.** Each path is modelled as the activity calls the guard, in B11's `twoWayDrop` shape:
the loss, the start's take + flush, and `stopSession`'s hand-over (a model, not the activity; disclosed as B11's was).
- **A 5-s surface loss (the same instance):**
  - the host gets `start`, `report(A)`, `stop`, `start` (one stop, one report);
  - `restart_cause.trigger` is `surface`, `away_ms` 5,000, both posts recorded;
  - frames 5 / 5 on the real receiver;
  - **the audio rebuilt plays the host's restarted stream (300 / 300); the carried state plays 0 / 300** (the storm).
- **The process path (cell 1's):**
  - guard A loses the surface; guard B (another process's mark, the same file) starts;
  - the host gets `start`, `report(A)`, `stop`, `start`; `trigger` `process`, `away_ms` 6,100; the audio rebuilt; the
    file taken once;
  - **B11's memory-only guard in the new process gives `start` and a null cause** (cell 1's rows).
- **A recreation:**
  - A's `stopSession` with `isChangingConfigurations` posts nothing;
  - B (the same process) flushes exactly one report and one stop before its start; `trigger` `recreate`;
  - the surface not lost before the destroy: the hand-over makes the pending from the cached report;
  - nothing open: no hand-over.
- **An old instance destroyed after another took its pending:** no second report or stop. Its surface back: a normal
  start.
- **A normal end clears only its own pending.** Another instance's end leaves this one's in the file.
- **A corrupt or missing file:** a normal start. **A failed write** (the store a directory): memory serves,
  `surface`.
- **The store keeps the fields, and its keys are only the eight named** (no address, no identifier).
- **The flag absent → today:** `start`, `start`; the audio receiver carried over; `fromSystem()` false.

**The suite:** **122 / 122**, offline in `/tmp/b_q24f/PrivyHub` with `--no-configuration-cache`, only
`privyhub-companion` and `privyhub-link-n1` active. B11's `RestartGuardTest` (8) is unchanged and green.

**Proof** `proof_flag_absent_client.md`: **PROVEN**, 0 removed / 14 added.
- `restartGuard?.attach(...)` evaluates no argument without the guard.
- `if (restartGuard?.handOver(...) { ... } == true)` is `null == true`, which is false: its body (`thermalSampler?.stop()`,
  `sessionStarted = false`, `stopLocalPipeline()`, `return`) and the lambda never run.

## 3. For CL-B11 (A)

- `setprop debug.privyhub.restart_guard 1`.
- **The Home press, as cell 1:** Home for ~5 s mid-game, then back to the game the way the user returns. Expected, on
  any of the paths:
  - in the host's log, before the new `native-stream-start`: the old report (`decoder-session-log`), then
    `native-stream-stop` (`session_ended`);
  - the new report's `restart_cause`, with `trigger` (`surface` if the process lived, `process` if it was
    re-created) and `away_ms` ≈ the time away;
  - **the new session's underruns ≈ the others' (0-13 per 2-s interval), not ~85 / s.**
- **Which path ran** is a logcat read (A's adb, read-only): `logcat -b events -d` around the press, for `am_kill` /
  `am_proc_died` / `am_proc_start` and `wm_on_create_called` / `wm_on_destroy_called`. The `trigger` key says the same.

## 4. Files

- **`b15_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b15.diff`, `proof_flag_absent_client.py` / `.md`, `tests_jvm.txt`, `tests_restart_guard_all_paths.xml`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `PrivyHub/app/src/main/java/streaming/RestartGuard.kt`, `NativeStreamActivity.kt`,
    `PrivyHub/app/src/test/java/streaming/RestartGuardAllPathsTest.kt` (new);
  - `docs/memory/patches/B15_RESTART_GUARD_ALL_PATHS.md`, `logs/b15_git_status.txt`.
- **Disclosed:**
  - the tree's `gradlew` has no execute bit, so it ran as `bash ./gradlew`;
  - the baseline regression's `tests/impairment` wrote its own `logs/impairment.jsonl` inside the copy (test output, as
    in earlier copies). It is left in place.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
