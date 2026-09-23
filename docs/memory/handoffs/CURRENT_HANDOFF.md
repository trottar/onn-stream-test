# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

## READ FIRST — Phase C has resumed (2026-09-23)

**`D-BASE` is CLOSED: BASELINE MET** (`../evidence/D_BASE_CLOSEOUT_2026-09-23.md`).
Cold / warm on the adopted build: spikes 32.8 / 26.0 per min, fps 59.90 /
59.91, stale drops 1.1 / 0.8, video loss 8.7 / 8.4 (post-FEC), audio
underruns 17 / 14 per session; max output gap 163 / 110 ms — the
transport's one open row. The onn is not the ceiling.

**The active item is `C3.L3a` Part 2** (gameplay acceptance of the Linux
actuator). **Fix the probe's three recorded defects before any rerun**
(`../investigations/BASELINE_STREAM_HEALTH.md`, "Suspended, not failed"),
re-score the retained 2026-09-20 marks
(`logs/streaming/c3_l3a_gameplay_acceptance_state.json`) without
replaying, then decide. Then `C3.L4`. **`C3.L2`'s classification stands**:
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
