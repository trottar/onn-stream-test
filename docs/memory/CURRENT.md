---
memory_schema: 1
as_of: 2026-09-23
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

**`C3.L3a` Part 2 — gameplay acceptance of the Linux actuator**, where
Phase C was suspended on 2026-09-20. **Fix the probe's three recorded
defects before any rerun** (`investigations/BASELINE_STREAM_HEALTH.md`,
"Suspended, not failed"): the mark-association window anchors on
sequence start, so ramps close their window before finishing; telemetry
field paths were taken from a probe artifact, not the endpoint, so
settling was never measured; the picture rating used an unanchored 1-5
scale that rescaled 1-10 answers. The 2026-09-20 raw marks and per-cycle
timings are in `logs/streaming/c3_l3a_gameplay_acceptance_state.json` —
re-score them without replaying first.

## Verified State

**The baseline, cold and warm, on the adopted build** (close-out,
2026-09-23; target / cold / warm): spikes ≥ 20 ms/min < 200 / **32.8** /
**26.0**; rendered fps ≥ 59.5 / **59.90** / **59.91**; stale drops/min
< 20 / 1.1 / 0.8; video loss/min (post-FEC) < 10 / **8.7** / **8.4**;
audio underruns 17 / 14 per session; max output gap ≤ 100 / **163** /
**110** ms — the transport's open row. Frames < 20 ms rx→output 99.1-99.3 %.

- **Profile** `native_game_720p60_reference`
  (`companion/native_stream_profiles.py`), all `source: profile`,
  `any_override: false`: 1280x720@60, 7 Mbps, GOP 15, no B, 8+1 FEC,
  **cap 90,000 B** (`P6a`), **cushion 12/17** (`P9`), **audio redundancy
  2/4** (`P10`). Env overrides exist for comparison sessions only
  (`TOOLS.md`); none set.
- **Installed**: APK `f31b1c18…8ae7`; companion = systemd user unit
  `privyhub-companion` (`H3`) — restart with `systemctl --user restart`.
  Host headless (`H2`); host wired to the Opal, onn on its 5 GHz (`B2`).
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); adb after a host reboot: `adb connect <onn-address>:5555`.
- **`.claude/` and `_prel2b/` are untracked and unignored** — the user's
  call before any commit.

## Next Action

Fix the three `C3.L3a` Part 2 probe defects, re-score the retained
2026-09-20 marks, and only then decide on a rerun; then `C3.L4` (the
automatic controller). **Constraint to honour**: `C3.L2` classified Linux
as `video_only_restart`, not authorized for automatic adaptation during
play — `C3.L4` must answer it, not ignore it. Also open for the user: the
`T2`/`T3` warm-state threshold proposals (none enforced); `host_link`
(first fact: `T3`).

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
  `patches/PATCH_INDEX.md` lists all 119.
