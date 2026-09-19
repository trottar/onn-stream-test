---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: 41bbc6acd3534f79283e328596115a02c3acc296
---

# C3.L2c — MediaCodec low-latency decode is falsified

## Classification

**RUNTIME VALIDATED / CANDIDATE FALSIFIED / ROLLED BACK**

`C3.L2c` removed the capability gate on `MediaFormat.KEY_LOW_LATENCY` in
`AvcLowLatencyDecoder.kt`, so the client requests low-latency decode
unconditionally instead of honoring `c2.realtek.video.avc.decoder`'s own
`FEATURE_LowLatency` self-report, which says unsupported. It was installed
with a real gradle build, run on device, measured, and reverted the same day.
Install record: `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.

This file exists because the install record carried the result and no
evidence record did. Every figure below is re-derived from the raw decoder
session JSON in `logs/games/decoder_sessions/`, not transcribed from the
install record.

## The one session with the flag set

Exactly one decoder session on record reports `low_latency_enabled: true`:
`logs/games/decoder_sessions/native_decoder_20260919_042611_053.json`.
Every other session before and after it, on the same decoder, reports false.
The capability-gate removal worked exactly as designed.

## What it bought, and what it cost

Same day, same device, same decoder, same profile. The low-latency session
against the seven ordinary sessions that bracket it:

| session (UTC) | `low_latency` | dur ms | `max_codec_ms` | **`max_output_gap_ms`** | `spike_20_ms` | `spike_50_ms` | `spike_250_ms` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 03:53:05 | false | 76,691 | 290 | 281 | 3,260 | 314 | 4 |
| 04:06:13 | false | 50,627 | 353 | 345 | 2,088 | 172 | 2 |
| **04:26:11** | **true** | **55,333** | **107** | **385** | **147** | **19** | **0** |
| 04:34:33 | false | 44,872 | 231 | 221 | 1,792 | 214 | 0 |
| 04:41:24 | false | 17,798 | 433 | 424 | 775 | 91 | 2 |
| 04:42:35 | false | 43,797 | 140 | 126 | 1,759 | 183 | 0 |
| 04:43:47 | false | 34,350 | 253 | 244 | 1,422 | 136 | 1 |
| 04:46:41 | false | 43,311 | 346 | 338 | 1,765 | 143 | 4 |

Per-frame decode got dramatically faster and more uniform:

- `max_codec_ms` **107**, against 140-433 ms across the seven ordinary
  sessions — better than every one of them;
- `spike_20_ms` **147**, against 775-3,260 — an order of magnitude fewer;
- `spike_50_ms` **19**, against 91-314;
- `spike_250_ms` **0**, the only session of the eight with none.

The worst perceptible stall did not follow:

- `max_output_gap_ms` **385**, the second worst of the eight, beaten only
  by the 17.8s session at 424 ms;
- in every ordinary session `max_output_gap_ms` tracks `max_codec_ms` to
  within ~10 ms. In the low-latency session it exceeds it by **278 ms**.
  Whatever produced the 385 ms stall, it was not single-frame decode time.

The install record states the comparison it used at the time — 367 -> 107 ms
codec, 359 -> 385 ms gap, against the `C3.L2a` E2 session of 2026-09-18.
The same-day table above is the stronger form of the same result and is what
this record stands on.

## The decision

The user's own gameplay assessment of the low-latency build was "trash", and
it matched the measurement: the metric that tracks a visible stall got
worse, not better. Reverted to the capability-gated behavior.
`AvcLowLatencyDecoder.kt` was restored to its exact predecessor bytes,
SHA-256 `22038e355f85bb8330d900bae64c37db54c902d4affdef12be4810bb03271c07`,
verified byte-exact. The first post-revert session, 04:34:33 above, reports
`low_latency_enabled: false` and a 221 ms gap.

## What this settles, and what it does not

Settled: requesting `KEY_LOW_LATENCY` unconditionally on
`c2.realtek.video.avc.decoder` does not reduce the worst-case decoder output
gap, even though it substantially reduces per-frame decode time and spike
counts. **Do not retry the unconditional request without new evidence.**

Settled, and worth more than the candidate itself: `max_codec_ms` and
`max_output_gap_ms` are **not** the same quantity, even though they move
together in ordinary sessions. Optimizing the first does not imply
improving the second. The `C3.L2a` E2 conclusion that "decoder time is the
largest measured contributor to perceptible interruption" is narrowed by
this: it holds for the correlation, not for the mechanism.

Not settled: what produced the 385 ms gap in a session with no 250 ms codec
spike at all. Candidates not discriminated by this data — output-surface or
compositor-side scheduling, a renderer-side wait, a queueing effect from the
7.2x drop in `spike_20_ms` changing how frames bunch on the way out. One
session, no instrumentation aimed at it. Not pursued; no work item opened.

Not attempted: a mode between the two — requesting low latency only for
part of a session, or pairing it with a different queue policy. The
candidate as registered was the unconditional request, and that is what was
falsified.

## Negative results

- The candidate is dead as specified.
- `max_codec_ms` is falsified as a proxy for `max_output_gap_ms`. Any future
  candidate justified by "it lowers decode time" needs the gap measured
  directly before acceptance.
- The single-session design is a weakness of this result, not a strength.
  It is accepted here because the effect it needed to show — an improvement
  — did not appear at all, and because the subjective report agreed. A
  positive result at n=1 would not have been accepted.

## Privacy

No network addresses appear in this record.
