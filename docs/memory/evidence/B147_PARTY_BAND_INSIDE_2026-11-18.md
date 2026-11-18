---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AY) — the practice band inside the frame's inner 90 %, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Settled from the app's code: the app fits the whole 16:9 frame to its full-screen surface (a SurfaceView MATCH_PARENT, MediaCodec's default scale-to-fit, no crop, no zoom), so the cut the user saw is the TV's own overscan, which the hub cannot read. The same words; the box's top at h*5/100, as wide as the words: rows 36-85 and columns 379-899 of the 1280 × 720 frame, 3.8 % of a 4:3 title's picture (B144's covered rows 0-58 across the frame, 8.2 %); +0.22 ms CPU a frame (B144's +0.27). Tests: the practices' commands carry it, every other command equals HEAD's; the output frame at 720p and 1080p inside the inner 90 %. Nothing adopted; nothing committed
---

# B147 — the band inside the picture

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B147. The user at PP-H3d: "The practice band was there (maybe a little too
high, it was partially cut off)". The directory is `b147_2026-11-18/`: the design + `.sha256` (hashed 07:41:35Z,
before any code), `banner_cost.txt`, `b147.diff`, the runs (`tests_x3.txt`, `tests_recent.txt`, `tests_others.txt`,
`tests_mutations.txt`), `scripts/`, the checks, `manifest.sha256`. Patch: `patches/B147_PARTY_BAND_INSIDE.md`. No
picture in git (the probe's made-up frame looked at once, removed).

## Settled from the app's code (read only)

`NativeStreamActivity` places one `SurfaceView` in a full-screen `FrameLayout` (`MATCH_PARENT` both ways, black, immersive)
and `AvcLowLatencyDecoder` configures MediaCodec on that surface without `setVideoScalingMode`. MediaCodec's default
mode, SCALE_TO_FIT, scales the 1280 × 720 frame to the surface without crop, and both are 16:9. **The app shows the
whole frame: no crop, no zoom, no fill.** Its overlays are a status line (gone in play), a centred wait text and notices
at the bottom, none at the top. **So the cut can only be the TV's own overscan** (or the onn's display-area setting),
which the hub cannot read; the inner 90 % is the safe area for it.

## Built (`b147.diff`)

`companion/native_stream.py`: `PARTY_BANNER_FILTER` is now `drawtext=font=Sans:text='PRACTICE — press Start to go
back':fontcolor=white:fontsize=h*30/720:x=(w-text_w)/2:y=h*5/100+10:box=1:boxcolor=black@0.72:boxborderw=10|16|10|16`.
The words, font, size and colours are the same; the box's top is at `h*5/100`, 10 px above and below the words and
16 px to each side, centred. **Rows 36-85, columns 379-899** of the 1280 × 720 frame (521 × 50 px), all inside the
inner 90 % (rows 36-683, columns 64-1215). **3.8 % of a 4:3 title's picture** (its 960 × 720 between the pillars);
B144's band covered the picture's full width over rows 0-58, 8.2 %. **The box is as wide as the words, not the frame,**
because the words are what says "practice" and the less of the game it covers the better. At the 1080 rung it scales
(text 45 px, top at row 54). The arm, the place in the chain (after `format=nv12`, before `hwupload`) and when it is on
are B144's, unchanged. **Cost** (`banner_cost.txt`, 1800 frames, three runs): no band 7.40 s user CPU, B144's 7.89 s
(+0.27 ms a frame), **this one 7.79 s (+0.22 ms a frame)**.

## Tests (`tests/b147_party_band_inside/`, 2; B144's updated)

| test | shown |
| --- | --- |
| the commands | through the real routes (B143's `b143` scenario, mine and HEAD's, 9 starts each): **the two practices' commands carry the new filter**; the onn's own start, the real goes and every way back **equal HEAD's** at the same step |
| the output frame | a made-up 4:3 picture through the practice command's own `-vf` (`hwupload` swapped for an RGB frame out) against the same chain without the band, at 1280 × 720 and 1920 × 1080: **every changed pixel inside the inner 90 %** (nothing above `h*5/100`, nothing within `w*5/100` of a side); above it and at the sides equal within 2 grey levels (B144's bound); **rows 36-85 at 720p**; the box narrower than half the frame; the text's white pixels inside it |
| B144's frame test | updated: the band's rows 36-90, above and below equal; the made-up window grabbed by its id still its own picture |

The flags absent → today: B114's flag test in `tests_others.txt`.
