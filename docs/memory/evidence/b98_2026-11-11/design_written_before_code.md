# B98 — the acceptance rule in the search itself (design, written before code; queue AK, 2026-11-11)

Baseline: HEAD `6cb4663b` (H7-P3 committed). Changes `tools/h7_rule_search.py` and `tests/h7_rule_search/` only; the
companion unchanged.

## Why

H7-P2 / H7-P3 applied B's note by hand: a "strong" answer whose template is the loosest ((b2), not hinted) or a single
field ((c)) must not become the rule. The search should say so itself.

## The rule (in `_verdict`)

The strong templates are ordered as today (a hinted top family first, then a, b, c, b2, h). Each strong template's top
passing family is an **answer**, reported with `template`, `level` ("strong"), `hinted`, `passing_count`, `rule`,
`accepted` and, when not accepted, `why_not` in words. **Accepted** when its template is **a** or **b**, or its family
is **hinted**, or it is a **hinted set (h)**. Not accepted:
- (b2), not hinted — "(b2), a level whose loser may be above 0, is the loosest template: strong evidence alone does not
  decide it unless the game's cheat list points at the family";
- (c) — "(c), a single field, fits memory that merely follows the outcome; it never decides on its own".
**`decided` = the first accepted answer exists**; it is the rule (`rule`, `template`); `also_fits` = the other
accepted answers; `not_accepted` = the strong answers not accepted, with their level and words; top-level `accepted`:
true / false. With no accepted answer: `decided` false, `accepted` false, `not_decided` as today plus `not_accepted` and
`why` ("strong only in templates that do not decide on their own: …").

**Ranking honesty:** with a decided answer, `ranking_pick` = its template has more than one family passing every fold,
and `ranking_pick_count` = that count ("strong by order, not a unique fit"); `ranking_pick` false with count 1.

**`--accept-loose`** (module `ACCEPT_LOOSE`; tests and study only): today's `_verdict` exactly — no new key — so the
output is B97's byte for byte.

## Tests (`tests/h7_rule_search/`, no emulator unless stated)

- **H7-P3's shape on made-up memory** (five states; a counter pair (a), a level that empties (b), a single field 0 / 1
  (c), a level whose loser stays above 0 (b2), a hinted pair no template finds (h), with hints): a, b, c, b2, h all
  strong → the answer **h**, `accepted` true, `ranking_pick` false; a and b in `also_fits`; c and b2 in `not_accepted`
  with words.
- **No hints, only (b2) strong** → `decided` false, `accepted` false, the reason in words; **(c) alone strong** → not
  accepted.
- **`--accept-loose` byte for byte:** the search of B97's commit (`a5383e3b`, read with `git show`, skipped without git)
  against this one with `ACCEPT_LOOSE` on: the made-up memories of B97's tests (3 and 5 states, with and without hints)
  and the PS1 emulator fixtures (B61's form; 3 and 5 states, with and without the made-up list) — `json.dumps` equal.
  The CLI flag exists and sets it.
- A ranking pick: the PS1 fixture at five states without hints (template a, several passing families? — the count is
  whatever the fixture gives; asserted `ranking_pick == (count > 1)`).
- B96 / B97's tests unchanged and green.
