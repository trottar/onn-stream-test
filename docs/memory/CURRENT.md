---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: 4e45a4f
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase C — `C3.L4` CLOSED 2026-09-30, and since 2026-10-01 live adaptive
bitrate is ON BY DEFAULT (`C3-L4-D1`)**, through the unit drop-in
`~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`. The
user authorized it on 2026-09-30: "do the loss row look first and then
the live default".

- **The loss row look (`LINK-L1`) is MIXED.** 3 of 6 pre-registered
  holds over one day meet loss < 10/min, and the misses bracket a meet.
  No conclusion is drawn.
- C7 / D8 are met or explicitly deferred. The checkpoint commit
  `4e45a4f` is in.
- **Earlier:**
  - `D-BASE` CLOSED (baseline met, 2026-09-23); C1 done;
  - C4 closed (8+1);
  - C5 characterized (1080p60 NOT CAPABLE at parity; the low rungs
    screened for Phase G);
  - C6 contract on paper; D7 complete;
  - the `CL-B1` APK `de072762…835e` adopted (2026-09-30).

## Current Work Item

**The LINK-L1 / D1 prompt (under `handoffs/QUEUE_2026-09-29B.md`'s
rules): Code ran Part A, then Part B, and stopped.**

- **`LINK-L1`: MIXED** (`evidence/LINK_L1_LOSS_ROW_2026-10-01.md`).
  - Six 20-min holds, adaptive off, one per local 4-hour block, 12:40
    EDT on 09-30 to 08:41 EDT on 10-01. Loss/min: 37.27 ✗, 4.25 ✓,
    15.19 ✗, 3.16 ✓, 7.54 ✓, 16.78 ✗. The max gap met ≤ 100 on one hold.
  - History since D-BASE: 16 of 36 holds meet, with meets and misses in
    every block.
  - Retries, link rate, RSSI and the MCS share do not predict the loss
    across nights.
  - The air (read-only, counts only) is as O1 found it: channel 36 at 80
    MHz, idle 3.3 %, noise −89/−90. 3-4 strong BSSIDs share the 80 MHz
    block's secondaries, and 0 are on 36.
- **`C3-L4-D1`: live ON BY DEFAULT since 2026-10-01 13:07Z**
  (`decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`,
  `evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`).
  - B1: the drop-in is verified. The environ carries exactly the one
    name and the manager none; mode live, acts true; `any_override`
    false; the unit file and the shadow unchanged.
  - B2: `tools/c3_l4_nft_night.py` and `tools/d7_regression.py` accept
    the one name only. The nft teardown restores the baseline, not off,
    and a skipped-teardown path was fixed. Tests 32/32, mutations 4/4,
    fake-sudo FULL and ABORT PASS.
  - B3a, the injection: **NOT PASS AS PRE-REGISTERED.** The controller
    acted as intended (one FALLBACK 7000 → 5000, client SSRC change 1,
    reset at BACK, inject flag gone, route 403). But two clauses failed
    as worded:
    - an `ssrc_change` row that is never emitted for an own transition;
    - a stream read 0.3 s before the client's stop.
  - B3b, the 30-min hold on the default: **SILENT** (0 transitions,
    refusals or HOLDs; client rows met; loss 7.59, max gap 447 ms).
- **Earlier** (records under `evidence/`, and the daily files): N3,
  `CL-B1`, C7 / D8 (09-30); N2, C5-M2/M3, N1 (09-29); L1, R4, C5-M1 (09-28).

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
  2026-09-30; hash confirmed on the onn at every LINK-L1 / D1 teardown,
  last 2026-10-01 14:38Z; the previous
  `f31b1c18…8ae7` is kept at `runtime/c4_m1/adopted_app-debug.apk` for
  rollback).
  - The companion is the systemd user unit `privyhub-companion` (`H3`);
    restart it with `systemctl --user restart`.
  - **Live adaptive bitrate by default, since 2026-10-01 13:07Z**,
    through the drop-in
    `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
    (`Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`). The unit file
    is unchanged.
    - The companion's environ carries exactly that one `PRIVYHUB_*`,
      and the user manager none.
    - `adaptive_bitrate.mode live`, `configured_mode live`, `acts true`.
    - Kill switches: delete the drop-in + `daemon-reload` + restart
      (off); `POST /plugins/games/adaptive-bitrate/disable` (shadow, one
      session).
  - Last restarted 2026-10-01 14:38Z by the D1 night's teardown:
    - manager none, environ the one name, mode live;
    - no selector, `PRIVYHUB_FEC_SCHEME` absent;
    - profile adopted at 7000, `any_override` false;
    - no game, 0 banners.
  - The companion tree carries the live controller through `C3-L4-N2`
    (unchanged by D1) and the C5 selector profiles (dormant).
  - The C5 night scripts in evidence still name the old APK (`TOOLS.md`).
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); adb after a host reboot: `adb connect <onn-address>:5555`.

## Next Action

1. **The user's commit** of the LINK-L1 / D1 work. Cowork gives the line
   from `logs/link_l1_d1_git_status_2026-10-01.txt`. Nothing is
   committed by Code; `logs/` and the APKs stay out of git.
2. **Part A was MIXED, not TIME OF DAY or MOVED**, so there is no window
   to schedule into and no re-baselining is called for. The loss row is
   met on about half the holds at any hour.
   - If the user wants it to hold reliably, the levers are theirs, with
     what the air view says about each in the LINK-L1 record: the Opal's
     channel or width (read-only to Code), the onn's placement, or a
     wired hop.
   - Also for the user: B3a's two pre-registration clauses (the record
     explains both). The controller acted; no rule changed.
3. **Phase E per the ROADMAP** (Linux core resource characterization and
   optimization, starting at E1, freezing the workload suite). It is not
   started.

**Open, not blocking:**

- the max output gap (447 ms on the D1 hold); `host_link`; the thermal
  flag proposal; `CTRL-L1` (PATH); the recent slow-event ring; the
  `C6-D1` migration list; the mild step's ~120 s bound (the user's ask);
- **adaptive-off measurements now need the drop-in out for the session**
  (`TOOLS.md`);
- the evidence copies of older night scripts refuse or misreport on the
  default-live companion; use the D1 pattern.

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
  `patches/PATCH_INDEX.md` lists all 140.
