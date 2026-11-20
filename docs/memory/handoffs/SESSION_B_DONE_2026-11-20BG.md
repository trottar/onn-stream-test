# SESSION B — done, 2026-11-20 BG (QUEUE_2026-11-20BG: B178 the `score` result kind; B179 the stop at the questions; B180 the user's part; run ~19:15Z-21:00Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active (user units; none system-wide);
- `git status --short` empty, T90's record committed (`3e44c1d5`, `b243dd63`).

**B178's exception:** **not used.** The picture source never ran and no title was started. T90's six saves already had
pictures (made by session A's learn); they were copied, read only, to a scratch off the repo, and removed after the
record.

**Rules kept:**
- No stream, no companion or keeper restart, no flag set on the hub, no adb, no sudo, no nft; nothing fetched or
  installed; nothing written to the drive.
- Read only: the users' setups, slots and saves, the kept H7 folders, the rules folder, the tool's T90 folder.
- No bar in `BARS` lowered or changed; `winner` / `places` and T88's / T89's rules unchanged.
- The app and the board's repo not touched.
- No title, id, path or picture in any record (the three checks).

Nothing adopted; nothing committed in either repo.

## Where T90's scores sit, and how they are read

- **Where:**
  - twice on the final screen, at the same places every match: large under each side's emblem (P1 left), and the
    FINAL column of the bottom table (P1's row above P2's);
  - the final screen holds still 6.5-9 s, then a loading screen;
  - the reader uses **the FINAL column for both sides** (16 px tall at 640 × 480). P2's large number touches its
    panel's edge highlight and never sits on one line.
- **How:**
  - a digit reader learnt from T90's own glyphs in the labelled saves (spec version 4, PIL + numpy; no OCR package is
    on the hub);
  - each digit read only within its learnt threshold and margin — the largest 3 × 3 local difference to its template;
  - deterministic: the same picture always gives the same numbers.

## B178 — BUILT (`evidence/B178_ADD_GAME_SCORE_KIND_2026-11-20.md`, `b178_2026-11-20/`, `patches/B178_…`)

- **The label stage, the one picture the session reads:**
  - `label <code>` puts two pictures of each end save's final screen, two ticks apart, off the repo, and each side's
    number cut out once the places are known;
  - the session passes `end_P1=15-2,15-2 …`;
  - **the tool checks every reading:** the two the same; the role's player ahead; the numbers at one place in every
    save; read back by a reader learnt without that save;
  - its line names **the misread save alone** (addendum 3);
  - the same save named again after a re-read → **ask the user for that one save's numbers.** The user types nothing
    otherwise.
- **How far the checks catch a misread** (`table.txt`, made-up titles):
  - **caught, that save named alone:** a reading differing between the two pictures; a digit misread as any other
    digit (twice, consistently); the sides swapped; a digit dropped;
  - **caught later:** a misread on a digit only one save shows. Learn cannot pass with it, and the label stage names
    the save once another save shows that digit;
  - **gets through:** one glyph misread the same way in every save that shows it.
- **learn:**
  - each side's place and the title's digits;
  - every save read exactly by a spec learnt without it (B175 for numbers);
  - the final screen held to T88's bars;
  - the digit margin held to today's 0.0796;
  - its line names the digits another save must show.
- **The hub:** the real numbers; the winner the side strictly ahead; **a tie null**. An unreadable final screen is
  `unknown`: no result, never a guess.
- **Tests and checks:**
  - 23 tests ×3 on the final code;
  - mutations 5 of 5 caught by B178's own suite: a score read by a spec that saw the save; a tie taken as a win; an
    unread digit guessed; the role check skipped; one reading accepted where two disagree;
  - B157-B176 and the suites of the files touched green;
  - the flags absent → HEAD's bytes on today's routes.

**T90 with my labels:**
- my readings, the same from both pictures: 15-2, 35-28, 0-22, 0-29;
- label: **PASS**;
- learn: **FAIL**, 20 of 23 cells met. Not met: left out end_P1, end_P1_2 and end_P2_2. Each holds a digit no other
  save shows (1; 3 and 8; 9). Each stayed unread, at 0.72-0.79 against bars of 0.43-0.47; none was guessed;
- learn's line: "One more save: a match either player won whose final score shows 1, 3, 8 or 9 …".

**A tie, read only on the board:**
- `[14, 14]` → places `[0, 0]` → coins `[10, 10]`, and no mini game won;
- the same as the board's own draw (a mini game given up);
- **the PC side should change it if a draw is not meant to pay everyone the winner's coins** (a draw row, e.g. the
  second place's coins for all, or nothing). The hub cannot say it through the scores.

**The least labelled saves:** every digit an end save shows must be shown by another end save.
- 4 end saves (6 saves in all) when the final scores share their digits;
- one more for each digit only one save shows, and one match can carry several;
- in practice 5-6 end saves; at most the cap, 4 per player.

## B179 — DONE (`handoffs/ADD_GAME_TASK.md`; the template unchanged, sha256 `4ba6a99a…` before = after)

- **§1:**
  - a third answer, "the scores (or points, a count) of each side" → `--result score`, with `winner`'s saves;
  - a fourth, "some other way" → **stop at the questions before any save**, with the exact line;
  - the same stop for any answer the tool has no kind for, or when unsure;
  - saves already kept under a code (T90's six) stay.
- **§2:** the `label` stage, its lines, and the line to the user after a second disagreement; learn's score line
  word for word.
- **§4:** the score kind's saves.

## B180 — the user's part (no code)

**A two-player `score` title, as the task now has it:**
- **Saves:** 6 at the least, when the four final scores share their digits; in practice 7-8; at most 10.
- **The numbers on the final screen are read by the session.** The user is asked one match's final score only when
  the session's readings of it disagree twice.

1. Tell the session which game the code is (in chat only).
2. Answer: two players; who won is shown by each side's score on the screen after a match; anything to unlock; the
   words to find it in Games.
3. Set the shortest match, the same for every save.
4. Round 1: slot 1 the select screen before anyone picks; slot 2 the middle of a match; slot 3 the final score screen
   after a match P1 won.
5. Round 2, each match with other teams (or characters): P2 wins → slot 1; P1 wins → slot 2; P2 wins → slot 3. Each
   on the final score screen. Say only who won.
6. Then, only as the session asks, one at a time:
   - one more match whose final score shows a digit it names, in either side's score; save it on the final score
     screen to slot 2 or 3, and say who won;
   - if asked for one match's final score, reply like "21-14".
7. Nothing during bench.
8. Solo: the pads on the onn; follow the lines; say who won (or "a tie") and whether the board showed one card.
9. If the session says the game shows who won in a way the hub can't read yet, it goes back to Cowork.
10. Commit.

**T90 now: it cannot pass on its six kept saves as they are.** With my labels, learn needs **at least one more saved
match whose final score shows a 1, 3, 8 or 9**. One score can carry all four (e.g. 39-18); otherwise one more match per
digit still missing.
- The six saves stay. Session A re-registers T90 as `score` with no new saves, labels the six itself, and learn asks
  for that match.
- Then: the one more match (other teams, trying for those digits; saved on the final score screen to slot 2 or 3;
  say who won); nothing during bench; solo; commit.

**The one line the user types in session A:**

```
Read docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt, put T90 where it says ____, and follow it as my prompt.
```

At the questions, answer "who won is shown how" with: the scores of each side on the final stats screen, the winner
the side with more.

## What I would change (not done — the queue is the task)

1. **A final screen read but not readable waits too long.** A match ending with a digit no save has shown (T90 has
   never shown 4, 6 or 7) reads `unknown`, never a guess. T90's screen moves on after ~8 s, so the 30-s unknown rule
   never fires and the mini game waits until the 900-s play limit or the user's end. I would give such a match up at
   once, as a draw, after K agreeing reads of the final screen with a number not read. A stricter alternative: make
   learn require every digit 0-9 in two saves. Your call.
2. **The systematic misread:** before label's PASS, the stage could put every glyph read as the same digit side by
   side in one picture, for one last look. That would catch "every 4 read as 9", the one misread that gets through.
3. **The template says "You never judge a picture"**, and the label stage is the exception. The task says so; the
   template, unchanged by the queue, does not.
4. **B167's anchor** (learn's "screen that stays", the frame most of the run stays near) would label a final screen
   held for less of its 20-s run than a later screen on that later screen. T90's is fine. The first screen held 3 s
   after the load would be safer.
5. **The board's draw pays both players the winner's coins.** That is the PC side's call (above).

## Files

- **This repo:**
  - code: `tools/h7_endscreen.py`, `tools/party_add_game.py`, `companion/h7_minigame.py`,
    `companion/party_minigame.py`;
  - tests: `tests/b178_score_kind/` (new); `tests/b114_party_minigame_hang/b114_scenario.py` (one `b178` mode,
    disclosed).
- **Handoffs:** `handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt` (one line), and this file.
- **The record:** `evidence/B178_ADD_GAME_SCORE_KIND_2026-11-20.md` + `b178_2026-11-20/`:
  - the design and three addenda, each hashed;
  - `t90/` (label and learn pages, `settle.txt`);
  - `table.txt`, `tests_x3.txt`, `tests_mutations.txt`, the checks, `scripts/`;
  - `b178.diff` (applies on `b243dd63`), `apply_check.txt`, `manifest.sha256`.
- **Patch:** `patches/B178_ADD_GAME_SCORE_KIND.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b178_git_status.txt` (`logs/` is git-ignored).
- **The board's repo:** nothing.

**The user, now:** this repo — commit the tree (queue BG). The board's repo — nothing to commit.
