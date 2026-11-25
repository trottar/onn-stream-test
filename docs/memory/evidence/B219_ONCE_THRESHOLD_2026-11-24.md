---
memory_schema: 1
as_of: 2026-11-24
status: NOT BUILT by the queue's own condition (queue BR, B219) — the valid test variants read "?" failed on the margin (five of six), not on the threshold alone, so nothing was changed; B220 ran on the code as committed. T92 (its real folder as it stands, scratch): plan and train "Still needed: a final score with a 6 in it (either player)."; T90: "… 6 … 7 … 8 …". Nothing in BARS changed; T88-T91's rules sha256 before = after. Nothing adopted; nothing committed
---

# B219 / B220 — a once-seen symbol's threshold (queue BR)

Queue: `handoffs/QUEUE_2026-11-24BR.md`. Read line 2026-11-25T00:26:17Z; limit 01:11:17Z. The directory
`b219_2026-11-24/`:
- the decision, written and hashed before any code (`design_written_before_code.md`, `design.sha256`, 00:29Z): none
  followed;
- the read-only diagnostics (`scripts/`) and their outputs (`br_why_*.json`, `br_seeds_*.json`, `br_parts_T92.json`);
- `b220/` — T92's and T90's plan and train pages (scratch; no name in them);
- the checks, `manifest.sha256`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (queue BQ and
session A's T92 page committed, `4af23eb4`). T88-T91's rules: 23 files hashed.

## B219 item 1 — why each valid test variant was not read (nothing changed)

Scratch copies: T92's real folder as it stands (eight saves, its survey and labels, read only) and T90 with BQ's
answers. Today's `score_gates`, every valid test variant of the once-seen symbol read by the reader's own rule, taken
apart:

| title | symbol | variant | nearest template | its distance | that template's threshold | distance to the symbol's own | margin | margin_needed | failed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T92 | 6 | 3 | 5 | 0.8572 | 0.5223 | 0.9129 (6's threshold 0.4575) | 0.0097 | 0.1968 | threshold + margin |
| T92 | 6 | 6 | 5 | 0.8462 | 0.5223 | 0.9026 | 0.0285 | 0.1968 | threshold + margin |
| T90 | 8 | 1 | 8 | 0.5292 | 0.5432 | 0.5292 | 0.2190 | 0.2345 | **margin** |
| T90 | 8 | 4 | 8 | 0.5423 | 0.5432 | 0.5423 | 0.2033 | 0.2345 | **margin** |
| T90 | 8 | 7 | 8 | 0.5392 | 0.5432 | 0.5392 | 0.2116 | 0.2345 | **margin** |
| T90 | 8 | 8 | 8 | 0.5601 | 0.5432 | 0.5601 | 0.1961 | 0.2345 | threshold + margin |

Separable failed for none. The six read right (T92) and four read right (T90) sit at 0.13-0.34 from their own template
with margins 0.32-0.52.

**Item 2's condition — "if any failed on the margin or on separable, change nothing, report and go to B220" — holds
(five of six failed on the margin). Nothing was built:** no calibration stream, no widened threshold, no new tests,
no mutations.

**What T92's two "?" 6s are** (`br_parts_T92.json`, read only): both passed B214's share (86.6 % and 86.4 % of the
cut's ink pasted, the floor 85 %), but each cut is 62 px wide around a 35 px glyph. The pasted 6 joined leftover ink
on its background into one cut, so `glyph_cell` squeezes it, and the result is far from every template. The other six
cuts are the glyph's own width (35-40 px). **The share bounds foreign ink as a share of the cut, not the cut's size:**
on a 58 px tall glyph, 14 % foreign ink nearly doubles the width. On T90's 8 the misses are genuine. Those variants
are the glyph, read as 8, but at a margin a little under the title's `margin_needed` (half the least margin among
the real glyphs).

## B219 item 3 — the seed (reported, never a gate; today's code, "before" only — there is no "after")

| title | symbol | the title's seed | +1 | +2 | +3 | +4 |
| --- | --- | --- | --- | --- | --- | --- |
| T92 | 1 | counted | counted | counted | counted | counted |
| T92 | 4 | counted | counted | counted | counted | counted |
| T92 | 6 | not (6 of 8) | not (6 of 8) | not (5 of 8) | not (6 of 8) | not (6 of 8) |
| T90 | 3 | counted | counted | counted | counted | counted |
| T90 | 4 | counted | counted | counted | counted | counted |
| T90 | 8 | not (4 of 8) | not (6 of 8) | **counted** | not (6 of 8) | **counted** |
| T90 | 9 | counted | not (6 of 8) | not (6 of 8) | not (5 of 8) | counted |

T90's 8 and 9 turn on the seed; T92's 6 does not (refused under all five). **T92's 6 was counted in BQ and is
refused now for more than the seed:** the sixth save (03-01) added real 1s and 3s, and the title's `margin_needed`
(half the least margin among its real glyphs) went from 0.1039 (BQ, five saves) to 0.1968. A save that teaches one
digit tightened the margin every once-seen digit must clear.

## B220 — T92 and T90, plan then train, once each (scratch; nothing changed after)

T92's real folder copied as it stands (nothing answered again); T90 as BQ's scratch left it (BQ's answers).

| | T92 | T90 |
| --- | --- | --- |
| plan | PASS; 0 2 3 5 twice+; 1 4 seen once (counted); 6 once, not counted | PASS; 0 1 2 5 twice+; 3 4 9 seen once; 8 not counted; 6 7 never |
| **plan's last line** | "Still needed: a final score with a 6 in it (either player)." | "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one)." |
| train | FAIL (23); last line = plan's | FAIL (22); last line = plan's |
| endings read right | 5 of 6 (end_P2_3 05-06 not: the 6) | 4 of 5 (end_P1_2 35-28 not: the 8) |

Every cell: `b220/T92/train.md`, `b220/T90/train.md`.

## Tests

No code changed, so there are no new tests and no mutations. `b208_survey`, `b214_variants`, `b210_keep_result` once
on the committed code: b208 9 OK, b214 10 OK, b210 9 OK (`tests_runs.txt`). `git diff --stat` on code (`tools/`, `companion/`, `tests/`): empty —
the old path's suites not run (`logs/b219_git_status.txt` carries the stat).

## Checks

`redact_check.txt`, `title_check.txt`, `id_check.txt`, `code_check.txt` (BQ's, unchanged) over every file this
queue wrote: FAILS 0 each; the screens' team names (the check kept off the repo): FAILS 0. T88-T91's rules folder: 23
files, sha256 before = after. T92's real folder only read (copied).
