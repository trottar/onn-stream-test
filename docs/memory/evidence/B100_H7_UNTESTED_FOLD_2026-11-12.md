---
memory_schema: 1
as_of: 2026-11-12
status: BUILT (session B, queue AL) — tools/h7_rule_search.py: a fold whose training search was "not testable" (over a cap) is reported as not tested, and a template with any such fold reads at most "weak", the words saying why; a fold skipped for want of another example of its winner is as before. H7-P3's shape on made-up memory: (b2) with 1 fold run and 3 not tested → "weak" (B97's search: "strong"); the hinted pair's answer unchanged. Tools and tests only; the companion unchanged. Nothing committed. No title, serial, code name, character name, cheat name or path in this record
---

# B100 — a fold that could not be tested does not count as passed (2026-11-12)

**Why:** H7-P3's (b2) read "strong" with 1 of 4 folds run — the other three training searches were over (b2)'s
200,000-candidate cap, skipped as "not testable", and passed vacuously (B's note after queue AK). **Baseline:** HEAD
`33d8d2cf`. **Design** hashed before code at 01:02:11Z; **addendum 1** (where the mark is set) at 01:10:30Z, before
its fix (`b100_2026-11-12/design.sha256`).

## Built — `tools/h7_rule_search.py`

- A fold skipped as "the template is not testable on the other states", **in a template testable on all the states**,
  gets `not_tested: true`; the template's evidence carries `folds_not_tested` (only when there is one) and **cannot be
  "strong"** — at most "weak": "weak: N families pass the K folds that ran, but M folds could not be tested (the search
  on the other states was over its cap) — a fold not tested is not a fold passed"; `would_make_strong`: "every fold
  tested — the search on the other states stayed over its cap; more states of the same kind do not lift it".
- A template untestable as a whole (e.g. h without hints) is "none" as before; its folds unmarked, as B97's
  (addendum 1: the first run marked them and B98's byte-for-byte checks caught it).
- A fold skipped for want of another example of its winner: unchanged.

## Tests

| test | result |
| --- | --- |
| H7-P3's shape (B98's made-up memory + 2 KiB of fixed pseudo-random bytes); (b2)'s least cap measured by bisection: five states 36, the four-state training sets 89 / 106 / 94 / 97 | **the cap at 89** (H7-P3's case: 1 fold runs, 3 not tested): (b2) **"weak"**, `folds_not_tested` 3, `folds_run` 1, the words and `would_make_strong` as above; the cap out of reach: (b2) "strong" |
| the hinted pair's answer | **h** in both (capped: (b2) is not an answer at all; uncapped: (b2) strong and not accepted, B98) |
| `--accept-loose` against B97's commit **where the change touches** (the capped shape) | **the stated difference:** B97 reads (b2) "strong", B100 "weak"; templates a, b, c and h byte-for-byte equal; the answer's keys equal |
| `--accept-loose` against B97's commit where it does not | B98's byte-for-byte cases (B97's made-up memories, B98's, the PS1 emulator fixtures) **unchanged and equal** |
| the no-other-example case | unchanged (no `folds_not_tested`; "no other example of that winner") |
| B96-B98's tests | green |

**3 runs, 52 / 52 each, none skipped** (`tests_x3.txt`: B96-B98's 46 and B100's 6); `tests/h7_minigame_proof` 13 / 13. Mutations **4 / 4 caught** (`tests_mutations.txt`: a not-tested fold counted as passed, not marked, its count not reported, the words not saying why).

## Disclosed

- The first full run failed B98's two byte-for-byte checks: the mark had been set on the folds of a template untestable
  as a whole (h without hints); addendum 1 moved it (hashed before the fix).
- RetroArch headless on synthetic fixtures only (B61's form) in the suite; counted: **0 at the end** (`ps`, 02:03Z, after every batch). Intermediate counts of 2 were one headless session of the other item's batch running beside it from its own work copy (noted in `b101_2026-11-12/tests_x3.txt`, `tests_mutations.txt`, `tests_mutations_first.txt`).

## Files

`b100_2026-11-12/`: start files, the design + addendum + hashes, `b100.diff` (applies on `33d8d2cf`), `tests_x3.txt`,
`tests_mutations.txt`, `scripts/`, `sha256_before_after.txt`, redact / title / cheat-name checks, `manifest.sha256`.
Patch note: `patches/B100_H7_UNTESTED_FOLD.md`.
