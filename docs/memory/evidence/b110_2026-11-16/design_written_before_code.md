# B110 — the hub's mini-game session: the design, written before code (queue AP)

Baseline HEAD `0a3d78e2`. New: `companion/party_minigame.py`. Hooks: `companion/plugins/games.py` (four routes),
`companion/games/emulator_manager.py` (stash / restore of the board's session, the stop hook),
`companion/native_session_io.py` (the pads' route). **Flags:** the four routes exist only with **both**
`PRIVYHUB_PARTY=1` (the board as the session, B108) **and** `PRIVYHUB_H7=1` (the end-screen watcher and the rules
folder, B103 / B105); either absent → none of them (today's "Unknown Games plugin action"), and every hook is inert
(`None` unless the mini-game layer sets it). Proved byte for byte through the real HTTP routes against `git archive
0a3d78e2`'s companion with each flag absent.

## The settle (from the code)

1. **Two processes at once.** The emulator manager holds one session (`process`, `active_game`, `_launch_kind`, its
   log, …; `launch` refuses while `process` is set; a launch of another id through the route stops the running game).
   **Change:** the mini-game layer **stashes the board's session fields** (the board's process keeps running, owned
   by the stash) and empties them, so the manager's own `launch` starts the emulator title as an ordinary RetroArch
   session (not through the route: no stop of the board, no play count). At the end the emulator is stopped by the
   manager's own `stop` (RetroArch's path), then **the board's fields are restored** — the board never stopped or
   sent a key. While the stash is held, the manager's `stop` (END, another launch, `launch_orphaned`) first ends the
   mini game, then stops the board by its F10 path.
2. **The picture.** The capture is **one window id**, found **by pid** when the stream starts (`xdotool search --pid`,
   ffmpeg `x11grab -window_id`; `native_stream.py:843-1019, 1493-1500`). Switching windows needs a capture restart:
   **the recovery's own full start** (`_recovery_full_start_encoder`: `native_stream.start` with the remembered client
   and port and the manager's current pid; on Linux it stops the running capture / encoder / audio and starts them for
   the new pid; the controller session and the client's target are kept). So: swap the session to the emulator →
   full start → the emulator's window; at the end restore the board → full start → the board's window. **The onn's
   stream session is not ended** (no `native-stream-stop`, no recovery end); the onn sees **the last frame held** until
   the new stream's first frame (a host restart is ~1-2 s, B22 / B24; the client's restart guard releases at the first
   fresh frame), and its sound pauses as long. The recovery does not act (its monitor follows the client's packets,
   which keep flowing). If the stream is not up (the user at Home, or B112's bench) the switch is skipped and the next
   `native-stream-start` captures whichever session is current.
3. **The sound.** One capture per pid: the stream waits for exactly one sink-input of the pid and moves it to its null
   sink; stopping the audio moves it back to its original sink (`native_session_io.py:840-870`). So when the capture
   restarts for the emulator, **the board's sound goes back to the hub's own output** (not streamed) and the
   emulator's is streamed; at the end the reverse. The board's sound is **kept out** of the stream during the match.
4. **The pads.** The onn's packet's player byte p drives virtual pad P(p+1) (`native_session_io.py:2337`); both
   processes read the same four pads; RetroArch's port k reads P(k) (its config: joypad index k−1). (a) **The seats:**
   for `seats = [a, b]` (the board's pads 1-4: player a's pad and player b's) the layer sets **a route in the bridge
   for the mini game's length**: byte a−1 → P1 (port 1), byte b−1 → P2 (port 2), every other byte dropped; the four
   pads written neutral when the route is set and when it is cleared; **cleared at the end** (every end path). (b)
   **The board must not react:** the hub cannot stop Godot reading /dev/input (no file of the board edited; the pads
   are shared). **The hub** sends the board no key during the mini game (Home / RESUME go to the current session —
   the emulator), and the onn's pads all go through the route; **only the board's script** can make the board ignore
   the pads (B111: a node of its own that swallows joypad events while it waits; keys still pass, so END's F10 still
   quits the board).
5. **Home and END during a mini game.** The current session is the emulator, so **Home** (`native-stream-stop`) pauses
   the emulator as any game and stops the stream — no key to the board; **RESUME** (`native-stream-start` /
   `native-stream-ready`) captures and resumes the emulator; **END** (`stop`) → the mini game ended (`given_up`
   "ended from the onn"), the emulator stopped, the board restored, then **the board quit by F10** (B108's path).
   SAVE / LOAD during a mini game → refused as for the board ("…not offered for the board game; nothing was sent.").
6. **The watcher.** The layer uses B103 / B105's own `MiniGame.start("1")` for the title (the kept begin state
   through scratch slot 8, the load line, the scratch removed; the watch; `recognised` within 8 s) and its `result()`.
   **Given up** (a draw to the board, the reason in a row, never a guess): `recognised` false (at once); an `unknown`
   class read for 30 s running; **the time limit: 15 minutes of play** (`PLAY_LIMIT_S = 900`); the watch stopping
   for any other reason. `ended` with an end class → the sidecar's scores.

## The routes (behind both flags; with the board running as the game session)

- **`GET /plugins/games/party-minigames`** → `{"minigames": [{"id": "mg_<12 hex>", "players": n}]}` — every title in
  the library whose rules folder holds a **version-2 spec** (`<game id>.endscreen.json`, `load_spec` reads it), a
  **kept begin state** (`<game id>.state`, non-empty) and a **sidecar** `<game id>.party.json` =
  `{"players": n, "scores": {"<end class>": [n numbers], …}}` naming every end class of the spec, each list n long; any
  file missing or wrong → not listed. The id is an opaque token (a hash of the game id with a per-boot salt); no
  title, game id or path reaches the board.
- **`POST /plugins/games/party-minigame-start?id=<token>&seats=a,b`** → refused plainly unless the board is the running
  session, no mini game is on, the token is listed, the seats are n distinct numbers 1-4; else **at once** `{"state":
  "starting"}`, and a worker: stash → launch the title → pause → route the pads → switch the stream (if up) →
  `MiniGame.start("1")` → release the pause (`resume`) → `playing`.
- **`GET /plugins/games/party-minigame-result`** → `{"state": "none" | "starting" | "playing" | "ended" | "given_up",
  "recognised", "class", "scores", "why", "seats", "since_s"}` — `scores` **in the order of the seats given** (the
  sidecar's list for the class: its k-th number is port k's, and port k is `seats[k]`).
- **`POST /plugins/games/party-minigame-end`** → the watch stopped, the emulator stopped (RetroArch's own stop; the
  user's slots untouched; the scratch slot never left: the load removes it), the route cleared, the board restored,
  the stream switched back (if up); `{"state": <the final state>, "ended": true}`; **a second call** → the same final
  answer, nothing done. **The hub ends it itself** when: the board's process dies (checked each second — then the
  session is over), END / another launch / `launch_orphaned` reach `stop`, or **the caller never comes back** — no
  `party-minigame-result` call for 120 s while playing, or no `end` call 60 s after a final state.
- **Rows:** one per step in the party log (`logs/games/party.jsonl`): `minigame_start`, `minigame_launch`,
  `minigame_route`, `minigame_stream` (which window, seconds), `minigame_watch`, `minigame_playing`,
  `minigame_ended` / `minigame_given_up` (why), `minigame_end` (who ended it), `minigame_restore`.
- **The status the onn polls** stays a game session's throughout (the emulator's while it plays, the board's before
  and after).

## Tests (`tests/b110_party_minigame/`, the real HTTP server on loopback)

B108's stand-in board, B101's fake RetroArch (two processes: the board's real stand-in process and the fake
RetroArch), B103's fake picture source with synthetic tallies and a spec learnt in the test, the stream stub recording
its starts (with the pid each time) and stops, the bridge's route checked with recording pads. Cases: the list (a
title with all three files listed, an opaque id; a title missing any one → not); start → `starting` → `playing`,
`recognised` true → the scripted end → `ended`, scores for seats [2, 4] and [4, 2] (the same class, the scores
following the order); the route for the mini game's length and cleared after; the stub asked for the emulator's pid,
then the board's, no stream stop between; no key to the board during the mini game; `recognised` false → `given_up`,
the emulator stopped, the board's pid captured again; the time limit (shortened in the test) → `given_up`; Home → the
emulator paused (its fake's PAUSE_TOGGLE), no board key; END during a mini game → the emulator stopped, then F10 to
the board; end twice; the board dying mid-game; the slots byte-equal, no `.state8` left; each flag absent → today;
B108 / B103 / B105 / B90 / the client contract / PS2 / GameCube green.
