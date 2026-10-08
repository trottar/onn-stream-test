---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: e553673
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE.** E1 FROZEN; E2 MEASURED; E3 ran queues A-C
(`bf2120c`, `ccee2f5`, `e553673`) and **E3-A2** (2026-10-07/08,
unattended), each change behind a flag, judged by a pre-hashed bar.
**Two E3 adoptions stand: the guide index (E3-S6A) and the Snes9x core
(E3-A2).** Nothing is committed since `e553673`.

| item | verdict | finding |
| --- | --- | --- |
| E3-S1 / S2 / S3 / S5 / S5B | INCONCLUSIVE / REJECTED ×4 | led to S6 and S5C |
| E3-S6 → S6A the guide index | **ADOPTED, stands** | companion ~34 MB in META |
| E3-S4 → **A2 Snes9x** | **ADOPTED, stands** | RetroArch 8.9 % of a core (bsnes 436-517); "Sure it ran smoothly" |
| E3-S5C → **A2 `frame_spin`** | ACCEPTED, then **REVERTED** | one valid run's underruns 24 > 20 on a noisy link |

- **ABSENT:** Live TV, browser / camera sources, NES / Genesis, a power meter.
- **Standing:** Phase C closed; `D-BASE` CLOSED; the `CL-B1` APK adopted.

## Current Work Item

**E3-A2 is done** (22:51Z → 01:05Z 10-08;
`evidence/E3_A2_FRAME_SPIN_AND_SNES9X_ADOPTION_2026-10-07.md`):

- `audio-pacing.conf` and `snes-core.conf` written (four lines); state
  checks extended, including `d7_regression.py` and
  `c3_l4_nft_night.py`; pre-registration hashed 22:54:47Z.
- **Snes9x STANDS** (SNES: RetroArch 8.9 %, host 8.05 %, 60 fps).
  **`frame_spin` REVERTED** (PS1 r2: 24 underruns > 20; the replacement
  14); its drop-in and names removed at 01:05Z.
- PS1 run 1 was invalid (a recovery pause, `controller_silence`) and was
  replaced under an addendum hashed before further data. The same check
  found pauses in E2's PS1-1080P r1 and E3-S1's control and CONC runs.
- META: the index holds (33.9 MB, 256/0); its guide clause failed high.

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
  last 2026-10-08 01:05Z (E3-A2's end); the previous
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
  - **The adopted environ is exactly three `PRIVYHUB_*`** (live, the
    index, Snes9x) in three drop-ins; the manager none. `tools/e1_suite.py`
    (`ADOPTED`), `e3_state.py`, `d7_regression.py` and
    `c3_l4_nft_night.py` (`ADOPTED_E3`) check it. Last restarted 01:05Z
    2026-10-08 (the `frame_spin` revert); checked 01:05:05Z: the three
    lines, no `e3_flag.conf`, no game, PS1 files identical, APK
    CONFIRMED.
  - The companion tree carries the live controller through `C3-L4-N2`,
    the C5 selector profiles (dormant), **the 1080p rung behind
    `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`** (C5-M5; entry 415 since
    C5-M5B; since C5-CLOSE its window skips non-PLAYING reports; absent =
    the closed ladder; NOT ADOPTED) and **the PS1 look behind
    `PRIVYHUB_PS1_LOOK`** (C5-M5B; absent or `4x` = nothing written; NOT
    ADOPTED). Both flags off and absent.
  - The other E3 flags' code is dormant (`TOOLS.md`, "The E3 flags"),
    each absent, including `=frame_spin` (reverted by E3-A2).
- **Link-drop recovery** RUNTIME VALIDATED on real loss (`R3`-`R3d`);
  recovery never loads into a live core (`R3c2`).
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); after a host reboot `adb connect <onn-address>:5555`.

## Next Action

1. **The user's commit** of E3-A2 (`logs/e3_a2_git_status.txt`).
2. **What E3 has left**, the user's pick, or E4:
   - the CONC grab's spawn share (E3-S1's and S6's remainder);
   - the node grabber's start-up (a precompiled grabber).
   Both untested as changes; or `frame_spin` again, with a control.
3. **E4** after that, with the suite re-run on the adopted state as its
   base.

**Open, not blocking:**

- the suite marks a run OK through a recovery pause; E3-A2's validity
  check found pauses in E2's PS1-1080P r1 and E3-S1's control / CONC runs;
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

- `evidence/E3_A2_FRAME_SPIN_AND_SNES9X_ADOPTION_2026-10-07.md`; `handoffs/QUEUE_2026-10-07.md` and its records `evidence/E3_S6A_…`, `E3_S5C_…`, `E3_S4_…_2026-10-07.md`; `TOOLS.md` (the index's and Snes9x's drop-ins, "The E3 flags").
- Earlier E3: `handoffs/QUEUE_2026-10-06.md`, `-06B.md`; `evidence/E3_S1…S6_*`.
- `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` (E2); `architecture/E1_WORKLOAD_SUITE.md` (the frozen suite); `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
- `evidence/C5_CLOSE_2026-10-05.md`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` — C5 and Phase C closed; `evidence/C7_D8_CHECKPOINT_2026-09-30.md`.
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the baseline table.
- `docs/ROADMAP.md` (the E3 status tables); `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `docs/KNOWN_ISSUES.md`; `evidence/RUNTIME_VALIDATION.md`; `patches/PATCH_INDEX.md`.
