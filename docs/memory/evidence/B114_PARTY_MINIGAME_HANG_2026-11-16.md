---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AQ) — PP-H3's hang named, reproduced and made impossible, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1 (either absent → today byte for byte through the real HTTP routes against HEAD 8fa398c8's companion). The lock: the manager's own lock, held by the mini game's start across the stream switch, whose end waited on the live bitrate controller's lock — held by a client-health report waiting on the manager's lock. A new test (two mini games back to back through a stubbed live stream, the onn's traffic and status / result / Home / RESUME / END from other threads) times out on HEAD with the start's thread stopped exactly where PP-H3's did, and passes after the fix. The fix: no lock across a launch, a stream start or stop, or a wait on another thread; every route within 2 s while a mini game is on; a stuck start given up by the hub; END from the onn always works. Nothing adopted; nothing committed. No title, game id, path or picture in this record
---

# B114 — the party mini game's hang: reproduced first, then made impossible (2026-11-16)

**Baseline:** HEAD `8fa398c8` (PP-H3 committed with queue AQ). **Design** hashed 20:52:25Z, before code
(`b114_2026-11-16/design.sha256`, `design_written_before_code.md`); no amendment.

## The lock, named from the code (and seen in the test's own threads)

**The manager's lock** (`EmulatorManager.lock`, an RLock). B110's `party_minigame._run` held it (`with emu.lock:`)
across the whole start: set aside → launch → pause → the pads' route (`minigame_route`) → **the stream switch**
(`_recovery_full_start_encoder` → `NativeStreamManager.start`) → the watch → resume. The switch's own `finally` calls
the live bitrate controller's `note_recovery_restart`, which takes **the bitrate controller's lock**. That lock is
taken by every client-health report (`POST /diagnostics/client-health`, every 2.0 s from the onn): `observe()` holds it
and asks `_adaptive_bitrate_context()` → `emulator.status()` → **the manager's lock**. Two threads, two locks, each
holding what the other waits for:

| thread | holds | waits for (HEAD's test run, `hang_head_threads.json`) |
| --- | --- | --- |
| the mini game's start (`party-minigame`) | the manager's lock | the bitrate lock — `party_minigame.py:_switch_stream` → `games.py:_recovery_full_start_encoder` → `adaptive_bitrate_live.py:note_recovery_restart` |
| a client-health report | the bitrate lock | the manager's lock — `adaptive_bitrate_live.py:_ctx` → `games.py:_adaptive_bitrate_context` → `emulator_manager.py:status` |

**Everything else then waits on one of the two:** every `status` (`emulator_manager.status`, 3 threads in the test),
every `native-stream-status` and every later client-health report (the bitrate controller's `status`, 5), the
recovery's stall worker (`stall_signal.handle` → `_enter_recovery` → `emulator_manager.pause` — its state set to
PAUSED_RECOVERING before the call and its `desync_pause` row written after, so **no row, and the give-up exactly 120 s
later**: 20:29:20.6Z → 20:31:20.6Z at the TV). PP-H3's 208 of 214 threads on a futex were this pile.
`party-minigame-result` takes only the layer's own lock: **in the test it kept answering in ≤ 13 ms during the hang**
(A's result calls must have waited behind A's own status calls).

**Why match 1 passed and match 2 did not** (the bitrate log, `logs/games/adaptive_bitrate_shadow.jsonl`, read-only):
the cycle closes only if a report reaches `observe()` while the start holds the manager's lock **and not yet the
stream's** (a report arriving during the stream's start first waits on the stream's lock in its own
`_native_stream_status()`, and the start's `finally` then wins the bitrate lock) — a window of ~1.2 s (the launch, the
pause, the route) in every 2.0 s. **Match 1:** reports at 20:25:35.998Z / ~37.99Z, the route at 37.763Z, the stream's
lock taken right after → that report met the stream's lock; `ssrc_change` written at 41.355Z. **Match 2:** reports at
…15.410Z, 17.447Z and ~19.46Z; **the route at 20:29:19.448Z** → the report took the bitrate lock first; **no
`ssrc_change`, no `minigame_stream`, no sample row after 17.447Z**; the new encoders ran (two ffmpeg at 85-94 %): the
start itself finished, only its `finally` hung. **The recovery's restart after match 1 was not the cause** — it only
moved the reports' phase (to x.4xx at its 20:27:40.85Z restart), which put the route 12 ms before a report. About a
60 % chance per start. **The way back had the same edge** (`end()` held the manager's lock across the switch back);
match 1's did not switch (the stream was already down — B115).

## The test that hangs on HEAD (`tests/b114_party_minigame_hang/`)

Through the real HTTP server on loopback in a child process (B110's harness: B108's stand-in board, B101's fake
RetroArch, B103's fake pictures) **with the hub's adopted lines that matter on**: `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`,
`PRIVYHUB_LINK_RECOVERY=1` (the stall worker, the stall owner, the holds), `PRIVYHUB_RESTART_FAST=1`,
`PRIVYHUB_RESTART_FAST_UNLOCK=1`, plus both bench flags. **The stream stub** (`b114_scenario.py`): its own RLock over
start / stop / status / the recovery's restart / the bitrate step; a start = the old teardown + the new encoder
(0.6 s, scaled); **the capture bound to the process it was started for — that process gone, the stream down** until
the next start (the real `_reap_locked`); the live bitrate controller re-bound to it (serial lock = the stub's). **The
onn**, on its own threads: a real `privyhub_client_health_v1` report every 0.1 s (20× the onn's rate: the window is
always hit), heartbeats with the real output age every 0.25 s, the **stall datagrams (PHS1) through the real
`StallSignal`** whenever frames stop ≥ 400 ms, a stall end when they resume; the recovery's own monitor (the stall
owner's v2 shortened to 1 s). **Other threads throughout:** `status`, `native-stream-status`, `party-minigame-result`
every 0.1 s (each answer's latency recorded, and whether a mini game was on); Home and RESUME in match 1; END at the
close; then (after the fix) END in five phases and two stuck starts. A start not `playing` within 25 s (or a match not
ended within 40 s) → every thread's stack written, the child leaves: **the suite fails, it does not hang.**

**The two runs** (`tests_b114_state_then_head.txt`; the child's own answers in `run_after_b114_summary.json` and
`hang_head_threads.json`):

- **HEAD `8fa398c8` (B110-B112), `B114_AGAINST=8fa398c8`:** **hung** — "m1: never playing (starting)"; mini game 1's
  rows `minigame_start`, `minigame_launch`, `minigame_route` and nothing more (PP-H3's match 2 exactly); `status` and
  `native-stream-status` timed out at 12 s; the start's thread in `note_recovery_restart`; the threads above. 7 tests:
  3 failures, 4 errors (they read what never came).
- **HEAD + B114** (its own work copy): **both mini games ended** (end_P2 [0, 1], end_P1 [1, 0]); every answer while a
  mini game was on < 2 s; 7 of 8 tests OK — the eighth, END during **the hand-over back**, needs B115 (under HEAD's
  way back the stream is already down by then, so there is no hand-over to be in: the END came after the mini game had
  closed). **With B115 in the tree: 8 / 8** (and 3 runs in `b115_2026-11-16/tests_x3.txt`).

## The fix (`companion/party_minigame.py`, `companion/plugins/games.py`; properties as designed, each tested)

- **P1 — no lock across a launch, a stream start or stop, or a wait on another thread.** The start is a sequence of
  steps on the mini game's own actor thread; each manager call takes the manager's lock **for that call only**
  (`_emu_call`: tried in 0.2-s steps, an END checked between, re-checked under it); **the stream switch runs on a helper
  thread with nothing held**, waited for at most 15 s (a miss → `switched: false`, "the switch did not finish within
  15 s", the mini game given up); the layer's own lock guards its fields only. *Test:* the stub records, at every
  stream start, whether the calling thread holds the manager's lock — HEAD: `[false, true]` (the mini game's), after:
  all `false`.
- **P2 — every route answers within 2 s while a mini game is on.** `status` / `native-stream-status`: today's answer
  if it comes within 1.5 s, else the last good one with `"snapshot": true` (one helper per route at a time, so a stuck
  read cannot pile threads). `party-minigame-result`: the mini game's own state. **Home (`native-stream-stop`), END
  (`stop`) and the board's `party-minigame-end`: taken at once** onto the mini game's queue — answered with their own
  answer (and `"taken"`) if done within 1.5 s, else `{"taken", "pending": true}` — **acted on in order** by the actor
  (the start's steps first). **RESUME (`native-stream-start` / `-ready`)**: taken onto the same queue in order, and
  answered with its own real answer (the onn needs `"active": true` from the started stream; its start's own seconds
  are today's). *Test:* through two mini games, the stuck starts and END in five phases, while a mini game was on:
  `status` max 1.50 s, `native-stream-status` 1.50 s, the result 0.003 s, Home 0.006 s, the board's end 0.006 s,
  END 1.50 s, the start 0.004 s (B114's own run; with B115 the board's end 0.61 s: the switch back runs in it); Home paused the title, RESUME's start and ready 200 / active / released in the order sent.
  (With no mini game on, the routes are today's code: a 3-s stream start still holds `status` 3 s — seen in the test
  only under B114 alone, when the recovery restarted the stream after HEAD's way back; B115 removes that restart.)
- **P3 — a mini game stuck in `starting` for 30 s is given up by the hub itself**: the watch runs from the start; past
  `START_LIMIT_S` → `given_up` "the mini game did not start within 30 s" (a draw to the board) and the end runs —
  **without the actor if it is the stuck one** (after 3 s): the watch stopped, the title stopped (the manager's own stop
  if its lock comes within 10 s, and the title's process ended directly in any case), the route cleared, the board's
  session back, the stream switched to the board. A start that fails (an exception, a switch past its bound) is given
  up and **ended by the hub at once** (HEAD waited for the board's end call). If a stuck step returns later the actor
  sees the mini game closed and stops what it made (a title it launched). *Test (limits shortened to 3 s / 2 s):* a
  start stuck in the watch's start → given_up "did not start within 3 s", the title gone, the route cleared, the board's
  session and picture back; a start stuck in the stream switch → given_up "the stream switch did not finish within
  2 s", the same.
- **P4 — END from the onn always works**: during **starting, playing, the hand-over in, the hand-over back (with
  B115), a stuck start** → answered 200 `"taken": "end"` within 1.5 s; the title gone, **the board quit by F10**, the
  stream's session ended, `status` not active, the route cleared, the result `given_up` "ended from the onn".
- **The manager's stop hook** (another launch, `launch_orphaned`: callers that hold the manager's lock) ends the mini
  game inline, waiting on nothing (no actor, no stream), then the board's own stop — as B110.
- **Rows** added: `minigame_taken` (what: home / resume_start / resume_ready / end / end_board / end_hub, state) and
  `minigame_stuck` (the step, its seconds).

## Flags absent → today

`FlagsAbsentAreToday` (B114's suite): four flag combinations with the adopted lines on (PARTY alone, H7 alone,
neither, PARTY with H7=0), each **run on HEAD `8fa398c8`'s companion and on the tree** through the real routes — the
four party routes, `status`, `native-stream-stop` and `stop` with nothing running: the same code and bytes (the
recovery's `since_ms` clock reading masked on both sides). Every new line in `games.py` sits under
`_party_minigame is not None` (the module is imported only with both flags).

## Other suites (the tree, B114 + B115)

B110 13, B112 7, B108 16, B103 13, B105 12, B111 2 (Godot), the stall signal 12, the stall owner 10, the stall
resume 7, the session end 8, B61 14, the rewind 13 + 14, the link recovery 16 + 22, the fast restart 13 + 10, the client
contract 5, PS2 93, GameCube 54: OK (`b115_2026-11-16/tests_x3.txt`; the five party suites' 15 runs left no temp dir —
the older stall / restart suites leave theirs, `b7_` / `b8_` / `b9_` / `b22_`, as before). **`tests/input_hold_b8`: 1 failure (1347 ≠ 1348 ms) — the same on HEAD's own code
(3 of 3 runs in a HEAD archive), not B114's.**

## Files

`companion/party_minigame.py`, `companion/plugins/games.py` (two blocks), `tests/b114_party_minigame_hang/`
(`test_b114.py`, `b114_scenario.py`); `b114_2026-11-16/`: the design and its hash, `b114.diff` (applies on
`8fa398c8`), `tests_b114_state_then_head.txt`, `hang_head_threads.json`, `run_after_b114_summary.json`,
`sha256_before_after.txt`, redact / title checks, `manifest.sha256`; `patches/B114_PARTY_MINIGAME_HANG.md`.
