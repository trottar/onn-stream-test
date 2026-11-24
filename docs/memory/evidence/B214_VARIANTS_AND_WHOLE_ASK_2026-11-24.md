---
memory_schema: 1
as_of: 2026-11-24
status: BUILT (queue BQ — B214 the once rule's test variants, each the glyph that was pasted; B215 plan's last line the whole ask, from train's own gates; B216 register on three saves on the new path, the survey kept across a register; B217 B181 / B185 back on the pre-BP noise). B218 once each in scratch: T90 train FAIL (6 7 8 asked), T92 train FAIL (1 3 asked), plan = train in both. Nothing in BARS changed; T88-T91's rules sha256 before = after. Nothing adopted; nothing committed
---

# B214-B218 — the once rule's variants, plan's whole ask (queue BQ)

Queue: `handoffs/QUEUE_2026-11-24BQ.md`. Read line 2026-11-24T20:11:56Z; limit 21:26:56Z. The directory
`b214_2026-11-24/`:
- the design and `design.sha256` (hashed 20:13:00Z, before any code);
- `b218/` — the tool's pages for T90 and T92 (scratch; no name in them);
- the runs, the mutations, the checks, `scripts/`;
- `b214.diff` (applies on `689207fc`), `apply_check.txt`, `manifest.sha256`.

Patch: `patches/B214_VARIANTS_AND_WHOLE_ASK.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (queue BP committed,
`689207fc`). T88-T91's rules: 23 files hashed.

## B214 — the once rule's variants (BUILT)

- **Two streams from the readings' seed:** `[seed, 0]` makes the templates' synthetic glyphs; `[seed, 1]` makes the
  test variants. A test variant is never in the templates.
- **A test variant counts only when it is the glyph that was pasted:**
  - the cut finds exactly one glyph;
  - at least `SYN_OWN` (0.85, the same as `h7_endscreen.SYN_OWN`) of the cut's ink is pasted ink.
- An invalid one is thrown away and the next drawn from the same stream: up to 24 draws, stopping at 8 valid.
- **Fewer than 8 valid → not counted;** the cell says "variants could not be made (n valid of 8 needed)".
- The rule otherwise as it was: rigidity ≥ `rigid_min`, all 8 read as itself, no other symbol's real glyph read as it.
- The record now says what the variants read as.
- **Letters' variants** are the glyph's own cell at a shift: the pasted glyph by construction. They come from the test
  stream, 8 needed.

## B215 — plan's last line is the whole ask (BUILT)

- `score_gates` / `letters_gates` hold train's gates 1-3 and write nothing. plan and train both call them.
- plan's last line is `ask_line(kind, never seen ∪ seen once and not counted)`, one sentence. Its list marks each once
  symbol "counted: seen once" or "not counted: asked".
- **train's last line is the same line.**

## B216 — register on the new path (BUILT)

- **A score or letters title is on the new path** when:
  - its binding has a survey of that kind, or
  - the old learn never learnt it: no `learnt` in its binding, and no sidecar of the old learn's (one without `code`)
    in the rules folder.
- **New path: "kept states present" needs begin, other and one ending.**
- **Old path (T90 / T91; winner / places; `--rules-players`): the two-per-ending minimum.**
- **Register now keeps the binding's `survey`.** BP's register rebuilt the binding from its arguments, so a later
  `--collect` would have dropped it. Found while reading the code for this queue.

## B217 — the old path's two suites (BUILT)

- `tests/b181_every_digit/line_capture.py`, `test_b181.py` and `tests/b185_overtime/test_b185.py` are exactly their
  `ef8a0ce5` (pre-BP) text plus one first line: "Frozen with T90's old score path (queue BQ, B217): this suite's
  made-up noise is exactly the pre-BP fixture …".
- The per-picture noise stays in B178 / B198 / B200's captures and B178's harness, which B208 / B214 use.
- Both suites ran to their end (below).

## B218 — T90 and T92 once each (scratch; nothing changed after)

A fresh scratch copy of each: binding (no survey), kept saves and pictures, register's verdict. Survey with BP's
answers (T90 boxes 25 / 33, T92 boxes 10 / 12: the same regions as BP), BP's readings, `look=all`, plan, train.

| | T90 | T92 |
| --- | --- | --- |
| survey / label / plan | PASS / PASS (13) / PASS | PASS / PASS (13) / PASS |
| plan's list | 0 1 2 5 twice+; 3 4 9 seen once (counted); 8 once, not counted; 6 7 never | 0 2 5 twice+; 4 6 seen once (counted); 3 once, not counted; 1 never |
| **plan's last line** | "Still needed: a final score with a 6 in it and a final score with a 7 in it and a final score with a 8 in it (either player; one match may show more than one)." | "Still needed: a final score with a 1 in it and a final score with a 3 in it (either player; one match may show more than one)." |
| train | FAIL (22); last line = plan's | FAIL (21); last line = plan's |
| gate 2 | 3, 4, 9: 8 of 8 (8 draws each); **8: 4 of 8** | 4, 6: 8 of 8 (8 draws each); **3: 6 of 8** (10 draws, 2 thrown away) |
| endings read right | 4 of 5 (end_P1_2 35-28 not: the 8) | 4 of 5 (end_P2 02-03 not: the 3) |

**What the refused symbols' variants read as:**
- **T90's 8:** 8 valid variants (8 draws, none thrown away). 4 read as 8; 4 read as "?" (not read: outside 8's
  threshold or under the margin). Never as another digit.
- **T92's 3:** 8 valid variants (10 draws, 2 thrown away by the cut rule). 6 read as 3, 2 read as "?". Never as another
  digit.

So the variants are the glyph now, and the gaps that remain are the reader's. A digit learnt from one save has its
threshold from that save's own glyphs only, and some shifted copies of the same glyph fall just outside it.

Every train cell: `b218/T90/train.md`, `b218/T92/train.md`.

## Tests

- **New, three runs:** `tests/b214_variants/` 10 tests OK ×3 (`tests_new_runs.txt`). Three earlier runs were of the
  file before its share test (`Variants.test_4`) was added. That test's first assertion (no valid variant at all)
  was wrong: where the bar sits under the glyph's own stem, the variant really is the pasted glyph. It now asserts
  the property instead: 24 draws, fewer than eight valid.
- **Mutations, 5 of 5 caught** (`tests_mutations.txt`): a test variant in the templates; counted with fewer than
  eight; the SYN_OWN share not checked; plan's ask without train's gate 2; register's three saves for a title the old
  learn wrote.
- **The every-time suites, once, all at once, each to its end, plus the new path's B208 / B210:** B157, B171, B175,
  B178, **B181 (7 OK)**, **B185 (9 OK, 29.7 min)**, B198, B200, B204 and B210 OK. **B208: 2 failures** — two of BP's
  own assertions, written for what this queue changes on purpose (the once rule with two variants; plan's rows
  "once"). Brought to B214 / B215 (eight variants; "once (counted: seen once)"), then 9 OK (`tests_runs.txt`).

## Checks

`redact_check.txt`, `title_check.txt`, `id_check.txt` (B205's), `code_check.txt` (BP's, T90-T92's names from their
bindings, never printed) over every file this queue wrote: FAILS 0 each. The screens' team names (the check kept off
the repo): FAILS 0. T88-T91's rules folder: 23 files, sha256 before = after. `b214.diff` applies on `689207fc`.
