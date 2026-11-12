# B102 — the end-screen learner: design (written before code; hashed)

Queue 2026-11-12AM, item B102. Baseline HEAD `8b43a266`. Before this design: a numeric look at H7-V1's labelled
frames (counts, pixel statistics and distances only; no picture kept, nothing written beside them) to choose the
sizes below — the masks came out at ~16,500 px (screen) and ~124 px (outcome) of 19,200, own distances ≤ 2.4 against
other frames ≥ 26 (median form); a 2-px shift at 640 wide already brings an outcome distance near the midpoint of its
gap, an 8-px shift or a 5 % rescale breaks the plain read — so the tool carries a small alignment search.

## The tool: `tools/h7_endscreen.py` (Python 3, PIL + numpy — both already on the hub as Debian packages; nothing fetched)

### The picture, reduced (`reduce(img, aspect)`)

1. grey (`L`);
2. **the window's bars taken off**: if the picture's width / height differs from the spec's `aspect` by more than 2 %,
   the centre of the picture at the spec's aspect is kept (columns cut for a wider picture, rows for a taller one) — the
   stream's window can carry bars a screenshot does not; never cut per frame from the content (a select screen's own
   dark bands would move the cut);
3. resized to **320 × 240** (PIL BILINEAR, which filters when shrinking), then to **160 × 120** (BOX) — **the reduced
   picture is 160 × 120 = 19,200 grey values, float32, 0-255**. The aspect is not kept (both sizes fixed), so a picture
   of a slightly different aspect lands on the same grid. The 320 × 240 step is what the search below moves.

### Learn (`learn(runs_folder, labels, half=None) → (spec, arrays, report)`)

- **Input:** a folder of runs (`<run>/index.csv` with `seconds,file,…`; the frames beside it) and a labels file
  (`{"classes": {name: text}, "runs": {run: [{"from", "to", "label"}]}}`, times inclusive). `ignore` is left out.
  `other` is the non-screen class; **the start class** is `start` (an option); every other class is an end class.
- **Plain errors (ValueError, one sentence):** a run named in the labels with no folder or no `index.csv`; a label not
  in `classes`; **a class named in `classes` (other than `ignore`) with no frame in its ranges**; no `other` frame; fewer
  than two screen classes; the start class absent.
- `half="first"`: from each labelled range only its first half (by count, `n // 2` frames; at least one) is learnt
  from; `half=None`: all.
- **Steady** = a pixel's standard deviation over the frames in question < **6 grey levels** (`STEADY`).
- **The screen mask:** the pixels steady across all frames of every screen class taken together (every class but
  `other`). Its reference: their mean there.
- **The outcome mask:** the pixels steady within each screen class (each class's own deviation < `STEADY`) **and**
  different between them (the largest gap between two classes' means > **32** grey levels, `DIFFER`). Each class's
  **reference**: its mean over the outcome mask.
- **Distances.** The screen distance: **the median** of |frame − screen reference| over the screen mask (robust: up to
  half the screen's still pixels may change — another pair of portraits — without the screen being missed). A class
  distance: the mean of |frame − class reference| over the outcome mask. The margin: the second-nearest class distance
  − the nearest.
- **Thresholds (the safety margin: halfway across the gap).** The screen: worst own (largest screen distance over the
  screen classes' learnt frames) and best foreign (smallest over the `other` frames); gap = foreign − own; threshold =
  own + **0.5** × gap. Per class: worst own distance (its frames to its reference) and best foreign (the other screen
  classes' frames to its reference); gap; threshold = own + 0.5 × gap. The margin needed: **0.5 ×** the smallest
  margin of a learnt screen frame to its own class. A gap ≤ 0 → that verdict "not separable from these frames"; such a
  class is never named by a read (its frames read `unknown`); a screen gap ≤ 0 → the spec says `usable: false` and
  every read says `other`.
- **The spec:** `<name>.endscreen.json` (small: version, `size` [160, 120], `aspect`, the classes, start / end
  classes, the thresholds, `STEADY` / `DIFFER` / the safety, `K`, the search's grid, the masks' sizes, frames per
  class, the arrays file's name and sha256 — no path, no picture) and **one arrays file beside it,
  `<name>.endscreen.npz`** (`screen_mask`, `screen_ref`, `outcome_mask`, `refs` [one row per class, the classes'
  order]; numpy arrays, not pictures; loaded with `allow_pickle=False`, its sha256 checked against the JSON).
- **The learn report** (a dict, JSON): frames per class (learnt), the masks' sizes (pixels and share of the 19,200),
  the outcome mask's bounding box on the 160 × 120 grid, per class worst own / best foreign / gap / threshold and the
  verdict `separable` / `not separable from these frames`; the screen's the same; the margin needed; the time to learn.

### Read (`Reader(spec).read(img, now) → {"screen", "class", "distances", "margin", "align"}`; `read(spec, img)`)

- At the current alignment (scale, dx, dy on the 320 × 240 step; identity to begin): the screen distance; **not under
  the screen threshold → `{"screen": false, "class": "other"}`**; else the class distances, the nearest and the margin:
  the nearest's distance ≤ its threshold **and** margin ≥ the margin needed **and** the class separable → that class;
  **else `"class": "unknown"`** (a screen no class is close enough to — a draw never shown, a tally never learnt —
  reported, never guessed).
- **The search (alignment):** when a read is not the screen and no search ran in the last **10 s** (`SEARCH_EVERY`;
  a fresh `Reader` searches at once): coarse — scales 0.95 / 0.975 / 1 / 1.025 / 1.05 × shifts −4, −2, 0, +2, +4 px
  of the 320 × 240 step in x and y (±8 px of a 640-wide picture), 125 candidates; then fine — ±0.0125 scale × ±1 px
  around the best, 27 candidates; each candidate's screen distance; **the best is adopted only if it is under the
  screen threshold**, and the read is made at it. The `Reader` keeps it (the window does not move during a game).
  `read(spec, img)` = a fresh `Reader`: every non-screen frame gets the full search — the worst case for "an `other`
  frame read as the screen", so `score` uses it.
- **Ended (`Ended(spec)`, K = 3 agreeing reads in a row, at one read a second ≈ 3 s):** fed each read; `seen_start`
  after K start reads in a row (or told the start was loaded); an end class counts only after `seen_start`; `ended`
  with the class after K reads in a row of the same end class; any other read (other, unknown, another class) breaks
  the run. `unknown` reads are reported as the watcher's current class, never as an end.

### Score (`score(runs_folder, labels, spec, half=None) → dict`)

`half="second"`: the frames each range did not learn from (the second half); `None`: all labelled frames. The
confusion counts per labelled class (read as: each class, `unknown`, `other`), **`other_read_as_screen`** (must be 0),
right / total per class, per class the largest own distance and the smallest margin among right reads, the time per
read (median / worst ms).

### CLI

`h7_endscreen.py learn <runs> <labels> <out .endscreen.json> [--half first]` (writes the JSON and the `.npz`, prints the
report) · `score <runs> <labels> <spec> [--half second]` · `read <spec> <picture>`. Nothing is written beside the frames.

## On T88's real frames (read-only; `t88_eval.py` in the record's dir; numbers only)

Learn on the first half of each labelled range (in memory or in a temp folder off the repo; the spec is not kept in
git), score on the second half and on every `other` frame; the counts, gaps, masks' sizes, learn time, read time (one
frame, ms, on the hub, plain and with the search). Then the same score with every scored frame **shifted** (x / y,
2-12 px at 640 wide) and **rescaled** (0.95-1.05) in memory (PIL affine, black fill), with the search on and off — the
right / total per class, `other_read_as_screen`, and the range the search absorbs.

## Tests (`tests/b102_h7_endscreen/`, synthetic pictures drawn in the tests; PIL + numpy only)

A 320 × 260 "screen": a still panel (bars and boxes), **a moving banner** (a stripe whose offset changes each frame),
**a varying portrait** (a box whose shade changes each frame), and **a digit-like patch per side** (seven-segment
"0" / "1"); outcomes `start` (0-0), `end_P1` (1-0), `end_P2` (0-1); `other` frames of moving shapes on a different
background. Cases: the masks exclude the banner's and the portrait's pixels and the outcome mask lies inside the digit
patches; the three classes are told apart; **an unseen third outcome (1-1) reads `unknown`**; no `other` frame ever reads
as the screen (search on); K in a row (2 end reads then an other → not ended; a third → ended; an end before start →
not counted; unknown never ends); **a labels file naming a class with no frames → the plain error**; a run folder
missing → the plain error; the spec written and read back (sha256 checked, a changed `.npz` refused); the reduced size
160 × 120 and the bars cut (a picture with black side bars reads as the screen); a shifted / rescaled screen read right
with the search; one read in milliseconds. Temp dirs removed (`_tmp_cleanup`).

## Record

`evidence/B102_H7_END_SCREEN_LEARNER_2026-11-12.md` + `b102_2026-11-12/` (start files, this design + hash, `b102.diff`,
`t88_eval.py` + its numbers, tests ×3, mutations, redact / title checks, manifest); `patches/B102_H7_END_SCREEN_LEARNER.md`.
No title, character name, path or picture in any of it.
