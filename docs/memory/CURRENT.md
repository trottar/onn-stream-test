---
memory_schema: 1
as_of: 2026-09-30
baseline_commit: f01c3b2
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase C — adaptive streaming on Linux — `C3.L4` CLOSED 2026-09-30:
live adaptive bitrate VALIDATED UNDER REAL LOSS on the user's three `nft`
nights.**

- Night 1 NOT; nights 2 and 3 WORKS UNDER LOSS; night 3 showed the
  pre-registered HOLD shape.
- The controller as built is authorized. **Live stays behind
  `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default**; turning it on
  by default is the user's call.
- **C7 / D8 are met or explicitly deferred**, except the commit. The
  checkpoint record is `evidence/C7_D8_CHECKPOINT_2026-09-30.md`.
- **The `CL-B1` APK `de072762…835e` is adopted** (2026-09-30).
- Earlier: `D-BASE` CLOSED (baseline met, 2026-09-23); C1 done; C4
  closed (8+1); C5 characterized (1080p60 NOT CAPABLE at parity; the
  follow-ups INCONCLUSIVE (link); the low rungs screened for Phase G); C6
  contract on paper; D7 complete.

## Current Work Item

**The N3 prompt (under `handoffs/QUEUE_2026-09-29B.md`'s rules): Code
ran `C3-L4-N3`, then `CL-B1` APK, and stopped.**

- **`C3-L4-N3`: DONE.**
  - The user's night 3 is **WORKS UNDER LOSS (F1)**: capacity at +15.5 s;
    INCREASE ×2 (111 / 93 reports); `capacity_mild` 6000 → 5500 at 121 s
    after two `hold_down` refusals; HOLD `oscillation` at 5500.
  - 0 escalations and 0 recovery cycles. BACK reset to 7000 and the
    status read 7000.
  - **`C3.L4` is closed** in the decision (with the exact drop-in that
    would make live the default, not made), `docs/ROADMAP.md` (C3 criteria
    mapped to records; the C7 row), the architecture ("the controller as
    closed" table) and `ACTIVE.md`.
  - **The C7 / D8 checkpoint record** is written (it corrects the "PS1-
    and-below" claim: NES / Genesis are not claimed), with
    `logs/c7_d8_git_status_2026-09-30.txt`.
  - Records: `evidence/C3_L4_NFT_NIGHT3_2026-09-30.md`,
    `evidence/C7_D8_CHECKPOINT_2026-09-30.md`.
- **`CL-B1` APK: ADOPTED** by the pre-registered rule.
  - A clean, reproducible build `de072762…835e`; Kotlin 11/11.
  - A3: the body form, key set identical, `slow_event_capacity` 1,280.
  - A4: every client row met. A5: loss 10.29 against 11.81/min for the
    paired old APK.
  - `tools/c3_l4_nft_night.py` now expects the new hash (24/24 tests).
  - Records: `evidence/CL_B1_APK_ADOPTION_2026-09-30.md`,
    `decisions/CL-B1_APK_ADOPTION_2026-09-30.md`.
- **Earlier:** 2026-09-29/30 `C3-L4-N2` (`capacity_mild`), `C5-M2`
  (INCONCLUSIVE (link)), `C5-M3` (720p/4000 passes transport), `C3-L4-N1`,
  `C3-L4-L2(B)`; 2026-09-28 `C3-L4-L1`, `C3-L3A-R4`, `C5-M1`; 2026-09-24/25
  as before. Records under `evidence/` and in the daily files.

## Verified State

**The baseline, cold and warm, on the adopted build** (close-out,
2026-09-23; target / cold / warm): spikes ≥ 20 ms/min < 200 / **32.8** /
**26.0**; rendered fps ≥ 59.5 / **59.90** / **59.91**; stale drops/min
< 20 / 1.1 / 0.8; video loss/min (post-FEC) < 10 / **8.7** / **8.4**;
audio underruns 17 / 14 per session; max output gap ≤ 100 / **163** /
**110** ms — the transport's open row. Frames < 20 ms rx→output 99.1-99.3 %.
**Transitions on it** (`C3.L3a` smoke, 2026-09-24): telemetry settled within
one to two client reports (≤ ~4 s); each costs one 125-211 ms gap
(`codec_ms` 7-11) — the restart's ~152 ms RTP silence.
**`C3.L3a` pool rule** (`C3-L3A-P2R3`): `--aggregate` pools only v2-state
runs with the pre-registered config and lists every skipped file with its
reason; `c3_l3a_runs/` holds the four pooled runs (2026-09-24 ×3, 2026-09-28).
**`C3.L3a-S1` transition soak** (2026-09-24, n = 60 / 30, attract mode):
each restart costs one gap of median 186.5 ms (128-225; codec ≤ 13 ms;
2 of 60 an extra GOP, ~410-420 ms); telemetry settles within one to three
client reports (≤ ~4 s; once 6 s); lifecycle CLEAN
(`evidence/C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md`: A PARTIAL 52/60, B,
C CLEAN, D fps ELEVATED −0.24 else within noise, baseline in T NO on video
loss — the losses are not at transitions; no-transition H2 missed too).

- **Profile** `native_game_720p60_reference`
  (`companion/native_stream_profiles.py`), all `source: profile`,
  `any_override: false`: 1280x720@60, 7 Mbps, GOP 15, no B, 8+1 FEC,
  **cap 90,000 B** (`P6a`), **cushion 12/17** (`P9`), **audio redundancy
  2/4** (`P10`). Env overrides exist for comparison sessions only
  (`TOOLS.md`, including `C5-M1`'s `PRIVYHUB_NATIVE_PROFILE_ID`); none set.
- **Installed**: **APK `de072762…835e`** (the `CL-B1` APK, adopted
  2026-09-30; hash confirmed on the onn 15:06Z; the previous
  `f31b1c18…8ae7` is kept at `runtime/c4_m1/adopted_app-debug.apk` for
  rollback).
  - The companion is the systemd user unit `privyhub-companion` (`H3`);
    restart it with `systemctl --user restart`.
  - Last restarted 2026-09-30 15:05Z by the `CL-B1` paired hold's
    teardown: no flag, no selector, `PRIVYHUB_FEC_SCHEME` absent, profile
    adopted, `adaptive_bitrate` off.
  - The companion tree carries the live controller through `C3-L4-N2`
    (off unless its flag is set) and the C5 selector profiles (dormant).
  - The C5 night scripts in evidence still name the old APK (`TOOLS.md`).
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); adb after a host reboot: `adb connect <onn-address>:5555`.

## Next Action

1. **The user's commit** (C7 / D8 "clean checkpoint/push"). Cowork gives
   the line from `logs/c7_d8_git_status_2026-09-30.txt`. What must not be
   committed is listed in `evidence/C7_D8_CHECKPOINT_2026-09-30.md`; all
   of it is already ignored.
2. **The user's call: turn live adaptive bitrate on by default, or not.**
   The one drop-in that would do it is in the decision's 2026-09-30 close.
   Also open for the user: the adopted 720p's loss row on these evenings
   (`investigations/ACTIVE.md`).
3. **What the ROADMAP says follows C7 / D8** on the Linux order: **Phase
   E — Linux core resource characterization and optimization**, starting
   at E1, freezing the workload suite. It is not started.

**Open, not blocking:**

- the max output gap;
- `host_link`;
- the thermal flag proposal;
- the controller item (`CTRL-L1`: PATH);
- the recent slow-event ring (fills in ~12 min in attract mode, `CL-B1`;
  session 4's Phase A off-transition events were all evicted);
- the `C6-D1` migration list.

## Success Criteria

`C3` per `docs/ROADMAP.md`: bitrate first at fixed 720p60; bounded
min/max; fast decrease, slow increase; hysteresis and congestion
hold-down; no oscillation; reason codes; safe fallback to the reference
profile; latency protected before image quality. **Every change measured
against the close-out table** — the baseline must stay met. No
perceptual gate unless the user sets one.

## Do Not Reopen Without New Evidence

- **`D-BASE` is closed** — reopen only if the close-out table fails on the
  adopted profile. Its settled findings (curated in `MEMORY.md`): client
  latency (`C3.L2c`, `P1`), the audio startup burst (`P2a`), the loss is
  the frame-size tail (`P6`/`P6a`; not pacing, the air or the onn's
  receive path), the audio holes are the path's (`P7`/`P8`), the
  warm-state loss is between the ends (`T3`). **Do not derive loss as
  host-sent minus client-received** (`P4`); use `R5`'s counters.
- The adopted values: cap 90 KB (60 KB and VBV measured, not rejected —
  reopen on a picture complaint), cushion 12/17, redundancy 2/4.
- The host display path (`H2-PREP`/`H2`): the plug is X `DisplayPort-1`
  = DRM `card0-DP-2`, 1920x1080@60 by EDID; re-run the inventory, don't
  re-derive.
- The synthetic UDP pathology is **PAUSED** (`M1`), never seen post-`B2`.
- The onn's thermal zones / radio counters are absent (`T1`, `P4`); its
  status is 0 always; its CPU temperature is `dumpsys thermalservice`.
- D4/D5 restoration; the Windows-era C3 record; `C3.L3a` Part 1 (chained
  ladder transitions are clean).
- **`C3.L3a` is closed** (four sessions, the user's reading): single
  transitions are not reliably noticed, ramps are. Do not re-run the gate;
  build to the decision. **C4 is closed** for Phase C (8+1 stays).

## Relevant References

- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the scored table and verdict.
- `investigations/BASELINE_STREAM_HEALTH.md` (MET);
  `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` (closed);
  `decisions/D-BASE-P{6A,9,10}_*` (the three adopted values).
- `handoffs/CURRENT_HANDOFF.md` (Phase C); `investigations/ACTIVE.md`;
  `docs/ROADMAP.md` (Phase C, D-072 order); `docs/KNOWN_ISSUES.md`.
- `evidence/RUNTIME_VALIDATION.md` — a classification per record;
  `patches/PATCH_INDEX.md` lists all 137.
