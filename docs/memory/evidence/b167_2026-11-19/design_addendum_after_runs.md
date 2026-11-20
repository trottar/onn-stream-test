# B167 — addendum after the real runs (written and hashed before the label change; two changes before it disclosed)

The design (hashed 23:22:29Z) made the picture source start. The real runs then showed three more things.

## Made after the design, before this addendum (disclosed: no hash before them)

1. **The screenshot read whole** (run 2: `OSError`, then `SyntaxError` — PIL on a PNG still being written; the hub's
   4x render scale makes the PNG large). `_read_shot`: the file's size the same twice 20 ms apart and the picture
   loads, read again for up to 1.5 s, else the frame skipped (H7-V1 read again after 0.1 s). An unknown failure's
   trace kept beside RetroArch's log, off the repo.
2. **For a title already added, the begin the mini game starts from** (run 3: start and end_P2 not separable). T88's
   kept `begin.state` is the rules folder's **plain** begin (from before its setup; sha256 equal), not the setup's begin
   the party mini game loads. rehearse now takes the rules folder's own begin (`<game>.<setup>.state` or
   `<game>.state`, the listing's), read only; a kept begin that differs is listed unused. Run 4: separable, 0 unknown.

## This addendum: learn's labels anchored on the screen that stays (before the code)

Run 5's pictures (copied off the repo for study; no title started for it): **T88's kept `end_p1` was saved a moment
before its end screen settled** — the real rules read its first ~1-2 s as `other`, then `end_P1` to the end. learn's
labels measure "moved" (B140's 20 % of 64 x 48 cells by more than 16 grey levels) **against each run's first frame**,
so they labelled that one transitional frame `end_P1` and ignored the 19 frames of the real end screen. A new title's
ending saved a beat early would be learnt from the wrong screen — and could pass.

**The rule:** for a begin or an ending, the frame most of the run stays near (the most frames within the same measure
of it; the earliest on a tie) is the run's screen; frames near it take the run's class, the rest `ignore`. A still run
labels as before; an ending with a lead-in or a move-on labels the screen that stays. `other` runs unchanged. In
`_labels` only; learn's bars and the learner unchanged.

## What the runs show of learn itself (no code)

With the labels right, T88's end_P1 and end_P2 (its select screen with a per-side win tally) are **not separable from
one still save each**: every run is one source to the learner, so its outcome mask is where start and the endings
differ, and the tally's few pixels are a small part of it (margin 0.0169; the bar 0.0796, from specs learnt on three
sittings with different matches). The kept `end_p1_b` / `end_p2_b` are not end screens (the real rules read `other` on
every frame). **rehearse T88 cannot meet learn's bars from T88's kept saves**; no bar is loosened and the learner is
not changed. What it would take is said in the record (each ending saved in two different matches).

## Tests added for it

A made-up ending whose first frames are another screen: labelled by the screen that stays (the old rule's first-frame
label caught by a test). B157's made-up titles label as before.
