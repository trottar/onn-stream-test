# B104 — the reader made independent of tone: the design, written before code (session B, queue AN)

Baseline HEAD `d61f9b56`. One file of code changes: `tools/h7_endscreen.py`. Tests: `tests/b104_h7_tone/`. The
companion is not touched by B104 (the watcher calls `Reader.read`, so it takes the new measure through the tool).

## What H7-V2 showed (the problem in one line)

B102 compares absolute grey levels; the live window is darker than RetroArch's headless screenshots by a gain-and-offset
or a curve (Cowork: ~16 levels in the mid tones, ~6 in the bright ones; the game's own dark border is 22 in the
screenshots and 0 in the window). The fix must not depend on where that comes from.

## A look before this design (disclosed; read only; no tool code)

`pre_design_look/` (scripts and the numbers they printed): every labelled picture of both folders reduced in memory;
the screen mask learnt from H7-V1 alone; three per-picture tone removals compared on the live pictures, untouched and
with tone changes applied in memory. **Untouched, all three put every live screen far nearer than every fight** (the
standardised one: H7-V1 screens ≤ 0.005, live screens median ~0.03, a tail to 0.32 at range boundaries, every `other`
of both kinds ≥ 0.52). **Under the worst pair (a curve 1.25 and −30)** the gap ratio (others' least ÷ screens' 95th
percentile) was 1.5 for the standardised picture, 1.1 for a median / IQR one, **2.6 for ranks**; ranks are unchanged by
any curve (by construction) and lost least to clipping. That look chose ranks. It also showed **the window's bars
must not be found from dark content**: the game fills the window's height (1318 × 1080 at the screenshots' 1.219
aspect) and its own dark border rows read 0 on the window but 22 on the screenshots.

## The measure (stated; why; what it loses)

- **Each reduced picture's own tone is taken out by ranks against its own screen-mask tone.** For a picture `a`
  (160 × 120, as B102: grey, the area found, 320 × 240 BILINEAR, 160 × 120 BOX) and the screen mask `M`: every pixel's
  value is replaced by its **mid-rank in the distribution of the picture's own values over `M`** — the share of `M`'s
  pixels darker, plus half the share equally bright — with values quantised to ¼ grey level (1,024 steps, a histogram:
  O(n), no sort). A value in [0, 1]. Defined for every pixel (in `M` or not), so the outcome pixels get it too.
- **The screen distance:** the median |rank − the screen reference's rank| over `M` (B102's median, as before: up to
  half the still pixels may change — other portraits — without the screen being missed).
- **A class distance:** the mean |rank − the class reference| **over the outcome mask `O`**, the ranks being the same
  ones (against the picture's own screen-mask tone); the margin = second nearest − nearest (as B102).
- **Why ranks:** any gain, offset or monotone curve on the whole picture leaves every rank unchanged (only clipping at
  0 / 255 and JPEG noise move them) — so the reading does not depend on what the tone change is; the look above showed
  it absorbs the worst pair best. Cheap: one histogram per read.
- **Why the outcome is ranked against the screen mask's tone and not its own (a departure from a literal reading of
  "again over the outcome mask"; disclosed):** a tally patch's own tone, taken out over the patch alone, makes a patch
  that is all bright (0-0) the same as one all dark (1-1) — B102's unseen 1-1 would read as the start, not `unknown`
  (B102's set must stay green), and on the synthetic tallies the start would sit as near the ends as its own frames.
  Ranked against the picture's own screen-mask tone, the patch keeps its place in the picture's own tone curve: still
  unchanged by any whole-picture tone change, and 0-0, 1-0, 0-1, 1-1 stay apart.
- **What it loses (honest limits):** (1) **two classes whose pictures differ only by a tone change of the whole
  picture are not told apart** — the learn report says "not separable" (the test draws exactly that); (2) a fade of the
  screen itself reads as the screen while its contrast holds (a fade-in after a match can count a read early; a fade is
  under a second, K = 3 at one a second); (3) magnitudes are lost — a faint pattern counts as much as a strong one, and
  flat areas with picture noise rank more loosely than in a clean screenshot (the live screens' distances are larger
  than the screenshots', not near a fight's); (4) **a flat picture** (the 2nd-98th percentile over `M` under 8 grey
  levels: black, a fade's bottom) **has no tone to rank** → distances 1.0, never the screen; (5) what B102 lost to
  framing still holds (the search absorbs ±8 px at 640 wide and 0.95-1.05).
- **Thresholds in that measure:** B102's rule unchanged — halfway (`SAFETY = 0.5`) across the gap each class and the
  screen leave between their own worst and the foreign best; the margin needed = half the smallest margin seen; a gap
  ≤ 0 → "not separable" and that class is never named.
- **Learning the masks in that measure:** the screen mask `M` — pixels whose rank (against `M`) varies little across
  every screen frame (std < `STEADY_R` = 0.05), found by three passes from `M` = every pixel (ranks against the previous
  pass's `M`; a pixel may come back); the outcome mask `O` — pixels steady within each screen class (std < 0.05) and
  whose class means are more than `DIFFER_R` = 0.25 apart for some pair; the references: the screen's mean ranks (the
  whole 160 × 120 grid, used over `M`), each class's mean ranks over `O`. Frames of different sources (screenshots,
  window pictures) are learnt together because ranks and the area rule take out tone and size. The values 0.05 / 0.25
  / 8 are the initial ones; any change is an amendment hashed before the run it changes.

## The game's picture found inside a window — one way, in `reduce` (learn, read, replay and the watcher all call it)

- From the grey picture: on each side, the count of whole edge columns (left, right) / rows (top, bottom) whose
  **brightest pixel is ≤ 16** (a window's black bar). Per axis, the bar is the smaller of its two sides (bars are
  symmetric; a game's own dark edge on one side is not a bar). **Only one axis is cut** — the one with the larger bar
  as a share of its side — and **only if that share is ≥ 5 %** and leaves at least half: a window scaled to fit has
  bars on one axis; a game's own dark border is a few per cent. Else the picture as it is. Then 320 × 240 whatever the
  aspect (the screenshots and the window's game picture share the game's aspect).
- On the real pictures this cuts 301 columns each side of the 1920 × 1080 window (the game 1318 × 1080) and nothing
  from a 640 × 525 screenshot (its border rows are 22; its top / bottom dark rows are under 5 %).
- The spec's `aspect` becomes a record of the learnt pictures' median cut aspect; it is no longer used to read.

## The spec — version 2, the old refused

- `"version": 2`, `"measure": "rank-against-screen-mask"`, the area rule's constants (`bar_max` 16, `bar_share` 0.05),
  `quant` 0.25, `flat` 8, `steady_r`, `differ_r`, `safety`, K, the search's grid, the masks' sizes, the frames per class
  and per source, the arrays file and its sha256 (as B102).
- **`load_spec` of a version-1 spec → `ValueError("this end-screen spec was learnt with the old measure (absolute grey
  levels): learn it again")`** — never read. Any other kind / version → B102's line.

## The tool's commands

- `learn <runs> <labels> [<runs> <labels> …] <out>.endscreen.json [--half first]` — one or several sources (each a
  runs folder and its labels file); the report adds frames per source.
- `score <runs> <labels> [<runs> <labels> …] <spec> [--half second]` — as B102's, over all sources; adds per source.
- `read <spec> <picture>` — as B102's.
- **`replay <run folder> <spec> [--k K] [--labels <labels>]`** — the run's pictures in `index.csv` order through **one**
  `Reader` (as the watcher: the alignment kept, the search floored by the pictures' own seconds) and B102's `Ended`
  with K, **re-armed after each `ended`** (a fresh watch; the start must then be seen again — the load=0 case);
  prints one JSON line per picture (seconds, class, screen distance), one per change of class, one per `ended` (its
  seconds, class) and a summary; with labels (default: `labels.json` in the run folder, when present), each `ended`
  set against **the first picture labelled with an end class after the preceding `other` stretch** (seconds between).
- The API: `labelled_frames` / `learn` / `score` take a labels dict or a path, and a list of sources.

## Proved on the real pictures (numbers only in the record; read only; scripts in the record dir)

1. H7-V1 alone → the 508 live pictures against Cowork's labels (per class right / wrong, the least margin, `other`
   read as the screen); the reverse.
2. Live match 1 (its seconds from the labels' `matches`) + H7-V1's `end_P2` run → match 2; the mirror (match 2 +
   H7-V1's `end_P1` run → match 1).
3. Everything → the score, the masks' sizes, the gaps: the spec A will use (learnt in memory and its numbers recorded;
   **the spec file itself is not written to the rules folder** — that is A's step; it may be written under the
   git-ignored `runtime/` scratch of this task only if needed, and listed).
4. Tone changes in memory, applied to the full picture before reduction (clipped to 0-255): offset ±10, ±20, ±30;
   gain 0.8, 0.9, 1.1, 1.2; gamma 0.8, 0.9, 1.1, 1.25; each alone and every pair of extremes (the worst named) — on the
   held-out second halves of both sources with a spec learnt on the first halves of both; and on the live pictures with
   the H7-V1-only spec. Counts per class, `other` read as the screen, classes changed against the untouched read; the
   range absorbed with nothing misread.
5. H7-V1 alone as in B102 (first halves → second halves): every class right; B102's moved cases with the search; one
   read's time.
6. `replay` on the live run with the arrangement-3 spec, K = 3 and K = 2: each `ended` against the first select-screen
   picture after each match.

Each must give `other` read as the screen = 0; if any does not, that is reported as it is, not tuned away silently.

## Tests (`tests/b104_h7_tone/`, synthetic pictures from B102's drawing; temp dirs removed)

B102's set unchanged and green; the same screen under an offset (±30), a gain (0.8 / 1.2) and a curve (0.8 / 1.25)
reads the same class; 60 fights under each never read as the screen; **two classes whose pictures differ only by a
whole-picture tone change → "not separable"** (and, disclosed, a tally patch whose tone alone differs from the rest of
the picture IS told apart under this measure — a test states it); a picture inside black bars of another size (pillar
and letter box) reads as the bare picture, with no search; a dark game border on one side is not cut; a flat picture
never reads as the screen; a version-1 spec refused with the plain line; learning from two sources of different sizes
and tones together; `replay` on a synthetic run (the ended moments, re-armed); one read in milliseconds. Mutations as
B102's runner. 3 runs.
