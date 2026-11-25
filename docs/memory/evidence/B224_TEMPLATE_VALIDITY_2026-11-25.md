---
memory_schema: 1
as_of: 2026-11-25
status: BUILT (queue BU — B224 the score path's template stream keeps a synthetic glyph only when it is valid as a test variant is: one glyph cut, at least SYN_OWN of its cut ink pasted, its cut box within VARIANT_SIZE_TOL of the pasted glyph's size; the same code (`paste_cut`) as the test variants. B225 in scratch: T92 (its real folder as it stands) plan "Nothing more is needed.", train PASS (23 cells), 88 template draws thrown away and redrawn, 192 made, margin_needed 0.2548 (BS 0.1968); T90's plan and train cells equal BS's, cell for cell. Nothing in BARS changed; no gate changed; the rules folder's 27 files sha256 before = after. Nothing adopted; nothing committed
---

# B224 / B225 — the templates' synthetic glyphs are the glyph that was pasted (queue BU)

Queue: `handoffs/QUEUE_2026-11-25BU.md`. Read line 2026-11-25T07:24:11Z; limit 08:04:11Z. The directory
`b224_2026-11-25/`:
- the design and `design.sha256` (hashed 07:25:59Z, before any code);
- `b225/` — T92's and T90's plan and train pages (scratch; no name in them);
- the runs, the mutation, the checks;
- `b224.diff` (applies on `c7750afc`), `apply_check.txt`, `manifest.sha256`.

Patch: `patches/B224_TEMPLATE_VALIDITY.md`.

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty (queue BU committed, `c7750afc`);
- the rules folder hashed: 27 files (T88-T91's 23 and T92's 4).

## B224 (BUILT)

**The rule:** `synthetic_glyphs` (the template stream, stream 0) keeps a draw only when all three hold:
1. it is cut as one glyph;
2. at least `SYN_OWN` of its cut ink is pasted ink;
3. its cut box is within `VARIANT_SIZE_TOL` (2) px of the pasted glyph's width and height.

**How it works:**
- One draw is `paste_cut`, the code `test_variants` used, moved out and called by both. The test variants are unchanged:
  the same rng calls and cells, a test against the predecessor.
- A draw that is not valid is thrown away and the next one drawn from the same stream. It stops at `SYN_PER_GLYPH`
  (8) valid or `VARIANT_DRAWS` (24) draws. Fewer: those made.
- Train's page, `recorded.synthetic`:
  - "made" and "not cut" as before. With B224 no template cell is empty, so "not cut" is always 0.
  - new: "thrown away" (the total) and "by symbol" → made / thrown away / draws / why / glyphs short of 8.
- **Departure from the hashed design:** the design renamed "not cut" to "thrown away". `b214_variants`'
  `Ask.test_2` reads `made + not cut`, and failed with `KeyError: 'not cut'` (the first runs are set aside in
  scratch, `bu/runs_before_not_cut_fix`). The key was kept rather than editing an old test. Every run below is on the
  code after that change.

**Not changed:** the test variants' stream, the once rule, gate 1, the margins, `BARS`, every bar; the letters path;
`party_add_game.py`; `companion/`.

**A title with no draw thrown away is byte for byte the predecessor's.** It makes the same rng calls in the same
order and keeps the same cells. Tested against `c7750afc`'s `party_steps.py`, loaded from git, on a made-up glyph and
on a made-up score title's fit and refs. B225's T90 shows the same: every cell equal.

**Not caught by my design, found by the first B225 run:** the first version raised `KeyError: 'why'`. Python evaluates
the right side of `log.setdefault("why", {})[why] = log["why"].get(...)` first. It was fixed before any test or
recorded run. That run's scratch folders were set aside (`bu/*_first`), not deleted.

## B225 — T92 and T90, plan then train, once each (scratch; nothing changed after)

T92's real folder and its evidence were copied as they stand (nothing answered again). T90 is BS's scratch copy,
which holds BQ's answers. The rules folder was a new, empty scratch one.

**T92 — plan's last line, word for word:** `Nothing more is needed.` Plan's one cell: "every end save shows text in every region",
yes, met. Symbols: 0 2 3 5 twice or more; 1 4 6 once (counted: seen once).

**T92 — train: PASS (23 cells)**, last line `Nothing more is needed.` Every cell as it fell:

| cell | read | bar | met | BS |
| --- | --- | --- | --- | --- |
| gate 1: every glyph of a symbol two or more saves show, read right without its save | all | all | yes | same |
| **margin_needed** | **0.2548** | >= 0.0796 | yes | **0.1968** |
| every symbol two saves show separable | all | all | yes | same |
| gate 2: 1, one real picture | seen once | counted when … | yes | same |
| gate 2: 4, one real picture | seen once | counted when … | yes | same |
| gate 2: 6, one real picture | seen once | counted when … | yes | same |
| gate 3: every symbol the result can show learnt (none never seen) | all | all | yes | same |
| the screens: start and end thresholds | end 0.173, start 0.1648 | both set | yes | same |
| begin: never ended / recognised within | true / 0.0 | true / <= 8.0 s | yes | same |
| end_P1: ended as itself / within | 02-00 / 1.5 | 02-00 / <= 2.0 s | yes | same |
| end_P1_2: ended as itself / within | 05-04 / 1.5 | 05-04 / <= 2.0 s | yes | same |
| end_P1_3: ended as itself / within | 03-01 / 1.5 | 03-01 / <= 2.0 s | yes | same |
| end_P2: ended as itself / within | 02-03 / 2.0 | 02-03 / <= 2.0 s | yes | same |
| end_P2_2: ended as itself / within | 00-02 / 2.0 | 00-02 / <= 2.0 s | yes | same |
| end_P2_3: ended as itself / within | 05-06 / 2.0 | 05-06 / <= 2.0 s | yes | same |
| other: never ended | true | true | yes | same |

**The templates, by symbol (T92):**

| symbol | real glyphs | BS: made / would fail the size rule | BU: made | thrown away (all "not its own size") | draws |
| --- | --- | --- | --- | --- | --- |
| 0 | 14 | 112 / 33 | 112 | 55 | 167 |
| 1 | 1 | 8 / 1 | 8 | 0 | 8 |
| 2 | 3 | 24 / 9 | 24 | 8 | 32 |
| 3 | 2 | 16 / 5 | 16 | 6 | 22 |
| 4 | 1 | 8 / 1 | 8 | 0 | 8 |
| 5 | 2 | 16 / 5 | 16 | 9 | 25 |
| 6 | 1 | 8 / 4 | 8 | 10 | 18 |
| all | 24 | 192 / 58 | **192** | **88** | 280 |

- Every glyph got its 8; none was short. BS's column counts the cuts BS's stream made. BU's thrown-away count differs,
  because each redraw moves every later draw in the one stream.
- **margin_needed:** 0.2548 (BS 0.1968). Without the joined cuts, the digits' templates are farther apart.

**T92's once-seen symbols, beside BS's** (the test variants' stream untouched):

| symbol | rigid / bar | draws | valid | read as | other glyphs read as it | verdict | BS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.6414 / 0.0995 | 9 | 8 | 1 ×8 | 0 | seen once | the same row |
| 4 | 0.6414 / 0.0995 | 9 | 8 | 4 ×8 | 0 | seen once | the same row |
| 6 | 0.6414 / 0.0995 | 13 | 8 | 6 ×8 | 0 | seen once | the same row |

**T90:**
- Plan: "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it
  (either player; one match may show more than one)." Train FAIL (22 cells), the same last line.
- **Its plan's and train's cells equal BS's scratch run, cell for cell** (plan 1 = 1, train 22 = 22).
- None of its template draws was thrown away (0 of 136).

The scratch train wrote T92's spec, begin and sidecar to the **scratch** rules folder only. The real rules folder and
the real T92 folder are unchanged (sha256 before = after). Session A retrains the real T92 only if Cowork says so.

## Tests

- **New, `tests/b224_template_validity/`, 7 tests, three runs:** see `tests_runs.txt`.
  - `Stream`: a joined, wider cut is thrown away and redrawn, never a template (checked against a hand replay of the
    stream); every paste cut as two glyphs → 0 made in 24 draws, recorded, no error; none thrown away → byte for byte
    the predecessor's; the test variants the predecessor's.
  - `Score`: a made-up score title's fit and refs are the predecessor's, none thrown away; train's page records made /
    thrown away by symbol.
  - `Letters`: B191's made-up letters title through survey, label, plan and train, on the predecessor's and on mine →
    the spec's JSON and arrays byte for byte the same.
- **Mutation: the size condition removed from the template stream — caught** by `Stream.test_1` (`tests_mutations.txt`).
  The mutation's copy has no git, so the two predecessor tests error there; the catch is test_1's failure.
- `b208_survey`, `b214_variants`, `b221_variant_size` and `b223_bench_numbers`, once each: see `tests_runs.txt`.
- `git diff --stat`: `tools/party_steps.py` only (the new test folder is untracked). So the old path's suites were not
  run (`logs/b224_git_status.txt`).

## Checks

`redact_check.txt`, `title_check.txt`, `id_check.txt` and `code_check.txt` (BS's, unchanged) over every file this
queue wrote: see each file. The rules folder: 27 files, sha256 before = after. The real T92 folder: before = after.
`b224.diff` applies on `c7750afc`.
