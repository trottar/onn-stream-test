---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AP) — the hub's party mini game behind PRIVYHUB_PARTY=1 **and** PRIVYHUB_H7=1 (either absent → today byte for byte through the real HTTP routes against HEAD 0a3d78e2's companion): with the board as the game session, `party-minigames` lists the titles with a version-2 spec, a kept begin state and a sidecar (ids opaque); `party-minigame-start` sets the board's session aside (it keeps running), launches the title beside it, routes the seats' pads to ports 1 and 2, **switches the onn's stream to the title by the recovery's own full start (the session not ended; the last frame held ~1-2 s)**, starts B103's watch with the kept begin state and releases the pause; `party-minigame-result` → starting / playing (recognised) / ended (class, **scores in the order of the seats given**) / given_up (why); `party-minigame-end` stops the title, clears the route, gives the board its session back and switches the stream back — safe twice, and done by the hub itself if the board dies, END is pressed or the caller does not come back. Tests through the real HTTP server on loopback: 13, 3 runs green; B108 / B103 / B105 / B90 / the client contract / PS2 / GameCube green; mutations 12 / 12. Nothing adopted; nothing committed. No title, game id, path or picture in this record
---

# B110 — the hub's party mini game (2026-11-16)

**What the user gets** (when PP-H3 proves it): the board reaches a mini game → the TV shows the emulator title at its
start, the two players' pads drive it → the match ends → the hub knows who won from the title's own screen → the TV
is back on the board, which goes on with that result. **Baseline:** HEAD `0a3d78e2`. **Design** hashed 18:09:48Z,
before code (`b110_2026-11-16/design.sha256`); no amendment.

## The settle (from the code)

1. **Two processes at once.** The manager holds one session and a launch through the route stops the running game.
   **Built:** the mini-game layer **sets the board's session fields aside** (`_party_stash_begin`: the board's process
   keeps running, owned by the stash), so the manager's own `launch` starts the title as an ordinary RetroArch session
   (not through the route: nothing stopped, no play count); at the end the title is stopped by the manager's own
   `stop` and **the board's fields come back** (`_party_stash_end`) — the board never stopped and never sent a key.
   While the stash is held the manager's `stop` (END, another launch, `launch_orphaned`) runs the layer's hook first.
2. **The picture.** The capture is one window id found **by pid** when the stream starts (`native_stream.py:843-1019`,
   ffmpeg `x11grab -window_id`). **The switch is the recovery's own full start** (`_recovery_full_start_encoder`:
   `native_stream.start` with the remembered client and port and the manager's current pid; on Linux it stops the
   running capture, encoder and sound and starts them for the new pid — the controller session and the client's target
   kept). **The onn's stream session is not ended** (no `native-stream-stop`, no recovery end); the onn holds the last
   frame until the new stream's first frame (a host restart ~1-2 s, B22 / B24; the client's restart guard releases at
   the first fresh frame) and its sound pauses as long; the recovery does not act (the client's packets keep flowing).
   A `minigame_stream` row says which window and how long the host took. With the stream down (the user at Home, or
   B112's bench) the switch is skipped and the next `native-stream-start` captures whichever session is current.
3. **The sound.** One capture per pid; stopping it moves the old pid's sound stream back to its own sink
   (`native_session_io.py:840-870`). So while the title plays, **the board's sound goes to the hub's own output — kept
   out of the stream** — and the title's is streamed; at the end the reverse.
4. **The pads.** (a) The onn's player byte p drives virtual pad P(p+1) (`native_session_io.py:2337`); RetroArch's port
   k reads P(k). **Built:** a route in the bridge for the mini game's length — `seats = [a, b]` → byte a−1 → P1 (port 1),
   byte b−1 → P2 (port 2), every other byte dropped; all four pads written neutral when it is set and when it is
   cleared; **cleared on every end path**. (b) **The board not reacting:** the hub sends the board no key during the
   mini game (Home / RESUME go to the current session, the title) and cannot stop Godot reading /dev/input (the pads
   are shared; the board's files untouched); **the board's script does it** (B111: a node of its own that swallows
   joypad input while it waits — keys still pass, so END's F10 still quits the board).
5. **Home and END during a mini game.** Home (`native-stream-stop`) pauses the title as any game (RetroArch
   PAUSE_TOGGLE) and stops the stream — no key to the board; RESUME (`native-stream-start` / `native-stream-ready`)
   captures and resumes the title; **END** (`stop`) → the mini game `given_up` ("ended from the onn"), the title
   stopped, the board's session back, then **the board quit by F10** (B108's path). SAVE / LOAD (and the recovery's
   states) during a mini game → B108's refusal ("…not offered for the board game; nothing was sent.").
6. **The watcher.** B103 / B105's own `MiniGame.start("1")` for the title (the kept begin state through scratch slot
   8, the load line, the scratch removed; the watch; `recognised` within 8 s) and its `result()`. **Given up** (a draw
   to the board; the reason in a row; never a guess): `recognised` false (at once); an `unknown` screen for 30 s;
   **15 minutes of play** with no end; the watch stopping; an end class the sidecar does not name.

## The routes (with both flags; the board running as the session)

- **`GET /plugins/games/party-minigames`** → `{"minigames": [{"id": "mg_<12 hex>", "players": n}]}`: every title whose
  rules folder holds a **version-2 spec**, a **kept begin state** and a **sidecar** `<game id>.party.json` = `{"players":
  n, "scores": {"<end class>": [n numbers], …}}` naming every end class of the spec (for T88: `{"players": 2,
  "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}`), and that is in the library. The id: a hash of the game id with a
  per-boot salt — no title, game id or path reaches the board.
- **`POST /plugins/games/party-minigame-start?id=<token>&seats=a,b`** → refused plainly unless the board is the
  running session, no mini game is on, the token is listed and the seats are n different numbers 1-4; else **at once**
  `{"state": "starting", "seats"}`; then (serialised with stop / Home under the manager's lock): set aside → launch →
  pause → route → switch the stream (if up) → B103's start → release → `playing`.
- **`GET /plugins/games/party-minigame-result`** → `{"state": "none" | "starting" | "playing" | "ended" | "given_up",
  "seats", "recognised", "class", "scores", "why", "closed", "since_s"}` — `scores` in the order of the seats given
  (the sidecar's k-th number is port k's, and port k is `seats[k]`).
- **`POST /plugins/games/party-minigame-end`** → the watch stopped, the title stopped (RetroArch's own stop — the
  user's slots untouched; the scratch never left: the load removes it), the route cleared, the board's session back,
  the stream switched back (if up); a second call → the same final answer with `"again": true`. **The hub ends it
  itself:** the board's process dead (checked each tick), END / another launch / `launch_orphaned` (the stop hook),
  **no result call for 120 s while playing**, **no end call 60 s after a final state**.
- **Rows** in `logs/games/party.jsonl`: `minigame_start`, `_launch`, `_route` (port → seat), `_stream` (window,
  switched, seconds), `_watch`, `_playing`, `_ended` (class, scores) / `_given_up` (why), `_restore`, `_end` (by whom).
- **The status the onn polls** stays a game session's throughout (the title's while it plays, the board's around it).

## Tests (`tests/b110_party_minigame/`, 13; the real HTTP server on loopback)

B108's stand-in board (a real process) beside B101's fake RetroArch; B103's fake picture source with synthetic tallies
and a spec learnt in the test; a stub stream recording each start's pid and each stop; a real bridge with recording
pads; made-up user slots 0-3 for the title. Limits shortened in the test (recognised 1.6 s, play 2 s in its case).

- **The list:** no sidecar → empty; a title with all three → listed (`mg_` + 12 hex, players 2, no game id in the
  answer); a second title with no kept state → not listed. **Refusals:** no board running; seats 1,1; an unknown id.
- **Seats [2, 4] and [4, 2]:** `starting` → `playing` (recognised true) → `ended` `end_P1` with scores **[1, 0]** both
  times (the scores follow the order given); end → ended; end again → `again`.
- **The route:** during the mini game {byte 1 → P1, byte 3 → P2}; the onn's players 1-4 pressing: only seats 2 and 4
  reach pads, as P1 and P2; cleared after every mini game.
- **The stream:** for each mini game exactly two starts — the title's pid, then the board's — and **no stop between**.
- **No key to the board** during any mini game.
- **Not recognised** → `given_up` "the title's start screen was not recognised"; **the time limit** → `given_up` "no end
  within 2 s"; after each the board's session back (`launch_kind` godot).
- **Home** during a mini game → the title's PAUSE_TOGGLE, no board key; RESUME → the title; it ends `end_P2` → [0, 1].
- **END** during a mini game → `given_up` "ended from the onn", then F10 to the board, the board gone, no session.
- **The board dying** mid-game → `given_up` "the board stopped", ended by the hub.
- **The user's slots** (4 made-up files) byte-equal after five mini games and at the end; no `.state8` left.
- **Rows:** start, launch, route, stream, watch, playing, ended, restore, stream, end.
- **Each flag absent** (`FlagsAbsentAreToday`: PARTY only, H7 only, neither, H7=0): the list, start, result, end and
  the systems answer **byte for byte as `git archive 0a3d78e2`'s companion** ("Unknown Games plugin action").
- Results: `tests_x3.txt`, `tests_mutations.txt` — **3 runs × 13 green** (with B111's 2 and B112's 7); B108 16, B103 13, B105 12, B90 10, the client contract 5, PS2 93, GameCube 54 OK; stand-ins / Godot / RetroArch left 0; temp dirs 0; **mutations 12 / 12** (the second run; the first, `tests_mutations_first.txt`, 11 / 12 — below).

## Disclosed

- **The picture's change is a capture restart** — not proved on the onn here (the stream is a stub): PP-H3's sitting
  measures what the onn shows and for how long.
- **RetroArch's own stop** (the title's end) flushes its save files as on any stop (`SAVE_FILES`); the user's save
  states and slots are untouched (tested); a memory card is unchanged unless the title saved to it during the match.
- **Twelve HEAD lines changed** (not only added): the seven B108 refusal conditions widened to "or a mini game is
  on", and five lines of the watcher's start and its route for B112's bench word — each inside code reached only with
  the flags. Both diffs apply in order on HEAD (`diffs_apply_in_order.txt`).
- **A start racing an END** (the user pressing END in the ~1-2 s of `starting`): the start holds the manager's lock,
  so END waits for it and then ends both — stated from the code, not tested.
- **The first mutation run missed one** (Q12: the title's pause never released): no test looked at whether the title
  was running once the mini game said `playing`. The check was added (the fake RetroArch not paused at `playing`), the
  suite run once more (`tests_after_q12.txt`: 13 OK; the 3-run batch above ran before it) and all 12 mutations run
  again: 12 / 12.
- The first test run passed at once; a look at its numbers showed the slots check was empty (no slot files) — made-up
  slots were added and the scores kept as the sidecar's integers; then green.

## Files

`b110_2026-11-16/`: start files, the design + hash, `b110.diff` (applies on `0a3d78e2`; B112's applies after it),
`diffs_apply_in_order.txt`, `sha256_before_after.txt`, `tests_x3.txt` (B110, B111, B112), `tests_mutations.txt`,
`scripts/` (`run_all.sh`, `mutate.py`, `mutations.json`), redact / title checks, `manifest.sha256`. Patch note:
`patches/B110_PARTY_MINIGAME_SESSION.md`.
