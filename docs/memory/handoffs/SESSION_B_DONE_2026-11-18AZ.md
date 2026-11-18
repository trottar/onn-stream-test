# SESSION B — done, 2026-11-18 AZ (QUEUE_2026-11-18AZ: B151 a practice is left by Select, not Start; B152 the changes to B150's PP-H4; run ~16:05Z-17:35Z)

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (queue AY's work in
`58bc6c42`; the prompt files unchanged). No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing
fetched or installed; nothing written to the drive; the users' cheat setups, their slots and in-game saves, the kept H7
folders, the rules folder and `runtime/` pictures not opened. **No emulator title started** (the tests' made-up fake
title only). **Godot headless only, in B111's own scratch copy** of the board's tree (one run, in `tests_others.txt`).
**The board's repo was not touched** — read only: its new commit's names, `game/minigame_screens.gd`'s
`PRACTICE_ENDS`, the README's practice line, my two files' sha256 and comments; its status 0 lines before and after, its
HEAD `674407d`. No title, serial, game id, `profile_id`, character name, cheat name or path in any record; no picture or
sound in git. The `/tmp/b_q37az` copy holds companion/, tools/, tests/, PrivyHub/ (its `app/src` only) — **disclosed:**
my first copy took the whole PrivyHub/ (557 MB with its build output); that copy of mine was removed within the minute
and made again from the sources only. Also removed, all my own scratch made in this queue: the mutation copies (by the
script) and two one-off temp files / a baseline extract used to check that the diff applies. **Nothing else deleted:**
the 153 temp dirs the older suites leave (as in queue AY) stay in my main-disk scratch; the earlier queues' `/tmp/b_*`
copies untouched. Nothing adopted; nothing committed in either repo.

## What was found and built

- **B151 — BUILT** (`evidence/B151_PARTY_PRACTICE_LEFT_BY_SELECT_2026-11-18.md`). **Settled:** the practice's hook
  sees every pad's raw report first — before B141's Select hold, the route and the write. **Start was never
  swallowed:** it reached the title *and* ended the practice. **Select** was held from a held title's launch to a real
  go, practices included, and in a practice did nothing at all; **Select + Start** ended a practice by Start, the title
  getting Start alone. **Now:** a Select press on any pad ends a practice (`"by": "select_button"`). A Select already
  down at the hand-over counts only once let go and pressed again: the bridge keeps each pad's raw Select while the
  hold is on, and `set_party_route` keeps that across its own neutral writes, which would otherwise have marked every
  pad "up" at the hand-over (found while building). Start is not looked at and reaches the title as in a real game;
  Select never reaches the title before a real go; the 90 s bound as it was. **The band: "PRACTICE — press Select
  (Share) to go back"**, B147's placement — **rows 36-85, columns 318-960 of 720p**, every pixel inside the inner 90 %.
- **B152 — below (no code).**

**Tests:** B151 11 (T89-shaped: four seats; Start from every pad in a practice reaches the title, which leaves its
start screen, and the practice goes on; a Select press on each of the four pads ends one; a Select held across the
hand-over; Select + Start; the time; no Select in any report the title gets before the real go; a real go as today);
B134, B145, B144, B147, B143 updated — **three runs each, all OK but one B143 setup error in run 2** (no traceback kept;
three more runs OK — 5 of 6, not explained); the recent and earlier suites once, all OK (B114 and B108 with their
flags-absent tests, B133, B111 with Godot, `art_systems` 120 against the repo); **mutations 4 / 4** (Start kept as the
way out; the hook's first state "up"; the route's neutral writes counted; the old words).

## What I would change (not done — the queue is the task)

1. **B143's one setup error** in six runs: worth a run with the traceback kept (`-v`, the whole output), in case the
   switch's timing has a rare edge.
2. **B150's part 1 (e)** still says "On the bench no pad presses Start, so the practice ends by its own bound": still
   true (no pad presses anything), but its reason now reads "Select". Not in B152's list, so left as it is.
3. **My board file's header comment** (`minigames/hub_minigame.gd`, line 30) says "its Start pressed within a poll of
   the hand-over". A comment only, no behaviour; it should say Select whenever that file is next changed. My check file
   needs nothing, and neither file needs anything for this queue.
4. **The band is 3 px wider than half the frame** (643 of 1280). It is inside the inner 90 % and a 4:3 title's own
   columns, so B147's test now uses that bound. If the users find it covers too much, "PRACTICE — Select (Share) to go
   back" would save about 70 px.
5. **Which button is "Select" on the users' pads:** "Share" names a PlayStation pad's. On an Xbox-style pad it is View
   (the two overlapping squares). The lines below name both only if the users' pads are mixed.
6. From AY, still open: the switch's own gap with no sound; the import's bound against a big push; the onn's Home during
   the load screen gives the mini game up; `announce_minigame` still says "On the hub".

## B152 — the changes to B150's PP-H4 sketch (`SESSION_B_DONE_2026-11-18AY.md`), as exact strings; nothing else re-written

**Stage 1, 2 (this repo).** The precondition's words, because the new greps need B151 committed:
`queue AY and PP-H3d's record committed` → `queue AZ committed`; `"YOU, now: commit queue AY first, then send the read
line again"` → `"YOU, now: commit queue AZ first, then send the read line again"`. **Added after** `` `grep -c "def
party_hold_select" companion/native_session_io.py` → 1 ``:
`grep -c 'press Select (Share) to go back' companion/native_stream.py` → 1; `grep -c '"select_button"'
companion/party_minigame.py` → 1; `grep -c "start_button" companion/party_minigame.py` → 0; `grep -c "def
party_select_down" companion/native_session_io.py` → 1; `grep -c "def _select_hook" companion/party_minigame.py` → 1.
(The rest of 2 unchanged; `y=h*5/100+10:box=1:boxcolor=black@0.72:boxborderw=10|16|10|16` still → 1.)

**Stage 1, 3 (the board's repo). Added after** `` `grep -c 'PrivyParty: hub mini game: cards %d, chose'
"$BOARD/minigames/hub_minigame.gd"` → 3 ``:
**`git -C "$BOARD" merge-base --is-ancestor 674407d HEAD` → true** (the PC side's Select commit), else "YOU, now: in the
board's repo pull the PC side's Select change, then send the read line again"; `grep -c 'const PRACTICE_ENDS := "A
practice ends with the Select button (Share on a PlayStation pad), or after about 90 seconds."'
"$BOARD/game/minigame_screens.gd"` → 1; `grep -c 'Start button' "$BOARD/game/minigame_screens.gd"` → 0.
(My two files' sha256 `3f32d339…` / `01301ec5…` unchanged: the PC side's `674407d` did not touch them.)

**Stage 1, 4.** `At \`32d5329\`:` → `At \`674407d\`:`; `"A practice ends with the Start button, or after about 90
seconds"` → `"A practice ends with the Select button (Share on a PlayStation pad), or after about 90 seconds."`.

**The lines the four get about a practice** (in "On 'started'"), this sentence:
`**△ asks for a practice. A band at the top of the TV says 'PRACTICE — press Start to go back'. Anyone's Start ends it
(or it ends after about 90 seconds) and you are back on the load screen.**`
→
`**△ asks for a practice. A band near the top of the TV says 'PRACTICE — press Select (Share) to go back'. Anyone's
Select button — Share on a PlayStation pad — ends it (or it ends after about 90 seconds) and you are back on the load
screen. In a practice Start works as in the game: in T89 it starts the fight.**`
(In the reply to the users T89 is named; in every record only T89.)

**The cell PR.** `grep -c 'PRACTICE — press Start to go back'` → `grep -c 'PRACTICE — press Select (Share) to go
back'` (the rest of the pipe unchanged: `… | grep -a '^encoder argv:' | grep -c '…'` = the number of practices);
`` `minigame_practice_end` `"by": "start_button"` or `"time"` `` → `` `minigame_practice_end` `"by": "select_button"`
or `"time"` ``.

**`"by": "select_button"`** is the only new word in the hub's rows; every other row, the self-proof, S, its read and
every other cell stay as written.

## Files

`companion/party_minigame.py`, `companion/native_session_io.py`, `companion/native_stream.py`;
`tests/b151_party_select_leaves/` (new), `tests/b114_party_minigame_hang/b114_scenario.py`,
`tests/b134_party_practice/test_b134.py`, `tests/b145_party_small_things/test_b145.py`,
`tests/b144_party_practice_banner/test_b144.py`, `tests/b147_party_band_inside/test_b147.py`;
`evidence/B151_PARTY_PRACTICE_LEFT_BY_SELECT_2026-11-18.md` + `b151_2026-11-18/` (`b151.diff` applies on `58bc6c42`),
`patches/B151_PARTY_PRACTICE_LEFT_BY_SELECT.md`. Then `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md`
(one paragraph after queue AY's), `logs/b151_git_status.txt`, `handoffs/SESSION_B_STATUS.txt` (one line), this file.

**The user, now:** this repo — commit the tree (queue AZ's B151-B152). The board's repo — nothing.
