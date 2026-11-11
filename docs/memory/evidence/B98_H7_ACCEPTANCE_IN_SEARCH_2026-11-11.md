---
memory_schema: 1
as_of: 2026-11-11
status: BUILT (session B, queue AK) — tools/h7_rule_search.py: the acceptance rule H7-P2 / H7-P3 applied by hand is now the search's own — a "strong" answer decides only when its template is a or b, its family is hinted, or it is a hinted set (h); a (b2) or (c) answer is listed as not accepted, with its level and the reason in words; with a decided answer, ranking_pick says whether its template had more than one family passing every fold. --accept-loose (tests and study only) gives B97's output byte for byte. Tools and tests only; the companion unchanged. Nothing committed. No title, serial, code name, character name, cheat name or path in this record
---

# B98 — the acceptance rule in the search itself (2026-11-11)

**Why:** B's two notes after queue AJ — (b2) and (c) should never decide on their own, and "strong" with many passing
families is a pick by order, not a unique fit. H7-P2 and H7-P3 applied the first by hand (H7-P3: "strong AND template
h → accepted"). **Baseline:** HEAD `6cb4663b`. **Design** hashed before code at 20:44:50Z (`b98_2026-11-11/design.sha256`).

## Built — `_verdict` in `tools/h7_rule_search.py`

- Every strong template's top passing family is an **answer** (`template`, `level`, `hinted`, `passing_count`,
  `accepted`, `rule`, and `why_not` when not accepted). **Accepted:** template a or b, or a hinted family, or a hinted
  set (h). **Not accepted:** (b2) not hinted — "(b2), a level whose loser may be above 0, is the loosest template:
  strong evidence alone does not decide it unless the game's cheat list points at the family"; (c) — "(c), a single
  field, fits memory that merely follows the outcome; it never decides on its own".
- `decided` = an accepted answer exists; the first by the order (a hinted top family first, then a, b, c, b2, h) is
  `rule` / `template`; top-level `accepted`; `also_fits` the other accepted; `not_accepted` the rest. None accepted →
  `decided` false, `accepted` false, `not_decided.not_accepted` and `not_decided.why` in words.
- **`ranking_pick`** (with a decided answer): true when the answer's template has more than one family passing every
  fold, with `ranking_pick_count` and `ranking_pick_words` ("strong by order, not a unique fit: N families of template a
  pass every fold; the rule is the top one").
- **`--accept-loose`** (`ACCEPT_LOOSE`; tests and study only): B97's `_verdict` exactly, no new key.

## Tests

| test | result |
| --- | --- |
| H7-P3's shape (made-up memory, five states, hints): a counter, a level that empties, a 0 / 1 field, a level whose loser stays above 0, a hinted pair no template finds | a, b, c, b2, h all **strong** → the answer **h**, `accepted` true, `ranking_pick` false (count 1); a and b in `also_fits`; c and b2 in `not_accepted` with their level and words |
| no hints, only (b2) strong | `decided` false, `accepted` false, no rule; the reason names (b2) as the loosest |
| (c) alone strong | not accepted; the reason names the single field |
| a hinted (b2) family | accepted, the answer itself (b2, first by the order) |
| two counters both passing | `ranking_pick` true, the count, the words |
| `--accept-loose` | the (b2)-only memory decides as B97's did; no `accepted` key; the CLI flag exists |
| **`--accept-loose` byte for byte** | **B97's search, read from its commit `a5383e3b` with `git show`**, against this one with the flag: B97's made-up memories (3 and 5 states, with and without hints) and this item's four, and **the PS1 emulator fixtures** (3 and 5 states, with and without the made-up cheat list) — `json.dumps` equal in every case |
| the PS1 fixture's own five states | accepted (template a); `ranking_pick` = its count > 1 |
| B96 / B97's tests | unchanged, green |

**3 runs, 46 / 46 each, none skipped** (`tests_x3.txt`: B96 / B97's 37 and B98's 9; the byte-for-byte checks ran against B97's commit); B93 / B95's `tests/h7_minigame_proof` 13 / 13. Mutations **6 / 6 caught** (`tests_mutations.txt`: every strong answer accepted, a hinted (b2) not accepted, a unique fit called a pick, `--accept-loose` ignored, the not-accepted answers unreported, the answer not the first by the order).

## Disclosed

- **Seen in H7-P3's own table (not changed here):** (b2) read "strong" with 1 of 4 folds run — its training sets
  passed the 200,000-candidate cap, so those folds were skipped as "not testable" and could not count against it. B98
  makes that harmless (a non-hinted (b2) never decides); a fold skipped for that reason still lets a template read
  "strong". Noted for a later item.
- The byte-for-byte test reads B97's search from git (`H7_GIT_REPO`, set by the runners, points the work copies at the
  repo; skipped without git).
- The first B98 batch was stopped after it had started: its work copy was not a git repo, so the byte-for-byte test
  would have been skipped; the helper was pointed at the repo and the batch restarted (nothing recorded from the first).
- RetroArch headless on synthetic fixtures only (B61's form); counted: **0 at the end** (`ps`, 22:14Z, after every batch). Intermediate counts of 2 were one headless session (an AppImage's two processes) of the other item's batch running beside it from its own work copy (noted in `b99_2026-11-11/tests_x3.txt` and `tests_mutations.txt`).

## Files

`b98_2026-11-11/`: start files, the design + hash, `b98.diff` (applies on `6cb4663b`), `tests_x3.txt`,
`tests_mutations.txt`, `scripts/`, `sha256_before_after.txt`, redact / title / cheat-name checks, `manifest.sha256`.
Patch note: `patches/B98_H7_ACCEPTANCE_IN_SEARCH.md`.
