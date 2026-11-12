# B103 — the mini game's two calls (`PRIVYHUB_H7=1`): design (written before code; hashed)

Queue 2026-11-12AM, item B103. Baseline HEAD `8b43a266`. Written after the settle (`settle/picture.py`,
`settle/picture_results.jsonl`) and after B102's learner (`tools/h7_endscreen.py`, its tests green).

## The picture: the window read in process (built) — settled

PS1 fixture, 60-s windows (`settle/picture_results_first.jsonl`; SNES's windows and RetroArch's screenshot re-measured
with its real folder in the record): no reader 3,600 frames · **the window read in process 3,601 frames, 60 / 60
pictures, 12.1 ms a picture (worst 15.1), ~10 ms of the reader's CPU a picture, the X server +0.25 s CPU a minute,
nothing written** · ffmpeg one-shot window read 3,600 frames, 168 ms and ~80 ms CPU a picture · RetroArch's
`SCREENSHOT` **3,496 frames (104 lost)**, RetroArch +1.2 s CPU a minute, a PNG written per picture into RetroArch's
own screenshot folder (its config folder; with the hub's config, which names no folder) — and RetroArch only.
**Built: the window read in process** — it costs least, loses no frame, writes nothing, and works for every emulator
the hub runs (PS2 and GameCube are not RetroArch).

- The window: the emulator's process (the manager's `process.pid`) → `xdotool search --onlyvisible --pid` → the
  largest window → `xdotool getwindowgeometry --shell` (X, Y, width, height) — the same search the stream's capture
  makes; found once per watch, found again after a failed picture.
- The picture: Pillow's X11 grab (`ImageGrab.grab(bbox=…, xdisplay=$DISPLAY)`, the companion's display) of that
  area; nothing is written; the stream's own capture (ffmpeg x11grab of the window) is not touched.
- B102's reader cuts bars by the spec's aspect and searches small shifts / scales, so the window read need not line
  up exactly with the screenshots the spec was learnt from (the stream's window logs 879 × 720; A's screenshots
  878 × 720).

## The module: `companion/h7_minigame.py` (new), imported only with `PRIVYHUB_H7=1`

`plugins/games.py` imports it beside B99 / B101's modules inside the same `if PRIVYHUB_H7 == "1"` block; absent /
`0`: not imported, neither route exists (today's "Unknown Games plugin action: h7-result" / "Unknown Games plugin POST
action: h7-start", 400), no picture read, no rules folder looked at, `tools/h7_endscreen.py` (numpy, PIL) not
imported. With the flag the module imports `tools/h7_endscreen.py` from the project's `tools/` (the companion already
loads a tool from there for the stream).

### `POST /plugins/games/h7-start[?load=0]` — the mini game's start

1. **Checks (400, one `refused` row each, B101's wording where the same):** "no game is running"; "no end-screen
   spec for this game" (`<rules folder>/<game id>.endscreen.json` absent; one that does not load (bad JSON, arrays
   missing or not matching its sha256) → "the end-screen spec for this game cannot be read: …"); "the stream is not
   up"; "a mini game is already being watched" (a watcher in `watching`).
2. **The load (unless `load=0`)** — B101's load step alone, the same code (`h7_contest.Contest._load` and
   `_core_file`, reused through a small subclass whose rows go to `h7_results` — B101's file not edited): PS1 / SNES only — PS2 / GameCube "not supported yet", N64 "not
   supported yet — a state cannot be loaded into a running N64 game", another system "not supported yet", an unknown
   core folder "not supported yet with this game's core"; "no state for this game's mini game" (`<rules
   folder>/<game id>.state` absent or empty); under the manager's lock (2 s, else "the game is busy (a save or a
   load); try again"); refused if a `.state8` is already there; the state copied to scratch slot 8
   (`<state root>/<core folder>/<stem>.state8`), `LOAD_STATE_SLOT 8`, the answer and RetroArch's own load line within
   1.5 s, no failure line; the scratch removed in every case; a failed load → 503 "the mini game's state did not
   load; the game is as it was". **No clock, no read of memory** — no B99 rule is needed or read.
3. **The watcher begins** (a daemon thread). The answer: `{"ok": true, "watch": "started", "game", "loaded": bool,
   "load_line_ms"}`. With `load=0` the load is skipped (any system; the game is already where it starts) and the
   watcher must see the start class itself.

### The watcher

- Every **1.0 s** (`READ_EVERY`): the game still running and the same (the manager's process / active game under its
  lock, 0.3 s wait — B99's `_running`); not → **`stopped`** with one row ("the game stopped") and the thread ends.
  Then one picture (the source above); a failed picture → one `picture_failed` row, the watcher goes on. Then B102's
  `Reader.read` (the spec's alignment search kept per watch) → B102's `Ended.feed`; with the load done
  `Ended.start_loaded()` first.
- **K = 3** agreeing reads (the spec's `k`): `seen_start` after K start reads (or the load); an end class counts only
  after `seen_start`; `ended` after K reads in a row of the same end class → the state `ended` with the class, one
  row, **the watcher stops reading**.
- It changes nothing in the game: **no command is sent to RetroArch by the watcher** (no pause, save, key, read of
  memory); the start's only command is B101's `LOAD_STATE_SLOT 8`.
- An `unknown` read (the screen, no class close enough) is reported as the current class and logged once per stretch
  (`unknown_screen` row); it never ends the watch.

### `GET /plugins/games/h7-result`

`{"ok": true, "state", "class", "seen_start", "since_s", "reads", "last": {"distances", "margin"}}`:
- `"no_game"` — no game running (with `"stopped"`: the reason, when a watch was ended by the game stopping);
- `"no_spec"` — a game, no spec (or one that cannot be read: `"why"`);
- `"idle"` — a game and its spec, no watch started for it (**added**: the queue's four states do not name this one);
- `"watching"` — `class` = the last read's class (`other`, `unknown`, a class), `seen_start`, `since_s` (seconds
  since the start), `reads`, `last` (the last read's distances and margin);
- `"ended"` — `class` = the end class, `ended_after_s`, the same fields; it stays until the next start or the game
  stops.

### END

The user's END (`POST /plugins/games/stop`, the game stopped) or the game ending by itself → the watcher's next step
sees it → `stopped`, one row; GET then answers `no_game` with `"stopped": "the game stopped"`.

### The log: `logs/games/h7_results.jsonl` (new, beside `h7_reads` / `h7_contests`)

One row per change: `refused` (why), `loaded` (game, load-line ms), `error` (a failed load), `watching` (game,
loaded), `start_seen` (after s), `unknown_screen` (once per stretch), `ended` (class, after s, reads), `stopped`
(why), `picture_failed` (why). No picture is kept by the companion.

## Absent / `0`

Neither route exists; no picture is read; byte for byte against HEAD's companion (`git archive 8b43a266`) through the
real HTTP route: GET `h7-result`, POST `h7-start`, POST `h7-start?load=0` before and after a launch — codes and
bodies equal.

## Tests (`tests/b103_h7_minigame/`; B101's harness: the companion's real HTTP server on loopback; B101's fake RetroArch)

A fake picture source the test scripts (synthetic frames drawn as in B102's tests; a spec learnt from them in the
test and written to the test's rules folder as `<game id>.endscreen.json` + `.npz`), put on the plugin's watcher in
the child. Cases: start → `watching` → the scripted end screen → `ended` with the right class after K reads (and not
before K); an end class shown before any start (`load=0`) not counted; an `other` stretch never ends it; an unknown
screen (1-1) → `ended` not said, `class: unknown` said; no spec (`no_spec`, the start refused); no game (`no_game`,
the start refused); the load's refusals as B101's (no state, the stream not up, PS2 / N64 / another system, a load the
fake refuses → 503 and the fake's memory as before, a load with no line → 503); a second start while watching
refused; END while watching → `stopped` row, GET `no_game`; a failed picture is a row and the watch goes on; **the
fake's command log over a watch: one `LOAD_STATE_SLOT` and nothing else from the watch**; the user's slots 1-3 and
the slot-0 copy byte-equal; one row per change in `h7_results.jsonl`; **flag absent / `0` → today** (HEAD's code vs
this, byte for byte); B99's and B101's suites green in the same work copy. Temp dirs removed.

## Record

`evidence/B103_H7_START_AND_RESULT_2026-11-12.md` + `b103_2026-11-12/` (start files, this design + hash, `settle/`
with the table's numbers, `b103.diff`, tests ×3, mutations, redact / title checks, manifest);
`patches/B103_H7_START_AND_RESULT.md`.
