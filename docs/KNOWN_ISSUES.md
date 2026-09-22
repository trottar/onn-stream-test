# Known issues and deferred work

<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 baseline stream health — open faults, corrected by Group A

The reference stream fails its own target. Original record:
`docs/memory/evidence/BASELINE_STREAM_HEALTH_2026-09-20.md` (47 sessions =
the newest 50 files). Full-corpus re-score, 128 sessions:
`docs/memory/evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`. Read the
first with the second.

- **Client receive-to-output latency.** `spike_20_ms` (>= 20 ms from
  access-unit completion to decoder output) median 2,535/min: 66 % of
  frames sit at 20-60 ms and are rendered, 5.5 % exceed 60 ms and are
  dropped by the client's stale policy, which is 3.5 of the 4.5 fps
  deficit. The decoder holds 2-3 frames during slow events (11-13 is a
  transient maximum). A1-live (2026-09-20) read the SPS on the wire: no
  B-frames, `max_num_reorder_frames 0`, `max_dec_frame_buffering 1`,
  `dpb_output_delay 0` on every frame. **The bitstream is not asking for the
  hold; the decoder is.** Client side. Status: **answered by `C3.L2c`,
  decision pending.** Three 130 s sessions on the unconditional
  `KEY_LOW_LATENCY` build (2026-09-20 evening) read 203/107/119 spikes per
  minute against a corpus median of 2,535, with 94.3-97.0 % of frames under
  20 ms and the client-side fps deficit down to 0.22-0.67 fps. **Kept by
  the user.** Record:
  `docs/memory/evidence/C3_L2C_DISTRIBUTION_2026-09-20.md`.
- **The 60 ms stale threshold — CHARACTERIZED 2026-09-20 (`D-BASE-P1`), no
  change recommended.** The clause above — "5.5 % exceed 60 ms and are
  dropped … 3.5 of the 4.5 fps deficit" — was measured **before** `C3.L2c`
  and is no longer true of the current build. Thirteen sessions at
  thresholds 60 / 90 / 120 / 200: at the default the policy discards 6, 17
  and 15 frames per ~97 s session, so recovering all of them would add
  **0.06-0.18 fps**, and the arm medians show no gain (59.65 / 59.56 /
  59.06 / 59.27, tracking received-AU fps). p50 and p90 of rendered-frame
  latency are <= 20 ms in every arm; only p99.9 moves (<= 40 ms → <= 120 ms),
  and rendered frames above 60 ms go 0.000 % → 0.279 %.
  `max_output_gap_ms` shows no trend. **The default already meets
  `rendered fps >= 59.5`.** Record:
  `docs/memory/evidence/D_BASE_P1_STALE_THRESHOLD_2026-09-20.md`; knob:
  `docs/memory/patches/D-BASE-P1_STALE_THRESHOLD_PROBE_KNOB.md`.
  Caveats that matter: thirteen idle attract sessions on a quiet link with
  zero resyncs, n = 3 per arm, and the interleave's fixed cycle order is
  confounded with the arm — so the `spike_20_ms` differences between arms
  are position, not threshold. **The decision is the user's; nothing was
  changed.**
- **Stall tail = transport outages + IDR wait.** Every stall over 1,000 ms
  in every epoch carries an outage-class sequence jump and an IDR wait,
  with the last frame held inside the codec meanwhile; pre-flatten stalls
  of 2,035 ms exist. The 2026-09-19 "regression" was a 21-session window
  artifact. Status: **owner Step 3 (transport).** The `C3.L2b` revert
  (Step 1) is withdrawn.
- **Thermal headroom on both ends — telemetry only, no threshold set
  (`D-BASE-T1`, 2026-09-21).** The host will be an always-on server and the
  eventual PS2 / GameCube work needs thermal headroom, so host and onn
  temperatures are now recorded in every session: the onn's
  `thermal_status`, `thermal_headroom` and `thermal_zones_c` in each
  heartbeat plus a `thermal` block in each report, and the host's through
  `tools/host_resource_sampler.py` and `host_thermal_c` on
  `native-stream-status`. **No threshold is set and nothing acts on the
  numbers.** A thermal pause on the recovery state machine is deferred with
  its reopen condition in
  `docs/memory/investigations/DEFERRED.md` ("Thermal pause on the link-drop
  recovery state machine"). Evidence:
  `docs/memory/evidence/D_BASE_T1_THERMAL_TELEMETRY_2026-09-21.md`.

- **RetroArch memory growth during play — CLOSED 2026-09-21
  (`D-BASE-S2`). It is not a leak.** `D-BASE-S1` measured +108 MB per
  30 minutes across four 30-minute sessions and could not say where it
  stopped. A 3-hour session says: it stops. Total growth **+119.9 MB**, of
  which **+110.2 MB is the first 30 minutes**; the last block was +4 kB.
  And it is **file-backed** — `RssFile` +113.6 MB against `RssAnon`
  **+6.2 MB over three hours** (~2.1 MB/h), `RssShmem` +88 kB, `VmSwap` 0
  throughout. That is the emulator's mapped ROM, core and assets becoming
  resident, which finishes, and is reclaimable under pressure;
  `MemAvailable` was *higher* at the end of the session (7,954,440 kB) than
  at the start (7,832,556 kB) against a MemTotal of 14.94 GiB. The
  companion plateaus the same way (+6.8 MB total, ~0.18 MB per 30 min after
  startup) and the encoder is flat (+0.5 MB, then nothing). **No action.**
  Evidence: `docs/memory/evidence/D_BASE_S2_THREE_HOUR_SESSION_2026-09-21.md`.

- ~~Native-stream log rotation is only synthetically tested~~ **RESOLVED
  2026-09-21 (`D-BASE-R5`): rotation has now run against real traffic and
  lost nothing.** The heartbeat log crossed 4 MiB **17.9 minutes into a
  20-minute session** and rotated to
  `stream_log_archive/native_stream_heartbeat.log.1` (4,194,628 bytes):
  sequence step **1** and elapsed step **2,007 ms** across the boundary —
  exactly one heartbeat interval, **no line lost**.
  **Growth is now ~819 KB/h, not ~453**, because `D-BASE-R5` took the
  heartbeat line from 276 to **465 bytes**; the log therefore fills 4 MiB
  in **~5.0 hours** of continuous streaming, not ~9. **Still untested: the
  archive family's retention limit**, which has not yet had to discard a
  rotated file.
  **A slicing trap comes with it:** anything that cuts this log by line
  offset breaks across a rotation — the file gets *shorter* than the
  offset and the slice comes back empty, which is what happened to
  `D-BASE-R5`'s own harness. Read the archive and the live log together
  and filter on a rising `elapsed_ms` run (`TOOLS.md`).

- **Audio underruns — CHARACTERIZED 2026-09-20 (`D-BASE-P2`).** The
  per-event timeline now exists (`audio.tick_series`) and it places the
  whole thing: **a median 98.7 % of a session's underruns occur in the
  first 3 seconds**, 80 % by 1,512 ms, ending the tick the audio queue
  first fills. `queue_depth` is **0** for every tick of the burst. It is
  over before the stabilization gate releases gameplay (median 5,757 ms)
  and it ends at the first real PCM write (median 1,800 ms), which is a
  median 1,013 ms *after* the first video frame.

  **So "113/min" is a fixed per-session burst divided by a short session,
  and "~17/min steady state" was the same artifact at a longer duration.**
  Across 177 sessions `underruns` is flat at 116-162 from the 0-40 s bucket
  to the 300 s+ bucket while `prolonged_starvation_events` and
  `concealed_underruns` scale ~20x with duration; Spearman
  `underruns_pm` against duration is **-0.725**. Steady-state underruns are
  2-12 per session and do not coincide with video slow events, so the
  "tracks decode pressure" reading is withdrawn — the correlation with
  `lost_packets` is 0.113 and with `avg_queue_residence_ms` **-0.414**
  (shallow queue, i.e. starvation).

  **`prolonged_starvation_events` is a second phenomenon**, not the same
  thing counted differently: absent from the burst, steady at 1-2 per 10 s
  afterwards, rho 0.195 against underruns. It is unexplained and deserves
  its own question.

  **The fix is implemented and works (`D-BASE-P2a`, 2026-09-21).**
  `playbackLoop` now holds the AudioTrack until the first real PCM packet
  is queued, bounded at 3,000 ms, after which the original behaviour
  resumes. `audio.underruns` per session: **0 / 6 / 21 / 20 / 3, median 6**
  against P2's median 207, with 0-3 in the first three seconds against
  ~204. `first_write_elapsed_ms` moved 7 ms at the median, so audio is not
  delayed — only the track's start. Records:
  `docs/memory/evidence/D_BASE_P2_AUDIO_UNDERRUN_BURST_2026-09-20.md`
  (where the burst is) and
  `docs/memory/evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md` (the
  fix); patches of the same names.

  Status: **RUNTIME VALIDATED 2026-09-21** by `D-BASE-P2b`
  (`docs/memory/evidence/D_BASE_P2B_STARVATION_SEPARATION_2026-09-21.md`),
  which closed both of P2a's open checks. Ten sessions, five matched pairs,
  strictly alternating against a build with the hold compiled out: that
  build measures `prolonged_starvation_events` **125-157, median 151** —
  the same band the fix was blamed for — pooled Spearman against run index
  is **-0.036** (no drift either), and the sign test puts hold-on above
  hold-off in only **3 of 5** pairs. `avg_queue_residence_ms` is 27.70 off
  against 27.62 on, so the shifted-queue mechanism P2a proposed is absent.
  Both arms clear the fps bar on a quiet link (median **59.53** off,
  **59.56** on). The underrun result replicated: median **276** off against
  **19** on.

  **`prolonged_starvation_events` itself is still unexplained** and is the
  surviving open question — a second phenomenon (`D-BASE-P2`), insensitive
  to the startup hold, with no run-order trend, varying session to session
  in a 125-157 band and not following video loss (1.9-23.7 per minute
  across the same ten sessions). Nobody has related it to anything
  audible.
- **Link type.** Host measured wired (`eno1`, `r8169`, no radio present) on
  2026-09-20; on 2026-09-15 it was a USB RTL8822BU radio. The onn's
  association is still unread. One wireless hop by role. Nothing per
  session records it. Status: **open** — implement the `host_link` field
  specified in the Group A record before the next transport comparison.

Two metric defects found by the re-score, both open:

- **`lost_packets` excludes every gap >= 128 packets.**
  `RtpH264Receiver.beginStreamResync` resets the sequence tracker without
  adding the jump to `lostPackets`. Post-`C3.L2b` corpus: 53,679 jump
  packets vs 23,521 counted (2.3x); corrected loss/min median 252 vs 120.
  Status: **fixed and runtime-confirmed 2026-09-20** (`D-BASE-R1`):
  `beginStreamResync` adds the jump to `lost_packets` and to a new
  `lost_packets_in_resyncs` field. Confirmed on the onn in
  `native_decoder_20260920_145024_777.json` (`lost_packets_in_resyncs` 493 =
  the sum of the session's three resync jumps; `lost_packets` 695 against a
  pre-fix 202) and carried by every session since. Record:
  `docs/memory/evidence/D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md`.
  Reports without the field: read loss as `lost_packets` + sum of
  `stream_discontinuities[].jump_packets`; reports with it: `lost_packets`
  already includes the jumps.
- ~~The worst ordinary-play slow event is evicted from the report~~
  **FIXED 2026-09-20 (`D-BASE-R4` item 2).** Two magnitude-ordered top-16
  lists now sit beside the two FIFO segments: `slow_events_top_gap` and
  `slow_events_top_latency`, same seven columns, with
  `slow_event_retained_top_gap` / `_top_latency` and their capacities. In
  all four validation reports the top-gap maximum equals
  `max_output_gap_ms` and the top-latency maximum equals
  `max_rx_to_decode_ms`; in one the worst event had already been evicted
  from the merged array and only the top list held it. Record:
  `docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`.
  The lists keep no union, so an event 17th worst on both axes is in
  neither.
- ~~A slow event is recorded only on receive-to-output latency >= 50 ms~~
  **FIXED 2026-09-20 (`D-BASE-R2` piece 1).** `drainOutputs` now also
  records when `outputGapMs >= 50`. Confirmed on three sessions: each one's
  `max_output_gap_ms` (276 / 744 / 474 ms) has its own row, every one
  ending on a frame with `rx_to_decode_ms` 10-18 and `codec_ms` 10-13 —
  rows the predecessor trigger could not produce. One session recorded
  `slow_event_retained_marked` **3** against its 3 resyncs, the first
  non-zero marked segment on a low-latency build, so the `C3.L2b` cycle
  window now protects something. Record:
  `docs/memory/evidence/D_BASE_R2_STALL_VISIBILITY_2026-09-20.md`.
  **This made the worst gap qualify, not survive** — both halves are now
  closed by `D-BASE-R4`: the retention item above (top-16 lists) and, for a
  gap that never ends at all, item 1 below. Keep the retention counters in
  the report; they are what makes an absence readable.
- ~~A gap that never ends is never recorded~~ **FIXED 2026-09-20
  (`D-BASE-R4` item 1).** `drainOutputs` only records when a frame comes
  out, so a terminal stall used to leave `max_output_gap_ms` at the last
  *completed* gap — `D-BASE-R3` F15 reported 135 ms for a 46 s stall. The
  client now checks the age since the last output on its 500 ms tick and
  again at report assembly, raises `max_output_gap_ms` to it, and emits
  `terminal_slow_event` (flagged `terminal: true`, with `-1` for
  receive-to-output, feed delay and codec time, which do not exist for a
  frame that never arrived) plus `output_age_at_end_ms`. Confirmed: a 70 s
  held stall reported both as 68,617 ms. The slot clears whenever a frame
  is output, so `terminal: true` never labels a gap that closed.
- ~~The native stream heartbeat log is append-only and is not rotated~~
  **FIXED 2026-09-20 (`D-BASE-R4` item 4).**
  `logs/games/native_stream_heartbeat.log` rotates at 4 MiB keeping 3, and
  `logs/games/native_stream_recovery.log` at 1 MiB keeping 3, into
  `logs/games/stream_log_archive/`. Rotation runs before the append, so the
  line that triggers it becomes the first line of the fresh file; a
  5,000-append run across 25 files lost no line and preserved ordering.
  `tools/diagnostic_retention.py` covers the archive through a new
  `stream_log_archive` family — **its policy SHA-256 is now
  `b13fbc32dbf7f46a4ca9321985ea2d410804c15b9faaf82c3f87dce8356971b5`, which
  an `--apply` run must quote.**
- **The launcher's game-session banner refreshes only on `onResume`.**
  `D-BASE-R2` piece 3 fixed what a *failed* poll does — it now clears the
  banner and says "Companion unreachable", and retires that notice when the
  companion answers again. It did not add a timer, so a launcher left in the
  foreground while the companion dies underneath it still shows a stale
  banner until the next resume. Status: **open by design**; a timer was not
  authorized.
- **Stopping the companion with a game active orphans RetroArch.** A
  restarted companion reports `active: false` and does not reclaim the
  running emulator. Seen twice on 2026-09-20 during the `D-BASE-R2`
  piece-3 checks; both were killed directly.
  `tools/recover_orphan_game_session.py` exists for the case where the
  session is worth recovering. Status: **open**, pre-existing.

Also open, from the `C3.L3a` Part 2 probe's first run — fix before any rerun:

- the mark-association window anchors on sequence start, so a ramp closes its
  window before it finishes and marks are lost;
- telemetry field paths were taken from a probe's output artifact rather than
  the endpoint, so settling was never measured;
- the picture rating used an unanchored 1-5 scale and silently rescaled 1-10
  answers.

The 2026-09-20 session's raw marks and per-cycle timings are retained in
`logs/streaming/c3_l3a_gameplay_acceptance_state.json` and can be re-scored
without replaying.
<!-- PRIVYHUB_BASELINE_STREAM_HEALTH:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:BEGIN -->
## 2026-09-16 current issue override

Current Phase-D blocker:
- **PS1 multiplayer / multitap parity on Linux** — active. Windows Phase A proved
  the intended Port-1 multitap behavior; Linux currently fails to reproduce it.
  Exact boundary is not yet classified.

Resolved/superseded:
- broad "Linux controller input is broken" — resolved for the tested paths by
  D-084/D-085 and runtime validated across three games / three input profiles;
- "native Games streaming host is Windows-specific" — superseded for Games by
  the current Linux X11/VAAPI/PulseAudio/uinput runtime.

Do not reopen the lower controller transport or D-pad mapping while debugging
multitap unless a fresh diagnostic contradicts the D-085 runtime acceptance.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L0 audit findings

Added by the `C3.L0` Linux actuator boundary audit. Neither item is fixed by
that work.

- **Linux host resource telemetry never starts.**
  `NativeStreamManager._host_telemetry.start()` is called only inside the
  Windows start path, gated on `_capture_process is not None`.
  `_start_linux_locked` never calls it, while `status()` still publishes a
  `host_telemetry` section, so the field reports an inactive profiler on every
  Linux session. The C2 telemetry contract is unaffected because its sender
  metrics come from the FEC relay `sendto()` boundary, which does run on Linux.
  Status: open, Phase E prerequisite. Does not block C3.

- **`_patches/` and `_probes/` are not covered by `.gitignore`.**
  Status: **RESOLVED 2026-09-18** by the STREAMLINE patch. `.gitignore` was
  deduplicated and now covers `_patches/`, `_probes/` and `Claude outputs/`
  explicitly, alongside the existing `privyhub_*` patterns. The directories
  themselves are left on disk; delete them when you want the space back.

- **Existing C3 probes cannot run on Linux.**
  `companion/diagnostics/c3_actuator_probe.py` and
  `companion/diagnostics/c3_fixed_bitrate_probe.py` require `_wgc_ready()`, an
  HWND capture target and `_build_ffmpeg_command`, and fail closed with
  `wgc_runtime_unavailable` before modifying anything. They are correct as
  written. Status: expected prototype limitation; resolved by the `C3.L1` Linux
  cycle implementation.
<!-- PRIVYHUB_C3_L0_AUDIT:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2a E1 diagnostic retention findings

Found by the `C3.L2a` E1 evidence pass. Record:
`docs/memory/evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.

- **The decoder session report's slow-event list was a 128-entry ring that
  discarded the actuator cycle.** In the `C3.L1R1` session it held 128 of 128
  and covered only the last 29.4 s of a 64.8 s session, so the row explaining
  `max_output_gap_ms` 287 was already gone. Any session with more than 128
  slow events after a cycle lost the cycle's evidence. Status: **code fix
  installed 2026-09-18 by `C3.L2b`** (`docs/memory/patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`)
  — segmented marked/recent retention plus `elapsed_ms`-anchored
  discontinuity and first-IDR-after-discontinuity lists. **Not yet
  runtime-confirmed**: no APK built with the real Android/Gradle toolchain has
  been installed on the onn device, and no actuator cycle has been run against
  it. `C3.L2a` itself stays open until that cycle runs and the new report
  fields are read. Diagnostic-only client work; no streaming constant changed.

- **The encoder swap is not visible in the native video host log tail.** The
  bundle carries the last 500 lines, which for the `C3.L1R1` session showed a
  single continuous frame counter with no restart banner while the receiver
  recorded one SSRC change. Status: open question for the probe source; either
  the replacement encoder does not write to that log or the swap fell outside
  the tail. Unaffected by `C3.L2b`.

- **Decoder time dominates the large output gaps on the onn client.**
  `output_gap_ms` tracks `codec_ms` one-to-one in ordinary play, reaching 238 ms
  with no actuator involved; 2,696 spikes at or above 20 ms against 3,847 queued
  frames; `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`.
  Status: open, unattributed. Enabling low-latency decode is `C3.L2c`, a
  separate production-behavior candidate, registered but not scheduled and
  not authorized; it was not folded into `C3.L2b`.
<!-- PRIVYHUB_C3_L2A_E1:KNOWN_ISSUES:END -->

Status as of 2026-09-11.

| Issue | Status | Blocks current Phase C work? | Resume / resolve when |
| --- | --- | --- | --- |
| Bidirectional UDP burst/gap distortion and duplication in the current test path | **RESOLVED on the Linux host path, 2026-09-22.** Mechanism: **frame-size tail → large-frame burst → wireless queue overflow.** `D-BASE-P6` proved it by intervention and `D-BASE-P6a` adopted the fix — `max_frame_size 90,000` is now a declared profile parameter, validated at **loss 249 against an uncapped 2,690-2,896**, zero ≥80-packet frames, bitrate/fps/CPU unchanged. **The Windows-era pathology is a separate deferred note and is NOT claimed resolved** | No | Windows path: replay after a representative Windows baseline. Linux path: closed |
| Native streaming host is Windows-specific | Expected prototype limitation | No | Phase D Linux migration |
| NES runtime coverage | No local A9 fixture | No | Representative NES fixture is available |
| Genesis runtime coverage | No local A9 fixture | No | Representative Genesis fixture is available |
| Android cleartext/exported diagnostics and companion network exposure without mature auth | Security/privacy debt | No for isolated prototype | Dedicated threat-model/auth/encryption/privacy work |
| WGC/FFmpeg/process-audio bootstrap is not fully portable | Portability debt | No | Phase D / clean-machine reproducibility work |
| Conventional automated CI is minimal | Engineering debt | No | Before productization / broader platform expansion |
| Large orchestration files | Maintainability debt | No | Dedicated refactor with its own validation objective |
| Remaining Live TV / EPG / guide polish | Planned product work | No | Phase F |
| Game Session banner latency | Low-priority polish | No | Dedicated measured latency investigation if prioritized |

Resolved items such as the historical `companion/games/` ignore defect,
four-player support, manual PS1 multitap, and Sunshine/Moonlight production
integration are not open issues.

## UDP transport: two separate entries

**Read this first.** What was one entry is now two, because the evidence
separated them on 2026-09-22.

### Entry 1 — the synthetic burst/gap/duplication pathology: PAUSED

**Symptom.** The Prototype 1 environment could transform nominally paced
UDP traffic into large arrival bursts/gaps and produce **same-stamp
duplicates**, reproduced by synthetic probes **without game load, in both
directions**.

**It is not a Windows-only artifact, and saying so would be wrong.**
`docs/memory/investigations/DEFERRED.md` ("Linux + home Opal + onn UDP
transport root cause", PAUSED after the D083 closeout) records that the
pathology **was replayed from a Linux sender and reproduced
bidirectionally while idle**, that a Linux-only sender implementation
cannot explain it, that `wlan0`/`wlan1`/`br-lan` capture points on the
Opal were **zero-record during confirmed traffic**, and that disabling
OpenWrt flow-offload did not repair it. Proprietary Siflower components
remain in the unresolved region. **D082 is the last valid router-boundary
measurement; D083/D083R1 are invalid as networking evidence.**

**What `D-BASE-B2` changed.** That replay ran on what was then called the
"representative Linux path" — but **the Windows PC was still in it**, a
fact not known when the wording was written. Since `B2` (2026-09-21) the
host is wired directly into the Opal. `B2` compared the two arms and could
**neither implicate nor exonerate** the PC: loss/min median fell only
**2.8x** where the pre-registration required an order of magnitude, the
loss stayed bursty (**4.46** packets per forward-gap event against 11.17),
and **the arms overlapped**, with three PC-path sessions quieter than
every Opal session. **Same-stamp duplication was never re-measured on the
wire** — `duplicate_highest_packets` is 0 in all 29 client reports of both
arms, which is the receiver's view, not the link's.

**So: the synthetic suite has never been replayed on the current
production topology**, and duplication in particular is untested there.
**Status: PAUSED, not resolved.** What would move it: replaying the
preserved synthetic suite on the post-`B2` `Linux + home Opal + onn` path,
or on a different representative router. Do not continue open-ended
router/vendor reverse engineering, and **do not tune product buffering,
bitrate, FEC or decoder thresholds to hide it.** Records:
`docs/memory/investigations/DEFERRED.md`,
`docs/memory/evidence/B2_HOST_ON_OPAL_2026-09-21.md`; full chronology
`investigations/2026-09-07-udp-transport.md`.

### Entry 2 — the in-session packet loss on the production path: RESOLVED

**This is a different fault from Entry 1** — measured under real game
load, on the post-`B2` topology, in the per-second loss counters rather
than in a synthetic probe. Entry 1's duplication signature does not appear
here at all: `late_or_reordered_packets` is **0 across 11 M packets**.

**Cause.** A per-frame micro-burst meeting the wireless hop. The CBR
encoder emits one frame in a hundred as an 80-plus-packet burst at line
rate; that burst overflows the access point's per-station queue; the client
records a forward gap. Established **by intervention, not inference**
(`D-BASE-P6`, 2026-09-21).

**Fix, adopted.** `max_frame_size_bytes = 90,000` is a declared field of
`native_game_720p60_reference` (`D-BASE-P6a`, 2026-09-22), in force with
nothing set in the environment. Loss falls **7-9x** with achieved bitrate,
fps, encoder CPU and GPU power unchanged.

**Residual, measured over three hours** (`D-BASE-S3`, 2026-09-22):
**5.4 losses/min**, 0 resyncs, 0 client socket drops, fps 59.96, hourly
totals trending down (380/340/253). **The residual tracks nothing** —
every Spearman under **0.08** across 1,080 ten-second and 180 per-minute
windows, and the bucketed loss table is flat where uncapped it rose
14-fold. **A tighter cap is not a lever; the loss column is closed at this
level.**

**Reopen conditions** (from `docs/memory/CURRENT.md`, "Do Not Reopen
Without New Evidence"): a sub-second airtime instrument; a driver whose
`tx failed` is independent of `tx retries`; or a moving `drops` column on
the client's socket. Absent one of those, do not re-derive this column.
**Do not revive** loss-as-`host_sent − client_received` (`D-BASE-P4`
measured it at 29x noise) — use the heartbeat's cumulative counters.

**One testing trap:** the driver's `max_frame_size` is a **target, not a
hard ceiling**. Frames land up to ~0.02 % over it. Check with a tolerance,
never `<= 90000` exactly.

### The chronology, 2026-09-21 onward

The subsections below are the investigation in order. **The last three are
the ones to read.**

### Current conclusion — updated 2026-09-21, the cause is identified

**Superseding the 2026-09-15 reading.** As originally written, this section
said the investigation did not establish which network component was at
fault, and listed endpoint Wi-Fi/driver/firmware behaviour, network-device
behaviour, offload/bridging/routing effects and RF scheduling as open
possibilities. **That list is now closed.**

**The cause is a per-frame micro-burst meeting the wireless hop**, and it
was established by intervention, not inference: capping the encoder's
largest frame removes the burst and **7-9x of the loss with it**
(`D-BASE-P6`).

| candidate | state |
| --- | --- |
| the Windows PC as sole cause | **excluded** as sole cause (`B2`); not exonerated |
| the host's send path | **excluded** — relay `send_errors` 0, host UDP `SndbufErrors` 0 (`P3`, `P5`) |
| the air / interference / contention | **excluded** — channel ~93 % idle, no Opal counter moves with the loss (`P4`, `O1`) |
| the Opal's forwarding | **excluded** — every interface `dropped`/`errors` constant 0 (`O1`) |
| the onn's receive path | **excluded** — its UDP socket dropped 0 of 4,349 (`P5`) |
| **a per-frame burst at the wireless hop** | **the cause** — correlated by `P5`, **demonstrated by `P6`** |

The loss is also **reproducible from stream position** rather than
environmental: the same attract loop loses in the same minutes across
sessions. The sections below are the chronology; **the last three are the
ones to read.**

### Which side of the Windows PC it lives on — measured 2026-09-21 (`D-BASE-B2`)

Until 2026-09-21 the host's Ethernet ran to the **Windows PC**, so every
session on disk was measured on host -> PC -> Opal -> onn — the same machine
whose burst/gap/duplication pathology this section records. `D-BASE-B2` moved
the host onto the production path (wired directly into the Opal, onn wireless,
one hop, gate-checked on the host) and re-measured.

**The pathology does not live wholly in the Windows PC.** With the PC out of
the path, across six attract-mode sessions:

- loss/min median **16.6** against the PC-path arm's **46.3** — a 2.8x fall,
  where the pre-registered reading required an **order of magnitude** to
  implicate the PC;
- loss is **still bursty**: **4.46 packets per forward-gap event** against
  11.17, where uniform independent loss would give ~1.0 and A2.2's own
  burstiness threshold is 1.5;
- forward-gap events **did not vanish** — 7 per session against 11.

**And the two arms overlap**: the PC-path arm spans 0.0-206.7 loss/min and
contains the whole Opal range of 7.0-24.1, with three PC-path sessions quieter
than every Opal session. Against a day-to-day swing of 12.6x in the Group A
medians, a 2.8x median shift is **not a verdict**. Every transport column did
move the same way at once (max forward gap 2.84x, max output gap 1.75x, spikes
1.82x) and the Opal arm is markedly tighter, so a real improvement is
plausible — but six sessions in one 17-minute window cannot separate it from a
quiet quarter of an hour.

**So: the burst shrank and stayed bursty. The Windows PC is neither
implicated nor exonerated, and this entry stays open.** Same-stamp
duplication was not re-measured on the wire; `duplicate_highest_packets` is 0
in all 29 client reports of both arms, which is the receiver's view, not the
link's.

Record: `docs/memory/evidence/B2_HOST_ON_OPAL_2026-09-21.md`.

### Is it the host's own send burst? Tested 2026-09-21 (`D-BASE-P3`)

The encoder emits a frame's packets back to back at line rate, so every
frame is a micro-burst into the wireless queue. A diagnostic sender pacer
in the FEC relay (`PRIVYHUB_FEC_PACING_US`, environment, **default off**)
spread each frame's packets instead, clamped so a frame is still out within
8 ms of its first packet arriving. Fifteen 120 s sessions, strictly
alternating with the companion restarted for each, 0 rejected.

**The account is neither confirmed nor dead.** Loss per minute fell in only
**3 of 5** pairs and the medians **1.72x**, short of the pre-registered 4
of 5 and 2x; packets per gap did fall in **4 of 5** and the median maximum
forward gap **halved, 16 → 8**; and **`spike_20_ms`/min rose in 5 of 5**,
+41 %, which the criterion forbids. At 400 µs the achieved spacing reaches
only 187.5 µs and loss fell in **0 of 2** pairs, so the effect does not
scale.

**Read that null with its bound.** Spacing is capped at
`8000 µs / packets-in-frame`, so a frame is clamped above **53 packets** at
150 µs; the mean frame is **15.85** and **11 %** exceed 53. **The large
frames this account blames are exactly the ones the budget refuses to
spread**, so pacing was tested hardest where it applies least. A stronger
test needs a larger frame budget, which costs latency and is a product
decision. Separately the unpaced arm swung **1.8-35.2 loss/min inside one
hour**, so five pairs cannot resolve a 1.7x effect against it.

**Nothing was adopted and the knob defaults to off.** Record:
`docs/memory/evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`.

### Is it the air? Tested 2026-09-21 (`D-BASE-P4`)

Radio telemetry read from the onn over adb beside seven sessions, no code
change. **The onn is on 5 GHz** — 5180 MHz, channel 36, 80 MHz, 802.11ac,
866 Mbps ceiling, supplicant `COMPLETED` and **never re-associated**.

**The radio does not move with the loss.** Loss/min swung **1.4 → 105, a
74x range**, while RSSI spanned **5 dB in total** across 639 three-second
samples with a median of **−66 in every session**, and **not one scan of any
kind** was logged inside any session window. At **n = 597** heartbeat ticks
in a 20-minute session the client's receive rate against RSSI gives
**rho = −0.022**, against Tx link speed **−0.001**; the 5 % of ticks more
than 10 % below median rate all sit at ordinary RSSI.

**What could not be tested, and it is the half that matters most here.**
This client exposes **no retry, failure, airtime or channel-occupancy
counter** — `tx_retry`, `tx_bad`, `bcnCnt`, `total_tx_retries`,
`total_tx_bad`, the `/proc/net/wireless` discard columns and missed-beacon
count are all identically 0, `noise` is −256, `channel_utilization_ratio` a
constant 15. **Signal strength, association, link rate and background
scanning are excluded as the cause. Interference and airtime contention are
not excluded — they are invisible from this device**, and settling them
needs the Opal side or a client that reports retries.

**The loss is episodic.** A 20-minute session lost **105/min at 14.89
packets per gap** against 3.0-7.0 in two-minute sessions with identical
radio readings — bigger bursts accumulating over longer observation. **Short
sessions sample this pathology badly**, which is the best available account
of the swing that has made every previous arm overlap.

**`D-BASE-R5` (2026-09-21) then made the series directly measurable** and
confirmed it at sixty times the resolution: inside one 20-minute session
the per-minute loss ran **0, 2, 4, 5, 7, 9, 72, 78, 87, 128, 146, 152, 159,
161, 203, 228, 230, 236, 303** — **0 to 303 per minute** with the RSSI
moving 2 dB and the link speed not moving at all. **Minute 6 lost 303
packets and minute 15 lost none, at the same RSSI and the same link
speed.** The per-minute series is now read straight from the heartbeat log
(`TOOLS.md`); the derived-from-counters approach `D-BASE-P4` abandoned is
not needed and should not be revived.

### And the Opal's own view? Read 2026-09-21 (`O1`) — still not the air

The access block is gone; the router was read **read-only** over `ssh opal`
beside two 20-minute sessions — 40 minutes, 269 sampling rounds, 1,196
heartbeats — and it gives the retry and airtime counters the onn cannot.

**Neither airtime nor the Opal's radio is implicated.** Client loss swung
**0-331/min** while every Opal reading stayed flat: channel utilization
**rho −0.434** per minute — *and on the wrong sign*, a busier channel going
with **less** loss — **−0.008** at 10 s, `tx retries` **+0.219**, and
`rx drop misc` plus **every** `dropped` and `errors` counter on `wlan1`,
`br-lan`, `eth0` and `eth0.1` **constant 0** for the whole 40 minutes. The
24 worst ten-second windows read **6.78 %** utilization against **6.94 %**
in the 141 windows that lost nothing at all. In absolute terms **the
channel is ~93 % idle while the game streams** (2.9-3.3 % idle, 6.9 % under
load), so sustained contention is not merely uncorrelated with the loss —
it is **not present**. Retries do run **10.2-11.3 %** of transmitted
packets at −70 dBm, and they do not track the loss.
**`iw dev sta0 link` and `iw dev sta1 link` both read `Not connected`**, so
the 5 GHz radio is not time-shared with a wifi uplink.

**And the loss is reproducible.** The per-minute loss series of two
sessions started three minutes apart agree at **Pearson 0.964** while their
totals differ:

```text
A  4  2 214  8 123 180 121  0  84  89 188 115 272 17 90 0 242 331 148  2
B 12 30 212  3  94 173 135  4 103  80 162 121 204  0 72 2 183 251 185 14
```

Each session relaunches the title, so the attract loop replays and **the
loss follows the replay**. **No wall-clock account — a neighbour, a
microwave, a scan, a thermal ramp — can produce a shape that repeats on
restart.**

### Which queue, then? Answered 2026-09-21 (`D-BASE-P5`)

Two queues were left standing: the AP's per-station wireless queue and the
onn's own receive path. `P5` put three instruments on one clock across two
more 20-minute sessions — **packets per frame** counted in the relay,
**the onn's `/proc/net/udp6` receive-queue `drops`** read over adb, and the
`D-BASE-R5` heartbeat loss counters.

**The onn's receive path is not the queue.** Its UDP socket discarded **0
datagrams in 40 minutes** — 0 of 4,349 lost packets, **0 of 240**
ten-second windows, on the video and the audio socket both. `rx_queue`
peaked at **480,512 bytes of a 2 MiB buffer**, a quarter used at its worst.
Below the socket, `wlan0` `rx_errors`, `rx_missed_errors`,
`rx_over_errors` and `rx_fifo_errors` are **all +0**, and device-wide UDP
`RcvbufErrors` moved **+1** in twenty minutes. **A larger client receive
buffer is not a fix** — ruled out rather than assumed.

**One counter on the onn looks like the answer and is not.** `wlan0
rx_dropped` advances **+36,988** over a session, **16.6x** the loss, but
does **not** track it — per minute Spearman **0.040**, Pearson **−0.123**,
ranging 203 to 8,154 against a loss range of 0 to 293, with every hardware
error counter beside it at zero. It is the ordinary Android
broadcast/multicast filter on a busy home network. **Never read it as
stream loss.**

**The loss tracks the frame-size tail.** Max packets per frame gives rho
**0.583** over 240 ten-second windows and **0.780** over 40 minutes;
`frames >= 80 packets` **0.569** and **0.779**; forward-gap events the
same. Meanwhile **frame rate and mean frame do not move at all** — 599-601
frames per 10 s, mean 12.96-14.20 packets — so nothing about the *volume*
of traffic changes. **Only the tail moves, and the loss moves with it.**

**The distribution**, ~72,600 frames a session at CBR 7000 kbps:

| | p50 | p90 | p99 | max | >= 40 pkt | >= 80 pkt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| session A | 11 | 29 | **82** | **207** | 3.99 % | 1.01 % |
| session B | 11 | 29 | **78** | **208** | 4.03 % | 1.00 % |

**The shape is the problem, not the rate.** A nineteen-fold spread between
the median frame and the p99, emitted back to back at line rate into a
wireless queue.

**So the mechanism is a per-frame micro-burst meeting the wireless hop** —
the AP's per-station queue or the air during the burst. It is **not
observed directly and cannot be on this AP**, whose `tx failed` is a copy
of `tx retries` (`O1`), so retry exhaustion is unreadable. The case is that
**everything else on the path now reports zero** and the one thing that
moves with the loss is how big the burst is. Three earlier results fall
into place: **`P3`'s bounded null** (its 8 ms budget clamps above 53
packets a frame — exactly this tail), **the audio/video split** (0.024 %
against 0.214 % on one radio in one second), and **the content-lock** (the
frame-size tail repeats across sessions at Pearson **0.996**, more tightly
than the loss at 0.890).

Records: `docs/memory/evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md`,
`O1_OPAL_AIR_VIEW_2026-09-21.md`,
`D_BASE_P4_AIR_TELEMETRY_2026-09-21.md`,
`D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`.

### Controlled 2026-09-21 (`D-BASE-P6`) — and that settles the cause

`P5` left a correlation: loss rises and falls with the count of large
frames. `P6` **intervened on that variable** across seven 20-minute arms
with baseline bookends, and the loss followed.

| arm | encoder | loss | ≥80-pkt frames | max frame | achieved kbps |
| --- | --- | ---: | ---: | ---: | ---: |
| A0 | default | 2,696 | 718 | 242,418 B | 6,928.9 |
| **A1** | **`-max_frame_size 90000`** | **311** | **0** | 89,996 B | 6,929.7 |
| A2 | `-max_frame_size 60000` | 299 | 0 | 60,092 B | 6,929.2 |
| B1 | `-bufsize 117k` (VBV) | 938 | 0 | 17,144 B | 6,931.3 |
| A0′ | default | 2,189 | 717 | 244,794 B | 6,930.0 |
| A1r2 | `-max_frame_size 90000` | 408 | 0 | 89,937 B | 6,929.7 |
| A0r2 | default | 2,896 | 734 | 247,170 B | 6,929.9 |

**8.7x and 7.1x on two independent pairs**, against a pre-registered bar of
2x. Forward gaps 306 → 105, maximum forward gap 61 → 13-27 packets, spikes
61.6 → 33-35 per minute, fps 59.58 → 59.88; audio loss falls too.

**The causal pattern, not just the totals.** Windows assigned to the bucket
of their largest frame:

| bucket | A0 loss/window | A0r2 | A1 | A1r2 | B1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| < 40 packets | 3.33 | 4.62 | 1.63 | 2.88 | **7.79** |
| 40-59 | 2.45 | 2.71 | 2.83 | 4.91 | — |
| 60-79 | 1.27 | 3.79 | 2.69 | 2.75 | — |
| **≥ 80** | **42.5** | **45.5** | *(none)* | *(none)* | *(none)* |

**In both baselines the ≥ 80 bucket carries 93-95 % of all loss at ~14x
the loss per window of anything below it.** Capping deletes that bucket
**while the small-frame buckets stay where they were** — which is the
bucket-specific evidence that distinguishes cause from coincidence.

**The knee was measured, not assumed.** Bucketing A0's windows by their
largest frame in bytes gives **1.2-4.2 loss/window up to 100 KB and 46.3
above it** — a step, not a slope. A1's cap was set just under it and A2's a
third lower.

**And it costs nothing this run can measure.** Achieved bitrate spans
**6,928.9-6,931.3 kbps across all seven arms** (0.03 %); encoder CPU
**26.6-26.9 %**; GPU power overlapping. A cap does not starve the stream,
it redistributes inside it.

**Two bounds on the finding.** The benefit **saturates** — A2 constrains a
third harder for no further gain (299 vs 311) — so the looser cap is the
better setting. And **conventional rate control is a different lever, not a
better one**: B1 flattened hardest of all (every frame 14-16 packets, its
per-0.5 s bitrate range 6,661-7,168 against the default's 64-15,792) yet
lost **3x more than the cap**, and it is **the only arm that raised loss in
windows that had none**. It trades the tail for a higher floor.

**Drift was flagged and survived.** The three baselines ran 2,696 / 2,189 /
2,896 — ±15 %, wider than expected — while their frame distributions stayed
near-identical (≥ 80: 718/717/734). The environment moved; the content did
not; each pair clears the bar against its own bookend.

Record: `docs/memory/evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`.

### Resolved on the Linux host path, 2026-09-22 (`D-BASE-P6a`)

**The user made the judgement and adopted the fix.** Having played the
capped arm for about a minute — **no stutters, "could barely tell it was
over the LAN"** (their words, 2026-09-22; a user-stated perceptual result,
not instrument evidence) — they decided to adopt.

**`max_frame_size_bytes = 90,000` is now a declared parameter of the
`native_game_720p60_reference` profile**, in force with nothing set in the
environment. Validated the same day: **loss 249** against an uncapped
2,690-2,896, **zero ≥ 80-packet frames**, max frame **89,874 bytes**,
bitrate **6,929.6 kbps**, fps **59.90**, zero resyncs, zero socket drops,
encoder CPU 26.6 %.

**The mechanism, stated once for the record:**

> **frame-size tail → large-frame burst → wireless queue overflow →
> forward gaps at the client.**

The encoder is CBR, so the *average* rate never moved; what moved was the
*shape*. One frame in a hundred was 80+ packets emitted back to back at
line rate, that burst overflowed the AP's per-station queue, and the client
saw it as a forward gap. Capping the frame bounds the burst. The encoder
spends the same bits — the cap only changes when it may spend them.

**Scope of this resolution.** It is the **Linux host path** only. The
Windows-era burst/gap/duplication pathology recorded at the top of this
section is a **separate deferred note** — measured on a different encoder,
a different capture path and a different machine — and **nothing here
claims it fixed**. The Linux fix is an `h264_vaapi` profile parameter; the
NVENC path ignores the field and logs that it does.

**The uncapped path remains available** — `PRIVYHUB_ENC_MAX_FRAME_SIZE=0`
runs with the flag absent — so the pre-fix behaviour can be reproduced for
comparison at any time without editing source.

**Measured alternatives, not chosen:** a 60,000-byte cap (ties on loss,
constrains a third harder) and VBV `-bufsize` at the one-frame budget
(smoothest bitrate, best spike rate, but 3x the loss and it raises loss in
windows that had none). Both stay reachable through the overrides.

Records: `docs/memory/evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`,
`D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`;
`docs/memory/decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

### The audio starvation counter, named 2026-09-22 (`D-BASE-P7`)

`audio.prolonged_starvation_events` was the last counter in the decoder
report whose meaning was unknown, and it was read as a fault because 32-76
a minute sounds like one. **It is an audio arrival-gap counter**: the code
latches it, so it increments **once per hole in the audio arrival stream
longer than ~15 ms**, never twice for the same hole. Episodes, not polls.

**It measures jitter, not loss** — rho **+0.684** against the per-tick
maximum audio inter-arrival gap over 596 ticks, **+0.020** against audio
loss, and a packet deficit averaging **+0.54 of ~400 expected**, i.e. no
packets missing, only late.

**The hole is periodic and it is not the sender's**: 93 % of ticks show a
largest gap of **50-69 ms**, while the host's audio pacer measures **5.0 ms
average, max 5.08**. The jitter appears between the host's socket and the
onn's, and the rate is therefore a property of the path — 75.9/min on the
old PC path, 32/min on the capped Opal path.

**Read it as a path-jitter rate, not a fault.** 32/min accompanied **4
actual underruns in 20 minutes**. The only client-side lever is a deeper
audio cushion — the queue target is **3 packets (15 ms)** against a p90
hole of **60 ms**, so absorbing it costs about **+45 ms of audio
latency** — and sender-side pacing is closed by measurement. Nothing was
changed and the counter was not renamed; the name is accurate.

**What is still open** is the cause of the 55-60 ms hole itself. `P7`'s
instrument records one maximum per 2 s tick, so it cannot locate the hole
within the tick or align it with the video burst, the AP's scheduling or a
client-side stall. Record:
`docs/memory/evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.

### Product decision

Do not encode this environment’s measured jitter/duplicate rate into product
buffering or transport architecture.

Preserve the diagnostics. After Phase D establishes the representative native
Linux baseline, replay the acceptance suite during Phase E Linux
resource/transport characterization unless the issue becomes a blocker sooner.

Full record: `investigations/2026-09-07-udp-transport.md`.

## 2026-09-22 open items after the baseline-stream-health chain

One line each; the record named is authoritative.

- **`D-BASE-R3b` — nftables loss injection, PARTLY RUN 2026-09-22.** The
  user drove `r3b_run.sh` by hand (the session classifier still refuses every
  `nft` write). **N3, N15 and N150 all PASS**, so `GIVE_UP_MS` and the
  `.state.recovery` save are now exercised under controlled loss, and N15
  reached the case no substitute fault could — an encoder restart that
  **succeeded while the fault was still dropping every packet**. **N05, N15b
  and E30 were not run**, so `R3` + `R3a` do **not** reach RUNTIME VALIDATED
  and `END_MS` stays unexercised. Record:
  `docs/memory/evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`.
  **Status: open — three of five required runs done.**

- **A recovery restart hides the outage from `lost_packets`.** `D-BASE-R3b`
  measured it: a 3 s outage with **no** restart counted **2 348** lost
  packets; 15 s and 150 s outages that **did** restart counted **22** and
  **40**, because the new ffmpeg brings a new SSRC and the client books the
  return as an `ssrc_change` (`jump_packets: 0`), not as loss. Every
  loss-per-minute figure in the `D-BASE` column therefore under-counts
  outages that triggered a restart; **`max_output_gap_ms` is the honest
  column for them.** **Status: open — the loss column needs this caveat
  applied.**

- **`R3b-D1` — a stream-stop leaves the game session live, and the launcher
  then cannot launch.** `native-stream-stop` pauses the game and keeps the
  session by design, so after the N150 run RetroArch stayed alive and paused.
  Launching the same title from the launcher resolved to `recovery-resume`,
  which loaded the state into the running process and reported **"Loaded"**
  while **no window opened**; no `POST /plugins/games/launch` was ever issued.
  Record: `docs/memory/evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
  **Status: open.**

- **`R3b-D2` — after a recovery-state load the picture cycles through about
  four frames.** The stream itself was clean (`lost_packets 0`,
  `sequence_resyncs 0`, 59.85 fps); the **source** looped. Measured by IDR-size
  dispersion: spread **3 686 B** against **52 923-74 242 B** for live gameplay
  and **0 B** for a frozen window — so neither a freeze nor gameplay. Starts
  within one second of the core being unpaused. Cause not resolved: either the
  load-while-paused ordering or Beetle PSX HW's state restore under GL
  hardware rendering. Needs a run to separate. **Status: open.**

- **The `.state.recovery` file survives being consumed.**
  `load_recovery_state` stages it as slot 0 and does not remove it, so the
  recovery prompt reappears on the next launch of that title. The Tekken 3
  pair is being kept deliberately as the evidence for `R3b-D1`/`R3b-D2`.
  **Status: open.**

- **`END_MS` (30 minutes) has never been exercised.** Recorded under
  "link-drop resilience — stated requirement, not yet owned" below.
  **Status: open.**

- **`audio.prolonged_starvation_events` is characterized, not a fault.**
  `D-BASE-P7` (2026-09-22) established it counts **one hole in the audio
  arrival stream longer than ~15 ms**, episodes not polls, and measures
  **jitter, not loss** (rho +0.684 against the arrival gap, +0.020 against
  audio loss; the packet deficit averages +0.54 of ~400, so nothing is
  missing, it is late). 32/min accompanied **4 actual underruns in 20
  minutes**. **Status: not a defect. What is open** is the cause of the
  55-60 ms hole itself, which `P7`'s one-maximum-per-2 s instrument cannot
  locate within a tick. The only client lever is a deeper cushion at about
  **+45 ms of audio latency**, which has not been spent. Record:
  `D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.

- **Thermal thresholds: deferred.** `D-BASE-T1` measured both ends — the
  host's hottest sensor rises 54 -> 60 °C over ten minutes and plateaus
  (`S3` confirms over three hours). **No threshold, no throttle response
  and no action on a thermal reading exists**, and none is authorized.
  **Status: deferred**, reopen with a sustained-load complaint.

- **`host_link` is specified but not implemented.** The session record has
  no field saying which link the host was on. **Status: open** — see the
  entry above at "implement the `host_link` field".

- **The onn reports no radio or thermal detail, and that is the device,
  not a gap in the search.** `D-BASE-P4`: **no retry, failure, airtime or
  channel-occupancy counter at all**. `D-BASE-T1`: **thermal status only**,
  no zones and no headroom, reading 0 (NONE) throughout. Every such field
  is recorded as an **absence, never a zero**. **Status: closed on this
  hardware**; reopen with a different device.

- **The Opal's SSH host key is RSA-only (Dropbear).** Noted in
  `docs/memory/TOOLS.md`. It constrains which client key types work
  against the router and is a **note, not an action item** — the Opal is
  read-only from this project and nothing is installed on it.

- **The Linux host has no SSH server and no autologin** (`H2-PREP`,
  2026-09-22). `openssh-server` is not installed and every `autologin-*`
  line in LightDM's config is commented out, so a reboot stops at the
  greeter with no X session and therefore no capture. Nothing starts the
  companion at boot and `Linger=no`. **Status: blocking the headless
  cutover (`H2`)**; both are user-side root writes. Record:
  `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`.

- **Adding a heartbeat field takes two edits.**
  `companion/plugins/games.py`'s `native-stream-heartbeat` handler carries
  an **explicit key whitelist** and drops unlisted keys **silently**, with
  no warning and an otherwise healthy heartbeat. `D-BASE-P7`'s first
  session recorded no audio fields at all because of it and had to be
  re-run. **Status: a documented trap, not a defect to fix** — the
  whitelist is deliberate.

## Runtime coverage gaps: NES and Genesis

NES and Genesis are configured/supported, and earlier user testing indicated
normal behavior, but the final A9 evidence did not have local fixtures for those
families.

Current durable status is therefore:

- NES — **not runtime validated**;
- Genesis — **not runtime validated**.

Do not infer validation from configuration or from another emulator family.
Upgrade status only after a normal launch/input/lifecycle regression with a real
fixture.

## Security/privacy debt

The isolated prototype still has security surfaces that require a dedicated
hardening phase:

- Android cleartext networking;
- exported diagnostic/probe activities;
- companion network listening without mature authentication;
- normal service logging that may contain operational requester information.

These should be handled together with a threat model, authentication,
encryption, authorization and privacy review. Do not mix ad-hoc security changes
into unrelated C1 streaming work.

## Windows/Linux portability debt

The current native path intentionally uses Windows-specific components,
including WGC, NVENC/FFmpeg integration, process-loopback audio and ViGEm.

Phase D owns Linux functional parity. Phase E owns representative Linux
resource/transport characterization. The current Windows implementation remains
the validated behavior reference until those phases execute.

## Maintainability / test debt

Large central files remain:

- Android `MainActivity.kt`;
- companion `games/emulator_manager.py`;
- companion `plugins/games.py`.

Minimal conventional CI also remains. Existing deterministic probes and runtime
evidence are strong, but they are not a substitute for future automated
multi-platform coverage.

Refactor only with a dedicated objective and explicit regression boundary.

<!-- PRIVYHUB_CLIENT_BANNER_RECONCILE:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 launcher banner does not reconcile when the companion is unreachable

`MainActivity.refreshGameSessionBanner()` clears the "NOW PLAYING" banner only
on a successful `/plugins/games/status` answer with `active: false`; on any
exception it logs and leaves the banner as it was. If the game is ended
host-side and the companion then goes away before the launcher resumes, the
onn keeps showing a paused game that no longer exists until the app is
relaunched or the companion comes back. Seen after the first autonomous
session on 2026-09-20. Status: **open, client UX, low priority** — the
operational rule (end the game via the client, stop the companion last) is
in `docs/memory/TOOLS.md`; a client fix would treat companion-unreachable as
"no active session" after a bounded retry, or poll status periodically while
the banner is visible.
<!-- PRIVYHUB_CLIENT_BANNER_RECONCILE:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_LINK_DROP_RESILIENCE:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 link-drop resilience — `D-BASE-R3` + `D-BASE-R3a`

**Status: built, installed, RUNTIME VALIDATED FOR THE SUBSTITUTE FAULT, and
as of 2026-09-22 exercised against real on-the-wire loss by `D-BASE-R3b` —
N3, N15 and N150 all PASS, but N05, N15b and E30 were not run, so the set the
handoff requires is incomplete and this is NOT yet RUNTIME VALIDATED for real
loss.** `D-BASE-R3b` record:
`docs/memory/evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`; two
post-run defects in
`docs/memory/evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`.
Records: `docs/memory/evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`
and `docs/memory/evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`.
Patches: `docs/memory/patches/D-BASE-R3_LINK_DROP_SELF_RECOVERY.md`,
`docs/memory/patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md`.
Design and constants:
`docs/memory/investigations/LINK_DROP_RECOVERY_DESIGN.md`.

The behaviour the user specified is in place: the host pauses the game on
desync, keeps restarting the encoder with backoff, resumes only after the
client passes the stabilization gate again, and after `GIVE_UP_MS` saves the
game to its own file and stays paused with the launcher saying so. Observed
constants: pause 1.3-1.7 s after the fault; give-up at 120.243 s against
120,000; backoff 5 / 10 / 20 / 30 / 30 s; recovery save
`<stem>.state.recovery`, never a slot.

**Both `D-BASE-R3` defects are FIXED by `D-BASE-R3a`** (2026-09-20,
`docs/memory/evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`,
`docs/memory/patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md`):

- ~~A failed encoder restart is terminal~~ **fixed.** When the session has
  no encoder the recovery now calls the same `NativeStreamManager.start()`
  `native-stream-start` uses instead of re-entering the `C3.L1` cycle, and
  logs `method: "full_start"`. Confirmed on two runs that the pre-fix build
  left stuck in `PAUSED_RECOVERING`.
- ~~The restart decision reads a heartbeat up to 2 s stale~~ **fixed.** It
  now needs the two newest heartbeats both at or above `DESYNC_MS` with the
  newer not lower, and the newer received at or after the restart became
  eligible; each line logs `age_pair_ms`. A 3 s outage records `restarts`
  **0** where the pre-fix build restarted every time.

**What is still open:**

- **The nftables runs are owed.** Every run so far used a substitute
  (SIGSTOP on the managed encoder) because this host has no
  non-interactive root (`sudo -n nft …` → "a password is required"). Loss,
  sequence jumps and FEC during an outage are therefore untested, and so is
  a `C3.L1` restart whose replacement encoder is alive but unheard. A
  passwordless `sudo nft` rule, or an equivalent, is the unblock.
- **The host-side controller-silence trigger is unexercised.** Every run was
  triggered by the client's own notice, because no host-side fault
  interrupts the client->host controller channel. Testing it needs the
  client stopped, not the link.
- **`END_MS` (30 minutes) was never exercised.**
- **Two of the plan's pass criteria are not reachable as written**, and
  `D-BASE-R3a` measured why: "resume within 2.5 s" is below the gate's
  baseline-plus-three-ticks 2.0 s floor plus encoder resume time, and
  "within one backoff interval" on a 15 s outage is dominated by
  `_kill_managed_process` waiting 5 s on a `SIGTERM` the *substitute*
  injector's stopped encoder cannot act on.

The original statement of the requirement, and the freeze that prompted it,
are preserved below.

---

## 2026-09-20 link-drop resilience — stated requirement, not yet owned

During the first play session on the `C3.L2c` build the stream froze once
(onn on a stale frame, host still running) and did not recover, coincident
with a house-network disturbance the user observed independently (chats
arriving out of order). Not attributed to the build: the only report from
that period (`native_decoder_20260920_173423_609.json`, 1,133 motion
events) scores like the attract sessions. Happened once.

**Requirement (user, 2026-09-20):** when the Linux host is a headless
server, a Wi-Fi drop must self-heal end to end — the client must detect a
dead stream, resync or restart it, the companion must keep or restore
session state, and the launcher must reflect reality — without anyone
accessing the host. Today none of that is automatic: a long outage leaves
the client frozen or on a stale banner and the fix is manual.

Pieces that exist: sequence/SSRC resync and IDR wait in `RtpH264Receiver`
(recovers from gaps that end), the actuator's encoder-only restart primitive
(`C3.L1`), `tools/recover_orphan_game_session.py` (host side). Pieces that do
not: a client-side "no output for N ms" watchdog that re-requests the stream
or returns to the launcher with state intact; a companion-side stream
liveness check that restarts the encoder when the client reappears; a
launcher that reconciles from a failed poll (see the banner issue below).
**Behaviour, as the user specified it (2026-09-20, late):**

1. **Pause on desync.** The moment the session looks desynced — the client
   has stopped getting decoder output, or the host has stopped hearing
   from the client — the game is paused on the host so it does not advance
   while the player is blind. The pause must be host-side: when the link
   is down the client cannot ask for it, so the companion pauses on its own
   when the client's heartbeat (`D-BASE-R2`) goes stale.
2. **Auto-recover.** Host and client keep trying to re-establish the stream
   on their own — client re-requests `native-stream-start`; companion
   restarts the encoder with the validated encoder-only restart primitive
   (`C3.L1`) when the client reappears — with backoff, for as long as it
   takes, with no one touching the host.
3. **Resync check before resume.** The game unpauses only when a separate
   check says the stream is actually good again: reuse the startup
   stabilization gate (clean frames, fps, gap — `C3_STARTUP_STABILIZATION`)
   that already gates the first unpause via `native-stream-ready`. Same
   gate, second use.
4. **Give up safely.** After a bounded time, save state, leave the game
   paused, and make the launcher say so. Nothing is lost and nothing is
   left running blind.

Detection thresholds, backoff, and the give-up bound are the design
note's to propose; the four steps above are settled. Status: **open,
registered, behaviour decided, not yet authorized for code.** Prerequisite:
`D-BASE-R2` (the heartbeat is the host-side detector). Owner: transport
(Step 3).
<!-- PRIVYHUB_LINK_DROP_RESILIENCE:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_TERMINAL_STALL_UNRECORDED:KNOWN_ISSUES:BEGIN -->
## 2026-09-20 a terminal stall leaves no evidence in the session report

`max_output_gap_ms` is updated when the *next* frame leaves the decoder, so
a stall that never ends is never recorded, and an app killed during it posts
no report at all. The freeze above therefore has no row anywhere. Fix
direction: a "last output age" the companion polls (or the client posts
periodically), so a frozen session leaves a timestamped trace and the
companion can act on it; this is also the trigger the link-drop watchdog
above needs. Status: open, diagnostic instrumentation, low cost.
<!-- PRIVYHUB_TERMINAL_STALL_UNRECORDED:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:BEGIN -->
## 2026-09-18 C3.L2b reporting defect

- ~~`slow_events_marked` is emitted as an empty array.~~ **CLOSED
  2026-09-20 (`D-BASE-R4` item 3), no code change needed.** That key does
  not exist on the current code: `C3.L2b` merges the marked and recent
  segments into the single chronological `slow_events_ge_50_ms`, and the
  two retention counters say how many of each went in. Two reports already
  on disk show the merged array's length equal to marked + recent exactly —
  `d_base_r2_2026-09-20/native_decoder_20260920_180217_204.json` (67 =
  3 + 64) and `d_base_r3a_2026-09-20/native_decoder_20260920_205736_106.json`
  (75 = 11 + 64) — and neither contains a `slow_events_marked` key. The
  marked window is inspectable row by row. Record:
  `docs/memory/evidence/D_BASE_R4_REPORT_VISIBILITY_2026-09-20.md`.

- **Decoder time correlates with perceptible interruption on the onn client,
  but is not its mechanism.** `low_latency_enabled` is false on
  `c2.realtek.video.avc.decoder`; `max_codec_ms` 367; the two largest output
  gaps in the `C3.L2a` E2 session, 359 ms and 352 ms, tracked `codec_ms` to
  within 8 ms with feed delay at zero. `C3.L2c` then cut `max_codec_ms` to
  107 ms and `max_output_gap_ms` got **worse** (385 ms), which falsifies
  `max_codec_ms` as a proxy for the gap. Status: open, owner unassigned —
  `C3.L2c` is closed as falsified and is not the owner. Any future candidate
  justified by "it lowers decode time" must measure `max_output_gap_ms`
  directly before acceptance. Record:
  `docs/memory/evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.
<!-- PRIVYHUB_C3_L2A_E2:KNOWN_ISSUES:END -->

<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:BEGIN -->
## 2026-09-19 C3.L3 characterization probe finalize bug

Found during `C3.L3` Linux fixed-bitrate characterization (third run).
Corrected 2026-09-19 by `C3-L3R1`: the original entry misidentified the
decoder-session file involved and implied the 6000 kbps result was
unrecoverable. Neither was right. The defect itself is real and stays open.

- **`--finalize` can match the wrong decoder-session file.**
  `tools/probe_c3_fixed_6000_characterization.py --finalize`, run
  immediately after `tools/probe_c3_fixed_5500_characterization.py
  --finalize` in the same sequence, returned measurements byte-identical to
  the 5500 kbps result (`session_duration_ms` 66,638, every
  decoder/controller count, `sequence_resyncs`, `ssrc_changes`) apart from
  `target_bitrate_kbps` itself, and was missing several audio fields the
  5500 result had. It had matched the 5500 kbps run's own decoder-session
  file, `logs/games/decoder_sessions/native_decoder_20260919_055703_163.json`.
  That attempt was discarded.

  **The defect is intermittent.** The 6000 kbps rerun taken the same
  session matched correctly:
  `logs/streaming/c3_fixed_6000_characterization.json` records
  `payload.decoder_session_log =
  logs/games/decoder_sessions/native_decoder_20260919_060325_369.json`, a
  distinct 64,840 ms session written 9.4 s before that finalize, whose
  figures differ from the 5500 kbps session in every field. So back-to-back
  finalizes do not fail deterministically, and the data that was thought
  lost was never lost.

  Not root-caused. Status: **open**. Affects
  `tools/probe_c3_fixed_*_characterization.py`'s decoder-session matching
  only — the `C3.L3` companion-side Linux cycle
  (`companion/diagnostics/c3_linux_actuator_probe.py`) is not implicated.

  **Workaround until fixed:** after any `--finalize`, check
  `payload.decoder_session_log` and `session_duration_ms` in the written
  JSON against the session you intended to measure, before using the
  result. A finalize that reports the previous bitrate's duration has
  matched the wrong file.

  Records: `docs/memory/evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`,
  `docs/memory/patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md`.
<!-- PRIVYHUB_C3_L3_FINALIZE_MATCH_BUG:KNOWN_ISSUES:END -->
