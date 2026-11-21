# B185-B187 — addendum, written after the code (queue BI); what differs from the hashed design

1. **The label stage reads by the direct read too.** The hashed design gave the direct read (finals and columns at
   their places on the save's first labelled picture, when the reader learnt without the save cannot end) to learn's
   left-out cell only. On a T90-shaped made-up title, the reader learnt without the overtime save could not end on
   its finals, so label fell back to B181's "not read" and never judged its cells or columns. The label stage's
   read-back now reads the same way. Stricter: a save whose final holds a digit only it shows has every other number
   judged (B178's test of a 16 read for 15 is now named at the first label instead of after one more save; its
   expectation changed, disclosed).
2. **`_culprit` (one misread spoiling the others' readers)** takes a final read in part (`?5`) and allows each other
   save's digits only it shows, as the read-back does (`_mend`).
3. **A blank cell in a column with no place reads `_`, not `*`** (only a filled one is "shown only here").
4. **learn's line (B188)** ends "<n> digit(s) still short (<digits>); if one is still short after that match, learn
   asks for one more" — the session's words to the user come from it.
5. **The ask's folder** can be moved by `PRIVYHUB_ADD_GAME_ASK` (the tests' temp dirs); default this repo's
   `logs/add_game_ask/`.
6. **A `sum` ask names every cell of that side and its final** (blank cells included: the user says they are blank).
