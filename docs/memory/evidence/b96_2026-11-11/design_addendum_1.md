# B96 — design addendum 1 (before its code; 2026-11-11)

Found while smoke-testing the pure search: with **one winner only** (e.g. begin + two ends both won by P1) "every winner
seen has two 'end' states" holds, and a field where P1 is larger in every state (B94's decoy) would pass every fold —
"strong" on a rule that cannot tell players apart. **"strong" also needs ends won by at least two different players.**
`would_make_strong` then names an end won by a player not yet seen ("an 'end' won by P2"), before the repeats.
The cross pair seen in the smoke test (P1's field from the planted block, P2's from its copy, stride +0x100) is a
second family by the stated links (a different stride); it ranks below the planted one (larger stride). Left as is,
reported in the record.
