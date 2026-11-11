# B97 — design addendum 2 ((b2)'s size on a real game; 2026-11-11, before its code)

Seen while B97's batch was starting (that batch stopped, nothing recorded from it): (b2) leaves ~420,000 candidates on a
random 2 MiB × 3 states and ~267,000 on a structured 128 KiB in B97's own equivalence check; every candidate is a Python
record, kept again per fold. On T88's real memory (where B94's (a) alone had 8,520) the count is unknown and could be
millions — enough to exhaust the hub's memory in A's unattended run, beside the companion. **A cap:** when (b2)'s pair
search passes **`B2_CAP` = 200,000** candidates, it stops and (b2) is reported **not testable** — "too many (b2)
candidates to rank: more than 200,000 — the template cannot decide here" — evidence "none", its folds skipped with the
same reason; every other template unchanged. Tested: with a small cap on made-up memory (b2) says so and (a) still
answers. The loop path (`B2_PAIRS = False`, tests only) has no cap.
