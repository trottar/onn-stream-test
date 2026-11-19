# SESSION B — done, 2026-11-18 BB (QUEUE_2026-11-18BB: B156 what adding a title takes; B157 the add-a-game tool; B158 winner-only; B159 PS1 four pads, PS2, GameCube; B160 one line in my board file; B161 A's first use; run ~01:05Z-04:15Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide); `git status
--short` empty (queue BA in `3a9de095`). No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing
fetched or installed; nothing written to the drive; the users' cheat setups, their slots and in-game saves, the kept H7
folders, the rules folder and `runtime/` pictures **read only** (the rules folder's JSON and file names; the tests'
`--check` and digests); every write of the tool's tests went to made-up copies in temp dirs. **No emulator title
started** (B114's made-up titles and B103's fake RetroArch only). **Godot headless only, in scratch copies of the
board's tree** — **disclosed:** my first baseline run of my board check used a scratch copy but not the temp XDG folders
the B145 wrapper sets; I stopped it within ~2 min, found nothing written in Godot's user folders (`find … -newermt`),
and ran every check after through B145's wrapper. **The board's repo: only my two files changed** (uncommitted there).
No title, serial, game id, `profile_id`, character name, cheat name or path in any record, test or output of the tool
(the tool's guard and B157's test 7); **disclosed:** one read of the hub's slot index printed a few real titles to my
own terminal while finding its shape — in no file. The `/tmp/b_q39bb` copy holds companion/, tools/, tests/ and
PrivyHub/'s `app/src` only. Three read-only research agents (the T88 / T89 road; PS1 / PS2 / GameCube; the board's
payout); their findings checked against the code where used. **Nothing deleted** but my own scratch (the mutation
copies, by the script); the B160 timing run stopped at its limit, and one stopped suite run left 2 temp dirs in my
main-disk scratch (kept). Nothing adopted; nothing committed in either repo.

## What was found and built

- **B157 — BUILT** (`evidence/B157_ADD_GAME_TOOL_2026-11-18.md`, `b157_2026-11-18/`, `patches/B157_…`,
  `handoffs/ADD_GAME_TASK.md`, `handoffs/ADD_GAME_PROMPT_TEMPLATE.txt`). `tools/party_add_game.py`: register, learn,
  bench, solo, close; every bar in `BARS` with its source; exit 0 only on PASS; a verdict and a page per stage;
  refused without the stage before (and after its inputs changed); the same bytes twice; a guard on everything written
  or printed. No companion change. **Tests 17** (two made-up titles through the whole path through the real HTTP server, each gate failing with its cell, the refusals, the same bytes twice, no name written; solo's reads; the bars against their sources; T88 and T89 `--check` read only: register and learn PASS, nothing written): three runs OK, and once more after each of two fixes made after them (the PS1 four-player lookup; the no-restart guard).
- **B158 — BUILT** (`evidence/B158_WINNER_ONLY_2026-11-18.md`, `patches/B158_…`): a sidecar's `"result": "winner"`
  → one-hot scores and `"winner"` (the seat) in the ended row and the result, for a class per player or a row of
  places; without the key, today. The board pays `[10, 5, 5, 5]` for `[1, 0, 0, 0]` (read only). **Tests 6**, three runs OK; T88's and T89's rules untouched (sha256 before = after).
- **B160 — DONE** (`evidence/b160_2026-11-18/`): `const ELSEWHERE := true` with its comment; the header's "Start" →
  "Select"; my check asserts both the constant and the picker's `elsewhere()`. **The check PASS (98 assertions; 97 before)** and the PC side's step28 PASS (59); sha256 `920d0073…` / `5d51ffa2…` (were `3f32d339…` / `01301ec5…`). **Disclosed:** one FAIL in nine runs of my files ("no press made during a practice reaches the load screen…", got 1) — six more alone all PASS, HEAD's six all PASS; not explained.
- **B156, B159, B161 — below (no code).**

**Mutations:** **8 / 8 caught** — the margin bar loosened, the predecessor gate skipped, the PAUSED and files cells always met, the guard off, the no-restart guard off (B157); the winner's seat as the port, `result` with `scores` listed (B158). The recent and earlier suites once, all OK (`art_systems` against the repo: its docs test needs `docs/`).

## B156 — what adding a title takes

**T88's and T89's road, in order** ([S] already scripted · [CS] can be scripted · [U] the user's hands · [J] took
judgment then):

1. **[U]** The user's saves on the onn: begin, ends, mid-match (T88: HOME-12V / H7-P1-P3; T89: H7-C1 with four people
   and set finishing orders). Only a person can play a match to a chosen end and press SAVE.
2. **[CS → S by B157]** The slots copied to a kept folder (A by shell) → `register --collect`.
3. ~~The memory rule (H7-P1-P3, `h7_rule_search`)~~ — superseded; the party layer never reads it.
4. **[CS → S by B157]** Pictures from the kept states, run forward headless (H7-V1, A's `capture_frames.py`) →
   learn's capture (`party_add_game_capture.py`, the same B95 `Session`).
5. **[J → S by B157]** **The labels** (Cowork drew time ranges by eye: which screen is the end). Now from the state each
   picture came from, the moved frames left out by B140's measure. **The one judgment that remains for a new title:
   which screen the user saves as the end** — a screen that stays and shows who won by player, not by character; the
   task tells the user so.
6. **[S]** The learner (`h7_endscreen.py learn / score / replay`, B102; tone B104; places B122).
7. **[J → S by B157]** The acceptance of a spec (A and Cowork read the confusion and the replays) → learn's bars.
8. **[CS → S by B157]** The begin and the sidecar written by hand (`cp`, a JSON by hand) → learn writes them.
9. **[U]** The setup (Extras → Cheats) and its slot 1 at the select screen (H7-C2) — the user's, when the game has
   things to unlock. **[J → S]** which setup (T88 had two): the tool takes the one whose slot 1 is filled, else FAILs.
10. **[S]** The hub's start / watch / end (B103-B105), the party layer (B108-B116), hold and go (B133), practice
    (B134).
11. **[J → general]** Each fix after a missed sitting, now general for any title: B129 (the game's own window by pid),
    B130 (15 s under a setup — **sized from T88's 9.0 s**: a title whose notices last longer would need it again),
    B137 (paused, pads muted), B139 (RetroArch's text off), B140 (frames until the picture moved), B141 (Select held),
    B143-B155 (sound, band, Select, switch, keys).
12. **[J → S by B157]** The bench's bars (H7-V6b: `prepare_s` ≤ 5 / 6 s chosen per title) → one bar, 6 s (T89's).
13. **[CS → S by B157]** The bench by curl (PP-H4 part 1) → `bench`; the solo sitting's reads (A's scripts) → `solo
    --read`; the close → `close`.
14. **[U]** The solo and four-person sittings at the TV.

**The user's part for a new title, in full.** First tell the session: two players or four; how the game shows who won
(a screen that says which player won → `winner`; a results screen with every player's place in a row → `places`, four
players only); whether it has things to unlock (→ a setup made in Extras → Cheats, every save inside it); the words to
find it in the library. Set the game to its **shortest match** (one round or one life, items off, the shortest time),
the same for every save. Then the saves with the onn's **SAVE (slots 1-3; slot 9 and slot 0 are the hub's)**, three at
a time — after each three the session collects them and the user may save over them:

- **Two players (`winner`), two rounds:** slot 1 = **begin** (the select screen before anyone picks, nothing moving
  when nobody presses); slot 2 = **other** (the middle of a match); slot 3 = **P1 won** (the screen that stays after a
  match P1 won, showing it by player); then slot 1 = **P2 won**.
- **Four players (`winner`), two rounds:** begin, other, P1 won; then P2 won, P3 won, P4 won (four people, or the user
  with four pads).
- **Four players (`places`), two rounds:** begin (character select, nobody picked), other, the results screen of a
  match finished in the order P1 1st, P2 2nd, P3 3rd, P4 4th (`1234`); then the results screens of three matches
  finished `2341`, `3412`, `4123` — so every player takes every place.

**A setup or not:** a title needs a setup only to unlock things (characters, stages). With nothing to unlock: no setup
— `--setup none`; the sidecar has no `cheat`, the begin is `<id>.state`, the launch is the plain one. **Today's code
takes it** (`_cheat_of` → None without `cheat`; PP-H3 and PP-H3b ran T88 that way). A setup with no cheats is not a
form; leave it out.

## B159 — four pads on PS1; PS2 and GameCube (settled; no code)

**PS1, four players:** the core needs its port-1 multitap on (`beetle_psx_hw_enable_multitap_port1 = "enabled"`, in
the per-content `.opt`) and four `--device` arguments (RetroArch ignores the config's device lines). **For one title
only: yes, today, by its own setting** — the per-title `ps1_multitap: port1` (the hub's controller overrides, B63);
the party launch takes the title's own setting (it passes no players). **The catch:** that setting is the title's for
every launch, the users' own included (fine for a four-player game). **The four pads:** the bridge always has four
virtual pads; `set_party_route` maps seat → pad k → port k; with the multitap on, pads 3-4 reach 1C / 1D; mute and
Select hold cover all four. **A bench with no pad can prove** the launch's `.opt` line and four `--device` arguments
(B63's pattern) and, on the hub, RetroArch's own log of the ports; **that ports 3-4 take input needs a press on routed
pad 3 / 4** at the title's join screen read as B140's "moved" — no bench route does that yet. Never run in a party mini
game (PP-H4's four-player title was N64). The tool's register checks the title's four-player setting for PS1.

**PS2 (PCSX2) and GameCube (Dolphin), today** (both adopted; launched by `_launch_pcsx2` / `_launch_dolphin`; the party
layer and `h7_minigame` speak RetroArch only and refuse both):

| a party mini game leans on | PS2 | GameCube |
| --- | --- | --- |
| a state loaded by the hub | has it by slot (PINE), but confirms by resuming and watching the picture — **missing** for a held title | by hotkey only, confirms by resuming — **missing** for a held title |
| a pause that can be proved | has it (PINE status PAUSED) | has it by measurement (the CPU clock still for 0.5 s) |
| the begin shown while paused | **by settings** (bind PCSX2's frame advance) — unmeasured | **by settings** (bind Dolphin's frame advance) — unmeasured |
| the pads off until the go | has it (the bridge's mute) | has it |
| Select held | has it (not needed) | has it (no Select on the pad) |
| a clean window | **by settings** (its OSD message / indicator keys) | has it (messages off) |
| its own window and sound found | has it (by pid) | has it (by pid) |
| the stop | has it | has it |

**What it would take, in order — PS2:** ports from the sidecar's players with a PS2 capability like B63's; the begin
kept as a `.p2s`, copied to the hub's scratch slot and loaded through PINE while paused, confirmed by PCSX2's own "Loaded
state from slot" line; the party's "is it paused" made emulator-neutral (PINE in place of GET_STATUS); frame advance
bound and used in the preparation; the OSD keys off for the party launch, `keys_written` reading `PCSX2.ini`;
`h7_minigame`'s refusal lifted with its state folder and naming; then measure whether focusing the held window shows on
the board's stream; fakes, bench, TV. **GameCube:** ports nothing (four always); the begin kept as `.s0N`, copied to
slot 9, a paused load confirmation found (Dolphin's log, or B140's grab after a frame advance); the clock proof as
"paused"; frame advance bound; `h7_minigame`'s refusal lifted; measure the window activation the keys need; fakes,
bench, TV.

## B161 — A's first use: the tool's solo on T88 (sketch)

T88 is already in the rules folder, so the task's §0: register (`--rules-players 2`), learn (its kept spec's numbers),
solo (the flags on, the lines, then the read), close. It proves on the onn: **B153** (every planned switch ≤ 1.6 s, the
arrival gap ≤ 1200 ms, S), **B155** (`keys_written` true), and the **PC side's change** (the board's checks PASS with
step28 — the task's precondition; the user's words on the host's voice and the cover recorded, no bar). **The exact
prompt for session A** (the template, its blank filled):

```
You are SESSION A, on the hub with the user. Run docs/memory/handoffs/ADD_GAME_TASK.md exactly as written for the title with code T88 (the user knows which game it is; it is never written down), under every standing rule in it. First check the window and the preconditions it names; then the user's saves, then the tool's stages in order — register, learn, bench, solo, close — one command each, the verdict read from the tool's own last line and page. You never judge a picture, choose a threshold or edit a rule: a stage that is not PASS stops the task with one plain sentence (the cell and by how much), then close, then "YOU, now: commit". Every reply to the user begins "YOU, now:"; nothing about adb is ever asked at the TV; no title, id, path or picture in any record. Nothing adopted; nothing committed by you. Your reply ends with the five verdicts in order and "YOU, now: commit".
```

## What I would change (not done — the queue is the task)

1. **The board's payout for a lone winner** (`[10, 5, 5, 5]`): before any four-player `winner` title is played, the PC
   side should give winner-only results their own payout (the tied last taking the worst place, or `[10, 0, 0, 0]`).
2. **Learn's real picture source has never run** (no title could be started here). The first new title's learn is its
   first run; a short bench rehearsal — learn on T88's own kept states into a scratch rules folder, `--check`-style,
   nothing written to the real one — would prove it before a new title depends on it.
3. **B114's harness is near the kernel's one-argument limit** (127,400 of 131,072 bytes for its child's `-c` text): the
   next mode added inline will break every suite on it. Running the child from a file by path would end that for all.
4. **B130's 15-s window was sized from T88's 9 s**; a title whose notices last longer would miss its start. The bench's
   6-s ready bar catches it, but the window could be a learnt number per title.
5. **A winner read from a row of places still needs every place read and no ties.** A winner-only read of the "1"
   alone would let more results screens in (one change in the reader, not per game).
6. **solo's lines name the controls in PlayStation words** (△, ✕, Select / Share): an Xbox-pad line is needed when a
   pad's class says so (as PP-H4 did by hand).
7. From BA, still open: the users' own stop path's 2-s wait; the sound after Home (the app's 12-s hold).

## Files

This repo: `tools/party_add_game.py`, `tools/party_add_game_capture.py` (new), `companion/party_minigame.py`;
`tests/b157_add_game/` (new: tests, made-up pictures, the harness mode), `tests/b158_winner_only/` (new),
`tests/b114_party_minigame_hang/b114_scenario.py` (the `winner158` mode, the `b157` hook);
`handoffs/ADD_GAME_TASK.md`, `handoffs/ADD_GAME_PROMPT_TEMPLATE.txt` (new); `evidence/B157_ADD_GAME_TOOL_2026-11-18.md`
+ `b157_2026-11-18/` (`b157.diff` on top of `b158.diff`), `evidence/B158_WINNER_ONLY_2026-11-18.md` +
`b158_2026-11-18/` (`b158.diff` applies on `3a9de095`), `evidence/b160_2026-11-18/` (the board's `b160.diff`, the
checks), `patches/B157_ADD_GAME_TOOL.md`, `patches/B158_WINNER_ONLY.md`, `patches/B160_BOARD_ELSEWHERE.md`;
`docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph after queue BA's),
`logs/b157_git_status.txt`, `logs/b158_git_status.txt`, `logs/b160_git_status.txt`, `handoffs/SESSION_B_STATUS.txt`
(one line), this file. **The board's repo:** `minigames/hub_minigame.gd`, `checks/hub_minigame_check.gd`.

**The user, now:** this repo — commit the tree (queue BB). **The board's repo** — commit my two files:
`git -C <board repo> add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git -C <board repo> commit -m
"Hub mini game says it is played elsewhere; Select in its header"`.
