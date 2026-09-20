---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: e2fd7b566534f4bbd9a74d6456916bace7abfc29
---

# D-BASE — baseline health before adaptation

**Status:** Accepted decision (2026-09-20)

Roadmap and sequencing decision. No source is changed by it. It is made from
`evidence/BASELINE_STREAM_HEALTH_2026-09-20.md`, which aggregates 47 decoder
sessions already on disk.

## Decision

**Phase C adaptive-bitrate work is SUSPENDED.** `C3.L4` and `C3.L3a` Part 2
are suspended, not cancelled and not failed.

**Baseline stream health becomes the active line of work**, tracked in
`investigations/BASELINE_STREAM_HEALTH.md`, and Phase C does not resume until
the baseline target below is met or the attempt is formally abandoned.

## Why

The reference stream is not healthy and never has been. At 7000 kbps, on a
local link, carrying upscaled PlayStation-era content, roughly **70% of every
frame misses the 16.7 ms budget**, in every session on record, going back to
the earliest data. The stream never reaches 60 fps. Stalls reach 7.3 seconds.
Audio underruns run at ~2.5 per second.

**None of the three identified faults is a bandwidth fault.** Adaptive bitrate
control is a remedy for bandwidth scarcity. Building `C3.L4` now would ship a
controller that adjusts the one variable that is not the problem, on top of a
stream that fails its own baseline.

The user's framing, recorded because it is the actual requirement: the target
is seamless, lag-free local play, and **remote play is unreachable without
it** — a link that stalls 7.3 seconds locally has no headroom to spend on WAN
latency, jitter and real loss.

## The target, stated numerically

"Seamless" is defined as measurable acceptance criteria, all distributional,
none requiring a subjective judgement:

| metric | target | current median |
| --- | --- | ---: |
| decode spikes >20 ms / min | **< 200** | 2,506 |
| rendered fps | **>= 59.5** | ~56 |
| max output gap, per session | **<= 100 ms** | 345 |
| stale output drops / min | **< 20** | 181 |
| lost packets / min | **< 10** | 199 |
| audio underruns / min | **< 5** | 155 |

These are entry criteria for resuming Phase C, not a product SLA. They are
derived from what the hardware and content should permit, not from what the
system currently does.

## Order of work, by measured impact

1. **Remove the stall-tail regression.** Revert only the `C3.L2b` hot-path
   instrumentation, keep the flat layout, take five sessions of >= 2 minutes,
   compare the tail. One variable, existing metric, no new tooling.
   - tail returns to <= ~340 ms -> `C3.L2b` is the cause; re-add the
     instrumentation off the hot path;
   - tail stays high -> the cause is the rebuild or the flattening, and the
     layout change needs a real look.
2. **Fix the decoder path.** Reopen `C3.L2c`, judged on
   `spike_20_ms/min`, `stale_output_drops` and fps rather than a single
   `max_output_gap_ms` sample. Investigate the 11-13 frame in-flight depth
   directly: low-latency request, feed pacing, and whether a tunneled or
   explicitly-timed output path is available.
3. **Establish and fix transport.** Record the physical link type first —
   wired or wireless — because the loss column is consistent with a wireless
   link and that single fact may explain it entirely. The deferred UDP
   burst/gap pathology belongs here.
4. **Fix audio underruns.** Separate subsystem, no investigation on record.
5. **Client viability decision.** See below.

## The client decision, pre-registered

The onn device may be a ceiling. Even the low-latency session held **12 frames
in flight** and had a 107 ms worst frame.

**Pre-registered:** if, after steps 1-3, a client with a healthy decode path
and a wired link cannot reach `spike_20_ms/min < 200` and fps `>= 59.5`, the
onn is the ceiling and the client changes. That is a hardware conclusion, not
a failure of the software, and it is named now so it is not discovered by
attrition three weeks from now.

The project description already calls the onn "the first client", so a second
client is consistent with the architecture, not a retreat from it.

## What this decision does not say

- It does not discard Phase C. The Linux actuator is real, measured and
  correct; `C3.L3a` Part 1 showed chained transitions are clean on both host
  and client. Phase C is a mechanism awaiting a reason, and it resumes when
  the baseline justifies adaptation.
- It does not blame the flattening. Epoch B is too thin to separate the two
  2026-09-19 changes; step 1 settles it with one variable.
- It does not claim the onn is inadequate. That is step 5, and it has a
  pre-registered criterion rather than an opinion.
- It does not authorize any perceptual gate. Every acceptance metric above is
  instrumentation, by the user's explicit instruction that this be data-driven
  and not a judgement of their own opinion.

## Negative results this decision records

- **Phase C was sequenced on an unexamined premise.** The baseline was never
  aggregated across sessions until 2026-09-20, so nothing contradicted the
  assumption that the stream was healthy enough to optimize adaptation on.
  Every individual session report was available the whole time.
- **A single worst-case statistic overruled a distribution.** `C3.L2c` was
  rolled back on `max_output_gap_ms` while `spike_20_ms/min` showed a 15x
  improvement in the same data.
- **Instrumentation is a suspect in the fault it was built to measure.**
  `C3.L2b` added per-frame work to the hot path and is the stronger candidate
  for the stall-tail regression.

## Privacy

No network addresses appear in this record. "Link type" means wired versus
wireless.
