---
memory_schema: 1
as_of: 2026-09-25
baseline_commit: 824c9d9
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase C — adaptive streaming on Linux — RESUMED 2026-09-23.** `D-BASE`
is **CLOSED: BASELINE MET** (`evidence/D_BASE_CLOSEOUT_2026-09-23.md`;
decision `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`, closed). The
roadmap's Linux order: **C3** (adaptive bitrate) → C4 → C5 → C6 → C7.
**C1 is done**: the reference profile declares every stream parameter
explicitly, including the cap, cushion and redundancy.

## Current Work Item

**`C3.L3a` Part 2 — the pre-registered rerun: sessions 1-3 of ≥ 4
RECORDED (2026-09-24, runs `20260924_115810`, `20260924_130016`,
`20260924_151953`, pooled); session 4 AWAITING THE USER** (their play).
**Session 3** (`C3-L3A-R3`, `evidence/C3_L3A_R3_SESSION3_2026-09-24.md`):
its 24-change report was stored — **the cap is RUNTIME VALIDATED**; W 5.0
jump 1/5, ramp 2/5, decoys 1/10 and 3/10; max gap 564 ms = the
after-Phase-B restore. **Interim pooled (3 sessions, W 5.0): jump 5/15,
ramp 11/15 (20 marks), decoys 4/30 and 9/30 — bar not reached, no
verdict.**
**Sessions 1-2**: no verdict.
- Session 1: `evidence/C3_L3A_R1_SESSION1_2026-09-24.md`. An accidental
  BACK split its client session.
- Session 2: `evidence/C3_L3A_R2_SESSION2_2026-09-24.md`. It is on the
  decoder axis from its journal-rebuilt report.
- The cap was raised to 48,000 by `C3-L3A-R2B`, and the URL transport
  ceiling is ~41.4K.

**The pre-registration** is 10 traversals, dwell 55-90 s, primary W 5.0 s,
≥ 4 sessions to ≥ 20 per shape, anchored 1-10 rating
(`investigations/ACTIVE.md` §C3.L3a). The 2026-09-20 session was
re-scored without answering the gate (`C3-L3A-P2R1`).

**Weekend queue 1 (2026-09-24/25, `handoffs/WEEKEND_2026-09-24_QUEUE.md`):**
- `C3-L3A-R3`: session 3 recorded, cap RUNTIME VALIDATED.
- `C4-D1`: BUILD static k+2 first; adaptive FEC not supported.
- `CTRL-L1`: the controller loss is on the PATH.
- `C3-L4-S1`: shadow SILENT; live BLOCKED.
- `D6-R1`: NOT REPRODUCED.

The records are under `evidence/` and in the daily file `2026-09-24.md`.

**Weekend queue 2 (`handoffs/WEEKEND_2026-09-25_QUEUE.md`):**

1. **`C6-D1`: source contract ESTABLISHED.** It exists on paper and as an
   interface module that production does not import (7/7 tests), with 14
   cross-boundary findings. The one correctness defect: recovery's restart
   refuses after any ladder transition
   (`evidence/C6_D1_SOURCE_CONTRACT_2026-09-25.md`).
2. **`C4-M1`: FEC arm (8+2 `xor8_2`, override only) NOT SHOWN.** It won
   1 of 3 pairs, with the A median at 69 % of B's. The arm recovered more
   but raised pre-FEC loss 2-3×. Cost within noise; nothing adopted; the
   adopted APK is reinstalled (`evidence/C4_M1_FEC_ARM_2026-09-25.md`).
3. **`D7-R1`: 8 of 10 rows PASS twice**; recovery cited; the profiles row
   FAIL is a script defect (every field as expected). NEEDS USER:
   controller feel and picture
   (`evidence/D7_R1_LINUX_REGRESSION_2026-09-25.md`).

**Phase C preconditions (`handoffs/PHASE_C_PRECONDITIONS_2026-09-25_TASK.md`):**

1. **`C3-F1`: WORKING.** Recovery's restart is level-preserving at
   5000-7000 (`evidence/C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`).
2. **`D7-R2`: the profiles row PASS.** All 9 scripted rows PASS in one
   pass of the fixed script (`evidence/D7_R1_LINUX_REGRESSION_2026-09-25.md`
   §R2).
3. **`CL-B1`: the decoder report as a POST body, built and tested; not
   adopted.** Companion both forms, cap 128,000; the arm APK `71d8c3d7…`
   stored a body report; the adopted APK is reinstalled
   (`evidence/CL_B1_DECODER_REPORT_BODY_2026-09-25.md`).

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
reason; `c3_l3a_runs/` is empty (2026-09-20 files moved to evidence).
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
  (`TOOLS.md`); none set.
- **Installed**: APK `f31b1c18…8ae7`; companion = systemd user unit
  `privyhub-companion` (`H3`) — restart with `systemctl --user restart`;
  last restarted 2026-09-25 07:03:55Z by `CL-B1` (no override; `fec` `xor8_1`); installed APK the adopted `f31b1c18…8ae7` (reinstalled 07:17Z, hash confirmed; the source tree also carries `C4-M1`'s and `CL-B1`'s client changes).
  Host headless (`H2`); host wired to the Opal, onn on its 5 GHz (`B2`).
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); adb after a host reboot: `adb connect <onn-address>:5555`.

## Next Action

1. **The user's `C3.L3a` session 4 and their reading of the pooled table.**
   Nothing runs without them. After it, run `--finalize`, then
   `--aggregate`.
2. **The user's FEC call.** Recommended: no adoption; 8+1 stays (`C4-M1`
   NOT SHOWN).
3. **The `C3.L4` live decision.** Its precondition, `C3-F1`, is met:
   recovery's restart is level-preserving. Live still needs the gate
   reading, a fault-injection night (the user's `nft`), and the shadow
   log trimmed.
4. **C5, which needs a profile.** 1080p60 waits on the user's yes.
5. **D7's NEEDS USER rows**: controller feel, picture, and save/load
   through the TV (the list in the D7-R1 record).
6. **The user's APK adoption call for `CL-B1`.** The arm APK is
   `71d8c3d7…`; the source also carries `C4-M1`'s inert v2 FEC decoder.
7. **A commit of everything since `7a2e103`** (the user's).
8. **Then the C7 / D8 checkpoint.**

**Open, not blocking:**

- the max output gap;
- `host_link`;
- the thermal flag proposal;
- the controller item (`CTRL-L1`: PATH);
- the recent slow-event ring (fills in ~12 min in attract mode, `CL-B1`);
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

## Relevant References

- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the scored table and verdict.
- `investigations/BASELINE_STREAM_HEALTH.md` (MET);
  `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` (closed);
  `decisions/D-BASE-P{6A,9,10}_*` (the three adopted values).
- `handoffs/CURRENT_HANDOFF.md` (Phase C); `investigations/ACTIVE.md`;
  `docs/ROADMAP.md` (Phase C, D-072 order); `docs/KNOWN_ISSUES.md`.
- `evidence/RUNTIME_VALIDATION.md` — a classification per record;
  `patches/PATCH_INDEX.md` lists all 131.
