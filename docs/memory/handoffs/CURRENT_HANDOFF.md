# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

Baseline commit `d9fdbdd` (E2-S1 committed). The E3 queue's work is not
committed (the user's commit: `../../../logs/e3_s5_git_status.txt`, the
last of `logs/e3_s1..s5_git_status.txt`).

## 2026-10-06 — `QUEUE_2026-10-06`: E3, all five items, unattended

Each task's change is behind its own flag. Every flag was absent at every
teardown and at the end; E2's final state was restored after each task
(08:06Z, APK CONFIRMED). **Nothing accepted, adopted or committed.**

| # | item | the one change (flag) | verdict | the finding |
| --- | --- | --- | --- | --- |
| S1 | EPG grabs vs a live stream | grabber at SCHED_IDLE / nice 19 / idle I/O (`PRIVYHUB_EPG_GRAB_PRIORITY=idle`) | **INCONCLUSIVE** (the control 0.01 fps outside E1's band; a bad-link hour) | the core peak halved; **the loss peak at +1 s did not move**: not host CPU |
| S2 | the companion's memory after a grab | `malloc_trim(0)` after each refresh (`PRIVYHUB_EPG_MALLOC_TRIM=1`) | **REJECTED** (PSS 155 MB at the window's end) | the per-grab 25.6 MB metadata parse, live through each grab |
| S3 | the grabber's own cost | node started directly, no npm (`PRIVYHUB_EPG_DIRECT_NODE=1`) | **REJECTED** (3.3 CPU-s per grab vs 2.25) | the cost is the node grabber's own start-up; 4.9 CPU-s per grab |
| S4 | a lighter SNES core | `PRIVYHUB_SNES_CORE` (prepared, not applied) | **NOT RUN** | no snes9x core; the fetch was refused by the session's policy |
| S5 | streaming's fixed cost | audio sender: one timed wait per packet (`PRIVYHUB_AUDIO_SENDER_PACING=frame`) | **REJECTED** (run 1's loss 106.5/min > 3 × control) | sender 13 → 2.5 %, companion 25 → 15 %; run 2 passed |

- **New, untested hypotheses from the records:**
  - a cached, slim guide-metadata index, which may serve S2 and S1's loss
    peak (the GIL at each grab's start);
  - a precompiled grabber;
  - a remembered source per channel.
- **Next, the user's:**
  1. the commit;
  2. decisions from the records: no item is ACCEPTED, so nothing is
     offered for adoption. The open choices are S4 (fetch the core
     yourself; the look and the licence are yours), and a decisive
     re-run for S1 or S5 (a new pre-registration);
  3. E4 only after that.

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
