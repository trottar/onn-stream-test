---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: ee2f89f
durable_memory_updated: true
---

# D-BASE-P8 — every audio arrival hole, tagged with the 2 s senders

## Purpose

`P7` found a 55-60 ms hole in the audio arrival stream about once every
2 s and could not locate it. Two things run on a 2 s clock: the client's
stall heartbeat and the host's adb socket sampler. This records **every
hole** with where the heartbeat was when it opened, so the alignment can be
read directly. **Diagnostic only**: no new thread, no new sampling, every
existing counter's semantics unchanged. Built and installed directly under
the overnight authorization (`handoffs/OVERNIGHT_2026-09-23_QUEUE.md`),
not as a ZIP.

## Changed scope

**`PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`**
-> `19ce21562553cf4d2751ca8f49b855efb281f5af0d5691e4ce21e0a4a028c688`
(was `9c808a3db7f951ac72e24fcbe74a12cf6b0b895d2073e768b8f20e2d768c59cb`).

- New top-level `object AudioHoleTrace`: `heartbeatInFlight`
  (AtomicBoolean), `heartbeatLastStartNs`, `healthLastStartNs`
  (AtomicLong). Set by the activity, read by the receive thread only.
- In the receive loop, beside `P7`'s `updateMax`, a gap **> 15 ms**
  appends one row to a bounded ring (**4,000**): start (monotonic ms, the
  previous datagram's arrival), length, ms since the last heartbeat start
  (signed; null before the first), the in-flight flag, ms since the last
  client-health start. A short `synchronized` block, holes only.
- `arrivalHolesJson()` returns the ring for the report.

**`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`**
-> `b640e2bedc6c1c5e36acfcd111cad31a94ebcc4c70433a5df135b683ed9dfe60`
(was `96582702ab52799d0abf7847c09020ccb60004167457831eb5ecb7b9b319c1d6`).

- The heartbeat thread sets `heartbeatLastStartNs`/`heartbeatInFlight`
  around its `httpPost`; the client-health thread sets `healthLastStartNs`
  (the second 2 s sender, found in the code — added beside the heartbeat
  so it can be read the same way).
- `heartbeatIntervalMs` (default `HEARTBEAT_INTERVAL_MS` = 2,000) is read
  once per session from the `native-stream-start` response's
  `heartbeat_interval_ms`, clamped 1,000-10,000.
- Report: `audio.arrival_holes` {threshold_ms, capacity, total, retained,
  columns, rows} and `audio.heartbeat_interval_ms`. **Schema
  `privyhub_native_decoder_session_v1` → `_v2`**, profiler `0.12.2` →
  `0.12.3`; no v1 field changed. Nothing in `companion/` or `tools/` reads
  the schema string.

**`companion/plugins/games.py`**
-> `c7c753a988cf91112b45452167bb31bcd53239b6f6c910121b0e1266443aa034`
(was `90e568d68014cfeede86dba85a25d7939b5bc7bb9b8c8c09f273fb9b9ad073a8`).

- `native-stream-start` returns `heartbeat_interval_ms` from
  **`PRIVYHUB_HEARTBEAT_MS`** (read at each stream start, clamped
  1,000-10,000, default 2,000). Diagnostic only. The heartbeat can be
  slowed, never disabled — link-drop recovery reads it.

## Validation performed

- `python3 -m py_compile companion/plugins/games.py`; `git diff --check`
  clean.
- `./gradlew :app:assembleDebug` — first attempt failed (`This annotation
  is not repeatable`: the new field was inserted between an existing
  `@Volatile` and its property); fixed, BUILD SUCCESSFUL.
- APK `dc8bf37e16bfd8cd372e035ae374c5e3f97c783f02b7850166cf99f61eb05678`;
  installed, the device's package hash equal.
- Runtime: a 60 s smoke session with `PRIVYHUB_HEARTBEAT_MS=10000` —
  report schema v2, `heartbeat_interval_ms` 10000, heartbeats 10 s apart
  in the host log, 185 holes in the ring. Then the three `P8` arms
  (`evidence/D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md`).

## Revision v2 — the ring was too big for the report's transport

The decoder report travels as a **URL query**
(`POST …/decoder-session-log?report=…`), and the companion's
`http.server` rejects a request line over 65,536 bytes with **414**
(then crashes in `send_error` on a missing `path` attribute — a
pre-existing companion bug, not fixed here). A 20-minute session holds
~3,000 holes; at ~44.5 encoded bytes per row the v1 ring (4,000) made
the report unsendable, and **the first P8 run lost the reports of arms
A and C** (any session over ~5 minutes would have). v2:

- raw ring **300** rows (the last 300, for a spot check);
- **whole-session histograms on the device**: hole length (edges
  15/20/30/40/50/60/70/100/200 ms), and ms since the last heartbeat start
  (50 ms bins, 0-10,000) and since the last client-health start (50 ms
  bins, 0-2,000), each for all holes and for holes >= 40 ms, with
  outside-range and in-flight counts — `arrival_holes.histograms`.

The encoded report is ~40 KB whatever the session length (5-min check:
791 holes, report landed). `NativeAudioReceiver.kt` →
`3537b26102c33180f0c63a25388e3a4fbd0f1a6a08bb47bca6b1c98c261edf81`; APK
`322022efb71ed48384199008ede58a0caa4d49d6ea68721577c4c71283878492`,
installed, device hash equal. `NativeStreamActivity.kt` and
`companion/plugins/games.py` unchanged from v1.

## Status

**INSTALLED (v2), diagnostic.** Leave installed or revert as the user decides;
the default heartbeat interval is unchanged with the variable unset.
