---
memory_schema: 1
as_of: 2026-09-30
baseline_commit: f01c3b2
status: C5-M3 DONE — three low rungs screened for Phase G, behind the selector, never the default, never on the live ladder (golden unset byte-identical; 14/14 selector tests; no client change — 540p decoded at 960x540 on the onn and composited full-screen). Offline quality (60 s lossless reference, same source and argv), content-only SSIM: 7000 0.9939, 6000 0.9929, 5500 0.9923, 5000 0.9918, 4000 0.9903, 3000 0.9879, 540p/3500 0.9871 (bilinear back to 720p); no 4 Hz IDR pulse at any rung (< 1.2 % of the SSIM variance). The seven-hold night (02:09-04:38Z) was INCONCLUSIVE (link): 3 of 4 adopted B holds missed loss. The one re-run (05:18-07:47Z; 1 of 4 B missed) decided it: 720p/4000 PASSES TRANSPORT (loss 2.2/min, gap 130 ms; it also met every row in the first night); 720p/3000 does NOT (loss 39.9/min, gap 279); 540p/3500 does NOT (loss 10.9/min, one row, narrowly; it met every row in the first night). Measured on the wire: 5.02 / 3.85 / 4.42 Mbit/s against 8.60 at 7000. Data for Phase G; the remote floor is the user's later choice. Selector unset and absent, adopted profile and APK confirmed, stream 7000, no game, banner cleared; nothing adopted; nothing committed
---

# C5-M3 — the low rungs, screened for later

Task: `handoffs/C5-M3_LOW_RUNG_SCREENING_TASK.md` (authorized by the user
2026-09-28, "yes fold in the low-rung screening"). It ran on the N2 prompt
after C5-M2.

- Evidence: `c5_m3_2026-09-29/` (manifest).
- Patch: `patches/C5-M3_LOW_RUNG_PROFILES.md`.
- Pre-registration: `c5_m3_preregistration.txt`, sha256 `4617fd42…`,
  written before the night.

## The profiles

`companion/native_stream_profiles.py`, selectable only by
`PRIVYHUB_NATIVE_PROFILE_ID`. Each has GOP 15, B 0, FEC 8, cushion 12/17,
redundancy 2/4, and cap 90,000 B.

| id | size | kbps |
| --- | --- | --- |
| `native_game_720p60_4000` | 1280×720 | 4000 |
| `native_game_720p60_3000` | 1280×720 | 3000 |
| `native_game_540p60_3500` | 960×540 | 3500 |

- **Golden:** unset, byte-identical before and after
  (`golden_before.txt`, `golden_after_unset.txt`; the per-id argvs are in
  `golden_after_<id>.txt`).
- **Tests:** 14/14, including "none is on the live ladder". The ladder,
  the controller, the actuator's validated list and the adopted profile
  are untouched.
- **The client needed no change**, as expected.
  - `AvcLowLatencyDecoder` is configured with 1280×720 as a hint; the
    stream's own SPS/PPS set the decoded size.
  - `SurfaceView` is MATCH_PARENT on the 1920×1080 display, so the
    compositor scales the buffer.
  - **Confirmed:** during every S5 hold SurfaceFlinger showed the stream
    surface's buffers at **w/h 960x540** (the 1920x1080 lines are the
    window layer). The B holds showed 1280x720.

## 1. Offline objective quality (`offline/`, `c5_m3_quality.py`)

**Method.**

- **The source.** The attract title was launched through the companion
  without a stream and unpaused through RetroArch's command port
  (`ra_cmd.py`; GET_STATUS PLAYING, the window 879×720).
- **The reference.** 60 s of x11grab of the window, through the
  companion's own scale/pad (1280×720, fast_bilinear, pad), in 4:2:0 and
  lossless (`libx264 -qp 0`).
  - 3,600 frames in 60.0 s, speed 1×, no dup or drop.
  - 120 MB, so it is kept outside git in `runtime/c5_m3/`. Its sha256 is
    in `offline/clips_sha256.txt`.
  - The game was re-paused (GET_STATUS PAUSED) and stopped.
- **The encodes.** Each rung through the companion's `h264_vaapi` argv:
  `-profile:v high -b:v K -maxrate K -bufsize K -max_frame_size 90000
  -g 15 -bf 0`.
  - 540p: the reference scaled to 960×540 with the companion's scaler
    flags (fast_bilinear).
  - After decoding, **scaled back to 1280×720 with a bilinear scaler** as
    a stand-in for the TV's upscale. The onn's own scaler is not
    measurable from here.
- **The comparison.** ffmpeg `ssim` and `psnr` per frame.
  - The whole frame includes the pad bars (~31 % of the width is black),
    which flatter the whole-frame figures.
  - So a **content-only SSIM** (the centre 880×720) is also given, and it
    is the one to read.

| rung | enc kbps | SSIM (frame) | SSIM (content) | p5 SSIM (content) | PSNR dB | IDR pulse | 4 Hz bin | GOP fold | IDR B p50 / p90 / max | frames / IDRs ≥ 95 % cap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 720p 7000 | 7007 | 0.99578 | **0.99389** | 0.98024 | 60.7 | 0.00032 | 1.06 % | 1.14 % | 39,269 / 49,584 / 67,781 | 1 / 0 |
| 720p 6000 | 6012 | 0.99513 | **0.99294** | 0.97726 | 60.1 | 0.00052 | 0.73 % | 0.83 % | 35,971 / 46,756 / 73,515 | 1 / 0 |
| 720p 5500 | 5511 | 0.99469 | **0.99231** | 0.97572 | 59.8 | 0.00053 | 0.70 % | 0.81 % | 33,972 / 43,496 / 73,515 | 1 / 0 |
| 720p 5000 | 5007 | 0.99437 | **0.99184** | 0.97533 | 59.4 | 0.00091 | 0.10 % | 0.20 % | 30,214 / 39,900 / 80,844 | 0 / 0 |
| 720p 4000 | 4008 | 0.99327 | **0.99026** | 0.97075 | 58.6 | 0.00100 | 0.09 % | 0.19 % | 24,284 / 34,196 / 60,950 | 0 / 0 |
| 720p 3000 | 3008 | 0.99161 | **0.98787** | 0.96427 | 57.6 | 0.00123 | 0.07 % | 0.16 % | 19,223 / 26,641 / 45,287 | 0 / 0 |
| 540p 3500 | 3506 | 0.99095 | **0.98708** | 0.96545 | 53.0 | 0.00091 | 0.05 % | 0.11 % | 21,439 / 28,477 / 55,604 | 0 / 0 |

**The IDR pulse** is the mean |SSIM(IDR) − SSIM(frame before)| over
the 239 GOP boundaries. The 4 Hz bin and the GOP fold are the 4 Hz share
of the SSIM series' variance: the fundamental alone, and every harmonic
(the variance of the 15 GOP-phase means).

**How to read it** (anchors, not a gate):

- **Content SSIM falls smoothly with the bitrate.** Per 1000 kbps it
  falls ~0.0010 between 7000 and 5000, 0.0016 from 5000 to 4000, and
  0.0024 from 4000 to 3000. The loss per kbit is accelerating below 4000.
- **540p at 3500 lands just below 720p at 3000** on content SSIM (0.9871
  against 0.9879), with a similar p5. Its PSNR is lower (53.0 against
  57.6 dB), because the upscale softens edges that PSNR counts heavily.
  **540p buys nothing over 720p at these rates on this content** (an
  upscaled 879×720 PS1 picture).
- **No rung pulses at 4 Hz**: under 1.2 % of the SSIM variance at 7000,
  and under 0.2 % at 5000 and below. With every rung at GOP 15 the
  question has a numeric answer. The pulse is largest at 7000, where
  frame-to-frame quality is highest and each IDR stands out slightly.
- **IDRs:** p90 is 26-50 KB, and no IDR reached 95 % of the cap. The cap
  does not bind the IDRs on the offline content. In the live holds the
  per-second largest frame p90 is 83-86 KB at every rung; that is the
  motion-heavy attract segments.
- The user rated 5000-6000 at 7-9. **4000 sits 0.0016 below 5000 on
  content SSIM**, a somewhat larger step than 5000 is below 6000
  (0.0011).

## 2. The night (`runs/`, `c5_m3_night.log`, `c5_m3_night_score.txt`)

**The first night:** seven 20-min holds B1 L4 B2 L3 B3 S5 B4, 2026-09-30
02:09-04:38Z, after ≥ 40 min cold. **INCONCLUSIVE (link).**

| hold | profile | spikes/min | fps | stale/min | loss/min | max gap | frame max p50 / p90 / max | cap hits s/min | Opal retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | adopted 7000 | 23.9 | 59.93 | 0.64 | 7.32 | 148 | 47,505 / 86,311 / 89,498 | 9.6 | 77k |
| L4 | 720p 4000 | 37.1 | 59.94 | 0.70 | 7.00 | 165 | 32,543 / 85,114 / 89,536 | 5.4 | 54k |
| B2 | adopted | 24.3 | 59.90 | 0.69 | **15.49** | 180 | 48,574 / 86,311 / 89,942 | 9.8 | 81k |
| L3 | 720p 3000 | 36.8 | 59.92 | 0.89 | **11.08** | 167 | 25,180 / 83,244 / 88,884 | 3.3 | 32k |
| B3 | adopted | 26.5 | 59.93 | 0.39 | **25.61** | **306** | 47,710 / 86,311 / 89,498 | 9.6 | 66k |
| S5 | 540p 3500 | 9.0 | 59.92 | 0.94 | 5.44 | 98 | 27,919 / 85,324 / 89,001 | 5.9 | 40k |
| B4 | adopted | 29.2 | 59.89 | 0.94 | **17.63** | **471** | 48,413 / 86,311 / 90,027 | 9.8 | 73k |

B2, B3 and B4 missed, so the pre-registered one re-run followed.

**The re-run:** 05:18-07:47Z (`runs_rerun/`, `c5_m3_night_rerun.log`,
`c5_m3_night_rerun_score.txt`). **Conclusive: only B3 missed.**

| hold | profile | spikes/min | fps | stale/min | loss/min | max gap | frame max p50 / p90 / max | cap hits s/min | Opal retries |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | adopted | 23.0 | 59.95 | 0.94 | 3.16 | 91 | 48,205 / 86,311 / 89,885 | 9.4 | 66k |
| **L4** | **720p 4000** | 27.8 | 59.96 | 0.84 | 2.24 | 130 | 32,651 / 85,114 / 89,071 | 5.2 | 45k |
| B2 | adopted | 22.6 | 59.94 | 0.40 | 5.84 | 85 | 47,699 / 86,311 / 89,876 | 9.6 | 68k |
| L3 | 720p 3000 | 84.8 | 59.63 | 2.29 | **39.86** | **279** | 25,207 / 83,244 / 88,884 | 3.0 | 101k |
| B3 | adopted | 22.5 | 59.89 | 0.84 | **32.68** | **251** | 47,928 / 86,311 / 89,854 | 9.7 | 66k |
| S5 | 540p 3500 | 9.0 | 59.90 | 0.79 | **10.89** | 169 | 27,898 / 85,315 / 88,914 | 5.3 | 36k |
| B4 | adopted | 22.6 | 59.94 | 0.55 | 4.12 | 101 | 47,861 / 86,311 / 89,876 | 9.8 | 59k |

## Outcome per arm (the re-run, as pre-registered)

| arm | transport | the first night (inconclusive, reported) |
| --- | --- | --- |
| **720p / 4000** | **PASSES** — every row; loss 2.24/min, gap 130 ms | every row met (7.00, 165 ms) |
| 720p / 3000 | **does not pass** — loss 39.86/min, gap 279 ms | loss 11.08 (one row) |
| 540p / 3500 | **does not pass** — loss 10.89/min (one row, narrowly) | every row met (5.44, 98 ms) |

**Reported beside it:**

- **4000 met every row on both nights.** It is the only low rung that
  did.
- **3000 was not safer than 7000.** Its loss (11-40/min) was at or
  above the B holds'.
  - At 3000 the largest frame per second still reaches 83-89 KB (the
    motion segments), so the per-frame burst is not smaller.
  - The re-run's L3 hold ran into the busiest air of that run (101k
    retries).
  - **A lower bitrate at the same frame cap does not buy transport
    robustness on this hop.** It buys headroom on a thin uplink. That is
    Phase G's question, not the home link's.
- **540p had the fewest spikes** (9/min on both nights, against 22-37
  elsewhere). The decoder does less work, and the per-second largest
  frame is lower (p50 28 KB). Its loss was 5.4 on night 1 and 10.9 on
  the re-run: one row, on each side of the line.
- **Measured on the wire** (`c5_m3_onair.txt`: client-received video plus
  FEC parity plus ~40 B/packet headers). L1's rung-load table estimated
  7000 at 8.66 Mbit/s and 5000 at 6.20.

| rung | video | parity | wire | packets/s |
| --- | --- | --- | --- | --- |
| 7000 | 7.09 | 1.21 | **8.60 Mbit/s** | 954 |
| 4000 | 4.06 | 0.77 | **5.02** | 590 |
| 540p 3500 | 3.55 | 0.70 | **4.42** | 532 |
| 3000 | 3.04 | 0.65 | **3.84** | 473 |

- **Host:** CPU 9-11 %, GPU 8.6-10.7 %, encoder 25-31 % of a core; the
  host 52-55 °C, the onn 59-67 °C.

## What it means for Phase G (data; the remote floor is the user's later choice)

- **On a link that carries ~5 Mbit/s**, 720p at 4000 passed transport
  twice here. Its content SSIM is 0.0016 below 5000, and it has no IDR
  pulse.
- **Below that**, 720p at 3000 and 540p at 3500 cost about the same in
  content SSIM (0.988 / 0.987), and neither passed transport on the
  re-run.
  - 540p saves decoder work (the fewest spikes), not picture.
  - On this content 540p is not the better way down.
- **None of these joins the live ladder.** A remote ladder would be built
  and validated in Phase G on the remote path, with these numbers as its
  starting data.

## Teardown (both runs)

- Selector unset: manager 0, and 0 in the new MainPID's environ.
- The adopted profile at 7000; the **adopted APK `f31b1c18…8ae7`
  confirmed** (no arm APK).
- No game; samplers stopped.
- The stale launcher banner was cleared by the teardown itself (count 0
  after force-stop and relaunch), both runs.

## Files (`c5_m3_2026-09-29/`)

- `c5_m3_preregistration.txt`.
- The golden files, `c5_m3_golden.py`.
- `c5_m3_quality.py`, `ra_cmd.py`, the `ra_status_*` files.
- `offline/`: `quality_table.txt`, `quality.json` (the per-frame SSIM
  series), `quality_content_crop.txt`, `clips_sha256.txt`, the capture
  log tail.
- The harness (C5-M2's, copied): `c5_m2_night.sh`, `c5_m2_run.sh`,
  `c5_m2_score.py`, `t2_sample.py`.
- `runs/` and `runs_rerun/` (as C5-M2's).
- The two score files, the link files and `c5_m3_onair.txt`.
- `sha256_manifest.txt`.

The clips themselves are in `runtime/c5_m3/`, outside git.
