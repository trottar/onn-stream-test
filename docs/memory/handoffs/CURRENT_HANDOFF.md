# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

Baseline commit `92e388e` (the user's Phase-G commit, 2026-10-16). Not committed since: G3-S3 (session B), G-A1
and CL-B3 (`../../../logs/g_a1_git_status.txt`, `../../../logs/cl_b3_git_status.txt`).

## 2026-10-16 (later) — session A: G-A1 adopted; CL-B3 (`G-A1_ADOPTION_AND_CL-B3_TASK.md`, uncommitted)

- Baseline `92e388e`. G3-S3 (session B) is uncommitted beside it and untouched.
- **G-A1: ADOPTED** (`../evidence/G_A1_OVERLAY_AND_IDENTITY_ADOPTION_2026-10-16.md`; patch
  `G-A1_OVERLAY_AND_IDENTITY_ADOPTED`):
  - `overlay.conf` (`PRIVYHUB_OVERLAY_PROVIDER=tailscale`) and `session-identity.conf`
    (`PRIVYHUB_SESSION_IDENTITY=v2`). The user wrote both by hand, after this session's write was refused by its
    permission check.
  - **Seven lines** read back. `e1_suite.ADOPTED` and the preflight have seven (e3_state reads them).
  - `/status` shows the overlay object (connected, `no-peer`); `/session/status` reads v2, 1 paired device.
  - The reverts are written in the record.
- **CL-B3: OPEN** (`../evidence/CL_B3_HARDENED_APK_LAN_2026-10-16.md`; patch `CL-B3_HARDENED_APK_HASH`):
  - APK `59f736d2…` installed and CONFIRMED. The pairing survived `-r`.
  - `identity_v2` on (the user, on the TV).
  - **R1** (10-min PS1-STREAM, seven lines, signed path): every host gate held.
    - Host CPU 11.57 %, at the 7000-7000 rung, reported only.
    - `sig_v` 2, `?port=48100` → 200 (the binding), no `legacy_setup`, `media_token_live` true.
  - **W** (G5-S1 smoke, `PRIVYHUB_WAN_TELEMETRY=1` per run): host gates held, and `wan` was live with eleven
    measures and a class per window. `/status` after was byte for byte equal except `server.pid`. **Two gates NOT
    MET:**
    - companion CPU +0.633 point (≤ 0.5), from two runs, not paired arms;
    - no `wan_sessions.jsonl` line (written only when a next session starts). The user decides.
  - **VOD: PASSED** (19:58Z, the user back home): `media_session` for the paired device, the header
    (`media_token_used` false), `lan`; the range server answered 200 / 206; the movie streamed (~1.3 Mbit/s). No
    `legacy-*` or `media-token-unknown`.
- End state: seven lines, no flag, no game; APK `59f736d2…` CONFIRMED; one paired device; `identity_v2` on, hub
  host empty.

## 2026-10-16 — session A: the watch's record; G1-S2; CL-B2 (`QUEUE_2026-10-16`, uncommitted)

- Baseline `3107fb5`. G1-S1 / G3-S1 / G3-S2 are uncommitted beside it and
  untouched.
- **E4-S4C** (`../evidence/E4_S4C_LINK_WATCH_2026-10-16.md`):
  - the watch was stopped after 6 probes, none clean (102-4,299 lost/min);
  - deferral INCONCLUSIVE (link);
  - the loss moved with the AP's retry %;
  - the two ends' signal disagrees by about 10 dB;
  - the LAN loss row is parked; the hand option is a wired adapter.
- **G1-S2** (`../evidence/G1_S2_OVERLAY_PROVIDER_LIVE_SMOKE_2026-10-16.md`):
  PASSED.
  - The overlay object appears behind the flag, at +0.28 point CPU and
    +0.55 MB.
  - With the flag off, `/status` is identical except `server.pid`.
  - Path `no-peer`, because no second tailnet device was online.
  - Not adopted; `overlay.conf` is written in the record.
- **CL-B2: CLOSED** (`../evidence/CL_B2_IDENTITY_APK_AND_LAN_SMOKE_2026-10-16.md`):
  - APK `77011eef…` is CONFIRMED (patch `CL-B2_IDENTITY_APK_HASH`) and
    **stays**: the user's decision, the only adoption.
  - G3 passed end to end on the LAN: pairing, signed setup and token, a
    20-min stream with every gate, a forged token → 401, an unpaired
    device → `unknown-device`, then re-paired (second sitting, 13:49Z).
  - Flag and setting off (R3, 13:54Z): the stream is today's, but **host
    CPU 12.963 % FAILED the 10.9 ± 2 band by 0.06**, recorded so.
    - Against R1, the encoder was 46.65 vs 35.75 % of a core, and the
      ladder held 7000 vs 5000-7000.
    - The E4-S1 reference and R2 also held 7000 at about 36 %, so the
      rung mix does not explain it, and the cause is not located (§2a).
    - The bar lesson is in `docs/KNOWN_ISSUES.md`.
  - Not adopted: `session-identity.conf` and the client setting are
    written in the record.
  - The G3-S3 follow-ups: the declared port (`audio_port` unsigned, the
    chosen target unobservable), the store directory's mode, and two
    setups per entry.
- End state: five lines, no flag; APK `77011eef…`; one paired device;
  `identity_v2` off.

## 2026-10-15 — session A: E4-S5D adopted; E4-S4D's watch launched (`QUEUE_2026-10-15`)

- **E4-S5D: the SNES capture fix ADOPTED and CONFIRMED.**
  - `snes-capture.conf` (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate`) is the
    fifth adopted line; `tools/e1_suite.py` `ADOPTED` has five names.
  - SNES 20 min: capture 59.964, dup+drop 0.05/min, RA 59.999, host 7.81 %.
  - PS1 10 min: 59.942, 0.10/min.
  - The link was very lossy (1,006 / 3,349 per min), reported only.
  - Revert: delete the drop-in, daemon-reload, restart, and take the line
    out of `ADOPTED`.
- **E4-S4D: the link watch is RUNNING detached**, as the unit
  `privyhub-link-watch`, launched 21:41:41Z, cap 2026-10-20T04:00Z.
  - Status: `cat ~/privyhub_link_watch/status.txt`.
  - Stop: `touch ~/privyhub_link_watch/STOP`.
  - Record: `../evidence/E4_S4D_LINK_WATCH_LAUNCH_2026-10-15.md`.
- Session B (E4-C1 close-out, E5-S1 capability probe) ran beside it.
  Its summary is in `SESSION_B_DONE_2026-10-15.md`.
- End state: five lines, no flag or constraint, APK CONFIRMED, the watch
  running.

## 2026-10-10 (B) — E4-S3B / S5B / S4B (`QUEUE_2026-10-10B`, uncommitted)

- **E4-S3B**: memory floor closed, swap off — META 1G; CONC OOM-killed at
  1G (before the window, ×2; INCONCLUSIVE as judged), 1536M PASS on a
  hashed addendum. **The stack 1.5G.** Runner: refresh back-off (patch).
- **E4-S5B**: the SNES fix outputs 60 on 4 / 4 bad probes; INCONCLUSIVE
  (the bench's null sink hides drops in both arms). Not adopted.
- **E4-S4B**: the clean-link gate failed 4 / 4 controls (loss 66-652/min);
  INCONCLUSIVE (link), no flagged run. Not adopted.
- Files for the user before the commit: E4-S3's two ~300 MB `epg.jsonl`,
  plus E4-S3B's 4.4 MB `backoff_demo/stopped_predecessor_5s.jsonl`.
- End state: four lines, no flag or constraint, APK CONFIRMED.

## 2026-10-10 — E4-S3 / S4 / S5 (`QUEUE_2026-10-10`, uncommitted)

- **E4-S3**: memory floor, swap off — streams ≤ 384M; CONC / META > 768M
  (grabber OOM). Stack floor between 768M and 1G.
- **E4-S4**: grab deferral (flag) works on the host (0 s throttled at
  150 %) but REJECTED on the link's stream quality.
- **E4-S5**: the SNES 59-fps fault LOCATED (probed `tbr`); the `-r 60`
  fix (flag) REJECTED on rendered fps, not exercised.
- Both flags dormant in the tree. Two ~300 MB `epg.jsonl` in
  `../evidence/e4_s3_2026-10-10/` (the user's call before commit).
- End state: four lines, no flag or constraint, APK CONFIRMED.

## 2026-10-09 (B) — E4: reference re-measured, floor measured (`QUEUE_2026-10-09`)

- **E4-S1**: the reference on the adopted state, 8 rows, all valid; drift
  from E2 by Snes9x and the index. Open: SNES capture at exactly 59 fps
  in some sessions.
- **E4-S2**: 30 runs. **CPU-time floor (not slow-core): the stack 400 %
  (CONC), PS1-STREAM 150 %, SNES / META ≤ 100 %; memory ≤ 1G.** Alpha:
  a proposal (§5).
- The runner writes a per-run `e4_constraint.conf`; the state check
  requires none (`../patches/E4-S2_…`). End state clean, APK CONFIRMED.

## 2026-10-09 (A) — recovery v2 ADOPTED (E3-A3B); **E3 CLOSED** (committed `7331184`)

E3-A3 adopted v2 and reverted it on its validity rule; E3-A3B re-adopted
it under a bar judged on its own trigger (0 controller pauses, 0 saves).
State: four lines, four drop-ins; kill switch in `../TOOLS.md`. cpu and
memory are delegated (not cpuset). The link was at its worst on 10-09.

## E3, before 10-09 (committed `75b2b6b` … `bf2120c`)

10-08 B: R2 REJECTED (two bar clauses), S7B REJECTED. 10-08 A: R1
INCONCLUSIVE, S7 REJECTED. E3-A2: Snes9x adopted, `frame_spin` REVERTED.
Queues A-C (10-06/07): S6A the index ADOPTED; S1 INCONCLUSIVE; S2, S3, S5,
S5B REJECTED. Records `../evidence/E3_*`; flags `../TOOLS.md`.

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
