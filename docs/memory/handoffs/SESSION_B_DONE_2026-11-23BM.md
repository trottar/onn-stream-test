# SESSION B — done, 2026-11-23 BM (QUEUE_2026-11-23BM: B200 the place finder on T92's screen; B201 `--find`; B202 the user's saves asked only through register; B203 T92 from its six kept saves; run ~18:20Z-23:30Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; T92's first record committed (`ec6d8ea9`).

**Rules kept:**
- No stream, no companion or keeper restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to
  the drive; nothing deleted by hand (three temp dirs of stopped test runs stay in my scratch, off the repo — the
  record says so).
- **The picture source never ran:** T92's pictures were reused because its kept states are unchanged. `status` and
  `native-stream-status` were checked first anyway: nothing running, no client.
- Read only: your setups, slots and in-game saves, the kept H7 folders, the runtime pictures, and the rules folder
  (sha256 before = after learn).
- No bar in `BARS` lowered; T88-T91's rules unchanged; the sum check, the two readings, the last look and the
  left-out cells stay. The app and the board's repo were not touched. The template is unchanged (`aadccb04…`).
- No title, serial, game id, profile_id, team or character name, cheat name or path in any record (four checks).
- Nothing adopted; nothing committed in either repo.

## B200 — BUILT

- **Settled from T92's pictures:**
  - each final is a big number either side of a small box;
  - the box holds a cell per period for each side (1ST, 2ND, 1EX, 2EX, PK), a quarter the finals' height, **above
    their line, not on it**;
  - **every number is two digits with a leading 0**: the finals, the cells and the stats table;
  - the same shape in every save: the box, the headings, the "--" blanks, the stats headings, and the hollow inside
    every final's leading 0.
- **Numbers are read as drawn:** "03" is 3 for every check and the glyphs 0 and 3 for every count; the leading 0 is a
  0 learnt. The label line says so. A title that does not pad works as before.
- **A place whose glyphs are the same shape in saves labelled with different digits is never taken.** One save may be
  excused while the others still differ there (one misread save is then named by the read-back, as before).
- **Cells off the final's line are found where they are.** They get their own template group and teach no final's
  digit.
- **T90's and T91's label and learn verdicts are the same** (T91's file differs only in its recorded training time).
- **Disclosed:**
  - the same-shape rule as built differs from the hashed one;
  - three more fixes found while building;
  - one earlier test's assertion changed (B198's `Limit`: still never a PASS).

## B201 — BUILT

- **Why every title answered:** the hub's library applies `q` only with `view=search`, so it listed all 72 titles.
- **`--find` now takes your words as you say them:** a part of the name, the name without its region, or the whole
  name. It finds one title, or names 2-6 candidates for the chat only (never written).

## B202 — DONE (`ADD_GAME_TASK.md`)

- Register runs with round 1's collects first. **The session never asks you to make a save before register says it is
  missing.**
- **No "other teams / characters" for score and letters titles.**
- **"The same match saved twice" stays:** one match's glyphs must not count twice. It is told by the whole screen,
  never by the teams.
- **The highest score is asked once;** a later change is taken as you say it.

## B203 — T92

| stage | verdict |
| --- | --- |
| register `--max-score 5`, no `--collect` | **PASS** (9) |
| label (my readings as drawn, the last look `all`) | **PASS** (19) |
| learn | **FAIL** (24) |

learn's line: **one more match showing 1, 3, 4 or 5.**
- 0 is covered by every save's leading zeros, and 2 is in three saves.
- 1 is in no number read: the stats table is never read.
- 3, 4 and 5 are each in one save, once at the finals' size. The small cell's copy is another size, so B186's rule
  does not cover them.

Each must show twice in the finals: expect at least three more matches.

The first label run ran before the last fix (it asked to read end_P2 again; read again, the same). Disclosed.

## What I would change (not done — the queue is the task)

1. **Read T92's stats table too.** Its 01 and 13 show a 1 in every match with a shot or a corner. Labelling those
   cells would cover 1 without waiting for a score of 1. It needs the session to read more numbers per save.
2. **Let one save's small cell count with its final when the fonts match.** T92's cells are another size, so they
   cannot. A title whose cells are the finals' font at another size could be measured and pooled.
3. **The finals' moving background:** the hub ends on its first 3 agreeing reads, before the glyph drops. A read on
   the cells (always clean) as a fallback would make that certain.
4. **The one-save excuse** lets a junk place stand on a made-up screen with three saves (it fails safe at the
   read-back). Requiring four saves before excusing one would close it, at the cost of naming two saves where one
   would do.

## Files

- **Code:** `tools/h7_endscreen.py`, `tools/party_add_game.py`.
- **Tests:**
  - `tests/b200_drawn_places/` (new);
  - `tests/b201_find/` (new);
  - `tests/b198_max_score/test_b198.py` (`Limit`'s assertion).
- **Handoffs:** `ADD_GAME_TASK.md`, `SESSION_B_STATUS.txt`, this file.
- **Record:** `evidence/B200_DRAWN_PLACES_FIND_2026-11-23.md` + `b200_2026-11-23/`, and T92's verdicts
  (`add_game/T92/label.*`, `learn.*`).
- **Patch:** `patches/B200_DRAWN_PLACES_FIND.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b200_git_status.txt`.

## T92 now

T92 is at learn. Its six saves stand; it needs matches showing **1, 3, 4 or 5** in either side's final score, each
digit in two matches. Session A asks one match at a time (any teams): save it on the screen after the match to slot 2
or 3, say who won, and it runs register, label (its own reading) and learn again. Then bench, and solo with you.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_TASK.md and continue T92 (score, two players, --max-score 5) from learn's line: ask me for one more match showing a 1, 3, 4 or 5, as §1 and §2 say — no questions already answered, no other teams.
```
