---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0
---

# Adaptive Bitrate Architecture

## Status

**C3.1 SOURCE/POLICY AUDIT: COMPLETE**

**Production adaptive bitrate: NOT IMPLEMENTED**

**Next diagnostic:** `C3_ACTUATOR_CONTINUITY_PROBE`

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
