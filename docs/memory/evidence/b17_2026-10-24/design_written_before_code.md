# B17 — the audio before the guard's restart, and the flush's 3.4 s: design, written before any B17 code

Baseline HEAD 7f3f71d (the client = `e2db0aa0…`'s sources, CONFIRMED). Queue: `handoffs/QUEUE_2026-10-24G.md` §B17.
Data: CL-B11 §4 (`cl_b11_2026-10-24/runs/1_snes_5ghz_restart_guard_all_paths/`: the heartbeat and recovery logs, the
journal, the decoder report file names).

## 0. Settled from the code and cell 1's rows

**The timeline (UTC):**
- 15:26:01.629: the new `NativeStreamActivity` is created (the events read).
- ~15:26:02.30: its `startSession` runs, after its surface. Its first heartbeat (sequence 1) arrived at 02.724 with
  `elapsed_ms` 427, so this is **~0.67 s after creation**.
- At the top of `startSession` the audio receiver is created **and started**, then the session thread runs B15's flush:
  - the old report POST: the host's file `…_152602_670` → **received 02.670**;
  - `native-stream-stop`: the handler logs `session_ended` at its entry, **02.753**. The journal's response line reads
    **05**, so **~2.3 s inside the host's stop**;
  - `native-stream-start`: response line 06 (`_start_linux_locked`'s own work); `session_started` at the ready, 09.479.
- **Heartbeat 2 (04.752): `audio_underruns` 221, `audio_rx_packets` 56.**
  - The new receiver started at ~02.30 and locked onto the host's still-running old audio.
  - When the stop handler tore the old stream down at ~02.75, it starved: 56 packets in that interval, then nothing.
  - So every playback slot from ~02.8 to the rebuild (after the start response, ~06) was an underrun.
- Heartbeat 3 (06.786): 0 underruns, 0 packets (the rebuilt receiver, waiting). After that, 0.

**Why the flush took 3.4 s:**
- The posts are sequential and each waits for its response.
- **The host's stop is the slow one.** `native-stream-stop` → `NativeStreamManager.stop()` → `_stop_locked()`: the
  session I/O stopped, then **the encoder and the capture process terminated and waited for** (`wait(timeout=5)` each),
  the FEC relay stopped. That took ~2.3 s here.
- **`native-stream-start` runs the same `_stop_locked()` itself** (`_start_linux_locked`, before it spawns anything).
  Stop and start serialize on the manager's one lock. The server is a `ThreadingHTTPServer`, so the two requests can
  run at once.
- **So the separate stop is redundant for the stream.** Its only own effect is the bookkeeping: the recovery's
  `session_ended` and the ladder's session end.
- **And a stop that is not waited on is unsafe.** Its handler does work before it takes the lock (`session_ended`, the
  ladder, the emulator's status, `host_resource_sampling.stop()`). A start sent after a short bound can take the lock
  first, and then the late stop ends the **new** stream.

## 1. The design, behind the same `debug.privyhub.restart_guard=1` (absent = today; B15's paths otherwise unchanged)

1. **The audio waits.**
   - When a pending is taken, `startSession` takes it **on the UI thread, before the audio receiver** (`prepareStart()`;
     the session thread's `takePending()` then returns that same pending).
   - The receiver is created **but not started**.
   - B11's rebuild after the host's start response is unchanged: a fresh receiver, the cushion and redundancy applied,
     then started, with D-BASE-P2a's hold re-armed.
   - **No audio is played before the start response.**
2. **The picture: unchanged order.**
   - The video receiver and decoder start at once, as today. Any old-stream frames decode behind the full-screen
     start-up overlay ("Stabilizing game…"), which stands until the new stream's gate releases.
   - After the host's start, the SSRC change resyncs to the new stream's IDR.
   - **Why only the audio waits:** it is the only output that reaches the user through the overlay.
3. **The flush made fast: the end of the old session rides in the start.**
   - The session thread posts **`native-stream-start?port=…&guard_end=1` first.** The host's start action, seeing
     `guard_end=1`, runs the stop action's bookkeeping **at its entry**, in the same request:
     `self._recovery.session_ended()` and `self._adaptive_bitrate_session_ended()`. Then today's start runs, whose
     `_stop_locked()` ends the old stream.
   - The response carries `"guard_end": true`.
   - **No separate `native-stream-stop` is posted.** The order (end, then start) holds by construction, and no stop can
     land after the new start.
   - **The old report is posted after the start's response,** on its own thread. It is the old session's file, keyed by
     its own content.
   - Host side: request-gated. Without `guard_end=1` the start action is today's byte for byte (an AST proof). Only the
     guarded client sends it.
   - Against a host without this, the start alone still ends the old stream (its `_stop_locked()`), with no
     `session_ended` row. `restart_cause.host_ended_session` false says so.
4. **`restart_cause`** gains:
   - `create_to_start_ms`: the activity's `onCreate` → the start request sent;
   - `flush`: `"via_start"`;
   - `host_ended_session`: the response's `guard_end`;
   - `old_report_posted`, set when the report's POST returns;
   - `stop_posted` stays in the map and reads false (no stop is posted).
5. **Limit, stated:** the host's own teardown (~2.3 s here) still runs inside the start, before its response. The
   picture and the rebuilt audio come back after it, as before. The row below counts the request.

**Target rows (hashed with this design):**
- **R1:** on the new-instance path, the first 2-s heartbeat interval after the new `session_started` has
  **≤ 15 underruns**. No receiver plays before the start response, so no interval of the new session can starve on the
  old stream.
- **R2:** the new instance's creation → `native-stream-start` **≤ 1.0 s on a LAN.**
  - Client: `restart_cause.create_to_start_ms`.
  - Host: the start handler's `session_ended` row (logged at its entry with `guard_end=1`) against the events log's
    `wm_on_create_called`.
- Absent = today byte for byte (client: the property; host: the parameter).

## 2. Tests

- **JVM (B15's harness), `RestartGuardAudioOrderTest`:**
  - **the recreate path with a slow fake host (300 ms per post) and CL-B11's 0.67-s creation → surface:**
    - the start is the first post, sent ≤ 1.0 s after creation;
    - **no audio receiver started before the start's response**; the rebuilt receiver starts after it;
    - exactly one report (after the start), no separate stop;
    - `trigger` `recreate`, `create_to_start_ms` measured;
    - B15's two-post order, modelled with the same host, sends its start at 1.27 s (beyond the bound);
  - the `surface` and `process` paths the same way (their triggers, one report, no stop);
  - the host without `guard_end` (no acknowledgement) → `host_ended_session` false, the start still sent once;
  - **absent → today:** the receiver started at once, `start` with no parameter, nothing posted before.
  - B11's and B15's tests unchanged and green.
- **Host:** the plugin's start action (the module loaded alone, as `tests/remote_ladder` does) with `guard_end=1` →
  `session_ended`, then the ladder's session end, then today's start, and `guard_end` true in the response. Without it
  → today's calls only. The AST proof.

## 3. Files

Record `evidence/B17_GUARD_AUDIO_ORDER_2026-10-24.md` + `b17_2026-10-24/`; `patches/B17_GUARD_AUDIO_ORDER.md`;
`logs/b17_git_status.txt`.
