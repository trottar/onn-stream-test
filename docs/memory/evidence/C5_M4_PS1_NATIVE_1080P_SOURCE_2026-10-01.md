---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: cddacaf
status: C5-M4 Part 1 DONE — the PS1 source at native 1080p, source side and offline only; nothing adopted. Inventory: the window is 879x720 because RetroArch's default video_scale 3 (240 lines x 3) at the core's 1.219 aspect; fullscreen (borderless, the 1920x1080 headless display) makes it 1920x1080 with the 4:3 picture pillarboxed (1316x1008); the companion's argv is unchanged and its scale/pad becomes a downscale (720p) or an identity (1080p). Beetle PSX HW (OpenGL, radeonsi/Renoir) offers 1x/2x/4x/8x — 3x is NOT offered (RetroArch rewrote it to 1x). Host table (pre-registered, sha256 4193ef8a…): 1x, 2x, 4x HOLD 60 in (a) no stream, (b) the adopted 7000 stream and (c) the c3 1080p arm; 8x (run because 4x had >= 40 % headroom) MISSES R1 by one 256-frame interval in (b) (4,279.0 ms vs 4,278.7) and (c). R3 (codec_ms) NOT EVALUABLE as worded — the C2 telemetry carries no codec_ms; substitutes flat. CANDIDATE 4x: GPU busy 21 % (b) vs 15 % at 1x, +1 W; RetroArch ~33 % of a core either way; the 1080 window raises the encoder to 36 % of a core at 720p, 74 % at 1080p. Offline (the 3D demo segment, 4x lossless reference, deterministic replay, repeat control bit-identical): content SSIM T 0.838, S720 0.873, S1080 c3 0.902 / parity 0.912 / GOP30 0.908 / cap120 0.905; the 1080p arms pulse at the IDR rate under the 90 KB cap (0.032 vs 0.004), the 120 KB cap halves it but brings back 28 frames/min of >= 80 packets. C5-M3's FMV segment reproduced (lag 338 frames, MAD 0.16): T 0.986, S720 0.989, S1080 0.995-0.996. Proposal written, not applied: a Beetle PSX HW core override (fullscreen) + internal_resolution 4x in the base core options (six titles carry their own .opt copies). The 1080p rung's needs for Part 2 listed, not built. Launch config and core options byte-identical; selector absent; stream 7000; live default intact; APK de072762…835e confirmed; nothing committed
---

# C5-M4 Part 1 — the PS1 source at native 1080p

Task: `handoffs/C5-M4_PS1_NATIVE_1080P_SOURCE_TASK.md`, run unattended under
`handoffs/QUEUE_2026-09-29B.md`'s rules, 2026-10-01 16:07-18:30Z. The user's
reading of 2026-10-01: 1080p is a Phase C deliverable through the adaptive
ladder, and the source should render natively at 1080p. Evidence:
`c5_m4_2026-10-01/` (manifest). Pre-registration:
`c5_m4_2026-10-01/c5_m4_preregistration.txt`, sha256 `4193ef8a…`, written
16:09Z, before the first hold (16:20Z).

**Nothing is adopted.** The measurements ran on two game-specific files
for Tekken 3 only (`Tekken 3 (USA).cfg` / `.opt`, which did not exist
before), created per hold and deleted by every teardown.

## 1. Inventory

### How the attract title is launched

- `POST /plugins/games/launch?id=game_ps1_b0a5986638f61a11` →
  `EmulatorManager.launch` (`companion/games/emulator_manager.py`):
  `RetroArch-Linux-x86_64.AppImage --config data/games/retroarch/config/privyhub-session.cfg
  --device=1:1 --device=2:1 --verbose -L …/cores-linux/mednafen_psx_hw_libretro.so "games/ps1/Tekken 3 (USA).cue"`.
- `privyhub-session.cfg` is regenerated at every launch from
  `data/games/retroarch/retroarch.cfg` (the persistent PrivyHub config,
  32 lines) plus the input override (the command port is a new random
  port each launch).
- The core options come from `~/.config/retroarch/config/Beetle PSX HW/`
  because the companion's environ carries `XDG_CONFIG_HOME`. The
  AppImage's own `.home` copy is stale and unused. RetroArch's defaults
  are in force for every key `retroarch.cfg` does not set. They were read
  from the full default dump at `~/.config/retroarch/retroarch.cfg`, which
  this RetroArch never reads.
- **The launch starts from power-on**: no entry state is loaded, and
  `config_save_on_exit = "false"`. The companion launches the game
  paused; the client's PLAYING, or the command port's `PAUSE_TOGGLE`,
  unpauses it. With zero input the attract loop is deterministic from the
  unpause: the intro FMV runs ~0-100 s, the VS card ~120 s, a 3D demo
  fight ~125-170 s, and the title screen by ~240 s.

### The video keys and where each is set

| key | value in force | where |
| --- | --- | --- |
| `video_driver` | gl (the core: "OpenGL driver forced") | default |
| `video_fullscreen` / `video_windowed_fullscreen` | false / false | both set false by `retroarch.cfg` (RetroArch's default for the second is true) |
| `video_fullscreen_x/y` | 0 / 0 (desktop size) | default |
| `video_scale` | **3** | default |
| `video_scale_integer` | false | default |
| `aspect_ratio_index` | 22, core-provided (1.219) | default |
| `video_force_aspect` | true | `retroarch.cfg` |
| `video_smooth` | false (nearest) | default |
| `video_shader_enable` | true, but no preset is set | default |
| `video_vsync` | true; swap interval 1 | `retroarch.cfg` / default |
| `video_frame_delay` | 0 | default |
| `video_hard_sync` | false | default |
| `video_threaded` | false | default |
| `video_max_swapchain_images` | 3 | default |
| run-ahead / preemptive frames | off / off | default |
| `vrr_runloop_enable` | false | default |
| `video_refresh_rate` | 60.0 | default |
| `audio_sync` | true; rate control on (delta 0.005) | `retroarch.cfg` / default |
| `game_specific_options` / `auto_overrides_enable` / `global_core_options` | true / true / false | default |

The core options are `Beetle PSX HW.opt`, sha256 `7885077…`, 91 keys.
**Tekken 3 has no per-game `.opt` and no override.**

| key | value | bears on |
| --- | --- | --- |
| `beetle_psx_hw_renderer` | hardware (→ OpenGL with the gl driver) | the picture |
| `beetle_psx_hw_internal_resolution` | **1x(native)** | geometry detail |
| `beetle_psx_hw_dither_mode` | 1x(native) | the dither pattern's size at any scale |
| `beetle_psx_hw_filter` | nearest; the 2D/sprite exclusions disabled | texture smoothing |
| `beetle_psx_hw_msaa` / `super_sampling` / `mdec_yuv` | 1x / disabled / disabled | edges / FMV chroma |
| `beetle_psx_hw_depth` / `color_format` | 16bpp(native) / 24bit | banding |
| `beetle_psx_hw_pgxp_mode` and the vertex, texture and nclip keys | disabled | wobble and precision |
| `beetle_psx_hw_widescreen_hack` | disabled (16:9 if enabled) | aspect |
| `beetle_psx_hw_frame_duping` | disabled | frame rate |
| `beetle_psx_hw_core_timing_fps` | auto_toggle | 59.94 / 59.83 |
| `beetle_psx_hw_crop_overscan` | smart | geometry (320×240 → 1.219) |
| `beetle_psx_hw_aspect_ratio` | corrected | geometry (320×240 → 1.219) |
| `beetle_psx_hw_renderer_software_fb` | enabled | CPU (the software framebuffer copy) |
| `beetle_psx_hw_gpu_overclock` / `cpu_freq_scale` / `gte_overclock` | 1x / 100 % / disabled | frame rate |
| `beetle_psx_hw_line_render` / `scaled_uv_offset` | default / enabled | upscaled artefacts |
| `beetle_psx_hw_video_cable` / `hdr_*` / `src_primaries` | off / off / off | the analog and HDR chains, which this core build adds |

What the multitap audit pinned:

- Only `beetle_psx_hw_enable_multitap_port1/2`, both disabled in the
  base file.
- Six titles have their own `.opt` **copies** (Bomberman, Crash Bash,
  FIFA 98, Nicktoons Racing and Speed Punks, sha256 `acd5…`; Twisted Metal
  2, a byte copy of the base).
- The multitap path seeds a game's `.opt` from the base once
  (`_prepare_ps1_multitap_options`). So **a later change to the base file
  does not reach those six titles.**

### Why the window is 879×720, and what makes it 1920×1080

- `video_scale` 3 × 240 lines = 720. The width is 720 × the core's 1.219
  aspect ≈ 878-879.
- **Windowed at 1920×1080 cannot hold this aspect on a 1920×1080 display
  that has window decorations.** `video_fullscreen = "true"` with
  `video_windowed_fullscreen = "true"` (which `retroarch.cfg` sets false,
  so the override must set it) gives a borderless 1920×1080 window with
  no mode switch. RetroArch logged "Using windowed
  fullscreen … Using resolution 1920x1080".
- **Verified:** `xdotool` reads 1920×1080 at 0,0. x11grab of the window
  captures it (`-window_id`, as the companion does). The 4:3 picture sits
  at x 302-1617, a 1316×1008 box; the rest is black pillars.
- As a RetroArch **core override**, `config/Beetle PSX HW/Beetle PSX HW.cfg`,
  this applies to PS1 only. The measurement used the game override
  `Tekken 3 (USA).cfg`, and RetroArch logged "Game-specific overrides
  found … Appending override config".

### The capture path at 1080p

- **No change in the companion's argv.** It finds the window by pid
  (`xdotool search --pid`; the only filter is ≥ 64×64), and
  `capture_target` reads 1920×1080.
- The filter is `scale=W:H:force_original_aspect_ratio=decrease:flags=fast_bilinear,pad=W:H…`:
  - at 720p it is now a 1.5× downscale of the whole window, pillars
    included;
  - at 1080p it is an identity.
- Nothing in `native_stream.py` assumes the source is no larger than the
  profile.
- x11grab of the 1920×1080 window held 60 fps with no dup and no drop in
  every hold (R2).

### The renderer and the GPU

- **Host:** AMD Ryzen 5 PRO 4650G (6C/12T) with integrated Radeon
  (Renoir, Vega). Mesa 25.0.7: radeonsi GL 4.6, RADV Vulkan 1.4, and VAAPI
  H.264 High encode.
- **The core runs OpenGL**, because RetroArch's driver is gl. The HW
  render target is 1024² at 1x, 2048² at 2x, 4096² at 4x and 8192² at 8x.
- **Internal resolutions offered: 1x, 2x, 4x, 8x (and 16x).**
  - "3x" was tried in the smoke. RetroArch rewrote it to `1x(native)` on
    exit and the render target stayed 1024², so this core build does not
    offer 3x. The renderer scales by a power-of-two shift ("upscale
    shift").
  - So the table is 1x, 2x, 4x, plus 8x by the headroom rule.
- Vulkan (RADV) is available but was not measured; it would need
  `video_driver = vulkan`, a different driver path.

## 2. The host table (`c5_m4_host_table.py` → `c5_m4_host_table_runs{,_8x}.txt/.json`)

The holds ran 2026-10-01 16:20-17:34Z, 5 minutes each, in the order
a_1x b_1x c_1x a_2x … c_4x, then a_8x b_8x c_8x. The setup:

- the window was 1920×1080 in every hold;
- zero input;
- (b) was the adopted profile at 7000 with live adaptive bitrate by
  default;
- (c) was `native_game_1080p60_c3_80pct_cap90` behind the selector, for
  that hold only;
- the T2 sampler ran at 10 s and `c5_m4_sampler.py` at 1 s.

Every session's RetroArch log shows its render target: 1024², 2048²,
4096² and 8192² as intended (12 sessions).

**How the frame rate was read (R1).**

- RetroArch's own frame counter is the window title's
  "|| FPS: x || Frames: n". RetroArch rewrites it every 256 frames, and
  each rewrite was timestamped by `xprop -spy`.
- `fps_show` and `framecount_show` were set with `video_font_enable` and
  `menu_enable_widgets` off, so nothing is drawn on the picture. Frames
  grabbed during the smoke confirmed it.
- The resolution is about 1 ms per 256-frame interval. A missed vsync
  adds 16.7 ms.

| hold | HOLDS 60 | RA fps | longest 256-fr interval ms (nominal 4,266.7; bar 4,278.7) | enc fps / dup+drop | CPU mean % | busiest core p95 | GPU busy mean / p95 | GPU W | RetroArch % of a core (T2) | encoder % of a core (T2) | Tctl max °C |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| a_1x | **yes** | 59.998 | 4,270.0 | – | 4.6 | 37.3 | 10.3 / 11 | 15.4 | 32.4 | – | 49.1 |
| b_1x | **yes** | 59.999 | 4,271.0 | 60.00 / 0 | 10.9 | 35.6 | 14.6 / 16 | 22.1 | 31.6 | 36.3 | 57.8 |
| c_1x | **yes** | 59.999 | 4,271.0 | 60.00 / 0 | 14.3 | 34.0 | 15.3 / 16 | 23.6 | 31.7 | 73.8 | 61.6 |
| a_2x | **yes** | 59.999 | 4,271.0 | – | 4.5 | 38.2 | 11.9 / 14 | 15.6 | 32.3 | – | 52.4 |
| b_2x | **yes** | 59.999 | 4,272.0 | 60.00 / 0 | 10.1 | 34.7 | 16.2 / 18 | 22.5 | 31.6 | 36.4 | 59.2 |
| c_2x | **yes** | 59.998 | 4,272.0 | 60.00 / 0 | 14.0 | 38.2 | 16.8 / 19 | 24.2 | 33.3 | 73.5 | 63.1 |
| a_4x | **yes** | 59.999 | 4,271.0 | – | 4.6 | 36.6 | 17.7 / 22 | 16.6 | 32.6 | – | 54.1 |
| **b_4x** | **yes** | 59.999 | 4,275.0 | 60.00 / 0 | 10.5 | 35.6 | **21.4 / 26** | 23.2 | 32.8 | 36.0 | 61.0 |
| c_4x | yes* | 59.999 | 4,272.0 | 60.00 / 0 | 13.3 | 26.9 | 14.3 / 17 | 22.8 | 13.9 | 73.6 | 61.1 |
| a_8x | yes | 59.998 | 4,273.0 | – | 4.6 | 39.6 | 35.8 / 54 | 20.6 | 33.1 | – | 60.1 |
| **b_8x** | **no** | 59.999 | **4,279.0** (1 long, ≈ 1 frame) | 60.00 / 0 | 10.7 | 36.4 | 38.9 / 55 | 27.0 | 33.2 | 36.1 | 67.1 |
| c_8x | no | 59.995 | **4,284.0** (1 long) | 60.00 / 0 | 15.8 | 29.4 | 41.0 / 58 | 29.2 | 35.1 | 76.7 | 69.5 |

\* **c_4x: link-drop recovery paused the game.** It ran `desync_pause` at
17:11:25Z and `gave_up_saved` at 17:13:25Z, so only ~124 s of the hold
was PLAYING. RetroArch's counter also counts paused frames, so the row's
R1, CPU and GPU figures cover a part-paused session. Over its PLAYING
span alone, R1 reads 59.999 fps and a 4,272 ms longest interval. That
recovery is the only one in the run. (c) is reported, not judged.

**R3 is NOT EVALUABLE as pre-registered.**

- The rule named the C2 telemetry's `codec_ms`. The per-report C2
  telemetry carries no `codec_ms`: its decoder block has queue and drop
  deltas, and its latency block `receive_to_decode_ms` and
  `output_gap_ms`. `codec_ms` exists only as the decoder report's session
  max, end value and per-slow-event column.
- So HOLDS 60 is read on R1 and R2, as the scorer states. No rule was
  tightened or loosened.
- **The substitutes are flat in every (b) and (c) hold**:
  - slow-event `codec_ms` median, first full minute → last: 9 → 9 in (b),
    12-13 → 12-13 in (c);
  - `receive_to_decode_ms` median: 9-9.5 → 9 in (b), 13.5-14 → 13-14 in
    (c);
  - report max `codec_ms`: 105-130 in (b), 130-245 in (c).

**The candidate: 4x.**

- It is the highest scale that HOLDS 60 in (b). **8x does not**: b_8x's
  one 256-frame interval of 4,279.0 ms is 0.3 ms over the pre-registered
  bar, about one missed vsync, and c_8x's is 4,284 ms. By the rule, 8x is
  not a candidate.
- 8x was run because 4x in (b) had more than 40 % headroom: GPU p95 26 %,
  busiest core p95 36 %.
- At 8x the GPU p95 reaches 54-58 % and Tctl 67-70 °C. That is closer to
  the margin than 4x for no gain on a 1316×1008 picture. 8x renders
  2560×1920 and downsamples, so it is supersampling, not added on-screen
  resolution.

**The client rows (b, c), reported, not judged.** These are 5-minute holds
on a day whose LINK-L1 row is MIXED.

| hold | fps | spikes/min | stale/min | loss/min | max gap ms | Mbit/s | per-s largest frame p50 / p90 / max B | cap hits s/min | ≥ 80-pkt frames/min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| b_1x | 59.86 | 31.8 | 1.17 | 27.28 | 173 | 7.08 | 44,428 / 86,721 / 89,529 | 6.6 | 0 |
| b_2x | 59.82 | 36.9 | 3.69 | 14.57 | 138 | 7.09 | 46,920 / 86,340 / 89,587 | 6.2 | 0 |
| b_4x | 59.80 | 46.2 | 4.49 | 11.90 | 177 | 7.09 | 47,310 / 86,340 / 89,590 | 6.4 | 0 |
| b_8x | 59.88 | 36.9 | 1.76 | 7.61 | 155 | 7.09 | 48,463 / 86,688 / 89,562 | 7.0 | 0 |
| c_1x | 59.71 | 328.5 | 3.25 | 88.38 | 162 | 12.73 | 63,080 / 86,623 / 89,395 | 9.8 | 0 |
| c_2x | 59.69 | 364.6 | 3.87 | 94.18 | 160 | 12.73 | 65,567 / 86,477 / 89,409 | 8.7 | 0 |
| c_4x* | 59.47 | 607.0 | 5.60 | 212.70 | 404 | 12.71 | 86,263 / 87,388 / 89,084 | 39.4 | 0 |
| c_8x | 59.76 | 379.4 | 3.67 | 57.24 | 162 | 12.74 | 69,728 / 86,617 / 89,433 | 9.9 | 0 |

- **The quick win costs the link almost nothing.** In (b), with the 1080p
  source downscaled to 720p at 7000, the per-second largest frame p50
  rises 44 → 47-48 KB, cap hits stay at 6-7 s/min, and there are no
  ≥ 80-packet frames. The loss in the (b) holds fell as the scale rose
  (27 → 8/min), which is the link's variance, not the source's.
- **The c3 1080p arm still fails on this link**, as it did in C5-M2:
  328-607 spikes/min and 57-213 loss/min. The live controller made **no
  decisions** in any (c) hold, because its guards refuse under the
  selector (`reference_profile`, `no_override`), as designed. It also
  made none in (b) on this link: 0 transitions.
- The decision-log slices are in `runs*/decision_log_*.jsonl`.

## 3. Offline quality on the real 1080p source (`c5_m4_offline.py`, `offline_G/`, `offline_F/`)

**The method** is C5-M3's, with these differences:

- **Deterministic replay.** Each reference is a fresh launch from
  power-on, unpaused through the command port and captured at a fixed
  offset after the unpause: x11grab, `libx264 -qp 0`, 4:2:0, 60 s. While
  each capture ran, RetroArch held 59.999 fps with no interval over the
  bar, and every capture is 3,600 frames with no dup and no drop.
- **The alignment is exact.** A second capture of the same segment at 4x
  (the control) is **bit-identical** to the reference once aligned: a
  20-frame lag, a 1-pixel vertical offset, SSIM 1.0, PSNR 100. So the
  method adds no alignment noise.
- T comes from a separate capture at today's 1x/879×720 window, through
  the companion's scale/pad. It is aligned the same way (lag 23 frames,
  shift 0/−1 px).
- **Every arm is compared with the 4x 1920×1080 reference as shown.**
  - T and S720 can only be compared after the TV's upscale. That upscale
    is modelled as a bilinear 1.5× (the onn's own scaler cannot be
    measured from here).
  - The S1080 arms are compared as they are.
  - "Content" is the 1316×1008 picture box, pillars excluded. It is the
    figure to read.
- The encodes run the companion's `h264_vaapi` argv (its scale/pad filter
  at the arm's size, `-max_frame_size`, `-g`, `-bf 0`).
- Packets per frame are counted at 1,186 payload bytes per RTP packet.

### G — the 3D segment: a 3D demo fight (~45 s), then the black "NAMCO PRESENTS" card (125-185 s after the unpause)

The 4x reference is 1.7 GB for 60 s, against 0.25 GB for the FMV
segment.

| arm | source → encode | shown | SSIM full | **SSIM content** | p5 content | PSNR content dB | IDR pulse | 4 Hz bin / GOP fold |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| T (today) | 879×720 @1x → 720p/7000/90K/G15 | bilinear ×1.5 | 0.8948 | **0.8378** | 0.7730 | 32.67 | 0.0054 | 0.2 % / 0.4 % |
| S720 (quick win) | 1080 @4x → 720p/7000/90K/G15 | bilinear ×1.5 | 0.9181 | **0.8731** | 0.8099 | 35.09 | 0.0044 | 1.1 % / 1.1 % |
| S1080-c3 | 1080 @4x → 1080p/12,600/90K/G15 | as is | 0.9365 | **0.9015** | 0.8275 | 41.30 | **0.0321** | **8.2 % / 9.9 %** |
| S1080-par | → 1080p/15,750/90K/G15 | as is | 0.9434 | **0.9121** | 0.8408 | 41.90 | 0.0342 | 10.2 % / 12.7 % |
| S1080-g30 | → 1080p/12,600/90K/**G30** | as is | 0.9407 | **0.9080** | 0.8319 | 41.78 | 0.0356 | at its own 2 Hz: 5.4 % / 9.3 % (4 Hz: 2.4 %) |
| S1080-cap | → 1080p/12,600/**120K**/G15 | as is | 0.9385 | **0.9045** | 0.8374 | 41.53 | 0.0181 | 5.0 % / 5.7 % |

| arm | IDR B p50 / p90 / max | per-s largest B p50 / p90 / max | ≥ 80-pkt frames/min | max pkts | cap hits s/min | mean / peak 1 s kbps |
| --- | --- | --- | ---: | ---: | ---: | --- |
| T | 36,147 / 59,475 / 88,833 | 42,178 / 86,652 / 89,329 | 0 | 76 | 8 | 7,006 / 8,477 |
| S720 | 42,592 / 68,010 / 88,972 | 48,576 / 86,923 / 89,177 | 0 | 76 | 7 | 7,006 / 9,773 |
| S1080-c3 | 46,710 / 70,054 / 87,329 | 54,961 / 84,609 / 89,243 | 0 | 76 | 5 | 12,592 / 14,881 |
| S1080-par | 51,964 / 74,362 / 88,458 | 62,250 / 85,959 / 89,243 | 0 | 76 | 7 | 15,730 / 18,844 |
| S1080-g30 | 46,310 / 70,023 / 88,720 | 51,737 / 86,682 / 89,243 | 0 | 76 | 8 | 12,601 / 15,177 |
| S1080-cap | 54,745 / 89,687 / 117,130 | 66,193 / 110,523 / 118,855 | **28** | **101** | 5 | 12,598 / 16,155 |

### F — C5-M3's segment, the intro FMV, reproduced

- The FMV capture started 1.55 s after the unpause. C5-M3's reference
  (sha256 `2df8ffe5…`, unchanged) aligns at its frame 338, with a mean
  absolute difference of 0.16/255. **So C5-M3's segment was reproduced
  from the command port**: it starts ~7.2 s after the unpause.
- A 60-s 4x reference was cut at that frame, and **T is C5-M3's
  reference, re-used.**

| arm | SSIM content | p5 | PSNR c dB | IDR pulse | 4 Hz bin | IDR p50/p90/max B | per-s max p50/p90/max B | ≥80 pkt/min | cap s/min | mean / peak kbps |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- |
| T | 0.9865 | 0.9644 | 50.75 | 0.0005 | 0.2 % | 39,269 / 49,584 / 67,781 | 48,325 / 56,495 / 88,571 | 0 | 1 | 7,007 / 7,606 |
| S720 | 0.9887 | 0.9687 | 52.53 | 0.0005 | 0.3 % | 38,733 / 48,618 / 74,959 | 48,315 / 55,783 / 88,305 | 0 | 1 | 7,008 / 7,661 |
| S1080-c3 | 0.9950 | 0.9820 | 60.54 | 0.0032 | 4.8 % | 48,262 / 62,372 / 72,305 | 81,101 / 86,551 / 89,079 | 0 | 10 | 12,577 / 13,835 |
| S1080-par | 0.9961 | 0.9858 | 61.69 | 0.0027 | 4.6 % | 56,535 / 71,109 / 79,083 | 85,540 / 87,834 / 89,342 | 0 | 30 | 15,702 / 16,858 |
| S1080-g30 | 0.9957 | 0.9844 | 61.13 | 0.0033 | 1.3 % | 47,973 / 63,309 / 75,879 | 81,299 / 87,156 / 89,079 | 0 | 12 | 12,590 / 13,807 |
| S1080-cap | 0.9952 | 0.9838 | 60.75 | 0.0018 | 2.8 % | 56,678 / 72,662 / 83,449 | 81,406 / 97,524 / 118,215 | 11 | 1 | 12,602 / 13,674 |

### How to read it (anchors, not a gate)

- **T → S720 is the value of the source change alone.**
  - On 3D, content SSIM goes 0.838 → 0.873 (+0.035) and PSNR +2.4 dB, at
    the same 7000, the same link cost and the same TV upscale.
  - On FMV it is +0.002. Internal resolution does not touch MDEC video;
    the small gain is the different scaling path.
- **S720 → S1080 is the value of the rung**, on 3D at 12,600 / 90 KB:
  - +0.028 (c3), +0.035 at 15,750 (parity), +0.035 at GOP 30 and +0.031
    at the 120 KB cap; PSNR +6 dB;
  - on FMV, +0.006 to +0.007.
  - The absolute figures on 3D are low, because the 4x reference carries
    a great deal of fine detail: 230 Mbit/s lossless.
- **The 1080p arms pulse at the IDR rate under the 90 KB cap**:
  - IDR pulse 0.032-0.034 against 0.004-0.005 at 720p, and the 4 Hz bin
    holds 8-10 % of the SSIM variance on 3D;
  - the cap holds the 1080p IDRs to ~half the bytes their detail asks
    for, and the frames after each IDR recover.
  - **The 120 KB cap halves the pulse**, but brings back 28 frames/min of
    ≥ 80 packets (max 101). That is `P6`'s burst, the loss mechanism
    C5-M1 measured at ~150/min.
  - **GOP 30 moves the pulse to 2 Hz** and buys the most picture at
    12,600, but doubles the wait for an IDR after an unrecoverable loss.
- **Whether S1080's gain is visible at the TV's viewing size is a picture
  question.** It is the user's, on the TV, later, and not a gate here.
  The same goes for whether the 4 Hz pulse at 90 KB is visible.

## 4. The proposal — written, NOT applied (`c5_m4_proposed_source_config.diff`, `proposal/`)

**The PS1 source config, as a diff against the current files.** Both
files are under `~/.config/retroarch/config/Beetle PSX HW/`.

1. **New file, the core override `Beetle PSX HW.cfg`**:
   `video_fullscreen = "true"` and `video_windowed_fullscreen = "true"`.
   The window becomes 1920×1080 for every PS1 title and for no other
   core. That is RetroArch's own per-core override mechanism;
   `retroarch.cfg` is untouched, so NES, SNES and Genesis are untouched.
2. **The base core options `Beetle PSX HW.opt`**: one line,
   `beetle_psx_hw_internal_resolution` `"1x(native)"` → `"4x"`.
   - Core options are per-core already (the 2D cores read their own
     `.opt`).
   - **The six titles with their own `.opt` copy keep 1x unless the same
     line is changed in each.** The multitap path seeds the copy once and
     never re-reads the base. Tekken 3 has none, so it would follow the
     base.
3. **Not proposed, because not measured:**
   - `dither_mode` (1x native dithering at 4x makes a coarse pattern; the
     alternatives are "internal resolution" or "disabled");
   - `filter` (textures stay nearest-filtered at 4x);
   - MSAA, PGXP, the Vulkan renderer, and 8x.

   Each is a candidate for the user's picture look, then a measured arm.

**Applying and reverting (hand steps).**

- Apply with no game running: write the override, and back up the base
  `.opt` (sha256 `7885077…`) before editing the one line.
- Revert: delete `Beetle PSX HW.cfg` and restore the backed-up `.opt`.
- The companion and its argv need no change. The adopted stream (720p at
  7000) then carries the 4x source. That is the S720 row, which is the
  **quick win** path, and its link cost is the (b) rows.
- RetroArch rewrites `.opt` on exit with the values in force, so editing
  it while a game runs is lost.

**What the 1080p rung would need — a design for Part 2, not built.**

- **Bitrate / cap / GOP.**
  - Start from `native_game_1080p60_c3_80pct_cap90` (12,600 kbps,
    90,000 B, GOP 15), which is already in the tree behind the selector.
    It is the one 1080p arm with no ≥ 80-packet frames on either segment,
    and its IDR interval stays at 250 ms.
  - Screen GOP 30 beside it: +0.0065 content SSIM at the same rate,
    against a 500 ms worst-case wait for an IDR.
  - Not the 120 KB cap: its ≥ 80-packet frames are the burst `P6` removed.
  - Parity (15,750) buys +0.011 over c3 for +25 % on the wire.
- **The packet and FEC load.**
  - c3 measured 12.71-12.74 Mbit/s of client-received video in every
    (c) hold.
  - Scaled by C5-M3's measured 7000 row (7.09 video → 8.60 Mbit/s and
    954 packets/s on the wire, parity and headers included), the rung is
    **~15.4 Mbit/s and ~1,710 packets/s on the wire**. That is about 1.8×
    the 7000 rung, with 8+1 parity at ~1/9 of the packets.
- **Against the calibrated capacities.**
  - The `nft` nights' caps were 854-856 kB/s (~6.9 Mbit/s), set to
    0.82× the 7000 rung's measured 1,065 kB/s. **They are synthetic
    shortfalls for testing the decrease path, not a measure of the
    link.**
  - No real throughput ceiling of the hop has been measured. O1's PHY
    rate is 94-200 Mbit/s, and 7 Mbit/s costs ~3.6 airtime points.
  - On today's link the c3 arm lost 57-213 packets/min. So the rung
    needs the user's link change (40 MHz) and a LINK-L1 re-run before
    any screening.
- **The ladder position.**
  - It is a rung above 7000: 5000 / 5500 / 6000 / 7000 / **1080p 12,600**.
  - It is entered only from 7000, after a long clean window (a
    pre-registered number of consecutive clean reports, many times the
    increase rule's).
  - It is left on the **first** `capacity_mild` bar (fps < 57 on 4/5,
    lost ≥ 50 on 3/5), to 7000 at 720p. The strict capacity rule and the
    recovery backstop act as now.
- **The actuator change it needs (listed, not built):**
  1. the actuator's validated level list and its 7000 guards
     (`c3-validated-bitrate-transition`, the continuity cycle, recovery's
     restart) take a level that carries a **size** as well as a bitrate;
  2. the encoder restart rebuilds the argv's scale/pad at 1920×1080, and
     `native-stream-status` reports the level's width and height;
  3. the controller's `reference_profile` and `no_override` guards accept
     the 1080p level as a ladder level, not as a selector override;
  4. recovery's level-preserving restart (C3-F1) covers it;
  5. the client takes its size from the SPS. C5-M1 showed 1920×1080
     decoded at session start with no client change. **A size change
     mid-session**, on a restart with a new SSRC and SPS, has not been
     tested, and is the first thing Part 2 must show;
  6. the source must already be at the 1080p window, which is this
     proposal; otherwise the rung carries an upscale.

**The host cost of the candidate, in plain figures.** Both are measured
at the 1920×1080 window; the picture's pixel count is the same at both
scales.

- **No stream, 1x → 4x**: GPU busy 10 → 18 % (p95 11 → 22), GPU power
  15.4 → 16.6 W, RetroArch ~32-33 % of one core at both, Tctl max
  49 → 54 °C.
- **With the 7000 stream**: GPU 15 → 21 % (p95 16 → 26), 22.1 → 23.2 W,
  Tctl 58 → 61 °C. The encoder process takes ~36 % of one core at either
  scale. That is more than C5-M3's 25-31 % on the 879×720 window, because
  the capture of 2.25× the pixels plus the downscale is now in the
  encoder process.
- **With the 1080p stream**, the encoder takes ~74 % of one core, against
  C5-M1's 37-40 % on the 879×720 source.
- Host CPU overall is 10-14 %.
- **No minimum-hardware claim is made.** This is one host, one title and
  attract mode. Phase E owns the resource envelope (E1-E4).

## 5. Teardown and state

**After each table** (`c5_m4_table.log`, `c5_m4_table_8x.log`):

- the measurement files deleted (count 0);
- the selector unset, so the manager's `PRIVYHUB_*` is none and the
  environ holds exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
- mode live, configured live, acts true;
- the stream at 7000, the adopted profile, `any_override` false;
- no game;
- APK `de072762…835e` confirmed on the onn;
- the stale banner cleared by force-stop and relaunch (count 0).

**The offline run's trap cleared the files and stopped the game.**

**At the end (§ "Final state" in `c5_m4_final_state.txt`):**

- `retroarch.cfg`, the core options (all eight `.opt`), the input config,
  `emulators.json`, `controller_overrides.json`, the core, the unit file
  and the drop-in are **byte-identical** to `prestate_sha256.txt`.
- `privyhub-session.cfg` and `privyhub-input.cfg` are regenerated at
  every launch with a new command port. Both were restored to the
  pre-task bytes, port 48185.
- The companion, checked at 17:59Z:
  - its MainPID serves 8765;
  - the manager carries no `PRIVYHUB_*`, and the environ carries only
    `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
  - adaptive mode live, configured live, acts true;
  - the adopted profile at 7000, `any_override` false;
  - the selector is absent from the manager and the environ;
  - no game and no RetroArch process;
  - the APK on the onn is `de072762…835e`.

**Side effects, outside the launch config:**

- c_4x's link-drop recovery saved `Tekken 3 (USA).state.recovery` and the
  slot-0 state at 17:13:25Z, and rewrote
  `data/games/retroarch/privyhub_recovery_save.json`. That is the
  companion's designed behavior under real loss, as on the D1 night,
  which left the previous one. All of it is outside git.
- The 4x clips (5.6 GB) are in `runtime/c5_m4/`, outside git.
  `offline_clips_sha256.txt` holds their hashes.

## Files (`c5_m4_2026-10-01/`)

- **Pre-registration:** `c5_m4_preregistration.txt` / `.sha256`.
- **Pre-state:** `prestate_sha256.txt`.
- **Tools:**
  - `c5_m4_source.sh` (the measurement override and options);
  - `c5_m4_sampler.py` (the 1 s host rows, the frame counter, telemetry
    and thumbnails);
  - `c5_m4_hold_a.sh`;
  - `c5_m4_run.sh` (C5-M2's hold under D1's rules);
  - `c5_m4_table.sh` (the D1-pattern orchestrator);
  - `c5_m4_host_table.py`;
  - `c5_m4_offline.py`, `c5_m4_offline_run.sh`;
  - `ra_cmd.py`, `t2_sample.py`.
- **Runs:** `runs/`, `runs_8x/` (per hold: the host, title and telemetry
  series, the report, armcheck, status, frames, heartbeat, alpha, the
  decision log, SurfaceFlinger, companion and adb monitor; thumbnails
  for a_1x).
- **Logs:** `c5_m4_table{,_8x}.log`, `c5_m4_offline_run.log`.
- **Offline:** `offline_G/`, `offline_F/` (the tables and the per-frame
  series), `offline_*_{encode,score}.log`, `offline_F_align.txt`,
  `offline_clips_sha256.txt`.
- **Proposal:** `c5_m4_proposed_source_config.diff`, `proposal/`.
- **The redactor's check:** `redact_check.txt`.
- **Manifest:** `sha256_manifest.txt`.
