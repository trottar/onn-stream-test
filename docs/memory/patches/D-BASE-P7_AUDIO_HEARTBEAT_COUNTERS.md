---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P7 — the audio counters ride the heartbeat

## Purpose

`prolonged_starvation_events` was the last counter in the decoder report
whose meaning was unknown. Reading it needed the audio counters **on the
same 2 s clock as the loss series**, plus one measurement that did not
exist: **how long the gaps between arriving audio datagrams actually are.**

**Diagnostic only. The starvation counter's semantics are not touched**,
no new thread is created and nothing new is sampled — the arrival gap is
one `max()` on a receive path that was already running.

## Changed scope

**`PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`**
-> `9c808a3db7f951ac72e24fcbe74a12cf6b0b895d2073e768b8f20e2d768c59cb`
(was `76fe6401fb02da3897794b1aff7fe5f9e06815c5d03eb73447306a4a00877131`).

- `NativeAudioMetrics` gains **`maxArrivalGapMs`**, the largest gap between
  two consecutive valid audio datagrams over the **whole session**.
- The receive loop takes `System.nanoTime()` **after** the header checks —
  so a malformed datagram does not reset the clock — and feeds the gap to
  two atomics through a small lock-free `updateMax` helper.
- **Two atomics, deliberately.** `maxArrivalGapNs` is the session maximum
  and is **never reset**, so the end-of-session report reads a
  whole-session figure. `windowMaxArrivalGapNs` is read-and-reset by
  **`takeWindowMaxArrivalGapMs()`**, which the heartbeat calls. Had the
  heartbeat reset the session figure, it would have corrupted the report —
  both read the same `snapshot()`.

**`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`**
-> `96582702ab52799d0abf7847c09020ccb60004167457831eb5ecb7b9b319c1d6`
(was `6aeee06283bcfd94cdd577085e29033310336c5d22a830b908c974a75acc2d8e`).

`maybeSendStallHeartbeat` takes `audioReceiver?.snapshot()` beside the
decoder and RTP snapshots it already took, and a new `audioQuery()` appends
ten fields. **Every field is omitted when the audio receiver is absent
rather than sent as 0** — the `D-BASE-P4` rule, so a missing value reads as
missing.

**`companion/games/native_stream_heartbeat.py`**
-> `e787add207afdb07dcbc403437f38fd40d424bdb661576c51deffc9bb02c2dd3`
(was `a39521e5a986e7b0c537eb390750d65b5a0d6e396ebaf8e7d57df9f0a5957550`).

`SCHEMA` bumped to **`privyhub_native_stream_heartbeat_v3`**; `AUDIO_FIELDS`
passed through unchanged, each optional.

**`companion/plugins/games.py`**
-> `90e568d68014cfeede86dba85a25d7939b5bc7bb9b8c8c09f273fb9b9ad073a8`
(was `23de0c410044b7291775145ac7239e52675cc2cdf8870b79e6e04cdec9e7a658`).

The ten audio keys added to the `native-stream-heartbeat` integer
whitelist. **This is the gate**, and it is called out in a comment because
missing it is exactly what happened: the first build sent all ten fields
and the log recorded none of them, because a key not on this list is
dropped silently. That session was abandoned and re-run after the fix.

## Cost

One `System.nanoTime()`, one comparison and one or two uncontended CAS
loops per **audio** datagram — 200 a second, against a receive path that
already parses a 16-byte header and copies a payload. One extra
`snapshot()` per 2 s heartbeat. The heartbeat line grows from ~465 to ~620
bytes, so the 4 MiB log fills in ~3.7 h instead of ~5.0.

Measured in the session: fps **59.94**, `spike_20_ms` **25.6/min**, video
loss 4.4/min — all inside the bands the capped profile has been producing.
**No cost shows.**

## Validation

**Runtime**: one 20-minute session, **597 heartbeats all carrying the ten
audio fields**, 596 usable tick intervals, and the new gap field
immediately produced the result the task was after — starvation tracks the
arrival gap at **rho +0.684** while audio loss is flat at **+0.020**.
Record: `evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.

APK `6d25dee0…be96`, **hash-verified against `pm path` on the device**
before the session counted. `git diff --check` clean; Python compiles;
Gradle build clean.

## Not done

- **The starvation counter is unchanged.** `P7` names what it counts; it
  does not redefine it, and the record argues it needs no renaming.
- **No audio behaviour changed** — not the queue target, not the capacity,
  not the prefill. The deeper-cushion lever is costed in the record and
  left to the user.
- **No encoder change**; the adopted profile was in force throughout.
