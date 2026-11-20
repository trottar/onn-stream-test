# B175 + B176 — addendum after the code (written after the design was hashed; disclosed)

1. **The wrong-role rule, as built — the design's guard was not enough.** The design named a save in the wrong role
   when, left out, it ended as another ending while its ending kept two other matches. On the made-up title with the
   right roles (P1 looks 1, 2, 5; P2 looks 3, 4, 6), `end_P2` left out still ended as `end_P1` with two other P2
   matches: that rule would have accused a right save. And on the made-up mislabel (end_P2_2 holding a P1 win), the
   wrong save, left out, never ended (read unknown) at every step — never "as another ending".
   What tells them apart: **a mislabel spoils the spec learnt from every save** (the other ending's mark inside this
   ending's frames is not steady, so the learner cannot use it); a thin ending does not.
   **The rule as built:** a save is named in the wrong role when **(a)** the full spec reads its held-out frames as
   another ending, or **(b)** all four hold:
   - the spec learnt from every save does not meet learn's own cells (separable, margin, held-out unknown);
   - the save's left-out cell is not met;
   - its ending kept at least two other matches;
   - **relabelling only that save as the other ending makes the spec from every save meet learn's bars** (separable,
     margin, unknown, nothing read as another class).
   One extra learn per suspect, only when the full spec already fails.
   Result on the made-up titles:
   - **The right roles:** asked `end_P1_3`, `end_P2_3`, `end_P2_4`, then PASS; never accused.
   - **The mislabel:** asked the same three, then "A save may be in the wrong role: end_P2_2 reads as end_P1", with
     nothing asked.
2. **The near-alike title whose first P2 match had P1's characters** (P1 looks 1, 2; P2 looks 1, 3 — B171's PASS):
   asked `end_P1_3`, `end_P2_3`, `end_P2_4`, then **the cap**. `end_P2` (look 1), left out, is never read as its own:
   P1 still has a look-1 save, so the spec ties those characters to P1 — what the cell is for. It means the new cell can
   be hard to meet. **Three saves per ending is the least for a near-alike title, not a promise that three suffice.**
   The record's table says which made-up titles met it on three.
3. **Places:** each results save left out in turn; a row left with no save is dropped as a class (the learner refuses a
   class with no frames).
