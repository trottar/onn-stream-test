# CL-B7P §1 — the location, from the client's code

The reading was done before any code edit and fixed the design (`design_written_before_code.md`, hashed
14:43:55Z); this write-up of it was written after that hash, while the build waited on session A's unit.

Source: `PrivyHub/app/src/main/java/streaming/` at HEAD `7a1ab60` (predecessors in `predecessors/`). Every claim below
is from the code unless marked **(framework, recalled)** — a statement about Android's MediaCodec / Codec2 internals
from memory of AOSP, not read in this task (nothing fetched); CL-B7's reads check each one.

## 1. The thread map during a stream

The client sets **no thread priority anywhere**: 0 hits for `setThreadPriority`, `THREAD_PRIORITY`, `priority =`
under `app/src/main/java/`. Every thread below is made with Kotlin `thread(...)` or `Thread(...)` without a priority,
so it inherits the creator's Java priority (5, nice 0 on Android). All ours are equal.

| thread (name in code) | where | per packet / frame | priority |
| --- | --- | --- | --- |
| `PrivyHub-RTP-H264-FEC` | `RtpH264Receiver.kt:433` | video RTP receive, RS(8,2) FEC, access-unit assembly → the decoder's input queue (capacity 4) | none (nice 0) |
| `PrivyHub-MediaCodec` | `AvcLowLatencyDecoder.kt:319` | the video decode loop: `drainOutputs` (`dequeueOutputBuffer(info, 0)` until empty; the ≥ 20-ms spike counter is here, `:737`, receive → output latency), then `queue.poll(2 ms)`, `dequeueInputBuffer(1 ms)`, `queueInputBuffer`; render by `releaseOutputBuffer` | none (nice 0) |
| `PrivyHub-Native-Audio-RX` | `NativeAudioReceiver.kt:733` | `DatagramSocket.receive` (timeout 500 ms, 64 KiB buffer), PHA1 parse, dedupe; PCM: copy 960 B, enqueue; Opus: copy the payload, `OpusReorder`, `offerFrame` | none (nice 0) |
| `PrivyHub-Native-Audio-Opus` (Opus only) | `OpusDecodePipeline.kt:80` | `poll(200 ms)` → `OpusAudioDecoder.decode` (MediaCodec, synchronous) → `OpusFraming.split` → 2 × `enqueueLatest` | none (nice 0) |
| `PrivyHub-Native-Audio-Playback` | `NativeAudioReceiver.kt:724` | `queue.poll` → `AudioTrack.write(…, WRITE_BLOCKING)` of one 5-ms packet (960 B), low-latency track; the same for both codecs | none (nice 0) |
| `PrivyHub-Native-Controller` | `NativeControllerSender.kt:113` | controller state send loop | none (nice 0) |
| `PrivyHub-Stall-Heartbeat`, `PrivyHub-Client-Health` | `NativeStreamActivity.kt:2430`, `:2617` | one HTTP post each per 2 s, short-lived threads | none |
| `PrivyHub-Native-Session` / `-Ready` / `-Stop` / `-Desync` / `Paused-Frame` | `NativeStreamActivity.kt` | one-shot control posts | none |
| main (UI) | the activity | metrics, overlay, surface | the framework's |
| **framework, in the app process, per MediaCodec instance (recalled)** | not our code | each MediaCodec has its own looper thread(s); every synchronous call (`dequeueInputBuffer`, `queueInputBuffer`, `dequeueOutputBuffer`, `releaseOutputBuffer`) is a message posted to that looper and a wait for its reply. The Codec2 client queues work to the component over binder, and the component's "work done" comes back on the process's binder thread pool, **shared by both codecs**. AOSP starts these loopers at raised priorities, above nice 0. | the framework's (to read) |
| **out of process (recalled)** | — | `c2.android.opus.decoder` is a software Codec2 component: on Android 10+ it runs in the `media.swcodec` process, **not** in PrivyHub's. The H.264 decoder is the SoC's hardware component in a vendor process. | — |

## 2. The per-second work, counted from the code

**Opus** (10-ms frames, 2 copies, 128 kbit/s CBR: 160-B packets in 176-B datagrams):

- RX thread: **200 datagrams/s** → 200 `receive` + header parse + `seenSequences` check; 100 pass (100 dropped as
  duplicates). Per pass: `copyOfRange` of the payload (~160 B), `OpusReorder.offer`, `offerFrame`
  (an `ArrayBlockingQueue.offer`: lock + signal) → **100 decode-thread wake-ups/s**.
- Decode thread, per frame (`OpusAudioDecoder.decode` / `drain`):
  1. `dequeueInputBuffer(10 ms)` — synchronous call
  2. `getInputBuffer` (JNI), put ~160 B
  3. `queueInputBuffer` — synchronous call (+ the Codec2 client's work queue to the component)
  4. `dequeueOutputBuffer(info, ≤ 4 ms)` — synchronous call, **blocks ~3.2 ms per frame** waiting for the output
     (CL-B5: `decode_avg_us` 3,161; blocked, not CPU)
  5. `getOutputBuffer` (JNI); `ByteArray(1,920)` + copy 1,920 B
  6. `OpusFraming.split` → 2 × 960 B arrays (copy 1,920 B) + a list; 2 × `enqueueLatest` (PcmPacket + queue offer)
  7. `releaseOutputBuffer` — synchronous call
  8. `dequeueOutputBuffer(info, 0)` — synchronous call; nothing pending, so it returns `INFO_TRY_AGAIN_LATER`
     almost always (the next output is ~3 ms after the next input)

  Per second: **500 synchronous MediaCodec calls** (5 per frame), 200 JNI buffer gets, ~384 KB/s copied in Java
  (1,920 + 1,920 B × 100), ~100 × 2 Codec2 binder transactions (work queued, work done) **(framework, recalled)**.
- Playback thread: 200 × (poll + `AudioTrack.write` 960 B) per second. **Same as PCM.**

**PCM** (5-ms packets, 2 copies, 976-B datagrams: 16-B header + 960 B):

- RX thread: **400 datagrams/s** → 400 `receive` + parse + dedupe; 200 pass, each `copyOfRange` 960 B +
  `enqueueLatest` (192 KB/s copied). **No codec, no decode thread, no hand-off.**
- Playback thread: as above.

**The net, Opus against PCM, both ways:**

| | Opus does, PCM does not | PCM does, Opus does not |
| --- | --- | --- |
| socket | — | **+200 `receive`/s** (400 vs 200) and their parse / dedupe |
| hand-off | **+100 queue hand-offs/s** (RX → decode thread wake-ups) | — |
| codec | **+500 synchronous MediaCodec calls/s** (each a looper post-and-wait: ≥ 2 thread switches) **+ ~200 binder transactions/s** and the callbacks on the binder pool | — |
| copy / alloc | ~384 KB/s copied, ~100 × (1,920 + 2 × 960 B) arrays | 192 KB/s copied, 200 × 960 B arrays |

## 3. The hypothesis, stated once

**The ~0.2 core (CL-B6: PrivyHub 107 % vs 85 % of a core, single `top` samples) is the MediaCodec client-side
per-buffer machinery in the PrivyHub process: 500 synchronous calls/s, each a post-and-wait to the codec's looper,
plus the Codec2 client's ~200 binder transactions/s and their callbacks — about 1,000-1,500 extra thread switches a
second spread over framework threads (the looper(s), the binder pool) — not our decode thread's Java code and not
the decode itself.**

Why this, from the code:
1. **The decode itself is out of process** (recalled): `c2.android.opus.decoder` runs in `media.swcodec`, so libopus's
   own cycles are not in PrivyHub's 107 %.
2. **Our decode thread has no tight loop:** it blocks in `poll(200 ms)` and in `dequeueOutputBuffer` with a wait;
   the 3.2-ms average decode call is mostly blocked time.
3. **The copy is too small:** ~0.4 MB/s of Java copies and ~300 small arrays/s, against PCM's 0.2 MB/s / 200.
4. **The receive side is cheaper with Opus** (−200 `receive`/s), so the extra must come from what Opus adds:
   the hand-off (100/s, cheap) and the codec traffic (the bulk of the count).

**The size is not proved by the count.** At a plausible 20-50 µs per looper round trip and 50-100 µs per binder
transaction on the onn's cores, the count gives ~0.03-0.05 core, not 0.2. Either the per-call cost on this SoC is
several times that, or part of CL-B6's 0.22 is the single samples' noise, or the owner is elsewhere. That is what
CL-B7's per-thread read decides.

**How CL-B7 tests it on the onn: `tools/cl_b7_onn_threads.py`** (adb state reads only; written here, not run):
`top -H -p <PrivyHub>` for 10 one-second iterations (the first dropped), per thread name: PR, NI, %CPU mean / max;
the same seconds' process view: PrivyHub, `media.swcodec`, the codec HAL services, audioserver, surfaceflinger; the
onn's busy %; `getprop debug.privyhub.opus_decode`. PIDs / TIDs not written, digit runs in names masked.

Reading the result (Opus arm minus PCM arm, per category):
- **the delta sits on the framework codec threads and binder threads** → the hypothesis holds; the lean drain
  (§2) should take ~1/5 of the looper share off;
- **on `PrivyHub-Native-Audio-Opus` itself** → our Java side (JNI, copies, allocation / GC) owns it; the next
  change is the copy (split straight from the output ByteBuffer), not the call count;
- **`media.swcodec` absent or idle and a thread named like the component inside PrivyHub** → the decoder runs in
  process on this build; libopus's own cost is then the owner;
- **no thread carries a delta beyond the samples' spread** → CL-B6's 0.22 was noise; the item reduces to the
  spikes alone.

## 4. Why the video decoder's spikes would follow (hypothesis)

The spike counter (`AvcLowLatencyDecoder.kt:737`) counts outputs whose receive → output latency is ≥ 20 ms,
measured when `PrivyHub-MediaCodec` dequeues them. That thread polls: `dequeueOutputBuffer(0)`, then
`queue.poll(2 ms)` and `dequeueInputBuffer(1 ms)`. So an output's latency grows past 20 ms when the frame is late
into the decoder (the RX / assembly thread was not run) or when the drain thread itself is not run.

With Opus, every 10 ms a chain of wake-ups runs: RX → decode thread → the codec's looper → binder → `media.swcodec`
→ binder pool → looper → decode thread → PCM queue → playback. On a 4-core onn ~50 % busy, the video threads
compete with that chain as equals (ours: all nice 0) and lose to the framework threads raised above nice 0
(recalled; CL-B7 reads PR / NI). The video codec's own work-done callbacks share the process's binder pool with the
Opus codec's 100/s. More audio wake-ups → more moments when a video receive, assembly, feed or drain waits behind
them → more outputs late by ≥ 20 ms. PCM has no such chain (its RX thread enqueues directly).

This is consistent with CL-B5 / CL-B6 (Opus +43-44 spikes / min on the same evening) and with G4-S3 (fewer video
bytes at 4000, ~45 / min). It is a hypothesis. CL-B7's per-thread read (who runs, at what NI) and the third arm
(`lean`: −100 calls / s) test it: if the spikes follow the call count, the lean arm sits between the other two.
