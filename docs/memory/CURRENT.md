---
memory_schema: 1
as_of: 2026-10-15
baseline_commit: 7331184 (E4-S1..S5D, E4-C1, E5-S1 uncommitted; the user commits 2026-10-15)
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE. E4 is CLOSED on the host side (E4-C1, session B,
2026-10-15). The SNES capture fix is ADOPTED (E4-S5D, the fifth line). The
link watch (E4-S4D) runs detached until 2026-10-20T04:00Z. Next is E5-S2.**
E1 FROZEN; E2 MEASURED; E3 CLOSED. Nothing committed since `7331184`. The
user commits tonight.

- **The E4 floors and the alpha** are in
  `evidence/E4_CLOSEOUT_2026-10-15.md` (B).
  - Alpha today: ≥ 6 cores, 1.5 GB stack, 8 GB system.
  - With grab deferral: ≥ 4 cores, 1.25 GB.
  - VAAPI H.264 720p60.
  - Grab deferral is not adopted. Its verdict waits on a clean link: the
    watch.
- **Five adoptions stand:** the guide index, Snes9x, recovery v2 (E3),
  live adaptive (C), and the SNES capture fix (E4-S5D).
- **ABSENT:** Live TV, browser / camera sources, NES / Genesis, a power meter.
- **Standing:** Phase C, `D-BASE` closed; the `CL-B1` APK adopted.

## Current Work Item

**`QUEUE_2026-10-15` is done.** Two sessions ran side by side.

- **Session A (this):**
  - **E4-S5D, ADOPTED and CONFIRMED**
    (`evidence/E4_S5D_SNES_CAPTURE_FIX_ADOPTION_2026-10-15.md`):
    `snes-capture.conf`.
    - SNES 20 min: capture 59.964, dup+drop 0.05/min, RA 59.999, host
      7.81 %.
    - PS1 10 min: 59.942, 0.10/min.
    - Both SNES starts probed 60, so the bad-probe case rests on E4-S5C.
  - **E4-S4D, the watch LAUNCHED**
    (`evidence/E4_S4D_LINK_WATCH_LAUNCH_2026-10-15.md`): the unit
    `privyhub-link-watch`, from 21:41:41Z.
    - Probe 1 was dirty: 1,645 loss/min.
- **Session B** (`handoffs/SESSION_B_DONE_2026-10-15.md`, folded here):
  1. Session B finished on 2026-10-15 (E4-C1 + E5-S1). It adopted and
     committed nothing, touched none of A's files, and used no sudo, no
     nft, nothing fetched.
  2. It wrote `evidence/E4_CLOSEOUT_2026-10-15.md`: the reference, both
     floors final, the alpha in two columns with margins, adopted / not,
     the link, and E7's list.
  3. E4 is CLOSED on the host side. Alpha today ≥ 6 cores / 1.5 GB stack
     / 8 GB system; with deferral ≥ 4 cores / 1.25 GB; VAAPI H.264
     720p60.
  4. The link: 60 stream runs since 10-09, none under D-BASE's 10/min
     (min 34, median 218). The 10-10 stall is noted. The open item is the
     watch (E4-S4D).
  5. E4-S5D had no `state_at_end.json` at B's end (21:04Z), so B wrote it
     as "in adoption, session A". It is now adopted and confirmed.
  6. ROADMAP:
     - §E4 status, the final tables and a 10-10C/10-15 table (one link to
       the close-out);
     - §E7 items marked; the §E5 status line;
     - Phase E's header line was left alone (not B's section).
  7. It wrote `docs/CAPABILITY_MODEL.md` (seven classes; E4 thresholds;
     "not measured; E5-S2" where there are none) and
     `tools/capability_probe.py` (host reads, JSON, the threshold beside
     each verdict).
  8. The probe (21:03:43Z, with A's stream live) found the reference
     known-good on all seven classes. Storage, decode, NES and Genesis
     are unknown. The model needed no fix.
  9. Files: `evidence/E5_S1_CAPABILITY_PROBE_2026-10-15.md` +
     `e5_s1_2026-10-15/` (probe.json, console, redact_check all OK,
     manifest.sha256).
  10. Git status: `logs/e4_c1_git_status.txt`, `logs/e5_s1_git_status.txt`.
      The tree is dirty on purpose: B's new paths are untracked and
      ROADMAP is modified. B's next item: E5-S2 (a second machine, the
      alpha candidate).

Before it: `QUEUE_2026-10-10B` (E4-S3B, S5B, S4B) and `QUEUE_2026-10-10`
(E4-S3, S4, S5). `QUEUE_2026-10-10C`'s session stalled after its first
job (E4-S5C), and its watch never started.

## Verified State

**The E4 reference** (E4-S1, 20-min means): idle 1.2 % host CPU / 5.3 W;
PS1 streamed 10.9 % / 20.1 W (stack 95 % of a core, 354 MB); PS1 + grabs
21.4 % / 25.7 W (172 %, 856 MB); SNES 7.4 % / 15.2 W.

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
  last 2026-10-09 05:40Z (E3-A3B's end); the previous
  `f31b1c18…8ae7` is kept at `runtime/c4_m1/adopted_app-debug.apk` for
  rollback).
  - The companion is the systemd user unit `privyhub-companion` (`H3`);
    restart it with `systemctl --user restart`.
  - **Live adaptive bitrate by default, since 2026-10-01 13:07Z**
    (the ladder 5000-7000 at 720p), through the drop-in
    `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
    (`Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`). The unit file
    is unchanged.
    - `adaptive_bitrate.mode live`, `configured_mode live`, `acts true`.
    - Kill switches: delete the drop-in + `daemon-reload` + restart
      (off); `POST /plugins/games/adaptive-bitrate/disable` (shadow, one
      session).
  - **The cached guide index by default, since 2026-10-07 04:15:49Z
    (E3-S6A)**: its own drop-in `epg-index.conf` beside `adaptive.conf`
    (`Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`). Grabs read
    `data/epg/metadata/guides_index.json` (3,268,095 bytes at the end;
    rebuilt once per 24-h metadata refresh) instead of parsing the 25.6
    MB file. Kill switch: delete `epg-index.conf` + `daemon-reload` +
    restart, revert the state-check diff (`TOOLS.md`).
  - **The Snes9x core by default, since 2026-10-07 22:52:28Z (E3-A2)**:
    `snes-core.conf` (`Environment=PRIVYHUB_SNES_CORE=snes9x`); SNES
    runs on `snes9x_libretro.so` (Snes9x 1.63, `9b2b6ea9…7a31`, licence
    "Non-commercial"), not bsnes; `emulators.json` unchanged. Saves and
    states per core (`Snes9x/` vs `bsnes/`). Kill switch: delete
    `snes-core.conf` + `daemon-reload` + restart (`TOOLS.md`).
  - **Recovery v2 by default, since 2026-10-09 04:50:43Z (E3-A3B)**:
    `recovery.conf` (`Environment=PRIVYHUB_RECOVERY_TRIGGER=v2`). It
    gives the gap log (`logs/games/native_stream_ctrl_gaps.log`), the
    5-s two-check controller trigger, and the controller-return exit.
    Kill switch: delete `recovery.conf` + `daemon-reload` + restart,
    reverse the state-check diff (`TOOLS.md`, "Recovery v2").
  - **The SNES capture fix by default, since 2026-10-15 20:56Z
    (E4-S5D)**: `snes-capture.conf`
    (`Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`). The encoder's
    output rate is `-r 60`, not x11grab's probed `tbr`. Kill switch:
    delete `snes-capture.conf` + `daemon-reload` + restart, and take the
    line out of `tools/e1_suite.py` `ADOPTED`.
  - **The adopted environ is exactly five `PRIVYHUB_*`** (live, the
    index, Snes9x, recovery v2, output_rate) in **five drop-ins**
    (`adaptive.conf`, `epg-index.conf`, `snes-core.conf`, `recovery.conf`,
    `snes-capture.conf`). The manager has none. Last checked 2026-10-15
    21:36Z (E4-S5D's end, `state_at_end.json`).
    - `d7_regression.py` and `c3_l4_nft_night.py` (`ADOPTED_E3`) still
      list four lines. They were not run or changed here.
    - `tools/e1_suite.py` (`ADOPTED`, five) and `e3_state.py` check it.
      Since E4-S2 they also require no `e4_constraint.conf` (the per-run
      constraint drop-in).
    - On 10-15 the state was five lines, with no `e3_flag.conf` or
      `e4_constraint.conf`, no game, PS1 files identical, APK CONFIRMED.
  - The companion tree carries the live controller through `C3-L4-N2`,
    the C5 selector profiles (dormant), **the 1080p rung behind
    `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`** (C5-M5; entry 415 since
    C5-M5B; since C5-CLOSE its window skips non-PLAYING reports; absent =
    the closed ladder; NOT ADOPTED) and **the PS1 look behind
    `PRIVYHUB_PS1_LOOK`** (C5-M5B; absent or `4x` = nothing written; NOT
    ADOPTED). Both flags off and absent.
  - The other E3 flags' code is dormant and absent (`TOOLS.md`, "The E3
    flags"): `frame_spin`, `RECOVERY_GAP_LOG` (alone), `EPG_GRAB_NET=paced`
    + `EPG_GRAB_DELAY_MS` (S7, S7B), `GRAB_NONET`. **E4's, dormant and
    absent:** `PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1` (`epg.py`, E4-S4),
    (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate` is adopted since E4-S5D.)
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); after a host reboot `adb connect <onn-address>:5555`.

## Next Action

1. **The user's commit tonight (2026-10-15):** everything since `7331184`.
   - E4-S1 to E4-S5D, E4-C1, E5-S1, the runner patches;
   - the git status in `logs/e4_s4d_git_status.txt`.
   - Before it, the user decides what to do with E4-S3's two ~300 MB
     `epg.jsonl` and E4-S3B's 4.4 MB `stopped_predecessor_5s.jsonl`.
   - The watch keeps writing into `evidence/e4_s4d_2026-10-15/` while it
     runs, so its later files are not in tonight's commit.
2. **The watch's status:** `cat ~/privyhub_link_watch/status.txt`.
   - The line ends with a heartbeat at most 5 min old.
   - Stop it: `touch ~/privyhub_link_watch/STOP`.
   - Unit: `systemctl --user status privyhub-link-watch`.
   - It runs the deferral set on its own on the first clean probe.
3. **The watch's record when it ends** (the cap is 2026-10-20T04:00Z):
   a one-line Code task, "write E4-S4C's record from the watch's files".
   The record covers the link history and the deferral verdict.
4. **E5-S2**, as `docs/ROADMAP.md` has it: a second machine, the alpha
   candidate.

**Open, not blocking:**

- the SNES 59-fps fault is FIXED and adopted (E4-S5D); the sampler's first-to-last capture fps
  (E4 uses a segment-aware one); the pass rule's kill gates are
  window-scoped (E4-S3B's addendum reads the run span);

- the false pause: fixed and adopted (v2); the client's own 1-3-s
  output stalls stay open; **the link lossy since 10-09** (a LINK
  item, `docs/KNOWN_ISSUES.md`; 10-10: 39-863 loss/min, 0 of 4 clean
  controls): use same-night controls;
- the max output gap; `host_link`; the thermal flag; `CTRL-L1`; the
  slow-event ring; the mild step's ~120 s bound;
- **the onn's 1080p decode jitter**; the overlay's constant size text;
- `C6-D1`'s list; B3a's two clauses; C5-M4's R3; `encoder_command` is the
  full start's only;
- **adaptive-off measurements need the drop-in out** (`TOOLS.md`).

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

- E4: `evidence/E4_S1_…`, `E4_S2_…` (10-09), `E4_S3_MEMORY_FLOOR_CLOSE_…`, `E4_S4_GRAB_DEFERRAL_…`, `E4_S5_SNES_CAPTURE_59FPS_…`, `E4_S3B_MEMORY_FLOOR_1G_SWAPOFF_…`, `E4_S5B_SNES_CAPTURE_PROBE_BENCH_…`, `E4_S4B_GRAB_DEFERRAL_CLEAN_LINK_…` (10-10); `handoffs/QUEUE_2026-10-09.md`, `QUEUE_2026-10-10.md`, `QUEUE_2026-10-10B.md`; `patches/E4-S2_…` … `E4-S5_…`, `E4-S3B_RUNNER_REFRESH_BACKOFF.md`.
- E3: `evidence/E3_A3B_…`, `E3_A3_…` (10-09), `E3_R2_…`, `E3_S7B_…`, `E3_R1_…`, `E3_S7_…` (10-08), `E3_A2_…`, `E3_S*`; `handoffs/QUEUE_2026-10-06.md` … `-08B`; `TOOLS.md` ("The E3 flags", the drop-ins).
- `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` (E2); `architecture/E1_WORKLOAD_SUITE.md` (the frozen suite); `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
- `evidence/C5_CLOSE_2026-10-05.md`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` — C5 and Phase C closed; `evidence/C7_D8_CHECKPOINT_2026-09-30.md`.
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the baseline table.
- `docs/ROADMAP.md` (the E3 status tables); `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `docs/KNOWN_ISSUES.md`; `evidence/RUNTIME_VALIDATION.md`; `patches/PATCH_INDEX.md`.
