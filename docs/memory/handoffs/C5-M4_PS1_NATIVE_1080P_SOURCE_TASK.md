---
memory_schema: 1
as_of: 2026-10-01
status: TASK HANDOFF — C5-M4 Part 1 (source side, no nights, no Opal change): the user's reading of 2026-10-01 — 1080p is a Phase C deliverable through the adaptive ladder, not only a characterization, and the source should render natively at 1080p (RetroArch window 1920×1080, Beetle PSX HW internal resolution raised) instead of the onn upscaling a 720p stream. Inventory the source-side options; measure the host at each internal resolution with and without the stream; make a lossless 1080p reference at the chosen scale and compare offline: today's 720p / 720p-of-the-1080p-source / 1080p-of-the-1080p-source, each as shown on the 1080p TV, with the frame-size data the link would have to carry. Propose, adopt nothing. PS1 first (the user: it maps onto PS2+ later)
---

# C5-M4 Part 1 — the PS1 source at native 1080p

**Why.** C5-M1 wrote it and then nobody acted on it: *"the 879×720 source
is upscaled 1.5× (fast_bilinear), so a 1080p stream on this source adds
no detail … a source with real 1080p detail needs a larger RetroArch
window."* The user's reading (2026-10-01): Phase C's adaptive machinery
was built so that a higher rung becomes usable; 1080p has had one parity
test (C5-M1) and two unjudged nights (C5-M2), never a rung on the ladder,
and never a source with 1080p detail in it. **PS1 first**: Beetle PSX HW's
internal resolution scale is real added geometry, and the same approach
carries to PS2-class emulation later. The 2D systems come after.

**What this part is and is not.** Source side and offline only: no
screening night, no Opal change, nothing adopted, the adopted launch
config untouched at the end. The 1080p rung on the ladder is Part 2, after
the user's link change (40 MHz) and the LINK-L1 re-run. Host resource
figures are measured and reported; **no minimum-hardware claim** (Phase
E's).

Read first: `evidence/C5_M1_1080P60_PROFILE_2026-09-28.md` (§1a, the
"measurements that could change it"), `C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`
§1 (the offline method, `c5_m3_quality.py`, `ra_cmd.py`),
`C5_M2_1080P60_FOLLOWUP_2026-09-29.md` (the arms and the cap-binding
figures), `PS1_MULTITAP_CORE_OPTIONS_AUDIT_2026-09-10.md` (where the core
options live and how they were audited), `H2_HEADLESS_CUTOVER_2026-09-22.md`
and `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` (the 1920×1080 headless
display), `TOOLS.md` (how the games plugin launches RetroArch, the sys
samplers, x11grab), `companion/plugins/games.py` and the launch path,
`CURRENT.md`. Note: **live adaptive bitrate is now the default** (D1); on
a clean link it is silent, and any session here records its decision log
as every session does.

## 1. Inventory — report, change nothing yet

- **How the game is launched**: the exact RetroArch command and config
  files the companion uses for the PS1 attract title (Tekken 3, Beetle
  PSX HW): `retroarch.cfg` keys for video (`video_fullscreen`,
  `video_windowed_fullscreen`, `video_fullscreen_x/y`, `video_scale`,
  `video_scale_integer`, `aspect_ratio_index`, `video_driver`, shaders,
  `video_vsync`, `video_frame_delay`, run-ahead), and the Beetle PSX HW
  core options file: `beetle_psx_hw_renderer`,
  `beetle_psx_hw_internal_resolution`, `beetle_psx_hw_dither_mode`,
  `beetle_psx_hw_filter`, PGXP keys, `beetle_psx_hw_widescreen_hack`,
  `beetle_psx_hw_frame_duping`, and any others that bear on the picture
  or the frame rate. Current values, with where each is set (global cfg,
  core-specific, per-game override) and what the multitap audit already
  pinned.
- **Why the window is 879×720**: which key makes it so, and what makes it
  1920×1080 (fullscreen on the headless display, or windowed at that
  size), keeping the 4:3 game pillarboxed inside — the companion's
  scale/pad then sees a 1920×1080 source.
- **The capture path at 1080p**: x11grab of a 1920×1080 window at 60 —
  what changes in the companion's ffmpeg argv (the input size, the
  scale/pad for the 720p profile becomes a downscale; for a 1080p profile
  a no-op), and whether anything in `native_stream.py` assumes the
  source is ≤ the profile size.
- The renderer: Vulkan or OpenGL as configured, and what the host's GPU
  (the EliteDesk's integrated graphics, per H2's inventory) offers.

## 2. The host at each internal resolution (`c5_m4_host_table.*`)

Pre-register the bar before measuring: **a scale HOLDS 60 if RetroArch
reports no dropped frames over 5 minutes of the attract loop and the
companion's capture delivers 60 fps to the encoder with no `codec_ms`
growth** (the C2 telemetry) — the bar is on the frame rate, not on the
CPU/GPU figures, which are reported.

For the attract title, window at 1920×1080, internal resolution **1×
(today's picture), 2×, 3×, 4×** (and 8× only if 4× holds with ≥ 40 %
headroom), each 5 minutes:

- (a) **without a stream**: RetroArch's own frame statistics (the command
  port; frame time, dropped frames), host CPU per core, GPU busy,
  temperatures (the C5 `sys` sampler and T2's host rows);
- (b) **with the adopted 7000 stream** (the 1080p source downscaled to
  1280×720 on the host): the same plus the encoder's share of a core,
  capture fps, `codec_ms`, and the client's fps / spikes / stale over the
  5 minutes (reported; this is the "quick win" path — the better source
  through today's profile and today's link);
- (c) **with the c3 arm** (`native_game_1080p60_c3_80pct_cap90`, behind
  the selector for this hold only): encoder share, capture fps,
  `codec_ms`, the per-second largest-frame p50/p90/max, cap hits s/min,
  frames ≥ 80 packets/min, and the client rows — reported, not judged
  (one 5-minute hold is not a screening night).

Teardown after each: the selector unset and absent, stream 7000, no game.
Pick **the highest scale that HOLDS 60 in (b)** as the candidate; say
why.

## 3. Offline quality on the real 1080p source (`offline/`)

C5-M3's method, at the candidate scale. The reference: 60 s x11grab of
the 1920×1080 window, 4:2:0, lossless (`libx264 -qp 0`; ~400 MB, kept in
`runtime/c5_m4/`, sha256 in the evidence). Same attract segment as C5-M3
if it can be reproduced from the command port; say whether it was.

**The encodes**, each through the companion's `h264_vaapi` argv:

| arm | source | encode | shown as |
| --- | --- | --- | --- |
| T (today) | the 879×720 window at 1× (C5-M3's reference, re-used) | 720p / 7000 / cap 90 KB / GOP 15 | bilinear ×1.5 to 1920×1080 |
| S720 (the quick win) | the 1080p source | 720p / 7000 / cap 90 KB / GOP 15 (the host downscale) | bilinear ×1.5 to 1920×1080 |
| S1080-c3 | the 1080p source | 1080p / 12,600 / cap 90 KB / GOP 15 | as is |
| S1080-par | the 1080p source | 1080p / 15,750 / cap 90 KB / GOP 15 | as is |
| S1080-g30 | the 1080p source | 1080p / 12,600 / cap 90 KB / **GOP 30** | as is |
| S1080-cap | the 1080p source | 1080p / 12,600 / **cap 120 KB** / GOP 15 | as is |

All compared against the **1080p reference as shown** (T and S720 can only
be compared after their upscale; say so). Per arm: SSIM whole-frame and
content-only (the 4:3 picture, not the pillars), p5 SSIM, PSNR, the IDR
pulse and 4 Hz share as in C5-M3; **and the frame-size data the link
would carry**: IDR sizes p50/p90/max, per-second largest frame, frames ≥
80 packets per minute, cap hits s/min, and the mean and peak bitrate
actually produced. T vs S720 is the value of the source change alone;
S720 vs the S1080 arms is the value of the rung; the frame-size columns
are what the rung costs on the air.

Also report, honestly: how much of S1080's gain is visible at the TV's
viewing size is a picture question — the user's, on the TV, later, not a
gate here.

## 4. The proposal — nothing adopted

`evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-0X.md`:

- the inventory; the host table with the HOLDS 60 verdicts; the offline
  table; the frame-size table;
- **a proposed source config** for PS1 (the window size, the internal
  resolution, any renderer/dither/filter setting the measurements
  justify), as a diff against the current files, **written to the
  evidence dir and not applied**; how it would be applied per-core (so
  the 2D systems are untouched) and reverted;
- **what the 1080p rung would need**, from the frame-size data: the
  bitrate, the cap, the GOP, the FEC parity load at that packet rate, the
  rung's wire rate against the calibrated capacities from the `nft`
  nights, and the ladder position (above 7000; entered only after a long
  clean window; left on the first `capacity_mild` bar) — as a design for
  Part 2, with the actuator change it needs (a resolution change on the
  encoder restart; the client takes its size from the SPS, as C5-M1
  showed) listed, not built;
- the host cost of the candidate scale in plain figures, with the Phase E
  caveat.

`docs/ROADMAP.md` C5: add the user's reading of 2026-10-01 as the
section's current status — 1080p60 is a Phase C deliverable through the
adaptive ladder; C5-M1/M2 characterized the stream on a 720p-detail
source and an unsettled link; C5-M4 is the source-side step; the rung is
Part 2 after the link work — and the C7 row's 1080p entry reworded to
match. `investigations/ACTIVE.md`: a C5-M4 item. `CURRENT.md` last —
Active Objective: Phase C continues, C5 reopened by the user's reading;
Next Action 1: the user's commit; 2: the user's picture decision on the
proposed source config (hand steps, TV only, nothing perceptual as a
gate) and the 40 MHz change on the Opal; 3: the LINK-L1 re-run and Part 2
on the user's word.

At the end: the adopted launch config and core options byte-identical to
the start (hash them first), no game, stream 7000, selector absent, live
default intact, the APK `de072762…835e` confirmed. The clips outside git.
`check_memory_health.py` healthy; the redactor `--check` on every text
file written; `git status --short` and `git diff --stat` to
`logs/c5_m4_git_status.txt`. No addresses, MACs, SSIDs, ADB endpoints,
serials or credentials anywhere; no `nft`, no real `sudo`; the Opal
read-only. Nothing adopted. Nothing committed.
