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
