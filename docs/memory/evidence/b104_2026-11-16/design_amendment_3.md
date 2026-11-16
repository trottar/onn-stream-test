# B104 — design amendment 3 (written after the first run on the real pictures; disclosed)

**What the first run showed** (`run1_before_amendment3_a1/a2/a3.jsonl`, kept): the measure itself held — learnt from
H7-V1 alone, 495 / 507 labelled live pictures right, **no fight read as the screen in any arrangement** — but the
LEARNING failed when live pictures were in the learning set: learnt from everything (the spec A would use) no class
was separable (outcome mask 37 px); learnt from the live run alone two of three classes not separable; and in
arrangement 2a **21 of match 2's start pictures read as `end_P2`** (a wrong class). Read-only checks
(`amendment3_look/`, scripts only) found three causes, none in the measure:

1. **B102's absolute steadiness test drops the tally itself.** With other characters on screen the tally's ranks
   shift by ~0.04 (part of the screen mask's content changes, so the picture's tone reference moves a little) and
   its strokes' edges by up to ~0.1; within-class std < 0.05 then fails on the tally (live start: median 0.045).
   Frame to frame the live tally is steady (consecutive change ~0.001): the variation is between stretches.
2. **A handful of labelled pictures at the edges of ranges** (the seconds where the game is launched or ended — the
   kind H7-V1's labels mark `ignore` for RetroArch's own notice) read nearer another class than their own label. B102
   puts each threshold halfway past the WORST own frame, so 3-5 such pictures per class erase every gap.
3. **A confound in arrangement 2 by construction:** a pair of classes that never appear in the same source (2a: the
   start from match 1, `end_P2` only from H7-V1's other characters) differ by the characters as much as by the tally;
   the learner took the portraits for "the outcome".

**The changes (learning only; the measure, the area rule, the reader and the screen's threshold unchanged):**

- **The outcome mask:** a pixel is in it when, **within one source** (one runs folder + labels file), the means of
  two classes that both have frames there are more than `DIFFER_R` (0.25) apart, **and** that difference is more than
  `SEP` = 3 × the pixel's widest within-class spread, the spread being the 10th-90th percentile range of its ranks
  over all that class's frames (all sources) — steadiness judged against the separation, and a minority stretch does
  not count. A pair of classes never seen together in a source cannot make the mask.
- **A labelled frame that is not nearest its own class's reference does not set its class's threshold** (it is
  counted in the learn report as `unlike_label` per class, and is read `unknown` or `other` like any other picture);
  the foreign side stays strict (the least distance of any frame of another class). The margin needed: half the
  smallest margin among frames nearest their own class (as B102).
- **A class is separable only when its gap is at least `MIN_GAP` = 0.05** (rank-distance units; the real gaps are
  ~0.2): a positive gap smaller than that is the sources' tone noise, not a difference — "not separable", never named.
- The screen's threshold: B102's rule unchanged (halfway past the worst own screen frame).

A prototype of exactly these rules on the reduced frames (`amendment3_look/proto.py`, its last form) gave: 1a, 1b and
3 every class separable and no picture read as a wrong class; 2a and 2b no wrong class (the classes the data cannot
support are `unknown`, or read as the start where the end differs from the start only in the tally half that source
never saw — the exact counts are in the record), every arrangement `other` read as the screen 0. The full evaluation
is run once, after this amendment, on the tool's code.
