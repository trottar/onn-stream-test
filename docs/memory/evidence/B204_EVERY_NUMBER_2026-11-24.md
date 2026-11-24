---
memory_schema: 1
as_of: 2026-11-24
status: BUILT (B204 every number on a score title's final screen read — finals, period cells, stats table — and another size of the score's font counted when the title's own numbers say so; T92: the cells and the stats table are the finals' font, 0.652 against 0.830). B205 synthetic training for the score kind NOT BUILT (the 90-minute limit). B206 T92 from its six kept saves: register PASS, label PASS, learn FAIL — only 5 short (one save shows it, once at each size, and the two do not read each other). No bar lowered; nothing adopted; nothing committed
---

# B204-B207 — T92's digits from the saves it has (a 90-minute queue)

Queue: `handoffs/QUEUE_2026-11-24BN.md`; the read line 2026-11-24T00:39:51Z, the limit 02:09:51Z. The directory is
`b204_2026-11-24/`:
- the design + `.sha256` (hashed 00:41:37Z, before any code);
- the tests, the mutations, T90's and T91's re-run, the four checks, `scripts/`;
- `b204.diff` (applies on `2b4afeab`), `apply_check.txt`, the template's sha256, `manifest.sha256`.

Patch: `patches/B204_EVERY_NUMBER.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty; queue BM committed
(`2b4afeab`).

## B204 — settled with numbers (T92's kept pictures, read only; no picture source run)

Each end save's first picture. Every glyph of the finals (F, 57 px), the 1ST period cells (C, 15 px) and the six stats
rows SHOOT..PK (S, 15-17 px), labelled by my reading as drawn. Each glyph scaled to one height (`glyph_cell`), then
B186's measure (`cell_dists`).

| pair | min | max |
| --- | --- | --- |
| one digit, one size (F / C / S) | 0.003 | 0.492 |
| one digit, C and S | 0.040 | 0.500 |
| **one digit, a small one (C or S) and F** | 0.415 | **0.652** |
| two digits, one size | 0.830 | 0.986 |
| **two digits, any two sizes** | **0.834** | 0.993 |

**The cells and the stats table are one small font, and it is the score's font.** Scaled to the finals' height, every
same-digit pair across the sizes (≤ 0.652) is nearer than every two-digit pair (≥ 0.830), a gap of 0.178. They are not
the same pixels: 0.652 is above the finals' own 0.309. The learner's own decision, over every labelled picture (12
glyphs a digit and size): **0.6745 against 0.8296 → counted** (`score.sizes`).

## B204 — built

- **The reading names every number.** A side is `[<period cells>=]<final>[:<stat>.<stat>…]`, e.g. T92's end_P1:
  `02+_+_+_+_=02:13.00.00.00.01.00-00+_+_+_+_=00:00.00.00.00.00.00`.
  - Only the final is the result.
  - The period cells add up to it (the sum check, over the period cells only).
  - Each stats row is one more column for the learner. It is found as B200 finds an off-line cell: a side's columns
    are chosen together, in drawn order, each nearest its own side's final.
  - A reading without `:` is today's text.
  - The label line names the stats rows; `ADD_GAME_TASK.md` §2 says so (the template unchanged, `aadccb04…`).
- **Another size is counted when the numbers say so.** When some off-line columns are another size, their glyphs join
  the finals' group only if every one-digit pair across the two sizes is nearer than every two-digit pair. Otherwise
  they keep their own group and teach nothing (B200). The decision and both numbers are in the spec.
- **What guards a misread stat (there is no sum):**
  - the two readings must be the same;
  - the read-back: every stat is a column the reader learnt without that save reads;
  - the last look: every stat glyph is on `label/digits.png`; T92's sheet has 128 tiles (one picture of each save).

  A stat misread as a digit no other save shows is caught only by the last look, as a one-save period cell is today.
- **Found while building (disclosed):**
  - a side's columns may only be those nearest its own final (P1's all-00 stats rows had taken P2's);
  - the joint choice now weighs as many candidates as the side has columns (with six all-00 stats rows, four were
    too few), searched depth first.

## B205 — NOT BUILT

The 90-minute limit; B204 and B206 came first. Synthetic training would not have changed B206's verdict: the
every-digit cell counts only real glyphs, and B205 trains only.

## B206 — T92 from its six kept saves (no new match, no new save)

Before: `status` and `native-stream-status` showed nothing running (not active, recovery ENDED), and no RetroArch
process ran. **The picture source did not run** (the pictures were reused). The rules folder: sha256 before = after.

| stage (UTC) | verdict |
| --- | --- |
| register T92 … `--max-score 5`, no `--collect` (01:00:57) | **PASS** (9) |
| label, every number as drawn (01:00:58) | FAIL (19) — only the last look not given |
| label `look=all` (01:06:05) — every tile its row's digit: 0 ×113, 1 ×2, 2 ×6, 3 ×3, 4 ×2, 5 ×2 | **PASS** (19) |
| learn T92 (01:10:18) | **FAIL** (24) |

**My readings** (from `.1` and `.2`, the same both times). The stats are all 00 but end_P1's P1 SHOOT 13 and CK 01:
- end_P1 `02+_+_+_+_=02:13.00.00.00.01.00-00+_+_+_+_=00:00.00.00.00.00.00`;
- end_P1_2 `05…=05:00…-04…=04:00…`;
- end_P2 `02…=02:00…-03…=03:00…`;
- end_P2_2 `00…=00:00…-02…=02:00…`.

**learn, digit by digit (0-5):**

| digit | how it counts |
| --- | --- |
| 0 | every save |
| 2 | three saves |
| 3 | now in two saves: end_P2's final and cell, and end_P1's stats "13" |
| **1** | **learnt from one save**: end_P1's SHOOT 13 and CK 01, each glyph read back by the other |
| **4** | **learnt from one save**: end_P1_2's final 04 and cell 04, read back |
| **5** | **short** |

**Why 5 is short:**
- **Only end_P1_2 shows a 5,** in P1's final (05) and P1's 1ST cell (05), one at each size.
- Those two are the farthest one-digit pair across sizes (0.652), and neither reads the other back.
- No save shows a 5 anywhere else: in no other final, no other cell, and no stats row (every other stat is 00, 13
  or 01).

learn's line asks for one more match with a 5 on its final screen.

**Also not met:**
- **left out: end_P1_2:** its 5s.
- **left out: end_P2:** read right, 03, but ended only after 14.0 s (bar 2.0 s). The reader learnt without end_P2 has
  only the small 3 from end_P1's stats, and it reads the big 3 slowly. That is the cost of a cross-size sample; the
  bar caught it.

## Tests, mutations, the 90 minutes

- **B204's 6 fast tests** (`tests/b204_every_number/`: the reading, the sum, the size decision on made-up glyph
  cells): three runs OK.
- **Every earlier suite once, 12 at a time** (`tests_runs.txt`): all green except B200 `Drawn` and `Counted`. Those
  pinned BM's "a small size teaches nothing", which B204 changes on purpose for one font at two sizes. Both assertions
  were updated (disclosed); B200 rerun: once more red (`Counted`'s made-up title now PASSES learn, its cells' 2
  counting), that assertion set to the PASS, then OK (`b200_rerun.txt`). Some suites skipped one or two tests run in parallel
  (B162 2, B158, B103, B178 1 each — their own port / companion skips); earlier serial runs skipped fewer.
- **Mutations, 3 of 3 caught** (`tests_mutations.txt`):
  - the stats added into the sum;
  - another size never counted;
  - another size always counted.
- **T90 and T91 re-run on copies:** `regress.txt`.

## Checks

- `b204.diff` applies on a clean export of `2b4afeab`, every file byte for byte the tree (`apply_check.txt`).
- **No title, game id, setup id, serial, path or address** in any file this queue wrote: BF's three checks and BM's
  T92 check, run after every file was written.
- **No picture in git:** the sheet crops I read stayed in my scratch, off the repo.
- **Read only / untouched:** the rules folder (sha256 the same), the kept H7 folders, your slots, setups and in-game
  saves, the runtime pictures. The label stage writes its own `label/` pictures and `label.json` (the tool's own).
- **Nothing else run or touched:** no title started, no stream, no restart, no adb, no sudo, no nft. The app, the
  companion and the board's repo were not touched.
- **Hub calls:** read-only GETs — the library list (register) and `status` / `native-stream-status` (once).
- **Disclosed:** three copies of the work tree, one per mutation, remain in my scratch folder (not removed by hand).
  One scratch clean-up (`rm` of an old probe rules folder) was refused by the safety check; I used fresh scratch
  folders instead.
