---
memory_schema: 1
as_of: 2026-09-21
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R5 — the receiver's loss counters ride the heartbeat

## Purpose

`D-BASE-P4` established that loss on this link is **episodic** — a
20-minute session lost at 105/min in 14.9-packet bursts while six 2-minute
sessions read 1.4-24.6/min — and that **no per-minute loss series existed**,
because the receiver's counters were visible only in the end-of-session
report. P4's attempt to derive one from host-sent minus client-received
measured the noise at **86 packets per 10 s window against a 3.0-packet
signal**, a 29x ratio, with windows coming out negative.

The receiver already maintains every counter needed. This patch only puts
them in the 2 s heartbeat that already exists. **Diagnostic only: nothing
new is sampled, counted, threaded or acted upon.**

## Changed scope

**`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`**
-> `6aeee06283bcfd94cdd577085e29033310336c5d22a830b908c974a75acc2d8e`
(was `e0c013f6ddcc37b0031a59d2e412925b0aa5dfd531fe7246f8afbc7210673dda`).

One touch point: the heartbeat query string in `maybeSendStallHeartbeat`
gains seven fields read from the **same `receiver.snapshot()` the function
already calls** for `rx_packets` — `lost_packets`,
`lost_packets_in_resyncs`, `forward_gap_events`,
`max_forward_gap_packets`, `stream_resyncs` (the sum of `sequenceResyncs`
and `ssrcChanges`, which the report keeps apart), `fec_recovered_packets`
and `fec_unrecoverable_groups`. **No new snapshot, no new thread, no change
to what the receiver counts, and no change to the heartbeat's cadence or
its failure behaviour.** Values are cumulative session totals, so a delta
between any two heartbeats of one session is exact.

**`companion/games/native_stream_heartbeat.py`**
-> `a39521e5a986e7b0c537eb390750d65b5a0d6e396ebaf8e7d57df9f0a5957550`
(was `8fb47b11998d75a485a8dfec4f6889e7a94da6e2686a1bef846a8ad4f545287d`).

- `SCHEMA` bumped to **`privyhub_native_stream_heartbeat_v2`**.
- `LOSS_FIELDS` passed through **unchanged** — nothing here derives,
  smooths or resets. Each is optional, so an older client records nothing
  for it rather than a zero.
- New `loss_per_min_recent()`: loss over the last 60 s of the current
  session. It uses the client's **`elapsed_ms` as the clock**, not wall
  time, so a companion restart does not distort it, and it **stops at a
  session boundary** — a heartbeat whose `elapsed_ms` goes backwards
  belongs to a later session whose counters restart at zero. Returns
  **None, never 0**, when there is no session, when the client is too old
  to send the counters, or when the window holds fewer than two
  heartbeats.
- New `_tail_records()` reads and parses the log tail, skipping torn lines
  rather than raising: a status call must not fail on a half-written line.
- `LOSS_WINDOW_TAIL_BYTES` = 64 KiB, because a 60 s window at ~450 bytes a
  line and 30 lines a minute does **not** fit in the existing 8 KiB
  `MAX_TAIL_BYTES`, which stays as it is for `latest_native_stream_heartbeat`.

**`companion/plugins/games.py`**
-> `1d466421c2854033af372b2d3f438039610c2af751fdfd552e7bc0dd8c017415`
(was `47b008280b416be393a8def7dfc8daffb8e80e8e35ee9e4d2ffb6a28ceff8af5`).
The `native-stream-heartbeat` ingest loop gains the seven field names, and
`native-stream-status` gains `loss_per_min_recent`.

**Not changed:** the receiver, the decoder, the relay, the encoder, the
report, the heartbeat cadence, and everything else.

**APK** `8d6004fdac54872ec376dd8232d1908de4e26a8ccb9947e34311accd84fb26e1`,
built from `PrivyHub/` and **hash-verified against the installed package on
the device** before any session was treated as evidence.

## Validation

Offline first, before spending a build: `loss_per_min_recent` was driven
against synthetic logs and got the arithmetic right (2 lost per 2 s tick ->
**60.0/min** over a 60.0 s window), **confined its window to the current
session** when `elapsed_ms` restarted, returned **None rather than 0** for
a client sending no loss fields and for a log with one heartbeat, and left
`latest_native_stream_heartbeat` working on v1-shaped records.

Runtime: one 20-minute attract-mode session of the PS1 reference title,
zero input, per `TOOLS.md`. Full numbers and every check in
`evidence/D_BASE_R5_HEARTBEAT_LOSS_COUNTERS_2026-09-21.md`.

`python3 -m py_compile` clean on both Python files; the Gradle build is
`BUILD SUCCESSFUL`; `git diff --check` clean.

## Status

**DEVELOPMENT / DIAGNOSTIC.** Runtime status is whatever the evidence
record says; this patch record does not assert it.
