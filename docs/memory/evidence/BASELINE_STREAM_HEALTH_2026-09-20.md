---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# Baseline stream health — the reference stream is not healthy

## Classification

**RUNTIME EVIDENCE / PHASE C PREMISE FALSIFIED**

Source: every decoder session on disk of 15 s or longer, 47 sessions spanning
2026-09-16 to 2026-09-20, all at the 7000 kbps reference profile. Most have no
actuator activity at all. Derived by parsing
`logs/games/decoder_sessions/*.json` directly.

This record exists because Phase C spent its entire length measuring a bitrate
actuator to four significant figures while the stream it actuates was never
healthy, and nobody had aggregated the sessions to notice.

## The reference stream, aggregated

| | median | min | max |
| --- | ---: | ---: | ---: |
| lost packets / min | 199 | 5 | 2,094 |
| max output gap (ms) | 345 | 126 | 7,341 |
| dropped frames % | 0.6 | 0.2 | 13.5 |
| **decode spikes >20 ms / min** | **2,506** | 159 | 2,723 |
| audio underruns / min | 155 | 13 | 2,555 |
| rendered fps | ~56 | 34 | 59 |

At 60 fps a minute contains 3,600 frames and the per-frame budget is 16.7 ms.
**A median of 2,506 spikes per minute means roughly 70% of every frame misses
budget, in every session, at reference bitrate, with nothing else happening.**
The stream never reaches 60 fps in any session on record.

This is a local wired-class link carrying upscaled PlayStation-era content at
7000 kbps. None of these numbers is a bandwidth symptom.

## Split by client code epoch

Two client changes landed within one hour on 2026-09-19: `ANDROID-FLAT`
(directory flattening, ~01:37 UTC) and `C3.L2b` (receiver/decoder
instrumentation, ~02:38 UTC). The `C3.L2c` low-latency session is excluded
from both groups.

| | A: pre-flatten (n=21) | C: post-`C3.L2b` (n=22) |
| --- | ---: | ---: |
| decode spikes >20 ms / min | 2,552 | 2,495 |
| rendered fps | 55.8 | 55.3 |
| stale output drops / min | 181 | 192 |
| max output gap, median | 231 ms | 392 ms |
| **max output gap, worst** | **338 ms** | **7,341 ms** |
| audio underruns / min | 69 | 139 |

**The decode fault is constant across every epoch.** It predates the
flattening, `C3.L2b`, and all of Phase C.

**The stall tail is not.** Across 21 sessions before the flattening the worst
stall ever recorded was 338 ms. After, the worst is 7,341 ms, with 3,783,
1,997, 1,271 and 1,062 also on the board. The median moved modestly; the tail
rose about twentyfold.

Session length does not explain it. A 16.7-minute session in epoch A maxed at
**331 ms**; a 14.2-minute session in epoch C maxed at **7,341 ms**.

Epoch B — flattened, pre-`C3.L2b` — has only four sessions and two are
sub-30-second fragments. **It is too thin to separate the two changes**, and
this record does not claim to.

## Mechanism for the decode fault

The decoder is buffering for throughput, which is correct for video playback
and wrong for interactive streaming.

| | non-low-latency (64.8 s) | low-latency (55.3 s) | non-low-latency (849 s) |
| --- | ---: | ---: | ---: |
| `max_codec_in_flight` | 13 | 12 | 11 |
| `max_codec_ms` | 315 | **107** | 7,350 |
| `stale_output_drops` | 191 | **16** | 2,461 |
| `latest_feed_delay_ms` | 0 | 0 | 0 |

`latest_feed_delay_ms` is 0 everywhere and `input_waits` stays in the tens:
the client feeds the decoder promptly and is never starved. The decoder holds
**11-13 frames in flight**, which at 60 fps is 180-220 ms of pipeline depth
before any decode work is counted. `stale_output_drops` are frames decoded but
returned too late to display — 2,461 of 50,515 in the long session.

`MediaFormat.KEY_LOW_LATENCY` is the API that tells a decoder to stop doing
this. `c2.realtek.video.avc.decoder` reports `FEATURE_LowLatency` as
**unsupported**, which is why the capability gate blocked it and why removing
that gate in `C3.L2c` changed so much.

## The C3.L2c rollback was decided on the wrong statistic

`C3.L2c` is the single session in this corpus with `low_latency_enabled` true:

| | `C3.L2c` session | all 46 others |
| --- | ---: | --- |
| decode spikes >20 ms / min | **159** | 1,828 - 2,723 |
| `max_codec_ms` | **107** | 140 - 7,350 |
| `stale_output_drops` | **16** | 16 - 2,461 |
| rendered fps | **59.0** | 34 - 57.2 |
| dropped frames % | **0.15** | 0.2 - 13.5 |

It is the best session on record on every distributional metric, by a wide
margin, in a column (`spike_20_ms/min`) that is otherwise remarkably tight
across 46 sessions.

It was rolled back because `max_output_gap_ms` moved 359 -> 385 — **one
worst-case sample per session** — and on a subjective report taken in the same
session. `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`
correctly recorded that `max_codec_ms` is not a proxy for
`max_output_gap_ms`. The error was the unstated converse: **`max_output_gap_ms`
is not a proxy for how the stream plays either.** One sample was allowed to
overrule thousands.

That record's own reopening condition is "without new evidence". This is new
evidence. `C3.L2c` is reopened.

## Three faults, ranked by measured impact

1. **Decoder path.** ~70% of frames over budget, every epoch, since at least
   2026-09-16. Mechanism identified above. A demonstrated candidate fix exists
   and was rejected on the wrong statistic. Never held a work item.
2. **Stall-tail regression**, somewhere in 2026-09-19 01:37-02:38 UTC. Worst
   stall 338 ms before, 7,341 ms after. Two candidate causes, not separated.
   `C3.L2b` is the stronger suspect on mechanism — it added per-frame and
   per-packet bookkeeping to `AvcLowLatencyDecoder` and `RtpH264Receiver`,
   i.e. to the hot path — while `ANDROID-FLAT` changed only directory layout,
   leaving Kotlin package declarations and therefore bytecode semantics
   unchanged. The flattening did force a full rebuild and reinstall, so it is
   not excluded.
3. **Audio underruns.** 69/min before the boundary, 139/min after, spiking to
   2,555/min. A separate subsystem, never investigated.

## What this falsifies

**The premise of Phase C.** C3 exists to build adaptive bitrate control. None
of the three faults is a bandwidth fault. Lowering the bitrate cannot make a
decoder drain faster, cannot remove hot-path instrumentation overhead, and
cannot stop audio underruns. `C3.L4` would adjust the one variable that is not
the problem.

The Phase C work itself is not wrong and is not discarded: the Linux actuator
is real, measured and correct, and `C3.L3a` Part 1 showed chained transitions
are clean. It is **sequenced wrongly**. It is a mechanism awaiting a reason.

## What this does not establish

- Which of the two 2026-09-19 changes caused the tail regression. Epoch B is
  too thin. A one-variable revert test settles it.
- Whether the onn client can reach the target after the decode path is fixed.
  Even the low-latency session held 12 frames in flight and had a 107 ms worst
  frame. The client may be a ceiling; nothing here proves it either way.
- The physical link type between host and client. The loss column (5 to 2,094
  packets/min) is consistent with a wireless link, but nothing on record states
  which it is. This must be recorded before the transport fault is worked.
- Any cause for the audio underruns.
- Anything perceptual. Every figure here is instrumentation.

## Privacy

No network addresses appear in this record, and none were collected to produce
it. "Link type" above means wired versus wireless, not an address.
