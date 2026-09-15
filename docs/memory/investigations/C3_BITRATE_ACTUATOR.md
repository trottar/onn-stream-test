---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: da03bb59cee9f7e9cf8bdfcc91dc1f52454beff0
---

# C3 bitrate actuator feasibility

## Status

**ACTIVE / DIAGNOSTIC REQUIRED**

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
