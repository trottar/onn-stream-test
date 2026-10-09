# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

Baseline commit `969085f` (E3-R1 / E3-S7 committed). Queue B's work is
not committed (the user's commit: `../../../logs/e3_s7b_git_status.txt`;
also `logs/e3_r2_git_status.txt`).

## 2026-10-08 (B) — `QUEUE_2026-10-08B`: E3-R2, E3-S7B, unattended

Both ran on the adopted state (live, the guide index, Snes9x), with
E3-A2's validity rule standing. Every task flag was absent at every
teardown; the adopted state held after each task (16:29Z, APK
CONFIRMED). **Nothing adopted or committed.**

| task | change (flag) | verdict | finding |
| --- | --- | --- | --- |
| R2 the false pause, fixed | the 5-s / two-check threshold + **an exit** for a `controller_silence` pause + a silence-gap log (`PRIVYHUB_RECOVERY_TRIGGER=v2`) | **REJECTED** (iii: CONC fps *above* its cross-night band; v: one gap 41 ms after a log write) | the replay, made faithful, held r1-r4; **no recovery pause in 4 runs**; a 1,253-ms uplink silence passed that today's rule pauses on. Adoption waits for the user's nft paste (record §4) |
| S7B the grab paced, shorter | `PRIVYHUB_EPG_GRAB_NET=paced` + `PRIVYHUB_EPG_GRAB_DELAY_MS=1500` | **REJECTED** (loss 309 / 346 per min; 59.33 fps; aligned 0-2 s 7.6 / 11.7) | today's request groups go back to back; at 1,500 the cycle holds (20-21 refreshes) but the cost per grab equals tonight's unpaced grab; only 4,000 cut it |

- Task 1's flag was absent from task 2's runs; all seven runs valid.
- **Next, the user's:** the commit; the nft paste for R2 (R2 §4);
  decisions on R2 and CONC (S7B §4); E4.

## 2026-10-08 (A) — `QUEUE_2026-10-08` (committed `969085f`)

R1 INCONCLUSIVE (the replay not faithful; v2 dormant); S7 REJECTED (the
cycle), with CONC loss 1,312 → ~60/min at `--delay=4000`.

## E3-A2 (committed `def1ad1`)

Snes9x adopted; `frame_spin` REVERTED. The validity rule was born there.

## Queues A, B, C (committed `bf2120c`, `ccee2f5`, `e553673`)

C (2026-10-07): S6A the guide index ADOPTED (stands); S5C `frame_spin`
and S4 Snes9x ACCEPTED (decided in E3-A2, above).
A (2026-10-06): S1 INCONCLUSIVE, S2 / S3 / S5 REJECTED, S4 NOT RUN. B:
S5B REJECTED (F2 underruns 18 > 16); S6 MEMORY ACCEPTED (adopted since,
S6A), STREAM REJECTED. Records `../evidence/E3_S*`; flags `../TOOLS.md`.

## Earlier (condensed 2026-10-06, E3 queue)

- **E2-S1** (2026-10-06): `../evidence/E2_S1_WHOLE_SYSTEM_2026-10-06.md`
  (the table, the answers, the reference numbers §6, the E3 list §8).
- **E1-S1** (2026-10-05): `../architecture/E1_WORKLOAD_SUITE.md`,
  `../evidence/E1_S1_WORKLOAD_SUITE_2026-10-05.md`.
- **C5-CLOSE** (2026-10-05): Phase C closed; the rung and `remaster` not
  adopted, the 4x source stays (`../evidence/C5_CLOSE_2026-10-05.md`).
- **2026-10-01**: the 4x source adopted, live adaptive bitrate on by
  default (`../2026-10-01.md`; reverts in `../TOOLS.md`).
- **2026-09-28**: `../2026-09-28.md`.

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
