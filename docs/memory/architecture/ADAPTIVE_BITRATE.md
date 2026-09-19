---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# Adaptive Bitrate Architecture

## Status

**C3.1 SOURCE/POLICY AUDIT: COMPLETE**

**Production adaptive bitrate: NOT IMPLEMENTED**

**Linux actuator capability:** `video_only_restart`, classified by `C3.L2`.
Authorized for start-time, manual, fallback and characterization use; not
authorized for automatic in-game adaptation.

**Next diagnostic:** `C3.L2a` — first-IDR acceptance after an encoder-only
cycle.

Sections appear in the order they were written. Later sections are
authoritative where they disagree with earlier ones; the Linux sections at the
end supersede Windows-era numbers for the Linux backend.

C3 changes bitrate first while holding the validated reference stream at
1280x720, 60 fps, GOP 15, B-frames 0 and FEC group size 8.

C3 consumes the already-runtime-validated `privyhub_stream_telemetry_v1`
contract. It does not create another Android sampler.

## Exact source findings

Audited synchronized checkpoint:

`da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0`

The current telemetry contract already exposes the measurement families C3
needs: receiver delivery/FPS/loss/jitter, FEC recovery/unrecoverable groups,
sender pressure, control-path latency, receive/decode/output-gap timing,
decoder queue depth/change and decoder drop counters.

The current reference profile has:
- target bitrate 7000 kbps;
- max bitrate 7000 kbps;
- no minimum bitrate field.

That omission was deliberate in C1.1 because no lower bound had been
characterized.

## Actuator discovery

The current encoder command is static at process creation:

- FFmpeg receives fixed `-b:v`;
- FFmpeg receives fixed `-maxrate`;
- FFmpeg is launched with `-nostdin`;
- WGC bridge stdout is connected directly to FFmpeg stdin;
- after FFmpeg inherits the read handle, the parent closes its duplicate.

Therefore PrivyHub currently has **no live bitrate actuator**.

A controller must not be built around a nonexistent setter.

Killing the current FFmpeg process also closes the only reader of the WGC raw
video pipe. The existing full stop path also stops audio/controller session I/O
and FEC. Blindly using full stream restart as an adaptation primitive would
violate established lifecycle preservation boundaries.

## Backend-neutral actuator contract

C3 should introduce an internal video-encoder control boundary before the
controller:

```text
encoder actuator
  capability:
    live_bitrate_reconfigure
    video_only_restart
    unsupported

  apply_bitrate(target_kbps)
    -> applied / failed
    -> effective bitrate
    -> actuator mode
    -> interruption/resync measurements
```

The adaptation controller must consume this boundary rather than knowing how
FFmpeg/NVENC implements bitrate changes.

This keeps the future Linux implementation free to use a different encoder
backend while preserving one adaptation policy.

## C3 control cadence

Reuse the accepted 2-second telemetry cadence.

Do not add:
- a second receiver sampler;
- a high-frequency congestion loop;
- per-packet adaptation decisions.

The controller evaluates only accepted fresh telemetry snapshots.

## C3 safety state

The controller must have explicit states, not scattered conditionals.

Minimum conceptual states:

- `REFERENCE`;
- `HOLD`;
- `PRESSURE`;
- `HOLD_DOWN`;
- `RECOVERY_PROBATION`;
- `TELEMETRY_STALE`;
- `ACTUATOR_FAILED`.

Exact implementation names may differ, but equivalent state must be inspectable.

## Fast-down / slow-up rule

C3 must be asymmetric:

- decreasing quality reacts faster than increasing it;
- an increase must require a longer clean period than a decrease requires
  pressure evidence;
- after any decrease, a hold-down period prevents immediate reversal;
- one decision changes at most one validated bitrate level;
- no sample may trigger multiple steps;
- repeated up/down oscillation is a failed acceptance result.

Timing constants must be multiples of the existing 2-second telemetry interval
and are tuned only after actuator and bitrate-envelope characterization.

## Signal interpretation

C3 is a capacity/latency controller.

Evidence that may support bitrate decrease:
- positive decoder queue growth;
- sustained nonzero decoder queue depth;
- worsening output continuity/output gap;
- worsening receive-to-decode latency;
- delivered-stream degradation;
- unrecoverable FEC groups when corroborated by capacity/latency pressure;
- sender-pressure growth when corroborated by receiver degradation.

Evidence that must not independently force bitrate decrease:
- recovered FEC packets alone;
- stale-output drops alone;
- one isolated random-loss event without capacity/latency pressure;
- source/request network identity;
- a sender error better classified as a transport/host fault;
- `waiting_for_idr` during a known stream resync.

D-019 remains authoritative: stale-output shedding alone is informational.

C4 later owns adaptive FEC.

## Telemetry freshness and fail-safe behavior

If telemetry is stale, unavailable, lacks required deltas, or is in receiver
resync:

- do not increase bitrate;
- do not make a blind decrease from incomplete evidence;
- freeze at the last successfully applied validated bitrate;
- expose an explicit hold reason.

At a new session with no prior successful adaptive level, the known reference is
7000 kbps.

An actuator failure freezes further adaptation for that session.

## Bitrate bounds

The upper bound is evidence-backed now:

`max = 7000 kbps`

A production lower bound is **not yet evidence-backed**.

Therefore:
- do not add a guessed `min_bitrate_kbps` yet;
- do not ship a guessed production bitrate ladder;
- after actuator feasibility is known, run fixed-bitrate characterization using
  the same 720p60/GOP/FEC settings;
- only validated levels enter the production ladder;
- the lowest validated level becomes the C3 minimum.

## Decision diagnostics

Every automatic C3 decision must be explainable.

Planned companion-facing adaptation status:

`privyhub_adaptive_bitrate_v1`

Conceptual fields include state, current/target bitrate, validated levels,
telemetry freshness/age, decision sequence, reason code, reason measurements,
hold-down, clean-sample count, actuator capability/mode and last actuator
result.

No source/request address identity belongs in this contract.

## First narrow diagnostic

Before production adaptation code, answer one question:

Can the current video path perform one controlled video-actuator cycle while
preserving audio/controller/game lifecycle and returning the Android receiver to
clean IDR/rendered continuity quickly enough to be a viable adaptation
mechanism?

The probe keeps bitrate unchanged at 7000 kbps. It measures interruption,
receiver resync/IDR recovery, render continuity, decoder queue state, packet/FEC
deltas, and preservation of audio/controller/lifecycle.

If video-only restart is acceptable, C3 may use it initially with conservative
hold-down. If it is not, move to true live encoder reconfiguration.

## C3 staging after this design

1. `C3_ACTUATOR_CONTINUITY_PROBE`
2. choose `video_only_restart` or `live_bitrate_reconfigure`
3. fixed-bitrate envelope/quality characterization
4. freeze validated bitrate levels/minimum
5. implement explainable fast-down/slow-up controller
6. runtime adverse-condition validation
7. normal Games regression
8. checkpoint C3 before adaptive FEC

## Non-goals

C3 does not change resolution, frame rate, GOP/B-frames, FEC group size, WAN
routing, source identity, audio/controller architecture, or C4 adaptive FEC.

## C3 actuator continuity probe implementation

**Status:** RUNTIME VALIDATED / `video_only_restart` ACCEPTED FOR INITIAL C3

The first actuator candidate is a same-bitrate video-only cycle:
- stop old FFmpeg then old WGC capture;
- leave FEC relay running;
- leave process audio running;
- leave persistent controller running;
- launch replacement WGC capture against the same managed RetroArch HWND;
- launch replacement FFmpeg at the unchanged 7000 kbps reference settings;
- measure host time until FEC observes RTP again.

The diagnostic action is loopback-only.

The Android production app is unchanged. Existing decoder-session reporting
already supplies SSRC/resync/IDR, decoder output-gap, audio and controller
evidence after normal End.

No threshold for acceptable interruption is encoded in the probe. Raw
measurements and manual gameplay behavior decide whether restart-based actuation
is viable.

## Accepted actuator portability boundary

D-063 accepts `video_only_restart` as the initial C3 actuator **strategy**, not
WGC as a cross-platform implementation.

Controller-facing contract:

```text
adaptive bitrate controller
        |
        v
backend-neutral video actuator
        |
        +-- Windows: WGC + FFmpeg/NVENC video-only restart
        |
        `-- Linux: selected Linux capture + encoder video-only restart
```

The stable boundary is:
- replace/reconfigure only video-producing processes;
- keep FEC/transport ownership alive where the backend permits;
- keep process audio alive;
- keep controller alive;
- keep emulator/game-session lifecycle alive;
- require receiver IDR/resync recovery;
- expose raw interruption/recovery measurements.

Linux migration acceptance must rerun this continuity test. If the Linux
backend cannot meet the same lifecycle boundary, revisit live encoder
reconfiguration there without changing the controller policy.

## Fixed-bitrate characterization

After D-063, lower bitrate levels are established one at a time.

The first candidate is 6000 kbps. It keeps:
- 1280x720;
- 60 fps;
- GOP15;
- B-frames0;
- FEC8.

The reference profile remains 7000 kbps. The stream manager now distinguishes
the immutable reference bitrate from the **active encoder bitrate** so
diagnostics do not claim 7000 after a fixed-bitrate actuator cycle.

Normal sessions still start/reset to the reference. Only the loopback-only C3
characterization action changes the active development bitrate.

A candidate becomes a production ladder level only after technical and focused
visual-quality acceptance.

## Validated bitrate candidate 6000

6000 kbps is validated as a lower C3 candidate at unchanged
1280x720@60/GOP15/B-frames0/FEC8.

The characterization result must not be conflated with the independent audio
transport pathology. At 6000, the Android audio queue repeatedly reached its
8-packet cap and trimmed old PCM while also recording prolonged starvation and
concealment. That simultaneous overflow/starvation pattern is evidence of
bursty delivery/scheduling, not simple insufficient average video bitrate.

The bitrate ladder remains under characterization. Current evidence-backed
levels:
- 7000 kbps: validated reference/max;
- 6000 kbps: validated lower candidate.

Next candidate: 5000 kbps.

No minimum or automatic controller is set until lower-level characterization
finishes.

## 5000 characterization implementation

The fixed-bitrate characterization actuator now has one shared internal
video-cycle implementation with stable loopback-only wrappers for the individual
test points.

Installed wrappers:
- 6000 kbps — previously runtime validated;
- 5000 kbps — runtime evidence pending.

This avoids parallel actuator implementations while preserving the exact
candidate-at-a-time characterization workflow.

All candidate cycles still start from the 7000 reference and preserve
1280x720@60, GOP15, B-frames0, FEC8, process audio, controller and game
lifecycle.

The production ladder/minimum is not defined merely by installing a wrapper; a
candidate becomes evidence-backed only after runtime and focused quality
acceptance.

## 5000 result and current bitrate bracket

5000 kbps is technically viable but not accepted as a production-ladder
candidate in the current environment.

The reason is steady-state presentation quality: after the transition settled,
focused play showed definitely more visual stutters than the validated 6000 and
7000 settings. Subjective image clarity at 5000 does not override that
smoothness regression.

Current evidence-backed state:
- 7000 kbps: validated reference/max;
- 6000 kbps: validated lower candidate;
- 5000 kbps: runtime tested / not accepted;
- bracket for the lower usable boundary: 5000–6000 kbps.

Next test point: 5500 kbps.

The audio burst/gap pathology remains independently deferred and is not part of
the 5000 rejection criterion.

## 5500 midpoint bracket characterization

The shared fixed-bitrate characterization actuator now exposes loopback-only
wrappers for:
- 6000 kbps — validated;
- 5000 kbps — runtime tested / not accepted;
- 5500 kbps — runtime evidence pending.

All wrappers use the same internal video-only cycle. No parallel actuator
implementation is introduced.

The pre-test lower boundary is 5000–6000 kbps. 5500 is the midpoint test.

All candidate cycles retain 1280x720@60, GOP15, B-frames0, FEC8, process audio,
persistent controller and game lifecycle.

A 5500 pass would make it an evidence-backed candidate; a 5500 smoothness
failure would move the practical lower boundary upward toward 6000. Production
minimum and controller policy remain undefined until the fixed envelope is
resolved.

## D-066 fixed ladder for adaptive controller

The Windows C3 adaptive controller uses three fixed evidence-backed targets:

- 5500 kbps — low;
- 6000 kbps — medium;
- 7000 kbps — high/reference.

5000 kbps is excluded from the ladder because focused extended play showed more
steady-state visual stuttering.

5500 is accepted because focused steady-state gameplay was excellent after a
short initial transition, and the stored six post-cycle C2 telemetry intervals
showed zero decoder-drop/overflow deltas across 638 rendered frames.

The final decoder-session report still recorded 57 whole-session
drop/queue-overflow events. Their timing outside the sampled interval is
unresolved and must remain visible in evidence. Controller policy must reason
from fresh interval deltas rather than blindly reacting to cumulative
whole-session totals.

The controller should treat actuator transitions as a stabilization period:
freeze further bitrate decisions while telemetry is stale/unavailable or the
receiver is resynchronizing, and require fresh post-transition evidence before
another decision. Exact timing/hysteresis remains controller implementation
work.

This fixed envelope is Windows-runtime validated. Linux backend migration must
revalidate the actuator and fixed bitrate envelope before these thresholds are
treated as portable constants.

## Startup/resume readiness boundary — D-067

Adaptive bitrate policy operates only after gameplay readiness.

Startup states:
`LAUNCHING -> STABILIZING -> READY -> PLAYING`.

Freeze automatic adaptation during STABILIZING or PAUSED. Static paused-scene
telemetry is not representative gameplay evidence. Future bitrate transitions
must also receive fresh post-transition telemetry before another decision.

D-067 does not enable automatic adaptation; it establishes the lifecycle/status
boundary first.

## Startup readiness boundary runtime validated — D-068

D-067's startup readiness boundary is runtime validated on the current Windows +
onn environment.

The gate successfully hid the known initial gameplay lag after a clean
companion restart.

Controller implementation may now rely on:
`LAUNCHING -> STABILIZING -> READY -> PLAYING`

Adaptation remains frozen during STABILIZING/PAUSED and is still not
implemented.

Operational prerequisite: if companion Python changes, restart the companion
before validating policy/actuator behavior.

## Bidirectional actuator gate before controller — D-069

The final actuator prerequisite before automatic policy is upward-transition
validation.

Existing fixed characterization starts at the 7000 reference and moves down.
The controller must also move upward after sustained clean conditions.

D-069 therefore validates:
`7000 -> 6000 -> 7000`.

The low-level video-only restart implementation is shared with fixed
characterization. Diagnostic mode expands allowed start/target states only to
the validated 5500/6000/7000 ladder; existing characterization wrappers still
require a 7000 reference start and retain 5000 only as historical diagnostic
coverage.

The probe waits for two consecutive clean existing C2 telemetry intervals after
the downshift before attempting the upshift. This is a safety gate for the
probe, not the final hysteresis/hold-down policy.

Automatic adaptation remains unimplemented until runtime evidence accepts both
directions.

## Video-only restart rejected for automatic policy — D-070

The C3 capability classification is refined:

- `video_only_restart`: runtime validated in both directions, but unsuitable for
  seamless automatic active-game adaptation because it creates ~0.84-0.95 s RTP
  interruption and a user-visible ~1 s freeze.
- `live_bitrate_reconfigure`: next actuator capability to investigate.
- `unsupported`: fallback classification if a backend supports neither.

Automatic policy must not use `video_only_restart` for routine fast-down/slow-up
changes during active gameplay.

A backend may still expose restart as diagnostic/startup/manual/fallback
behavior.

The controller remains blocked until a low-interruption actuator is validated.

## Linux migration boundary for adaptation — D-071

Windows-specific actuator development stops after D-070.

Do not pursue NVENC-specific live bitrate control solely for the outgoing
Windows prototype.

Preserve the backend-neutral capability model:
- `live_bitrate_reconfigure`;
- `video_only_restart`;
- `unsupported`.

Current Windows classification:
- `video_only_restart`: bidirectionally functional, ~1 s interruption, fallback
  only for active gameplay;
- `live_bitrate_reconfigure`: intentionally not pursued on Windows;
- automatic controller: deferred to Linux.

New Phase D establishes the Linux backend.
New Phase E must classify Linux actuation and revalidate fixed levels.
Only then resume controller thresholds/hysteresis/hold-down implementation.

The Windows 5500/6000/7000 ladder is evidence, not a Linux product constant.

Adaptive FEC remains deferred to representative Linux transport evidence.

## Linux actuator boundary audit — C3.L0

Audited at `310596dd0cc3ff22f3fe46e2eb025d052da90ec0`. Source only; no runtime
execution and no production change.

The backend-neutral capability model from D-071 is retained unchanged:
`live_bitrate_reconfigure`, `video_only_restart`, `unsupported`.

Current Linux classification:

- `live_bitrate_reconfigure`: **foreclosed by the current architecture.** The
  encoder is an external FFmpeg CLI launched with `-nostdin` and
  `stdin=DEVNULL`, with `-b:v`/`-maxrate`/`-bufsize` baked into argv at `Popen`
  time. There is no control socket, no ZMQ filter and no in-process libavcodec
  handle. Reaching this capability requires an in-process encoder or a
  controllable encoder host. That is an architecture change, not a patch. This
  is a statement about the current architecture, not about h264_vaapi hardware.
- `video_only_restart`: **not implemented on Linux.** `_start_linux_locked`
  calls `_stop_locked()`, which also stops the FEC relay, session I/O and host
  telemetry, violating the lifecycle-preservation boundary. A narrow
  encoder-only seam must be added before the continuity test can run.
- interruption cost: **unmeasured on Linux.**

### Topology difference that motivates measuring rather than assuming

Windows runs two managed video processes: the WGC bridge writes raw frames into
FFmpeg's stdin over an inherited pipe, so a video-only restart must replace both
and re-handshake the pipe.

Linux runs one process; `_running_locked()` asserts `_capture_process is None`
because x11grab is an FFmpeg input format. A Linux encoder-only restart is one
`Popen` with no pipe handoff and no capture-metadata first-frame wait.

The Windows 0.84-0.95 s RTP gap therefore does not transfer in either
direction, and D-070's rejection cannot be assumed to hold on Linux until
measured.

### Parameters other than bitrate

Resolution and FPS are **client-pinned, not negotiated**. `NativeStreamActivity`
holds them as compile-time constants and passes them to
`AvcLowLatencyDecoder`, which configures MediaCodec once, does not derive
dimensions from the in-band SPS, and ignores `INFO_OUTPUT_FORMAT_CHANGED`.
Changing either requires an APK change, not merely a restart. GOP is expressed
in frames, so an FPS change silently rescales the keyframe interval in seconds.
These remain C3 non-goals.

FEC group size is the only in-place seam in the system. The FEC header carries
the real group length and the receiver validates 1 to 8, so mutation would need
no encoder restart, SSRC change, resync or IDR wait. No setter exists and no
runtime evidence exists. **C4 continues to own adaptive FEC.**

Pacing has no owner and no actuator, consistent with the
`architecture/STREAM_TELEMETRY.md` rule against importing probe-style pacing
semantics into the live stream.

### Existing C3 probes do not run on Linux

`companion/diagnostics/c3_actuator_probe.py` and
`companion/diagnostics/c3_fixed_bitrate_probe.py` require `_wgc_ready()`, an
HWND capture target and `_build_ffmpeg_command`. On Linux they fail closed with
`wgc_runtime_unavailable` before modifying anything. They are correct as
written; they are simply not reusable without a Linux cycle implementation
behind the same probe structure.

### Next

`C3.L1` — Linux encoder-only restart continuity probe, same bitrate 7000 to
7000, loopback only, no acceptance threshold encoded. Full plan in
`investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.

## Linux encoder-only actuator runtime result — C3.L1 / C3.L1R1

The Linux actuator exists and was measured. Evidence:
`../evidence/C3_L1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` and
`../evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md`.

Implementation: `companion/diagnostics/c3_linux_actuator_probe.py`, selected by
platform inside `NativeStreamManager.diagnostic_c3_actuator_continuity_cycle()`.
It replaces only the encoder and never calls `_stop_locked()`, so the FEC relay,
process audio, persistent controller and emulator all stay up.

Lifecycle preservation passed on both runs: zero FEC send errors, zero audio
write errors, zero controller send errors, exactly one SSRC change per cycle,
receiver not waiting for IDR at session end.

Interruption, on `decoder_max_output_gap_ms` measured at the receiver:

| Run | Backend | Gap |
| --- | --- | ---: |
| Windows D-062 same-bitrate | WGC + NVENC | 791 ms |
| Windows D-070 bidirectional | WGC + NVENC | 1,059 ms |
| Linux `C3.L1` same-bitrate | x11grab + VAAPI | 318 ms |
| Linux `C3.L1R1` same-bitrate | x11grab + VAAPI | 287 ms |

Linux is ~2.5-2.75x better than the directly comparable Windows run, as the
single-process topology predicted. D-070's interruption figures are not portable
to Linux and are not used to classify it.

Read the supporting figures with care: `max_resync_to_idr_ms` and
`packets_dropped_waiting_for_idr` are whole-session values against two sequence
resyncs per session, and spawn, RTP silence and decoder gap overlap in time
rather than summing.

## Linux actuator classification — C3.L2

Decision record: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

The backend-neutral capability model is unchanged. Current Linux classification:

- `live_bitrate_reconfigure`: **not available.** The encoder is an external
  FFmpeg CLI with bitrate baked into argv at `Popen` time and no control
  channel. This is an architecture statement, not a VAAPI capability statement.
- `video_only_restart`: **runtime validated**, 287-318 ms decoder output gap,
  lifecycle preserved twice.
- `unsupported`: does not apply.

Controller-facing consequence, which is the part that matters to this
architecture:

```text
adaptive bitrate controller            <- still BLOCKED on Linux
        |
        v
backend-neutral video actuator
        |
        +-- Windows: WGC + FFmpeg/NVENC video-only restart   (~1 s, fallback only)
        |
        `-- Linux: x11grab + VAAPI encoder-only restart      (~290 ms, non-automatic)
```

The actuator is authorized for session start and start-time profile selection
before `READY`, for manual and loopback-only diagnostic changes, for fallback
and recovery including replacing a dead encoder, and for `C3.L3`
characterization cycles. It is not authorized for automatic adaptation during
`PLAYING`.

Rationale in short: the gap is ~17 frame intervals against a settled stream
whose post-cycle output gap was 5 ms; an automatic controller fires under
pressure, when a deliberate discontinuity costs most; one accepted manual cycle
is not evidence for repeated automatic ones; and a lead to reduce the cost
exists but is untested.

Unchanged by this classification: the fast-down/slow-up asymmetry, the 2-second
telemetry cadence, the safety states, the freshness and fail-safe rules, the
signal-interpretation rules, and the requirement that every automatic decision
be explainable. Those remain the policy the controller will implement once an
actuator is authorized for automatic use.

Still not established on Linux: bidirectional and upward transitions, any
bitrate ladder or minimum, and whether a ~290 ms automatic interruption is
acceptable. `C3.L3` owns the envelope; `C3.L2a` owns the interruption cost.

## C3.L3a design — Linux ladder transition and gameplay acceptance probe

**Status: DESIGNED, 2026-09-19. Not yet built or run.** This section records
the design produced before authorization, per `CURRENT.md`'s own gate:
present the plan first, build only after it is authorized.

### The ladder

`LINUX_LADDER_BITRATES_KBPS = (5000, 5500, 6000, 7000)`. All four are already
timing-characterized on Linux: 7000 is the reference/baseline; 5000, 5500 and
6000 were measured by `C3.L3` (`decoder_max_output_gap_ms` bands 125/365/40 ms
respectively). None has been quality-accepted — that is exactly what `C3.L3a`
gathers evidence for. Adding a fifth rung (for example 6500, to fill a gap
between two existing levels) is not a decision this probe makes for itself: a
new rung needs its own `C3.L3`-style timing characterization pass before it
joins the ladder, mirroring how 5500 itself was added as a midpoint bracket
test between 5000 and 6000. `C3.L3a`'s job with the current four-point ladder
is to find out whether that ladder is already fine/coarse enough, or whether a
gap needs filling — not to guess at arbitrary intermediate bitrates.

### Why the existing precondition blocks C3.L3a, and the fix

`run_c3_linux_fixed_bitrate_cycle` (`C3.L3`) requires `current_bitrate_kbps ==
7000` and `target in (5000, 5500, 6000)`. As written it supports exactly one
transition per session, which cannot rehearse "several transitions... not
one" (the `C3.L4` gate's first requirement).

The fix reuses a precedent already set on Windows rather than inventing a new
shape: D-069's `_run_c3_fixed_bitrate_cycle(..., validated_transition: bool =
False)` on Windows already distinguishes a one-shot characterization
precondition from a bidirectional-ladder precondition restricted to a named,
validated set (`VALIDATED_ADAPTIVE_BITRATES_KBPS`). **Correction, `C3-L3A-P1` (installed 2026-09-19).** The text that stood here
said the Windows code "stays untouched and historical; only its precondition
*shape* is reused", and proposed a new `ladder_transition` flag plus a new
companion method and route. A source audit before building found more of the
seam already present than that assumed:

- `run_c3_validated_bitrate_transition()` and
  `VALIDATED_ADAPTIVE_BITRATES_KBPS` exist in
  `companion/diagnostics/c3_fixed_bitrate_probe.py`;
- `NativeStreamManager.diagnostic_c3_validated_bitrate_transition()` already
  exists in `companion/native_stream.py`;
- the loopback-only route already exists in `companion/plugins/games.py`,
  allowlisting `{5500, 6000, 7000}`;
- `BIDIRECTIONAL_SCHEMA` and `BIDIRECTIONAL_MODE` already exist.

The dispatch called the Windows implementation unconditionally, so on Linux
it failed exactly the way the fixed-bitrate cycles did before `C3.L3`. The
seam was built for D-069 and simply never ported. Building a parallel
`ladder_transition` flag beside it would have been a second implementation of
an existing path, which this project's principles forbid. **What shipped is
the port, under the existing names.**

- `_run_c3_linux_bitrate_cycle(..., validated_transition: bool = False)`
  holds one body with two preconditions, mirroring the Windows
  `_run_c3_fixed_bitrate_cycle` split;
- `run_c3_linux_fixed_bitrate_cycle(manager, target, **kw)` — unchanged call
  shape, `validated_transition=False`, the `C3.L3` path, behaving as it did
  when `C3.L3`'s runtime evidence was produced;
- `run_c3_linux_validated_bitrate_transition(manager, *, target_bitrate_kbps,
  **kw)` — `validated_transition=True`, keyword-only target matching the
  Windows signature so one dispatch call shape serves both;
- guards under `validated_transition=True` reuse the Windows error strings
  verbatim: `unsupported_validated_bitrate`,
  `validated_transition_requires_validated_start`, `bitrate_transition_noop`.

Restart mechanics are identical in both modes — kill, RTP baseline after the
kill, spawn, poll for resume, 0.75 s stability window.

One guard deliberately does **not** relax: `manager.BITRATE_KBPS` and
`MAX_BITRATE_KBPS` must still be 7000. That asserts the configured reference
profile is untampered, a different claim from where the stream currently sits.

**Ladder divergence, deliberate.** Linux is `(5000, 5500, 6000, 7000)`;
Windows `VALIDATED_ADAPTIVE_BITRATES_KBPS` is `(5500, 6000, 7000)`. 5000 kbps
has three valid Linux characterization samples from `C3.L3` and none on
Windows. The shared route allowlists the union and each platform's
implementation rejects what it has not characterized, so a 5000 kbps request
on Windows fails closed with `unsupported_validated_bitrate`.

This is a real precondition change, not a no-op; the default path's byte-
identical behavior is what keeps `C3.L3`'s existing runtime evidence valid
without rerunning it.

### Jump vs. ramp, and why both matter

This architecture's own fast-down/slow-up rule (above, "Fast-down / slow-up
rule") already states that one automatic decision changes at most one
validated bitrate level and no sample may trigger multiple steps. That means
the eventual `C3.L4` controller will only ever move one ladder rung at a
time — a **ramp** (7000 -> 6000 -> 5500 -> 5000, one rung per cycle) is the
routine pattern it would actually execute. A **jump** (7000 -> 5000 directly)
is not routine-adaptation behavior; it exercises the separately-authorized
fallback/recovery use case (`C3.L2`'s "fallback and recovery, including
replacing a dead encoder"). Both are worth rehearsing, but they answer
different questions and must be labeled and reported separately, never
pooled — the ramp's multiple smaller discontinuities and the jump's one
larger discontinuity are not directly comparable without knowing which
produced which mark.

### Companion primitive — no new one was needed

The design originally called for a new
`diagnostic_c3_l3a_ladder_transition()` method and a new
`POST /plugins/games/c3-l3a-ladder-transition` route. **Neither was built,
because both already existed** under the D-069 name. `C3.L3a` uses the
existing `diagnostic_c3_validated_bitrate_transition(target_bitrate_kbps)`
and its existing loopback-only route; the only route change was adding 5000
to the allowlist.

The properties the design asked for hold unchanged: the manager lock is held
for the single restart call only, never across dwell time, so all timing,
randomization and the control interval live in the probe script — matching
how every other multi-stage checkout probe in `tools/` orchestrates
client-side against a single companion primitive. **`C3.L3a` introduces no
new companion-side mechanism at all.** It authorizes nothing and adds no
controller logic.

The line that must not be crossed: the probe follows a **pre-generated
random script**. It never reads telemetry and decides a target. A sequencer
that observes conditions and picks a bitrate *is* `C3.L4`, and would have
skipped its own gate.

### The gameplay acceptance probe

`tools/probe_c3_l3a_gameplay_acceptance.py` orchestrates one play session
against the primitive above: a background thread fires a randomized,
unannounced sequence of ladder transitions (at least one full ramp, at least
one direct jump, at least one control interval where nothing fires) while the
main thread runs a non-blocking mark-capture loop — the player presses Enter
on the companion terminal the instant they notice something, timestamped
against the same clock the cycle log and the decoder's
`stream_discontinuities` use, without pausing gameplay or asking a question
mid-session (a blocking yes/no prompt would itself telegraph that a
transition just fired). The session dwells long enough at 5000/5500/6000 kbps
for the picture itself to be judged, not just measured. After the session
ends, a post-session debrief reuses the existing terminal yes/no idiom
already used by every other `tools/` checkout probe (see next section) to ask
whether each destination bitrate looked acceptable. No pass/fail threshold is
encoded in the probe anywhere — it records, the user judges, per
`investigations/ACTIVE.md`'s existing disposition rule.

### Shared checkout module

Every existing manual checkout probe (`probe_ps1_multitap_onoff_runtime.py`,
`probe_phase_a_a9_emulator_checkpoint.py`, and others in the same family)
duplicates its own copy of a `yes(prompt)` input helper and its own
`lines`-list-plus-`Classification:`-header report writer. `C3.L3a` factors
this into one shared `tools/manual_checkout.py` module — `yes()`, a report
writer matching the existing convention, and the new non-blocking mark-
capture loop — so this probe and future ones stop duplicating it. Existing
probes are not touched; this is additive only.
