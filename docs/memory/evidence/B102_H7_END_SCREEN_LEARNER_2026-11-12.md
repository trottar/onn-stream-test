---
memory_schema: 1
as_of: 2026-11-12
status: BUILT (session B, queue AM) — tools/h7_endscreen.py learns, from labelled pictures alone, which part of a game's screen marks a mini game's start / end and which part tells the outcomes apart, and reads a picture back (screen? → which class, or "unknown" → else "other"; K = 3 agreeing reads to end; a small shift / scale search). On the user's game's real frames (H7-V1's, read-only): learnt on the first half of each labelled range, the second half read 576 / 576 right — start, the P1 end and the P2 end told apart, **0 fight frames read as the screen**; one read ~1 ms on the hub, a learn 1.6 s; with the search on, pictures shifted up to 8 px and rescaled 0.95-1.08 still read, never a fight as the screen. No companion change. Nothing committed. No title, code name, character name, path or picture in this record
---

# B102 — the end-screen learner (`tools/h7_endscreen.py`) (2026-11-12)

**Why (the user's words, 2026-11-12):** "I don't need automatic scoring at all, I just need to know who got 1-4 in a
game or who won"; "you don't even have knowledge when a mini game would end"; "we need to check per game start and end
of each mini game so the end we take that screenshot. Then we give that to the model to train." **The tool must find
the end screen from labelled pictures by itself — no hand-drawn boxes — because the same has to work for dozens of
games.** **Baseline:** HEAD `8b43a266`. **Design** hashed before code at 15:42:47Z (`b102_2026-11-12/design.sha256`);
**amendment 1** hashed at 15:44:19Z, before any test or evaluation ran (`design_amendment_1.*`): a read that is the
screen but `unknown` also searches the alignment.

## The tool

- **The picture, reduced:** grey; a window's bars cut by the spec's aspect (only when the picture's aspect is > 2 %
  off — never per frame from the content); 320 × 240 (the search's step) → **160 × 120 = 19,200 grey values**.
- **Learn** (`learn <runs> <labels> <out>.endscreen.json [--half first]`): `ignore` left out; `other` = not the screen;
  `start` = the start class; the rest end classes. **Steady** = a pixel's deviation < 6 grey levels. **The screen
  mask:** steady across all screen classes' frames together. **The outcome mask:** steady within each screen class and
  > 32 levels apart between two classes' means. **References:** each class's mean over the outcome mask. **Distances:**
  the screen's = the median |frame − reference| over the screen mask (up to half the screen's still pixels may change —
  other portraits — without the screen being missed); a class's = the mean over the outcome mask; the margin = second
  nearest − nearest. **Thresholds halfway across the gap** each class (and the screen) leaves between its own worst and
  the foreign best; the margin needed = half the smallest margin seen. A gap ≤ 0 → "not separable from these frames"
  and that class is never named.
- **The spec:** `<name>.endscreen.json` (small: sizes, aspect, classes, thresholds, K, the search's grid, the masks'
  sizes, frames per class, the arrays file's name and sha256) + **one arrays file beside it, `<name>.endscreen.npz`**
  (the two masks, the screen reference, one reference row per class — arrays, not pictures; loaded without pickle; its
  sha256 checked). **The learn report:** frames per class, the masks' sizes and shares, per class worst own / best
  foreign / gap / threshold / verdict, the screen's the same, the margin needed, the learn time.
- **Read** (`Reader.read(picture)` → `{"screen", "class", "distances", "margin", "align"}`): not under the screen
  threshold → `other`; else the nearest class if under its threshold with the margin, **else `unknown`** — reported,
  never guessed. **The search:** when a read is not the screen, or the screen but `unknown`, at most once per 10 s per
  `Reader` (a fresh `Reader` at once): 125 coarse candidates (scale 0.95-1.05 × shifts ±4 px of the 320 step, i.e. ±8 px
  at 640 wide) + 27 fine (±0.0125, ±1 px); the best is kept only if under the screen threshold; the `Reader` keeps it.
- **Ended** (`Ended(spec)`): **K = 3 agreeing reads in a row** (one read a second ≈ 3 s); `seen_start` after K start
  reads, or when told the start was loaded; an end class counts only after it; any other read breaks the run;
  `unknown` never ends.
- **Score** (`score <runs> <labels> <spec> [--half second]`): confusion counts per labelled class, right / total,
  **`other_read_as_screen`**, the worst own distance and least margin among right reads, the read time.
- PIL + numpy only (both Debian packages already on the hub; nothing fetched). Nothing is written beside the frames.

## On the user's game's real frames (H7-V1's, read-only; `b102_2026-11-12/t88_eval.py`, `t88_eval_results.jsonl`)

Cowork's labels; learnt **in memory** on the first half of each labelled range; no spec kept; no picture, crop or
name in any file here.

| | start | end_P1 | end_P2 | other |
| --- | --- | --- | --- | --- |
| frames learnt (first halves) | 394 | 36 | 37 | 109 |
| **the second halves read right** | **394 / 394** | **36 / 36** | **37 / 37** | **109 / 109** |
| every labelled frame read right (both halves) | 788 / 788 | 72 / 72 | 74 / 74 | 218 / 218 |
| worst own distance · best foreign · gap · threshold | 1.44 · 52.53 · 51.09 · 26.99 | 1.72 · 53.35 · 51.63 · 27.53 | 1.72 · 52.73 · 51.01 · 27.23 | — |
| least margin among right reads (needed 25.41) | 52.1 | 51.5 | 50.8 | — |

- **`other` read as the screen: 0** (second halves; and 0 of all 218).
- **The screen:** worst own 2.36, best foreign (a fight frame) 29.81, gap 27.45, threshold 16.09 — **separable**. Every
  class **separable** — **start, the P1 end and the P2 end are told apart** with ~50 grey levels to spare.
- **The masks:** the screen mask **16,498 px (85.9 %)**; the outcome mask **124 px (0.65 %)**, one compact patch
  (x 63-108, y 84-92 on the 160 × 120 grid) — where the two tally numbers sit, found from the labels alone.
- **Times on the hub:** learn **1.6 s** (576 frames + 109 other, JPEG decode included); **one read 1.0 ms** (worst 1.1;
  the picture decoded); a read with a full search 158 ms; a JPEG decode 1.6 ms.

### Alignment — the frames shifted and rescaled in memory (the second halves; PIL affine, black fill)

| moved (px at 640 wide; scale) | plain read: right (start / P1 / P2 / other) | with the search | `other` as screen |
| --- | --- | --- | --- |
| +2, 0 | 167 / 36 / 37 / 109 | **394 / 36 / 37 / 109** | 0 |
| +4, 0 · +8, 0 · 0, +8 · +8, +8 | 0 / 0 / 0 / 109 | **all right** | 0 |
| 0, +4 | 0 / 36 / 37 / 109 | **all right** | 0 |
| −6, +5 | 0 / 0 / 0 / 109 | 372 / 33 / 36 / 109 | 0 |
| scale 0.97 · 1.03 | 0 / 0 / 0 / 109 | 372 / 33 / 36 / 109 | 0 |
| scale 0.95 · 1.05 · 1.08 | 0 / 0 / 0 / 109 | **all right** | 0 |
| +5, +3, ×1.04 | 0 / 0 / 0 / 109 | **all right** | 0 |
| −4, −6, ×0.96 | 0 / 0 / 0 / 109 | 372 / 33 / 36 / 109 | 0 |
| +12, 0 (past the search's reach) | 0 / 0 / 0 / 109 | 145 / 33 / 36 / 109 | 0 |
| +16, 0 · scale 0.92 | 0 / 0 / 0 / 109 | 0 / 0 / 0 / 109 · 0 / 1 / 36 / 109 | 0 |

- **Without the search the reading depends on exact alignment:** 2 px already loses most start frames, 4 px loses
  everything. **With the search**, shifts to ±8 px and rescales of 0.95-1.08 read right, with the same small set of
  frames missed in four cases (22 start, 3 P1, 1 P2) — **every missed frame, in every moved case (12 px and 0.92
  included), reads `unknown`: never the other side, never `other`** (`t88_moved_confusion_results.jsonl`) — so a miss
  can delay an end, never name the wrong winner. **In no case was a fight frame read as the screen.** The search's grid
  is 2 px at 640 wide, so an odd shift is read half a step off (own distances up to ~20 after a search, against
  thresholds ~27). The stream's window logs 879 × 720 against the screenshots' 878 × 720 — inside what is absorbed.
- **The search's cost:** 158 ms; at most once per 10 s per watch, and the alignment is then kept — one read a second
  costs ~1 ms plus, rarely, a search.

## What these frames cannot show (the set's limits — Cowork's)

One pair of characters (the screen mask holds the portraits as they were; the median distance lets up to half the mask
change, but a new pair is unseen); one run per end class; the two start runs the same picture for picture; no draw;
RetroArch's own screenshots, not the stream's window. **The live check (H7-V2) is where other characters, the same
character on both sides and the window read are first seen.**

## Tests (`tests/b102_h7_endscreen/`, 16; synthetic pictures drawn in the tests — no game art; PIL + numpy only)

A 320 × 260 "screen": a still panel, **a moving banner**, **a varying portrait**, a seven-segment digit per side
(start 0-0, end_P1 1-0, end_P2 0-1); `other` = moving shapes on another background; ±2 noise. **Cases:** the reduced
size 160 × 120; **the masks leave out the banner and the portrait, the outcome mask lies inside the digits**; the
report (frames, verdicts, shares); **the three classes told apart**; **an unseen third outcome (1-1) reads `unknown`**;
an unseen portrait still reads; **60 `other` frames and a black frame never read as the screen** (search on); moved
pictures (6 px, 4 px + 3 %, −5 / +2 px + −3 %) read right with the search; side bars cut; the search kept and floored
at 10 s; one read in milliseconds; **K in a row** (an end before the start not counted; a run broken by `other`;
unknown never ends; ended stays ended; the start loaded); **a labels file naming a class with no frames → "the labels
name a class with no frames: end_P3"**; a run with no folder → a plain error; the halves split; the spec on disk (a
changed `.npz` refused); nothing written beside the frames.

**3 runs, 16 / 16 each** (`tests_x3.txt`, a work copy of the snapshot; temp dirs left: 0). **Mutations 11 / 11 caught**
(`tests_mutations.txt`: a loose "steady", the screen mask every pixel, `unknown` guessed, K ignored, an end before the
start, no search, the halves the same, a changed arrays file accepted, bars not cut, thresholds past the gap, the
outcome mask not limited to steady pixels).

## Disclosed

- **The first evaluation run was stopped by me** after 9 lines (`t88_eval_stopped_first_run.jsonl`): I suspected the
  search's median objective missed the exact alignment at 2 px; a direct check showed those frames had read right
  without a search (near the threshold) and that the search does find the alignment — no code change; the run was
  started again unchanged.
- A first synthetic-test failure was the test's own drawing (a portrait circle shaded 255 − s, whose edge blends to a
  constant 127.5 — truly steady pixels); the circle got its own shade; the tool unchanged.
- numpy is used beside Pillow (both on the hub as Debian packages, both already used by the hub's tools).
- The evaluation ran beside B103's settle (one core each, the evaluation niced).
- The evaluation scripts' file names (`t88_*`) and the hashed design carry the queue's own label for the game, as
  the queue does; no title, character name or path is in them or in their outputs (title / redact checks: 0 FAILS).

## Files

`b102_2026-11-12/`: start files, the design + amendment + hashes, `b102.diff` (applies on `8b43a266`), `t88_eval.py` +
`t88_eval_results.jsonl` + `t88_eval_stopped_first_run.jsonl`, `t88_moved_confusion.py` + its results, `tests_x3.txt`,
`tests_mutations.txt`, `scripts/` (`run_all.sh`, `mutate.py` — B101's runner, unchanged — `mutations.json`),
`sha256_before_after.txt`, redact / title checks, `manifest.sha256`. Patch note: `patches/B102_H7_END_SCREEN_LEARNER.md`.
