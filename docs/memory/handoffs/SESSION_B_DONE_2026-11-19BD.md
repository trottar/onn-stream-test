# SESSION B — done, 2026-11-19 BD (QUEUE_2026-11-19BD: B167 learn's picture source starts; B168 the board after a practice; B169 two cells for solo; B170 the fixed task; run ~23:15Z-23:59Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide); `git status
--short` empty (the first use in `df81c762`); my check file committed in the board's repo (`c8fc348`, sha256
`a71b4d8f…`, its status empty). **The queue's exception, used six times:** `python3 tools/party_add_game.py rehearse
T88 --collect other=2`, each time after `status` and `native-stream-status` showed nothing running and no client;
headless (the window on the hub's display, nothing streamed), no companion restart, no flag set; the user's slot 2 and
the kept folder only read; **every run and its verdict in `evidence/b167_2026-11-19/runs.md`**; the real rules folder
15 files, 0 changed, every run. **Run 1 was run with `TMPDIR` pointed at a private folder and a watcher copying
RetroArch's log out of the capture's temp folder before the tool's cleanup; run 5 with a watcher copying the scratch's
pictures** — both copies in my own scratch on the main disk, off the repo; the pictures removed after the record, run 1's
two logs kept there (they name the game). Nothing else started a title. No stream, no companion or keeper restart, no
adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; the users' setups, slots and in-game
saves, the kept H7 folders, the rules folder and `runtime/` pictures read only. **Read only beyond the tool, disclosed:**
the hub's RetroArch user config folder (its core options, names only; the capture now copies them), xfwm4's settings
file (two keys), the T88 binding's game file path tested for existence (never printed). **No Godot run** (B168 read
code only). **No change in the board's repo.** No title, id, path or picture in any record (the three checks).
**Disclosed: the tool's own page `add_game/T88/rehearse.*` in this repo now holds run 6's verdict** (the first use's is
in `df81c762`). Nothing adopted; nothing committed in either repo.

## Why RetroArch exited at startup — in one line

**It was given no display:** the tool runs from a shell with no `DISPLAY`/`XAUTHORITY`, so RetroArch found no X
display, no Wayland server, could not switch the KMS mode and logged "Cannot open video driver. Exiting...".

## B167 — BUILT (`evidence/B167_ADD_GAME_PICTURES_START_2026-11-19.md`, `b167_2026-11-19/`, `patches/B167_…`)

The capture starts as the hub starts the title: **the hub's display** (from the user manager the companion runs
under), **its own core** per system (bsnes for SNES, not B95's snes9x), **its own core options** (as H7-V1 did: the
render scale), never beside a game or a client's stream; every failure **a name-free reason** in a cell ("pictures
made": busy, display, content not found, core missing, config, exited, not playing, state refused), never "ProofError"
alone; **RetroArch's log kept in the title's add_game folder** (`logs/`). Found by the real runs and fixed: the
screenshot read whole (4x PNGs); **for a title already added, the begin its mini game starts from** (T88's kept begin
was the plain one from before its setup); **learn's labels anchored on the screen that stays** (T88's kept end_p1 was
saved a moment before its end screen settled; the old labels took the transitional frame). **The setup's cheats:
settled, not needed** — the real rules read T88's captured endings (no cheats loaded) as their own on every run.

**rehearse T88, as I ran it: FAIL (run 6) — on learn's own bars:** every class separable [end_P1, end_P2] not met,
margin_needed 0.0164 (bar 0.0796), held-out unknown 0.6552, the endings' replays not ended; the real rules folder before
= after **met**; the scratch removed **met**. **Why:** T88's end screen is its select screen with a per-side win tally;
from one still save per ending (one source to the learner) the outcome mask is wherever start and the endings differ,
and the tally is a few pixels of it. The real spec (0.0921) was learnt from three sittings. No bar loosened; the learner
not changed. **What it proves of learn for a new title:** its picture source now starts and runs on the hub (display,
core, options, a kept state and a user's slot loaded, every picture at the hub's scale, the log kept), the real rules
agree with those pictures, learn's whole path runs and speaks in cells, the real rules stay untouched. **What it does
not:** that one save per ending meets learn's bars — for a title whose endings differ only a little it will not (each
ending saved in two different matches would give the learner what the sittings gave); another core (N64, SNES's bsnes);
a title on the drive (T88's is on the hub's own disk); four players / `places`.

Tests 9 ×3 (each reason with a made-up RetroArch, the hub's start, learn's cell, the labels), B163 7 ×2 (updated), B157
17, B162 17 ×2 (updated for B169); **mutations 9 / 9 caught.**

## B168 — the board for a second after a practice: settled from the code; neither board file draws it

Frame by frame, from the practice's end to the load screen seen, by the code of both sides:

1. **The hub's way back** (`companion/party_minigame.py` `_way_back`): pause, unroute, **the planned switch to the
   board's window (line 929)**, and only then `state = "starting"` (line 932). The hand-over is the same order: the
   switch to the title (875), then `playing` (886).
2. **My file** (`minigames/hub_minigame.gd`): the load screen is up when the practice is chosen; at the first poll that
   sees the practice `playing` it is shown again behind it (**line 254**, "load screen again" — the first use's board log
   has it before `start`); it is **never hidden for a practice** (the hide at **261** is only `not practising`, and the
   hub says `playing` there only after its switch to the title). At the way back's first poll (`POLL_SECONDS` 1.0)
   **line 212** lifts the gate and the frame cap (`IDLE_FPS` 10, line 95) and shows nothing: the screen is already up.
3. **The PC side** (read only): `presenter.gd` `show_minigame_loading` (**1827**) → `minigame_screens.gd` `show_loading`
   (**243**): mode, `visible = true`, one `queue_redraw()` — **at once, no entrance from nothing**; called while already
   up it changes nothing that is seen. Under the cap a redraw waits at most one frame (0.1 s), not a second. The screen
   has no code of its own that takes it down (`hide_loading`, 279, only on the board's hide).

**So by the code the board's window holds the load screen from before the practice's go to after its way back; a second
of bare board is not drawn by either board file.** What remains is between the board's window and the onn: the stream
grabs the board's own X window (`x11grab -window_id`), under xfwm4's compositor with `unredirect_overlays` on, while the
paused title's full-screen window stays mapped above it. **Not fixed (not in my files); no note for the PC side's
screens.** What would settle it — for a later item, not done here: on a bench, grab the board's window by id (as the
stream does) every 0.1 s from the way back's switch for 2 s with the title held above it, and see whether the first
frames are the load screen, the board, or the title. PP-H4's "went to board for a second before load" and the first
use's both came with a practice; the user's second answer ("it was the board right before mini-game launched") may
describe the load screen itself.

## B169 — BUILT (`evidence/B169_SOLO_TWO_CELLS_2026-11-19.md`, `b169_2026-11-19/`, `patches/B169_…`)

"**the board showed one card**" (the board's own `cards <n>` line, bar 1); **a title already added gets its files'
before at solo's first run**, so close compares the users' files after every solo (in-game saves recorded as before).
Tests 5 ×3; mutations 2 / 2. It showed at once: B162's harness rewrites a sidecar after T90's solo, and close now says so.

## B170 — DONE (`handoffs/ADD_GAME_TASK.md`; the template unchanged, sha256 `4ba6a99a…` before = after)

At the very start, once, in chat only: "YOU, now: which game is <code>? I will not write its name anywhere." — the name
used only in replies; **never slot 1 under a setup** (§0's save, §1's rounds — round 2 now slot 2); §0's rehearse as
B167 leaves it — **the user's mid-match save stays usable until they save over that slot** (`--collect other=<the same
slot>` each time, no new save asked); for T88 rehearse is FAIL on learn's bars today, so in §0 it stops only on its real
rules cell or a "pictures made" reason; B169's two cells.

## What I would change (not done — the queue is the task)

1. **A new title's saves:** each ending saved in **two different matches** (`end_P1`, `end_P1_2` …), so learn has the
   variety T88's sittings gave; today's one-save-per-ending learn will fail its own margin for any title whose endings
   differ only a little. (`register`'s roles and learn's sources would take them; the learner unchanged.)
2. **The capture's frames:** at the hub's 4x scale about half the 0.5-s ticks gave a picture (21 of 41); SCREENSHOT is
   slow. A capture grabbing the window (as the stream does) would give every tick.
3. **B168's measurement** above, as its own bench item.
4. **The solo mark lasts across solos:** a later solo of the same code reuses the first one's mark (its launches, its
   board lines); close could end the mark.
5. From before, still open: the board's payout for a lone winner; B130's 15-s window; B114's harness at 127,705 bytes.

## Files

This repo: `tools/party_add_game.py`, `tools/party_add_game_capture.py`; `tests/b167_pictures_start/` (new),
`tests/b169_solo_cells/` (new), `tests/b163_rehearse/test_b163.py`, `tests/b162_solo_safe/test_b162.py`;
`handoffs/ADD_GAME_TASK.md`; `evidence/add_game/T88/rehearse.json` / `.md` (the tool's own page, run 6);
`evidence/B167_ADD_GAME_PICTURES_START_2026-11-19.md` + `b167_2026-11-19/` (`b167_b169.diff` applies on `df81c762`),
`evidence/B169_SOLO_TWO_CELLS_2026-11-19.md` + `b169_2026-11-19/`, `patches/B167_ADD_GAME_PICTURES_START.md`,
`patches/B169_SOLO_TWO_CELLS.md`; `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph),
`logs/b167_git_status.txt`, `logs/b169_git_status.txt` (`logs/` is git-ignored), `handoffs/SESSION_B_STATUS.txt` (one
line), this file. **The board's repo: nothing.**

**The user, now:** this repo — commit the tree (queue BD). The board's repo — nothing to commit.
