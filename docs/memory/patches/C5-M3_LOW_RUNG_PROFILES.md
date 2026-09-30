---
memory_schema: 1
as_of: 2026-09-30
baseline_commit: f01c3b2
durable_memory_updated: true
---

# C5-M3: three low-rung profiles for Phase G screening, and the offline quality tool

## Purpose

The live ladder is 5000-7000 and stays so on the home link. Phase G's
remote transport will meet upstream links that cannot carry 6+ Mbit/s,
and the controller will need somewhere to go. This task screens three
lower rungs unattended, so the data exist when Phase G starts. It was
authorized by the user on 2026-09-28 ("yes fold in the low-rung
screening").

- Task: `handoffs/C5-M3_LOW_RUNG_SCREENING_TASK.md`.
- Record: `evidence/C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`.

## Change

**`companion/native_stream_profiles.py`:** a `_c5_low_rung()` helper and
three named profiles in `NATIVE_STREAM_PROFILES`. Each has GOP 15, B 0,
FEC 8, the adopted cushion and redundancy, and the adopted 90,000-byte
cap. None is ever the default.

| id | size | kbps |
| --- | --- | --- |
| `native_game_720p60_4000` | 1280×720 | 4000 |
| `native_game_720p60_3000` | 1280×720 | 3000 |
| `native_game_540p60_3500` | 960×540 | 3500 |

- **Untouched:** the live ladder (`adaptive_bitrate.LADDER_KBPS`), the
  controller, the actuator's validated list, the reference profile and
  the selector.
- **Golden:** with the selector unset, the argv is byte-identical before
  and after.
- **Tests:** `tools/test_c5_m1_profile_selector.py` 14/14 (3 new
  `C5M3LowRungs`, including "none is on the live ladder").
- **No client change.** `AvcLowLatencyDecoder` is configured with
  1280×720 as a hint; the stream's own SPS sets the decoded size, as
  C5-M1's 1920×1080 buffers showed. The full-screen `SurfaceView` is
  scaled to the 1920×1080 display by the compositor. The 540p hold's
  SurfaceFlinger capture confirms the buffers.

**`evidence/c5_m3_2026-09-29/c5_m3_quality.py`** (new, offline):

- a lossless 60 s reference from the same x11grab source and scale/pad;
- the companion's `h264_vaapi` argv per rung;
- SSIM / PSNR per frame, the IDR pulse, the 4 Hz share, and IDR sizes /
  cap hits;
- `ra_cmd.py` (C5-M1's), for RetroArch's command port on loopback.

The night reuses C5-M2's harness, copied into the evidence dir.

Nothing adopted. Nothing committed.
