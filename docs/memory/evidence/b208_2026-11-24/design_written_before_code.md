# B208-B213 — the front of the add-a-game path, rebuilt once (design written before code, queue BP)

Read line 2026-11-24T19:16:04Z; limit 22:16:04Z. Written before any code; its sha256 in `design.sha256`.

## The path (the user's five steps, the tool's stages)

`register` (unchanged: three saves) → **`survey`** (new) → **`label`** on the regions (new, only for a binding that has a
survey) → **`plan`** (new) → **`train`** (new) → `bench` → `solo` → `close` (unchanged).

`plan` follows `label`, not the other way round: plan counts how many real pictures show each symbol in a result
region, and only the session's readings say which symbol a glyph is. The queue's B213 order (plan before labels) is
recorded as a change in the reply, not made silently.

A binding without `survey` (T88-T91 as they are) runs today's code byte for byte: every new branch is entered only on
`b.get("survey")`. The new code is one new module, `tools/party_steps.py`; `tools/party_add_game.py` gets only the
three stage names, their argument parsing, the dispatch, `label` handing a surveyed binding to the new module, and
`bench` / `solo` / `rehearse` requiring `train`'s PASS instead of `learn`'s for a surveyed binding.
`tools/h7_endscreen.py` gets one optional argument: `learn_letters(..., regions=None)` — given, each player's place is
the surveyed rectangle and the existing cut looks only inside it (`_letters_places` with the zones replaced by the
regions; nothing outside them is looked at); `None` → today. Nothing else in either old file changes.

## B208 — survey

- `survey <code>`: requires register's PASS. The ending: the first end save (sorted roles); its final screen is today's
  label picture (`_two_pictures`, B184's held anchor) made by today's `_pictures` if absent (the picture source only
  if the pictures are not there). Off the repo, `<home>/<code>/survey/`:
  - `boxes.png`: the game's area at 640 x 480 in colour, scaled x2, **every string today's segmentation finds**
    (`h7_endscreen.score_strings` on `score_picture`; strings of each polarity and radius merged when their boxes
    overlap by half) drawn as a numbered box, and a ruled grid every 40 px labelled in reader pixels;
  - `boxes.json`: the boxes as numbers (reader pixels, 640 x 480).
  - the line: `survey <code>: answer — survey <code> <kind> [<word>] <P1> <P2> (a box number or x0,y0,x1,y1)`.
- The answer: `survey <code> score 3 7`, `survey <code> letters WOW 20,30,120,70 520,30,620,70`, `survey <code>
  winner|places`. Players' count from the binding; one region per player, P1 first; kind must equal register's
  `--result` (else REFUSED, one line); letters: the word must equal register's `--word`.
- A region: a box number's box grown by `SURVEY_MARGIN` = 6 px each way (clipped to the picture); a rectangle as
  given. Kept in the binding: `survey = {"kind", "regions": [[x0,y0,x1,y1] per player], "margin": 6, "size": [640,
  480], "from": the ending's role, "confirmed": false}`.
- Shown back: `regions.png` — each player's region cut out, x4, side by side, labelled P1 / P2. The line:
  `survey <code>: look at regions.png — answer survey <code> ok, or survey <code> again P<k>`.
- `survey <code> ok` → `confirmed: true`, the verdict PASS (cells: the kind as register's; one region per player;
  every region inside the picture; the regions do not overlap; confirmed). `again P<k>` drops that region; the next
  answer names it again (the others kept).
- `winner` / `places`: the kind recorded, PASS, the line says "the path goes on as today (label, learn)". Nothing
  else changes for them.
- **The regions hold for every save:** `plan` and `train` check every end save's final picture has text in each
  region (ink of today's `_ink` at the region's polarity: at least `SCORE_HMIN` tall for score; letters: the corner
  text cut of the existing letters colour cue — see train). Not → the cell names the save and the region:
  `end_P2_3: no text in P1's region — mark the regions again (survey <code> again P1)`. Never a new rule.
- From here on nothing searches for a region: score places are built from the region (below); letters' places are
  the regions.

## B209 — label (regions only), plan, train

### label, for a surveyed binding

- Its pictures: today's `_two_pictures` for every end save, plus per region a x4 crop `<role>.P<k>.png`.
- The readings: score `<role>=<P1>-<P2>,<P1>-<P2>` (each the number as drawn: "02" keeps its 0); letters
  `<role>=<P1>/<P2>,<P1>/<P2>` (today's B191 grammar). Cells per save: two readings the same; the role agrees (score:
  end_Pk's side strictly ahead; letters: the other player's corner equals the word, its own does not); the region
  holds text (above). No line score, no stats table, no sum, no place cell.
- The last look: `look.png` — every glyph cut from the regions (both pictures' first), grouped in rows by the symbol it
  was read as. `look=all` → PASS; `look=<symbol>:<i>[.<j>]` → those glyphs named wrong: the cell names their saves to
  read again. Label's verdict PASS needs every cell and `look=all` for the current readings.
- A glyph in a region (score): `h7_endscreen.place_glyphs` on the region's place (below); (letters): today's
  `_letter_cells` inside the region.

### the place from a region (score; no search)

The region's own string on the ending the survey was made on: today's components (`_ink`, `_components`) **inside the
region only**, each polarity and radius in `SCORE_RS`; the first (polarity, radius) whose parts >= `SCORE_HMIN` tall
make one line (tops and bottoms within `SCORE_TOL`) → `top`, `bot` the line's, `pol`, `r`; `x0` / `x1` the region's
edges brought in by `place_glyphs`'s own pad so its window is the region. `group` "" (one font: the result's), `align`
"region". Kept in the spec as `score.places` — where `ReaderScore` already takes them. No line in the region → the
title does not fit: one line, stop (`<code>: no number in P<k>'s region on <role> — mark it again`).

### plan

Requires label's PASS. One page `plan.md` (+ `plan.json`), one list:

- **every symbol the result can show**: score — the digits of 0 … N, N = the higher of `--max-score` and the
  highest final any save's reading shows (none given and none above 9: 0 … 9 needs every digit; the digits of
  `str(i)` for i in 0..N, plus 0 when a reading draws a leading 0); letters — the word's letters and `-` (the
  not-yet mark) when any reading shows it.
- for each, **how many real pictures show it in a result region**: the number of end saves whose reading (the
  session's, label-checked) has that symbol in a region → `twice or more` / `once` / `never`.
- the regions-hold check for every end save (a cell).
- **The last line, the whole ask**: `Nothing more is needed.` when no symbol is `never`; else
  `Still needed: a final score with a <d> in it (either player).` (score; several digits: `with a 1 and a 7 in it
  (either player, one match or more)`), or `Still needed: a match where <the letters> show in a player's corner.`
  (letters). A `once` symbol is **not** asked for: train decides it by the once rule; if train refuses it, train's
  line says so (it is then counted `never`-like and the plan line is re-written by train — see gate 2).
  Nothing else on the new path asks the user for a save.

### train

Requires plan's PASS (plan PASS = the page written and its regions cell met; it passes even with symbols still
needed — the ask is its last line, and train's gate 3 holds the title).

- **score**: the real glyph cells (`glyph_cell`) of every end save's two pictures in each region, labelled by the
  reading's drawn digits left to right (a region whose glyph count is not the reading's → a cell not met, naming the
  save). Synthetic (B192's way): each real glyph's ink pixels (`_ink` at the place's polarity and radius, inside its
  box) pasted onto the same region of the other end saves' first pictures, their own ink there first filled with the
  region's median non-ink grey, at a shift dx in [-3, 3], dy in [-1, 1] drawn from `numpy.random.default_rng(seed)`,
  seed = the first 8 hex of the sha256 of the sorted readings; `SYN_PER_GLYPH` = 8 variants per real glyph, each
  re-cut by `place_glyphs` and `glyph_cell`. Templates: `_digit_stats(real, shown, synthetic)` (B205's weighting:
  the synthetic weigh at most as the real — the existing function, unchanged; every measure is on real cells).
  The spec: version 4, today's screens (`_learn_one_screen` on the begin's / the end saves' / the mid-match save's
  labelled frames, exactly as `_learn_v4` does it — the same calls, the learner's own labels via today's `_labels`),
  `score = {sides, places (from the regions), keys, thresholds, separable, margin_needed, found: true, max_score: N,
  columns: [], region_source: "survey", regions}` and `digit_refs`.
- **letters**: `learn_letters(..., regions=the survey's)` — today's B191 / B192 learner with the places fixed.
- **The gates, each a cell:**
  1. **two or more real samples**: for every end save X, the templates learnt without X (real and synthetic both
     without X); every glyph of X whose symbol has >= 2 saves showing it is read (B178's rule: separable, within
     threshold, margin >= margin_needed) as its label. Letters: today's `_learn_letters_spec(..., without=X)` and
     its read of X, only the corners whose symbols are all >= 2.
  2. **one real sample** (the user's decision, 2026-11-24): counted, marked "seen once", when
     (a) **the font is rigid**: `rigidity` (below) >= `BARS["rigid_min"]`;
     (b) every synthetic variant of that glyph is read (full reader) as itself; and
     (c) no other symbol's real glyph is read as it.
     Not counted → not learnt (its template dropped from the spec), and train's last line asks for it as plan would.
  3. **never seen**: not learnt; train FAILs with plan's line as its last line. Never invented.
  4. **the screens**: today's replays — every end save's run ends as itself with the right numbers / corners within
     `ended_within_s`; the begin recognised within `start_within_s` and never ended; the mid-match save never ended.
- On PASS: the spec, the begin and the sidecar written to the rules folder exactly as `learn` writes them (the sidecar
  `{"players", "result"}` as `_sidecar`, plus `"code"` for B210), `b["learnt"]` set; the verdict `train`.
  On FAIL nothing reaches the rules folder.

### the measure and the bar (fixed before T92 is looked at)

- **rigidity** = 1 - (the farthest pair of real glyphs of one symbol) / (the nearest pair of real glyphs of two
  symbols), over the symbols with two or more saves showing them, real glyphs in the result regions only. Pair
  distance: the kind's own — score: `cell_dists` (B178's local 3 x 3 mean, least over ±1 px), the larger of the two
  orders; letters: `letter_dists` (B191's), the larger of the two orders. 1 = every symbol's glyphs identical; 0 = a
  symbol's own farthest pair as far as two symbols' nearest; < 0 = not separable.
- **The bar**: computed for T90 and T91 on the new path (B211), `rigid_min` = half the smaller of the two (the
  learner's SAFETY 0.5: every threshold sits halfway across a gap), written into `BARS` with its source, then T92
  run. Not moved after T92 is looked at. If a kind has fewer than two symbols with two samples, rigidity is
  undefined: gate 2 not met for that title (the line says so).
- The tool's own measure cells (gate 1, margin_needed_min) stay as today's `BARS`.

## B210 — the hub keeps what it read (`PRIVYHUB_PARTY=1`; absent = today)

- `companion/h7_minigame.py`: in `_run`, only when the environ has `PRIVYHUB_PARTY=1` and the spec is version 4 or 5,
  the last K (= `ended.k`, 3) pictures whose read was an end class or `end_unread` are held in memory (`w["_end_seen"]`,
  pictures and their reads); `end_pictures(token)` returns them. Absent → no field, nothing held.
- `companion/party_minigame.py`: after `_final` for an entry with `score_read`, or a letters sidecar, ended or given
  up (any `why`), `_keep_result(mg, runner, state, fields)`: `<add_game home>/<code>/played/<UTC stamp>/` with the
  held pictures (`f1.jpg` …), `read.json` = {state, class, scores or the letters read, winner seat, seats, utc,
  why}. The code: the sidecar's `"code"`, else the add-game binding (`<home>/*/binding.json`) whose game is this
  one; neither → one row `result_not_kept` (no folder). The newest 200 a title: older `played/` folders removed by
  the hub (its own ring). Any error → one row `result_not_kept`, never raised. No name in it (the folder by code,
  the stamp; read.json has no game id).
- Tests in B114's harness style (fake emulator, fake runner); flags absent → nothing written, the rows today's.

## B211 — T90, T91, then T92 (scratch)

Scratch home / rules / evidence / logs under `$TMPDIR` on the main disk (`PRIVYHUB_ADD_GAME_HOME`,
`PRIVYHUB_H7_RULES`, `PRIVYHUB_ADD_GAME_EVIDENCE`, `PRIVYHUB_ADD_GAME_LOGS`); each title's binding, kept saves and
pictures copied there (read only from the real ones); register's verdict copied so survey's require holds (register
not re-run: no slot read). My survey answers by looking at `boxes.png` myself; labels from my own reading of the
pictures; my own looks. T90, T91: survey, label, plan, train → every kept ending read right through the new spec, the
rigidity of each. The bar set and written into `BARS`. Then T92: survey, label, plan, train — every cell as it
falls, plan's last line as it stands. The real rules folder's sha256 (every file) before = after.

## B212 — housekeeping; B213 — the commands (no code)

As the queue. The made-up titles' noise per picture: the suites on the every-time list whose made-up pictures draw
noise from one shared generator in test order get the generator seeded from the picture's own name
(`default_rng(int(sha256(name)[:8], 16))`); assertions unchanged.

## Tests

`tests/b208_survey/` (new): survey boxes on made-up screens, the answer grammar, the region kept, the again/ok flow,
the regions-hold check naming a save; the place from a region; plan's symbols, counts and its last line; the gates on
made-up glyph cells (rigid font, once counted / refused, never asked); the bar. `tests/b210_keep_result/` (new): the
keep with the flags, nothing without. Three runs each. Mutations (this queue's code only): a region the session did
not name taken; a search for a region (the place finder called); a never-seen symbol counted; a once-seen symbol
counted with a synthetic variant not read; the bar moved; the keep without the flag.
