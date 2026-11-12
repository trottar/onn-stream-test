# B100 — a fold that could not be tested does not count as passed (design, before code; queue AL, 2026-11-12)

Baseline: HEAD `33d8d2cf` (H7-L1 committed). Changes `tools/h7_rule_search.py` and `tests/h7_rule_search/` only.

## Why

H7-P3: (b2) read "strong" with 1 of 4 folds run — the other three training searches were over (b2)'s 200,000-candidate
cap, so those folds were skipped as "the template is not testable on the other states" and a family passed them
vacuously. B's note (queue AK): such a fold is not a fold passed.

## The change

- `_fold`: a fold whose training search is not testable keeps `skipped: true` and its words, and gains
  **`not_tested: true`**.
- `_report`: `folds_not_tested` = those folds (the key present only when there is at least one). **A template with any
  not-tested fold cannot read "strong": at most "weak"** — words: "weak: N families pass the K folds that ran, but M
  fold(s) could not be tested (the search on the other states was over its cap) — a fold not tested is not a fold
  passed"; `would_make_strong`: "every fold tested — the search on the other states stayed over its cap; more states of
  the same kind do not lift it" (with a winner seen once, `_more`'s text first). A template with no passing family stays
  "none".
- A fold skipped because its winner has no other example: unchanged (skipped, counted, the same words).
- B98's acceptance applies to what is then strong.

## Tests

- **H7-P3's shape on made-up memory** (B98's: a counter, a level that empties, a 0 / 1 field, a level whose loser stays
  above 0, a hinted pair; plus a block of fixed pseudo-random bytes so (b2)'s searches on four states find more than on
  five): with (b2)'s cap set between its five-state count and its four-state counts (measured in the test), **(b2) has
  folds not tested → "weak"**, `folds_not_tested` ≥ 1, the words say why; with the cap out of reach (b2) is "strong";
  **the answer h unchanged**.
- The no-other-example case unchanged (B96's tests).
- **`--accept-loose` against B97's commit:** B98's byte-for-byte cases kept — none has a not-tested fold, so the output
  is unchanged there (asserted, as before); **where the change touches** (a not-tested fold) the difference is stated
  and asserted: B97's output reads (b2) "strong", this one "weak" with `folds_not_tested`, every other key equal.
- B96-B98's tests green.
