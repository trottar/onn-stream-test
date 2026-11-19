---
memory_schema: 1
as_of: 2026-11-18
status: FIXED TASK (session A, hardware) — add one party mini game by its code with tools/party_add_game.py (B157). The same task for every title; only the code changes (ADD_GAME_PROMPT_TEMPLATE.txt). Nothing adopted by it
---

# ADD-GAME — one title, by its code, through the tool's five stages

The code (`T` + two digits) is the only name of the title in anything written. The user knows which game it is; the
words the user gives to find it in the library are typed into one command at run time and never written down. **The
tool decides every verdict; you never judge a picture, choose a threshold or edit a rule.** A stage that is not PASS
stops the task.

## Standing rules (all of them, as every A task)

- **The window:** not between 04:30 and 05:30Z (the hub's nightly window), and not within 45 min before it — else
  reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that".
- **Preconditions:** `git status --short` empty but for the prompt files; `grep -c "def cmd_bench"
  tools/party_add_game.py` → 1 and `grep -c "def _winner_entry" companion/party_minigame.py` → 1 — else "YOU, now:
  commit queue BB first, then send the read line again"; only `privyhub-companion` and `privyhub-diag` active.
- **The board's checks** (as PP-H4's stage 1, in a scratch copy of the board's repo, Godot headless:
  `docs/memory/evidence/b145_2026-11-18/scripts/run_check.sh <board repo> 1` and the same with
  `res://checks/step28_quiet_and_covered.gd`): `HUB MINIGAME CHECK: PASS` and `STEP 28 CHECK: PASS`, else "YOU, now: in
  the board's repo pull the PC side's latest, then send the read line again".
- **Replies to the user** begin "YOU, now:" and give one complete step, naming only what the onn or the board offers.
  **Nothing about adb is ever asked at the TV.** Plain words ("a normal game", not test words).
- No title, character name, cheat name, serial, game id, `profile_id`, path, address or picture in any record; the
  tool's own verdicts and pages (`docs/memory/evidence/add_game/<code>/`) are the record, with one short page of yours.
- The users' slots, saves and kept folders: the tool only reads them (it copies the user's slots to its own kept folder
  for the code, off the repo). Nothing deleted by hand. No stream started by you; the companion restarted only by the
  tool's bench and close.

## 0. A title already added (T88, T89)

No saves and no bench (its bench was its own task's part 1). The stages: `register <code> --players … --system …
--result … --rules-players <2|4>` (T88: 2, ps1, winner; T89: 4, n64, places), `learn <code>`, `solo <code>` and its
read, `close <code>`. Everything else as below. The user's words about the host's voice and the board's cover around
the mini game are recorded verbatim in your page — no bar.

## 1. The user's saves (the user's hands; B156)

Ask once, in this order, what the user already knows: **two players or four; who wins is shown how** — a screen that
says which player won (→ `winner`), or a results screen with every player's place in a row (→ `places`; four players
only); **whether the game has things to unlock** (→ a setup: `--setup slot1`, made by the user in Extras → Cheats, and
every save below made inside it; nothing to unlock → `--setup none`); **the words to find it in the library**.

Then the saves, three at a time (the onn's SAVE, slots 1-3; slot 9 and slot 0 are the hub's), each round followed by
`register … --collect role=slot …` (the tool copies them; the user may then save over them):

- **The match, shortest:** one round or one life, items off, the shortest time the game offers — the same settings
  for every save.
- **`begin`:** the screen just before a match, nobody picked yet, nothing moving when nobody presses (two players:
  the select screen; four: the character select screen). Under a setup: its slot 1.
- **`other`:** the middle of a match (a fight, a race) — anything that is not a begin or an end screen.
- **`winner`, n players:** `end_P1` … `end_Pn` — for each player, a match that player won, saved on the screen that
  stays after it and shows who won by player (not by character).
- **`places`, four players:** four matches finished in set orders so every player takes every place — rows `1234`,
  `2341`, `3412`, `4123` (P1's place first) — each saved on its results screen: `end_r1234` …

Line for the user (two players, `winner`, round 1): "YOU, now: set the game to its shortest match (one round, items
off). Save to slot 1 on the select screen before anyone picks; start a match and save to slot 2 in the middle of it;
let P1 win and save to slot 3 on the screen after the match that shows P1 won. Reply ok." Round 2: "YOU, now: play a
match P2 wins and save to slot 1 on the screen after it. Reply ok." (Four players and `places`: the rounds as the
roles above; four people, or the user with four pads.)

## 2. The stages — one command each, the verdict read from its last line

```
python3 tools/party_add_game.py register <code> --players <2|4> --system <ps1|n64|snes> --result <winner|places> \
        --find "<the user's words>" --setup <none|slot1> --collect begin=1 --collect other=2 --collect end_P1=3
python3 tools/party_add_game.py register <code> … --collect end_P2=1          # each further round
python3 tools/party_add_game.py learn <code>
python3 tools/party_add_game.py bench <code>                                    # unattended, ~5 min, flags on
python3 tools/party_add_game.py solo <code>                                     # prints the lines for the user
python3 tools/party_add_game.py solo <code> --read --winner <the seat the user named>
python3 tools/party_add_game.py close <code>                                    # flags off, the companion as found
```

- **register** FAIL "missing: …" → ask the user for exactly those saves (the role's line above), collect, run again.
  Any other FAIL → stop (below).
- **learn**, **bench** → PASS or stop. **bench** needs nobody: no pad, no TV.
- **solo:** pass its "YOU, now:" lines to the user one by one (pads on the onn); when the user says who won, run the
  read with that seat.
- **close** always, last — also after any stop.

**Stop:** one plain sentence — the cell(s) not met and by how much, from the stage's page — then `close`, then "YOU,
now: commit". Never run a stage again with a changed bar.

## 3. The record

The tool's `docs/memory/evidence/add_game/<code>/` (verdicts and pages) and yours,
`docs/memory/evidence/ADD_<code>_<date>.md`: the stages' verdicts in order, the user's words verbatim (titles replaced
by the code), what was disclosed. Then "YOU, now: commit". Nothing adopted: the title is offered by the board only while
both bench flags are on, as T88 and T89 are; adoption is the user's own go.
