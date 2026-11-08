---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 9682a38e (B50; HOME-4+ uncommitted beside it; the user commits)
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename. The history to 2026-11-03 is in
`archive/current/CURRENT_HISTORY_2026-11-02.md` (verbatim, newest first).

## Active Objective

**Phase H OPEN — H3 (PS2) first** by the user's decision (2026-11-07), then H0 (import), then H1 / H2. **The G track
CLOSED at its checkpoint 2026-11-07** (ROADMAP §G9: 9 met, 3 deferred, 2 open; `evidence/G9_CHECKPOINT_2026-11-07.md`).
Phase E stays ACTIVE (E1 FROZEN, E2 MEASURED, E3 / E4 CLOSED). The adopted environ is **FIFTEEN lines**; the fifteenth
is G-A13's host half, `PRIVYHUB_VOD_LOG=1`, on the user's "Reconnect by default yes"
(`evidence/G_A13_VOD_LOG_ADOPTION_2026-11-07.md`). APK `cfe0211c…` CONFIRMED (HOME-4+).

## Current Work Item

- **HOME-4+ done, uncommitted** (`evidence/HOME_4_PLUS_2026-11-08.md`): queue O's APK `cfe0211c…` CONFIRMED (C7 /
  C9 / C8 / C10 met, off checks met); PS2 C11 met, **C12 not met** (not run: PrivyHub's SAVE button answers 503 for
  PS2; the user wants PS2 saving to work like PS1's); **G-A14 not adopted**, PS2 bench-only, fifteen lines.

## Verified State

**The fifteen adopted lines.** Each one is its own drop-in under
`~/.config/systemd/user/privyhub-companion.service.d/`. `tools/e1_suite.py` `ADOPTED` lists the same fifteen, and
`e3_state.py --check` reads them back.

| # | Line | Drop-in | Gate (record) |
|---|---|---|---|
| 1 | `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` | `adaptive.conf` | C3-L4-D1 (`C3_L4_…_2026-10-01`) |
| 2 | `PRIVYHUB_EPG_GUIDE_INDEX=cached` | `epg-index.conf` | E3-S6A (`E3_S6A_…_2026-10-07`) |
| 3 | `PRIVYHUB_SNES_CORE=snes9x` | `snes-core.conf` | E3-A2 (`E3_A2_…_2026-10-07`) |
| 4 | `PRIVYHUB_RECOVERY_TRIGGER=v2` | `recovery.conf` | E3-A3B (`E3_A3B_…_2026-10-09`) |
| 5 | `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` | `snes-capture.conf` | E4-S5D (`E4_S5D_…_2026-10-15`) |
| 6 | `PRIVYHUB_OVERLAY_PROVIDER=tailscale` | `overlay.conf` | G-A1 (`G_A1_…_2026-10-16`) |
| 7 | `PRIVYHUB_SESSION_IDENTITY=v2` | `session-identity.conf` | G-A1 (same) |
| 8 | `PRIVYHUB_AUDIO_CODEC=opus` | `audio-codec.conf` | G-A2 (`G_A2_…_2026-10-19`) |
| 9 | `PRIVYHUB_LINK_REPORT=1` | `link-report.conf` | G-A3 (`G_A3_…_2026-10-23`) |
| 10 | `PRIVYHUB_LINK_RECOVERY=1` | `link-recovery.conf` | G-A4 (`G_A4_…_2026-10-24`) |
| 11 | `PRIVYHUB_RESTART_FAST=1` | `restart-fast.conf` | G-A5 (`G_A5_…_2026-10-26`) |
| 12 | `PRIVYHUB_RESTART_FAST_UNLOCK=1` | `restart-fast-unlock.conf` | G-A7 (`G_A7_…_2026-10-27`) |
| 13 | `PRIVYHUB_REMOTE=1` | `remote.conf` | G-A9 (`TRIP_PREP_2026-10-29.md`) |
| 14 | `PRIVYHUB_STEP_IN_PLACE=1` | `step-in-place.conf` | G-A10 (`G_A10_…_2026-11-02`) |
| 15 | `PRIVYHUB_VOD_LOG=1` | `vod-log.conf` | G-A13 host (`G_A13_…_2026-11-07`) |

Records under `evidence/`. Line 10 implies the input hold, B6, B8, the `state` path, the stall signal and resume (B33
live inside it); line 13 acts only on a remote-class session (floor start and climb, remote ladder, 7000 cap, WAN
telemetry; the LAN as before); line 14 splices each ladder step onto the same stream at one IDR (2-s fallback);
line 15 writes one redacted row per movie range request and a retrying client's rows.
**The off switch, every line:** delete its drop-in, `systemctl --user daemon-reload`, restart the companion, and take
the name out of `tools/e1_suite.py` `ADOPTED`. Each record names its exceptions; `docs/REMOTE_TRUST.md` has the G lines.

**The client.**
- APK **`cfe0211c…` is CONFIRMED** on the onn (HOME-4+; queue O: queue N + B46 + B47; `home4_installed/`), pinned in
  the three places. On by default: the hold and stable slots (G-A11 / G-A12), the player chooser (B46) and the movie
  retry (B47); `0` / `off` give the old behaviour.
- `8ba4d996…` (HOME-3, the previous CONFIRMED) is kept in `home3_installed/`; `0132b944…` in `home2_installed/`.
- The eleven client properties are empty. One device is paired, with `identity_v2` on.

**Units.** `privyhub-companion` and `privyhub-diag` are running. `privyhub-diag` is the B36 keeper:
`tools/diag_keeper.py`, read with `tools/diag_read.py` and `tools/diag_check.py`. The nightly watch
(`privyhub-link-n1`) ended 2026-10-31 and the trip keeper (`privyhub-trip-log`) ended 2026-11-01.

**Live inside an adopted line:** B33. A release under 1 s with no loss in its window resumes without the state load;
the save is still made. Off: `PRIVYHUB_REWIND_NEEDS_LOSS=0` (`evidence/B33_NO_REWIND_WITHOUT_LOSS_2026-10-31.md`).

**Built, not adopted** (flags absent unless a record says otherwise):
- G-A6 SHELVED (B23's WAN thresholds).
- G-A8 (`PRIVYHUB_LOSS_GUARD=1`): PREPARED and never applied. The guard is out, and B27 / B29 are not in the confirmed
  APK.
- `PRIVYHUB_PS2=1` (B49 / B50, bench only; G-A14 waits on C12 — PS2 saving like PS1's, the user's requirement).
  **Bench drop-in on:** `b49-ps2.conf` (user, 2026-11-08) until G-A14; 16 lines, `--check` fails on
  environ only; SAVE/LOAD error on PS2 until B51.
- Host bench flag `PRIVYHUB_VOD_DROP_TEST` (B40 / B43, never a line).
- `PRIVYHUB_WAN_ADAPTATION` (G5-S2; its live smoke G5-S2-L never ran) and `PRIVYHUB_ENCODER_RC` (G8-S4).
- The 1080p rung (`PRIVYHUB_ADAPTIVE_BITRATE_TOP`) and `PRIVYHUB_PS1_LOOK` (C5).
- The dormant E3 / E4 flags (`TOOLS.md`).

**Profile** `native_game_720p60_reference`: 1280x720@60, GOP 15, 8+1 FEC, cap 90,000 B (`P6a`), cushion 12/17 (`P9`),
redundancy 2/4 (`P10`); the live ladder's top 7000; the PS1 source 1920×1080 at 4x (C5-M4A). The D-BASE close-out table
(`evidence/D_BASE_CLOSEOUT_2026-09-23.md`) must stay met; the E4 reference: idle 1.2 % CPU / 5.3 W, PS1 10.9 % / 20.1 W.

**ABSENT:** Live TV, browser / camera sources, NES / Genesis coverage, a power meter.

## Next Action

1. **The user's commit** of HOME-4+ (`logs/home4_git_status.txt`), and the two chooser questions (a 1-player game:
   chooser or skip; a multitap pick: relaunch at once or from the next start).
2. **B: H0 import slice 1a** (B45's design), after the user's four answers: a real BIOS or OpenBIOS for PS1; `.m3u` for
   multi-disc or refuse; a "NEW" tag; hide PS1 `.iso`.
3. **Open:** PS2 save states through PINE (the user's yes, later; tonight's requirement: PS2 saving like PS1 — then
   C12 and G-A14 again); the drive read-ahead; the loss guard's return (G-A8 prepared).

**Open, not blocking** — the full list is `docs/KNOWN_ISSUES.md`'s open index: G8-S6 and G5-S2-L (`handoffs/QUEUE_2026-10-19N.md`,
never run); the nightly watch's nights not written up; the overlay-down local check never scored; the reconnect over
the overlay to read; the handheld (pending) and Steam / external compute (deferred); the client's 1–3-s output stalls;
the host-CPU band gate (CL-B2 R3); `privyhub-diag`'s session row 5 s past its 150-s bound in the G-A10 window.

## Success Criteria

Phase C: met (C7, `docs/ROADMAP.md`). **Phase E** (`docs/ROADMAP.md`):

- E1 froze the workload suite before any measurement.
- Every later change is measured with that suite
  (`architecture/E1_WORKLOAD_SUITE.md`) and against the D-BASE close-out
  table, which must stay met.
- No perceptual gate unless the user sets one.

**The G adoption rule** (G-A1 … G-A13): a line is adopted only on the user's word, after a pre-registered, hashed
confirmation window with every row met, through its own drop-in, with `--check` ok on the new count. An APK is
CONFIRMED only by its pre-registered rule (CL-B7 §6); otherwise the previous CONFIRMED goes back on.

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
- **C5 is closed** (C5-CLOSE, 2026-10-05): the rung and `remaster` not
  adopted, the 4x source adopted. Reopen only with a 1080p-detail source
  or a different client. **Phase C is closed.**
- **`C3.L3a` is closed** (four sessions, the user's reading): single
  transitions are not reliably noticed, ramps are. Do not re-run the gate;
  build to the decision. **C4 is closed** for Phase C (8+1 stays).
- **G-A6 is SHELVED** (CL-B13; B23's WAN thresholds built and off): reopen only with a remote-path signal that today's
  thresholds misfire (`evidence/CL_B13_RESTART_FAST_AND_WAN_CLASS_2026-10-25.md`).

## Relevant References

- G adoptions: `evidence/G_A1_…`, `G_A2_…`, `G_A3_…`, `G_A4_…`, `G_A5_…`, `G_A7_…`, `TRIP_PREP_2026-10-29.md` (G-A9),
  `G_A10_…_2026-11-02.md`, `G_A13_…_2026-11-07.md`, `G9_CHECKPOINT_2026-11-07.md`; `docs/REMOTE_TRUST.md`. Client / trip: `CL_B14_…` (`fcd924c2…`), `CL_B16_…`, `TRIP_R2_…`,
  `HOME_1_…`, `HOME_2_…`, `HOME_3_…`, `HOME_4_PLUS_…`, queue N's `B41_…` / `B42_…` / `B43_…` and `handoffs/SESSION_B_DONE_2026-11-06N.md`.
- Closers: `evidence/E4_CLOSEOUT_2026-10-15.md`, `E2_S1_…`, `E1_S1_…`, `C5_CLOSE_2026-10-05.md`,
  `D_BASE_CLOSEOUT_2026-09-23.md`; `architecture/E1_WORKLOAD_SUITE.md`.
- Indexes: `handoffs/README.md`, `patches/PATCH_INDEX.md`, `archive/INDEX.md`; `docs/ROADMAP.md`, `docs/KNOWN_ISSUES.md`,
  `docs/RUNBOOK.md`, `TOOLS.md`; history: `archive/current/CURRENT_HISTORY_2026-11-02.md`.
