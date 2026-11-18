# B147 — the band inside the picture: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B147. Baseline `baseline_head.txt`. Behind `PRIVYHUB_PARTY=1` (and
`PRIVYHUB_H7=1`): only a practice's planned switch arms the band (B144's arm, unchanged). Absent = today.

## Settled from the app's code (read only)

`NativeStreamActivity` puts one `SurfaceView` in a full-screen `FrameLayout` (`MATCH_PARENT` both ways, black
background, immersive system UI) and `AvcLowLatencyDecoder` configures MediaCodec with that surface and never calls
`setVideoScalingMode`: MediaCodec's default, SCALE_TO_FIT, scales the decoded 1280 × 720 frame to the surface without
crop. The frame is 16:9 and so is the screen: **the app fits the whole frame — no crop, no zoom, no fill.** The overlays
it draws over the video are a status line (gone in play), a centred wait text, and notices at the bottom — none at the
top. **The cut the user saw can only be the TV's own overscan** (or the onn's display-area setting), which the hub
cannot read.

## The design

- The same words: `PRACTICE — press Start to go back`; the same font (`font=Sans`), size (`fontsize=h*30/720`), colours
  (white on black at 72 %).
- **Every pixel inside the frame's inner 90 %:** the text at `y=h*5/100+10` with its box's border 10 px above and below
  and 16 px left and right (`boxborderw=10|16|10|16`), so the box's top is exactly `h*5/100`; centred (`x=(w-text_w)/2`).
- **The box as wide as the words, not the frame:** the less of the game it covers the better, and the words are what
  says "practice". Measured on a made-up 960 × 720 source in the 1280 × 720 frame: **rows 36-85, columns 379-899**
  (521 × 50 px) — **3.8 % of a 4:3 title's picture** (B144's band: rows 0-58 across the frame, the picture's whole
  960-px width × 59 rows, 8.2 %). Inside the inner 90 % (rows 36-683, columns 64-1215). At the 1080 rung it scales
  with the frame (text 45 px, top at row 54).
- `PARTY_BANNER_FILTER` replaced; nothing else changes: the arm, where it sits in the chain (after `format=nv12`,
  before `hwupload`), when it is on.
- **Cost** (`banner_cost.txt`, 1800 frames, three runs): no band 7.40 s user CPU, B144's 7.89 s (+0.27 ms a frame),
  this one 7.79 s (+0.22 ms a frame).

## Tests (`tests/b147_party_band_inside/`)

- Through the real routes (B143's `b143` scenario of B114's harness): the practices' commands carry the new filter;
  the real goes', the ways back' and the onn's own start's commands equal HEAD's at the same step.
- The output frame on a made-up source (the practice command's own `-vf`, `hwupload` swapped for an RGB frame out,
  against the same chain without the band): the rows above `h*5/100` (0-35) and the columns within `w*5/100` of either
  side equal within B144's bound (2 grey levels); the band's rows differ; every changed pixel inside the inner 90 %;
  the text's white pixels inside the box.
- B144's tests updated to the new band; the flags absent → today (B114's flag test).
