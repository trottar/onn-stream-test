---
memory_schema: 1
as_of: 2026-11-20
status: FIXED TASK (session A, hardware) — add one party mini game by its code with tools/party_add_game.py (B157; B162 solo's one-title setting, its title cell, S's listed switches, the in-game saves recorded, the pads' words; B163 rehearse for a title already added; B171 two saves per ending, learn's line for one more save, the cap; B172 the solo mark ended at close; B175 every save read by a spec learnt without it; B176 a save in the wrong role, the same match saved twice; B178 `--result score` and its label stage, the one picture the session reads; B179 a stop at the questions for a way of showing who won the tool has no kind for). The same task for every title; only the code changes (ADD_GAME_PROMPT_TEMPLATE.txt). Nothing adopted by it
---

# ADD-GAME — one title, by its code, through the tool's five stages

The code (`T` + two digits) is the only name of the title in anything written. The user knows which game it is; the
words the user gives to find it in the library are typed into one command at run time and never written down. **The
tool decides every verdict; you never judge a picture, choose a threshold or edit a rule.** A stage that is not PASS
stops the task. **The one exception (B178): a `score` title's `label` stage (§2)** — there you read each end save's
final score from the pictures the tool puts out, and pass the numbers in; the tool checks every reading and decides.

**First, once, in chat only (B170):** before anything else, ask the user — "YOU, now: which game is <code>? I will not
write its name anywhere." Use the name the user gives **only in your replies to the user**, so every line you send
about a save or a match names the game; never in a file, a command, a record or a page.

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
and the learner cannot learn without one: before `rehearse`, ask the user for that one save — "YOU, now: start <the
game's name> from Games the way you always play it (with its Extras setup, if it has one), and in the middle of a match
press SAVE to slot 2 or 3 — never slot 1 (with a setup, slot 1 is the game's own start). Reply with the slot number." —
then `rehearse <code> --collect other=<that slot>` (the slot is only read). **B171: rehearse keeps a copy of every save
it collects** in the title's own add_game folder (off the repo), so the user may save over that slot at once; a later
rehearse takes the copy (no `--collect` needed again; `--collect` again replaces it).

**rehearse as B167 leaves it:** the picture source starts as the hub starts the title (the hub's display, its own core
and core options); the begin is the one the mini game starts from (the rules folder's own, read only); a capture that
cannot start says why in a cell ("pictures made": busy, display, content not found, core missing, config, exited, not
playing, state refused), and RetroArch's own log is in the title's add_game folder (`logs/`, never the repo). **For
T88 rehearse is FAIL on learn's own bars from its kept saves alone** (B167: from one still save per ending the learner
cannot separate its two end screens, which differ only in a small win tally; B171: its kept `end_p1_b` / `end_p2_b` are
mid-fight saves, not end screens). **B171: rehearse's page now ends with learn's line** — "One more save: <role> — the
screen after a match player <k> won, from a match not saved yet … then rehearse <code> --collect <role>=<slot>." — and
lists the endings below two saves (for T88: `end_P1_2`, `end_P2_2`). Ask the user for exactly that save with §1's line
for one more save (under a setup: slot 2 or 3), then `rehearse <code> --collect <role>=<slot>`; repeat while the page
names a save; the most it asks is four saves of each ending, then the cap's line (§1). In §0, **rehearse stops the task
only when the real rules folder's sha256 cell is not met or a "pictures made" cell names a reason** (the picture source
did not run); learn's bars there are the record and its line the next save, not a stop. T88's own rules are never
changed by rehearse, PASS or not. T89 also lacks three of the four results rows `register` needs for a
`places` title (its kept folder has one results screen): its rehearse names them missing; it needs the user's saves of
the rows `2341`, `3412`, `4123` (`--collect end_r2341=<slot>` …) before it can be met.

## 1. The user's saves (the user's hands; B156)

Ask once, in this order, what the user already knows: **two players or four; who wins is shown how** — a screen that
says which player won (→ `winner`), or a results screen with every player's place in a row (→ `places`; four players
only), or **the scores (or points, a count) of each side, the winner the side with more** (→ `score`, B178: its saves
are `winner`'s, and the label stage after register), or **some other way (a time, a distance, only a team's or
character's name)** → **stop here, before any save is asked** (below); **whether the game has things to unlock** (→ a
setup: `--setup slot1`, made by the user in Extras → Cheats, and every save below made inside it; nothing to unlock →
`--setup none`); **the words to find it in the library**.

**The stop at the questions (B179) — when the answer to "who wins is shown how" is none of the three kinds** (a time, a
distance, a lap count read as a time, only a team's or a character's name, two numbers where the smaller wins, or
anything else the tool has no kind for): ask for no save and run no stage but close. Say, word for word: "YOU, now:
<the game> shows who won in a way the hub can't read yet (<the way, in the user's words>). I've stopped before asking
for any saves; it goes back to Cowork." Record the user's words in your page, then `close <code>` (if register ran),
then "YOU, now: commit". **The same stop for any answer the tool has no kind for**, and when you are not sure which of
the three the answer is: stop and ask Cowork, never fit a title to the nearest kind.

Then the saves, three at a time (the onn's SAVE, slots 1-3; slot 9 and slot 0 are the hub's), each round followed by
`register … --collect role=slot …` (the tool copies them; the user may then save over them). **With a setup, never
slot 1 for anything but the begin** (a setup's slot 1 is the title's own start): the other saves go to slots 2 and 3,
two at a time:

- **The match, shortest:** one round or one life, items off, the shortest time the game offers — the same settings
  for every save.
- **`begin`:** the screen just before a match, nobody picked yet, nothing moving when nobody presses (two players:
  the select screen; four: the character select screen). Under a setup: its slot 1.
- **`other`:** the middle of a match (a fight, a race) — anything that is not a begin or an end screen.
- **`winner`, n players (B171): two saves of every ending from the start** — `end_P1`, `end_P1_2`, … `end_Pn`,
  `end_Pn_2`: for each player, **two matches that player won, each from a different match with other characters (or
  another stage)** than every other match saved, saved on the screen that stays after it and shows who won by player
  (not by character). Two saves of one match, or two matches with the same characters, do not help: the tool learns
  what tells the endings apart from what changes between the matches.
- **`places`, four players:** four matches finished in set orders so every player takes every place — rows `1234`,
  `2341`, `3412`, `4123` (P1's place first) — each saved on its results screen: `end_r1234` …

- **`score` (B178), n players: the same saves as `winner`** — two wins for each player from the start, each from a
  different match, saved on the screen after the match that shows each side's number (the final score, the stats
  screen). The user says only who won; the numbers are read later by you in the label stage, never typed by the user
  unless the tool asks for one save's numbers. **Saves already kept under the code** (T90's six, taken under `winner`
  on 2026-11-20) stay: run `register <code> … --result score` with no `--collect` first and ask only for what its page
  names missing; then `label <code>`.

**The rounds, two players, `winner` or `score` (B171): begin, other, `end_P1`, `end_P1_2`, `end_P2`, `end_P2_2`.**

- **No setup — rounds of three slots:** round 1 `--collect begin=1 --collect other=2 --collect end_P1=3`; round 2
  `--collect end_P2=1 --collect end_P1_2=2 --collect end_P2_2=3`.
- **Under a setup — slot 1 is never used by the user** (it is the setup's own start, the begin): round 1 `--collect
  begin=1 --collect other=2 --collect end_P1=3`; round 2 `--collect end_P2=2 --collect end_P1_2=3`; round 3 `--collect
  end_P2_2=2`.

Lines for the user, word for word (the game named by the name the user gave, in the reply only):
- Round 1: "YOU, now: set <the game> to its shortest match (one round, items off). Save to slot 1 on the select screen
  before anyone picks; start a match and save to slot 2 in the middle of it; let P1 win and save to slot 3 on the screen
  after the match that shows P1 won. Reply ok." Under a setup: "YOU, now: start <the game> from Games with its Extras
  setup and set it to its shortest match (one round, items off). Don't save to slot 1. Start a match and save to slot 2
  in the middle of it; let P1 win and save to slot 3 on the screen after the match that shows P1 won. Reply ok."
- Round 2, no setup: "YOU, now: play three more matches, each with other characters (or another stage) than any match
  saved so far: P2 wins the first — save to slot 1 on the screen after it that shows P2 won; P1 wins the second — save to
  slot 2; P2 wins the third — save to slot 3. Reply ok."
- Round 2 under a setup: "YOU, now: play two more matches, each with other characters (or another stage) than any match
  saved so far: P2 wins the first — save to slot 2 on the screen after it that shows P2 won; P1 wins the second — save to
  slot 3. Never slot 1. Reply ok." Round 3: "YOU, now: play one more match P2 wins, with other characters (or another
  stage) than any match saved so far, and save to slot 2 on the screen after it that shows P2 won. Reply ok."

**One more save (B171) — when learn's (or rehearse's) page ends with "One more save: <role> …":** the line to the
user, word for word, `<k>` the player in the role (`end_P<k>_<n>`), the slot 2 or 3 (never 1 under a setup):
"YOU, now: play one more match of <the game> that P<k> wins, with other characters (or another stage) than any match
saved so far, and save to slot <2 or 3> on the screen after it that shows P<k> won. Reply ok." Then `register <code> …
--collect <role>=<slot>` and `learn <code>` (§0: `rehearse <code> --collect <role>=<slot>`). The bars are the same every
time; never a bar changed.

**The cap (B171):** the tool asks for at most four saves of each ending. When the page ends with "The end screens cannot
be told apart this way …", stop asking and say, word for word: "YOU, now: <the game> can't be added this way: after
four saves of each player's win, its end screen still doesn't show the hub who won. If it has another mode whose end
screen shows who won by player (P1 / P2, not the character), or another screen after a match that does, tell me and we
start its saves again; otherwise it stays off the board." Then `close`, then "YOU, now: commit".

**B175 — every save is read by a spec that never saw it.** learn learns again without each match's saves and reads
them back ("left out: <role>"): each must end as its own ending within 2 s and never as another. With two saves of an
ending, leaving one out leaves one, so **a title whose endings look nearly alike needs at least three saves of each
player's win** (learn asks for the third with the line above); one whose endings look clearly different can pass on
two. The spec the hub uses is still learnt from every save.

**B176 — two more lines; the page ends with only one, and the session passes it on in this order:**
- **"A save may be in the wrong role: <role> reads as <the other ending>. …"** — say, word for word: "YOU, now: one of
  the saves of <the game> may be the wrong player's win: the one saved as P<k>'s win looks like P<j>'s. Play one more
  match that P<k> wins and save to slot <2 or 3> on the screen after it that shows P<k> won. Reply ok." (`<k>` from the
  role, `<j>` from the other ending.) Then `register <code> … --collect <role>=<slot>` (it replaces that save) and
  `learn <code>`. **Ask for no other save until learn no longer says it.**
- **"<a> and <b> look like the same match saved twice: save <b> again from another match."** — say, word for word:
  "YOU, now: two of the saves of <the game> for P<k>'s win look like the same match. Play another match that P<k> wins,
  with other characters (or another stage) than any match saved so far, and save to slot <2 or 3> on the screen after it
  that shows P<k> won. Reply ok." (`<k>` from `<b>`.) Then `register <code> … --collect <b>=<slot>` (it replaces `<b>`)
  and `learn <code>`. The two count as one save until then.
- **"One more save: <role> …"** — the line above.
- **"The end screens cannot be told apart this way …"** — the cap's words above.

(Four players and `places`: the rounds as the roles above; four people, or the user with four pads. A `places` title's
rows already come from different matches; learn may ask one more results screen: "collect it as end_r<its row>, or
end_r<its row>_<n> when that row is kept already".)

## 2. The stages — one command each, the verdict read from its last line

```
python3 tools/party_add_game.py register <code> --players <2|4> --system <ps1|n64|snes> --result <winner|places|score> \
        --find "<the user's words>" --setup <none|slot1> --collect begin=1 --collect other=2 --collect end_P1=3
python3 tools/party_add_game.py register <code> … --collect end_P2=1 --collect end_P1_2=2 --collect end_P2_2=3  # round 2
python3 tools/party_add_game.py label <code>                                    # score only (B178): the pictures
python3 tools/party_add_game.py label <code> end_P1=<P1>-<P2>,<P1>-<P2> …      # score only: your two readings each
python3 tools/party_add_game.py learn <code>
python3 tools/party_add_game.py rehearse <code> [--collect <role>=<slot>]      # §0 only: a title already added
python3 tools/party_add_game.py bench <code>                                    # unattended, ~5 min, flags on
python3 tools/party_add_game.py solo <code>                                     # sets the one-title setting, prints the lines
python3 tools/party_add_game.py solo <code> --read --winner <the seat the user named>
python3 tools/party_add_game.py close <code>                                    # flags off, the companion as found
```

- **register** FAIL "missing: …" → ask the user for exactly those saves (the role's line above), collect, run again.
  Any other FAIL → stop (below).
- **label** (B178, `--result score` only; after register's PASS, before learn) — **the one picture you read.** Run
  `label <code>`: it puts two pictures of every end save's final screen, two ticks apart, in the title's add_game folder
  (`~/privyhub_h7/add_game/<code>/label/`, off the repo: `<role>.1.png`, `<role>.2.png`; once the places are known,
  each side's number cut out, `<role>.P1.png`, `<role>.P2.png`). Open each with your own vision; read each side's
  number, P1 first, from `.1` and then, separately, from `.2`; pass both:
  `label <code> end_P1=<P1>-<P2>,<P1>-<P2> end_P1_2=… end_P2=… end_P2_2=…`. Never a picture in the repo or a reply.
  **The tool checks every reading:** the two the same; the role's player ahead (an `end_P<k>` save has P<k> ahead);
  the numbers at one place in every save; each save read back by a reader learnt without it. Its last line is one of:
  - "Read the final score on each end save's two pictures …" → read them, run the line's command.
  - **"Read again: <role> (<why>) …"** → open that save's pictures again (and its cut-out numbers), read them afresh,
    run `label <code> <role>=<P1>-<P2>,<P1>-<P2>`. Nothing to the user.
  - **"Ask the user for <role>'s numbers …"** (the same save named a second time) → say, word for word: "YOU, now: I
    couldn't read one final score of <the game> for sure. In the match P<k> won that you saved for me, what was the
    final score — P1's number, then P2's? Reply like 21-14." Then `label <code> <role>=<their numbers>,user`.
  - "<role> cannot be read as the user says … collect it again from another match …" → §1's line for one more save for
    P<k>, `register <code> … --collect <role>=<slot>`, `label <code>` (its pictures), read, label, learn.
  - none (PASS) → learn. Any other FAIL → stop.
- **learn** → PASS; or its page's last line is one of §1's four — a save in the wrong role, the same match saved twice,
  one more save (each: §1's line to the user, then register's `--collect` and learn again), or the cap (§1: say it,
  stop). Any other FAIL → stop.
  - **A `score` title's own line (B178): "One more save: a match either player won whose final score shows <digits> …"**
    → say, word for word: "YOU, now: play one more match of <the game>, with other teams (or characters) than any match
    saved so far, and try to end it with a <digit> in either side's final score (<the digits> — any one helps). Save to
    slot <2 or 3> on the screen after the match that shows the final score, then tell me who won." Then `register
    <code> … --collect end_P<the winner>_<n>=<slot>` (the role the line names for that winner), `label <code>`, read
    the new save's pictures, `label <code> <role>=…`, `learn <code>`. **bench** → PASS or stop (it ends every
  kept save, each save of an ending as that ending); it needs nobody: no pad, no TV.
- **rehearse** (§0 only) → as §0 says.
- **solo:** it first sets the hub's **one-title setting** (B162): while it is set the board offers only this title for
  its player count, so its card is the only one shown. It refuses (nothing asked of the user) if the hub did not take
  it. Then pass its "YOU, now:" lines to the user one by one (pads on the onn; one person with the pads is enough; the
  buttons are named for the pads the onn last reported). **If the user says the board showed two cards for the mini
  game, stop — the setting failed** (one plain sentence, then `close`, then "YOU, now: commit"). When the user says who
  won, run the read with that seat: it clears the setting first, then reads — among its cells, **the mini game played
  was this title** (the launches since the lines, compared in memory), **the board showed one card** (the board's own
  `cards 1` line, B169), and S over every switch whose next began 4 s or more after it (a quicker one is listed, not
  read; at least four read). **solo's first run writes the users' files' before** when bench left none (a title
  already added: always, B169), so close compares them after every solo. **B172: close ends the solo mark and the
  befores** (and register ends one an earlier use left), so a later solo reads only its own rows.
- **close** always, last — also after any stop. It clears the one-title setting too (as does any restart), and records
  the title's own in-game saves before and after as changed or not — never a cell.

**Stop:** one plain sentence — the cell(s) not met and by how much, from the stage's page — then `close`, then "YOU,
now: commit". Never run a stage again with a changed bar.

## 3. The record

The tool's `docs/memory/evidence/add_game/<code>/` (verdicts and pages) and yours,
`docs/memory/evidence/ADD_<code>_<date>.md`: the stages' verdicts in order, the user's words verbatim (titles replaced
by the code), what was disclosed. Then "YOU, now: commit". Nothing adopted: the title is offered by the board only while
both bench flags are on, as T88 and T89 are; adoption is the user's own go.

## 4. The user's part, as it now is (B177; B178 for `score`) — two players, `winner` or `score`

**`score` (B178):** the same saves, rounds and lines; the user says only who won each match. The numbers on the final
screen are read by you in the label stage. **The user is asked one match's final score only when your readings of
it disagree twice.** Every digit a save shows must also be shown by another save, so learn may ask for one more match
whose final score shows a digit it names. The least is 6 saves, when the four final scores share their digits; in
practice 7 or 8; at most 10.

**Saves: 6 at the least** (the begin, a mid-match save, two wins for each player — enough when the two players' end
screens look clearly different), **in practice 8 for a game whose end screens look nearly alike** (three wins for each
player), **10 at the most** (four wins for each player); a save in the wrong role or the same match saved twice is saved
again, not added.

1. Tell the session which game the code is (in chat only).
2. Answer: two players; who won is shown by player after a match; anything to unlock (its setup made in Extras →
   Cheats first); the words to find it in Games.
3. Set the shortest match (one round, items off), the same for every save.
4. Round 1 — no setup: slot 1 the select screen before anyone picks, slot 2 the middle of a match, slot 3 after a match
   P1 won. Under a setup: never slot 1; slot 2 the middle of a match, slot 3 after a P1 win.
5. Round 2 — each match with other characters (or another stage) than any saved so far: no setup, P2 wins → slot 1,
   P1 wins → slot 2, P2 wins → slot 3; under a setup, P2 wins → slot 2, P1 wins → slot 3, then one more P2 win → slot 2.
6. Then as the session asks, one line at a time: one more win for a player (other characters again; up to four wins each);
   a win saved again under the right player; a win saved again from another match.
7. Nothing during bench.
8. Solo: the pads on the onn; follow the lines; say who won and whether the board showed one card.
9. If the session says the game can't be added this way: another mode or another screen that shows who won by player,
   or the game stays off the board.
10. Commit.
