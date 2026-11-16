# B115 — design, written before code (hashed before the first edit for B115)

Baseline: HEAD `8fa398c8` + B114 (in the tree, not committed). Behind the bench flags: the mini-game layer is imported
only with `PRIVYHUB_PARTY=1` and `PRIVYHUB_H7=1`; the one line outside it (`stall_signal.py`, the stall worker) reads an
attribute only the layer sets on the recovery (`_planned_switch`, absent → `None` → today's code path), and the desync
route's check sits under `_party_minigame is not None`. Either flag absent → today byte for byte.

## What PP-H3 showed (the rows)

- **The way in** (`minigame_stream` switched true in 3.588 s): the capture restarted for the title's pid; the onn's
  frames stopped → three `client_stall` datagrams (age 425-533 ms) → the recovery's `desync_pause` (the title paused)
  and `resumed` "stall_quiet" three times.
- **The way back**: `end()` stopped the title **first** (the manager's stop), the capture of the title's window ended
  with it (the real stream's `_reap_locked` → `_stop_locked`: "the stream is not up"), the switch found no stream; the
  onn's session stalled → `desync_pause` (**an Escape to the board**: by then the board was the manager's session
  again) → `stall_handover_v2` after 5.08 s → `encoder_restart` method full_start → `resumed` (Escape again) — ~7.2 s
  — and the recovery's full start counted as a **second recovery restart at 7,000 within 180 s** (the way in's full
  start was the first, `note_recovery_restart("recovery_full_start")`) → `escalation_armed` → **7,000 → 5,000**.

## The way back, planned

Order (the board's end, the hub's own ends; not END from the onn and not the manager's stop hook, where the session
ends): (1) the watch stopped; (2) the pads' route cleared; (3) **the stream switched to the board while the title still
runs** — the stream start for **the board's own pid** (from the stash), not the manager's current process (which is
still the title); (4) **then the title stopped** (the manager's stop): the capture is the board's window now, so the
title's end cannot take the stream; (5) the board's session back (`_party_stash_end`). If the stream is not up (Home,
B112's bench) — no switch, as today. If the switch fails or does not finish within its bound, the title is still
stopped and the board's session restored (the recovery then owns the stream as today).

## Both ways: the switch is planned, and the recovery is told

**How the recovery is told:** a **planned-switch window** on the recovery object (`recovery._planned_switch`, set only
by the mini-game layer): opened just before the stream start for the other window, closed **`PLANNED_GRACE_S` = 3.0 s
after the start returns** (the onn's first decodable frame of the new stream comes ~0.3-2 s after the host's start
returns: B22's client numbers), never longer than the switch's own bound + the grace. One row per switch when its window
closes (`minigame_switch_window`: which way, seconds open, stalls and desyncs not taken).

**What is not taken during the window:** the client's **video-stall datagrams** (PHS1 stall / stall end — the stall
worker returns before B8's / B12's hooks and before `_enter_recovery`: no `client_stall`, no `desync_pause`, no stall
save, no `stall_handover_v2`, no key to the board) and the client's **`native-stream-desync`** (accepted, answered as
today, not acted on). **The bitrate controller is told it is a planned switch:** the new SSRC's blackout as today (the
reports right after a restart are not judged), but **not counted as a recovery restart** (`note_ssrc_change` with no
clock: no escalation count, no `escalation_armed`, no step); the way in no longer uses
`_recovery_full_start_encoder` (whose note counts it).

**What still counts as a real stall during it:** the controller's silence (the pads' packets stop: B2's input hold at
H, the receive loop's `controller_silence` at 1 s — a capture restart never stops the uplink); a stall that outlasts
the window (the client sends a stall datagram every 50 ms while stalled: the first one after the window closes is taken
as today, at once); the recovery's own monitor (its give-up, its restarts of a session already recovering). Outside
the windows nothing changes: a stall during the match is handled as today (the title paused — the title is the
manager's session then, so no key reaches the board).

## Measured and stated

The stub's seconds each way (the test's), and from the host's own rows: PP-H3's way in 3.588 s (the recovery's full
start: the old audio's teardown, the new encoder and its 0.75-s check, the new audio); the recovery's full start on
the way back 1.03 s (`stall_handover_v2` 20:27:39.737Z → `encoder_restart` 20:27:40.765Z). **The real start without a
client is not run** — it captures the TV's display and sends to the client's address: that is a stream, which this
queue does not allow. **What the onn will see:** each way, the last frame of the old window held for the switch's
host seconds plus the client's wait for the new stream's first decodable frame (~1-4 s in all), the sound paused as
long, **no pause screen, no Escape to the board, no 5-s hold, no bitrate step**; the way back no longer passes through
a stream that is down (~7.2 s → the switch's seconds).

## Tests (`tests/b115_party_handovers/`, B114's harness with the stream stub and the client)

1. **The way back with the stream up** → `minigame_stream` window board **switched true** (planned), **the title
   stopped after it** (the stub's start for the board's pid comes before the title's process ends; the stream never
   `down`), **no** `client_stall` / `desync_pause` / `stall_handover_v2` / `encoder_restart` / `resumed` row, **no**
   `escalation_armed` / `transition` row, **no key to the board**; the window's row with the stalls not taken > 0
   (the client did stall during the restart: the test shows they were sent and not taken).
2. **The way in** the same (switched true for the title's pid; no recovery row; no escalation; no key).
3. **A real stall during a mini game** (the client's video stops while the title plays, outside the windows) →
   `client_stall` / `desync_pause` as today, **the title paused** (RetroArch's own pause), no key to the board; frames
   back → resumed.
4. **Three mini games back to back** through the stub with B114's concurrent calls (status / result / native-stream-status
   every 0.1 s, client-health every 0.1 s, heartbeats, stalls; Home / RESUME in the first) — all three ended with their
   scores, every hand-over switched true both ways with no recovery row, every route < 2 s while a mini game is on.
5. **Each flag absent → today** (the real routes' answers against HEAD's code) and the stall worker unchanged when the
   attribute is absent (the existing stall-signal suites green).
