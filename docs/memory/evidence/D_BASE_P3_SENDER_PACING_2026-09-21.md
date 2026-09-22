---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P3 — pace the sender and see whether the loss is a burst overflow

## Classification

**INDETERMINATE, and pacing is not adopted.** Fifteen 120 s attract-mode
sessions on the production path, strictly alternating, none rejected. On the
pre-registered reading pacing is **not implicated**: loss per minute fell in
only **3 of 5 pairs** (the bar was 4), the medians fell **1.72x** (loss) and
**1.70x** (packets per gap) against a bar of 2x, and **the spike rate rose in
5 of 5 pairs**, which the criterion forbids outright. It is **not ruled out**
either — packets per gap fell in **4 of 5** pairs and the median maximum
forward gap **halved**, 16 → 8 packets. So: **mixed, and reported as mixed.**

**The one reproducible result of this run is a cost, not a gain.**
`spike_20_ms` per minute rose in **every one of the seven paced sessions**,
median **42.7 → 60.1 (+41 %)** at 150 µs and 63.6 at 400 µs. Worst-case
latency did *not* rise — `max_rx_to_decode_ms` median **137 → 112** — so what
moved is the body of the distribution, exactly where spreading a frame's
packets over ~2 ms would move it.

**The effect does not scale.** At `PACING_US` = 400 the achieved median
spacing is only **187.5 µs**, not 400, because the 8 ms frame budget clamps
**29.7 %** of frames; loss per minute fell in **0 of 2** pairs.

## The knob

`companion/native_fec_relay.py`, diagnostic, **default off**. Configured by
the **environment variable `PRIVYHUB_FEC_PACING_US`** — not a companion config
key — read in `NativeVideoFecRelay.start()`, so the arm is whatever the
companion process was started with and changing arms means restarting the
companion (D-068). `0`, unset, non-numeric or negative all mean off.

With it off the relay is **byte-for-byte what it was**: `_handle_rtp` forwards
on arrival and `_emit_group_locked` sends parity immediately. With it on,
nothing goes out on arrival: a frame's packets accumulate in arrival order
keyed by RTP timestamp, parity is inserted directly after the group it
protects, and the whole frame is handed to a dedicated sender thread when its
marker lands. **The wire format, group size, parity and packet order are
untouched** — only the spacing differs. An offline check
(`p3_pacer_offline_check.txt`, `test_pacer.py`) drives the same synthetic
frames through both paths and asserts the emitted byte strings and their order
are **identical**, with `rtp_packets`, `parity_packets`, `groups`,
`skipped_packets`, `send_calls`, `send_errors` and `sent_bytes` all equal.

**The hard cap.** Spacing is clamped to `8000 µs / packets-in-frame`, so a
frame's packets are all out within 8 ms of its **first packet arriving** — the
wait for the marker and the sender-thread wake are inside that budget, so 8 ms
is the whole added latency, under half a 16.7 ms frame.

**Sleep resolution, measured on this host before choosing.** `time.sleep`
carries a ~55 µs floor of overshoot: `sleep(50 µs)` returns after a median
**105.5 µs**, `sleep(150 µs)` after **205.5 µs**, `sleep(400 µs)` after
**455.8 µs**. It cannot place a 150 µs gap. A busy-wait on `perf_counter_ns`
lands at **150.1 µs p50, 150.3 µs max**. So `_wait_until` sleeps only when more
than 300 µs remains, and always busy-waits the last ~200 µs.

**One implementation correction, caught by the offline check.** The first
version anchored the send schedule on the first packet's *arrival*. Because a
frame is only queued once its marker lands and waking the sender costs more
again, the early packets were already due and went out back to back: achieved
p50 came out **7.5 µs instead of 150**. The schedule is now anchored on the
moment the sender thread actually starts the frame, while the **budget stays
measured from arrival**, so the latency bound is unchanged. Measured
`max_start_delay_us` is 14.5-17.6 ms in ordinary sessions — see the caveat
below.

Reported in `relay.status()["pacing"]` and, per session, in the decoder
session log's `host.fec_pacing` block: `enabled`, `configured_us`, `source`,
`frame_budget_us`, `paced_frames`, `paced_packets`, `clamped_frames`,
`late_frames`, `last_spacing_us`, `achieved_spacing_p50_us`,
`achieved_spacing_p99_us`, `max_start_delay_us`, `queue_depth`,
`max_queue_depth`. Achieved spacing is a bounded 5 µs-bucket histogram, not a
sample list, so a long session cannot grow it.

## The onn's receive buffer, recorded once

`RtpH264Receiver.kt:573` asks for **2 MiB** (`localSocket.receiveBufferSize =
2 * 1024 * 1024`). **The granted value is not exposed** — nothing reads
`receiveBufferSize` back, and it appears in no heartbeat and no report. The
client was not changed in this task, so that stays unknown from the client
side. What *can* be said without touching it: the onn's
`/proc/sys/net/core/rmem_max` is **8,388,608** and `rmem_default` is
**229,376**, so a 2 MiB request is **inside the kernel cap and is not clamped**
there. The socket buffer is therefore not obviously the limiting queue; a
driver or wireless queue below it is not measured by this.

## Method

Fifteen attract-mode sessions of the PS1 reference title, **120 s each, zero
input**, opened through the launcher's RESUME PLAYING preview per `TOOLS.md`,
ended with BACK, the game stopped and `active: false` confirmed between every
one. **The companion was restarted for every session**, the port confirmed
free first and the serving pid confirmed to be the one just launched, and the
relay's reported `configured_us` confirmed to equal the requested arm before
the stream was opened — so no session can have run on a stale process.

- **Block A**, ten sessions, **strictly alternating off / 150 µs, starting
  off**: `P1off P1on P2off P2on P3off P3on P4off P4on P5off P5on`.
- **Block B**, five sessions, the scaling probe, alternating off / 400 µs and
  **ending off** as required: `S1off S1on400 S2off S2on400 S3off`.

**Rejected sessions: 0 of 15.** No session carried a discontinuity in its
first 30 s — in fact **no session carried a discontinuity at all** — so
nothing was re-run.

**The last session in run order is `S3off`**, and its report records
`fec_pacing.enabled: false`, `configured_us: 0`. The knob ends the run at 0.

Harness `p3_run.sh`, analysis `p3_analyze.py`, raw output `p3_analysis.txt`,
offline equivalence check `test_pacer.py` / `p3_pacer_offline_check.txt`,
per-session relay captures `relay_<label>.json`, SHA-256 of every file in
`p3_sha256.txt` — all under `d_base_p3_2026-09-21/`.

## Per session, in run order

| run | cfg µs | loss/min | fwd gaps | pkt/gap | max gap pk | disc | max out ms | spk20/min | max rx→dec | fps | space p50 | space p99 | send max µs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1off | 0 | 22.2 | 6 | 7.83 | 16 | 0 | 136 | 46.8 | 137 | 59.67 | — | — | 929.6 |
| P1on | 150 | 3.8 | 5 | 1.60 | 2 | 0 | 137 | 67.6 | 101 | 59.71 | 147.5 | 202.5 | 1,206.8 |
| P2off | 0 | 35.2 | 11 | 6.82 | 22 | 0 | 255 | 42.7 | 106 | 59.63 | — | — | 990.1 |
| P2on | 150 | 9.0 | 6 | 3.17 | 8 | 0 | 156 | 60.1 | 109 | 59.65 | 147.5 | 172.5 | 1,627.7 |
| P3off | 0 | 4.7 | 2 | 5.00 | 5 | 0 | 98 | 42.1 | 170 | 59.69 | — | — | 714.5 |
| P3on | 150 | 13.0 | 9 | 3.11 | 8 | 0 | 152 | 57.2 | 112 | 59.68 | 147.5 | 217.5 | 2,601.4 |
| P4off | 0 | 20.3 | 8 | 5.38 | 22 | 0 | 128 | 35.5 | 123 | 59.66 | — | — | **67,989.4** |
| P4on | 150 | 11.8 | 7 | 3.57 | 12 | 0 | 109 | 52.9 | 136 | 59.67 | 147.5 | 252.5 | 1,257.7 |
| P5off | 0 | 1.8 | 1 | 4.00 | 4 | 0 | 97 | 43.8 | 188 | 59.72 | — | — | 1,015.3 |
| P5on | 150 | 22.7 | 6 | 8.00 | 31 | 0 | 120 | 61.0 | 143 | 59.67 | 147.5 | 182.5 | **60,096.1** |
| S1off | 0 | 3.8 | 3 | 2.67 | 4 | 0 | 101 | 41.2 | 95 | 59.75 | — | — | 1,014.2 |
| S1on400 | 400 | 6.6 | 6 | 2.33 | 4 | 0 | 123 | 59.6 | 93 | 59.70 | 187.5 | 417.5 | 1,033.2 |
| S2off | 0 | 6.1 | 4 | 3.25 | 5 | 0 | 136 | 39.7 | 103 | 59.68 | — | — | 1,012.2 |
| S2on400 | 400 | 27.9 | 14 | 4.21 | 19 | 0 | 161 | 67.6 | 128 | 59.64 | 187.5 | 457.5 | 1,277.3 |
| S3off | 0 | 5.2 | 4 | 2.75 | 4 | 0 | 109 | 46.3 | 122 | 59.71 | — | — | 1,431.2 |

Loss is read by the `D-BASE-R1` rule; every session reports
`lost_packets_in_resyncs` 0 and zero discontinuities, so the two readings
coincide. The two bold `send_call_max_us` figures are single `sendto` calls
that blocked ~60-68 ms; **one fell in each arm**, so they are host stalls, not
a property of pacing.

## Block A — `PACING_US` = 150, five pairs

| pair | loss/min off | on | fall | pkt/gap off | on | fall | spk20 off | on | rx→dec off | on |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 22.2 | 3.8 | 5.87x | 7.83 | 1.60 | 4.90x | 46.8 | 67.6 | 137 | 101 |
| P2 | 35.2 | 9.0 | 3.91x | 6.82 | 3.17 | 2.15x | 42.7 | 60.1 | 106 | 109 |
| P3 | 4.7 | 13.0 | 0.36x | 5.00 | 3.11 | 1.61x | 42.1 | 57.2 | 170 | 112 |
| P4 | 20.3 | 11.8 | 1.72x | 5.38 | 3.57 | 1.50x | 35.5 | 52.9 | 123 | 136 |
| P5 | 1.8 | 22.7 | 0.08x | 4.00 | 8.00 | 0.50x | 43.8 | 61.0 | 188 | 143 |

- loss per minute fell in **3 of 5** pairs;
- packets per gap fell in **4 of 5**;
- **spikes ≥ 20 ms / min rose in 5 of 5**;
- `max_rx_to_decode_ms` rose in 2 of 5.

Medians: loss/min **20.3 → 11.8** (1.72x), packets per gap **5.38 → 3.17**
(1.70x), max forward gap **16 → 8** (2.00x), `max_output_gap_ms` 128 → 137,
spikes **42.7 → 60.1**, `max_rx_to_decode_ms` **137 → 112**, fps 59.67 → 59.67.

Full per-session lists, because the spread is larger than the effect:

- **loss/min** — off: 1.8, 4.7, 20.3, 22.2, 35.2 · on: 3.8, 9.0, 11.8, 13.0, 22.7
- **packets per gap** — off: 4.00, 5.00, 5.38, 6.82, 7.83 · on: 1.60, 3.11, 3.17, 3.57, 8.00
- **spikes ≥ 20 ms/min** — off: 35.5, 42.1, 42.7, 43.8, 46.8 · on: 52.9, 57.2, 60.1, 61.0, 67.6
- **max_rx_to_decode_ms** — off: 106, 123, 137, 170, 188 · on: 101, 109, 112, 136, 143

**The two loss distributions overlap almost completely**, and the pairs
disagree in direction: P1 and P2 show a 4-6x improvement, P3 and P5 show the
reverse. The off arm alone spans 1.8 to 35.2 loss/min — a 20x range inside one
hour, on one link, with nothing changed. Interleaving removed the time-of-day
confound `B2` had, and a minute-scale one took its place.

## Block B — `PACING_US` = 400, the scaling probe

| pair | loss/min off | on | fall | pkt/gap off | on | fall | spk20 off | on |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| S1 | 3.8 | 6.6 | 0.57x | 2.67 | 2.33 | 1.14x | 41.2 | 59.6 |
| S2 | 6.1 | 27.9 | 0.22x | 3.25 | 4.21 | 0.77x | 39.7 | 67.6 |

loss per minute fell in **0 of 2** pairs, packets per gap in 1 of 2, spikes
rose in 2 of 2. **Asking for more spacing did not deliver more spacing:**

| arm | n | achieved p50 | achieved p99 | clamped / frames | late frames | loss/min med | pkt/gap med | spk20 med |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| off | 8 | — | — | — | 0 | 5.7 | 4.50 | 42.4 |
| 150 µs | 5 | **147.5** | 202.5 | 833 / 7,629 (11 %) | 46 | 11.8 | 3.17 | 60.1 |
| 400 µs | 2 | **187.5** | 437.5 | 2,253 / 7,630 (30 %) | 99 | 17.3 | 3.27 | 63.6 |

## What bounds this null — read before reusing it

1. **The budget clamps exactly the frames the hypothesis implicates.** Spacing
   is capped at `8000 / packets-in-frame`, so a frame is clamped above **53
   packets** at 150 µs and above **20** at 400 µs. Mean frame size here is
   **15.85 packets** including parity, and **11 %** of frames exceed 53. Those
   large frames — the IDRs and big P-frames that a queue-overflow account
   blames — are precisely the ones the 8 ms budget refuses to spread at the
   requested rate. Pacing was therefore tested hardest where it applies least.
   **A stronger test needs a larger budget, which costs latency.**
2. **The noise beat the effect.** The off arm swings 20x within the hour. Five
   pairs can resolve a 4x effect; they cannot resolve the 1.7x that was seen.
3. **`late_frames` is not zero**: 39-55 frames per session at 150 µs and 88-110
   at 400 µs exceeded the 8 ms budget, out of ~7,600. `max_start_delay_us` ran
   14.5-17.6 ms, above the budget itself, meaning the accumulate-plus-wake cost
   sometimes consumed the whole allowance before the first packet moved and the
   clamp drove spacing to ~0 for that frame. The pacer is not tight.
4. **`max_queue_depth` reached 4-7 frames**, so the sender thread does fall
   behind the encoder in bursts.
5. Nothing here measures the air. Retries, interference and the Opal's own
   queues were not instrumented; a null on pacing is not evidence for them.

## Latency cost, measured rather than assumed

The design bound is **8 ms** worst case per frame, under half a frame at
60 fps. What the client actually saw at 150 µs: **`spike_20_ms`/min
42.7 → 60.1**, a **+41 %** rise in frames whose receive-to-output latency
crosses 20 ms, reproduced in 5 of 5 pairs and again in both 400 µs pairs.
Against that, `max_rx_to_decode_ms` **fell** (137 → 112) and rendered fps was
unchanged at **59.67**, and `max_output_gap_ms` moved 128 → 137, inside its
own noise. So the cost is a shifted middle of the latency distribution, not a
worse tail and not dropped frames.

**Adopting pacing is a product decision for the user, not a measurement
outcome.** This run measured the cost (+41 % spike rate at 150 µs) and failed
to establish the benefit. Nothing has been turned on.

## Ends at zero

The knob's default is 0 and the environment variable is not set anywhere in
the repository, in any service unit, or in any harness that outlives this run.
`S3off`, the last session, reports `fec_pacing.enabled: false`. The companion
was stopped last, per `TOOLS.md`.
