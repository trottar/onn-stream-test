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

**2026-09-28 (decision, `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`):**
`C3.L4` is **AUTHORIZED for live adaptation at one transition per event**;
ramps are excluded; live build pending. See "C3.L4 live mode — the
constraint" at the end; it supersedes the "not authorized for automatic
in-game adaptation" line above for single transitions only.

**2026-09-28 (`C3-L4-L1`):** the live mode is **BUILT** behind
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, which is off by default. See "C3.L4
live mode — as built" at the end.

- On a clean link it was **SILENT** for 30 minutes.
- The decrease path is proven on injection: one transition, a 171 ms gap,
  the blackout, and the hold-down refusal.
- **The increase path never fired.** The 90-consecutive-clean rule is
  not reachable in attract mode. The user's call is pending.
- No live run has met real loss yet; that is the user's `nft` night.

**2026-09-29 (`C3-L4-L2`):** the live increase rule is now **the user's
blend** (§"C3.L4 live increase rule — the blend" at the end). Session B2
**climbed 5000 → 7000**, one rung per event.

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

## C3.L4 shadow controller — S1

Task: `../handoffs/C3-L4-S1_SHADOW_CONTROLLER_TASK.md` (weekend queue item 4,
2026-09-24). Module: `companion/adaptive_bitrate.py`. Status field:
`adaptive_bitrate` on `native-stream-status`, schema
`privyhub_adaptive_bitrate_v1`. Flag: `PRIVYHUB_ADAPTIVE_BITRATE_MODE`.
**This section implements the design above; it adds no new design.**

### The answer to `C3-L2`

`video_only_restart` is authorized for fallback and recovery. It is not
authorized for automatic adaptation during play. So the controller has
**two trigger classes**, and only the first can ever be an acting path:

1. **FALLBACK.** The stream is already failing by the close-out's own
   rows. A ~190 ms restart is cheaper than what the player is already
   getting.
2. **ROUTINE.** Capacity or latency pressure short of failure. `C3-L2`
   does not authorize it, and the gate data so far says it is noticed.
   **ROUTINE acting is gated on the user's `C3.L3a` reading and is not
   built here.**

- **Modes.** `off` is the default, and any unrecognised value reads off,
  flagged `mode_env_ignored`. `shadow` evaluates and logs. The module
  holds no actuator and no accepted mode calls one. `acted` is `false` on
  every line and in the status.
- **The two tracks.** Shadow keeps a *virtual* level. It is what the
  acting path (FALLBACK down, RECOVERY up) would have done, with its
  blackout, hold-down and oscillation guard.
- **ROUTINE is counted on its own track.** It is logged once per 30
  reports while its evidence persists. It **never moves the virtual level
  or the acting track's timers**, because a later acting mode would not
  act on it.
- **A consequence of the pre-registered numbers.** On any queue-driven
  onset, ROUTINE's 4-of-5 is met one report before FALLBACK's 5-of-5. So
  a real failure logs one ROUTINE line, then the FALLBACK. This is
  recorded, not retuned.

### Jump, not ramp

The rerun evidence: ramps were marked 11/15 and jumps 5/15.

- **A decrease is one transition.** FALLBACK goes straight to the floor
  (5000). ROUTINE's would-target is one rung down.
- **An increase is one rung per decision** (slow-up). So each step up is
  a single restart, at a long interval.

### The constants (pre-registered in the task; sources)

| constant | value | source |
| --- | --- | --- |
| ladder, reference | 5000 / 5500 / 6000 / 7000, 7000 | `D-066`, `C3.L3` |
| cadence | the 2 s client report; only fresh, distinct snapshots (`session_elapsed_ms` advanced) | §C3 control cadence; the probe's rule |
| blackout after any action | 3 reports (≥ 6 s) | `C3.L3a-S1`: settling in 1-3 reports, once 4 |
| hold-down, same direction | 30 reports (60 s) | task |
| hold-down, reversal | 60 reports (120 s) | task |
| FALLBACK | over 5 fresh reports: fps < 50 on 5/5 **and** (queue ≥ 2 on ≥ 3/5 **or** output gap > 250 ms on ≥ 2/5) | close-out band: fps 59.9, queue 0, gap ≤ 163; transport gaps 100-200 ms must not trigger |
| ROUTINE | fps < 57 on ≥ 4/5 **and** queue ≥ 1 on ≥ 3/5 | task |
| never evidence | recovered FEC, stale drops, `lost_packets_delta` alone, `waiting_for_idr` in a known resync | D-019, §Signal interpretation |
| increase | below 7000, 90 consecutive clean reports (fps ≥ 59, queue 0, gap ≤ 150), counted after the blackout → one rung up | slow-up |
| oscillation | the third direction change within 10 min → `HOLD`, reason `oscillation`, for the rest of the session | task |
| stale | not fresh, not available, or no distinct snapshot for 3 reports → `TELEMETRY_STALE`, no decision | §Telemetry freshness |

**States** are `REFERENCE`, `PRESSURE`, `HOLD_DOWN` (blackout included),
`RECOVERY_PROBATION`, `TELEMETRY_STALE`, `ACTUATOR_FAILED` (never reached
in shadow) and `HOLD` (oscillation).

**The status field** carries:

- mode, state and reason, with the reason's measurements;
- `current_kbps` (the stream's) and `shadow_level_kbps` (the virtual
  level);
- the validated ladder and the telemetry age;
- the decision sequence, the blackout and hold-down remaining, the clean
  count;
- would-act counters by class (FALLBACK, ROUTINE, INCREASE), suppression
  counters, and `acted: false`.

**The decision log** is `logs/games/adaptive_bitrate_shadow.jsonl`: one
line per decision or state change, never per report. It rotates at 4 MiB,
keeping three, into `stream_log_archive/`.

**Where it hooks.** The companion's `/diagnostics/client-health` POST
already builds the `privyhub_stream_telemetry_v1` snapshot each 2 s. The
shadow reads that payload after it is built, inside the same "must never
disturb" guard. It writes nothing back.

## Recovery's restart primitive — C3-F1 (2026-09-25)

Beside the actuator (`c3-validated-bitrate-transition`) there is recovery's
restart, `NativeStreamManager.recovery_restart_encoder()`. It is
encoder-only and **level-preserving**:

- at the 7000 reference it is the unchanged `C3.L1` continuity cycle;
- off 7000 it restarts the encoder at `_active_bitrate_kbps` through the
  transition cycle's mechanics (`privyhub_c3_recovery_restart_v1`).

It was measured WORKING at 5000, 5500, 6000 and 7000
(`../evidence/C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md`). There is a
loopback-only diagnostic route, `c3-recovery-restart`. A live controller
that moves the ladder no longer disables link-drop recovery.

## C3.L4 live mode — the constraint (DECISION, 2026-09-28)

**This is a decision, not an implementation.** No code changed with it.
Source: `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` (the user's
reading of the pooled `C3.L3a` table: W 5.0 jump 6/20 at 1.9× chance, ramp
15/20 at 3.4×, decoys at or below chance;
`../evidence/C3_L3A_R4_SESSION4_2026-09-28.md`).

A live (acting) mode, when built, must hold to:

1. **One transition per adaptation event.** The controller picks its
   target on the validated ladder and reaches it in a single
   `video_only_restart`. The ladder chooses the target; it is **not
   stepped through**.
2. **Minimum spacing between transitions = the existing hold-downs**
   (§"The constants": blackout ≥ 3 reports / 6 s after any action; 60 s
   same direction; 120 s on reversal; the oscillation guard → `HOLD`).
   Each transition is its own event under those timers.
3. **No ramps.** Three restarts four seconds apart are noticed; that shape
   is excluded from live adaptation.
4. **No sampling inside the settling window** (the blackout stays).
5. **Cost per event** stays one output gap of ~190 ms (`C3.L3a-S1`).
6. **No live run before a fault-injection night with the user's `nft`.**
   That night is the next `C3.L4` task.

The shadow's shapes already fit (1)-(3): FALLBACK is one transition to the
floor; an increase is one rung per decision behind the hold-downs. Whether
ROUTINE acts, and to what target, is the live build's design question, to
be answered inside this constraint.

## C3.L4 live mode — as built (C3-L4-L1, 2026-09-28)

Task: `../handoffs/C3-L4-L1_LIVE_CONTROLLER_TASK.md`. Module:
`companion/adaptive_bitrate_live.py`. Design note, with the reasoning for
every choice below: `../evidence/c3_l4_l1_2026-09-28/c3_l4_l1_design.txt`.
Record: `../evidence/C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md`.
**This section implements the constraint above; the shadow sections stay
true of `shadow` mode.**

**Mode.** `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`. Off (the default) and
`shadow` are unchanged, and `companion/adaptive_bitrate.py` is
byte-identical. Its suite still asserts that it accepts only off and
shadow and holds no actuator. The live module owns the third value, and
`get_controller()` builds it only for `live`.

**The mapping table** (the only source of targets):

| trigger | evidence (the shadow's, unchanged) | target | transitions |
| --- | --- | --- | --- |
| FALLBACK | fps < 50 on 5/5 and (queue ≥ 2 on ≥ 3/5 or gap > 250 ms on ≥ 2/5) | 5000 | 1 |
| ROUTINE | fps < 57 on ≥ 4/5 and queue ≥ 1 on ≥ 3/5 | 6000 | 1 |
| INCREASE | below 7000, 90 consecutive clean reports after the blackout | one rung up | 1 per event |

**Refusals.**

- A decrease whose target is not below the current level is refused:
  `at_floor`, or `at_or_below_target`. So ROUTINE acts at most once (7000
  → 6000), and deeper trouble must meet FALLBACK.
- **ROUTINE waits for FALLBACK.** While the newest report is itself
  under 50 fps, ROUTINE waits up to 4 reports. On a queue-driven onset
  ROUTINE's 4-of-5 is met one report before FALLBACK's 5-of-5, so without
  the wait one failure would be two restarts.

**Hold-downs** (reports since the last transition, by its direction; at
2 s a report):

- FALLBACK: 30 after a down, 60 after an up;
- ROUTINE: 60 after either;
- INCREASE: 60 after a down, 30 after an up, plus the 90 clean reports
  (≥ 93 reports, 186 s).

Hold-downs are checked before the floor, so an early repeat is refused as
`hold_down`.

**The other timers and guards.**

- **Blackout**: 3 reports after any SSRC change. That covers the
  controller's own (re-armed when the actuator returns) and recovery's
  restart or full start. The games plugin wraps both and tells the
  controller. Reports that arrive while the actuator runs are dropped.
- **Guards**, all required:
  - the stream is active;
  - the game is active and not paused;
  - recovery reads PLAYING;
  - the reference profile is in force at 7000;
  - `any_override` is false;
  - the actuator is bound;
  - the client session is ≥ 60 s old.

  A failing guard is one `refused/guard` row that names it.
- **Rate limit**: 4 transitions in any 10 min, then `RATE_LIMITED` and
  the level is held. With the hold-downs, the fastest legal sequence is 4
  transitions in 558 s, so the limit is a backstop.
- **Oscillation** and **ACTUATOR_FAILED**: as the shadow, frozen for the
  session.

**Return to reference.** `session_ended` resets the controller to 7000,
with no history and the disable lifted. It runs on:

- stop;
- `native-stream-stop`;
- recovery's `END_MS` end;
- a fresh (non-recovery) gameplay release.

The stream is the truth: a mismatch is logged `level_sync` and the
stream's `bitrate_kbps` wins. A full start resets to 7000 (C1).

**Actuator and serialization.**

- The controller calls
  `NativeStreamManager.diagnostic_c3_validated_bitrate_transition(target)`,
  the loopback route's method (C3.L3a's ladder path, with the
  reference-7000 guard inside). It runs on one worker thread, never on the
  client-health request thread.
- The worker holds `NativeStreamManager._lock`, re-reads recovery's state
  under it, and restarts only if the state is PLAYING. Otherwise the event
  is `transition_aborted`: not counted, and not a failure.
- Recovery's restart (`recovery_restart_encoder`, C3-F1) and its full
  start take the same lock, **so a transition and a recovery restart
  never overlap**. A recovery that enters during a transition restarts
  ≥ 2 s later, at the new level (level-preserving).

**Kill switches and test hook.**

- **The flag**: unset it and restart the unit.
- **The disable route**, `POST /plugins/games/adaptive-bitrate/disable`,
  gives shadow behaviour for the rest of the session. It is idempotent
  and open to any caller. There is no enable route.
- **The injection hook** (test-only),
  `POST /plugins/games/adaptive-bitrate/inject?class=FALLBACK|ROUTINE`,
  needs `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1`, live mode and a loopback
  caller, else 403. It feeds one synthetic degraded report through every
  gate.

**Log and status.**

- **Log**: `logs/games/adaptive_bitrate_shadow.jsonl`, rows `mode: live`.
  A `transition` row (acted true) carries its inputs, the guards and the
  hold-downs in force. It is followed by `transition_done`,
  `transition_aborted` or `actuator_failed`, with the cycle's timings.
  - Other rows: `refused`, `ssrc_change`, `level_sync`,
    `session_ended_reset`, `disabled` and `inject`.
  - State rows are written only when the state changes (`S1` finding 1).
- **Status**: `native-stream-status.adaptive_bitrate` carries `mode`,
  `configured_mode`, `state` (`ACTUATING` during a restart), `level`,
  `last_action`, `transitions_this_session`, `rate_limited`, and `policy`.

**Where this stands against the constraint's item 6** ("no live run
before a fault-injection night"):

- The task, authorized by the user 2026-09-28, ran live twice on a clean
  link: a silent 30-minute hold, and one session in which the trigger was
  injected.
- **No live run has yet met real loss.** That is the `nft` night, the
  user's, with the hand-step list in the record.

**Results (2026-09-28).**

- **Session A** (30 min, clean link): **SILENT**. There were 0
  transitions over 898 reports, and every close-out row was met.
- **Session B** (injected FALLBACK): **PARTIAL (B6)**.
  - The decrease half behaved as pre-registered: one transition 7000 →
    5000 (actuation 1,225 ms, 152.9 ms RTP silence, a 171 ms output gap),
    the 3-report blackout, and the second injection refused by the
    hold-down.
  - **The increase path never fired** in 15.9 min at 5000.
- **Finding.** The increase rule, 90 *consecutive* clean reports (fps ≥
  59, queue 0, gap ≤ 150), is not reachable in attract mode on the
  adopted build. The controller's clean counter peaked at 21 (A) and 32
  (B), because the client's 2 s fps wanders 57-62.
  - Proxy runs under "no ROUTINE-level sample" reach 110-116.
  - Options (a) to (c) are in the record. The choice is the user's; the
    constant is unchanged.
- **As built, a stepped-down session stays down until the session ends**,
  which resets it to 7000.

## C3.L4 live increase rule — the blend (C3-L4-L2, 2026-09-29; the user's choice)

Decision: `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, appended
2026-09-29. Record: `../evidence/C3_L4_L2_INCREASE_RULE_2026-09-29.md`.
**This supersedes the INCREASE row of "as built" above, for live only.**
The shadow keeps its rule.

**The rule.**

- **clean** = fps ≥ 57, queue ≤ 1 and output gap ≤ 150, on fresh
  telemetry: no ROUTINE-level sample.
- **The window** holds the last 90 evaluated reports since the last SSRC
  change and its 3-report blackout. It starts empty after every change:
  the controller's own, recovery's restart or full start, or a session
  start.
  - Stale and non-distinct reports are skipped.
  - A resync report enters the window as not clean.
- **INCREASE**: one rung, when the window is full and ≥ 85 are clean, and
  the hold-downs, guards, rate limit and oscillation guard allow it.
- **Spacing**: the minimum between increases is 3 + 90 = 93 reports, 186
  s. With a few unclean reports the window keeps rolling until 85 of the
  last 90 are clean.
- **Constants**: `INCREASE_CLEAN_FPS_AT_LEAST 57`,
  `INCREASE_CLEAN_QUEUE_AT_MOST 1`, `INCREASE_CLEAN_GAP_AT_MOST_MS 150`,
  `INCREASE_WINDOW_REPORTS 90`, `INCREASE_CLEAN_NEEDED 85`.
- **Status**: `policy.increase_window`. The transition row carries
  `window_reports` and `clean_reports`.

**Per-report samples.** In live, every client report writes one `sample`
row to the controller's log, about 0.5 kB each (527 B measured) and ~0.95 MB an hour,
rotated at 4 MiB × 3. The row carries:

- fps, queue, gap, fresh;
- clean, and the disposition;
- the window count and its clean count;
- state, reason and level;
- the blackout and the hold-downs.

Any night can be re-scored offline under another rule from these rows.

**Measured (Session B2, attract mode).**

- **Clean share by rung**, the client's own values: 5000 91.2 %, 5500
  94.0 %, 6000 95.6 %, 7000 95.0 %.
- **Unclean**: 44 of the 45 unclean reports were fps < 57, and one was
  queue > 1.
- **The climb**: the steps came 117, 120 and 93 reports after the
  previous change, so ~4 min per rung at 5000 and 5500.
- **The pre-registered risk**: with 91 % clean at 5000, 85 of 90 is met
  but not with much room. A link that is merely noisy (≤ 90 % clean) will
  hold the stream at its rung, which is the safe side.


## C3.L4 live triggers — capacity and the recovery-escalation backstop (C3-L4-N1, 2026-09-29; the user's decision)

Decision: `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, appended
2026-09-29 ("Yes, add both"). Records:
`../evidence/C3_L4_NFT_NIGHT1_2026-09-29.md` (why) and
`../evidence/C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md` (as built).
**Live only; the shadow is byte-identical.** This extends the mapping
table of "as built" above.

**Why.** A capacity shortfall on this client does not queue frames. The
decoder drops them: under night 1's cap, queue was ≥ 1 on 3 of 357
reports, fps 8-40, and ~250 post-FEC lost packets per report. The
shadow's FALLBACK (queue ≥ 2 or gap > 250) met its bar only inside
freezes. Those belong to recovery (`client_output_silence` after
`DESYNC_MS` 1000), and there the recovery guard refuses the controller.

**The live FALLBACK triggers, in order** (all target 5000, one transition,
every existing gate):

| trigger (`trigger` / reason) | evidence, over the last 5 evaluated reports |
| --- | --- |
| `fps_queue_gap` / `decrease_fallback` | fps < 50 on 5/5 and (queue ≥ 2 on ≥ 3/5 or gap > 250 on ≥ 2/5) — the shadow's, unchanged |
| `capacity` / `capacity` | fps < 50 on 5/5 and `lost_packets_delta` ≥ 50 on ≥ 3/5 |
| `recovery_escalation` / `recovery_escalation` | not a window. Two recovery encoder restarts at one level within 180 s → one decision at the first evaluated report with recovery PLAYING (after the blackout) |

ROUTINE (→ 6000) and INCREASE are unchanged.

**The loss counter.** `lost_packets_delta` is
`receiver.lost_packets_delta` in `privyhub_stream_telemetry_v1`. It is
the companion's per-report delta of the client's video `lost_packets`
(`RtpH264Receiver.lostPackets`).

- **What it counts**: RTP sequence gaps in the ordered path *after* FEC
  reconstruction, so it is post-FEC. Since A2.2 it also counts the jump
  of a sequence resync.
- **An SSRC change adds 0**: `beginStreamResync(jumpPackets = 0)` resets
  the sequence state.
- **A sequence resync adds its whole jump to one report**, as B2's
  160-packet resync did.
  - The 3-report blackout covers only the controller's own and
    recovery's SSRC changes. A client-side resync gets no blackout.
  - So one resync can make one report count toward the ≥ 3.
  - It cannot fire the rule alone: fps < 50 must still hold on all 5,
    and two more reports must carry ≥ 50.
  - The blackout covers the loss the old stream carried into the first
    reports after a restart.
  - **The judgement: enough.** Every recorded clean-link series replays
    with zero raw capacity windows.

**Where the backstop reads recovery from, and serialization.**

- The games plugin's `_recovery_restart_encoder` calls
  `LiveController.note_recovery_restart("recovery_restart")` once per
  recovery `encoder_restart`; `_recovery_full_start_encoder` calls it
  with `"recovery_full_start"`. Each call is on recovery's monitor
  thread, after the restart returned and released the stream lock, and
  carries the monotonic clock.
- A desync pause alone never calls it.
- The level is the held level for a restart (C3-F1 is level-preserving)
  and 7000 for a full start (C1).
- The controller reads recovery only: these calls, and
  `current_state()` for the guard.
- Its own restart still re-checks PLAYING under `NativeStreamManager._lock`,
  the lock recovery's restart takes. So the two never overlap, and a
  recovery restart after a controller transition runs at the new level.
- The escalation waits, unspent, while recovery is not PLAYING. It is
  consumed by its one decision, whatever the outcome.

**Expected under a cap** (night 1's samples, open-loop): capacity acts
~14-20 s after the cap. After that recovery has no freeze to own at 5000,
so the backstop stays quiet; it is the net for a shortfall the capacity
bar misses. The blend's climb under a cap between the 5500 and 6000 wire
rates is predicted (not measured):

- 5500 fits;
- 6000 does not, and a capacity FALLBACK comes back to 5000 after the
  120 s reversal hold-down;
- the next increase is the third direction change inside 10 min →
  HOLD (oscillation).

Night 2's pre-registration holds exactly this.

**Status and log.**

- `policy.capacity_trigger` and `policy.recovery_escalation`: the rules,
  the restarts in the window, and the armed escalation.
- `escalation_armed` rows.
- `trigger` on every FALLBACK / ROUTINE decision row.
- `escalation_armed` on every `sample` row.

## C3.L4 live trigger — capacity_mild (C3-L4-N2, 2026-09-29; the user's decision)

Decision: `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, appended
2026-09-29 ("Go"). Records: `../evidence/C3_L4_NFT_NIGHT2_2026-09-29.md`
(why) and `../evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md` (as built).
**Live only; the shadow is byte-identical.**

**Why.** Under night 2's cap, 5000 and 5500 ran clean and 6000 did not
fit. The stream there was degraded but under every existing bar: fps
median 55.8, under 50 on 17 %, ~60 lost per report, queue ≥ 1 on 1 of 115.
It stayed at 6000 until the cap was removed.

**The live decrease triggers, in order** (all over the last 5 evaluated
reports):

| trigger | class → target | bar |
| --- | --- | --- |
| `fps_queue_gap` | FALLBACK → 5000 | the shadow's (fps < 50 on 5/5 and queue ≥ 2 on ≥ 3/5 or gap > 250 on ≥ 2/5) |
| `capacity` | FALLBACK → 5000 | fps < 50 on 5/5 and lost ≥ 50 on ≥ 3/5 |
| **`capacity_mild`** | **ROUTINE → one rung down** | **fps < 57 on ≥ 4/5 and lost ≥ 50 on ≥ 3/5** |
| `fps_queue_gap` | ROUTINE → 6000 | fps < 57 on ≥ 4/5 and queue ≥ 1 on ≥ 3/5 |
| `recovery_escalation` | FALLBACK → 5000 | two recovery restarts at one level within 180 s (not a window) |

**Timing as built.**

- **At a hard cap's onset** the mild bar is met first, at ~10 s. But the
  newest report is under 50 fps, so L1's 4-report ROUTINE deferral waits,
  and the strict FALLBACK acts at 14-20 s. In night 1's K cap the strict
  bar arrived exactly at the 4th deferred report.
- **On a mild shortfall after a climb**, the mild step is a reversal. The
  60-report ROUTINE hold-down after an up applies: the bar is met at
  ~46 s, and the step comes at ~120 s.
- The next increase is then the third direction change. Inside 10 min it
  becomes HOLD `oscillation` at the lower rung.

## C3.L4 — the controller as closed (2026-09-30)

**Default live since 2026-10-01 (`C3-L4-D1`)**, through the unit drop-in
`privyhub-companion.service.d/adaptive.conf`
(`../decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`).

Decision: `../decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, the close
appended 2026-09-30. **Live only**, behind
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default. **No new behaviour
in this section**; it tables the rules the earlier sections built.

| class | trigger (`trigger` / reason) | bar, over the last 5 evaluated reports | target | precedence | hold-downs (reports after a down / an up) |
| --- | --- | --- | --- | --- | --- |
| FALLBACK | `fps_queue_gap` / `decrease_fallback` | fps < 50 on 5/5 and (queue ≥ 2 on ≥ 3/5 or gap > 250 ms on ≥ 2/5) | 5000 | 1 | 30 / 60 |
| FALLBACK | `capacity` / `capacity` | fps < 50 on 5/5 and lost ≥ 50 on ≥ 3/5 | 5000 | 2 | 30 / 60 |
| ROUTINE | `capacity_mild` / `capacity_mild` | fps < 57 on ≥ 4/5 and lost ≥ 50 on ≥ 3/5 | one rung down (at 5000: `at_floor`) | 3 | 60 / 60 |
| ROUTINE | `fps_queue_gap` / `decrease_routine` | fps < 57 on ≥ 4/5 and queue ≥ 1 on ≥ 3/5 | 6000 | 4 | 60 / 60 |
| FALLBACK | `recovery_escalation` / `recovery_escalation` | two recovery encoder restarts at one level within 180 s → one decision once recovery is PLAYING and the blackout has passed | 5000 | its own path (not a window) | 30 / 60 |
| INCREASE | the blend | ≥ 85 of the last 90 evaluated reports since the last SSRC change clean (fps ≥ 57, queue ≤ 1, gap ≤ 150) | one rung up | when no decrease bar holds | 60 / 30 |

**Common to every row:**

- one transition per event;
- a 3-report blackout after any SSRC change;
- L1's ROUTINE deferral: while the newest report is under 50 fps, a
  ROUTINE waits up to 4 reports for FALLBACK;
- the oscillation guard: a third direction change within 10 min → HOLD
  for the session;
- the rate limit: 4 transitions per 10 min;
- the guards: stream active, game active and not paused, recovery
  PLAYING, reference profile, no override, session age ≥ 60 s;
- the disable route (shadow for the session).

**Recovery is unchanged** (`C3-F1`, level-preserving), and the shadow is
byte-identical.

**The three nights.**

- **Night 1** (2026-09-29, the shadow's triggers only): the stream never
  stepped down under a capacity cap. The client drops frames rather than
  queueing them, and recovery restarted at 7000 nine times. Hence
  capacity and the backstop.
- **Night 2**: capacity acted at +14 s, and recovery held 5000 through a
  15 s drop. But 6000 under the cap sat degraded for 4 min below every
  bar. Hence `capacity_mild`.
- **Night 3**: capacity at +15.5 s, the climb to 6000, `capacity_mild`
  back to 5500 at 121 s (the reversal hold-down), then HOLD `oscillation`
  at 5500 for the session. It was **the pre-registered shape**.

## C5-M5 — the 1080p rung, behind its flag (2026-10-02/03; NOT adopted)

Task `../handoffs/C5-M5_1080P_RUNG_TASK.md`; patch
`../patches/C5-M5_1080P_RUNG.md`; record
`../evidence/C5_M5_1080P_RUNG_2026-10-03.md`.

**What it rests on.** A mid-session size change works on the client with no
client change (`R0`, 2026-10-02). On one encoder restart, 7000/1280×720 →
12,600/1920×1080 and back:

- one SSRC change each way;
- the onn's SurfaceView buffers at 1920×1080 within 3 s, and back to
  1280×720 within 5 s;
- no recovery cycle, one decoder report;
- a gap at the switch of 315 / 287 ms.

The Codec2 decoder (`c2.realtek.video.avc.decoder`) takes the new SPS
in-band; its `INFO_OUTPUT_FORMAT_CHANGED` was already ignored, and the
compositor scales the surface.

**The flag.** `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p` (exact). It is read once,
when the companion starts, beside the live mode. Absent, the ladder tops
at 7000 and every decision is byte-identical to the closed controller's.
That is shown by `tools/c5_m5_replay.py`: 0 differences over 377 series.
**Off by default; nothing sets it but a session's own `set-environment`.**

**The ladder, with sizes.**

| level | kbps | size | argv |
| --- | --- | --- | --- |
| 5000 / 5500 / 6000 / 7000 | as before | 1280×720 (the profile's) | unchanged |
| `1080p_12600` (flag only) | 12,600 (`-maxrate`, `-bufsize` 12,600k) | 1920×1080 | C5-M2's c3 arm exactly: cap 90,000 B, GOP 15, bf 0, 8+1 FEC |

The source is already 1920×1080 (`C5-M4A`), so the rung carries real
detail, not an upscale.

**The rows the rung adds** (beside the table in the section above):

| class | trigger / reason | bar | target | hold-downs |
| --- | --- | --- | --- | --- |
| INCREASE | `increase_1080p` / `increase_1080p` | **at 7000 only**: the rung window full and **≥ 415** of the last 450 evaluated reports since the last SSRC change clean (the blend's clean and window rules; 435 as first built, 415 since C5-M5B's selection) | 12600 / 1920×1080 | as INCREASE (30 after an up, 60 after a down), plus **no entry for 10 min after any leave** (`rung_reentry_hold`) |
| (the leave) | the existing triggers (C5-M5B: no loss-based candidate met its pre-registered conditions, so none was added) | as in the table above | the existing mapping from 12600: `capacity_mild` → 7000 / 720p; strict or the queue/gap FALLBACK → 5000; the queue/gap ROUTINE → 6000; the backstop → 5000 | a decrease waits 60 reports after the entry |

**Plus:**

- **Rung oscillation.** A leave, then an entry, then a leave in one
  session. The second leave is carried out, then HOLD
  (`oscillation_rung`) for the session.
  - The general guard (three direction changes within 10 min) cannot see
    this, because of the 10-min re-entry hold-down; hence the rung's own
    count.
- **Guards** as before. `reference_profile` and `no_override` read the
  profile and the env overrides, never the active level, so the rung is
  a ladder level and not a selector: `any_override` stays false.
- **Recovery** at the rung restarts at 12600 / 1920×1080 (C3-F1, sized). A
  full start resets to 7000 / 720p (C1), and the backstop still falls
  back to 5000.
- **Actuator**: `NativeStreamManager.adaptive_level_transition`.
  - Between 720p levels it is the C3.L3a transition, unchanged.
  - To or from the rung it is the same encoder-only restart, with the
    scale/pad rebuilt at the level's size.
  - The loopback c3 route cannot reach the rung.
- **Status**: `native-stream-status` `width` / `height` are the active
  level's. The controller adds `level_size`, `rung_1080p` (window,
  leaves, closed, re-entry hold) and the ladder.
- **Cost of a sized switch** (R0, S1): the gap at the switch is 287-356 ms,
  against 128-225 ms for a bitrate-only restart. A sized restart's
  first RTP came 187-519 ms after the kill (R0 518 up / 187 down; S1 369
  up / 519 down), against ~187 ms for a bitrate-only one.
- **Kill switches**: unset the flag and restart the unit, so the ladder
  tops at 7000; the disable route still puts the session in shadow.

**What the replays say about this link** (`c5_m5_replays.txt`; reported,
no gate):

- The mild bar **does not catch the 1080p's loss** on any C2-telemetry
  series: C5-M4's c_1x … c_8x never meet it. The losses there are short
  bursts, fps < 57 on 7-17 of ~155 reports and lost ≥ 50 on only 2-4, not
  the sustained shortfall the bar was built for.
- Entry needs 15 clean minutes. The C2-telemetry and live-sample 720p
  holds at 7000 (N1, N2, D1, LINK-L2, C5-M4A V5) never reach 435 of 450:
  their best windows were 396-429. The heartbeat-proxy series (S1's
  night, LINK-L1) would have entered on 6 of 10.

**The sessions** (record §4):

- **S1, injection: PASSES.** The entry `increase_1080p` gave 7000 →
  12600, and the injected mild bar gave 12600 → 7000. Gaps 356 / 314 ms.
- **S3, a 2-h night from 01:06: WORKS AS A RUNG.** One entry by its own
  rule at 111.5 min, then 8.5 min at 1080p (loss 2.0/min, fps 60.1), no
  leave, 0 recovery. The switch's gap was 403 ms.
- **S2, a 30-min daytime hold: ENTRY NOT REACHED** (best window 431 of
  450).
- **Not adopted; the flag is off by default.** The user's picture look at
  1080p decides whether the rung is worth adopting.


## C5-M5B — the rung's rules chosen from the recorded data (2026-10-03; NOT adopted)

Task `../handoffs/C5-M5B_RUNG_RULES_AND_LOOK_TASK.md`; patch
`../patches/C5-M5B_RUNG_ENTRY_AND_PS1_LOOK.md`; record
`../evidence/C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md`. The selection
criteria were pre-registered before any replay
(`c5_m5b_preregistration.txt`), and the choice was written before any
code changed (`c5_m5b_selection.txt`).

**The entry, as chosen: ≥ 415 of the last 450 clean** (E415).

- The rule: the strictest of E435 … E405 and E300 (280 of 300) that
  enters within 20 min on ≥ 7 of the 10 real-input 720p holds.
- E415 entered on 8 of 10, at 15.0-16.9 min. Entered on: E435 0, E430 0,
  E425 1, E420 4, E300 5, E410 9, E405 9.
- On those holds' own later 720p reports, 4.3-15.7 % were unclean after
  the replayed entry (a preview).

**The leave, as chosen: unchanged.** The mild bar, strict capacity, the
queue/gap triggers and the backstop.

- None of the four loss-based candidates met the three pre-registered
  conditions:
  - L-A: ≥ 100 lost on 2 of 10;
  - L-B: ≥ 300 lost in 15;
  - L-C: ≥ 50 on 3 of 10;
  - L-D: L-A, or stale ≥ 5.
- The conditions were: leave S1's stretch within 60 s; leave C5-M2 n1r C3
  within 120 s; never fire on S3's stretch.
- **On this link the 1080p loss is rare, large bursts:**
  - S1's "80 lost/min" was one 183-packet resync jump;
  - n1r C3's loss began 587-714 s in;
  - S3's 8.5 min never met any bar.
- The burst rules fire on 2-5 of 13 series (L-B 5, L-D 4, L-A 3, L-C 2;
  the mild bar 1) and never on S3. They are recorded for the user,
  not built.

**The sessions:**

- **S1b, injection: PASSES.** Gaps 348 / 346 ms.
- **S2b, daytime: NOT RUNG SHOWN.**
  - Link-drop recovery paused the game 4.4 min in.
  - The window then reached 415 at 15.1 min, but the guards
    (`game_not_paused`, `recovery_playing`) refused all 448 entry
    decisions.
  - The clean count during a paused, static picture is not a gameplay
    measurement.
- **S3b, the night:** **DOES NOT WORK AS A RUNG by its rows.** One entry by its own rule at 15.1 min (434 of 450, one short of the old 435), then 104.9 min at 1080p with no leave, no oscillation and 0 recovery (fps 60.18, stale 0.70/min, loss 2.82/min). The miss is the session's spikes: 317.9/min against < 200, the 1080p decode's known rate on the onn (C5-M4's 1080p holds 328-607/min). The entry switch's gap was 649 ms.
