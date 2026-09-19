---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
status: actuator_classified_video_only_restart_non_automatic
---

# C3 Linux actuator boundary

## Status

**SOURCE AUDIT COMPLETE / ACTUATOR RUNTIME VALIDATED / CLASSIFIED BY C3.L2**

Linux is classified `video_only_restart`, authorized for start-time, manual,
fallback and characterization use and not authorized for automatic in-game
adaptation. Decision record:
`../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

The sections below are preserved in the order they were written. Later sections
are authoritative where they disagree with earlier ones.

## Narrow question

Can the existing Linux streaming architecture expose safe backend-neutral
quality controls without disturbing validated playback?

This audit answers ownership, runtime mutability and lifecycle cost from source.
It does not implement an actuator, a controller or any production change.

## Relationship to the Windows-era C3 record

C3 was substantially executed on the outgoing Windows prototype and then
deliberately handed to Linux by D-071. This investigation resumes that work; it
does not restart it.

Closed Windows-era results that remain authoritative as history:

- D-063 accepted `video_only_restart` as the initial backend-neutral actuator
  strategy;
- fixed-bitrate characterization produced 7000 reference, 6000 validated, 5500
  validated floor, 5000 runtime tested and not accepted;
- D-070 validated bidirectional transitions but **rejected**
  `video_only_restart` for seamless automatic in-game adaptation because the
  host produced no new RTP for roughly 0.84-0.95 s and gameplay visibly froze
  for roughly 1 s;
- D-067/D-068 runtime validated the
  `LAUNCHING -> STABILIZING -> READY -> PLAYING` readiness boundary and froze
  adaptation during STABILIZING/PAUSED;
- D-071 stopped Windows actuator development and required Linux to reclassify
  actuation and revalidate the fixed envelope.

The Windows 5500/6000/7000 ladder is evidence, not a Linux product constant.

## Audited source

Audited at `310596dd0cc3ff22f3fe46e2eb025d052da90ec0`:

- `companion/native_stream.py`
  - `_build_linux_ffmpeg_command` (encoder argv construction);
  - `_start_linux_locked` (Linux start path);
  - `_stop_locked` (teardown ownership);
  - `_running_locked` (Linux liveness definition);
  - `status()` (published backend/profile/bitrate surface);
- `companion/native_stream_profiles.py`;
- `companion/native_fec_relay.py` (`_handle_rtp`, `_emit_group_locked`, `_send`);
- `companion/diagnostics/c3_actuator_probe.py`;
- `companion/diagnostics/c3_fixed_bitrate_probe.py`;
- `companion/plugins/games.py` loopback-only C3 action registration;
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`;
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/AvcLowLatencyDecoder.kt`;
- `PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt`.

## Actuator boundary map

| Parameter | Owner | Runtime mutable? | Restart required? | Safe? |
| --- | --- | --- | --- | --- |
| bitrate | Companion FFmpeg `-b:v`/`-maxrate`/`-bufsize`, fixed at process creation | No | Encoder-process restart | Unknown on Linux; Windows functional but rejected for automatic use |
| resolution | Split: host `-vf scale/pad` from profile; Android compile-time constants | No | Encoder restart plus decoder re-creation plus APK rebuild | No; not negotiated; C3 non-goal |
| FPS | Split: host x11grab `-framerate`; Android compile-time constant | No | Same as resolution; also rescales GOP seconds | No; C3 non-goal |
| FEC | Companion `NativeVideoFecRelay.group_size` | Structurally yes; wire format is self-describing | No | Unvalidated; no setter exists; C4 owns adaptive FEC |
| pacing | No owner; no pacing actuator exists | Not applicable | Not applicable | Introducing one is a new transport scheduler; out of C3 scope |

### Bitrate

The Linux encoder is launched with `-nostdin` and `stdin=subprocess.DEVNULL`,
and the bitrate arguments are baked into argv at `Popen` time. There is no
control socket, no ZMQ filter and no in-process libavcodec handle.

Therefore `live_bitrate_reconfigure` is not merely unimplemented on Linux. It is
foreclosed by the current external FFmpeg CLI architecture, independently of
what h264_vaapi hardware supports. Reaching it requires an in-process encoder or
a controllable encoder host, which is an architecture change rather than a
patch.

`_build_linux_ffmpeg_command` already accepts and validates `bitrate_kbps` and
`max_bitrate_kbps` overrides, but no Linux caller passes them. The override seam
exists and is unexercised.

### Linux and Windows actuator topology differ in one favourable way

On Windows the video path is two managed processes: the WGC bridge writes raw
frames into FFmpeg's stdin over an inherited pipe. A video-only restart must
replace both and re-handshake the pipe.

On Linux there is one process. `_running_locked()` asserts
`self._capture_process is None` on Linux because x11grab is an input format
inside FFmpeg itself.

A Linux encoder-only restart is therefore structurally simpler: one `Popen`, no
pipe handoff, no capture-metadata first-frame wait. This is a concrete reason
the Linux interruption cost may not match the Windows 0.84-0.95 s, and it is the
strongest argument for measuring rather than assuming D-070 transfers.

### No Linux video-only restart path exists

`_start_linux_locked` calls `self._stop_locked()` first. `_stop_locked` stops
host telemetry, stops session I/O, kills the encoder **and stops the FEC relay**.

That is exactly the lifecycle violation the backend-neutral actuator contract
forbids. A Linux continuity probe therefore requires one narrow internal
encoder-only replacement seam that does not call `_stop_locked()`.

### Existing C3 probes are Windows-only

`c3_actuator_probe.py` and `c3_fixed_bitrate_probe.py` both require
`manager._wgc_ready()`, the WGC bridge path, an HWND capture target and
`_build_ffmpeg_command`. On Linux they fail closed with
`wgc_runtime_unavailable` before modifying anything.

They are correct as written. They are not reusable on Linux without a Linux
cycle implementation behind the same probe structure.

### Resolution and FPS are client-pinned, not negotiated

`NativeStreamActivity` holds `VIDEO_WIDTH = 1280`, `VIDEO_HEIGHT = 720` and
`VIDEO_FPS = 60` as compile-time constants and passes them to
`AvcLowLatencyDecoder` at construction. The decoder configures MediaCodec from
those constructor values, does not derive dimensions from the in-band SPS, and
ignores `INFO_OUTPUT_FORMAT_CHANGED` with a bare `continue`. It is never
reconfigured, and the Activity does not poll host status during playback.

Consequences:

- host profile and client constants can silently diverge with no negotiation and
  no runtime detection;
- any resolution or FPS change requires an APK change, not only a restart;
- GOP is expressed in frames, so an FPS change silently rescales the keyframe
  interval in seconds.

C1 deliberately preserved these Android constants. C3 must not change them.
Record the divergence risk; do not act on it inside C3.

### FEC is the only parameter with a real in-place seam

`_emit_group_locked` packs the actual `len(group)` into the FEC header.
`RtpH264Receiver.kt` reads the count from header byte 5 and validates a range of
1 to 8. No client constant participates.

Short groups are already an exercised production path, because the relay flushes
early on RTP marker or timestamp change.

So changing `group_size` between groups would take effect with no encoder
restart, no SSRC change, no sequence resync and no IDR wait. It is by a wide
margin the cheapest actuator in the system.

Constraints:

- the one-byte marker mask caps group size at 8;
- `group_size` is assigned only in `__init__` and has no thread-safe mutator;
- there is no runtime evidence for mid-stream mutation.

Adaptive FEC belongs to C4. C3 maps this seam and stops.

### Pacing has no owner

`_send()` calls `sendto()` immediately and only instruments monotonic duration
around it. There is no deadline, no sleep and no scheduler anywhere in the
production transport path.

`architecture/STREAM_TELEMETRY.md` states this as a deliberate rule: the relay
has no pacing deadline, so probe-style pacing-lateness semantics must not be
copied into the live stream.

There is nothing to actuate. Introducing pacing would be a new transport
scheduler adjacent to the deferred UDP burst/gap pathology, which is a Windows
measurement that has never been re-measured on Linux.

## Defects and gaps surfaced by this audit

1. **Host telemetry never starts on Linux.** `_host_telemetry.start()` is called
   only inside the Windows start path, gated on `_capture_process is not None`.
   `_start_linux_locked` never calls it, while `status()` still publishes a
   `host_telemetry` section. The C2 contract is unaffected because its sender
   metrics come from the FEC relay, which does run. Sender-side host resource
   telemetry is nevertheless absent on Linux and is a Phase E prerequisite.

2. **`_patches/` and `_probes/` are not ignored.** `.gitignore` covers
   `privyhub_*/` and `privyhub_*_v*.zip` but not `_patches/` or `_probes/`, and
   the local probe directories are named `PrivyHub_*`, which does not match on a
   case-sensitive filesystem. Confirm with `git status --short` before any
   commit.

Both are recorded in `docs/KNOWN_ISSUES.md`. Neither is fixed by this work.

## Unknowns, in priority order

1. Linux encoder-only restart interruption cost. Unmeasured. The Windows figure
   is not portable and the single-process topology gives real reason to expect a
   different number.
2. Whether any low-interruption Linux bitrate actuator is reachable without
   replacing the external FFmpeg CLI. Source says no for bitrate under the
   current architecture.
3. Whether mid-stream FEC group-size mutation is safe. Wire format permits it;
   no runtime evidence exists. C4 territory.
4. Linux UDP burst/gap behaviour. Deferred and never re-measured on
   representative Linux infrastructure.

## Next diagnostic

`C3.L1` — Linux encoder-only restart continuity probe.

Narrow question: can the Linux backend perform one same-bitrate 7000 to 7000
encoder-only cycle while preserving the FEC relay, process audio, the persistent
controller and emulator lifecycle, and how large is the RTP interruption?

This is the test that
`evidence/C3_VIDEO_ONLY_RESTART_RUNTIME_VALIDATED_2026-09-14.md` already
requires before Linux actuator acceptance. It is a gate memory has already set,
not new scope.

It reuses the existing probe structure, the existing loopback-only
`c3-actuator-continuity-cycle` Games action, and existing C2 telemetry and
decoder-session reporting for evidence. It encodes no acceptance threshold and
changes no bitrate.

It requires one narrow new internal seam: a Linux encoder-only replacement that
does not call `_stop_locked()`. That seam does not exist today and is the
minimum honest cost of answering the question.

Decision boundary:

- interruption materially below the Windows 0.84-0.95 s — D-070's rejection does
  not transfer; reopen Linux actuator classification and proceed to Linux fixed
  envelope revalidation;
- interruption comparable to Windows — `video_only_restart` is fallback-only on
  Linux as well, the automatic controller stays blocked, and the next real item
  is the encoder-host architecture question rather than further probing.

## C3 Linux sequence

1. `C3.L0` — this audit recorded in durable memory. **This item.**
2. `C3.L1` — Linux encoder-only restart continuity probe.
3. `C3.L2` — Linux actuator capability classification recorded as a decision:
   `live_bitrate_reconfigure`, `video_only_restart` or `unsupported`.
4. `C3.L3` — Linux fixed-bitrate envelope revalidation, only if `C3.L2` accepts
   an actuator. The Windows ladder enters as hypothesis, not constant.
5. `C3.L4` — explainable fast-down/slow-up controller. Still blocked.

## Preservation boundary for all C3 Linux work

Do not change:

- encoded resolution, frame rate, GOP or B-frames;
- FEC algorithm or wire format;
- RTP payload type, packet size or ports;
- process audio;
- controller transport;
- emulator/game lifecycle;
- Android streaming constants or startup ordering;
- any non-loopback control surface.

## Privacy

No network addresses appear in this record. Any C3 diagnostic output must
continue to exclude source/request address identity.

## C3.L1 implementation — installed, runtime evidence pending

Status: **INSTALLED / DEVELOPMENT VALIDATED / RUNTIME EVIDENCE PENDING**

### Seam

`companion/diagnostics/c3_linux_actuator_probe.py` implements the Linux
encoder-only cycle. `NativeStreamManager.diagnostic_c3_actuator_continuity_cycle()`
now selects it by platform: Linux uses the new module, Windows keeps
`c3_actuator_probe`, and any other host is refused.

`_stop_locked()` is never called. The FEC relay, process audio, the persistent
controller and the managed RetroArch process stay running.

### Why no new action and no new tool

The Linux cycle emits the same `privyhub_c3_actuator_cycle_probe_v1` schema and
the same `video.ffmpeg_spawn_ms`, `video.first_rtp_resume_ms` and
`video.host_verified_ms` fields the existing runner consumes. The existing
loopback-only `c3-actuator-continuity-cycle` action and
`tools/probe_c3_actuator_continuity.py` therefore work unchanged.

`companion/plugins/games.py` and the tools runner are intentionally untouched.
This avoids the parallel-implementation failure mode and keeps one evidence
format across both backends.

### Reaper hazard and how it is handled

`status()` calls `_reap_locked()`, which calls `_stop_locked()` when it observes
an exited encoder. During the swap the encoder is deliberately dead, so the
probe clears `manager._process` **before** killing the old process. With
`_process` set to `None`, `_reap_locked` sees no exited process, no absent
capture process and no relay-without-encoder condition, and does not tear down
FEC or session I/O.

The manager lock is held for the whole cycle; clearing the handle first is
defence against the reaper specifically rather than against concurrency.

### Honest Linux payload differences

`capture_restarted` is `false` and `capture_process_present` is `false`, because
x11grab is an FFmpeg input format rather than a separate process. The payload
also carries `platform`, `capture_backend` and `encoder_backend` so the two
backends' evidence is not silently conflated.

### What the probe measures

Host time from cycle start until the FEC relay observes new RTP
(`first_rtp_resume_ms`), encoder spawn time, and a 0.75 s post-resume stability
window, plus FEC, audio and controller continuity deltas across the cycle.

No acceptance threshold is encoded. Bitrate is held at the 7000 reference and
the probe refuses to run if the active bitrate is anything else.

### Development validation

48 deterministic behavioural checks against a fake manager, with no real
process, network or X11 access: happy-path payload shape and schema, FEC/audio/
controller continuity, `_process` cleared before the kill, no bitrate override
passed to the command builder, `_stop_locked` never called, replacement-exit and
RTP-never-resumed failure paths each clearing `_process` while leaving FEC and
session I/O intact, and twelve precondition rejections each asserted to modify
nothing.

Development validation is not runtime validation. The measured interruption
cost is still unknown.

### Next

Run the probe against a live Linux game session. The `C3.L0` decision boundary
is unchanged:

- interruption materially below the Windows 0.84-0.95 s — reopen Linux actuator
  classification and proceed to `C3.L3`;
- interruption comparable to Windows — `video_only_restart` is fallback-only on
  Linux too and the controller stays blocked.

## C3.L1 runtime result and C3.L1R1 measurement correction

Full evidence: `evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md`.

### Lifecycle preservation: PASSED

The cycle ran against a live session. FEC relay, process audio, persistent
controller and emulator all continued, with zero FEC send errors, zero audio
write errors, zero controller send errors, and exactly one SSRC change. The
receiver was not waiting for an IDR at session end.

### Measurement defect found in the C3.L1 probe

`host_first_rtp_resume_ms` of 215.017 ms sat 0.010 ms after
`host_ffmpeg_spawn_ms` of 215.007 ms, while the RTP poll sleeps 10 ms between
checks. The first poll succeeded immediately because the baseline came from the
pre-kill FEC snapshot and was already exceeded by old-encoder packets.

The figure is encoder spawn time mislabelled as video resume time and must not
be cited. `C3.L1R1` takes the baseline after the kill returns, reports
`rtp_baseline_residual_packets`, and adds `rtp_silence_after_spawn_ms` and
`encoder_down_ms`.

The Windows probe shares the same baseline pattern. Its evidence did not record
`ffmpeg_spawn_ms`, so its 837-953 ms figures cannot be checked retrospectively;
treat them as pipeline re-establishment time rather than verified video-resume
time. Windows is outgoing and its probe is not modified.

### Authoritative comparison

`decoder_max_output_gap_ms` is measured on the receiver, independently of the
host probe, and is unaffected by the defect:

- Windows D-062 same-bitrate cycle: 791 ms;
- Windows D-070 bidirectional cycle: 1,059 ms;
- **Linux C3.L1 same-bitrate cycle: 318 ms.**

Against the directly comparable D-062 run, Linux is 2.5x better. This matches
the single-process topology prediction recorded above.

### The gap is dominated by IDR wait, not spawn

`max_resync_to_idr_ms` 241 ms and `packets_dropped_waiting_for_idr` 118, against
0 dropped-waiting-for-IDR on both Windows runs. GOP 15 at 60 fps is a 250 ms
keyframe interval, so the 241 ms maximum is approximately one full GOP and
accounts for most of the 318 ms gap.

Whether an explicit immediate-IDR request on the replacement encoder would
shorten this is an open `C3.L2` question. It is not authorized by this
evidence.

### Disposition

The pre-registered boundary is met on the authoritative measure. D-070's
rejection does not automatically transfer to Linux, Linux actuator
classification is reopened as `C3.L2`, and the automatic controller stays
blocked pending that classification and the missing focused gameplay
observation.

### Runner invocation, for the record

The trigger phase takes no flag. `--finalize` is the only option the runner
defines. A `--trigger` flag does not exist and was an error in delivery
instructions, not in the code.

## C3.L1R1 re-run — C3.L1 closed

Corrected measurement: spawn 115.145 ms, first RTP resume 267.069 ms (152 ms of
real video silence), decoder max output gap 287 ms, max resync to IDR 191 ms,
123 packets dropped waiting for IDR.

Two Linux runs bracket the interruption at 287-318 ms decoder output gap against
Windows D-062's 791 ms on the directly comparable cycle.

Lifecycle preservation reproduced cleanly twice. `C3.L1` is
**COMPLETE / RUNTIME VALIDATED**.

Gameplay observation supplied: playable, no freeze reported from the cycle, the
occasional stutter is pre-existing baseline, and the user wants perceptible
streaming artifacts minimized. That preference is a constraint on `C3.L2`.

The dominant term is IDR wait, roughly one GOP at GOP 15 / 60 fps, not process
spawn. An immediate-IDR request on the replacement encoder is the strongest
open lead and is **not authorized** by this evidence.

Active work moves to `C3.L2` classification. Compact continuation brief:
`../PHASE_C_CONTEXT.md`.

## C3.L2 — classification recorded

Full record: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`. No new
measurement was taken; the classification is made from the `C3.L0` source audit
and the two `C3.L1` / `C3.L1R1` runs.

**Linux is `video_only_restart`.** `live_bitrate_reconfigure` is not available
under the current external-FFmpeg-CLI architecture. `unsupported` does not
apply.

Authorized: start-time profile selection before `READY`, manual and
loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
characterization cycles.

Not authorized: automatic adaptation during `PLAYING`. `C3.L4` stays blocked.

The reasons, short form: 287-318 ms is ~17 frame intervals against a settled
stream whose post-cycle output gap was 5 ms; an automatic controller fires under
pressure, when a deliberate discontinuity costs most; a single accepted manual
cycle is not evidence for repeated automatic ones; and the standing user
preference is to minimize perceptible artifacts while an untested lead to reduce
the cost exists.

### Two corrections to how the `C3.L1` figures are read

`max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are **whole-session
values**. Both sessions recorded two sequence resyncs against one SSRC change,
so attributing the session maximum to the actuator cycle is an inference rather
than a measurement. The 287-318 ms `decoder_max_output_gap_ms` is unaffected and
remains the figure to cite.

The terms also do not sum: spawn 115 ms, RTP silence ~152 ms and decoder gap
287 ms overlap in time, and 152 + 191 exceeds 287.

### The recorded "immediate IDR" lead had a false premise

`C3.L1R1` recorded the strongest lead as requesting an immediate IDR on the
replacement encoder. `_build_linux_ffmpeg_command` launches a fresh FFmpeg with
`-f rtp`, `-g 15`, `-bf 0` and no periodic-keyframe override, and
`_start_linux_locked` publishes `bootstrap: in_band_h264_parameter_sets`. A new
H.264 RTP stream begins with parameter sets and an IDR access unit, so the
replacement encoder's first frame is already a keyframe and there is nothing to
request.

The lead is re-registered with its premise corrected rather than discarded: the
IDR wait remains the best available explanation for most of the gap, but the
question is why a keyframe-first stream is not accepted promptly.

## C3.L2a — next diagnostic

Narrow question: why is the receiver's first accepted IDR late after an
encoder-only cycle, when the replacement stream's first frame is a keyframe?

Existing instrumentation first, no code change first:
`logs/games/decoder_sessions/*.json`, `logs/games/native_video_alpha.log`, the
stored `C3.L1` / `C3.L1R1` payloads, and
`PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`,
whose resync and IDR-acceptance policy `C3.L2` did not re-audit. That omission is
recorded here rather than left silent.

Candidates to discriminate:

1. the first IDR arrives damaged — its fragments span FEC groups at the
   discontinuity, and each session recorded 33 lost packets and 2 unrecoverable
   groups; a damaged first keyframe forces a wait of one GOP, 250 ms at GOP 15 /
   60 fps, which matches the observed magnitude with no encoder change;
2. the swap itself damages the first FEC groups, since the encoder-down window
   leaves a partially filled group and the relay flushes on marker or timestamp
   change;
3. receiver resync policy discards the first IDR while establishing parameter
   sets and a clean sequence baseline;
4. encoder ramp — largely excluded, because the ~152 ms silence window is
   measured before RTP resumes while the resync figure is measured after.

Pre-registered boundary, declared before the run: at or below ~120 ms reopens
the automatic-adaptation question, with a focused gameplay observation required
before acceptance; ~120-250 ms keeps the actuator non-automatic and moves the
question to pipeline re-establishment; unchanged falsifies the lead and makes
the encoder-host architecture question the next real item.

Constraints unchanged: loopback-only, no change to resolution, frame rate, GOP,
B-frames, FEC wire format, RTP payload type, packet size, ports, process audio,
controller transport, emulator lifecycle, Android streaming constants, or any
non-loopback control surface.

## C3.L2a E1 — first evidence pass, question not answered

Full record:
`../evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`. No new runtime run;
this is an analysis of the `C3.L1R1` session bundle produced by
`tools/collect_game_session_diagnostics.py`.

**The evidence needed was collected and then discarded.** The decoder report's
slow-event list is a fixed-capacity ring: `slow_event_retained` 128,
`slow_event_capacity` 128, retaining only elapsed 35,421-64,813 ms of a 64,842 ms
session. `max_output_gap_ms` 287 is a cumulative maximum whose per-event row no
longer exists. Any session with more than 128 slow events after a cycle loses
the cycle's evidence, so re-running the existing probe unchanged would not
answer the question either.

**What the retained window shows instead.** In ordinary play with no actuator
activity, output gap tracks codec time one-to-one — 238/247, 200/211, 133/142,
123/131 — with `feed_delay_ms` at or near zero, one or two frames in flight and
an empty app queue. Those gaps are decoder time on a single frame, not transport
or IDR wait. Session-wide: 2,696 spikes at or above 20 ms against 3,847 queued
frames, `max_codec_ms` 297, `low_latency_enabled` false on
`c2.realtek.video.avc.decoder`.

**Consequence for the classification.** Steady-state play in the same session
reached 238 ms and 200 ms output gaps without any actuator. Against that, the
cycle's 287 ms is either ~50 ms of attributable actuator cost or not separately
visible at all; this evidence cannot separate the two. `C3.L2` stands as
written, but 287-318 ms must not be restated as "the cost of the actuator"
without this qualification.

**Also found.** `max_frames_between_idr` is 27 against GOP 15, so the worst-case
keyframe wait is ~450 ms rather than the assumed 250 ms. The damaged-first-IDR
mechanism is real in-session — `fec_recovered_idr_packets` 1,
`fec_unrecoverable_groups` 2, `sequence_gap_au_drops` 4, `incomplete_au_drops`
3 — but cannot be tied to the cycle. The encoder swap is not visible in the
host log's retained 500-line tail, which is an instrumentation question for the
probe source rather than a claim that no swap occurred.

**Next, before any re-run:** the decoder session report must retain the cycle —
marked-window retention or a segmented ring, `elapsed_ms` anchors for the SSRC
change and sequence resyncs, and per-event IDR context for the first accepted
IDR after an SSRC change. Diagnostic-only client work requiring a real Gradle
build and its own patch.

`low_latency_enabled` false is a separate candidate with its own hypothesis. It
changes decoder configuration, which is production client behavior, and is not
authorized here.

## C3.L2b and C3.L2c registered

`C3.L2b` — decoder-report cycle retention. **NEXT.** Make the decoder session
report retain the actuator cycle: marked-window retention or a segmented
slow-event buffer, `elapsed_ms` anchors for the SSRC change and the sequence
resyncs, and per-event IDR context for the first accepted IDR after an SSRC
change. Diagnostic-only client work — the report, not decoder configuration or
any streaming constant. Real Gradle build, `adb install -r`, then one clean
cycle. Do not re-run `tools/probe_c3_actuator_continuity.py` before it lands.

`C3.L2c` — low-latency decode candidate. **REGISTERED, NOT SCHEDULED, NOT
AUTHORIZED.** `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`
while 2,696 of 3,847 frames took 20 ms or more to decode and `max_codec_ms` was
297. Enabling MediaCodec low-latency mode is a production client behavior change
requiring its own narrow hypothesis, its own probe and its own focused gameplay
acceptance. It must not be folded into `C3.L2b`, and it is not a C3 adaptation
item — it changes the baseline C3 measures against.

`C3.L2a` stays open behind `C3.L2b`. `C3.L3` remains unblocked for manual
characterization but is sequenced after `C3.L2a` closes. `C3.L4` remains
blocked.
