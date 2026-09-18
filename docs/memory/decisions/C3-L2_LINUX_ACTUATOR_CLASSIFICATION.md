---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# C3.L2 — Linux actuator capability classification

**Status:** Accepted classification (2026-09-18)

Roadmap and policy decision. No production source is changed by this decision
and no new measurement was taken for it; it is made from the `C3.L0` source
audit and the `C3.L1` / `C3.L1R1` runtime evidence that already exist.

## Decision

The backend-neutral capability model from D-071 is retained unchanged:
`live_bitrate_reconfigure`, `video_only_restart`, `unsupported`.

Linux is classified as **`video_only_restart`**.

- `live_bitrate_reconfigure` — **not available.** The encoder is an external
  FFmpeg CLI launched with `-nostdin` and `stdin=DEVNULL`, with
  `-b:v`/`-maxrate`/`-bufsize` baked into argv at `Popen` time. There is no
  control socket and no in-process encoder handle. This is a statement about the
  current architecture, not about `h264_vaapi` hardware capability. Reaching this
  capability is an architecture change.
- `video_only_restart` — **runtime validated**, twice, with lifecycle
  preservation reproduced: FEC relay, process audio, persistent controller and
  emulator all continued, zero FEC send errors, zero audio write errors, zero
  controller send errors, exactly one SSRC change per cycle.
- `unsupported` — does not apply.

## Authorized use

`video_only_restart` is authorized on Linux for:

- session start and start-time profile selection, before `READY`;
- explicit manual or loopback-only diagnostic bitrate changes;
- fallback and recovery, including replacing a dead encoder;
- `C3.L3` fixed-bitrate envelope characterization cycles.

`video_only_restart` is **not authorized for automatic adaptation during
`PLAYING`**. The automatic fast-down/slow-up controller (`C3.L4`) therefore
remains **BLOCKED**.

This mirrors the Windows D-070 disposition, but it is reached from Linux
measurements. D-070's numbers are not carried across.

## Why the cost is accepted for manual use and not for automatic use

The measured interruption is **287-318 ms of decoder output gap** across two
runs, against Windows D-062's 791 ms on the directly comparable same-bitrate
cycle. The `C3.L0` pre-registered boundary ("materially below 0.84-0.95 s
reopens classification") is met, which is why the actuator is accepted at all.

It is not accepted for automatic in-game use because:

1. **The gap is a distinct artifact class, not measurement noise.** 287 ms is
   roughly 17 frame intervals at 60 fps. The Linux steady-state baseline is
   queue depth 0, ~59.45 fps, and the post-cycle recovered output gap was 5 ms.
   The actuator gap is nearly two orders of magnitude above the stream's own
   settled continuity.
2. **An automatic controller fires under pressure.** A capacity/latency
   controller decides to step down precisely when delivery is already degrading.
   Inserting a deliberate ~290 ms discontinuity at that moment can worsen the
   experience the decision exists to protect, and a fast-down/slow-up policy
   produces such discontinuities repeatedly rather than once.
3. **One accepted manual cycle is not evidence for repeated automatic ones.**
   The 2026-09-18 focused gameplay observation reported the session as playable
   with no freeze attributed to the cycle. That is acceptance of a single
   operator-initiated transition, not of an unannounced policy-initiated one.
4. **The user's standing preference is to minimize perceptible streaming
   artifacts** (recorded 2026-09-18). Authorizing automatic interruptions of
   this size would spend that budget on a cost we have an untested lead to
   reduce.

## What this decision does not say

- It does not reject adaptation on Linux. It rejects *this* actuator for
  *automatic in-game* use at *this* measured cost.
- It does not claim ~290 ms is perceptible, or imperceptible. That is undecided,
  which is itself the reason automatic use is not authorized.
- It does not establish any Linux bitrate ladder. The Windows 5500/6000/7000
  levels remain evidence, not Linux constants; `C3.L3` owns that.
- It does not validate bidirectional or upward Linux transitions. Windows D-069
  is not Linux evidence. Only same-bitrate 7000 to 7000 cycles have run here.
- It does not authorize adaptive FEC. C4 still owns that.

## Correction to the recorded "immediate IDR" lead

`C3.L1R1` recorded the strongest open lead as "request an immediate IDR on the
replacement encoder", on the reasoning that `max_resync_to_idr_ms` of 191-241 ms
is approximately one GOP at GOP 15 / 60 fps.

That framing assumes the replacement stream does not begin with a keyframe.
Source does not support the assumption. `_build_linux_ffmpeg_command` launches a
fresh FFmpeg with `-f rtp`, `-g 15`, `-bf 0` and no periodic-keyframe override,
and the Linux start path publishes `bootstrap: in_band_h264_parameter_sets`. A
newly started H.264 RTP stream begins with in-band parameter sets and an IDR
access unit. There is nothing to request: the replacement encoder's first frame
is already a keyframe.

So the recorded lead names a remedy for a cause that has not been established.
The real open question is why the receiver spends time and discards 118-123
packets before it accepts an IDR from a stream whose first frame is one.

Two further cautions about the same figures:

- `max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are **whole-session
  values**. Both sessions recorded two sequence resyncs and one SSRC change, so
  attributing the session maximum to the actuator cycle is an inference, not a
  measurement.
- The terms do not sum. Spawn 115 ms, RTP silence after spawn ~152 ms and
  decoder output gap 287 ms overlap in time; 152 + 191 exceeds 287, so the
  resync window and the silence window cannot be additive.

The lead is not discarded — the IDR wait is still the best available explanation
for most of the gap. It is re-registered with its premise corrected.

## Consequences

| Item | State after this decision |
| --- | --- |
| `C3.L2` Linux actuator classification | **COMPLETE** |
| `C3.L2a` first-IDR acceptance investigation | **REGISTERED / NEXT** |
| `C3.L3` Linux fixed-bitrate envelope revalidation | UNBLOCKED for manual characterization; sequenced after `C3.L2a` |
| `C3.L4` fast-down/slow-up controller | **BLOCKED**; gate is `C3.L2a` |
| C4 adaptive FEC | DEFERRED, unchanged |

## `C3.L2a` — pre-registered next diagnostic

**Narrow question:** why is the receiver's first accepted IDR late after an
encoder-only cycle, when the replacement stream's first frame is a keyframe?

**Evidence first, no code change first.** The project rule is not to guess where
existing instrumentation can answer the question. `logs/games/decoder_sessions/*.json`,
`logs/games/native_video_alpha.log` and the two stored `C3.L1` / `C3.L1R1`
payloads already carry per-session decoder detail, and
`PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/RtpH264Receiver.kt`
holds the resync and IDR-acceptance policy. `C3.L2` did not re-audit that
receiver source; `C3.L2a` starts there.

Candidate causes to discriminate, in priority order:

1. **The first IDR arrives but is unusable.** Its fragments span FEC groups at
   the discontinuity; the sessions recorded 33 lost packets and 2 unrecoverable
   groups. A damaged first keyframe forces a wait for the next one, which at GOP
   15 / 60 fps is 250 ms later — matching the observed magnitude without any
   encoder change.
2. **The swap damages the first FEC groups.** The encoder-down window leaves a
   partially filled group; the relay flushes on marker or timestamp change, so
   the group boundary across the SSRC change deserves direct inspection.
3. **Receiver resync policy discards it.** The receiver may drop until it has
   both parameter sets and a clean sequence baseline, discarding the first IDR
   as part of resync rather than because it was damaged.
4. **Encoder ramp.** Largely excluded already: the ~152 ms of RTP silence is
   measured before resume, while the resync figure is measured after it.

**Pre-registered decision boundary**, declared before the run:

- if the first IDR is being discarded for a recoverable reason and the fix
  reproducibly brings the decoder output gap to **≈120 ms or below** with
  lifecycle preserved — that is the 287 ms gap less the ~191 ms resync term —
  reopen the automatic-adaptation question, with a focused gameplay observation
  required before any acceptance;
- if the gap lands between **~120 ms and ~250 ms**, the remaining cost is not
  first-IDR acceptance; the actuator stays non-automatic and the next question is
  pipeline re-establishment, not more IDR work;
- if the gap is **unchanged** or lifecycle regresses, the lead is falsified and
  closed; the next real item is the encoder-host architecture question, and
  `C3.L3` proceeds under manual actuation.

Constraints carried into `C3.L2a`: loopback-only, no change to resolution, frame
rate, GOP, B-frames, FEC wire format, RTP payload type, packet size, ports,
process audio, controller transport, emulator lifecycle, Android streaming
constants, or any non-loopback control surface. No acceptance threshold is
encoded in any probe.

## Negative results recorded by this work item

- No new runtime evidence was produced; none was required, and none is claimed.
- The "request an immediate IDR" lead is recorded as **premise-corrected**, not
  as a validated plan. Acting on it as written would have changed an encoder
  that already emits a keyframe first.
- Two headline figures from `C3.L1` / `C3.L1R1` are re-qualified as whole-session
  maxima rather than per-cycle measurements. The 287-318 ms decoder output gap is
  unaffected; it is the measurement the host probe cannot influence.
- The Android receiver source was not re-audited here. That is a known gap in
  this classification, and it is the first task of `C3.L2a` rather than a silent
  omission.

## Privacy

No network addresses appear in this record.
