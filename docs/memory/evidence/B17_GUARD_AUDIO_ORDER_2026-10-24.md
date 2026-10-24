---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d (the client = `e2db0aa0…`'s sources, CONFIRMED; B17 uncommitted)
---

# B17 — the new instance's audio played the old stream until the host's stop starved it; the guard now holds the audio until its start is answered, and the old session's end rides in the start

**Classification: SETTLED + BUILT** behind the same `debug.privyhub.restart_guard=1` (client), with a request-gated
host half (`native-stream-start?…&guard_end=1`).
- **Tests:** 5 JVM tests (B15's harness, a slow fake host), JVM **130 / 130**; 2 host tests (`tests/guard_end`).
- **Proof:** host AST = HEAD with the 3 B17 items removed; client 9 added lines + 3 changed lines, each the same as
  today without the property: **PROVEN**.
- In the APK of B19. NOT ADOPTED; no live run; nothing committed.

Design `b17_2026-10-24/design_written_before_code.md`, sha256 `e005b970…ed98299`, hashed **15:54:09Z, before any B17
code**.

## 0. Settled (CL-B11 cell 1)

**The timeline (UTC):**

| time | row |
| --- | --- |
| 15:26:01.629 | the new `NativeStreamActivity` created (events read) |
| ~02.30 | its `startSession` (heartbeat 1 at 02.724, `elapsed_ms` 427): **0.67 s after creation**. The audio receiver is created **and started**, on the host's still-running old audio |
| 02.670 | the old report received (B15's first post) |
| 02.753 | `native-stream-stop` enters: `session_ended` |
| 05 | the stop's response: **~2.3 s inside the host's stop** |
| 06 | `native-stream-start`'s response; B11's rebuilt receiver starts |
| 09.479 | `session_started` (the ready) |

- **Heartbeat 2 (04.752): 221 underruns, 56 audio packets.** The receiver locked onto the old stream at ~02.30. When
  the stop tore it down at ~02.75, the receiver starved until the rebuild. **Not "late" frames this time** (B11's
  mechanism): no frames at all.
- Heartbeat 3: 0 / 0 (the rebuilt receiver waiting). Then 0.

**The flush's 3.4 s:**
- B15's posts are sequential, each waiting for its response.
- **The host's stop is the slow one:** `_stop_locked()` terminates the encoder and capture processes and waits for them
  (`wait(timeout=5)` each). That was ~2.3 s here.
- **`native-stream-start` runs the same `_stop_locked()` itself.** The two serialize on the manager's one lock, under a
  `ThreadingHTTPServer`.
- So the separate stop adds only its bookkeeping (`session_ended`, the ladder's session end) and its own wait.
- **A stop not waited on is unsafe:** its handler works before it takes the lock (the ladder, the emulator's status,
  `host_resource_sampling.stop()`). A start sent after a short bound can take the lock first, and then the late stop
  ends the **new** stream.

## 1. Built (`b17.diff`)

1. **The audio waits.**
   - `startSession` takes the pending on the UI thread, before the audio (`prepareStart()`). The session thread's
     `takePending()` returns the same one.
   - With a pending, the receiver is created **unstarted**.
   - B11's rebuild after the start's response is unchanged: fresh, the cushion first, then started, with the hold
     re-armed.
   - **No audio plays before the host's start is answered.**
2. **The picture keeps today's order.** The video starts at once, behind the full-screen start-up overlay, which stands
   until the new stream's gate releases. The audio is the only output that reaches the user through it.
3. **The end rides in the start.**
   - The guard posts **`native-stream-start?port=…&guard_end=1` first.** The host's start action runs the stop's
     bookkeeping at its entry (`session_ended`, the ladder's session end), then today's start, whose `_stop_locked()`
     ends the old stream.
   - The response carries `"guard_end": true`.
   - **No separate stop**, so none can land after the new start.
   - **The old report follows the start's response** on its own thread.
   - Host: `plugins/games.py` +7, request-gated.
4. **`restart_cause`** gains `flush` `via_start`, **`create_to_start_ms`**, `host_ended_session`. `old_report_posted`
   is set when the report returns; `stop_posted` false.
   - **Against a host without B17:** the start alone ends the old stream, with no `session_ended` row, and
     `host_ended_session` false says so.
5. **Limit, stated:** the host's ~2.3-s teardown still runs inside the start. The picture and the rebuilt audio come
   back after it, as before. Only the request moved earlier.

## 2. The target rows

| row | here |
| --- | --- |
| **R1** the first 2-s interval after the new `session_started` ≤ 15 underruns | by construction: no receiver plays before the start's response (JVM: the held receiver never started, the rebuilt one starts after the response); **the live count is CL-B12's** |
| **R2** creation → `native-stream-start` ≤ 1.0 s on a LAN | JVM, with a 300-ms-per-post host and CL-B11's 0.67-s creation → surface: **the start is the first post, at 670 ms**. B15's order with the same host sends it at 1,270 ms, before the host's 2.3-s stop. Live: `restart_cause.create_to_start_ms`, and the host's `session_ended` (now at the start's entry) against `wm_on_create_called` |

**Tests** (`tests_jvm.txt`, `tests_restart_guard_audio_order.xml`, `tests_guard_end_host.txt`):
- **`RestartGuardAudioOrderTest`, 5:**
  - **the recreate path:**
    - posts: `start?…&guard_end=1`, then `report(A)`; no stop;
    - the start at 670 ms;
    - the held receiver never started; the rebuilt one starts at the response and plays the host's restarted stream
      (300 / 300);
    - `trigger` `recreate`, `create_to_start_ms` 670, `host_ended_session` / `old_report_posted` true, `stop_posted`
      false;
  - **the `surface` and `process` paths the same way;**
  - **a host without `guard_end`:** recorded false, one start, never a stop after it;
  - **a normal start after `prepareStart`:** today's (the receiver at once, no cause);
  - **absent → today.**
- **B11's 8 and B15's 8: unchanged and green.**
- **`tests/guard_end`, 2:**
  - with `guard_end=1`: `session_ended`, the ladder's end, then today's calls, and `guard_end` true;
  - without it, or with `=0`: today's calls, no key.
  - `tests/remote_ladder` (which drives the same action) stays green.

## 3. For CL-B12 (A)

**The Home press on both return paths, the stack's host line in force:**
- the menu return (CL-B11's: PrivyHub's menu → the game);
- the direct return (CL-B10's: back to the stream).

**Expected:**
- **Before the new start:** no separate `native-stream-stop` in the journal. The `session_ended` row comes from the
  start request, with the start's own journal line after it. The old report's `decoder-session-log` follows within ~1 s.
- **`restart_cause`:** `flush` `via_start`, `host_ended_session` true, `create_to_start_ms` ≤ 1,000.
- **The first heartbeat interval after the new `session_started`: ≤ 15 underruns,** and no interval of the new client
  session above 15.

## 4. Files

- **`b17_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b17.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_jvm.txt`, `tests_restart_guard_audio_order.xml`, `tests_guard_end_host.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `RestartGuard.kt`, `NativeStreamActivity.kt`, `RestartGuardAudioOrderTest.kt` (new);
  - `companion/plugins/games.py`, `tests/guard_end/` (new);
  - `patches/B17_GUARD_AUDIO_ORDER.md`, `logs/b17_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
