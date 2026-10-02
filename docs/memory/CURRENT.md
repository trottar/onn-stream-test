---
memory_schema: 1
as_of: 2026-10-02
baseline_commit: 598cb61
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase C continues. C5 was reopened by the user's reading of
2026-10-01: 1080p60 is a Phase C deliverable through the adaptive
ladder**, as a rung above 7000, not only a characterization, and the
source should render natively at 1080p. PS1 comes first.

- C5-M1/M2 characterized the stream on a 720p-detail source and an
  unsettled link.
- **C5-M4 Part 1** (the source side) is done, and **C5-M4A adopted the
  4x PS1 source** the same evening, through the quick win.
- The rung is Part 2, after the user's call on the link. The user set the
  Opal to 40 MHz, and **`LINK-L2` (2026-10-02) re-ran LINK-L1's day on
  it: TIME OF DAY as scored, on the 12-h boundary by 7 s** (MIXED at
  second resolution).
- **Standing, unchanged:**
  - live adaptive bitrate is ON BY DEFAULT (`C3-L4-D1`, the unit
    drop-in);
  - `C3.L4` is CLOSED;
  - `LINK-L1` (80 MHz) is MIXED; `LINK-L2` (40 MHz) is TIME OF DAY as
    scored, on the boundary;
  - C7 / D8 are met or deferred, with the C7 1080p row reopened (ROADMAP).
- **Earlier:** `D-BASE` CLOSED (2026-09-23); C1; C4 (8+1); C6; D7; the
  `CL-B1` APK adopted (2026-09-30).

## Current Work Item

**The LINK-L2 prompt** (`QUEUE_2026-09-29B.md`'s rules): **TIME OF DAY
as scored, on the boundary.** Nothing adopted, nothing committed.

- Opal 36 / 40 MHz (read-only). LINK-L1's rule verbatim (`cc755e1b…`).
  Six valid 20-min holds, 20:41 → 16:41 EDT, adopted 7000, 4x source,
  adaptive in shadow per session (confirmed, 0 acted rows).
- Loss 20.80 / 1.64 / 9.47 / 12.84 / 13.21 / 11.49 per min; max gap
  ≤ 100 on none.
- 2 of 6 meet (00:40, 04:40). The misses span 08:41 → 20:41: 12.00 h at
  the scorer's minute resolution (**TIME OF DAY**), 12 h 0 min 7 s with
  seconds (**MIXED**). Both are reported.
- Against LINK-L1 (80 MHz): 2/6 vs 3/6, the link rate halved. 00:40 and
  04:40 met on both days. The neighbours are all on 44-48 now (0 on
  36-40), and the loss did not improve.
- H4's empty decision-log slice (log rotation), recovered by time:
  VALID.
- Record: `evidence/LINK_L2_LOSS_ROW_2026-10-02.md` (options in §6).

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

- **The PS1 source, since 2026-10-01 (`C5-M4A`): a 1920×1080 window at
  internal resolution 4x.** It is set by the Beetle PSX HW core override
  (`dc4d6019…`) and the line in the base and six per-title `.opt`. The
  stream downscales it to the profile below. The revert is in
  `TOOLS.md`. SNES is untouched.
- **Profile** `native_game_720p60_reference`
  (`companion/native_stream_profiles.py`), all `source: profile`,
  `any_override: false`: 1280x720@60, 7 Mbps, GOP 15, no B, 8+1 FEC,
  **cap 90,000 B** (`P6a`), **cushion 12/17** (`P9`), **audio redundancy
  2/4** (`P10`). Env overrides exist for comparison sessions only
  (`TOOLS.md`, including `C5-M1`'s `PRIVYHUB_NATIVE_PROFILE_ID`); none set.
- **Installed**: **APK `de072762…835e`** (the `CL-B1` APK, adopted
  2026-09-30; hash confirmed on the onn at every teardown since,
  last 2026-10-02 21:01Z (LINK-L2 H6); the previous
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
  - Last restarted 2026-10-02 21:01Z by LINK-L2 H6's teardown:
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

1. **The user's commit** of LINK-L2 (C5-M4A is in `598cb61`). Cowork gives the
   line from `logs/link_l2_git_status.txt`. Nothing is committed by Code,
   and `logs/`, the clips and the APKs stay out of git.
2. **The user's call on the link**, from the options in
   `evidence/LINK_L2_LOSS_ROW_2026-10-02.md` §6:
   - **TIME OF DAY (as scored):** screening nights in 00:00-08:00 local,
     where 4 of 4 holds met over the two days;
   - **MIXED (the second-resolution reading):** the channel (52-64 is
     empty, DFS), the onn's placement, or a wired hop;
   - **40 vs 80 MHz**, by hand: 40 MHz did not improve the row and halved
     the link rate.

   The Opal stays read-only to Code.
3. **Part 2, the 1080p rung**, on the user's word, after the link is
   settled. The design is C5-M4 §4
   (`evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md`):
   - first, the mid-session size change on the encoder restart;
   - then the rung, tests and replays;
   - then one pre-registered night.

The user's picture look at 4x, **dither mode first**, can come whenever
they like: TV only, nothing perceptual as a gate.

**Open, not blocking:**

- the max gap (447 ms, D1; ≤ 100 on 0 of LINK-L2's six); `host_link`; the thermal flag; `CTRL-L1`;
  the slow-event ring; `C6-D1`'s list; the mild step's ~120 s bound;
  B3a's two clauses; C5-M4's R3 (no `codec_ms` in the C2 telemetry);
- **adaptive-off measurements need the drop-in out** (`TOOLS.md`); old
  evidence night scripts misreport on default-live, so use the D1
  pattern (`c5_m4_run.sh` is one);
- Phase E (E1 onward) is not started.

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

- `evidence/LINK_L2_LOSS_ROW_2026-10-02.md` — the loss row at 40 MHz (TIME OF DAY as scored, on the boundary); `evidence/LINK_L1_LOSS_ROW_2026-10-01.md` (80 MHz, MIXED).
- `evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` — the PS1 source at native 1080p (C5-M4 Part 1).
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the scored table and verdict.
- `investigations/BASELINE_STREAM_HEALTH.md` (MET);
  `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md` (closed);
  `decisions/D-BASE-P{6A,9,10}_*` (the three adopted values).
- `handoffs/CURRENT_HANDOFF.md` (Phase C); `investigations/ACTIVE.md`;
  `docs/ROADMAP.md` (Phase C, D-072 order); `docs/KNOWN_ISSUES.md`.
- `evidence/RUNTIME_VALIDATION.md` — a classification per record;
  `patches/PATCH_INDEX.md` lists all 140.
