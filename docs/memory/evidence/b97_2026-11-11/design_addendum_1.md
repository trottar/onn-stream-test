# B97 — design addendum 1 ((b2)'s speed; 2026-11-11)

Found by the pre-test of B97's draft in a temp copy (the tree still at B96): (b2) — the loosest template — took **133 s**
on B96's random 2 MiB × 5 states timing (the stride loop reads every seed at every stride; random memory leaves ~20 % of
addresses as seeds). Disclosed: the change below was drafted in that temp copy right after the measurement, and this
addendum written and hashed before it entered the tree.
- **A necessary condition added to (b2)'s per-player masks:** at an "end" a player lost, its level is strictly below
  its "begin" value (the loser's below the winner's, which is at most its begin). It follows from (b2)'s statement, so
  the candidates are the same.
- **(b2) pairs P1 / P2 by equal "begin" values** (sorted by value, then address; strides width … 0x400), then checks
  every condition as the loop does; `B2_PAIRS = False` keeps the loop. Tested: the same candidates as the loop on random
  and structured memories, 2 and 4 players. Measured: 19.7 s on the random 2 MiB × 5 states (folds included).
- **Seen on that random memory, stated for the record:** (b2) leaves ~58,000 families passing every fold on random
  bytes with five states — "strong" by the stated rule. The answer's template order (a, b, c before b2) keeps it from
  answering when another template is strong; on its own it answers as the queue states (hinted or held-out passing).
