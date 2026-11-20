# B171 + B172 — addendum after the code (written after the design was hashed; disclosed)

1. **bench reads each save by its class.** Missed by the design: bench runs every kept ending through the hub (a held
   start, the go, the save loaded) and named its class and expected scores by the role; `end_P1_2` would have been
   expected as a class of its own and its scores read from `"1_2"`. Now `_role_class` there too: **every save of an
   ending is benched as that ending** (one held cycle per save, unattended; a two-player title with two saves per
   ending runs four endings, not two). Found when B157's made-up title was given its second saves.
2. **Suites of earlier items updated for the new rules (their bars and cells unchanged):** B157's made-up titles T90 /
   T91 collect `end_P1_2` / `end_P2_2` (register's minimum), its missing-state test reads the three roles missing
   after round 1; B163's kept extra `end_p1_b` (it shows end_P1's screen) is now a source (`end_P1_2`), its page
   "Endings read, not a role: none", "below two saves per ending" `end_P2_2`; B162's and B169's close-twice tests take
   a new before between the two closes (B172: close ends it).
3. **What the tests showed of the learner on the made-up near-alike title (no bar touched):** from two saves per ending
   of one look, learn named `end_P1_3`, then `end_P2_3`; each collected from another look → PASS. T88's shape (one save
   per ending, rehearse): `end_P1_2`, then `end_P2_2` → PASS. **A made-up spec learnt from three looks per ending read
   every look tried from 2 to 6 but not look 7** — a spec that passes every bar can still miss a match whose characters
   it never saw. Learn's held-out split halves each save, so its bars never test a match the spec did not learn from.
   Not changed (the queue: no bar changed, the learner's rule not changed); in the reply's "what I would change".
4. **The real run** (`rehearse T88 --collect other=2`, once, 00:54-00:57Z): as the design predicted — `runs.md`.
