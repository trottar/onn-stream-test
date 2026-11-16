---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AQ) — the mini game's hand-overs made planned, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1 (either absent → today: the real routes against HEAD 8fa398c8's companion; the stall worker's one new line reads an attribute only the mini-game layer sets). The way back now switches the onn's stream to the board's own window while the title still runs, then stops the title — the title's stop can no longer take the stream. Both ways the recovery is told the capture restart is planned (a window on the recovery, open from the switch to 3 s after it): the client's video stalls and desyncs in it are not taken (no client_stall / desync_pause / stall_handover_v2, no key to the board), and the bitrate controller counts it as no recovery restart (no escalation, no step). A real stall during the match is handled as today. Tests: three mini games back to back with B114's concurrent calls; 3 runs. The real start was not run (it is a stream). Nothing adopted; nothing committed. No title, game id, path or picture in this record
---

# B115 — the hand-overs made planned (2026-11-16)

**Baseline:** HEAD `8fa398c8` + B114. **Design** hashed 21:08:28Z, before B115's code
(`b115_2026-11-16/design.sha256`); no amendment.

## What PP-H3's rows showed

- **The way in** (switched true in 3.588 s): the onn's frames stopped while the capture restarted → three
  `client_stall` (425-533 ms) → `desync_pause` / `resumed` three times on the title.
- **The way back**: the title stopped first; its window's capture ended with it ("the stream is not up"); the onn's
  session stalled → `desync_pause` (**an Escape to the board**) → `stall_handover_v2` at 5.08 s → a full encoder
  restart → `resumed` (Escape) — the board's picture back ~7.2 s after `ended` — and that full start was **the second
  recovery restart at 7,000 within 180 s** (the way in's, through `_recovery_full_start_encoder`, was the first) →
  `escalation_armed` → **7,000 → 5,000**.

## What was built (`companion/party_minigame.py`, `companion/stall_signal.py` one block, `companion/plugins/games.py` one block)

- **The way back:** the watch stopped → the pads' route cleared → **the stream switched to the board** — the stream's
  own start for **the board's pid** (from the set-aside session), with the remembered client and port, while the title
  still runs → **then the title stopped** (the manager's stop; the capture is the board's now) → the board's session
  back. A `minigame_title_stopped` row marks the order. With the stream not up (Home, the bench) — no switch, as today;
  END from the onn and the manager's stop hook — no switch (the session ends).
- **The way in:** the stream's start for **the title's pid** (the process the launch made), not
  `_recovery_full_start_encoder` (which reads the manager's current process and counts as a recovery restart).
- **How the recovery is told:** a **planned-switch window** on the recovery object (`recovery._planned_switch`, a
  `PlannedSwitch`, set only by the mini-game layer): opened just before the stream start for the other window, closed
  **3 s after the start returns** (the onn's first decodable frame of a new stream comes ~0.3-2 s after the host's
  start returns), each switch its own window (two may overlap by their grace), bounded by the switch's own bound + 3 s.
  **Not taken in it:** the client's video-stall datagrams (stall and stall end — the stall worker returns before B8's
  and B12's hooks and before `_enter_recovery`: no `client_stall`, no `desync_pause`, no stall save, no
  `stall_handover_v2`, no key to the board) and its `native-stream-desync` (accepted and answered as today, not acted
  on). One `minigame_switch_window` row per switch when it closes (which way, seconds open, stalls / stall ends /
  desyncs not taken).
- **The bitrate controller is told it is planned:** the new SSRC's blackout as for any restart, but through
  `note_ssrc_change("minigame_switch")` with no clock — **not counted as a recovery restart**: no escalation count, no
  `escalation_armed`, no step.
- **What still counts as a real stall during a window:** the controller's silence (the pads' packets stopping — B2's
  hold at H, the receive loop's 1-s silence; a capture restart never stops the uplink); a stall that outlasts the
  window (the client repeats its stall datagram every 50 ms while stalled: the first after the window closes is taken
  at once); the recovery's own monitor. **Outside the windows nothing changes.**

## Tests (`tests/b115_party_handovers/`, B114's harness and stub; 6 tests, 3 runs in `tests_x3.txt`)

Three mini games back to back (seats 1,2 / 2,1 / 1,2) through the stubbed live stream with the adopted lines on and
B114's concurrent calls; Home / RESUME in the first; a real stall in the third (`handovers_summary.json`):

- **Every hand-over planned and switched:** each mini game's `minigame_stream` rows = minigame switched true planned,
  board switched true planned; **the way back's switch row before `minigame_title_stopped`**; the stub's events: **the
  stream never `down`**, the last start for the board's pid; the board's picture already flowing when the mini game
  closes (0.0 s; under B114 alone: 3.2 s, by the recovery; at the TV: 7.2 s).
- **The recovery out of both:** no `client_stall` / `desync_pause` / `stall_handover_v2` / `encoder_restart` /
  `resumed` row in mini games 1 and 2 (only Home / RESUME's own `session_ended` / `session_started` in the first);
  in the third only the real stall's; **no key to the board** in any; **the client did stall at every restart**: each
  window's row 4-5 stalls and 1 stall end not taken.
- **No escalation, no step:** the bitrate rows across all three: six `ssrc_change` "minigame_switch" and nothing else
  (no `escalation_armed`, no `transition`, no "recovery_full_start").
- **A real stall during a mini game** (the client's video stopping while the title plays, 4 s after the way in's
  switch): `desync_pause` client_stall → **the title paused** (RetroArch's own pause) → frames back → stall end →
  `resumed`; no key to the board.
- **Every route < 2 s while a mini game is on** (`status` 0.60 s max, `native-stream-status` 0.53, the result 0.003,
  Home 0.007, the board's end 0.61, the start 0.005); RESUME's start 0.61 / ready 0.01 with their real answers.
- **Each flag absent → today:** B114's `FlagsAbsentAreToday` on the tree (B114 + B115). **The stall worker** with no
  window attribute: the attribute is never set outside the layer (`LinkDropRecovery` has none; `getattr(..., None)`),
  and its suites are green — the stall signal 12, the stall owner 10, the stall resume 7, the session end 8, B61 14,
  the rewind 13 + 14, the link recovery 16 + 22.

## Measured, and what the onn will see

- **The stub:** each way 0.60 s on the host (its modelled start), every window open 3.6 s (0.6 + 3).
- **The real path (the host's own rows; the real start was not run — it captures the TV's display and sends to the
  client: a stream):** the way in 3.588 s at PP-H3 (a running encoder's teardown, the new encoder and its 0.75-s check,
  the new audio — the same `NativeStreamManager.start` B115 calls); **the way back is now the same kind of start**
  (a running stream's teardown and a new start for the board's window) — expect **~3.6 s** on the host, against PP-H3's
  ~7.2 s to the board's picture by the recovery.
- **The onn:** each way, **the last frame of the old window held** for the host's seconds plus the client's wait for
  the new stream's first decodable frame (~0.3-2 s) — **about 4-5.5 s in all**, the sound paused as long; **no pause
  screen, no Escape to the board, no 5-s hold, no bitrate step.** While the way back's switch runs the title keeps
  running behind its end screen (its sound may play on the hub's own output for those seconds, as the board's does
  during a match).

## Files

`companion/party_minigame.py`, `companion/stall_signal.py`, `companion/plugins/games.py`,
`tests/b115_party_handovers/test_b115.py` (and B114's scenario's three-mini-game mode); `b115_2026-11-16/`: the
design and its hash, `b115.diff` (applies on `8fa398c8` + `b114.diff`), `handovers_summary.json`, `tests_x3.txt`,
`scripts/run_all.sh`, `sha256_before_after.txt`, redact / title checks, `manifest.sha256`;
`patches/B115_PARTY_HANDOVERS.md`.
