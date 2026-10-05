---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: f60234e
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE since 2026-10-05** (the user's go: "let's start E1").
**E1 is FROZEN** (E1-S1). **E2 is next, on the user's word.** Phase C is
closed (C5-CLOSE, 2026-10-05).

- **The suite**: `architecture/E1_WORKLOAD_SUITE.md` (frozen; amended
  only by date).
  - One command: `tools/e1_suite.py` (a hashed pre-registration is
    required).
  - One sampler set: `tools/e1_sampler.py` (1 s).
- **The rows:** idle; PS1 local (no stream); SNES streamed; PS1 streamed
  (= the 720p60 reference); the 1080p rung (flag, not adopted); the EPG
  grab; PS1 streaming + EPG.
- **Dry runs** (2 × 5 min each): **6 of 7 REPEATABLE.**
  - **E1-CONC NOT YET REPEATABLE**: EPG grabs during the stream raise
    loss to ~2,300-2,800/min, rendered fps falls to ~54, and the ladder
    steps down to 5500.
  - The suspect is the Node grabber child; untested, for E2.
- **ABSENT, on the user's list:** Live TV (no unattended channel start),
  VOD (drive not attached), the browser and camera sources, NES and
  Genesis fixtures, a power meter.
- **Standing** (unchanged by E1): Phase C closed (4x PS1 source adopted;
  the rung and `remaster` not); `D-BASE` CLOSED; `LINK-L1` MIXED,
  `LINK-L2` TIME OF DAY; the `CL-B1` APK adopted.

## Current Work Item

**E1-S1** (`handoffs/E1-S1_WORKLOAD_SUITE_FREEZE_TASK.md`,
`QUEUE_2026-09-29B.md`'s rules) is done. Nothing optimized, adopted or
committed. Record: `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md` (files in
`evidence/e1_s1_2026-10-05/`).

- Inventory and pre-registration (hashed `244c203f…`) before any run.
- **Runner smoke** (not data) fixed three sampler defects before the
  runs (RetroArch's process is `AppRun`; re-key on exec; `gpu_metrics`
  units).
- **The suite** 06:35:54-08:40:55Z: 14 runs OK, 0 missed samples.
  `runs/repeatability.md`, `--check` OK, redactor 0 findings.
- **Findings, not acted on:** SNES (bsnes) ~4.2 cores, its stream 58.5-58.9
  fps; the companion's RSS 37 → ~172-211 MB after the first EPG grab; VCN
  activity unusable; RAPL root-only; `throttle_status` 0x800 (EDC_CPU).
- **Costs** (host CPU / socket W): idle 0.8 % / 4; PS1 local 5 % / 13;
  PS1 streamed 11 % / 19-20; 1080p rung 15-16 % / 23-27; SNES streamed
  41 % / 21-22.

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
**`C3.L3a-S1` transition soak** (2026-09-24): each bitrate-only restart costs
one gap, median 186.5 ms (128-225); a sized (rung) switch costs 287-649 ms
(C5-M5 / C5-M5B).

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
  last 2026-10-05 08:40Z (E1-S1's final state); the previous
  `f31b1c18…8ae7` is kept at `runtime/c4_m1/adopted_app-debug.apk` for
  rollback).
  - The companion is the systemd user unit `privyhub-companion` (`H3`);
    restart it with `systemctl --user restart`.
  - **Live adaptive bitrate by default, since 2026-10-01 13:07Z**
    (the ladder 5000-7000 at 720p), through the drop-in
    `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
    (`Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`). The unit file
    is unchanged.
    - The companion's environ carries exactly that one `PRIVYHUB_*`,
      and the user manager none.
    - `adaptive_bitrate.mode live`, `configured_mode live`, `acts true`.
    - Kill switches: delete the drop-in + `daemon-reload` + restart
      (off); `POST /plugins/games/adaptive-bitrate/disable` (shadow, one
      session).
  - Last restarted 08:40Z by E1-S1's teardown; checked 08:50Z: as
    above, 7000 / 1280×720, no game, the adopted PS1 files identical.
  - The companion tree carries the live controller through `C3-L4-N2`,
    the C5 selector profiles (dormant), **the 1080p rung behind
    `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`** (C5-M5; entry 415 since
    C5-M5B; since C5-CLOSE its window skips non-PLAYING reports; absent =
    the closed ladder; NOT ADOPTED) and **the PS1 look behind
    `PRIVYHUB_PS1_LOOK`** (C5-M5B; absent or `4x` = nothing written; NOT
    ADOPTED). Both flags off and absent.
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); after a host reboot `adb connect <onn-address>:5555`.

## Next Action

1. **The user's commit** of E1-S1 (`logs/e1_s1_git_status.txt`: the two
   tools, the suite document, the record and its files, memory). The
   push of the 11 earlier commits is the user's as before
   (`evidence/PREPUSH_AUDIT_2026-10-05.md`).
2. **The user's answers to the list**
   (`evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md` §5):
   NES / Genesis fixtures; a camera (none); a power meter (none); the VOD
   drive; Live TV (hand-tuned in E2, a later APK, or ABSENT); which
   concurrency pairs matter; whether the 1080p-rung row stays; optionally
   the metadata reconcile as a workload.
3. **E2, on the user's word**: whole-system measurements on the frozen
   suite at 20-min windows, with a new hashed pre-registration. E1-CONC's
   degradation is its first concurrency item.

**Open, not blocking** (carried past Phase C):

- the max output gap (447 ms in D1; ≤ 100 on 0 of LINK-L2's six);
- `host_link`; the thermal flag; `CTRL-L1`; the slow-event ring;
- the mild step's ~120 s bound;
- **the onn's 1080p decode jitter**: a client item for later; the
  overlay's constant size text (a later APK);
- `C6-D1`'s list; B3a's two clauses; C5-M4's R3 (no `codec_ms` in the C2
  telemetry); `encoder_command` is the full start's only;
- **adaptive-off measurements need the drop-in out** (`TOOLS.md`); old
  evidence night scripts misreport on default-live, so use the D1 pattern.

## Success Criteria

Phase C: met (C7, `docs/ROADMAP.md`). **Phase E** (`docs/ROADMAP.md`):

- E1 froze the workload suite before any measurement.
- Every later change is measured with that suite
  (`architecture/E1_WORKLOAD_SUITE.md`) and against the D-BASE close-out
  table, which must stay met.
- No perceptual gate unless the user sets one.

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

## Relevant References

- `architecture/E1_WORKLOAD_SUITE.md` — the frozen E1 suite (Phase E's measurement base).
- `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md` — E1-S1: the inventory, the dry-run table, sampler coverage, the user's list.
- `evidence/C5_CLOSE_2026-10-05.md` — the user's look, the rung-window rule, the `--attract` fix, C5 and Phase C closed.
- `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` — C5's decision record with its close.
- `docs/ROADMAP.md` — Phase C CLOSED, the C7 table; Phase E (E1 next).
- `evidence/C7_D8_CHECKPOINT_2026-09-30.md` — the checkpoint (appended 2026-10-05).
- `evidence/C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`, `evidence/C5_M5_1080P_RUNG_2026-10-03.md` — the rung (behind its flag; not adopted).
- `evidence/LINK_L2_LOSS_ROW_2026-10-02.md`; `evidence/LINK_L1_LOSS_ROW_2026-10-01.md` — the link.
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the baseline table.
- `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `docs/KNOWN_ISSUES.md`.
- `evidence/RUNTIME_VALIDATION.md` — a classification per record;
  `patches/PATCH_INDEX.md` lists all 143.
