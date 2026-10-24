# B15 — the restart guard on every path: design, written before any B15 code

Baseline HEAD efa4240 (the client = `da09e154…`'s sources, B11 inside; A's uncommitted pin lines in `tools/` copied as
they stand). Queue: `handoffs/QUEUE_2026-10-24F.md` §B15. Data: CL-B10 §4 cell 1
(`cl_b10_2026-10-23/runs/1_snes_5ghz_restart_guard/`, the client reports `logs/games/decoder_sessions/
native_decoder_20261024_033912_129.json` and `…034221_063.json`).

## 0. Settled: the path the client took on the Home press, and why B11's guard was not on it

**The rows, in the host's own logs (cell 1):**
- the journal: `native-stream-start` 03:34:54Z, `native-stream-ready` 03:35:03; then **no request of any kind until
  the next `native-stream-start` at 03:38:45** (its handler logged `client_stream_restart` at 03:38:43.687, the
  response line at 03:38:45); `native-stream-ready` 03:38:50; at the user's back-out 03:39:12 **one**
  `decoder-session-log` (13,685 chars) and **one** `native-stream-stop`; the re-entry 03:41:45-03:42:21 the same.
- The heartbeat summary: the new client session's first heartbeat (sequence 1, `elapsed_ms` 473) at 03:38:44, so its
  `startSession` ran at ~03:38:43.5, ~6 s after the press (~03:38:37.6).
- The 03:39:12 report is the **new** session's (28.4 s). It carries `stall_signal_ms` and `link_notice_*` (so
  `debug.privyhub.stall_signal` and `link_notice` were read by that code, by the same `SystemProperties` reflection
  `RestartGuardFlag` uses) and **no `restart_cause`**. Its audio: `first_write_elapsed_ms` 133 — the first PCM 133 ms
  into the session, ~1.4 s before the host's start response — then 2,418 underruns / 5,165 concealed in 28 s: B11's
  mechanism exactly (the receiver locked onto the host's old stream, every frame of the restarted one `LATE`).
- **The first session's report never reached the host — not at the press, not at the back-out, not later.**

**What the code admits.** `native-stream-start` is posted from one place: `startSession`'s session thread, and
`startSession` is called from one place: `surfaceCreated`. B11's guard sits at exactly that choke point
(`restartGuard?.takePending()` before the start). With `restart_guard=1`:
- **the same activity instance** (surface lost, then created again): `surfaceDestroyed` stored the pending in the
  guard (a session was started), `takePending()` returns it, and `flush` posts the report and the stop and sets
  `lastCause` **even if both posts fail** (`old_report_posted` false). Neither a report, nor a stop, nor a
  `restart_cause` arrived. **So the start did not run in the instance whose surface was lost.**
- **another instance** (`restartGuard` is `by lazy` per activity object, so a new instance builds a new, empty guard):
  `takePending()` → null → a normal start: no flush, `lastCause` null, no audio rebuild. **That is every row of cell 1.**
- **Which other instance.** Had the old instance been destroyed in a live process, `onDestroy` → `stopSession` posts
  its cached report and `native-stream-stop` (both appear in the journal whenever that path runs: 03:39:12, 03:42:21).
  They never came, and no second `native-stream-start` came when the user backed out of the new instance at 03:39:12
  (an old instance still alive under it would have got its surface back and started again). **So the old instance
  ended without `onDestroy`: its process died.** The likely story (the logs cannot show the kill; no logcat was taken):
  the TV's launcher came to the foreground on Home, the system reclaimed the backgrounded PrivyHub process, and on the
  return Android re-created the task's top activity — `NativeStreamActivity`, from its saved intent (the companion
  host extra) — in a new process: `onCreate` → `surfaceCreated` → `startSession` → `native-stream-start`. To the code
  that is a cold start.
- **Why B11's guard was not on it:** B11's guard state (the cached report, the loss time) lived only in the activity
  object's memory. A new instance — after a process death, or a recreation in the same process — starts with an
  empty guard, so the guard's flush, its `restart_cause` and its audio rebuild are reachable only from the
  same-instance surface return. The property was not skipped: it is read lazily in each instance (here at the new
  session's `takePending()`), and read `1`; the guard simply held nothing. **B11 settled UX-R4's "silence
  self-restart" as the same surface path** (the link recovery never restarts), so the three named ways are two code
  paths: the same instance's surface return, and a new instance (same process: a configuration change or a second
  launch; a new process: the old one died with the session open).

**The other new-instance case, today, in a live process (no row yet, read from the code).** A recreation
(`isChangingConfigurations`: a gamepad's `keyboard|navigation` change, an HDMI mode change — the manifest declares no
`configChanges`) runs the old `onDestroy` → `stopSession`, whose report + `native-stream-stop` go out on a background
thread while the new instance's start goes out on its own: the host can get the stop **after** the new start and end
the new stream. And a second launch from the app (`openNativeGameStream`, standard launch mode) while a stopped stream
instance stays in the back stack: the new instance starts with no stop; when the old one is later destroyed its stop
ends the new stream.

## 1. The design, behind the same `debug.privyhub.restart_guard=1` (absent = today: no guard, every hook a no-op)

One guard for every start, its pending **kept outside the activity object**:
1. **The pending is persisted at the loss.** `onSurfaceLost` (B11's hook) also writes the pending to a small private
   file (`noBackupFilesDir/restart_guard_pending.properties`, `java.util.Properties`: the report text, the loss time on
   the system-wide monotonic clock, the B11 cause fields, the writing instance's number in its process and the
   process's mark = the monotonic time its guard class loaded — no address, no identifier). Written synchronously on
   the UI thread (~14-16 KB, a few ms; the page cache outlives a process death). A failed write is recorded, never
   thrown: the in-memory pending (B11) still serves the same instance.
2. **Every start takes it.** `takePending()` (B11's hook, the one choke point before `native-stream-start`) reads the
   file first, then memory:
   - the file holds a pending → take it, delete the file; **trigger** = `surface` (written by this instance),
     `recreate` (another instance, this process), `process` (another process);
   - the file is empty but this instance's memory holds one → another instance already flushed it → a normal start
     (no second stop);
   - no store (the tests' B11 shape) → memory only, trigger `surface`.
   Then B11's flush unchanged: the old report POSTed, `native-stream-stop` (the host's `session_ended`), the start, the
   audio receiver rebuilt after the host's start response with D-BASE-P2a's hold re-armed and the cushion /
   redundancy applied first.
3. **A recreation hands over instead of racing.** In `stopSession`, before today's posts: if the activity is being
   recreated (`isChangingConfigurations`), the guard keeps (or creates, from the cached report) the pending in the
   file and today's posts are skipped — the next instance's start flushes it in order (report, stop, start). If this
   instance's pending was already taken by another instance's start (memory holds one, the file does not), today's
   posts are skipped too (that report and stop were sent; a second stop would end the new stream). Otherwise B11's
   `onSessionStopped` (clear memory **and file**) and today's posts.
4. **`restart_cause`** gains `trigger` (`surface` / `recreate` / `process`) beside B11's fields; `away_ms` from the
   monotonic clock across processes (−1 if it reads backwards, i.e. a reboot).
5. **Limits, stated:** a process killed while the surface stands (no `surfaceDestroyed`) leaves no pending — today's
   cold start; the property cleared between the loss and the return leaves the file unread (no guard). A pending from
   long ago is flushed at the next start all the same (its report kept; the stop precedes the new start, so it can only
   end the old stream).

Absent: `restartGuard` is null; every new line is a `restartGuard?.…` call or an `if (restartGuard?.… == true)` whose
body never runs, plus the guard's own file (`RestartGuard.kt`, used only through the lazy property). **Added lines
only** in `NativeStreamActivity.kt`; the proof as B11's.

## 2. Tests (JVM, B10's / B11's harness)

New `RestartGuardAllPathsTest`, a model of the activity's calls around each path (as B11's `twoWayDrop`), a temp file
as the store, an injected clock, a fake host transport, the real `RtpH264Receiver` on loopback and a fake decoder, the
real `OpusReorder` as the audio's sequence state:
- **a 5-s surface loss (same instance):** one stop, one report (the old one), `restart_cause.trigger` `surface`,
  `away_ms` 5,000, one start; frames to the new receiver; the rebuilt audio state plays the host's restarted stream
  (0 frames lost) where the carried one plays none (the storm);
- **the process path (cell 1's):** guard A loses the surface (the file written), a new guard B (another process mark,
  the same file) starts: report(A), stop, start; `trigger` `process`, `away_ms` ≈ the gap; memory-only (B11) would
  give start, start;
- **a recreation:** A's `stopSession` with `isChangingConfigurations` → no posts; B (same process mark) flushes:
  exactly one report and one stop, before the start; `trigger` `recreate`;
- **the old instance destroyed after another took its pending:** no second report, no second stop;
- a normal end clears the file (the next start is a normal one); a corrupt / missing file → a normal start, nothing
  thrown; a failed write → memory still serves the same instance;
- **the flag absent → today** (start, start; nothing written); B11's 8 tests unchanged and green.
The whole JVM suite green, offline in `/tmp/b_q24f` with `--no-configuration-cache`.

## 3. Files

Record `evidence/B15_RESTART_GUARD_ALL_PATHS_2026-10-24.md` + `b15_2026-10-24/` (baseline, predecessors, the diff, the
proof, the tests, `redact_check`, `manifest.sha256`); `patches/B15_RESTART_GUARD_ALL_PATHS.md`;
`logs/b15_git_status.txt`.
