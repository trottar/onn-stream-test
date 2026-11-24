---
memory_schema: 1
as_of: 2026-11-24
status: AUDIT (Cowork, read from the raw artifacts and the code on the hub) — the add-a-game work from 2026-11-20 (queue BG) to 2026-11-24 (queue BO), the stretch run without the usual review depth. T90 and T91 are added and proven by real matches; T92 is not; the tool has more than doubled in size and its score reader is at the edge of its own bars. Recommends a freeze and one rebuild of the front of the path around the user's five steps. Nothing adopted; nothing committed by this file
---

# Audit — adding mini games, 2026-11-20 to 2026-11-24

## 1. Where things stand

| title | kind | state | proof |
| --- | --- | --- | --- |
| T88, T89 | winner / places | as before (PP-H4) | untouched: their rules' files and the hub's version-2 / 3 paths unchanged |
| T90 | score | **added**, every stage PASS (2026-11-21) | a real match read 16-14, the user's winner; the bench ended all five kept endings right |
| T91 | letters | **added**, every stage PASS (2026-11-23) | two real matches read right (both P1 wins); the bench ended both players' kept endings right |
| T92 | score | **not added** — stopped at label twice (2026-11-23, 2026-11-24) | — |

T90 and T91 are offered by the board only under the two bench flags. Nothing is adopted. The eighteen lines stand.

## 2. What it cost

- **Nine B queues in four days** (BG-BO), about 17 h 40 of session B time: BG 1:45, BH 1:25, BI 2:40, BJ 2:40, BK 0:40, BL 1:25, BM 5:10, BN 0:55, BO 1:00.
- **Eight session A runs for three titles**; six of them stopped or failed before the end (T90 two, T91 one at learn and one at solo / close, T92 two).
- **The user's saves:** T90 seven, T91 six, T92 seven — against "three saves and a test" as the aim.
- **Almost four of BM's five hours** were the earlier test suites run one after another three times (B's own account, B207). That was Cowork's standing rule; it was cut only on 2026-11-24.

## 3. What is sound

- **The hub's own changes are small and gated.** `companion/h7_minigame.py` and `companion/party_minigame.py` gained about 80 lines since queue BC: the score and letters entries, the read at the end, the give-up on an unreadable final (B182), a tie as no winner. Each acts only for a title whose sidecar says `score` or `letters`, behind both flags. Read line by line for this audit: no change reaches T88, T89 or a user's own session.
- **The safety net is real:** a final the reader cannot read is given up in about 3 s as a draw — never a guess, never the 15-minute wait.
- **The bars table (`BARS`) was not lowered** (diffed against the 2026-11-20 copy: two entries added, one reworded).
- **The planned switch is fast and stays fast** (1.06-1.34 s in every solo since B153); the practice band, Select, the one-card setting, close's file list all held in every run.
- **The letters kind with synthetic training worked first time on real saves** (T91: 96 synthetic pictures, 2.4 s, every real save read by a reader that never saw it).

## 4. What is not sound

1. **The tool has more than doubled and is now a stack of per-title patches.** `tools/party_add_game.py` 1,928 → 3,536 lines; `tools/h7_endscreen.py` 1,202 → 3,048 lines. Each title's screen broke an assumption and got its own rule: a line score (B181), overtime columns (B185), one-save digits (B186), leading zeros and off-line cells (B200), other sizes (B204), synthetic digits (B205). The letters reader alone carries about 25 hand-set constants fitted on one title.
2. **The score reader is a nearest-template matcher with thresholds learnt from a handful of glyphs, and T92 has pushed it to its edge.** T90's digit margin was 0.2047. T92's was 0.1943 after B204 and **0.0882 after B205, against a bar of 0.0796**. B205's weighting was chosen after its hashed design *because* the first version fell under the bar (0.0625) — disclosed by B, but it is fitting to the bar on the title under test.
3. **Two rules were bent without the table changing.** B186's check (a title's across-save spread ≤ its within-save spread + 0.05) was written for one glyph size; since B204 other sizes sit inside both numbers (T90: 0.40 / 0.42; T92: 0.67 / 0.67), so it no longer says much. And the 0.0796 bar for digits is T89's *screen-class* margin — a different quantity, borrowed.
4. **T92's second stop is that fragility showing.** Adding one more real save (5-6) moved the thresholds so that a digit which read back the day before (the small 3 in end_P1's stats) no longer does. More saves made the reader worse, not better. Another patch would be the tenth.
5. **The test suite has been bent to follow the code.** Earlier suites' assertions were rewritten in BI (B178, B181), BK (B162, five places), BM (B198) and BN (B200, two). Made-up titles' noise depends on test order (disclosed three times). In BO one every-time suite (B185) had not finished at the limit: no result on record.
6. **The fixed task is no longer something a session can follow.** `ADD_GAME_TASK.md` went from 6.9 KB (queue BB) to 39.5 KB, citing thirty B items. Session A's slips — asking for saves already made (twice), unclear asks, promising "one more match" — follow from that file as much as from the session.
7. **Records and state drift.** `CURRENT.md` is as of 2026-11-16 and still names PP-H4 as the work item: nothing of the tool, T90 or T91. Three queue files and one record quote the user with words he asked to be left out of records. The hub tree is shared with the tablet session, and `git add -A` has swept its work into commits named for this work.
8. **Still waiting on the PC side:** a drawn mini game pays half (the note is pushed, not handed over). Until then a T92 draw, or any given-up mini game, pays both players the winner's coins.

## 5. Cowork's own part

- Listed a score-screen title as fitting on 2026-11-20 although B158 had said "not yet": the first T90 run asked for six saves in a mode that could not take it.
- Told the user to make saves he had already made, twice; wrote a round-2 line that saved over slot 1 against his rule; wrote hand steps he could not follow.
- Agreed on synthetic data on 2026-11-21, then answered a missing digit with "play more matches" on 2026-11-23.
- Kept the three-runs-of-every-suite rule until a queue took five hours.
- Handed session A a run before session B's work was committed; told the user to play on the hub while B was running.
- Answered every failure with another queue instead of stopping to look at the whole.

## 6. Recommendation

1. **Freeze.** T90 and T91 stay as they are. No more patches to the score reader for T92.
2. **Rebuild the front of the path once, around the user's five steps** (his words, 2026-11-24): (1) three save slots; (2) Code isolates the region of the result and decides the kind of game; (3) the user collects the data needed, Code makes synthetic data to fill the gaps; (4) train; (5) test with PrivyParty. In the tool's terms:
   - **Survey** (new): from the three saves the session marks each player's result region as a rectangle and names the kind; the tool shows the crops back once. The regions are data — this replaces the place finder and its special cases.
   - **Plan** (new): the tool says, in one list, exactly what it still has not seen (which digits or letters, at the result's own size) — before anything is asked of the user.
   - **Collect:** the user plays; the hub keeps every final screen itself (no slots after the first three). Synthetic pictures cover backgrounds and positions, as T91's did.
   - **Train**, in seconds; **test** from the board; every later play kept, the user's "that one was wrong" relabels it.
   - Kept as they are: the capture, the bench, solo, close, the hub's readers and its give-up.
3. **One rule to decide (the user's):** today a symbol counts only when two real pictures show it. To stop asking for matches, a symbol seen **once** on a real picture would count when the title's font is measured rigid and its synthetic variants are all read — with the give-up as the net and the board test and later plays as the check. This is a lower bar than "two real samples"; it is what the five steps need.
4. **A short, plain task file** for session A (one page), written with the rebuild; the 39 KB file retired.
5. **Housekeeping in the same queue:** `CURRENT.md` brought up to date; the quoted words removed from the four files; every-time suites named (B207's list), run once.

T92 goes through the rebuilt path as its first title.
