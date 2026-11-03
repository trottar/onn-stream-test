---
memory_schema: 1
as_of: 2026-11-02
baseline_commit: e0155d1c (plus A's uncommitted G-A10 tools edits; B40 built in /tmp/b_q02m_b40, uncommitted)
---

# B40 — a hub-side VOD drop for the bench: `PRIVYHUB_VOD_DROP_TEST=1` resets the playing movie's connection once, on a file trigger, with the player untouched and in front

**Classification: BUILT** behind `PRIVYHUB_VOD_DROP_TEST=1`: host only, per run only, **never adopted**.
- **Tests:** `tests/vod_drop_test` 14 green (three runs). B35's `tests/vod_log` 9 green with one filter line added.
  Every host suite as the queue-M baseline, plus the new one. Three mutations caught.
- **Proof:** absent = today, PROVEN.
- No live run, nothing applied to the tree, nothing committed.

Design `b40_2026-11-02/design_written_before_code.md`, sha256 `b0454e4f…1932`, hashed **2026-11-03T02:58:39Z, before
any B40 code**. A scratch probe (`probe_rst.py`, run before the design) chose the reset method. Precondition, checked
by the coordinator: G-A10's record present; only the companion and `privyhub-diag` active.

## 0. Why

HOME-1's C5 was INVALID. To reach the onn's Wi-Fi setting the user pressed Home, and the player was released as the
app left (01:57:42). The Wi-Fi went down with no player running, so B35's retry had nothing to retry. The drop has to
come from the hub while the movie plays in front.

## 1. Settled

- **How the flag reaches the range server:** `privyhub_service.py` launches `range_server.py` with `Popen` and no
  `env=`, at the service's start (`CONTROLLER.start_server()`). It inherits the companion's environment, as B35's
  `PRIVYHUB_VOD_LOG` does. So the line needs a drop-in and a companion restart; the restart restarts the range server.
- **The control is a file, not a signal:**
  - nothing records the range server's pid, so a `pgrep` could pick the wrong process;
  - `SIGUSR1`'s default action terminates a process. A range server running without the flag (any evening but the
    bench's) would die and take VOD down. A file appended to with the flag absent does nothing (the absent test
    appends one and the server lives).
- **The reset** (`probe_rst_output.txt`): with the server's writer blocked in `sendall`, as it is when the player's
  buffer is full —

  | method | the writer | the client |
  | --- | --- | --- |
  | a Linux `connect()` with `AF_UNSPEC` (`tcp_disconnect`), after `SO_LINGER {1,0}` | `ConnectionResetError` | **`ConnectionResetError`** after 127 KB already queued to it |
  | `shutdown(SHUT_RDWR)` | `BrokenPipeError` | a clean **EOF** after 2.6 MB |

  The first is a drop, so it is the method; the second is the fallback only (`how: shutdown` in the row).
  - **Correction to the design:** it said the player's unread data is discarded. Linux still delivers what was already
    in the client's receive queue (127 KB here), then the reset.

## 2. Built (`b40_2026-11-02/b40.diff`)

- **`companion/vod_drop_test.py` (new, 155 lines), `DropTest`:**
  - **The trigger:** `<repo>/runtime/vod_drop_test.trigger` (`runtime/` is git-ignored), appended to by A.
  - **The poll:** a daemon thread `vod-drop-test` polls its `(st_mtime_ns, st_size)` every 250 ms. The signature at
    the server's start is the baseline, so a trigger left from an earlier run never fires. Each change fires one drop.
  - **The file is never read, written or removed here:** it is consumed by its signature, so nothing is deleted.
  - **What is dropped:** `install()` wraps the handler class's `copyfile`, outermost (over B35's wrapper when its log
    is on). It registers the connection with B35's opaque id while a body streams, and only for `/vod/…` (B35's
    `_kind`). Live media under the root is never touched.
  - **The drop:** on a trigger, every registered connection gets `SO_LINGER {1,0}` + `connect(AF_UNSPEC)` via `ctypes`
    (fallback `shutdown`). The handler thread unwinds as on any reset, so today's traceback reaches the range server's
    log and B35's row reads `closed: client_reset`. The listening socket is untouched, and the player's reconnect is
    served as any request.
  - **The row:** `{"at_utc", "event": "vod_drop_injected", "trigger": n, "dropped": k, "ids": [12-hex…], "how":
    "rst"|"shutdown"|"none", ["errors": [names]]}`.
    - It goes into **`logs/vod_drop_test.jsonl`**, and into **`logs/vod_range.jsonl`** when B35's log is on.
    - `at_utc` is taken before the resets, so it falls inside the reset request's `at_utc..end_utc`.
    - **Redacted by construction:** no address, path, title, URL or token; the trigger's content is never read.
  - A trigger with nothing in flight is consumed (`dropped: 0`, `how: none`), not kept.
- **`companion/range_server.py` (+15):** `VOD_DROP_TEST = None` and one guarded block after B35's (`.strip() ==
  "1"`, B35's convention): import, construct with `VOD_LOG`, `install(RangeRequestHandler)`, `start()`. The class body
  is not edited.
- **`tests/vod_log/test_vod_log.py` (B35's, one line):** its AST count of the nodes added since queue L's base skips
  B40's two. Disclosed; B40's own suite checks them.

## 3. Tests (`tests_vod_drop_test_x3.txt`, `tests_mutations.txt`, `tests_regression_after.txt`)

The setup: loopback, a real `RangeRequestHandler` subclass (the module's class never touched), a 16 MiB file under
`vod/`. A fake player sends one open-ended GET, reads 100 KiB, then stops reading (a full buffer: the server is
blocked mid-body).

- **Mid-stream + one trigger:**
  - the player's reads end in `ConnectionResetError` with < 16 MiB;
  - one row `dropped: 1`, `how: rst`, the opaque id; a second poll → nothing;
  - the trigger file still exists.
- **No trigger:** three polls, nothing; the whole file arrives (EOF, byte-equal); no row.
- **A trigger left from before the start:** never fires; the next append fires `trigger: 1`.
- **Two appends:** two streams, one drop each; no third.
- **Nothing in flight:** consumed (`dropped: 0`, `none`), and the next stream is not dropped.
- **A non-`/vod/` path in flight** (`/live/…`): not dropped, read whole.
- **No libc `connect`:** `how: shutdown`, said so.
- **The real thread** (50-ms poll): the drop by itself.
- **With B35's log on:**
  - `vod_range.jsonl` holds the injection, the reset request (`client_reset`, `bytes=0-`, bytes < length) and the
    reconnect `bytes=4321000-` → 206, `complete`, byte-equal;
  - the times nest: reset `at_utc` ≤ injection ≤ reset `end_utc` ≤ reconnect `at_utc`;
  - the injection row is in its own file too; every row redacted.
  - The file's order is the write order: the reset's handler can finish its row first, so the test reads the times,
    not the order.
- **Absent:**
  - `enabled` parses (`1` / ` 1 ` on; `""` / `0` / `true` / `yes` / unset off);
  - a fresh process imports nothing for five values; on, it installs and the thread runs;
  - the AST is the predecessor's minus two nodes;
  - the base and new servers give the same bytes; a trigger with the flag absent does nothing.
- **Mutations, all caught:**
  - m1, no baseline (a stale trigger fires): 1 fails;
  - m2, the `connect` reset removed (a shutdown): 4 fail;
  - m3, every path dropped: 1 fails.
- **Every host suite in the copy:** the baseline's outcomes line for line plus `tests/vod_drop_test`. The four
  `tools/` tests fail in a copy as at every baseline.

## 4. The C5' bench method (for HOME-2)

All on the hub; the movie plays in front throughout; the onn's remote stays in the user's hand, unused.
1. **The two host lines, for this run only:**
   ```
   printf '[Service]\nEnvironment=PRIVYHUB_VOD_LOG=1\nEnvironment=PRIVYHUB_VOD_DROP_TEST=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b40-vod-drop.conf
   systemctl --user daemon-reload && systemctl --user restart privyhub-companion
   ```
   Outside 04:30-05:30Z; no game running. The range server restarts with the service and takes its baseline then.
2. On the onn's APK (B35's client in it): `adb shell setprop debug.privyhub.vod_retry 1`.
3. The user starts a movie and lets it play ≥ 1 min.
4. **The drop, from the hub:** `cd ~/Projects/onn-stream-test && mkdir -p runtime && date -u +%FT%TZ >> runtime/vod_drop_test.trigger`.
5. **Expected within ~1 s:**
   - `logs/vod_drop_test.jsonl` / `logs/vod_range.jsonl`: `vod_drop_injected` with `dropped: 1`, `how: rst`. With
     `dropped: 0` nothing was streaming, and the cell is invalid.
   - `logs/vod_range.jsonl`: the movie's open request `closed: client_reset`, bytes < length; then a new request
     `range: bytes=<P>-` → 206.
   - `logs/vod_client.jsonl`: `vod_error` → `vod_retry` (attempt 1, …) → `vod_resumed`.
   - On screen: "reconnecting…", then the movie at the same position, with no "Playback error".
   - A player that buffers ahead may play out its buffer (seconds) before it reads and sees the reset; the rows say
     when.
6. **The close:**
   ```
   rm ~/.config/systemd/user/privyhub-companion.service.d/b40-vod-drop.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
   adb shell setprop debug.privyhub.vod_retry ""
   ```
   The drop-in is A's own bench file. The trigger file stays in the git-ignored `runtime/` and is harmless without the
   line.

## 5. Limits, stated

- **Linux only for the RST:** elsewhere it falls back to a shutdown (an EOF to the player), and the row says so.
- **Bench only:** `logs/vod_drop_test.jsonl` is not in B36's keeper list. The bench runs with B35's log on, so the
  row is also in `vod_range.jsonl`, which the keeper copies.
- **No auto-trigger, no timer, no network shim:** one drop per appended line, by hand.

## 6. Files

- **`b40_2026-11-02/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (`range_server.py`, `test_vod_log.py`), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `probe_rst.py` / `probe_rst_output.txt`;
  - `b40.diff`;
  - `proof_flag_absent.py` / `.md` / `_output.txt`;
  - `tests_vod_drop_test_x3.txt`, `tests_mutations.txt`, `tests_regression_queue_m_baseline.txt`,
    `tests_regression_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **In the diff:** `companion/vod_drop_test.py` (new), `companion/range_server.py`, `tests/vod_drop_test/` (new),
  `tests/vod_log/test_vod_log.py` (one line). Patch file: `patches/B40_VOD_DROP_TEST.md`.
- **Left in /tmp:** `b_q02m_b40` (the copy) and `b_q02m_b40_scratch/` (`probe_rst.py`, `mut_m1..m3/`).
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft; the Opal untouched;
  - `privyhub-diag` and `~/privyhub_diag/` untouched; the live tree's code untouched;
  - nothing of A's touched; nothing fetched, deleted, adopted or committed.
