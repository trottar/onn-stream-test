# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

Baseline commit `4e45a4f` (2026-09-30); nothing committed since.

## 2026-10-01 — `LINK-L1` MIXED; live adaptive bitrate ON BY DEFAULT (`C3-L4-D1`)

- **`LINK-L1`** (Part A, adaptive off): six pre-registered 20-min holds,
  one per local 4-hour block. **MIXED**: 3 of 6 meet loss < 10/min
  (37.27 / 4.25 / 15.19 / 3.16 / 7.54 / 16.78), and there is no time
  window. History since D-BASE: 16 of 36 meet. The air is as O1 left it.
  No conclusion is drawn; the levers are the user's
  (`../evidence/LINK_L1_LOSS_ROW_2026-10-01.md`).
- **`C3-L4-D1`** (Part B, the user's authorization 2026-09-30):
  - **Live is the default** through
    `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`.
    The companion's environ carries exactly
    `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, and the user manager none.
  - Kill switches: delete the drop-in (off), or the disable route
    (shadow, one session).
  - The 30-min hold on the default was SILENT.
  - The injection session acted as intended, but is NOT PASS AS
    PRE-REGISTERED on two clauses traced to the pre-registration and the
    harness's read timing.
  - `tools/c3_l4_nft_night.py` and `tools/d7_regression.py` accept the
    one name. **The evidence copies of older night scripts do not**: use
    the D1 pattern (`../TOOLS.md`).
  - Records: `../decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`,
    `../evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`.

## 2026-09-28 — `C3.L3a` closed; `C3.L4` authorized, single transition

Four pre-registered sessions pooled; the user's reading: **`C3.L4`
AUTHORIZED, one restart per adaptation event, straight to the target, the
existing hold-downs as spacing; ramps excluded; live build pending; no
live run before a fault-injection night with the user's `nft`**
(`../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`,
`../evidence/C3_L3A_R4_SESSION4_2026-09-28.md`). C4 closed (8+1 stays).
D7 complete (the user's rows reported fine). `CL-B1` ships in the next
adopted APK. **C5-M1: 1080p60 NOT CAPABLE (stream) at parity**; the
candidate stays behind `PRIVYHUB_NATIVE_PROFILE_ID`, never the default
(`../evidence/C5_M1_1080P60_PROFILE_2026-09-28.md`).

**`C3-L4-L1` (queue 2, same day): the `C3.L4` live mode is BUILT**, behind
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default.

- **Session A**, 30 min on a clean link: SILENT.
- **Session B**, an injected FALLBACK: the decrease path is proven (one
  transition 7000 → 5000, the blackout, the hold-down refusal). The
  increase path never fired: the 90-consecutive-clean rule is not
  reachable in attract mode, and that is the user's call.
- **Next**: the user's `nft` night, with the hand-step list in
  `../evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` §7.
- **`C5-M2`** was not started; the user queues it after the `nft` night.

The section below is the 2026-09-23 state, kept as written.

## READ FIRST — Phase C has resumed (2026-09-23)

**`D-BASE` is CLOSED: BASELINE MET** (`../evidence/D_BASE_CLOSEOUT_2026-09-23.md`).
Cold / warm on the adopted build: spikes 32.8 / 26.0 per min, fps 59.90 /
59.91, stale drops 1.1 / 0.8, video loss 8.7 / 8.4 (post-FEC), audio
underruns 17 / 14 per session; max output gap 163 / 110 ms — the
transport's one open row. The onn is not the ceiling.

**The active item is `C3.L3a` Part 2** (gameplay acceptance of the Linux
actuator). **Probe fixed and 2026-09-20 re-scored (`C3-L3A-P2R1`,
2026-09-23); the gate is not answered — the pre-registered rerun awaits the
user** (`../evidence/C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md`).
Then `C3.L4`, BLOCKED until then. **Smoke 2026-09-24 (`C3-L3A-P2R2`):**
settling and transition cost measured on the adopted build, picture 9/9/9 —
the ladder stands; not a gate observation
(`../evidence/C3_L3A_P2R2_SMOKE_SESSION_2026-09-24.md`). **Overnight soak
`C3.L3a-S1`** (n = 60 transitions, attract mode): restart gap median 186.5 ms,
lifecycle CLEAN, settling ≤ ~4 s; no-transition H2 also missed the video-loss
target (`../evidence/C3_L3A_S1_TRANSITION_SOAK_2026-09-24.md`). **Rerun session 1 of ≥ 4 recorded** (`C3-L3A-R1`, run `20260924_115810`, pooled; no verdict; an accidental BACK split its client session — `--finalize` now scores that; sessions 2-4 await the user; `../evidence/C3_L3A_R1_SESSION1_2026-09-24.md`). **Rerun session 2 recorded without its decoder report** (`C3-L3A-R2`: the companion rejected it at 32,057 > 32,000 characters and the client swallowed the 400; a 24-transition session is expected to exceed the cap every time, so it is the user's call before sessions 3-4; `../evidence/C3_L3A_R2_SESSION2_2026-09-24.md`, `docs/KNOWN_ISSUES.md`). **Cap raised, session 2 on the decoder axis** (`C3-L3A-R2B`: `MAX_REPORT_CHARS` 48,000 + a WARNING line on refusal, companion restarted through systemd 18:00:52Z, profile confirmed; session 2 finalized from the rebuilt report, 24 = 24, 10 of 11 transition marks behind a measured restart gap; cap runtime validation PENDING until session 3; `../evidence/C3_L3A_R2B_REPORT_CAP_2026-09-24.md`). **Rerun session 3 recorded, the cap RUNTIME VALIDATED** (`C3-L3A-R3`: 24-change report stored, 32,435 chars; W 5.0 jump 1/5, ramp 2/5, decoys 1/10 and 3/10; interim pooled 3 sessions jump 5/15, ramp 11/15, decoys 4/30 and 9/30, no verdict; session 4 awaits the user; `../evidence/C3_L3A_R3_SESSION3_2026-09-24.md`). **`C3.L4` shadow built and SILENT** (`C3-L4-S1`: flag `PRIVYHUB_ADAPTIVE_BITRATE_MODE` default off and unset; 4 healthy holds, 0 would-acts; live BLOCKED; `../evidence/C3_L4_S1_SHADOW_CONTROLLER_2026-09-24.md`). **`C3.L2`'s classification stands**:
Linux is `video_only_restart`, not authorized for automatic adaptation
during play — `C3.L4` has to answer it.

**Every Phase C change is measured against the close-out table** — the
baseline must stay met.

## The reference profile — three adopted fields, read before changing any

`native_game_720p60_reference` (`companion/native_stream_profiles.py`),
all `source: profile`, nothing in the environment, `any_override: false`:

- **`max_frame_size_bytes` 90,000** (`P6a`): the encoder's per-frame burst
  was the video loss. **`any_override: false` means "only the profile
  decided", not "no cap"**; `PRIVYHUB_ENC_MAX_FRAME_SIZE=0` runs uncapped.
  60 KB and VBV are measured alternatives, not rejected.
- **`audio_queue_target/capacity_packets` 12 / 17** (`P9`/`P9a`): **the
  capacity sets the running audio latency** (+34-38 ms over 3/8); the
  target is only the startup prefill.
- **`audio_redundancy_copies/offset_packets` 2 / 4** (`P10`): each audio
  datagram sent twice, 20 ms apart; the client de-duplicates by sequence
  first and a late copy fills its concealment slot in place.
  `lost_packets` = sequences never received.

Per-session overrides for comparison runs: `TOOLS.md`
(`systemctl --user set-environment …`, restart, `unset-environment`).

## Operating the host

- **The companion is the systemd user unit `privyhub-companion`** (`H3`):
  `systemctl --user restart privyhub-companion`, never `kill` + `nohup`;
  confirm the MainPID owns 8765. Its log is the journal.
- **Headless** (`H2`): the dummy plug is X `DisplayPort-1` = DRM
  `card0-DP-2`. adb after a host reboot: `adb connect <onn-address>:5555`.
- Sessions from a host shell: `MainActivity`, wake, tap RESUME PLAYING;
  BACK ends the stream and posts the report (`TOOLS.md`).
- **The warm state**: from cold, the path drops single packets from ~7
  min (onn cpu-thermal ≈ 67 °C) until ~30 min idle — compare arms
  **interleaved**, never in one block. `t2_sample.py` (host+onn+Opal,
  10 s) and `t3_host_sample.py` are the samplers.
- **The session harness**: `../evidence/d_base_p9_2026-09-23/p9_run.sh`.

## Still open, not blocking

Max output gap (transport); the warm-state loss's cause between the ends
(`host_link`); the synthetic UDP pathology (PAUSED, `M1`); thermal
threshold proposals (the user's). `D-BASE`'s full history:
`../MEMORY.md` (curated) and one evidence record per item
(`../evidence/RUNTIME_VALIDATION.md`).
