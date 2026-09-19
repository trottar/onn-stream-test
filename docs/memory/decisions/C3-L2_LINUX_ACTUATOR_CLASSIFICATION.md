---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# C3.L2 — Linux actuator capability classification

**Status:** Accepted classification (2026-09-18). **Premise corrected
2026-09-19** — see "Correction: reason 1's premise is falsified" and
"Consequences" below. The classification itself stands; one of its four
supporting reasons does not.

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

1. ~~**The gap is a distinct artifact class, not measurement noise.** 287 ms is
   roughly 17 frame intervals at 60 fps. The Linux steady-state baseline is
   queue depth 0, ~59.45 fps, and the post-cycle recovered output gap was 5 ms.
   The actuator gap is nearly two orders of magnitude above the stream's own
   settled continuity.~~ **FALSIFIED 2026-09-18 by `C3.L2a` E2. Struck, not
   deleted — see the correction section below. Do not reason from it.**
2. **An automatic controller fires under pressure.** A capacity/latency
   controller decides to step down precisely when delivery is already degrading.
   A fast-down/slow-up policy produces transitions repeatedly rather than once,
   and it produces them at the moment the experience is already worst. *(Stated
   here without a magnitude: the original text said "a deliberate ~290 ms
   discontinuity", which the correction below falsifies. The argument does not
   depend on the size of the transition and survives without it.)*
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
- It does not claim any transition size is perceptible, or imperceptible. That
  is undecided, and it is the reason automatic use is not authorized. After the
  2026-09-18 correction the undecided question is sharper: not "is ~290 ms
  perceptible" but "are repeated, unannounced, under-pressure transitions
  perceptible", which is a different question and still unanswered.
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

Original table, as written 2026-09-18 (kept for history):

| Item | State after this decision |
| --- | --- |
| `C3.L2` Linux actuator classification | **COMPLETE** |
| `C3.L2a` first-IDR acceptance investigation | **REGISTERED / NEXT** |
| `C3.L3` Linux fixed-bitrate envelope revalidation | UNBLOCKED for manual characterization; sequenced after `C3.L2a` |
| `C3.L4` fast-down/slow-up controller | **BLOCKED**; gate is `C3.L2a` |
| C4 adaptive FEC | DEFERRED, unchanged |

**Current state as of 2026-09-19 — this table is authoritative:**

| Item | State |
| --- | --- |
| `C3.L2` Linux actuator classification | **COMPLETE**; premise corrected, decision unchanged |
| `C3.L2a` first-IDR acceptance investigation | **ANSWERED** 2026-09-18; IDR wait falsified |
| `C3.L2b` decoder-report cycle retention | COMPLETE / RUNTIME VALIDATED |
| `C3.L2c` low-latency decode candidate | **FALSIFIED / ROLLED BACK** 2026-09-19 |
| `C3.L3` Linux fixed-bitrate characterization | **COMPLETE / RUNTIME VALIDATED** 2026-09-19 |
| `C3.L3a` gameplay acceptance probe | **REGISTERED / NEXT**; this is the `C3.L4` gate |
| `C3.L4` fast-down/slow-up controller | **BLOCKED**; gate is `C3.L3a`, no longer `C3.L2a` |
| C4 adaptive FEC | DEFERRED, unchanged |

## Correction: reason 1's premise is falsified

Recorded 2026-09-19. Source: `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

This decision was made on the belief that an encoder-only cycle costs 287-318 ms
of decoder output gap. It does not. In the one session that instrumented the
cycle directly, the SSRC change at 43,443 ms was followed by an accepted IDR at
43,471 ms — **27 ms, access unit complete, no FEC repair, no unrecoverable
group** — and **no slow event registered at or near the cycle at all**. The same
session's two ordinary sequence resyncs cost 195 ms and 210 ms, and its worst
output gaps, 359 ms and 352 ms, followed those resyncs and tracked `codec_ms`.

287-318 ms was a whole-session maximum attributed to the cycle by inference.
This record's own "Negative results" section already warned that
`max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` were whole-session
values; the same caution applied to the output gap and was not drawn.

What this changes:

- **reason 1 is struck.** There is no measured actuator artifact to call a
  distinct class;
- **reason 2 survives without its magnitude.** A controller still fires under
  pressure and still transitions repeatedly rather than once. That is an
  argument about frequency and timing, not size;
- **reasons 3 and 4 survive unchanged**, and reason 3 is now the whole gate;
- **the classification is unchanged.** `video_only_restart` for manual use,
  blocked for automatic use. A cheaper actuator than believed is not, by
  itself, an argument for firing it automatically.

The pre-registered `C3.L2a` boundary below anticipated three outcomes and got a
fourth: not "the fix brings the gap under 120 ms", not "the gap is 120-250 ms",
not "the gap is unchanged", but **the gap was never the actuator's**. No fix was
applied and none is owed. Treat the three branches as spent.

## The `C3.L4` gate, stated so it can be satisfied

Added 2026-09-19. Until now this record named a gate — reason 3's "focused
gameplay observation" — without saying what would satisfy it, and sessions have
repeatedly proposed the wrong thing in good faith.

**What does not satisfy it.** A manual cycle or two with a subjective read.
That observation was performed on 2026-09-18, reported the session playable with
no freeze attributed to the cycle, and reason 3 already ruled it insufficient:
it is acceptance of a single operator-initiated transition. Repeating it
produces the same non-answer.

**What does not satisfy it, second form.** Transport or decoder timing at any
sample size. `C3.L3` produced three valid samples per bitrate and measured no
perceptual quantity at all. `C3.L2c` is the standing proof that the two are not
interchangeable: it improved `max_codec_ms` to the best of eight same-day
sessions and the user's verdict on the build was still "trash".

**What satisfies it.** A gameplay session in which transitions are:

1. **repeated** — several within one session, not one;
2. **unannounced** — fired at intervals the player does not know in advance,
   so the report is an observation and not a confirmation;
3. **controlled** — at least one interval in which no transition fires, so a
   reported disturbance can be checked against a period with nothing to blame;
4. **checked after the fact** — the player's marks compared against
   `stream_discontinuities` `elapsed_ms` in the decoder session report, which
   `C3.L2b` exists to provide, *after* the session rather than during it.

A session meeting all four, in which the player's marks do not align with the
cycle times, satisfies the gate. A session in which they do align answers
`C3.L4` in the negative, cheaply.

**Destination quality is a separate, unmeasured question.** Nothing has
established that 5000 or 5500 kbps *looks* acceptable. A fast-down controller
whose destination is visually poor fails even if every transition is invisible.
The gate observation should park at the candidate bitrates long enough to judge
the picture.

`C3.L3a` owns this observation. It is diagnostic-only, it authorizes nothing,
and it is registered in `CURRENT.md`, `roadmap/STATUS.md`,
`PHASE_C_CONTEXT.md` and `investigations/ACTIVE.md`.

## `C3.L2a` — pre-registered next diagnostic

**Narrow question:** why is the receiver's first accepted IDR late after an
encoder-only cycle, when the replacement stream's first frame is a keyframe?

**Evidence first, no code change first.** The project rule is not to guess where
existing instrumentation can answer the question. `logs/games/decoder_sessions/*.json`,
`logs/games/native_video_alpha.log` and the two stored `C3.L1` / `C3.L1R1`
payloads already carry per-session decoder detail, and
`PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt` (path as of the
2026-09-18 `ANDROID-FLAT` flattening; this record originally named the
pre-flatten `com/safeiot/privyhub/` path)
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
