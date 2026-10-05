---
memory_schema: 1
as_of: 2026-10-05
baseline_commit: 4493e68
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Phase C CLOSED, 2026-10-05** (C5-CLOSE, the user's decisions, "Yep
agreed"). **Phase E is next — E1 first (freeze the workload suite), NOT
STARTED; it starts on the user's word.**

- **C5 CLOSED**: the 1080p rung NOT ADOPTED (stays behind
  `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, off, for a 1080p-detail source);
  the `remaster` preset NOT ADOPTED (stays behind `PRIVYHUB_PS1_LOOK`);
  **the 4x PS1 source stays adopted** (C5-M4A).
- **The user's look, their words:** Look 1 (4x, 720p) and Look 3 (the
  same at the 1080p rung) *"looked the best, little difference between
  them"*; Look 2 (`remaster`) *"was the worst, a bit less smooth"*.
- **Look 3, repeated (C5-CLOSE-A):** the user's words *"Looked the same
  and loading the game still says 720"*. From the logs it **was at 1080p**:
  the entry acted 132 s after PLAYING, ~1.5 min at 1920×1080 / 12600,
  entry gap 329 ms (the first try was refused by the 60-s age guard). The
  user saw no difference from the 4x 720p stream; the decision's grounds
  include the look. The on-screen 720 is the client's constant
  (`NativeStreamActivity.kt:66-67`), cosmetic.
- **Phase C delivered**: explicit profiles (C1), the C2 telemetry
  contract, live adaptive bitrate on by default (`C3.L4` closed, validated
  under real loss), the FEC decision (C4: 8+1, adaptive deferred), 1080p60
  characterized and built as a rung behind its flag (C5), the source
  contract (C6), the Games regression (D7). C7: every row met or deferred
  but the commit (`docs/ROADMAP.md`, `evidence/C7_D8_CHECKPOINT_2026-09-30.md`).
- **Standing:** `D-BASE` CLOSED; `LINK-L1` (80 MHz) MIXED; `LINK-L2`
  (40 MHz) TIME OF DAY on the boundary; the `CL-B1` APK adopted.

## Current Work Item

**C5-CLOSE** (`handoffs/C5-CLOSE_PHASE_C_CLOSE_TASK.md`,
`QUEUE_2026-09-29B.md`'s rules): done; nothing else adopted; nothing
committed. Record: `evidence/C5_CLOSE_2026-10-05.md` (with the
C5-CLOSE-A addendum, read-only from the logs).

- **The rung-window rule**, behind the rung flag: reports while recovery
  is not PLAYING are skipped (skip, not reset). Tests 126/126, mutations
  22/22, stop rule 0 differences (448 series); S2b replayed: 451 entry
  decisions → 0; the injection check PASSES (`window_rule`,
  `skipped_not_playing` in the status).
- **The helper's `--attract`** fixed from the journal (the launcher drawn
  before the launch never refreshed; nothing tapped RESUME): now
  force-stop → start → tap the NOW PLAYING preview → confirm, else the
  exact TV steps. Fake-run 11/11; one real `4x --attract` dry pass to
  PLAYING and back. The plain route stays the default.
- C5's close: `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`; Phase C
  CLOSED in `docs/ROADMAP.md`; C7 checkpoint appended.

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
  last 2026-10-05 04:42Z (C5-CLOSE's final state); the previous
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
  - Last restarted 2026-10-05 04:32Z by the helper's `--attract` dry
    pass teardown (C5-CLOSE): manager none, environ the one name, live,
    7000 / 1280×720, `any_override` false, no game, the adopted PS1 files
    byte-identical, the shadow `d66211b3…`.
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

1. **The user's push**: `git push` (the PREPUSH audit reads **READY TO
   PUSH** for `origin/main..HEAD`, 11 commits:
   `evidence/PREPUSH_AUDIT_2026-10-05.md`). That completes C7's "clean
   checkpoint/push".
2. **The user's go for Phase E** — E1 first, the workload suite frozen
   (`docs/ROADMAP.md`, Phase E). Not started.

**Open, not blocking** (carried past Phase C):

- the max output gap (447 ms in D1; ≤ 100 on 0 of LINK-L2's six);
  `host_link`; the thermal flag; `CTRL-L1`; the slow-event ring;
- the mild step's ~120 s bound;
- **the onn's 1080p decode jitter** (~300-600 spikes ≥ 20 ms/min in every
  1080p hold): a client item for later; the overlay's constant size text
  (a later APK);
- `C6-D1`'s list; B3a's two clauses; C5-M4's R3 (no `codec_ms` in the C2
  telemetry); `encoder_command` is the full start's only;
- **adaptive-off measurements need the drop-in out** (`TOOLS.md`); old
  evidence night scripts misreport on default-live, so use the D1 pattern.

## Success Criteria

Phase C: met (C7, `docs/ROADMAP.md`), the commit pending. **Phase E**
(`docs/ROADMAP.md`): E1 freezes the workload suite before any
measurement; every later change is measured against it and against the
D-BASE close-out table, which must stay met. No perceptual gate unless the
user sets one.

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
