# B175 + B176 — a cell for a match the spec did not learn from; two plain hints (design, written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-20BF.md` §B175, §B176. Baseline `dbbc316b`. **The tool only** (`tools/party_add_game.py`);
the learner (`tools/h7_endscreen.py`) not changed, called as it is; **no bar in `BARS` lowered** (none changed: the new
cell uses the replay's existing bar `ended_within_s`; the new measure's bar is a kept number, a constant beside `BARS`);
no title started (every proof on made-up titles).

## Measured first (scratch, the made-up near-alike screens of `tests/b171_more_saves/near_capture.py`, B171's tool)

Leave one save out = learn (the tool's labels, `es.learn` as learn calls it, first halves) with that save's run taken
out of the labels; then that save's pictures replayed through it exactly as learn's replays read a save.

| made-up title | the full spec (today's cells) | each save left out |
| --- | --- | --- |
| one save per ending, other characters in each (settle's weak pass) | PASS (margin 0.1666) | **cannot be learnt: the ending has no other save** |
| two per ending, other characters in every match (P1: looks 1, 2; P2: 3, 4) | PASS (0.1554) | end_P1, end_P1_2, end_P2_2 **never end**; **end_P2 ends as end_P1** |
| near-alike, two per ending (P1: 1, 2; P2: 1, 3 — B171's PASS) | PASS (0.159) | end_P1 and end_P2_2 never end; end_P1_2 ok; **end_P2 ends as end_P1** |
| near-alike, **three** per ending | PASS (0.158) | **every save ends as its own ending at 2.0 s** |
| far apart, two per ending | PASS | every save its own ending at 2.0 s |
| two per ending, the same characters within an ending, other characters between (only the cursor moved) | PASS | every save "its own" — **leave-one-out cannot see this confound** (each ending's other save has the same characters) |

**So:** with two saves an ending, leaving one out leaves one — the one-save weakness again. **A near-alike title needs
three saves per ending from three different matches; a far-apart one two.** The last row is caught by B176's same-match
measure (below): those pairs are the same picture but for a 20-px cursor.

**Mislabels (B176), measured the same way:** two per ending with end_P2_2 holding a P1 win → the full spec PASSes and,
left out, **the correctly labelled end_P2 ends as end_P1** while the mislabelled one never ends — the same signal as the
correct two-per-ending title above. **With two saves an ending, "read as another ending when left out" cannot tell a
wrong role from a thin ending, and as worded the hint would accuse a right save.** Three per ending with end_P2_3
holding a P1 win → the full spec fails (not separable) and **only end_P2_3, left out, ends as end_P1**. So the hint is
given only where the evidence tells the two apart (rule below).

**Same picture (B176):** each save's screen that stays (the anchor frame learn's labels already pick), 64 x 48 grey,
mean absolute difference: the same look with other noise 0.27; the same characters with only the cursor moved 0.76-0.79;
end_P1 vs end_P2 of one look (the tally alone) 0.54; other characters 16-32. **The bar: under 1.0 grey is the same
picture** — H7-V1's kept number for one T88 state run twice ("391 of 400 frames under 1.0 apart; the emulation is
repeatable"), on the same 64 x 48 measure.

**Cost (seconds), one learn per save left out (`es.learn` as it is; pictures 320 x 240 made-up / 1280 x 960, the hub's
4x of a 320 x 240 game):** two players, 2 / 3 / 4 saves an ending: 0.6 / 1.2 / 2.0 s and 3.4 / 6.7 / 10.9 s; four
players, 2 / 4 saves an ending: 1.9 / 7.3 s and 10.9 / 38.2 s; plus each left-out save's replay (~0.2 s at 4x). Against
a capture of ~20-40 s a save, no faster path is needed: the learner is called as it is.

## B175 — the design

1. **The cell, one per save:** for every ending's every save (winner `end_P<k>…`; places `end_r<row>…`), grouped by
   match (B176: saves that are the same picture are one match, left out together): the spec learnt **without that
   match's saves** (everything else as it is, learn's own call, first halves), then each of its saves replayed through
   it as learn's replays read a save (the begin loaded first) — **met when it ends as its own ending (places: its own
   row) within `ended_within_s` (2.0 s, the replay's bar today) and never as another ending** (every end it says, not
   only the first). Cell `left out: <role>`, read `[class, seconds]` (null when it never ends) or the learner's refusal;
   bar `"<its ending> within <= 2.0 s, never another"`.
2. **An ending with one match cannot be left out:** cell not met, read "its ending's only match". (A new title already
   fails register's two-per-ending without it; rehearse of one save per ending shows it.)
3. **The spec written to the rules folder is the one learnt from every save**, as today. The left-out specs are never
   written; their temporary labels file is removed.
4. **The line for one more save follows this cell:** a left-out cell not met names its ending (unless B176's wrong-role
   rule names the save), fewest matches first, the next role, as today; the cap as today, counted in matches.
5. **rehearse** carries the cell (it runs learn's whole path in its scratch); **bench is unchanged** — it only loads
   each save into the hub and reads it with the rules already written; it learns nothing.

## B176 — the design

1. **The same match saved twice:** for each ending, the anchor frames of its saves compared pairwise (the measure
   above); under 1.0 → one match. Cell `no two saves of one ending the same picture`, read the pairs `[a, b, mean
   difference]`, bar `>= 1.0 grey (64 x 48; H7-V1: one state run twice, 391 of 400 frames under 1.0)`. The pair counts
   as one match (the left-out cell, the line's count, the cap). The line, word for word: "<a> and <b> look like the
   same match saved twice: save <b> again from another match." (`<b>` the later role; collected again under the same
   role it replaces the copy.)
2. **A save in the wrong role (winner):** named when **(a)** its held-out frames (second halves) are read by the full
   spec **as another ending** (not unknown), or **(b)** left out, it ends as another ending **while its ending kept at
   least two other matches** in that learn. With fewer, a read as another ending is the thin ending of the table above:
   that ending is asked one more save instead. The line, word for word: "A save may be in the wrong role: <role> reads
   as <the other ending>. Check which player won that match; collect it again under the right role." **No further save
   is asked for until it is cleared.**
3. **One line, in this order:** wrong role, then the same match twice, then one more save, then the cap. Recorded as
   today (`recorded`), with the line itself (`recorded.line`) so rehearse carries it ("then rehearse <code> --collect …"
   for one more save).

## Tests (`tests/b175_left_out/`, made-up titles; temp dirs removed)

Each row of the table through `learn` (register's two per ending; one per ending through rehearse): the weak pass → the
left-out cells not met and the line; two per ending other characters → the line asks a third; near-alike two → asks
`_3`, and with three → PASS; far apart on two → PASS; same characters within an ending → the same-match cell and its
line; a mislabel with two per ending → asks a save (no accusation), with three → the wrong-role line and no ask; the
spec written equals the one from every save; rehearse carries the cell; **a made-up title where only the margin cell
fails** (endings that differ in their tally only beside a large start-only mark) → FAIL. **Mutations, caught by B175's
own suite:** the cell always met; the left-out save still among the sources; the margin cell alone always met; plus the
same-match measure off; the wrong-role rule's two-other-matches guard off; the wrong-role line not stopping the ask.
B157's, B162's, B163's, B167's, B169's, B171's suites green (their made-up titles given the saves this asks — disclosed).
