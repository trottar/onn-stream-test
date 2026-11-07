---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: d9fd9688 (queue N; HOME-3 uncommitted beside it; the user commits)
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename. The history to 2026-11-03 is in
`archive/current/CURRENT_HISTORY_2026-11-02.md` (verbatim, newest first).

## Active Objective

**Phase E ACTIVE** (E1 FROZEN, E2 MEASURED, E3 CLOSED, E4 CLOSED host side); **the G track (remote play) is under way.**
The adopted environ is **FOURTEEN lines**. The fourteenth is G-A10, `PRIVYHUB_STEP_IN_PLACE=1`, adopted on the user's
"Adopt" of 2026-11-02 (`evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`). HOME-2 (2026-11-06) confirmed queue M.
**HOME-3 (2026-11-07) put queue N's APK on the onn: C1'' and C4'' MET with no property, C6 (the prompt) NOT MET, C5''
(b) MET and (a) met on behaviour with two rows short; `8ba4d996…` CONFIRMED**
(`evidence/HOME_3_DEFAULTS_PROMPT_VOD_2026-11-06.md`).

## Current Work Item

- **HOME-3 is done, uncommitted** (session A, 2026-11-07). The user commits, then answers G-A13 and B45's four
  questions (Next Action). C6 goes back to B.

## Verified State

**The fourteen adopted lines.** Each one is its own drop-in under
`~/.config/systemd/user/privyhub-companion.service.d/`. `tools/e1_suite.py` `ADOPTED` lists the same fourteen, and
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

Records under `evidence/`. Line 10 implies the input hold, B6, B8, the `state` path, the stall signal and resume (B33
live inside it); line 13 acts only on a remote-class session (floor start and climb, remote ladder, 7000 cap, WAN
telemetry; the LAN as before); line 14 splices each ladder step onto the same stream at one IDR (2-s fallback).
**The off switch, every line:** delete its drop-in, `systemctl --user daemon-reload`, restart the companion, and take
the name out of `tools/e1_suite.py` `ADOPTED`. Each record names its exceptions; `docs/REMOTE_TRUST.md` has the G lines.

**The client.**
- APK **`8ba4d996…` is CONFIRMED** on the onn (HOME-3; queue N: queue M + B41 + B42 + B43, B27 / B29 out;
  `home3_installed/`), pinned in the three places. The hold and stable slots are on by default (G-A11 / G-A12; `0` /
  `off` turn them off); the player prompt and the movie retry are in it, off.
- `0132b944…` (HOME-2, the previous CONFIRMED) is kept in `home2_installed/`; `fcd924c2…` in `cl_b14_installed/`.
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
- Client flags `player_prompt` (B41; C6 not met) and `vod_retry` (B35 / B43; C5'' (b) met, (a) two rows short).
- Host per-run flags `PRIVYHUB_VOD_LOG` (B35) and `PRIVYHUB_VOD_DROP_TEST` (B40 / B43, never adopted).
- `PRIVYHUB_WAN_ADAPTATION` (G5-S2; its live smoke G5-S2-L never ran) and `PRIVYHUB_ENCODER_RC` (G8-S4).
- The 1080p rung (`PRIVYHUB_ADAPTIVE_BITRATE_TOP`) and `PRIVYHUB_PS1_LOOK` (C5).
- The dormant E3 / E4 flags (`TOOLS.md`).

**Profile** `native_game_720p60_reference`: 1280x720@60, GOP 15, 8+1 FEC, cap 90,000 B (`P6a`), cushion 12/17 (`P9`),
redundancy 2/4 (`P10`); the live ladder's top 7000; the PS1 source 1920×1080 at 4x (C5-M4A). The D-BASE close-out table
(`evidence/D_BASE_CLOSEOUT_2026-09-23.md`) must stay met; the E4 reference: idle 1.2 % CPU / 5.3 W, PS1 10.9 % / 20.1 W.

**ABSENT:** Live TV, browser / camera sources, NES / Genesis coverage, a power meter.

## Next Action

1. **The user's commit** of HOME-3 (`logs/home3_git_status.txt`).
2. **The user's question** (nothing adopted until answered): **G-A13 (C5'')**: "Turn the movie retry on by default
   (`debug.privyhub.vod_retry`) and adopt `PRIVYHUB_VOD_LOG=1`? A dropped movie, or a hub restart, then reconnects and
   resumes by itself." Disclosed: two of (a)'s rows short (the record). The prompt's default is not asked.
3. **A next: the G9 checkpoint** (apply `handoffs/G9_CHECKPOINT_DRAFT_2026-11-06.md` to ROADMAP §G9 and here; the
   overlay-down local check and the clean checkpoint commit are the user's).
4. **B next: H0 slice 1a** (PS1 inspect + dry run + manifest; `architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`),
   after B45's four questions to the user: a real BIOS or OpenBIOS; an `.m3u` for multi-disc titles or refuse; a "NEW"
   tag; hide PS1 `.iso`. Also to B: C6 and two VOD items (the record's reading).
5. **Later:** the loss guard's return (G-A8 is the prepared candidate).

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

**The G adoption rule** (G-A1 … G-A10): a line is adopted only on the user's word, after a pre-registered, hashed
confirmation window with every row met, through its own drop-in, with `--check` ok on the new count. An APK is
CONFIRMED only by its pre-registered rule (CL-B7 §6); otherwise `fcd924c2…` goes back on.

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
  `G_A10_…_2026-11-02.md`; `docs/REMOTE_TRUST.md`. Client / trip: `CL_B14_…` (`fcd924c2…`), `CL_B16_…`, `TRIP_R2_…`,
  `HOME_1_…`, `HOME_2_…`, `HOME_3_…`, queue N's `B41_…` / `B42_…` / `B43_…` and `handoffs/SESSION_B_DONE_2026-11-06N.md`.
- Closers: `evidence/E4_CLOSEOUT_2026-10-15.md`, `E2_S1_…`, `E1_S1_…`, `C5_CLOSE_2026-10-05.md`,
  `D_BASE_CLOSEOUT_2026-09-23.md`; `architecture/E1_WORKLOAD_SUITE.md`.
- Indexes: `handoffs/README.md`, `patches/PATCH_INDEX.md`, `archive/INDEX.md`; `docs/ROADMAP.md`, `docs/KNOWN_ISSUES.md`,
  `docs/RUNBOOK.md`, `TOOLS.md`; history: `archive/current/CURRENT_HISTORY_2026-11-02.md`.
