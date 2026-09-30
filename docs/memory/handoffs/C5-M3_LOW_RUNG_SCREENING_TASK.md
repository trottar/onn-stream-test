---
memory_schema: 1
as_of: 2026-09-29
status: TASK HANDOFF — C5-M3: screening data for the remote transport (Phase G) — three low-bitrate candidates (720p60 at 4000 and 3000 kbps, 540p60 at 3500) behind the profile selector, an offline objective-quality table against a lossless reference (incl. 5000-7000 as anchors), and one seven-hold night against the adopted profile; nothing joins the live ladder; nothing adopted; authorized by the user 2026-09-28 ("yes fold in the low-rung screening")
---

# C5-M3 — the low rungs, screened for later

**Why.** The live ladder is 5000-7000 and stays so on the home link:
nothing recorded at home is a capacity shortfall that a lower bitrate
would fix (L1's replays: outside link drops, the controller only ever
wanted 6000). 5000 was rejected on 2026-09-14 on the pre-baseline stack
(queue-overflow drops, a 1,010 ms gap, 203 audio underruns in 57 s), not
for its bitrate; on the adopted build 5000 met every row and the user
rated it 7-9. Phase G's remote transport will meet upstream links that
cannot carry 6+ Mbit/s, and the controller will need somewhere to go.
Whether that is a starved 720p or a lower resolution is unmeasured. This
task measures it unattended so the answer exists when Phase G starts.

Read first: `C3_FIXED_5000_NOT_ACCEPTED_2026-09-14.md`,
`C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`,
`C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` (§ rung load: 7000 ≈ 8.7 Mbit/s
on the wire, 5000 ≈ 6.2), the C5-M1 record and harness (the selector, the
golden test, the hold harness and scorer — reuse), the C5-M2 task (the
same named-profile table; add to it), `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`,
`D_BASE_CLOSEOUT_2026-09-23.md`.

**Scope.** Three more named profiles in the selector's table, none ever
the default, the golden test (unset → today's argv byte-for-byte) re-run
before and after:

| id | size | kbps | cap B |
| --- | --- | --- | --- |
| `native_game_720p60_4000` | 1280×720 | 4000 | 90,000 |
| `native_game_720p60_3000` | 1280×720 | 3000 | 90,000 |
| `native_game_540p60_3500` | 960×540 | 3500 | 90,000 |

GOP 15, bframes 0, FEC 8, audio cushion 12/17 and redundancy 2/4 copied
unchanged; the cap stays the adopted 90,000 in every arm so bitrate or
size is the only lever (at these rates the cap bounds the burst the same
way; if IDRs hit it, that is reported). No client change (540p is below
what the onn already decodes; the client scales to the surface — confirm
from `NativeStreamActivity` / the decoder config and say how). No change
to the live ladder, the controller, the actuator's validated list or the
adopted profile. No `nft`. Attract mode, no controller, the adaptive
flag and `PRIVYHUB_FEC_SCHEME` unset.

## 1. Offline objective quality (before any hold)

A 60 s lossless reference of the attract-mode window captured by the
same `x11grab` source (1280×720 after the adopted scale filter; lossless
`ffv1` or `libx264 -qp 0`), then that reference encoded through the same
`h264_vaapi` argv at 7000, 6000, 5500, 5000, 4000, 3000 (720p) and 3500
(540p, then scaled back to 1280×720 with a bilinear scaler as the TV
would upscale — say which), each decoded and compared frame by frame.
Report per arm: mean SSIM and PSNR, p5 SSIM, and an **IDR pulse** figure
— the mean |SSIM(IDR) − SSIM(frame before)| over every GOP boundary and
the 4 Hz component's share of the SSIM series' variance — so "does the
picture pulse every 250 ms" is a number. Also IDR size p50/p90/max and
cap hits. **Not a gate**; it is the anchor the user's later picture check
is read against (the user rated 5000-6000 at 7-9).

## 2. The night — seven 20-minute holds

**B, 720p/4000, B, 720p/3000, B, 540p/3500, B**, adopted between every
arm, companion restarted through its unit before each with the selector
set or unset, T2 on, `any_override` at PLAYING, first hold ≥ 40 min after
the last `session_ended`, one thing on the host at a time.

**Pre-registered** (written before the night, not changed after): an arm
**passes transport** if its hold meets spikes < 200/min, post-FEC video
loss < 10/min, max output gap ≤ 250 ms, rendered fps ≥ 59.5, stale drops
< 20/min. Reported, not gated: on-air Mbit/s (measured, not estimated),
frames ≥ 80 packets/min, cap hits/min, IDR sizes, decoder queue and
`codec_ms`, host/GPU load, thermal. If two or more B holds miss the
baseline, the night is **INCONCLUSIVE (link)** and re-runs once the
following night.

## 3. Teardown

Selector unset and confirmed absent in the manager and the companion's
environ, companion under systemd, profile adopted, adopted APK hash
confirmed, stream at 7000, game inactive, banner cleared, samplers
stopped.

## Record and memory

`evidence/C5_M3_LOW_RUNG_SCREENING_<date>.md` (the profiles, golden
checks, the offline quality table with 5000-7000 as anchors, the night's
seven holds, each arm's transport outcome, on-air rates side by side with
L1's rung-load table, and what it means for Phase G — stated as data, the
choice of a remote floor is the user's later); evidence dir with the
reference clip's hash (not the clip if it exceeds 50 MB — then its path
outside git), encodes' metrics, harness, reports, heartbeats, thermal,
manifest; `patches/C5-M3_*.md`; `PATCH_INDEX.md`; `docs/ROADMAP.md` (C5
line and a pointer under Phase G); `CURRENT.md`; `investigations/ACTIVE.md`;
`TOOLS.md` (the profile ids; never leave the selector set); the daily
file. No addresses. Nothing adopted. Nothing committed.
