---
memory_schema: 1
as_of: 2026-11-20
status: BUILT (B175 every save read by a spec learnt without it; B176 a save in the wrong role, the same match saved twice) — the tool only; a cell added, no bar lowered or changed; the learner not changed; no title started; nothing adopted
---

# B175 — a cell for a match the spec did not learn from (and B176, two plain hints)

Queue: `handoffs/QUEUE_2026-11-20BF.md` §B175, §B176. The directory is `b175_2026-11-20/`:
- the design + `.sha256` (hashed 2026-11-20T02:06:35Z, before any code) and its addendum after the code (hashed);
- `table.txt` / `cost.txt` and their scripts; the tests ×3; the mutations; the checks; `manifest.sha256`;
- `b175_b176.diff` (applies on `dbbc316b`).

Patches: `patches/B175_ADD_GAME_LEFT_OUT.md`, `patches/B176_ADD_GAME_TWO_HINTS.md`. **No title was started**: every
proof below is on made-up titles.

## B175 — the cell

**For every ending's every save** (saves that are the same picture count as one match and are left out together), learn:
1. learns again **without that match's saves** — learn's own call, everything else as it is;
2. replays each of them through that spec, as learn's replays read a save.

**Met** when it ends as its own ending within `ended_within_s` (2.0 s, the replay's bar today) **and never as another**.
One cell per save: `left out: end_P1_2`, read `["end_P1", 2.0]`, bar `"end_P1 within <= 2.0 s, never another"`.
- An ending with one match cannot be left out: the cell is not met, read "its ending's only match".
- **The spec written to the rules folder is still the one learnt from every save** (a test compares it).
- **The line for one more save follows the cell**, the cap as today, counted in matches.
- **rehearse** carries the cell: it runs learn's whole path in its scratch (a test).
- **bench is unchanged**: it only loads each save into the hub and reads it with the rules already written; it learns
  nothing.

## The made-up titles with the new cell (`table.txt`; each save asked given from another look, as the user would)

| made-up title (saves) | today's cells | left out | same picture | the line | asked | then |
| --- | --- | --- | --- | --- | --- | --- |
| one per ending, other characters in each (**settle's weak pass**) | all met | **0 of 2** (its ending's only match) | met | one more save: end_P1_2 | — | **FAIL** |
| two per ending, other characters in every match | all met | **0 of 4** (end_P2 read as end_P1; three never ended) | met | one more save: end_P1_3 | end_P1_3, end_P2_3, end_P2_4 | **PASS** (3 + 4) |
| near-alike, two per ending, P2's first with P1's characters | all met | 1 of 4 | met | one more save: end_P1_3 | end_P1_3, end_P2_3, end_P2_4 | **the cap** (end_P2) |
| near-alike, **three** per ending, other characters | all met | **6 of 6** | met | — | — | **PASS** |
| far apart, **two** per ending, other characters | all met | **4 of 4** | met | — | — | **PASS** |
| two per ending, the same characters within an ending (only the cursor moved) | all met | 0 of 4 (each pair one match) | **not met** (0.76-0.79 grey) | same match twice: end_P1, end_P1_2 | — | FAIL |
| two per ending, end_P2_2 holding a P1 win | all met | 0 of 4 | met | one more save: end_P1_3 | end_P1_3, end_P2_3, end_P2_4 | **wrong role: end_P2_2 as end_P1** |
| three per ending, a large mark only the begin shows | **margin_needed** only | 6 of 6 | met | one more save: end_P1_4 | — | FAIL |

**The least saves per ending:**
- **A near-alike title needs at least three per ending**, each from a different match. With two, leaving one out leaves
  one, and the one-save weakness returns.
- **A far-apart title needs two.**
- **Three is the least, not a promise.** The near-alike title whose first P2 match had P1's characters was asked to four
  P2 saves and reached the cap. Its P2 save with P1's characters, left out, is never read as P2: the spec does tie those
  characters to P1, and on the board it would credit the wrong player. That is what the cell is for, and it means the
  cell can be hard to meet.

**What it costs** (`cost.txt`): one learn per match left out (`es.learn` as it is), plus each left-out save's replay (~0.2
s at the larger size): at 1280 x 960 (the hub's 4x of a 320 x 240
game; 21 pictures a save), **two players: 3.5 s with two saves an ending, 6.7 s with three, 11.0 s with four; four
players: 10.9 / 22.8 / 38.3 s** (made-up 320 x 240: 0.6 / 1.2 / 2.0 s and 1.9 / 4.1 / 7.5 s). The wrong-role check adds
one learn per suspect, only when the full spec already fails. Against a capture of ~20-40 s a save, it is small; the learner is called as it is, with
no faster path.

## B176 — the two hints

- **The same match saved twice:**
  - **The measure:** each save's screen that stays (the anchor learn's labels already pick), 64 x 48 grey, mean absolute
    difference; under 1.0 grey is the same picture.
  - **The bar (`SAME_PICTURE`, a constant beside `BARS`):** H7-V1's kept number for one T88 state run twice ("391 of 400
    frames under 1.0").
  - **Made-up:** the same look with other noise 0.27; only the cursor moved 0.76-0.79; one look, end_P1 vs end_P2 (the
    tally alone) 0.54; other characters 16-32.
  - Cell `no two saves of one ending the same picture`. The pair counts as one match (the left-out cell, the line's
    count, the cap). The line, word for word: "end_P1 and end_P1_2 look like the same match saved twice: save end_P1_2
    again from another match."
- **A save in the wrong role (winner):** "A save may be in the wrong role: end_P2_2 reads as end_P1. Check which player
  won that match; collect it again under the right role." No save is asked for until it is cleared.
  - **The rule was changed after the hash** (`design_addendum_after_code.md`). As worded in the queue, and as designed,
    it would accuse a right save. On the made-up title with the right roles, a save left out was read as the other
    ending with two and with three saves an ending. On the mislabel, the wrong save left out never ended; it was read
    unknown, never "as another".
  - **What tells them apart:** a mislabel spoils the spec learnt from every save; a thin ending does not.
  - **As built**, a save is named when **(a)** the full spec reads its held-out frames as another ending, or **(b)** all
    four hold: the spec from every save does not meet separable / margin / unknown; the save's left-out cell is not met;
    its ending kept two other matches; and relabelling that save alone as the other ending makes the full spec meet
    learn's bars.
  - **Result:** the right-roles title is never accused (asked three saves, PASS); the mislabel is asked the same three,
    then named, with nothing more asked.
- **One line, in this order:** wrong role, the same match twice, one more save, the cap. It is recorded with the line
  itself (`recorded.line`), so rehearse carries it ("then rehearse <code> --collect <role>=<slot>").

## Tests and mutations

**Tests (`tests/b175_left_out/`, 9; temp dirs removed):**
- Each row of the table, through learn.
- One row through register (the made-up hub, the user's made-up slots).
- The spec written equals the one learnt from every save.
- rehearse carries the cell.
- No bar changed (checked after every test).

**Runs:** 9 OK ×3 (`tests_x3.txt`). B171's and B163's suites ×2 (updated); B157, B162, B167, B169 ×1 — all OK.

**Mutations (`tests_mutations.txt`), each caught by B175's own suite:** **6 of 6.**
- **The left-out cell always met:** the weak pass and the others PASS → caught.
- **The left-out save still among the sources:** each save read by a spec that learnt it → caught.
- **The margin cell alone always met:** caught by the made-up title whose margin alone fails (test 7), and by the
  wrong-role test. B171's suite could not catch this one in queue BE; B175's does.
- **The same-picture measure off:** caught.
- **The wrong-role rule without the relabel check:** it accuses the right saves → caught.
- **The wrong-role line still asking a save:** caught.

**Earlier suites updated, disclosed (no bar, no cell of theirs changed):**
- **B157:** its made-up capture now gives another save of the same screen other pictures (seeded by the whole state).
  Otherwise its second saves are the same picture, which B176 now rightly calls one match.
- **B163:** its made-up kept folder has a second save of `end_P2` (`end_p2_c`); one save cannot be left out.
- **B171:** its rows use saves of other looks; its asks are as the new cell gives them (near-alike: `end_P1_3`,
  `end_P2_3`, `end_P2_4`; T88's shape through rehearse: `end_P1_2`, `end_P2_2`, `end_P1_3`, `end_P2_3`, then PASS).
- **`near_capture.py`:** a cursor placed by hand and a begin-only mark.

## What it does not prove

- **That T88 or a new real title meets the cell on three saves.** Real end screens are not the made-up ones; T88's
  rehearsal now needs at least three saves of each win, each with other characters.
- **That two matches the user calls different differ in more than the 1.0-grey measure.** A title whose end screen
  shows nothing that changes between matches would have every second save named "the same match", and could not be
  added this way. No such title is known; said here so it is not a surprise.
- **Four players / places on the real capture:** B157's made-up four-player places title meets the cell.
