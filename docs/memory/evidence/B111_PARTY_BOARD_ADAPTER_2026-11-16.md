---
memory_schema: 1
as_of: 2026-11-16
status: BUILT (session B, queue AP) — two new files in the board game's repo (nothing else there changed; nothing committed there — the user commits in that repo): `minigames/hub_minigame.gd`, a mini game to the registry's contract whose `play(players)` asks the hub (loopback HTTP), picks a fitting mini game (seeded from the game's seed), starts it with the players' pads in order, keeps the board from reacting to the pads while it waits (a node of its own that swallows joypad input — no existing file edited), polls the result, ends it and returns the hub's scores — anything else a draw with one plain line in the board's log; and `checks/hub_minigame_check.gd` in the board's style with a stand-in hub of its own: **HUB MINIGAME CHECK: PASS (20 assertions)**; from this repo's tests the same check under Godot headless against this repo's fake hub (14 assertions, the calls checked by the fake). **The PC side needs no line for the picker to offer it** (the picker finds every script in minigames/). No title, path or picture in this record
---

# B111 — the board's side: a mini game that asks the hub (2026-11-16)

**The board's repo:** at `d774402` (the PC side's step-19 fix after B107, pushed since PP-H2), its tree clean before.
**The one exception to "read only":** new files only, under `minigames/` and `checks/` — after B111 its `git status
--short` shows exactly the two below (`board_repo_after.txt`). Godot ran headless only, never in the board's repo
itself: every run in a scratch copy (`git archive HEAD` + the two files), Godot's own folders redirected there,
removed after.

| new file | sha256 |
| --- | --- |
| `minigames/hub_minigame.gd` | `644f05417ce6190c403484c52d3fa967e517a2c74c5450a45f84bb9d320f532b` |
| `checks/hub_minigame_check.gd` | `de4c9db0a134890f6474938e450f02a9537c0279b7d5738bb11b99f13fe7b7b4` |

(Copies in `b111_2026-11-16/board_files/`. Godot makes their `.gd.uid` files the first time the editor opens the
project; the PC side commits those with them.)

## `minigames/hub_minigame.gd`

- **The contract** (`core/registry.gd`, `rules/minigame.gd`): `extends "res://rules/minigame.gd"`; `ID "hub"`, `TITLE
  "On the hub"`, `MIN_PLAYERS 2`, `MAX_PLAYERS 2` (the hub's titles are 2-player for now); `var stage`; `play(players)
  -> scores`, one number per player in the order given.
- **What `play` does:** `GET /plugins/games/party-minigames` (the hub at `http://127.0.0.1:8765`, or the computer's
  `PRIVYPARTY_HUB`) → the entries for this many players → one picked by a `RandomNumberGenerator` seeded from the game's
  seed (`seed_value` of the running scene) and a count of hub mini games played, so the same game gives the same picks
  → each player's **seat = the pad they joined with** (`stage.controls.players[index]`, `padN` → N+1; a keyboard player
  keeps their place number) → `POST party-minigame-start?id=…&seats=a,b` → **a pad gate** in the tree → `GET
  party-minigame-result` once a second → `ended`: the hub's scores (whole numbers back to ints) | `given_up`, the hub
  not answering 10 times, no result in 20 minutes, no mini game on: a draw → `POST party-minigame-end` (whenever it
  started) → the gate removed → the scores.
- **Keeping the board from reacting to the pads — what the board's own code offers:** nothing to switch the pads off
  (`input/controls.gd` reads every joypad event in `_input`; `pause` is Start on any pad). Godot gives input to the
  **last node in the tree first**, so the mini game adds a small node of its own (`PadGate`, process mode Always) as
  the root's last child that **marks every joypad button and motion event handled** while it waits — the board's
  controls never see them; **keys still pass**, so the hub's F10 (END) still closes the board. Removed when the mini
  game ends. No existing file edited.
- **A draw** (everyone 0 — the seam's draw, as `rules/minigame.gd`'s stub) with one line `PrivyParty: hub mini game: a
  draw: <why>` for: no hub, no mini game for this many players, a refusal (the hub's error), a give-up (the hub's
  why), the hub not answering, no result in time, scores that do not fit; a result `PrivyParty: hub mini game: scores
  [..] for seats a,b`.
- **Never blocks the frame:** every wait is an `await` (a timer, an `HTTPRequest`'s signal); the rules wait on it.

## `checks/hub_minigame_check.gd` (the board's style: `HUB MINIGAME CHECK: PASS (n assertions)`, exit 0 / 1)

A stand-in hub of its own (a `TCPServer` on loopback answering the four routes per scenario, every call recorded), or
an outside one named by `PRIVYPARTY_CHECK_HUB`. **Asserts:** a win for player 1 and for player 2 come back as the hub's
scores; the seats in the order of the players given; with the players given the other way round and joined with each
other's pads, the seats are still each player's pad and the scores follow the order given; the mini game ended on the
hub whenever it started (and not when refused); **while it waits the board's controls see no pad** (a witness node
where the controls stand; a joypad press injected during the wait) **and afterwards they do**; the gate gone; a
give-up, a refusal, no mini game for two players and no hub → a draw; it follows the registry's contract, is offered
for two, and the registry lists it. **20 assertions, PASS** (standalone; with an outside hub the five "asked" ones and
"listens" are that hub's to check: 14). A mutation run by hand — the gate never added — fails it on "while it waits
the board's controls see no pad".

## From this repo (`tests/b111_party_board/`, 2; Godot and the board's repo named by `PRIVYPARTY_GODOT` /
`PRIVYPARTY_REPO`, skipped without them)

Godot headless in a scratch copy of the board's repo (its HEAD + the two files; `--import` first): **the check with
its own stand-in hub → PASS (20 assertions)**; **the check against this test's fake hub** (a Python loopback server
answering the four routes per scenario) → **PASS (14 assertions)**, and the fake's own record: the start for the
first win asked with `seats=1,2`, **five end calls** (every started mini game), none for the refused one, the draw lines
for a give-up and for no hub in the board's output. 3 runs in `b110_2026-11-16/tests_x3.txt`.

## What the PC side must do

- **For the picker to offer it: nothing** — `game/minigame_picker.gd` takes every script in `minigames/` whose players
  fit, seeded; this one comes round in 2-player rounds and duels.
- **Commit the two files** (with the `.gd.uid` files Godot makes for them).
- **Known on the PC:** with no hub there, every time the picker draws it the round is a draw ("no hub") in a second. If
  the PC side wants it offered only on the hub, that is its own choice (e.g. leaving it out of the PC's runs); no line
  is needed for the hub.

## Files

`b111_2026-11-16/`: `board_repo_before.txt`, `board_repo_after.txt`, `board_files/` (copies of the two files),
redact / title checks, `manifest.sha256`. The test: `tests/b111_party_board/test_b111.py` (in B110's diff set:
`b111_test.diff`).
