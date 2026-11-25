---
memory_schema: 1
as_of: 2026-11-25
status: BUILT (queue BS — B221 a valid test variant is the glyph's own size: its cut box within 2 px of the pasted glyph's width and height, besides B214's two conditions; test variants only). B222 once each in scratch: T92 (its real folder as it stands) plan "Nothing more is needed.", train PASS (23 cells); T90 plan / train "Still needed: 6, 7, 8" (its 8: margin misses, not this queue). Nothing in BARS changed; the once rule's gate unchanged; T88-T91's rules sha256 before = after. Nothing adopted; nothing committed
---

# B221 / B222 — a valid test variant is the glyph's own size (queue BS)

Queue: `handoffs/QUEUE_2026-11-25BS.md`. Read line 2026-11-25T00:47:57Z; limit 01:17:57Z. The directory
`b221_2026-11-25/`:
- the design and `design.sha256` (hashed 00:48:11Z, before any code);
- `b222/` — T92's and T90's plan and train pages (scratch; no name in them);
- the templates table's outputs (`bs_templates_*.json`) and its script;
- the runs, the mutation, the checks;
- `b221.diff` (applies on `2d8a8345`), `apply_check.txt`, `manifest.sha256`.

Patch: `patches/B221_VARIANT_SIZE.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (queue BR committed,
`2d8a8345`). T88-T91's rules: 23 files hashed.

## B221 (BUILT)

- **The rule:** `test_variants` keeps a test variant only when all three hold:
  1. it is cut as one glyph;
  2. at least `SYN_OWN` of its ink is pasted ink;
  3. **its cut box's width and height are each within `VARIANT_SIZE_TOL` = 2 px of the pasted glyph's.**
- Otherwise it is thrown away and the next drawn: up to 24 draws, 8 valid needed, as B214.
- **Test variants only.** The templates, the once rule's gate, `BARS`, plan / train / register: unchanged.

**The templates' synthetic glyphs that would fail the same size rule** (reported, nothing changed — re-made exactly as
`score_gates` makes them):

| title | symbol | real glyphs | synthetic cut | own size | **would fail** | e.g. (cut for glyph, h x w px) |
| --- | --- | --- | --- | --- | --- | --- |
| T92 | 0 | 14 | 112 | 79 | **33** | 58x57 for 58x34 |
| T92 | 1 | 1 | 8 | 7 | **1** | 58x52 for 58x22 |
| T92 | 2 | 3 | 24 | 15 | **9** | 58x60 for 58x35 |
| T92 | 3 | 2 | 16 | 11 | **5** | 58x61 for 58x33 |
| T92 | 4 | 1 | 8 | 7 | **1** | 58x60 for 58x36 |
| T92 | 5 | 2 | 16 | 11 | **5** | 58x61 for 58x33 |
| T92 | 6 | 1 | 8 | 4 | **4** | 58x62 for 58x35 |
| T90 | 0 1 2 3 4 5 8 9 | 17 | 136 | 136 | **0** | — |

- **On T92, 58 of the 192 template glyphs are joined cuts.** Most are about 60 px wide for a 33-36 px glyph: the big
  finals' region holds two digits, and an erased background keeps enough of the other digit to join.
- **T90:** none.

## B222 — T92 and T90, plan then train, once each (scratch; nothing changed after)

T92's real folder copied as it stands (nothing answered again); T90 with BQ's answers.

| | T92 | T90 |
| --- | --- | --- |
| plan's list | 0 2 3 5 twice+; **1 4 6 seen once (counted)** | 0 1 2 5 twice+; 3 4 9 seen once; 8 not counted; 6 7 never |
| **plan's last line** | **"Nothing more is needed."** | "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one)." |
| train | **PASS (23 cells)**, last line "Nothing more is needed." | FAIL (22 cells); last line = plan's |
| endings read right | 6 of 6 | 4 of 5 (end_P1_2 35-28: the 8) |

Each once-seen symbol's test variants:

| title | symbol | draws | valid | read as | verdict |
| --- | --- | --- | --- | --- | --- |
| T92 | 1 | 9 | 8 | 1 ×8 | seen once |
| T92 | 4 | 9 | 8 | 4 ×8 | seen once |
| T92 | 6 | 13 | 8 | 6 ×8 | seen once |
| T90 | 3 | 8 | 8 | 3 ×8 | seen once |
| T90 | 4 | 8 | 8 | 4 ×8 | seen once |
| T90 | 8 | 8 | 8 | 8 ×4, ? ×4 | not counted (margin misses, BR; not this queue) |
| T90 | 9 | 8 | 8 | 9 ×8 | seen once |

T92's train wrote its spec, begin and sidecar to the **scratch** rules folder only. The real rules folder is
unchanged; the real T92 has no train PASS — session A's run makes it.

## Tests

- **New, three runs:** `tests/b221_variant_size/` 5 tests OK ×3. My own first version of test 1 also bounded each
  valid variant's shape (distance < 0.3 to the clean glyph's cell). That number was arbitrary: a 1-px vertical shift
  alone gave 0.333, so it was dropped before the runs; the size property is asserted directly in test 2.
- **Mutation: the size condition removed — caught** (`tests_mutations.txt`).
- `b208_survey` 9 OK, `b214_variants` 10 OK, `b210_keep_result` 9 OK, once.
- `git diff --stat -- tools companion tests`: `tools/party_steps.py` only (plus the new test folder), so the old path's
  suites were not run (`logs/b221_git_status.txt`).

## Checks

`redact_check.txt`, `title_check.txt`, `id_check.txt`, `code_check.txt` (BR's, unchanged) over every file this queue
wrote: FAILS 0 each. The screens' team names (the check kept off the repo): FAILS 0. T88-T91's rules folder: 23 files,
sha256 before = after. `b221.diff` applies on `2d8a8345`.
