# B54 — hold-to-join replaces the chooser; a third pad brings the multitap at once (design, hashed before code)

Queue: `handoffs/QUEUE_2026-11-08T.md` §B54. The user (HOME-6, 2026-11-08): "the controller connect takes a few clicks
before p1 connects it's a bit awkward"; "a quick press and hold might be a more clear and intuitive check"; a multitap
change "At once". Baseline `0eb115d9` (HOME-6 + the user's commit of the prompt / queue files; the code as `68386b32`);
built in `/tmp/b_q12t_b54`. **Client: `debug.privyhub.player_prompt` absent / empty / junk = ON (hold-to-join), `0` /
`off` = none, as today (no object, no view, no query or report key: the CONFIRMED build's `0`). Host: no flag; the
client's keys are the switch — no `players_joined` / `relaunch` request = today byte for byte.**

## 0. Settled (the code read in place; nothing run on the hub)

**S1. The hold: 500 ms**, measured from the pad's first down of a face button (A / B / X / Y) or Start to the moment
the prompt's tick sees 500 ms elapsed. The prompt's UI tick runs every 50 ms while a hold is in progress (else 200 ms
as today), so a join lands 500-550 ms after the press. Key repeats never start a hold (a hold already started
continues through them); an up before 500 ms cancels it (a tap). Only an **unclaimed** pad's hold joins; a joined
pad's keys are play.

**S2. What a tap does: nothing for an unclaimed pad.** An unclaimed pad holds no player, so there is no port to pass
its press to (B46 did the same for a pad beyond the pick); a joined pad's taps reach the game as today. **The joining
hold itself is not sent to the game** (a Start or a face button held half a second would otherwise pause or act in
the game at the moment of joining). Disclosed as the reading of "the press is passed to the game as today": the
tests check that a joined pad's tap reaches its slot and an unclaimed pad's tap claims nothing.

**S3. The launch's ports: `players_joined`.** The onn keeps the title's highest joined count (a private preference,
a new file `privyhub_players_joined`, keyed as B46 by sha256 of the game id, 12 hex) and sends `&players_joined=N` on
the launch. The host maps **1 / 2 → two ports** (B46's plan for 2), **3 / 4 → the multitap** (B46's plan for 4).
B46's plan for 1 (port 2 off) is not used by a hold-to-join launch: one player joining at the last launch must not
cost a relaunch when a second pad holds today (B46's own finding: an unclaimed port sends nothing). Disclosed as the
one reading of "1 / 2 / multitap 4 as B46". The old `players_chosen` is still accepted exactly as B46 (an older APK).
`ports_set.source`: `join` (a launch from `players_joined`), `relaunch` (the mid-session change), B46's `launch` /
`metadata` otherwise.

**S4. The mid-session relaunch ("at once").** RetroArch cannot change a port device or a core option mid-session
(B46 S2), so the companion **stops the core and launches the same title with the new ports**. The encoder captures
the core's own X11 window (`x11grab_window` by PID), so it is restarted on the new window; the **controller session
stays up** (`NativeStreamManager.stop()` stops the stream only; `end_game_session` is not called).
- **On the TV: the paused frame**, with the client's gate overlay reading **"Setting up 4 players…"** / "The game
  restarts with four controller ports and comes back where it was". The decoder keeps the last frame (the link
  recovery's way: the gate is re-entered with nothing torn down); then the new encoder's frames pass the same gate
  (6 clean ticks) and `native-stream-ready` resumes the core. No "Launching…" screen (that is the Games screen's).
- **The host's sequence** (`native-stream-relaunch-ports?players=4&players_joined=3`, POST):
  1. refuse unless a game is active, the stream's client is remembered, the target differs from the session's ports,
     the system has a multitap (ps1 / snes / ps2), and the session is a plain launch (a cheat or mod session is
     refused: its staging is not replayed; disclosed);
  2. `pause()`;
  3. **the state: RetroArch → a relaunch save** (`save_relaunch_state`: the SAVE_STATE_SLOT 0 capture the recovery
     save uses, copied to `<stem>.state.relaunch`, sha256-verified; the user's slots, the slot index and the recovery
     index untouched); **PS2 → none: the title restarts** (B55 lands after B54 in this queue; recorded as `state:
     "restarted"`, `reason: "ps2_no_relaunch_state"`, disclosed; B55's reserved PINE slot is the follow-up);
  4. `native_stream.stop()` (the encoder; the controller stays);
  5. `emulator.stop()` (today's graceful stop, SAVE_FILES first);
  6. `emulator.launch(game, players_chosen=<2|4>)`, the session's `source` then `relaunch`;
  7. with a relaunch save: `resume()`, 1.0 s settle (`RECOVERY_LOAD_SETTLE_S`, D-BASE-R3c2's running-core load: a
     paused load loops mid-FMV), `load_recovery_state_running(source=<the relaunch save>)` (the same staging,
     verification, LOAD_STATE_SLOT 0 and `[State] Loading` line), then `pause()`;
  8. `native_stream.start(<the remembered client and port>, managed_process_id=<the new pid>)` — D-BASE-R3a's full
     start;
  9. answer `{"ok": true, "relaunch": {state, ms per step, total_ms}, "ports_set": {…, "source": "relaunch"}}` and a
     recovery-log row `relaunch_ports` (players, players_joined, state, steps' ms, total, ok).
- **Failures:** the new launch fails → the old ports are launched again (the same state load), `ok: false`, `fallback:
  "previous_ports"`; that fails too → the session ends (`end_game_session`) and the error is the answer (HTTP 503,
  PS1's shape). The state load fails → the title runs from its start, `state: "restarted"`, `load_error` (disclosed).
- **Budget: 15 s from the join to play**, named. Expected ~6-10 s on PS1 (pause 0.2, save ≤ 2, stop ≤ 3, launch 2-3,
  settle 1 + load ≤ 2, encoder ~1, the client's gate ~1.5-2). The row's per-step ms is what A reads at C17.
- **The client during it:** the gate's `recoveryActive` path (no stabilization timeout; the desync detector held, as
  it is while the gate stands) with **no desync post**, and the gate's release blocked until the host's answer (so a
  still frame of the paused old core cannot pass the gate). The POST's read timeout is 30 s. On the answer: success →
  the new `ports_set`, the waiting pad joins as P3 (if still connected), "hold to add Player 4"; failure → "Couldn't
  set up 4 players" for 5 s, no join; either way the gate then releases on the new (or kept) stream's frames.
- **The audio:** as the link recovery's full start (no receiver rebuild); A listens at C17.

**S5. Players carried.** The client's slot map is the client's (`PadSlots`), untouched by the relaunch: P1 / P2 keep
their slots; the host needs nothing to carry them (only claimed slots send). `players_joined` rides on the relaunch
request and every heartbeat.

## 1. Client (`debug.privyhub.player_prompt` absent = ON; `0` / `off` = none, as today)

`PlayerPrompt.kt` rewritten on B34 / B38's slots (B46's chooser removed; disclosed):
- **The opening:** at every start that is not a self-restart (a game's start, every unpause) the slot map is cleared
  and a bottom-centre line reads **"Hold any button to join"**. A self-restart keeps the map (no line), as B46.
- **Joining:** an unclaimed eligible pad holding a face button or Start for 500 ms takes the lowest open slot (a slot
  with no holder, or whose holder is gone), with the 2-s badge `PN`; the line then reads **"P1 joined — hold to add
  Player 2"** (and "P1, P2, P3 joined — hold to add Player 4").
- **Closing:** a 1-player title (host `players` 1, i.e. `player_mode` `single`) closes the join after P1 (more holds
  do nothing); on the session's ports the line closes when every port is taken (P2 on two ports, P4 on four); in any
  case the line disappears 10 s after the last join, and comes back while an unclaimed pad is holding (when a join is
  still possible).
- **The multitap at once:** a hold that would need a port beyond the session's (P3 on two ports) with
  `multitap_available` → the prompt asks the activity for the relaunch (`players=4`); the line reads "Setting up 4
  players…"; other holds are ignored until the answer; then P3 is that pad. No multitap on the system → "No multitap
  on this system — 2 players" for 5 s, no join. (Generic: a session with fewer than two ports and a second pad asks
  `players=2`.)
- **The release** as today: Select + Start held 2 s frees the pad's slot; both keys must be lifted, and a fresh hold
  re-joins.
- **Keys:** a new hook before the gameplay gate takes every eligible pad's key: an unclaimed pad's key is consumed
  (its hold tracked); a joined pad's goes on to the sender. The B46 chooser hooks (left / right / pick, the hat) are
  gone. A stick never joins.
- **Queries / report:** `&players_joined=N` (the joined count) on the start (self-restart: the session's count) and
  every heartbeat, with `pad_claims` as B41 (`slot:p` for a join); `players_chosen` no longer sent. The report:
  `players`, `pad_claims`, **`players_joined`**, **`relaunches`** (count and the last one's answer: ok, state,
  total_ms), `ports_set`, **`join: "hold"`**.
- **The launch:** `&players_joined=N` from the title's highest joined count (the new preference), only with the prompt
  on.

## 2. Host

- `players_session.py`: `parse_joined` (0-4), `ports_for_joined` (1 / 2 → 2, 3 / 4 → 4), `plan(…, source=)`;
  `ports_set` reads a session whose `source` is `launch` / `join` / `relaunch`.
- `plugins/games.py`:
  - the launch: `players_joined` → `players_chosen=<2|4>` and `source: join`; else B46's `players_chosen`; else
    today;
  - the start / heartbeat: `players_joined` → `SlotsLog` (`join: "hold"`, `players_joined`, the labels);
  - **`native-stream-relaunch-ports`** (POST) → `relaunch_ports.run(…)`.
- `relaunch_ports.py` (new): S4's sequence, injectable clock / sleep, the row.
- `pad_slots.py`: `parse_joined`; `with_joined` (each entry's `label`); the rows carry `join: "hold"` and
  `players_joined`; a changed count is a change row. No key = B46's rows byte for byte.
- `emulator_manager.py`: `save_relaunch_state()` (new; RetroArch only); `load_recovery_state_running(source=None)`
  (`None` = today's path exactly).

## 3. Tests

**JVM (`PlayerPromptTest`, B46's 15 replaced — disclosed; fake devices and a fake clock):** a tap → no claim (and a
joined pad's tap reaches its slot); a 500-ms hold → P1 (499 ms → nothing); repeats never start a hold; a second pad →
P2 and the line closes on two ports; a third pad → the relaunch request (players 4), "Setting up 4 players…", the
answer → P3, "hold to add Player 4"; a failed answer → no P3, the note; a 1-player title closes after P1; the release
and a fresh hold re-join (a held Start does not); the 10-s line timeout and its return on a hold; the self-restart
keeps the map; no multitap → the note; the flag (absent / empty / junk / 1 → on, 0 / off → off); off → `PadSlots`
alone.

**Host (`tests/players_session` + `tests/relaunch_ports`):** `players_joined` → the ports (1 / 2 → 2, 3 / 4 → the
multitap, `source: join`); `players_chosen` still B46's; `relaunch_ports` → the call order pause / save / stream stop /
stop / launch(4) / resume / settle / load(source) / pause / stream start, the state round-trip on PS1, the recorded
`restarted` path on PS2 (no save, no load); refusals (no game, same ports, no multitap, cheat session, no client); the
launch failing → the previous ports; the load failing → `restarted`; the rows; `load_recovery_state_running()` with no
source = today's path; the pad rows with `players_joined`, and without it B46's rows exactly.
