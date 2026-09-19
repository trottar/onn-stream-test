<!-- PRIVYHUB_D5_TV_MEDIA_CLOSEOUT:BEGIN -->
## D5 media/server restoration closed

D5 is complete/runtime validated as of 2026-09-17.

Closure combines the clean D-136 automated regression with the final manual onn smoke: Live TV playback, Favorites/guide navigation, and VOD playback all passed.

The accepted D5 baseline includes external/removable VOD, Live TV, Linux EPG and Android guide caching/presentation, Linux-authoritative TV durable state, incorrect-guide durable intent, and the D-131/D-135 responsiveness boundaries.

D6 UDP replay remains preserved historically as a former Phase D item. Active ownership moved into Phase C transport validation.

The active roadmap proceeds through Phase C Linux continuation before remaining D checkpoint work.
<!-- PRIVYHUB_D5_TV_MEDIA_CLOSEOUT:END -->

<!-- PRIVYHUB_C3_L0_LINUX_ACTUATOR_BOUNDARY:BEGIN -->
## C3 Linux actuator boundary — durable facts

Established by the `C3.L0` source audit at
`310596dd0cc3ff22f3fe46e2eb025d052da90ec0`. Full map:
`investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.

**No live bitrate actuator exists on Linux, and the current architecture
forecloses one.** The encoder is an external FFmpeg CLI launched with `-nostdin`
and `stdin=DEVNULL`, with bitrate baked into argv at `Popen` time. There is no
control socket and no in-process encoder handle. `live_bitrate_reconfigure`
requires an architecture change, not a patch. This is a statement about the
current architecture, not about h264_vaapi hardware capability.

**Linux video topology is single-process.** `_running_locked()` asserts
`_capture_process is None` on Linux because x11grab is an FFmpeg input format.
Windows uses a separate WGC bridge feeding FFmpeg over an inherited pipe.
Therefore Windows actuator interruption figures are not portable to Linux, in
either direction.

**`_start_linux_locked` is not an actuator.** It calls `_stop_locked()`, which
also stops the FEC relay, session I/O and host telemetry. Any Linux
encoder-only restart needs a separate narrow seam.

**Resolution and FPS are client-pinned, not negotiated.**
`NativeStreamActivity` holds `VIDEO_WIDTH`, `VIDEO_HEIGHT` and `VIDEO_FPS` as
compile-time constants and passes them to `AvcLowLatencyDecoder`, which
configures MediaCodec once, never derives dimensions from the in-band SPS, and
ignores `INFO_OUTPUT_FORMAT_CHANGED`. Host and client can silently diverge.
Changing either requires an APK change, not merely a restart. GOP is expressed
in frames, so an FPS change silently rescales the keyframe interval in seconds.

**FEC group size is the only in-place seam.** The FEC header carries the real
group length and the Android receiver reads it, validating 1 to 8. Short groups
are already an exercised production path. Mutation would need no encoder
restart, SSRC change, resync or IDR wait. No setter exists and no runtime
evidence exists. **C4 owns adaptive FEC; C3 does not actuate it.**

**Pacing has no owner and no actuator.** The relay forwards immediately with no
deadline or scheduler. Do not introduce probe-style pacing semantics into the
live stream.

**The Windows 5500/6000/7000 ladder is evidence, not a Linux constant.**
Per D-071, Linux must reclassify actuation and revalidate the fixed envelope
before any level is treated as portable.
<!-- PRIVYHUB_C3_L0_LINUX_ACTUATOR_BOUNDARY:END -->

<!-- PRIVYHUB_C3_L2_LINUX_ACTUATOR_CLASSIFICATION:BEGIN -->
## C3 Linux actuator classification — durable facts

Recorded by `C3.L2` on 2026-09-18. Full record:
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

**Linux is `video_only_restart`.** The capability is runtime validated across
two clean cycles with full lifecycle preservation, at a cost of **287-318 ms of
decoder output gap** against Windows D-062's 791 ms on the directly comparable
cycle. `live_bitrate_reconfigure` is not available under the current external
FFmpeg CLI architecture. `unsupported` does not apply.

**Authorized use:** session start and start-time profile selection before
`READY`; manual and loopback-only diagnostic changes; fallback and recovery,
including replacing a dead encoder; `C3.L3` characterization cycles.

**Not authorized:** automatic adaptation during `PLAYING`. The automatic
fast-down/slow-up controller stays blocked. An automatic controller fires under
pressure, so it would insert a deliberate ~290 ms discontinuity exactly when
delivery is already degraded, repeatedly rather than once, against a standing
preference to minimize perceptible streaming artifacts.

This mirrors the Windows D-070 disposition but is reached from Linux
measurements. Windows numbers are not carried across in either direction.

**A fresh encoder process already starts with a keyframe.** A newly launched
FFmpeg RTP stream emits in-band parameter sets and an IDR access unit, and the
Linux start path publishes `bootstrap: in_band_h264_parameter_sets`. "Request an
immediate IDR on the replacement encoder" therefore names a remedy without an
established cause. The open question is why the receiver does not accept that
first keyframe promptly.

**`max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are whole-session
values.** Sessions carrying more than one sequence resync cannot attribute the
session maximum to a single actuator cycle. `decoder_max_output_gap_ms` is the
figure to cite, because the receiver measures it independently of the host
probe.
<!-- PRIVYHUB_C3_L2_LINUX_ACTUATOR_CLASSIFICATION:END -->

<!-- PRIVYHUB_C3_L2A_E1_DECODER_EVIDENCE:BEGIN -->
## Decoder-report retention limits — durable facts

Established by the `C3.L2a` E1 evidence pass. Record:
`evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.

**Superseded by `C3.L2b` (below): the specific "128-entry flat ring" retention
description is historical, describing the report as it existed through
`C3.L1R1`.** The facts about the client's own decoder baseline and the
287-318 ms qualification remain current and are restated, not superseded.

**The Android decoder session report's slow-event list *was* a fixed-capacity
ring.** It reports `slow_event_retained` and `slow_event_capacity`; when they were
equal the buffer had overflowed and only the most recent events survived. In the
`C3.L1R1` session it held 128 of 128 and covered only the last 29.4 s of a 64.8 s
session. A cumulative field such as `max_output_gap_ms` could therefore name an
event whose row was gone. `C3.L2b` replaced this with the segmented design
recorded below; read the two `_marked`/`_recent` field pairs there before
concluding anything from an absence in reports generated after this patch.

**The game diagnostic bundle's native video section is the last 500 lines of the
host log.** A missing encoder restart banner is not evidence that no restart
happened. Unaffected by `C3.L2b`.

**Decoder time, not transport, dominates the large output gaps on this client.**
In ordinary play, `output_gap_ms` tracks `codec_ms` one-to-one with
`feed_delay_ms` near zero and an empty app queue, reaching 238 ms and 200 ms with
no actuator involved. Session-wide: 2,696 spikes at or above 20 ms against 3,847
queued frames, `max_codec_ms` 297, `low_latency_enabled` false on
`c2.realtek.video.avc.decoder`. This is a fact about the client's decoder, not
about report retention, and does not change with `C3.L2b`.

**Therefore the actuator's 287-318 ms is not established as actuator cost.**
Against a baseline that reaches 238 ms unaided, the attributable part may be
~50 ms or may not be separately visible. Do not restate it as "the cost of the
actuator" without this qualification. `C3.L2b` makes it possible to measure
this on a future cycle; it did not itself perform that measurement.
<!-- PRIVYHUB_C3_L2A_E1_DECODER_EVIDENCE:END -->

<!-- PRIVYHUB_C3_L2B_DECODER_REPORT_CYCLE_RETENTION:BEGIN -->
## Decoder-report cycle retention — durable facts

Established by `C3.L2b`. Full record:
`patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.

**The decoder session report now retains two slow-event segments, not one
ring.** `slow_event_retained_marked` / `slow_event_capacity_marked` (64) cover
events recorded while a cycle window was open; `slow_event_retained_recent` /
`slow_event_capacity_recent` (64) cover ordinary play. `slow_event_retained`
and `slow_event_capacity` keep their old whole-report meaning.
`slow_events_ge_50_ms` keeps its old 7-column shape, now the two segments
merged and sorted by `elapsed_ms`.

**A cycle window opens on every SSRC change and sequence resync, for
2000 ms, protecting the marked segment from ordinary-play eviction during
that time.** `RtpH264Receiver.onStreamDiscontinuity` fires into
`AvcLowLatencyDecoder.markCycleWindow`. 2000 ms is a judgment call against
the measured cycle terms (max observed component 318 ms), not itself
runtime-validated — if a future cycle's discontinuity-adjacent slow events
land outside it, that is a finding for the next evidence pass, not a defect
in the design.

**`stream_discontinuities` gives `elapsed_ms`, `type`
(`ssrc_change`/`sequence_resync`, set explicitly at each call site) and
`jump_packets` for every discontinuity, bounded to 64 entries.**
**`first_idr_after_discontinuity` gives `elapsed_ms`, `resync_to_idr_ms`,
`au_complete`, `au_fec_recovered` and `au_fec_unrecoverable_group` for the
first accepted IDR following each discontinuity, bounded to 64 entries** —
only for discontinuities, not the session-start IDR.

**`au_fec_unrecoverable_group` does not cover `trimFecGroups`'s capacity
eviction (>96 concurrently buffered groups).** A known, accepted gap: that
path needs loss well past anything C3 evidence has shown, and omitting it can
only under-report the flag, never falsely claim recovery.

**Held packets now carry their FEC-recovery provenance.** `heldPackets`
changed from `HashMap<Int, ByteArray>` to `HashMap<Int, HeldPacket>` so a
packet recovered by FEC but then held for reordering does not silently lose
that fact before its access unit completes.

**This patch changed report retention and observation only.** It did not
change decoder configuration, resolution, frame rate, GOP, B-frames, FEC wire
format, RTP payload type, packet size, ports, process audio, controller
transport or emulator lifecycle, and it did not enable MediaCodec low-latency
mode (`C3.L2c`, separately registered, not authorized).

**As of 2026-09-18 this is code, not yet runtime evidence.** No APK built
with the real Android/Gradle toolchain has been installed on the onn device,
and no actuator cycle has been run against it. Do not treat
`stream_discontinuities` or `first_idr_after_discontinuity` field names or
behavior as confirmed against real hardware until that cycle runs.
<!-- PRIVYHUB_C3_L2B_DECODER_REPORT_CYCLE_RETENTION:END -->

<!-- PRIVYHUB_ANDROID_FLAT_SOURCE_LAYOUT:BEGIN -->
## Android source layout is flat by design

Kotlin sources live directly in the Gradle source roots
(`PrivyHub/app/src/main/java/`, with `diagnostics/` and `streaming/`
subdirectories) rather than under `com/safeiot/privyhub/`.

Package declarations were **not** edited and still read
`package com.safeiot.privyhub...`. Kotlin does not require directory/package
agreement; Java does, and this app has no Java sources. `namespace`,
`applicationId` and `AndroidManifest.xml` are all independent of directory
layout.

Do not re-nest. Android Studio's "package directive does not match file
location" inspection offers a quick-fix that would undo this; decline it. If a
Java source is ever introduced, it must use package-matching directories.

The reversed-domain chain was inherited Java convention that cost three
directory levels and bought this project nothing.
<!-- PRIVYHUB_ANDROID_FLAT_SOURCE_LAYOUT:END -->

<!-- PRIVYHUB_C3_L2A_ANSWERED:BEGIN -->
## The Linux actuator does not impose an IDR wait — durable fact

Measured 2026-09-18 by `C3.L2a` E2. Record:
`evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

After an encoder-only cycle, the receiver accepted the replacement encoder's
first IDR **27 ms** after the SSRC change, access unit complete, no FEC repair,
no unrecoverable group. The two ordinary sequence resyncs in the same session
took 195 ms and 210 ms.

Two explanations are dead by measurement: the IDR wait, and the
damaged-first-keyframe candidate. **The 287-318 ms figure from `C3.L1` /
`C3.L1R1` was never actuator cost and must not be cited as such.**

**Decoder time is the largest measured contributor to perceptible
interruption.** The session's worst output gaps — 359 ms and 352 ms — followed
sequence resyncs, not the cycle, and tracked `codec_ms` to within 8 ms with feed
delay at zero. `max_codec_ms` 367 with `low_latency_enabled` false on
`c2.realtek.video.avc.decoder`. Nothing registered at the actuator cycle at all.

This does not reopen `C3.L2`. One cycle in one session removes a mechanism; it
does not authorize automatic in-game adaptation, which still needs repetition
and a focused gameplay observation.
<!-- PRIVYHUB_C3_L2A_ANSWERED:END -->

<!-- PRIVYHUB_C3_L2C_FALSIFIED:BEGIN -->
## Decode time is not the stall — durable fact

Measured 2026-09-19 by `C3.L2c`. Record:
`evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.

Requesting `MediaFormat.KEY_LOW_LATENCY` unconditionally on
`c2.realtek.video.avc.decoder` — overriding its own `FEATURE_LowLatency`
self-report of unsupported — works: `low_latency_enabled` flips true.

It does not help. In the one session with the flag set, against the seven
ordinary sessions on the same device the same day:

- `max_codec_ms` 107, better than all seven (range 140-433);
- `spike_20_ms` 147, against 775-3,260;
- `spike_50_ms` 19, against 91-314;
- `spike_250_ms` 0, the only session of the eight with none;
- **`max_output_gap_ms` 385, second worst of the eight.**

In every ordinary session `max_output_gap_ms` tracks `max_codec_ms` to within
about 10 ms. In the low-latency session it exceeded it by 278 ms.

**`max_codec_ms` is therefore not a valid proxy for `max_output_gap_ms`.** Any
future candidate justified by "it lowers decode time" must measure the output
gap directly before acceptance. The `C3.L2a` E2 statement that decoder time is
the largest measured contributor to perceptible interruption holds as a
correlation and not as a mechanism.

Rolled back to exact predecessor bytes. **Do not retry the unconditional
`KEY_LOW_LATENCY` request without new evidence.**

What produced a 385 ms gap in a session with zero 250 ms codec spikes is
unexplained and no work item owns it.
<!-- PRIVYHUB_C3_L2C_FALSIFIED:END -->

<!-- PRIVYHUB_C3_L3_FIXED_BITRATE:BEGIN -->
## Linux fixed-bitrate characterization — durable facts

Established 2026-09-19 by `C3.L3`. Records:
`patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md`,
`evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.

The fixed-bitrate characterization cycle is Linux-capable. It was ported by
reusing the validated `C3.L1`/`C3.L1R1` encoder-only restart primitive rather
than porting the Windows WGC replacement-capture implementation, which stays
untouched and Windows-only. `_build_linux_ffmpeg_command`'s
`bitrate_kbps`/`max_bitrate_kbps` overrides existed and were unused; the port
called them.

Ten trigger/finalize cycles across three runs at 5000/5500/6000 kbps, zero
`cycle_fec_send_errors_delta`, `cycle_audio_send_errors_delta` and
`cycle_controller_bad_packets_delta` in every one. Lifecycle preserved
throughout.

`decoder_max_output_gap_ms`, three valid samples per bitrate:

| bitrate | samples | band |
| --- | --- | --- |
| 5000 kbps | 367 / 292 / 242 | 125 ms |
| 5500 kbps | 219 / 584 / 335 | 365 ms |
| 6000 kbps | 331 / 291 / 307 | **40 ms** |

**6000 kbps is the most consistent of the three**, across sessions of 21.1s,
77.2s and 64.8s, and never exceeded 331 ms. 5500 kbps produced both the best
and the worst single result in the data set; its 584 ms session traces to one
417 ms resync-to-IDR event.

Two standing qualifications:

- every figure here is transport and decoder timing. **No perceptual quality
  was measured**, so no bitrate is accepted as a fallback level on this data.
  A focused gameplay observation is still required, and it is the `C3.L4`
  gate;
- the Windows 5500/6000/7000 ladder remains evidence, not a Linux constant.

Operational rule from this work: `tools/probe_c3_fixed_*_characterization.py
--finalize` has matched the wrong decoder-session file when run back to back
after another bitrate's finalize. Always check `payload.decoder_session_log`
and `session_duration_ms` in the written JSON against the intended session
before using a finalize result. See `docs/KNOWN_ISSUES.md`.
<!-- PRIVYHUB_C3_L3_FIXED_BITRATE:END -->

<!-- PRIVYHUB_NEGATIVE_RESULT_POLICY:BEGIN -->
## Record failures, not only successes

Durable memory must capture what did **not** work alongside what did. A record
that preserves only successes teaches future work nothing and silently invites
repeated attempts down paths already known to be dead.

Every meaningful patch, probe, diagnostic, discussion outcome or roadmap change
records, in the same work:

- what was attempted and why;
- what succeeded, with measurements;
- what failed, was rejected, was rolled back, or was rejected before
  modification, with the measurement or reason that decided it;
- what remains unknown;
- the durable lesson, promoted to `LEARNINGS.md` when it generalizes.

A rejected candidate is a result. A rolled-back installer is a result. A
wrong-state rejection is a result. An absent failure section must mean "none
occurred", never "none were written down" — so state explicitly when a run was
clean.

Preserve superseded records rather than deleting them; mark newer state
authoritative. Raw measurements outrank later summaries when they conflict.
<!-- PRIVYHUB_NEGATIVE_RESULT_POLICY:END -->

## Memory health

Memory responsibilities remain separated:

- CURRENT.md: active resumable state.
- MEMORY.md: durable facts and rules only.
- CURRENT_HANDOFF.md: concise continuation instructions.
- roadmap status: current roadmap representation.
- dated memory/evidence/investigations: chronology and proof.

When roadmap sequencing changes, synchronize active state, roadmap status, and handoff state without rewriting historical evidence.

Compression must not destroy measurements. The 2026-09-18 checkpoint reduced
several active files to single-line assertions and left the C1/C2 Linux baseline
numbers outside the repository entirely. When shortening active memory, verify
the canonical evidence record holds the detail first.
