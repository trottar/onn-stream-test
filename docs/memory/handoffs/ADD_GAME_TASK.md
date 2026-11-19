---
memory_schema: 1
as_of: 2026-11-19
status: FIXED TASK (session A, hardware) — add one party mini game by its code with tools/party_add_game.py (B157; B162 solo's one-title setting, its title cell, S's listed switches, the in-game saves recorded, the pads' words; B163 rehearse for a title already added). The same task for every title; only the code changes (ADD_GAME_PROMPT_TEMPLATE.txt). Nothing adopted by it
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
  commit queue BB first, then send the read line again"; `grep -c "def cmd_rehearse" tools/party_add_game.py` → 1 and
  `grep -c "def set_only" companion/party_minigame.py` → 1 — else "YOU, now: commit queue BC first, then send the read
  line again"; only `privyhub-companion` and `privyhub-diag` active.
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

No bench (its bench was its own task's part 1). The stages: `register <code> --players … --system … --result …
--rules-players <2|4>` (T88: 2, ps1, winner; T89: 4, n64, places), `learn <code>`, **`rehearse <code>`** (B163),
`solo <code>` and its read, `close <code>`. Everything else as below. The user's words about the host's voice and the
board's cover around the mini game are recorded verbatim in your page — no bar.

**rehearse** runs learn's whole real path — the title started headless on the hub for its pictures, the labels, the
learner, the held-out score, the replays — on the title's kept states (`~/privyhub_h7/<code>/`, read only) into a
scratch rules folder, reads every kept ending with the scratch rules and the real ones, and checks the real rules
folder's every file sha256 before = after; the scratch is removed. ~4-5 min, nobody at the TV. Its page names which
kept state is which role and **what is missing**. **T88's and T89's kept folders have no mid-match state** (`other`),
and the learner cannot learn without one: before `rehearse`, ask the user for that one save — "YOU, now: start this game
from Games the way you always play it (with its Extras setup, if it has one), and in the middle of a match press SAVE
to a slot you don't need (1, 2 or 3). Reply with the slot number." — then `rehearse <code> --collect other=<that slot>` (the
slot is only read, copied into the scratch). T89 also lacks three of the four results rows `register` needs for a
`places` title (its kept folder has one results screen): its rehearse names them missing; it needs the user's saves of
the rows `2341`, `3412`, `4123` (`--collect end_r2341=<slot>` …) before it can be met.

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
python3 tools/party_add_game.py rehearse <code> [--collect other=<slot>]       # §0 only: a title already added
python3 tools/party_add_game.py bench <code>                                    # unattended, ~5 min, flags on
python3 tools/party_add_game.py solo <code>                                     # sets the one-title setting, prints the lines
python3 tools/party_add_game.py solo <code> --read --winner <the seat the user named>
python3 tools/party_add_game.py close <code>                                    # flags off, the companion as found
```

- **register** FAIL "missing: …" → ask the user for exactly those saves (the role's line above), collect, run again.
  Any other FAIL → stop (below).
- **learn**, **bench** → PASS or stop. **bench** needs nobody: no pad, no TV.
- **rehearse** (§0 only) → PASS or stop.
- **solo:** it first sets the hub's **one-title setting** (B162): while it is set the board offers only this title for
  its player count, so its card is the only one shown. It refuses (nothing asked of the user) if the hub did not take
  it. Then pass its "YOU, now:" lines to the user one by one (pads on the onn; one person with the pads is enough; the
  buttons are named for the pads the onn last reported). **If the user says the board showed two cards for the mini
  game, stop — the setting failed** (one plain sentence, then `close`, then "YOU, now: commit"). When the user says who
  won, run the read with that seat: it clears the setting first, then reads — among its cells, **the mini game played
  was this title** (the launches since the lines, compared in memory), and S over every switch whose next began 4 s or
  more after it (a quicker one is listed, not read; at least four read).
- **close** always, last — also after any stop. It clears the one-title setting too (as does any restart), and records
  the title's own in-game saves before and after as changed or not — never a cell.

**Stop:** one plain sentence — the cell(s) not met and by how much, from the stage's page — then `close`, then "YOU,
now: commit". Never run a stage again with a changed bar.

## 3. The record

The tool's `docs/memory/evidence/add_game/<code>/` (verdicts and pages) and yours,
`docs/memory/evidence/ADD_<code>_<date>.md`: the stages' verdicts in order, the user's words verbatim (titles replaced
by the code), what was disclosed. Then "YOU, now: commit". Nothing adopted: the title is offered by the board only while
both bench flags are on, as T88 and T89 are; adoption is the user's own go.
