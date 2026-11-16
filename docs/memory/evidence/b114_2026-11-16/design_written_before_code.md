# B114 — design, written before code (hashed before the first edit)

Baseline: HEAD `8fa398c8` (queue AQ; B110-B112 in the tree). Every change below is behind the bench flags: the
mini-game layer (`companion/party_minigame.py`) is imported only with `PRIVYHUB_PARTY=1` **and** `PRIVYHUB_H7=1`;
every new line in `plugins/games.py` sits under `_party_minigame is not None` (None when either flag is absent), so
either flag absent → today byte for byte through the real HTTP routes (tested against HEAD's code).

## 1. The lock, named from the code (the settle)

**The lock:** the manager's `EmulatorManager.lock` (an `RLock`, `games/emulator_manager.py:93`). `party_minigame.py`
`_run` takes it (`with emu.lock:`, "the start, serialised with stop / Home / the onn's reads") and holds it across the
whole start: `_party_stash_begin` → `emu.launch(title)` → `emu.pause()` → the pads' route (`minigame_route`) →
**`_switch_stream("minigame")`** → B103's `runner.start` → `emu.resume()`.

**What it was waiting for after `minigame_route`:** `_switch_stream` → `plugins/games.py`
`_recovery_full_start_encoder()` → `NativeStreamManager.start()` (the stream's own `RLock`, held ~3.6 s) and then, in
its `finally`, **`AdaptiveBitrateLive.note_recovery_restart()` → `with self._lock:` — the live bitrate controller's
`RLock`** (`adaptive_bitrate_live.py:1064`). The bitrate lock was held by an HTTP thread serving the client's
`POST /diagnostics/client-health` (every 2.0 s): `privyhub_service.py:2326` → `observe()` takes the bitrate lock
(`adaptive_bitrate_live.py:930`) → `_ctx()` → `games._adaptive_bitrate_context()` → **`self._emulator.status()` →
`with self.lock:` — the manager's lock, held by the start.** A cycle of two locks:

- the start (thread `party-minigame`): holds **emu.lock**, waits for the **bitrate lock**;
- the report (an HTTP thread): holds the **bitrate lock**, waits for **emu.lock**.

**Why every other route waited:** `status` → `emu.status()` → emu.lock; `party-minigame-end` → `end()` → `with
emu.lock`; `stop` (END) → `emu.stop()` → emu.lock; `native-stream-stop` (Home) → `emu.status()` → emu.lock; every
later client-health report → the bitrate lock; the recovery's stall worker → `_enter_recovery` → `pause_game` =
`emu.pause` → emu.lock (its state set to PAUSED_RECOVERING before the call, its `desync_pause` row written after it —
so no row, and its give-up came exactly 120 s later: 20:29:20.6Z → 20:31:20.6Z). 208 of 214 threads on a futex = the
pile of these. `party-minigame-result` takes only the layer's own `self._lock`, which the cycle did not hold — **its
time-out in A's record is not explained by the code read** (A's watcher may have waited behind its own `status`
call); the test settles it by timing `result` on its own thread during the hang.

**Why match 1 passed and match 2 did not (the real difference, from the rows):** the cycle closes only if a
client-health report enters `observe()` while the start holds emu.lock **and the stream's lock is free** (a report
arriving while `NativeStreamManager.start` runs blocks first on the stream's lock in `_native_stream_status()`,
before the bitrate lock, and the start's `finally` then wins the bitrate lock). That window is
`minigame_start` → the stream start's own lock: the launch (~1.1 s), the pause, the route, `_recovery_stream_active()`
and `emulator.status()` — about 1.2 s; the reports come every 2.0 s. The bitrate log
(`logs/games/adaptive_bitrate_shadow.jsonl`): **match 1** — reports at 20:25:35.998Z and the next ~37.99Z; the start
at 36.578Z, the route at 37.763Z, the stream's lock taken right after → the 37.99Z report hit the stream's lock (no
cycle), `ssrc_change` written at 41.355Z (the start's `finally`). **Match 2** — reports at 20:29:15.410Z, 17.447Z
and the next ~19.46Z; the start at 18.276Z, the route at **19.448Z** → the 19.46Z report reached `observe()` before
the start took the stream's lock (the report's own `_native_stream_status()` ran first), took the bitrate lock and
waited on emu.lock; the start ran the stream start and blocked in its `finally` → **no `ssrc_change` row, no
`minigame_stream` row, no sample row after 20:29:17.447Z.** The ffmpeg count (2 at 85-94 % CPU from 20:29:22Z) shows
the new encoders were running: the start itself finished; only its `finally` hung. **The recovery's restart after
match 1 was not the cause; it only moved the reports' phase** (from x.998 to x.4xx at its 20:27:40.85Z restart),
which put match 2's route 12 ms before a report. A ~60 % chance per start (1.2 s of every 2.0 s).

**The same cycle on the way back:** `end()` holds emu.lock across `_switch_stream("board")` — the same `finally` —
so a way back with the stream up could hang the same way (match 1's did not switch: the stream was already down).

## 2. The test that hangs on HEAD (`tests/b114_party_minigame_hang/`)

Through the real HTTP server on loopback in a child process (B110's harness: B108's stand-in board, B101's fake
RetroArch, B103's fake pictures), with the hub's own adopted lines that matter on: `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`,
`PRIVYHUB_LINK_RECOVERY=1` (the stall signal, the stall owner, the holds), `PRIVYHUB_RESTART_FAST=1`,
`PRIVYHUB_RESTART_FAST_UNLOCK=1`, plus `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1`. **The stream stub extended** to model
what the real stream does that B110's did not: **its own `RLock`** held across `start` (a modelled teardown + new
encoder, scaled), `stop`, `status`, `recovery_restart_encoder` and `adaptive_level_transition`; the capture **bound
to the process it was started for** — when that process ends, the stream goes down and stays down until the next
start (the real `_reap_locked` → `_stop_locked`); the live bitrate controller re-bound to the stub (its serial lock =
the stub's lock). **A client thread** as the onn: `POST /diagnostics/client-health` every 0.1 s (the real
`observe()` path; 20× the onn's rate so the window is always hit), `native-stream-heartbeat` every 0.25 s with the
real output age (the time since the stub last "sent a frame"), and the client's **stall datagrams** (PHS1, through
the real `StallSignal.on_datagram` → its worker → `_enter_recovery` → `emu.pause`) whenever frames stop for ≥ 400 ms
(the capture restarting, or the stream down), a stall end when they resume. The recovery's own monitor runs (the
stall owner's `stall_handover_v2` shortened to 1.0 s; its full encoder restart through
`_recovery_full_start_encoder` → the stub's lock → the bitrate lock). **Other threads throughout:** `status` and
`party-minigame-result` every 0.1 s, each answer's latency recorded; Home (`native-stream-stop`) and RESUME
(`native-stream-start` + `native-stream-ready`) during a match; END (`stop`) at the close. **Two mini games back to
back** through the live (stubbed) stream. **The bound:** each mini game must reach `playing` within 25 s and `ended`
within 40 s; on a miss the child writes every thread's stack (the waiters named) and leaves with `hung: true` — the
suite fails, it does not hang (the parent's own timeout too). **Expected on HEAD + B110-B112: hung** (the start stuck
after `minigame_route`, `status` timing out); after the fix: both mini games ended, every answer within 2 s.

## 3. The fix (properties stated, each tested)

**P1 — no lock across a launch, a stream start or stop, or any wait on another thread.** The layer's own
`self._lock` guards only its fields (never held across a call). **The start no longer holds emu.lock**: each
manager call takes the manager's lock for that one call only (`_emu_call`: acquire with a 0.2-s timeout in a loop
that checks for an END, re-check under it, call, release) — the manager's lock is held across the manager's own
launch as today, never across a stream call, a bitrate call, the watch's start or a wait on another thread. **The
stream switch runs on its own helper thread with no lock held** and is waited for at most `SWITCH_LIMIT_S` (15 s; a
miss → `"switched": false`, "the switch did not finish within 15 s", and the mini game given up). The way back the
same (no emu.lock around it). The bitrate note for a mini game's switch is taken with nothing else held. Tested: the
hang test passes; a check that no thread holds emu.lock while inside the stream stub's start (the stub records
`emu.lock._is_owned()` from the starting thread — must be false); the stub's start, stop and the bitrate lock
asserted free of emu.lock.

**P2 — every route answers within 2 s whatever a mini game is doing.** While a mini game is on (not closed):
- **`status`** (and `native-stream-status`): each part read with a bounded wait (the manager's lock, the stream's
  lock, the recovery's lock: 0.5 s each); a part that cannot be had is the **last snapshot** of that part (refreshed at
  every successful read), and the answer carries `"snapshot": [the parts served from it]`. No mini game → today's code
  path unchanged.
- **`party-minigame-result`**: from the mini game's own state (the layer's lock, never held across a call).
- **Home (`native-stream-stop`), END (`stop`), the board's `party-minigame-end`**: **taken at once** — put on the mini
  game's own ordered queue and answered at once (`{"ok": true, "taken": "home" | "end", "minigame": <state>}`; the
  board's end: today's keys with `"ended": true` once its end is taken); **acted on in order** by the mini game's actor
  thread (the start's steps first, then each taken call in the order taken).
- **RESUME (`native-stream-start`, `native-stream-ready`)**: taken at once onto the same queue, in order behind a
  taken Home; the route answers with **its own real answer** when its turn has run (the onn needs the started
  stream's answer — `"active": true` — so it cannot be answered before the start; its own start's seconds are today's,
  not the mini game's). Bound: 25 s (the onn's read timeout is 30 s).
- Tested: `status` / `party-minigame-result` latencies all < 2 s through two (B115: three) mini games, including during
  the switches, the way back, a stuck start and END; Home / END answered < 2 s and acted on in order (Home's pause
  of the title, then RESUME's start and ready, in the order sent).

**P3 — a mini game stuck in `starting` is given up by the hub itself.** The watch thread runs from the start (not
after it). A mini game still `starting` after **`START_LIMIT_S` = 30 s** (a normal start is ~5 s: launch ~1 s, switch
~3.6 s, the load) is given up: `given_up` "the mini game did not start within 30 s" — **a draw to the board** — and
the end runs **without the actor** (it may be the stuck one): the watch stopped, **the title stopped** (the manager's
own stop if its lock can be had within 2 s, else the title's process ended directly), the route cleared, the board's
session back, the stream switched to the board (bounded). If the stuck step returns later, the actor sees the mini
game closed and undoes what that step made (a title it launched is stopped). Tested: a start stuck in the stream
switch (the stub's start blocked) and a start stuck in the watch's start (blocked) → `given_up` within the (test's
shortened) limit, the title gone, the board's session back, the route cleared, routes answering < 2 s throughout.

**P4 — END from the onn always works**: during `starting`, `playing`, a hand-over (the switch in either direction) and
a stuck start. END is taken at once (answered < 2 s); the actor ends the mini game in order if it is free within
`STEP_GRACE_S` = 3 s, else the end runs without it (as P3); then today's stop route body runs in the same order (the
recovery's and the bitrate's session end, the board's stop by F10 — exit 0 — and the stream's session end). Tested:
END in each of the four phases → the title gone, the board gone (F10), the stream ended, `status` → not active, every
route < 2 s.

**The manager's stop hook** (another launch, `launch_orphaned` — callers already holding the manager's lock): the
mini game ended **inline with no wait on the actor or the stream** (the manager's own calls direct, re-entrant; no
switch: the session ends), then the board's stop as today.

**Rows** (party log): today's `minigame_*` rows, plus `minigame_taken` (what was taken: home / resume / end / board
end, in order) and `minigame_stuck` (the step, its seconds) — field names and numbers only.

## 4. Not changed

The manager, the stream, the recovery and the bitrate controller (B115 adds the planned switch); the board's files
(B116). Flags absent → today (test: each flag absent, the real routes' answers against HEAD's code).
