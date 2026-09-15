---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0
---

# C3 bitrate actuator feasibility

## Status

**CLOSED / RUNTIME VALIDATED / INITIAL ACTUATOR STRATEGY ACCEPTED**

## Question

Can PrivyHub apply a bitrate-level transition without unacceptable disruption to
the validated game stream?

## Source finding

The current FFmpeg process is configured with fixed startup bitrate/maxrate,
uses `-nostdin`, and directly consumes the WGC bridge stdout pipe. PrivyHub has
no live bitrate setter.

The existing full stream stop path also stops audio/controller stream I/O and
FEC, so it must not be reused blindly as the adaptation actuator.

## First probe

Use an unchanged 7000 kbps target and exercise exactly one prospective
video-actuator cycle.

The probe must preserve normal game state and must not change bitrate policy.
Its purpose is interruption/resync measurement only.

If a narrow video-only restart cannot preserve the stable subsystems with an
acceptable short recovery, reject restart-based adaptation and design a true
live-reconfigure encoder actuator.

## Privacy

Do not log or request network addresses.

## Installed diagnostic

Development probe surfaces:
- `companion/diagnostics/c3_actuator_probe.py`;
- `NativeStreamManager.diagnostic_c3_actuator_continuity_cycle()`;
- loopback-only Games POST action `c3-actuator-continuity-cycle`;
- `tools/probe_c3_actuator_continuity.py`.

The cycle keeps bitrate at 7000 kbps and does not modify FEC settings.

Acceptance remains evidence-based. The probe intentionally reports interruption
and recovery measurements without hard-coding an acceptable millisecond
threshold.

## Runtime result and closure

Result: `C3_ACTUATOR_CONTINUITY_EVIDENCE_CAPTURED`, problems none.

Key evidence:
- sequence resyncs: 1;
- SSRC changes: 1;
- packets dropped waiting for IDR: 0;
- resync-to-IDR: 17 ms;
- waiting for IDR at end: false;
- decoder rendered frames: 2,131;
- decoder drops: 0;
- queue-overflow drops: 0;
- max output gap: 791 ms;
- max receive-to-decode: 800 ms;
- audio write errors: 0;
- controller send errors: 0.

Whole-session loss/FEC totals are not attributed entirely to the actuator
cycle.

Focused UX observation: several minutes of play felt normal. Possible slight
stutter was not distinguishable from the existing occasional baseline stutter;
no clear freeze, black frame, audio interruption or controller stall was
observed.

Decision: close actuator-feasibility investigation. Use backend-neutral
`video_only_restart` for initial C3. Linux equivalent requires future runtime
revalidation.
