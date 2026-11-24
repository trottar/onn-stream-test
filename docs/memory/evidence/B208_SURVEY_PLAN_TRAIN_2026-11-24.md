---
memory_schema: 1
as_of: 2026-11-24
status: BUILT (queue BP — the front of the add-a-game path rebuilt once around the user's five steps; B208 survey, B209 label on the regions / plan / train with the once rule, B210 the hub keeps what it read, B211 T90 / T91 / T92 through it in scratch, B212 housekeeping, B213 the commands). The bar rigid_min 0.0995 set from T90 0.5693 and T91 0.1990 before T92 was looked at. T91 PASS on the new path; T90 and T92 FAIL at train (digits still needed); T92's plan: "Still needed: a final score with a 1 in it (either player)." T88-T91's rules sha256 before = after. Nothing adopted; nothing committed
---

# B208-B213 — survey, plan, train (queue BP)

Queue: `handoffs/QUEUE_2026-11-24BP.md`, after `handoffs/AUDIT_ADD_GAME_2026-11-24.md`. Read line 2026-11-24T19:16:04Z;
limit 22:16:04Z. The directory `b208_2026-11-24/`:
- the design and `design.sha256` (hashed 19:20Z, before any code);
- `b211/` — the tool's own pages for T90, T91 and T92 on the new path (scratch; no name in them);
- the tests' runs, the mutations, the checks, `scripts/`;
- `b208.diff` (applies on `ef8a0ce5`), `apply_check.txt`, `manifest.sha256`.

Patch: `patches/B208_SURVEY_PLAN_TRAIN.md`.

**Checked first:** only `privyhub-companion` and `privyhub-diag` active; `git status --short` empty (the audit and T92's
second record committed, `86120a3b` / `ef8a0ce5`).

## The path

`register` (unchanged) → **`survey`** → **`label`** on the regions → **`plan`** → **`train`** → `bench` → `solo` →
`close` (unchanged). A binding without a survey runs today's code; every new branch is entered only on
`b["survey"]`. New code is `tools/party_steps.py`; `tools/party_add_game.py` only routes the stages, hands a surveyed
binding's `label` to it, and makes `bench` need `train`'s PASS for a surveyed title; `tools/h7_endscreen.py` gets one
optional argument (`learn_letters(..., regions=None)`; absent → today).

## B208 — survey

- `survey <code>`: the first ending's final picture with every string today's segmentation (`score_strings`) finds
  as a numbered box, and a grid every 40 px (`survey/boxes.png`, off the repo). Runs once register holds begin,
  other and one ending (register's verdict for those saves, whatever it says about more).
- The answer once: `survey <code> score <P1> <P2>` (a box number, grown 6 px, or `x0,y0,x1,y1`), `letters <WORD> …`,
  or `winner|places` (recorded; the path as today). The kind must be register's, the word register's.
- Shown back: `survey/regions.png`, each region x4 side by side; `ok`, or `again P<k>` then `P<k> <box or rectangle>`.
- Kept in the binding as numbers. **From here nothing searches for a region:** the score place is the region's own
  line of glyphs (today's ink inside the region only), its window the region; letters' places are the regions.
- Every end save is checked against the regions (plan, label): a region with no text names the save and the region
  ("mark it again"), never a new rule.

## B209 — label, plan, train

- **label** on the regions only: two readings of two pictures per end save, the role agrees, the region has as many
  glyphs as the reading, the last look (`regions/look.png`, every glyph in the row of what it was read as).
- **plan**: every symbol the result can show (score: the digits of 0 … the higher of `--max-score` and the highest
  final a reading shows; letters: the word's letters and `-`), how many end saves show each in a result region, and
  the last line, the whole ask: `Nothing more is needed.` or `Still needed: a final score with a <d> in it (either
  player).`
- **train**: templates from the regions' real glyphs (B178's `_digit_stats`, B205's weighting unchanged); synthetic
  variants — each real glyph's ink pasted on the other end saves' regions (their own ink filled by the region's
  median), shifted ±3 / ±1 px, 8 per glyph, a seed from the readings, cut again by `place_glyphs`.
  1. ≥ 2 saves: every glyph read right by a reader learnt without its save.
  2. 1 save: counted "seen once" when rigidity ≥ `BARS["rigid_min"]`, all 8 synthetic variants read as itself, and
     no other symbol's real glyph read as it; else not learnt and asked.
  3. never: not learnt, asked.
  4. today's replays (every end save ends as itself within 2.0 s; begin and other never end).
  On PASS the spec (version 4 with `score.places` from the regions, or version 5 with the regions), the begin and the
  sidecar (with `"code"`) to the rules folder as learn writes them.

## The measure and the bar

**rigidity** = 1 − (the farthest pair of one symbol's real glyphs) / (the nearest pair of two symbols' real glyphs),
over the symbols two or more saves show, in the result regions only; the kind's own distance (score `cell_dists`,
letters `letter_dists`), the larger of the two orders.

| title | symbols (≥ 2 saves) | farthest same | nearest different | rigidity |
| --- | --- | --- | --- | --- |
| T90 | 0 1 2 5 | 0.3425 | 0.7952 | **0.5693** |
| T91 | - O W | 0.1090 | 0.1361 | **0.1990** |
| T92 (after the bar) | 0 2 5 | 0.3277 | 0.9268 | **0.6465** |

**The bar: `rigid_min` = 0.0995** — half the smaller of T90's and T91's (the learner's SAFETY 0.5), written into
`BARS` at 19:27:27Z, before anything of T92 ran. Not moved afterwards.

## B211 — T90, T91, T92 (scratch; no new save; the real rules untouched)

Scratch home / rules / evidence under `$HOME/b208_scratch` (copies of each title's binding, kept saves and pictures;
register's verdict copied; the picture source pointed at nothing, so it could not run — it did not). My own survey
answers (looking at `boxes.png`), my readings of the region pictures, my own looks.

| | T90 (score) | T91 (letters) | T92 (score) |
| --- | --- | --- | --- |
| survey | boxes 25 / 33 (the FINAL column) | rectangles (each corner, wide enough for the whole word) | boxes 10 / 12 (the big finals) |
| label | PASS (13) | PASS (14) | PASS (13) |
| plan's list | 0 1 2 5 twice+; 3 4 8 9 once; **6 7 never** | O W - twice+ | 0 2 5 twice+; 3 4 6 once; **1 never** |
| plan's last line | "Still needed: a final score with a 6 in it and a final score with a 7 in it (either player; one match may show more than one)." | "Nothing more is needed." | **"Still needed: a final score with a 1 in it (either player)."** |
| train | FAIL (22) | **PASS (15)**, 15.3 s | FAIL (21), 7.9 s |
| gate 1 | all | all | all |
| gate 2 | 3, 4 seen once; 8, 9 not counted (7 of 8 variants) | — (none once) | 4 seen once; 3, 6 not counted (7 of 8 variants) |
| gate 3 | 6 7 8 9 asked | met | 1 3 6 asked |
| endings read right | 3 of 5 (end_P1 15-2, end_P2 0-22, end_P2_3 14-24) | 4 of 4 | 3 of 5 (end_P1 02-00, end_P1_2 05-04, end_P2_2 00-02) |

T92's every train cell: `b211/T92/train.md`. Train's last line for T92: "Still needed: a final score with a 1 in it and a
final score with a 3 in it and a final score with a 6 in it (either player; one match may show more than one)."

**Disclosed:**
- **One synthetic variant per glyph cuts badly.** For T90's 8 / 9 and T92's 3 / 6, 7 of 8 variants read as
  themselves; the eighth sits at distance ~0.54-0.95 against ~0.3 for the rest — the cut taking more than the pasted
  glyph, a training artefact. Found after the bar was set and after T92 ran; not changed.
- **plan does not name a once-seen symbol that train later refuses** (as the hashed design says): T92's plan asks for
  1, train for 1, 3, 6. The queue says nothing but plan asks; that conflict is in the reply.
- T90 on the new path counts finals only (the old path counted the line score's cells too), so it needs 6 and 7.
- The T91 regions were marked twice (the first P1 rectangle cut the word off on two saves; seen on the region
  pictures); T90's and T92's once.
- The letters look sheet first used a cut of my own (wrong glyphs); replaced by the letters learner's own cut inside
  the regions before T91's look was given.

## B210 — the hub keeps what it read

`PRIVYHUB_PARTY=1` only: the watcher holds the last K pictures read as an end or `end_unread` (version-4 / 5 specs);
`_keep_result` after a score or letters mini game ends, or is given up as unreadable or with numbers that do not name
an end: `<add_game home>/<code>/played/<UTC stamp>/` with `f1.jpg …` and `read.json` (state, class, scores, winner,
why, seats, utc, the reads). The code: the sidecar's `code`, else the add-game binding naming the game. The newest
200 a title. No game id in it. Keeping only.

## B212 — housekeeping

- `CURRENT.md`: as of today, the work item (the tool, T90 / T91 added under the bench flags, T92 open, the audit, this
  queue) and the next action; headings kept; 11,092 bytes (was 10,878; the soft size 10 KB was already passed; hard
  20 KB); `check_memory_health` structure all true.
- The user's quoted words: `QUEUE_2026-11-20BG.md` one word, `QUEUE_2026-11-23BM.md`, `QUEUE_2026-11-24BN.md` and
  `evidence/ADD_T92_2026-11-23.md` one word each, replaced by "[…]". Only two different words occur in the four files.
- The made-up titles' noise: B178 / B181 / B198 / B200's captures draw each picture's noise from its own seed (the
  save's numbers and the frame); B178 / B181 / B185's harness gives each save its number from its code, role and
  content (`save_n`), not from a counter shared across tests. Assertions unchanged.

## Tests

- **New, three runs each:** `tests/b208_survey/` 9 tests OK ×3 (~45 s); `tests/b210_keep_result/` 9 tests OK ×3
  (~7.5 min; B114's harness, its `b210` mode). B210's first run failed one assertion of my own (it expected only the hub
  part's five kept results; bench's own mini games are kept too) — widened, then the three runs (`tests_new_runs.txt`).
- **Mutations (this queue's code), 9 of 9 caught** on the final code (`tests_mutations.txt`): a region the session did
  not name (its bounds ignored; the next box); a search for a place (the place finder called by train); a never-seen
  symbol counted (train) or not asked (plan); a once-seen symbol counted with a synthetic variant not read; the bar
  moved; the hub keeping without the flag; the watch holding pictures without it.
- **The every-time suites (B207's list), once, all at once, each to its end — B185 included** (it had no result in
  BO), plus the four whose code this queue touched (B191, B103, B114, B124): **9 OK** (B103, B114, B157, B171, B175,
  B178, B191, B198, B200, B204 — ten with B204); **B181 1 failure, B185 3 failures** (24 min, its own end); B124 ran
  0 tests (its harness child's answer was not its last line while 12 other suites ran) — alone, 6 OK on my code and on
  HEAD's.
- **B181's and B185's four failures are B212's noise, not this queue's code:** each reproduces on HEAD `ef8a0ce5`'s
  code with only the per-picture noise files copied in. They are the made-up font's tight thresholds BI reported
  ("some noise seeds miss its 5s and 8s"), which test order had hidden; the old score path's left-out read-back.
  Assertions unchanged. `tests_runs.txt`.

## Checks

`redact_check.txt`, `title_check.txt`, `id_check.txt` (B205's, unchanged), `code_check.txt` (T90 / T91 / T92's names, from
their bindings, never printed) over every file this queue wrote: FAILS 0 each. The team names seen on T90's and T92's
screens: checked by a script kept off the repo (it holds the words) — FAILS 0. T88-T91's rules folder: 23 files,
sha256 before = after. `b208.diff` applies on `ef8a0ce5` (`apply_check.txt`: every file the same as the tree).
