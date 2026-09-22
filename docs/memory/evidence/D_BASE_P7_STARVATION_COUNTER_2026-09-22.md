---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-P7 — what `prolonged_starvation_events` counts

## Classification

**CHARACTERIZED. The counter is arrival-gap driven**, the pre-registered
second reading. It counts **episodes, not polls**, and it fires on **audio
jitter, not audio loss**.

> **One increment per hole in the audio arrival stream longer than about
> 15 ms.** The host sends at a near-perfect 5 ms cadence; the client sees a
> **55-60 ms hole roughly once every two seconds**, and each hole costs one
> event.

Spearman against the per-tick maximum audio inter-arrival gap: **+0.684**
over 596 ticks. Against audio loss: **+0.020**. Against the packet
deficit: **+0.036**.

## 1. Step 1 — what the code says, written before the session

`NativeAudioReceiver.playbackLoop` polls the audio queue with
`queue.poll(STARVATION_POLL_MS, MILLISECONDS)` where
`STARVATION_POLL_MS = PACKET_MS = 5`. On each empty poll it increments
`concealedUnderruns` and `starvationPackets`. Then:

```kotlin
if (starvationPackets > FADE_CONCEAL_PACKETS && !starvationEpisodeCounted) {
    prolongedStarvationEvents.incrementAndGet()
    starvationEpisodeCounted = true
}
```

with `FADE_CONCEAL_PACKETS = 2`, and **both** `starvationPackets` and
`starvationEpisodeCounted` reset the moment any packet arrives.

**So the counter is latched.** It increments **exactly once per contiguous
run of three or more empty 5 ms polls** — that is, once per hole in the
arrival stream longer than **~15 ms** — and it cannot fire twice for the
same hole however long the hole lasts.

**This excludes the task's "definitional / duty cycle" reading before any
data was taken.** A poll-quantized counter would increment on every poll
while the condition held; the latch is precisely what stops that. "Events
per minute" is a real event rate, not a duty cycle.

The thread that evaluates it is the **playback** thread. The queue it
drains is the same `ArrayBlockingQueue` whose depth the report publishes as
`audio.queue_depth`, so the depth figure and the counter are about the same
queue. `audio.lost_packets` is counted on the **receive** thread from RTP
sequence gaps, `concealed_loss_packets` counts packets concealed because
they were lost, and `concealed_underruns` counts **every** empty poll — so
`concealed_underruns` and this counter are mechanically linked and their
correlation is close to tautological. `avg_queue_residence_ms` measures how
long a packet sat in the queue, which is a latency, not an arrival figure.

**Predicted before the session:** if the host's cadence is 5 ms and the
queue target is 3 packets (15 ms of cushion), then any arrival hole beyond
about 15-20 ms produces exactly one event, and the rate is the rate of such
holes. The session was run to confirm or refute that.

## 2. The instrument added

One diagnostic client build, **heartbeat payload only**. Ten audio fields
ride the existing 2 s heartbeat, read from the **same
`audioReceiver.snapshot()` the end-of-session report reads**, plus one new
measurement: the **maximum audio inter-arrival gap**, taken as a single
`max()` on the receive thread between consecutive valid datagrams. No new
thread, no new sampling, and the counter's semantics are untouched.

The session max (`audio_session_max_arrival_gap_ms`) and the per-heartbeat
window max (`audio_max_arrival_gap_ms`) are **separate atomics**: the
window one resets on read, and if the heartbeat had reset the session one
the end-of-session report — which calls the same `snapshot()` — would have
been corrupted.

Schema bumped to **`privyhub_native_stream_heartbeat_v3`**.

**One mistake worth recording.** The first build produced heartbeats with
**no audio fields at all** even though the client was sending them: the
companion's `native-stream-heartbeat` handler carries an **explicit
whitelist** of query keys, and keys not on it are dropped silently. Adding
the fields to `native_stream_heartbeat.py` was not enough — the whitelist
in `plugins/games.py` is the gate. Caught on the first heartbeat of the
first session, the session was abandoned and re-run after the fix.

## 3. The session

One 20-minute attract-mode session, zero input, on the adopted profile
(`any_override: false`, argv carrying `-max_frame_size 90000`,
`env | grep PRIVYHUB_ENC` empty). **597 heartbeats, 596 usable tick
intervals.**

| | |
| --- | ---: |
| audio packets / loss | 240,630 / 327 (0.1359 %) |
| `prolonged_starvation_events` | **654** (32.5/min) |
| audio underruns (session) | 4 |
| concealed underruns / concealed loss | 4,117 / 319 |
| queue target / capacity | **3 packets (15 ms) / 8 (40 ms)** |
| queue depth at end / max | 5 / 8 |
| avg / max queue residence | 31.21 ms / 159 ms |
| video loss | 88 (4.4/min) |
| fps / spike_20_ms per min | 59.94 / 25.6 |

## 4. It counts episodes, and the episodes are not quantized

Starvation delta per 2 s tick:

| delta | 0 | 1 | 2 | 3 | 4 | 5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ticks | **205** | 201 | 137 | 40 | 11 | 2 |

Mean **1.09**, sd **1.03**, and **34 % of ticks record none at all**. A
duty-cycle counter cannot produce a third of its samples at zero with a
spread this wide. The code said episodes; the data agrees.

## 5. What it tracks

**Per 2 s tick, n = 596:**

| reading | rho vs starvation | spread |
| --- | ---: | --- |
| **max audio arrival gap (ms)** | **+0.684** | 11 – 131 |
| concealed underruns | +0.747 | 0 – 40 |
| video loss | +0.162 | 0 – 9 |
| audio packet deficit | +0.036 | −11.4 – +14.6 |
| **audio loss** | **+0.020** | 0 – 7 |
| queue ms | +0.010 | 4 – 20 |
| queue depth | −0.011 | 0 – 8 |
| audio rx packets | −0.040 | 388 – 414 |

Per minute (n = 20) the gap gives **+0.473**, concealed underruns +0.652,
audio loss +0.187, queue depth −0.508.

**The concealed-underrun correlation is not independent evidence** and is
reported only for completeness: that counter increments on *every* empty
poll and an episode *is* a run of empty polls, so the two are linked by
construction.

**Audio loss and the packet deficit are flat.** Across 596 ticks the
deficit against the expected 400 packets per 2 s averages **+0.54 packets
with sd 2.86** — that is **±0.7 %**, i.e. **no packets are missing, they
are late**. This is jitter, and the counter is not a second name for loss.

## 6. The arrival gap, and where it is not coming from

The distribution of the per-tick maximum gap is **sharply periodic, not
noisy**:

| gap bin (ms) | 10-19 | 20-29 | 30-39 | 40-49 | **50-59** | **60-69** | 70+ |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ticks | 8 | 7 | 14 | 11 | **433** | **120** | 3 |

**93 % of ticks have their largest hole between 50 and 69 ms**, median
**55**, p90 **60**, max **131**. **Only 6 of 596 ticks stay under the
15 ms episode threshold.** So an arrival hole of ~55-60 ms happens about
once every two seconds, reliably, and that is the whole of the counter's
behaviour.

**It is not the sender.** The host's audio pacing was measured directly at
baseline (`linux_baseline_2026-09-15`, probe 34, the hybrid pacer): **send
interval average 5.0 ms, p95 5.04 ms, maximum 5.08 ms**, with 0 intervals
at or above 8 ms across 999 samples. The sender emits one packet every
5 ms to within 80 microseconds. **The 55 ms hole appears between the host's
socket and the onn's**, not before it.

**Nor is it the queue's depth being wrong on average.** Ticks that starve
and ticks that do not have the *same* mean `queue_ms` (17.2 either way);
what differs is the gap — **49.1 ms mean on quiet ticks against 57.7 ms on
starving ones**. Grouping by (gap − cushion) gives a monotonic rise in mean
starvation — 0.70, 1.71, 1.95 across 0-40, 40-45 and 45-50 ms — but it
correlates *worse* than the gap alone (+0.621 vs +0.684), because
`queue_ms` is a spot reading at heartbeat time and not the depth at the
moment of the hole. **The gap alone is the predictor this instrument
supports.**

## 7. The PC-versus-Opal halving, which the reading has to explain

| path | capped? | starvation |
| --- | --- | ---: |
| PC path (`S2`, 3 h) | no | **75.9/min** |
| Opal path (`O1`, 20 min) | no | 35.8-40.7/min |
| Opal path (`S3`, 3 h) | yes | **32.0/min** |
| Opal path (`P7`, this run) | yes | **32.5/min** |

**The reading explains it.** If the counter measured the client's own
scheduling, or the sender's cadence, the rate would not change when only
the network path changed — the client build and the host sender were the
same across `S2` and `O1`. It halves because **the path's jitter differs**,
which is exactly what an arrival-gap counter should do.

**The frame cap barely moved it** (35.8-40.7 → 32.0-32.5), and that is also
consistent: audio is a low-rate, evenly paced, small-packet stream. It was
never the bursty stream the cap exists to tame — `P5` measured audio losing
3-7x *less* than video for the same reason.

**What this run does not determine is what causes the 55 ms hole.** The
instrument records one maximum per 2 s tick, so it cannot locate the hole
inside the tick or align it with anything. Candidates it cannot separate:
queueing behind the video burst on the wireless hop, the AP's per-station
scheduling, or a client-side scheduling stall. The PC-vs-Opal difference
argues against a purely client-side cause, and no more than that.

## 8. Levers, and their costs — the user's decision

**Nothing is implemented. The counter's semantics were not touched.**

- **A deeper audio cushion.** The queue target is **3 packets = 15 ms**
  against holes with a p90 of **60 ms**. Absorbing the p90 needs about
  **12 packets**, so the honest figure is **+45 ms of audio latency**
  (15 → 60 ms), and `queue_capacity_packets` would have to rise from 8 as
  well. That trades lip-sync margin for concealment, and on a stream whose
  whole point is interactivity it is a real cost, not a free win.
- **Sender-side pacing: nothing to fix.** The sender already paces to
  within 80 microseconds of 5 ms. This lever is closed by measurement.
- **Reducing the path's jitter** is the same problem the video work has
  been addressing; the cap helped video and barely touched audio.
- **Renaming the counter is not needed.** It was suspected of being a
  poll-quantized duty cycle; it is not. `prolonged_starvation_events` is an
  accurate name for what it counts. What *was* misleading is reading it as
  a **fault** — 32/min sounds alarming and is simply the rate at which the
  path produces holes bigger than a 15 ms cushion, with **4 actual
  underruns in 20 minutes** and no audible consequence measured.

## 9. Artifacts

Under `evidence/d_base_p7_2026-09-22/`, SHA-256s in `p7_sha256.txt`:
`p7_run.sh`, `p7_analyze.py`, `heartbeat_P7.jsonl` (schema v3, with the
audio block), `frames_P7.jsonl`, `socket_P7.jsonl`, `report_P7.json`,
`status_P7.json`, `armcheck_P7.json`, `encoder_cmd_P7.txt`, `index.txt`,
`analysis_p7.txt`, `p7_ticks.json`.

Patch: `patches/D-BASE-P7_AUDIO_HEARTBEAT_COUNTERS.md`.

No address, MAC, SSID or device identifier appears here or in any artifact.
