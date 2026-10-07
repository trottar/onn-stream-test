---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: bf2120c
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase E ACTIVE.** E1 FROZEN; E2 MEASURED; **E3 ran queue A (S1-S5,
committed `bf2120c`) and queue B (S5B, S6; 2026-10-06/07, unattended,
`handoffs/QUEUE_2026-10-06B.md`).** Each change sits behind its own flag
and was judged against a bar hashed before its runs. **One item is
ACCEPTED, and nothing is adopted or committed.**

| item | verdict | finding |
| --- | --- | --- |
| E3-S1 / S2 / S3 (grab priority, `malloc_trim`, direct node) | INCONCLUSIVE / REJECTED / REJECTED | led to S6 |
| E3-S4 lighter SNES core | NOT RUN | no snes9x core; the fetch was refused by the session's policy |
| E3-S5 / **S5B** audio sender pacing | REJECTED (S5B: F2 underruns 18 > 16) | loss **not** burstier; sender 13 → 2 % |
| **E3-S6 cached guide index** | **MEMORY ACCEPTED; STREAM REJECTED** | the parse alone reproduces the CONC peak; companion 34 MB / 0.2 % in META; CONC peak halved |

- **ABSENT** (unchanged): Live TV, the browser and camera sources, NES /
  Genesis, a power meter.
- **Standing:** Phase C closed (4x PS1 source adopted); `D-BASE` CLOSED;
  the `CL-B1` APK adopted.

## Current Work Item

**Queue B is done** (2026-10-06 23:23Z → 2026-10-07 03:55Z). The records:

- `evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_2026-10-06.md`:
  - five interleaved runs (C F C F F);
  - pooled loss median 10 vs 5 per minute, no minute > 100;
  - underruns 15 / 18 / 8 against controls 11 / 7, so REJECTED on F2;
  - the send trace: no gaps or bunches, only wider jitter.
- `evidence/E3_S6_GUIDE_INDEX_2026-10-07.md`:
  - **the probe located the CONC loss**: the 25.6 MB metadata parse
    (0.42 s of the companion's GIL) reproduces the +1 s peak at 318 × the
    baseline; the grabber child alone does 63 ×;
  - the index (13,555 channels, 3.7 MB, built once in 0.95 s, candidates
    identical): META companion 33.6 / 34.1 MB and 0.22 % CPU (E2: 161 MB,
    7.6 %);
  - CONC 773 / 1,273 loss/min, 58.65 / 57.64 fps, 10 underruns; the peak
    went from 56-65 to 21-28 lost/s.
- Flags absent at every teardown; their code is dormant (`TOOLS.md`,
  "The E3 flags"); the index file was removed. Redactor clean.

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
  last 2026-10-07 03:55Z (queue B's end); the previous
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
  - Last restarted 03:52Z 2026-10-07 by E3-S6's teardown; checked 03:55Z:
    environ the live default only, no `e3_flag.conf` drop-in, no game, the
    adopted PS1 files identical, APK CONFIRMED.
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

1. **The user's commit** of queue B (`logs/e3_s6_git_status.txt`; also
   `logs/e3_s5b_git_status.txt`).
2. **The user's adoption decisions, per ACCEPTED item:**
   - **E3-S6, memory half:** the drop-in line
     `Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`, in
     `~/.config/systemd/user/privyhub-companion.service.d/`, then
     `daemon-reload` and a restart. Revert: delete the line. Its stream
     half was REJECTED; adopting it still roughly halves the grab's hit
     on a live stream.
   - **E3-S4**, if the user fetches `snes9x_libretro.so` (the core is
     also a look; licence "Non-commercial").
3. **E4** only after the adoptions are settled and the suite is re-run on
   the adopted state.

**Open, not blocking:**

- E3: the grabber child's share of the CONC loss (a precompiled grabber;
  a remembered source per channel); S5B's underrun excess (one timed wait
  + a short final spin);
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

- `handoffs/QUEUE_2026-10-06B.md`, `evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_2026-10-06.md`, `evidence/E3_S6_GUIDE_INDEX_2026-10-07.md` — queue B's verdicts.
- `handoffs/QUEUE_2026-10-06.md` and the five E3 records (`evidence/E3_S1…S5_*_2026-10-06.md`) — E3's verdicts; `TOOLS.md` "The E3 flags".
- `evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md` — E2: the table, the reference numbers, the CONC / SNES / memory answers, the E3 list.
- `architecture/E1_WORKLOAD_SUITE.md` — the frozen E1 suite (Phase E's measurement base).
- `evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md` — E1-S1.
- `evidence/C5_CLOSE_2026-10-05.md`, `decisions/C5_1080P60_CAPABILITY_2026-09-28.md` — C5 and Phase C closed.
- `docs/ROADMAP.md` — Phase C CLOSED; Phase E with the E3 status tables.
- `evidence/C7_D8_CHECKPOINT_2026-09-30.md` — the checkpoint (appended 2026-10-05).
- `evidence/C5_M5_1080P_RUNG_2026-10-03.md` (the rung, not adopted); `evidence/LINK_L2_LOSS_ROW_2026-10-02.md` (the link).
- `evidence/D_BASE_CLOSEOUT_2026-09-23.md` — the baseline table.
- `handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `docs/KNOWN_ISSUES.md`.
- `evidence/RUNTIME_VALIDATION.md` — a classification per record;
  `patches/PATCH_INDEX.md` lists every patch record.
