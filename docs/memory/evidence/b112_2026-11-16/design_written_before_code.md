# B112 — a bench way to run a game with no client: the design, written before code (queue AP)

Baseline HEAD `0a3d78e2` + B110. **Behind `PRIVYHUB_H7=1` only** (the party mini game's bench word also needs
`PRIVYHUB_PARTY=1`, as its route does); flag absent → today byte for byte through the real HTTP routes against HEAD's
companion. **Loopback callers only** (the address the handler gives the plugin — the socket's source, or a
session's declared endpoint, which is never loopback: a session's caller is always refused), and **refused whenever a
client's stream is up** (`native_stream.status()["active"]`). **Never touches the adopted audio line or the client's
identity:** no stream is started; nothing declares a codec; no session is made.

## Why (H7-V3's code read, settled again)

With no client: a launch is paused (`plugins/games.py:3711`); `native-stream-start` is refused by the adopted audio
line (no signed opus declaration for loopback); `native-stream-ready` is the only resume and needs the stream; and
`h7-start` refuses "the stream is not up". **What the stream is needed for:** the onn to see and hear the game and to
send its pads, and — for the watcher — only as a guard that a client is there (the watcher reads the game's window
itself: Pillow's X11 grab, never the stream). **What is skipped without it:** the picture and sound to the onn, the
pads from the onn (none), the recovery's monitor (it starts at `native-stream-ready`), the mini game's stream switch.

## What is built

- **`POST /plugins/games/bench-release`** — releases the running game's pause with no stream: the manager's own
  `resume` (RetroArch: PAUSE_TOGGLE; the board: its first release, no key). Refused: a non-loopback caller ("the bench
  is for loopback callers only"), a client's stream up ("a client's stream is up: not on the bench"), no game. A row
  `bench_release` in `logs/games/h7_results.jsonl`.
- **`POST /plugins/games/h7-start?bench=1`** — B103 / B105's start without the stream check, for a loopback caller
  while no client's stream is up (else the same refusals); `bench` in the `watching` row.
- **`POST /plugins/games/party-minigame-start?…&bench=1`** — the mini game with no stream: the switch skipped (as
  already when the stream is down), the watcher started with `bench`; the same refusals.
- Absent `bench` → today's behaviour on every route.

## Tests (`tests/b112_no_client_bench/`, the real HTTP server on loopback)

A PS1 title launched with no client (paused) → `bench-release` → the fake RetroArch PLAYING; `h7-start` refused "the
stream is not up", `h7-start?bench=1` → watching, recognised true, ended on the scripted end screen; a party mini game
with `bench=1` and no stream → ended with its scores, no stream start asked; each bench route refused for a
non-loopback caller (the handler's address given as another one) and while a stream is up; the flag absent → the
routes answer as HEAD's.
