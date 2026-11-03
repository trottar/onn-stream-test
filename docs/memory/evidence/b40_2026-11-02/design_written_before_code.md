# B40 — a hub-side VOD drop for the bench: the design, written before any code

Queue: `handoffs/QUEUE_2026-11-02M.md` §B40. Why: HOME-1's C5 was INVALID. To reach the onn's Wi-Fi setting the user
pressed Home, which released the player before the drop. The drop has to come from the hub, with the player untouched
and in front.

## The flag

- **`PRIVYHUB_VOD_DROP_TEST=1`**, read in `companion/range_server.py` exactly as B35's line is read
  (`os.environ.get(...).strip() == "1"`).
- **Host only, per-run only, never adopted.** The bench adds a drop-in, restarts, runs the cell, removes the drop-in
  and restarts.
- **It reaches the range server by inheritance.** `privyhub_service.py` launches `range_server.py` with
  `subprocess.Popen` and no `env=`, at the service's start (`CONTROLLER.start_server()`).
- **Absent / empty / anything but `1` = today byte for byte:**
  - one guarded block after B35's in `range_server.py`; nothing imported, the handler class untouched;
  - no thread, nothing read or written.

## The control: a file, appended to (not a signal)

- **The trigger is `<repo>/runtime/vod_drop_test.trigger`.** `runtime/` is git-ignored. A appends a line from a shell
  on the hub:
  ```
  mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger
  ```
- **Why a file, not `SIGUSR1`:**
  - **Nothing records the range server's pid.** Finding it with `ps` / `pgrep` can pick the wrong process.
  - **A signal to a range server running without the flag would kill it.** `SIGUSR1`'s default action terminates the
    process, which would take VOD down for the evening. A file touch with the flag absent does nothing.
  - A file works across the range server's restarts and leaves its own trail (one line per trigger).
- **Consumed without deleting** ("nothing deleted" holds; the server never writes or removes the file):
  - a daemon thread polls the file every 250 ms;
  - its signature is `(st_mtime_ns, st_size)`, or absent;
  - the signature at the server's start is the baseline, so a trigger left from an earlier run never fires;
  - each change of signature fires **one drop**, and the new signature becomes the last seen;
  - an appended line always grows the size, so a coarse mtime cannot hide a trigger.
- **A trigger with no VOD connection in flight is consumed** (row `dropped: 0`). It is not kept for later.

## The drop: a reset, as a dead link's TCP stack would give the player

- **Which connections:** every VOD connection currently streaming a body.
  - The guarded block wraps the handler class's `copyfile`, outermost: over B35's wrapper when `PRIVYHUB_VOD_LOG=1`,
    else over today's.
  - It registers `self.connection` with the request's opaque id (B35's `opaque_id`, 12 hex over the URL path) while
    the copy runs, and only for `/vod/…` paths (B35's `_kind` = `vod`). Live media under the root is never touched.
  - A movie is one long open-ended GET (HTTP/1.0, no keep-alive), so "in flight" is the movie.
- **How** (`probe_rst.py` / `probe_rst_output.txt`, run on this hub before this design):
  - `SO_LINGER {1, 0}`, then a Linux `connect()` with `AF_UNSPEC` on the socket (via `ctypes`), which is
    `tcp_disconnect`. It sends a **RST**.
  - The server's writer, even blocked in `sendall` because the player's buffer is full, wakes with
    `ConnectionResetError`. B35's row reads `closed: client_reset`.
  - The player's next read fails with a connection reset at once, its unread data discarded: Media3's network IO
    error, in B35's retry set.
  - The other way, `shutdown(SHUT_RDWR)`, gave the client a clean EOF only after 2.6 MB of buffered data. That is not
    a drop, so it is only the fallback if the `connect` call fails (non-Linux, no libc), and the row says so
    (`how: shutdown`).
- **The handler thread unwinds as on a real reset:** today's traceback reaches the range server's log, and B35's
  `vod_range` row is written. Nothing else in the server changes. The listening socket and the next request are
  untouched: the player's reconnect (`Range: bytes=<P>-`) is served as any request is.

## The rows

- **`logs/vod_drop_test.jsonl`** (rotating, B35's `_Writer`), one row per consumed trigger:
  - `at_utc`, `event: "vod_drop_injected"`, `trigger` (the count since the server's start);
  - `dropped` (connections reset) and `ids` (their opaque ids);
  - `how` (`rst` / `shutdown` / `none`), and `errors` (an error name per failed reset, no message).
- **The same row also into `logs/vod_range.jsonl`** when B35's log is on, so one file shows the injection, the reset
  request and the reconnect in order.
- **Redacted by construction:** no address, path, title or URL; the trigger file's content is never read.
- B36's keeper already copies `vod_range.jsonl`. `vod_drop_test.jsonl` is not in its list. It is a bench-only file,
  and the bench runs with B35's log on, so the row is in `vod_range.jsonl` too.

## Code

- **`companion/vod_drop_test.py` (new):** `DropTest(project_root, *, range_log=None, clock, interval)` with
  - `install(handler_class)`;
  - `poll_once()`, the unit the tests drive;
  - `start()`, the daemon thread;
  - `drop_now()`;
  - `drop_test_from_environ(environ, project_root, range_log)`.
- **`companion/range_server.py`:** one guarded block after B35's (+ ~10 lines). The class body is not edited.

## Tests (`tests/vod_drop_test/`, loopback, a real `RangeRequestHandler` subclass, a 16 MiB file)

1. **A fake player mid-stream** (it reads part of the body, then stops reading): one trigger → the player's next read
   raises a connection reset. Then:
   - the row `dropped: 1`, `how: rst`, the opaque id;
   - with B35's log on: `vod_range` reads `client_reset` with bytes < length, then the reconnect's `bytes=<P>-`
     request is served 206 with the right bytes.
2. **No trigger:** the player reads the whole file; no row.
3. **A trigger present at the start:** no drop (the baseline).
4. **Two appends:** two drops on two streams, one each; an unchanged file → none.
5. **A trigger with nothing in flight:** consumed, `dropped: 0`; the next stream is not dropped.
6. **A live / non-`/vod/` path in flight is not dropped.**
7. **The fallback:** `connect` unavailable → `how: shutdown`, the row says so.
8. **Absent = today:**
   - the module is not imported in a fresh process for unset / empty / `0` / `true`;
   - the base and new range servers give the same response bytes with the flag absent;
   - `range_server.py`'s AST minus the guarded block equals the predecessor's.
9. **Redaction:** no address and no title in any row.

**Mutations** (at least 1 caught): the baseline not taken (a stale trigger fires); `shutdown` instead of the RST
(test 1 sees EOF).

## The C5' bench method

The commands A types on the hub; the movie plays in front throughout. With B35's two (the client property, the log
line):

1. `PRIVYHUB_VOD_LOG=1` and `PRIVYHUB_VOD_DROP_TEST=1` in a drop-in, then the companion restart. The range server
   restarts with the service.
2. `adb shell setprop debug.privyhub.vod_retry 1`.
3. The movie playing ≥ 1 min.
4. `mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger`.
5. **Expected:**
   - `logs/vod_range.jsonl`: `vod_drop_injected` `dropped: 1`, then the stream's row `closed: client_reset`, then a
     `bytes=<P>-` request;
   - `logs/vod_client.jsonl`: `vod_error` → `vod_retry` → `vod_resumed`;
   - on screen, "reconnecting…" and the movie back at the position with no "Playback error".
6. The drop-in removed, the companion restarted, the property cleared.
