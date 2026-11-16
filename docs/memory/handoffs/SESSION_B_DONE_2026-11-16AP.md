# SESSION B — done, 2026-11-16 AP (QUEUE_2026-11-16AP: B110 the hub's mini-game session, B111 the board's hub mini game, B112 a bench way with no client, B113 A's PP-H3 sketched; run 17:56Z-19:10Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (PP-H2 committed in
`0a3d78e2` with queue AP). `privyhub-diag` and its folder untouched; no stream, no companion or keeper restart, no adb,
no sudo, no nft; nothing fetched or installed; nothing written to the drive; nothing of A's opened (the kept H7 folder,
the rules folder, A's working folders); no emulator title started; **Godot headless only**, always in scratch copies
of the board's repo with its own folders redirected; nothing deleted; no picture anywhere. **The board's repo** (now
at `d774402`, the PC side's step-19 fix): **two new files only** (`minigames/hub_minigame.gd`,
`checks/hub_minigame_check.gd`), nothing edited, nothing committed there. The `/tmp/b_q28ap` copy holds companion/,
tools/, tests/, PrivyHub/. Nothing adopted; nothing committed in either repo.

## What was found and built

- **B110 — BUILT** (`evidence/B110_PARTY_MINIGAME_SESSION_2026-11-16.md`), routes behind **both** `PRIVYHUB_PARTY=1`
  and `PRIVYHUB_H7=1` (the bench word of B112 behind `PRIVYHUB_H7=1`; either absent → today byte for byte):
  `party-minigames`, `party-minigame-start`, `party-minigame-result`, `party-minigame-end`. The board's session set
  aside while the title runs beside it (the board keeps running, no key); the seats' pads routed in the bridge (seat
  a → port 1, seat b → port 2, others dropped; cleared after); **the onn's stream switched by the recovery's own full
  start** (a capture restart for the other pid — the onn's session never ended; the last frame held ~1-2 s, the sound
  paused as long; the board's sound back on the hub's own output while the title plays); B103's watch with the kept
  begin state; the result **in the order of the seats given**, or `given_up` (not recognised, an unknown screen 30 s,
  15 minutes) — never a guess; Home → the title paused, no board key; END → the title stopped, then the board by F10;
  the hub ends it itself if the board dies or stops asking. Tests 13 (3 runs green; B108 / B103 / B105 / B90 / the client contract / PS2 / GameCube green), mutations 12 / 12 (the first run 11 / 12: a check that the title runs at `playing` was missing, added).
- **B111 — BUILT** (`evidence/B111_PARTY_BOARD_ADAPTER_2026-11-16.md`): `minigames/hub_minigame.gd` (sha256
  `644f0541…`) — `play(players)` asks the hub, picks seeded, starts with each player's own pad as the seat, **keeps the
  board from reacting to the pads with a node of its own that swallows joypad input while it waits** (keys pass, so
  END's F10 still works; no existing file edited), returns the hub's scores or a draw with one line in the board's log;
  `checks/hub_minigame_check.gd` (sha256 `de4c9db0…`) — **PASS (20 assertions)** with its own stand-in hub; from this
  repo, under Godot headless against this repo's fake hub, PASS (14; the calls checked by the fake). **The PC side: no
  line needed for the picker** — commit the two files (with Godot's `.gd.uid` files for them).
- **B112 — BUILT** (`evidence/B112_NO_CLIENT_BENCH_2026-11-16.md`), behind `PRIVYHUB_H7=1`, loopback only, refused
  while a client's stream is up, never touching the adopted audio line or the client's identity: `POST bench-release`
  (a launched game's pause released with no stream), `h7-start?bench=1`, `party-minigame-start?…&bench=1`. Tests 7 (3 runs green), mutations 5 / 5.

## What I would change (not done — the queue is the task)

1. **The picture's hand-over** is a capture restart (~1-2 s of the last frame held) — the cheapest with what exists,
   but not yet seen on the onn. A capture that follows a window id given at run time (no restart) would cut it; not
   built.
2. **Three joins for the user** before a hub mini game: the onn's hold, the board's hold, the title's own character
   select. One join needs the onn's join to seat the board's players directly (the board's change) — the title's
   select stays the title's.
3. **The bench and the board's script:** the script's start carries no bench word, so on the bench (no stream) it ends
   in a draw. A hub-side bench setting (rather than a word per call) would let the board's own script run the whole
   path with nobody at the TV — not built (the queue asked for a word per call).
4. **A shorter time limit by a bench word** for PP-H3's give-up case — not built; part 1 waits the 15 minutes.
5. **The board on the PC** draws every time the picker draws the hub mini game (no hub there); harmless, but the PC
   side may prefer it offered only on the hub.

## A — PP-H3, a mini game on the emulator from inside the board (B113; two parts, part 2 only if part 1 is fully met)

T88 = the 2-player PS1 title of H7 (its version-2 spec and kept begin state in the rules folder). No title, character
name, game id, serial or path in any record; no picture in git.

### Part 1 — unattended, no user (B112's bench), ~30 min (15 of them the time limit's wait)

**Stage 1 (pre-registered after it):**

1. **Preconditions:** this repo's HEAD with queue AP committed and the tree clean; **the board's repo with the two new
   files committed by the user** (`git -C <board repo> log -1 -- minigames/hub_minigame.gd` shows a commit; else stop:
   "YOU, now: commit the board's two new files first"); only the companion and `privyhub-diag`; no game; eighteen
   lines, `--check` ok.
2. **The sidecar** in the rules folder: `<T88 id>.party.json` = `{"players": 2, "scores": {"end_P1": [1, 0],
   "end_P2": [0, 1]}}` (the spec's end classes; port 1 = player 1's side). The board's config file as PP-H2 left it
   (renderer `gl_compatibility`).
3. **The bench flags for the task only:** B99's `.conf` (`PRIVYHUB_H7=1`) and PP-H2's party drop-in
   (`PRIVYHUB_PARTY=1`) → the companion's drop-in folder; `systemctl --user daemon-reload`; `systemctl --user restart
   privyhub-companion`; MainPID owns 8765; **twenty** lines.
4. **Before:** the saves listing (161 at PP-H1 / PP-H2; T88's slots; no `.state8`); the pictures folder's count and
   bytes; `logs/games/party.jsonl` line count.
5. **Pre-registration hashed.**

**Stage 2 — the run** (`H=http://127.0.0.1:8765/plugins/games`):

6. **The board by itself:** `curl -s -m 120 -X POST "$H/launch?id=<the board's id>"` (from `curl -s
   "$H/games?system=party"`) → `active`, `paused`; `curl -s -X POST "$H/bench-release"` → `"released": true`.
7. **The list:** `curl -s "$H/party-minigames"` → **one entry, `"players": 2`**, an `mg_…` id (call it TOKEN).
8. **Seats [1, 2]:** `curl -s -X POST "$H/party-minigame-start?id=$TOKEN&seats=1,2&bench=1"` → `"starting"`; poll
   `curl -s "$H/party-minigame-result"` once a second → **`playing`, `recognised` true** within 10 s; the title's
   window in front: `xdotool getactivewindow getwindowpid` = the RetroArch pid (`pgrep -f RetroArch`), both windows
   1920 × 1080; rows `minigame_route` {"1": 1, "2": 2}, `minigame_stream` "switched": false ("the stream is not up").
9. **The end P1 state by hand** (H7-V3 step 10, unchanged): the title's RetroArch command port from its launch row
   (`network_cmd_port`); `cp <kept end P1 state> "<its state folder>/<stem>.state8"`; `python3 -c "import socket;
   s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.settimeout(2);s.sendto(b'LOAD_STATE_SLOT 8',('127.0.0.1',
   <port>));print(s.recv(256).decode())"` → `LOAD_STATE_SLOT 8`; the load line in RetroArch's session log; remove
   the scratch copy → **`ended`, `end_P1`, `"scores": [1, 0]`** within 8 s.
10. **The end:** `curl -s -X POST "$H/party-minigame-end"` → `"ended": true`; **RetroArch gone** (`pgrep -f
    RetroArch` empty), the board's window active again, `curl -s "$H/status"` → `launch_kind` godot; a second end →
    `"again": true`.
11. **Seats [2, 1] with the end P2 state:** step 8 with `seats=2,1`, step 9 with the kept end P2 state → **`ended`,
    `end_P2`, `"scores": [0, 1]`** (port 2 = seat 1 won: the scores follow the order given — seat 2 first, 0) → step 10.
12. **The give-up by the time limit:** step 8 again, leave the select screen up, poll once a minute → **`given_up`, "no
    end within 900 s"** after 15 minutes → step 10.
13. **The board's own script against the live hub, headless** (no window): a driver off both repos — `extends
    SceneTree` / `func _initialize(): _go()` / `func _go(): await process_frame; var m =
    load("res://minigames/hub_minigame.gd").new(); var s := Node.new(); root.add_child(s); m.stage = s; print("DRIVER ",
    await m.play([{"index": 0, "name": "A", "coins": 0}, {"index": 1, "name": "B", "coins": 0}])); quit(0)` —
    `GODOT --headless --path <board repo> --script <driver>` (Godot's folders redirected to a scratch folder) → on the
    bench its start carries no bench word, so the hub gives it up at once: **expected `PrivyParty: hub mini game: a
    draw: the hub gave it up (the mini game did not start: the stream is not up)` and `DRIVER [0, 0]`**, RetroArch
    gone after (the live give-up → draw path; the whole path waits for part 2's stream).
14. **The board quit:** `curl -s -X POST "$H/stop"` → `party_exit` `"quit 0"`.
15. **After:** the saves listing before = after, no `.state8`; the pictures folder unchanged; the party rows
    (`minigame_*`) copied.

**Pre-registered:** steps 7, 8, 9, 10, 11, 12, 13 and 14 each as stated (the scores exactly [1, 0] and [0, 1]); no
key to the board between any `minigame_playing` and `minigame_end` row (no `pause` / `resume` / `quit` row there);
nothing of the user's touched. **All met → part 1 MET → part 2 may be offered.**

### Part 2 — the sitting (~12 min at the TV; only if part 1 is fully met)

The user with the onn and two pads paired to the onn over Bluetooth, as always; **nothing asked of the user on the
hub**; every message to the user starts **"YOU, now:"** and is a complete step — the screen, the entry, the button —
naming **only what the onn will offer, read from the hub at stage 1** (as PP-H2's `onn_offers.md`); the stages by the
user's messages; A never holds a turn while the user plays (the watchers run from stage 2's start). Stage 1 as part 1's
1-5 plus PP-H2's stage 1 (adb, the APK read back, the onn's offers), and the watchers: the status, `tail -F
logs/games/party.jsonl`, the board's own log (`logs/games/<ts>-party.log`), the recovery log.

- **"YOU, now: on the onn's PrivyHub home, open Games, then [the board's entry's exact name]. Press OK on its one game.
  Choose 'Launch on Companion' and press OK, then 'Start Fresh' and OK. When 'Hold any button to join' shows, hold ✕
  on the first pad for about two seconds — until the board shows a first player — then the same on the second pad.
  Then tell me 'ready'."**
- **"YOU, now: start a game in the board's lobby with the first pad and play on. If the board plays its own
  button-mash game, play it and go on. When the TV changes to the other game's character select screen with 00 – 00,
  each of you pick a character and confirm, and play one match to its end — Player 1 should win. Once during the
  match, press Home on the first pad (the bar RESUME PLAYING · SAVE · LOAD · END appears), then choose RESUME PLAYING
  and press OK. When the board is back on the TV, tell me in one line who won the match and whom the board gave the
  win to."**
- **"YOU, now: play on in the board until the TV changes to the other game again; pick characters and play one match —
  Player 2 should win. When the board is back, tell me in one line who won and whom the board gave the win to."**
- **"YOU, now: press Home on the first pad, move to END and press OK. Tell me 'ended'."**

**Pre-registered, nothing perceptual:** for each match **the hub's result = the user's winner** (`minigame_ended` with
the class and scores; seats as the board sent them) **and the board's own log crediting that seat** (`PrivyParty: hub
mini game: scores [..] for seats ..`); **the onn's stream session never ended across the hand-overs** (no
`native-stream-stop` / session end between `minigame_start` and `minigame_end` but the user's Home; two
`minigame_stream` rows "switched": true per match) and **how long the picture took to change each way** (the rows'
seconds, and the client's own report if it has one); **no key reached the board during a match** (no board `pause` /
`resume` row between `minigame_playing` and `minigame_end`; Home's pause the title's); **Home paused the title and
RESUME resumed it**; END quit the board by F10 (exit 0); the saves before = after; no `.state8`. All met → **MET**.

### The close (both parts)

Both drop-ins removed; `systemctl --user daemon-reload`; the companion restarted (MainPID owns 8765); **eighteen**
lines, `--check` ok; the routes gone (`curl -s "$H/party-minigames"` → 400 "Unknown Games plugin action:
party-minigames"; `curl -s -X POST "$H/bench-release"` → 400 "Unknown Games plugin POST action: bench-release"); no
board, Godot or RetroArch process left. The sidecar stays in the rules folder (off the repo).

### The record

`evidence/PP_H3_<date>.md` + `pph3_<date>/`: `pre/`, `part1/` (each step's answer, the party rows, `cells.md`),
`part2/` (only if run: `onn_offers.md`, the user's lines verbatim, the party rows, the board's log lines, the stream
rows, `cells.md`), `close/`, `preregistration.md` + `.sha256` per part, title / redact checks, `manifest.sha256`.

## Files

B110: `companion/party_minigame.py`, `companion/plugins/games.py`, `companion/games/emulator_manager.py`,
`companion/native_session_io.py`, `tests/b110_party_minigame/`, `evidence/B110_…` + `b110_2026-11-16/`,
`patches/B110_PARTY_MINIGAME_SESSION.md`. B111: the board's `minigames/hub_minigame.gd`, `checks/hub_minigame_check.gd`
(new, uncommitted), `tests/b111_party_board/`, `evidence/B111_…` + `b111_2026-11-16/`. B112: `companion/h7_minigame.py`,
`companion/plugins/games.py`, `companion/party_minigame.py`, `tests/b112_no_client_bench/`, `evidence/B112_…` +
`b112_2026-11-16/`, `patches/B112_NO_CLIENT_BENCH.md`. Then `docs/KNOWN_ISSUES.md` (one line), `docs/ROADMAP.md` (one
paragraph after PP-H2), `logs/b110_|b111_|b112_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`, this file.
