# SESSION B — done, 2026-11-19 BC (QUEUE_2026-11-19BC: B162 the tool's solo safe for many titles; B163 rehearse; B164 the board check's one FAIL in nine; B165 the fixed task; B166 A's first use; run ~04:15Z-06:18Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide); `git status
--short` empty (queue BB in `58497ab8`; the prompt files committed there); **my two board files committed in the board's
repo** (`9a803d6`, sha256 `920d0073…` / `5d51ffa2…` as B160 left them; its status empty). No stream, no companion or
keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; the users' cheat
setups, their slots and in-game saves, the kept H7 folders, the rules folder and `runtime/` pictures **read only** (the
kept folders' file names, by the tool's role mapping; the rules folder's spec counts, by name-free reads; the id check);
every write of the tool's tests went to made-up copies in temp dirs. **No emulator title started** (B114's made-up
titles, B103's fake RetroArch, B157's made-up picture source). **Godot headless only, in scratch copies of the board's
tree, Godot's own folders in the scratch** (B145's wrapper and my runner made the same way). **The board's repo: only
my check file changed** (uncommitted there), as B164 found the fault in it. No title, serial, game id, `profile_id`,
character name, cheat name or path in any record, test or output (the tool's guard; B162's test 6; the three checks);
**disclosed:** my own terminal showed the kept folders' file names (role words), the T88 spec's frame counts and one
heartbeat row's `pad_slots` (its pads' 6-hex hashes and classes) while finding their shape — in no file but the role
words. The `/tmp/b_q40bc` copy holds companion/, tools/, tests/ and
PrivyHub/'s `app/src` only. No agents. **Nothing deleted** but my own scratch. Nothing adopted; nothing committed in
either repo.

## What was found and built

- **B162 — BUILT** (`evidence/B162_ADD_GAME_SOLO_SAFE_2026-11-19.md`, `b162_2026-11-19/`, `patches/B162_…`). The
  companion: a one-title setting (`POST party-minigame-only`, loopback, memory only) under which `party-minigames`
  lists the title under test alone for its player count; one party row when set and one when cleared, no name. The
  tool: solo sets it and refuses unless the hub lists one title for the count; `--read` clears it first; close clears
  it; any restart clears it. **Tests 17 ×3 OK; the flags absent → HEAD's bytes on every route, the users' routes HEAD's
  bytes with both flags set.**
- **B163 — BUILT** (`evidence/B163_ADD_GAME_REHEARSE_2026-11-19.md`, `b163_2026-11-19/`, `patches/B163_…`):
  `rehearse <code>`. **Found: T88's and T89's kept folders have no mid-match state, and the learner cannot learn
  without one** — `--collect other=<slot>` (the user's one save, read only, into the scratch only), added after the
  design was hashed. **Tests 6 ×3 OK** (and ×3 again after the test fix below).
- **B164 — SETTLED, FIXED in my check** (`evidence/B164_BOARD_CHECK_RACE_2026-11-19.md`, `b164_2026-11-19/`,
  `patches/B164_…`): **the check's timing, not the board.** Its made-up presenter kept "shown behind a practice" from
  the practice before, and the stand-in hub turns "practice" as it takes the next practice's go, before the board's gate
  goes up: a press 6-7 ms after the go (made on the load screen, before any hand-over) was counted. **HEAD's two files 2
  FAIL in 30, mine 2 in 30** (every counted press in that window, the gate not in the tree); a probe pressing exactly
  then: the old check FAIL 3 / 3. At the TV no ready mark or go can come from it (the board has sent its go; the re-show
  at the hand-over clears every mark; the hub says `starting` only after its switch back). **Fixed in my check only**
  (a press counted only during the practice the screen was shown behind): **30 of 30 PASS (98)**, the probe PASS 3 / 3,
  the board's practice gate removed still FAIL 2 / 2, the PC side's **step28 PASS (59)**; `hub_minigame.gd` unchanged.
- **B165 — DONE** (`handoffs/ADD_GAME_TASK.md`; the template unchanged, sha256 `4ba6a99a…` before = after).
- **B166 — below (no code).**

**Mutations: 11 / 11 caught** — after one my test missed (below): the list filter off, the route's loopback check off,
the title cell always met, every switch read, the in-game saves compared, Xbox words never, the clear on `--read`
skipped, the clear on `close` skipped (B162); learn run into the real rules folder, the ending cell always met, the
scratch kept (B163). **The board:** the fixed check still FAILs with the board's practice gate removed (2 / 2). B157 17
×2, B158 6 ×2 and the recent party suites once (23 suites, B114 to B155), all OK, 0 temp dirs.

**Disclosed:** (1) the mutation "learn run into the real rules folder" was not caught on its first run — my test's
made-up real spec had the bytes a scratch learn makes; the test now learns it from shorter runs; caught on the rerun.
(2) My first B162 harness run used a made-up `.iso` title the manager refuses; the test uses the harness's N64 title.
(3) B157's solo tests now run a made-up hub (the setting must be taken before the lines) and write a launch log. (4)
One sync of the work copy happened while the recent suites ran (only B163's test file differed); the suite running then
(b139) passed, and passed again alone. (5) My run scripts first had this machine's paths inline; the copies in the
records take them as arguments (the same logic). (6) solo's lines got two phrases beyond B162's words (ten seconds in
a practice; "if two cards show, stop and tell me").

## B165 — the one line for any later code

Type this in session A, with the code in place of T90 (nothing else changes, no prompt written by Cowork):

```
Read docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt, put T90 where it says ____, and follow it as my prompt.
```

The template is unchanged; it runs `handoffs/ADD_GAME_TASK.md` for a new title (register, learn, bench, solo, close).
A title already added (T88, T89) is §0 of the same task, with `rehearse` after `learn` — B166's prompt below.

## B166 — A's first use: T88 through §0 (no code)

**What it proves on the hub and the onn:** the tool's own path end to end on a real title; **learn's real picture
source** (rehearse — the title started headless, its kept states and the user's one mid-match save captured, learnt into
a scratch rules folder, the real rules untouched); **B153** (every planned switch ≤ 1.6 s; the arrival gap ≤ 1200 ms at
each read switch); **B155** (`keys_written` true); **B162** on the onn (one card shown; the title cell; S with the
listed switches); **the PC side's cover and quiet host** (the user's words, no bar). The user's part: one SAVE in the
middle of a match (a slot they don't need), then the solo (one person with two pads is enough), ~15 min at the TV.
The stages: register and learn ~seconds; rehearse ~4-5 min unattended (six states × 20 s of pictures, the learner);
solo's lines, the user's match, the read; close.

**The exact prompt for session A:**

```
You are SESSION A, on the hub with the user. Run docs/memory/handoffs/ADD_GAME_TASK.md §0 exactly as written for the title with code T88 (the user knows which game it is; it is never written down), under every standing rule in it. First check the window, the preconditions it names (queue BC's two greps included) and the board's two checks. Then, one command each, the verdict read from the tool's own last line and page: register T88 --players 2 --system ps1 --result winner --rules-players 2; learn T88; the task's line to the user for the one mid-match save, word for word, then rehearse T88 --collect other=<the slot the user names>; solo T88, its "YOU, now:" lines passed to the user one by one, then solo T88 --read --winner <the seat the user names>; close T88. rehearse is the first run of learn's real picture source: report its cells as the tool wrote them. From solo's page, record without a bar of yours: every planned switch's seconds (B153's bound 1.6 s), the arrival gap at each read switch (1200 ms), the switches listed, keys_written, the title cell. After the match ask the user once, and record their words verbatim: did the host speak on the load screen, and was the board seen bare before the load screen. You never judge a picture, choose a threshold or edit a rule: a stage that is not PASS stops the task with one plain sentence (the cell and by how much), then close, then "YOU, now: commit"; if the user says the board showed two cards for the mini game, stop the same way (the one-title setting failed). Every reply to the user begins "YOU, now:"; nothing about adb is ever asked at the TV; no title, id, path or picture in any record. Nothing adopted; nothing committed by you. Your reply ends with the five verdicts in order (register, learn, rehearse, solo, close) and "YOU, now: commit".
```

## What I would change (not done — the queue is the task)

1. **A cell for the card count:** the board logs "cards <n>, chose …"; solo's read could make "cards 1" a cell, so
   the one-title setting is proved by the board's own line, not only by the user saying "two cards".
2. **A title already added has no files' before** (no bench): `close` compares none of the users' files after T88's
   solo. Solo's lines could write the files' before as bench does, so every solo is checked the same way.
3. **The kept folders want a mid-match state:** T88 needs one save; T89 needs one save and three results rows before
   its rehearse can be met. If the rehearsal is meant to prove learn on T89 too, that is four saves at the TV.
4. **rehearse runs a setup's kept states without the setup's cheats** (B95's Session has none): it showed pictures in
   H7-V1, but a title whose state needs its cheats loaded would capture wrong pictures; the capture could load the
   setup's cheats (the hub's own cheat file for that setup).
5. **B114's harness at 127,705 of 131,072 bytes** for its child's text: the next inline mode breaks every suite on it
   (B157's and B162's are in their own files for this reason). Running the child from a file would end it.
6. From BB, still open: the board's payout for a lone winner; B130's 15-s window sized from T88; a winner read from the
   "1" alone; the users' own stop path's 2-s wait; the sound after Home.

## Files

This repo: `companion/party_minigame.py`, `companion/plugins/games.py`, `tools/party_add_game.py`;
`tests/b162_solo_safe/` (new), `tests/b163_rehearse/` (new), `tests/b157_add_game/made_up_hub.py` (new),
`tests/b157_add_game/test_b157.py`, `tests/b114_party_minigame_hang/b114_scenario.py`; `handoffs/ADD_GAME_TASK.md`;
`evidence/B162_ADD_GAME_SOLO_SAFE_2026-11-19.md` + `b162_2026-11-19/` (`b162_b163.diff` applies on `58497ab8`),
`evidence/B163_ADD_GAME_REHEARSE_2026-11-19.md` + `b163_2026-11-19/`, `evidence/B164_BOARD_CHECK_RACE_2026-11-19.md` +
`b164_2026-11-19/` (the board's `b164.diff`), `patches/B162_ADD_GAME_SOLO_SAFE.md`, `patches/B163_ADD_GAME_REHEARSE.md`,
`patches/B164_BOARD_CHECK_RACE.md`; `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph after
queue BB's), `logs/b162_git_status.txt`, `logs/b163_git_status.txt`, `logs/b164_git_status.txt` (`logs/` is git-ignored, as BB's),
`handoffs/SESSION_B_STATUS.txt` (one line), this file. **The board's repo:** `checks/hub_minigame_check.gd`.

**The user, now:** this repo — commit the tree (queue BC). **The board's repo** — commit my check file:
`git -C <board repo> add checks/hub_minigame_check.gd && git -C <board repo> commit -m "Hub mini game check: a press counted only during the practice it was shown behind"`.
