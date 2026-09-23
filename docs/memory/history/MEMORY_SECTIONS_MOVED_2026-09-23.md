---
memory_schema: 1
as_of: 2026-09-23
status: HISTORY — MEMORY.md sections moved out verbatim on 2026-09-23 to bring MEMORY.md under its soft size limit; each left a one-line pointer in place. Nothing rewritten.
---

# MEMORY.md sections moved 2026-09-23

## C3 Linux actuator boundary and classification — durable facts

`C3.L0`/`C3.L2`/`C3.L2b`/`C3.L3`/`C3.L3a`, 2026-09-18/19. **Phase C is
SUSPENDED**; this is where it was left. Full map:
`investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`; authoritative decision:
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

**No live bitrate actuator exists on Linux, and the architecture
forecloses one.** The encoder is an external FFmpeg CLI (`-nostdin`,
`stdin=DEVNULL`), bitrate baked into argv at `Popen`; no control socket,
no in-process handle. `live_bitrate_reconfigure` needs an architecture
change, not a patch. **Linux video topology is single-process** (x11grab
is an input format where Windows uses a WGC bridge), so Windows actuator
interruption figures are **not** portable, and **`_start_linux_locked` is
not an actuator**: it calls `_stop_locked()`, stopping the FEC relay,
session I/O and host telemetry too.

**Resolution and FPS are client-pinned, not negotiated.**
`NativeStreamActivity` holds `VIDEO_WIDTH`/`HEIGHT`/`FPS` as compile-time
constants; `AvcLowLatencyDecoder` configures MediaCodec once, never
derives dimensions from the in-band SPS, and ignores
`INFO_OUTPUT_FORMAT_CHANGED`, so host and client can silently diverge.
GOP is in frames, so an FPS change rescales the keyframe interval.

**Linux is `video_only_restart`.** **Authorized:** session start and
start-time profile selection before `READY`; manual and loopback-only
diagnostic changes; fallback and recovery; `C3.L3` characterization.
**Not authorized:** automatic adaptation during `PLAYING` — a controller
fires under pressure, when delivery is already degraded, and repeatedly,
against a standing preference to minimize perceptible artifacts. *(Its
original "~290 ms discontinuity" figure is falsified; the
frequency-and-timing argument stands.)* **The gate for `C3.L4` is
`C3.L3a`, not `C3.L2a`**: repeated, unannounced, under-pressure
transitions with a no-op control interval, the player's marks compared
against `stream_discontinuities` **after** the session, plus a judgement
of the picture.

**Chained ladder transitions work.** Several in one session, either
direction, between `(5000, 5500, 6000, 7000)` kbps; six ran clean. Use
`run_c3_linux_validated_bitrate_transition`; the `C3.L3` path still
requires a 7000 start and cannot target 7000. **The actuator's first IDR
is accepted fast, on seven observations**: 18-65 ms plus 27 ms from
`C3.L2a` E2, all AU-complete, none FEC-repaired; discontinuities typed
`ssrc_change` with `jump_packets` 0 — an encoder restart does not disturb
the RTP sequence; ~1.17 s per transition. **A fresh encoder process
already starts with a keyframe**, and **the 287-318 ms figure from
`C3.L1` was never actuator cost**. **`max_resync_to_idr_ms` and
`packets_dropped_waiting_for_idr` are whole-session values.**

**6000 kbps is the most consistent characterized level** —
`decoder_max_output_gap_ms` 331/291/307, a 40 ms band, against 125 and
365 ms at 5000 and 5500. Every figure is transport and decoder timing:
**no perceptual quality was measured**, so no bitrate is a fallback level
on this data, and **the Windows 5500/6000/7000 ladder is evidence, not a
Linux constant** (D-071).

**FEC group size is the only in-place seam** (the header carries the real
group length, the receiver validates 1 to 8; mutation needs no restart,
SSRC change, resync or IDR wait). **C4 owns adaptive FEC; C3 does not
actuate it.** Diagnostic actuators exist and are unowned:
`PRIVYHUB_FEC_PACING_US` (`P3`) and `PRIVYHUB_ENC_BUFSIZE_K` (`P6`), both
default off; `PRIVYHUB_ENC_MAX_FRAME_SIZE` now **overrides an adopted
profile default** rather than enabling anything.

**Decoder-report retention** (`C3.L2b`). The report retains **two
slow-event segments, not one ring**: `_marked` (64) for events recorded
while a cycle window was open, `_recent` (64) for ordinary play, merged by
`elapsed_ms`. **A cycle window opens on every SSRC change and sequence
resync for 2000 ms** — a judgment call, not runtime-validated.
**`stream_discontinuities`** gives `elapsed_ms`, `type` and
`jump_packets`; **`first_idr_after_discontinuity`** is a **parallel array
joined by index**. **Both bounded to 64** (`S2` had 95), and neither
covers the session-start IDR. **`au_fec_unrecoverable_group` does not
cover `trimFecGroups`'s capacity eviction** (>96 groups) — an accepted gap
that can only under-report. One thing from the superseded design holds:
**the diagnostic bundle's native video section is the last 500 lines**, so
a missing restart banner is not evidence that none happened.

## A stalled encoder makes no sequence gap — FALSIFIED as written

`C5a`, **amended the same day by `D-BASE-B2`**, 2026-09-21. Records:
`evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`,
`B2_HOST_ON_OPAL_2026-09-21.md`.

**The rule said** a SIGSTOP of the encoder cannot produce a sequence resync
at any pulse short of a restart. **A 3 s stall gave a 690-packet
`sequence_resync` with `restarts` 0 and `ssrc_changes` 0**, off a resume
burst of 2,587 packets against a steady ~1,650. **The packets were minted
and dropped on that burst**: the boundary is the burst's size, and **a long
enough stall produces real loss, not only silence.**

**What survives:** a *stopped* encoder burns no sequence numbers, which
is what `C5a` measured with **0.3 s** pulses — too small a resume burst to
overflow anything, so the gap is in **time**, not **sequence**. **A short
pulse is a silence injection, not a loss injection.** Consequently
**`R3a`'s 720/984/480-packet jumps are unattributed**, and **the nftables
plan remains the only injection that drops packets on the wire by
construction.**

**The `C5a` counters** (`idr_aus_rejected_waiting_for_idr`,
`non_idr_aus_dropped_waiting_for_idr`, and the per-discontinuity
`rejected_idr_aus`/`dropped_non_idr_aus`) cannot fire at session start —
the encoder starts *with* the client — only after a resync.

## Sender pacing is not the loss lever at 150-400 us — durable fact

`D-BASE-P3`, 2026-09-21. Records:
`evidence/D_BASE_P3_SENDER_PACING_2026-09-21.md`,
`patches/D-BASE-P3_FEC_RELAY_SENDER_PACING.md`.

**The relay can pace and does not by default** (`PRIVYHUB_FEC_PACING_US`,
environment, read at relay `start()`; off is byte-for-byte the old path).
**`time.sleep` cannot pace this stack** — a ~55 us overshoot floor, so
`sleep(150 us)` returns after 205; a busy-wait on `perf_counter_ns` lands
at 150.1 us p50.

**Fifteen 120 s sessions, strictly alternating, 0 rejected: mixed, not
adopted.** Loss/min fell in **3 of 5** pairs, medians **1.72x** where the
bar was 4 of 5 and 2x, while **`spike_20_ms`/min rose in 5 of 5, +41 %**.
Packets per gap fell in 4 of 5 and max forward gap halved, 16 -> 8. At
400 us spacing reaches only **187.5 us**: **it does not scale.**

**Two things bound that null.** The 8 ms budget clamps spacing above **53
packets/frame** at 150 us against a mean frame of 15.85 — **the large
frames a queue-overflow account blames are exactly the ones it refuses to
spread**, which is why `P6` succeeded where this did not. And the off arm
swung **1.8-35.2 loss/min inside one hour**: episodic loss, badly sampled.

**The onn asks for a 2 MiB receive buffer and never reads back what it
got** (`RtpH264Receiver.kt:573`); `rmem_max` is 8 MiB, so nothing clamps
it.
