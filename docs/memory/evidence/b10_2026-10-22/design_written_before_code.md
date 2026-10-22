# B10 — the client under loss: freeze on the last good frame, ask for a keyframe, count — design, before any B10 code

Baseline HEAD 0f4b551 + B8 / B9 (uncommitted). Queue: `handoffs/QUEUE_2026-10-22D.md` §B10. Data: BENCH-R2 §7 (e1,
`loss-1@post-fec`: 454 + 34 access units dropped, 488 in 11.65 min, ~42 / min; IDR frames 2,706 of 41,365 rendered;
the user saw missing faces and a coloured band with no counter moving).

## 0. Settled from the code (before designing)

1. **What the client does on a dropped access unit today** (`RtpH264Receiver.parseRtpPacket`):
   - an AU whose packets carried a sequence gap (`currentCorrupt`) is discarded at its marker
     (`droppedFrames`, `sequenceGapAccessUnitDrops`); an AU cut off by the next timestamp before its marker is
     discarded there (`incompleteAccessUnitDrops`, + `sequenceGapAccessUnitDrops` if it had a gap);
   - **`waitingForIdr` is set only by a stream resync** (`beginStreamResync`: a forward jump ≥ 128 packets or an SSRC
     change). An ordinary drop does not set it;
   - so **the next complete AU — a P-frame — goes straight to `onAccessUnit` → `AvcLowLatencyDecoder.queueAccessUnit`
     → MediaCodec**, which decodes it against a reference picture it never received, and every following P-frame
     inherits the damage **until the next IDR** resets the references. No counter marks those frames: the decoder
     renders them (`rendered_frames`), and the only trace is the drop count. That is the user's picture.
2. **How often the host sends an IDR today:** every encoder profile has `gop_frames=15` (`native_stream_profiles.py`;
   `h264_vaapi -g 15`, `-bf 0`, `idr_interval` 0 → every I-frame is an IDR): **one IDR every 15 frames, 250 ms at
   60 fps**. e1 measured 41,365 / 2,706 = 15.3 frames per IDR. The "≤ 41 frames" in the record is the longest gap
   seen, when IDRs themselves were dropped. So today a drop corrupts ≤ 14 frames (mean ~7), or more if the next IDR is
   lost too.
3. **Can the host insert an IDR on demand?** **Not in the running encoder.** The encoder is an `ffmpeg` process
   (`h264_vaapi`, `-nostdin`, RTP to the FEC relay); `-g` / `-force_key_frames` are fixed at launch, and ffmpeg 7.1's
   CLI has no runtime keyframe command (`sendcmd` / `zmq` reach filters, not the encoder). The only "existing path" to
   a fresh IDR is the actuator's **encoder restart** (C3.L1 / C3.L2a-E2: the replacement's first IDR is accepted 27 ms
   after the SSRC change) — and **a restart costs a 287-318-ms decoder output gap** (C3.L1R1 / C3.L1), longer than the
   ≤ 250-ms wait for the next natural IDR. So a forced IDR by restart would always freeze longer than waiting.

## 1. The client (`debug.privyhub.loss_guard=<1|count>`; absent = today: no object, no datagram, no key)

New `LossGuard.kt` (pure, JVM-tested); hooks are added lines only in `RtpH264Receiver.kt`, `NativeStreamActivity.kt`,
`NativeControllerSender.kt`.
- **`1` (guard):** on a dropped AU (either drop point, not during a resync's own IDR wait), the receiver **stops
  queuing non-IDR frames to the decoder** — the surface keeps the last complete frame (a freeze) — **until the next
  complete IDR**, which is delivered and ends the wait. At the episode's start **one `keyframe_request` datagram**
  (24 bytes, magic `PHK1`, B7's layout: kind, flags, seq, the delivered-AU count, the episode's drops) goes out on the
  controller socket from the controller sender's own 8-ms loop (as B7's stall). One per episode.
  - **A cap on the freeze: 600 ms.** If no IDR has come by then (the IDRs lost too), the guard stops holding and lets
    frames through as today (counted, `loss_guard_timeouts`), so the client's own link recovery (output silence
    ≥ 1,000 ms → the "Reconnecting" gate) is never tripped by the guard.
- **`count`:** nothing held, nothing sent; only the counter (today's behaviour, measured) — the guard-off cell.
- **The counter `frames_after_dropped_reference`:** every complete non-IDR AU between a drop and the next IDR — with
  `count` the corrupted frames the decoder was asked to decode; with `1` the frames that *would* have been corrupted
  (held, not queued: `loss_guard_frames_held`; queued after a timeout: the difference).
- **The report** (property set only): `loss_guard_mode`, `frames_after_dropped_reference`, `loss_guard_episodes`,
  `loss_guard_frames_held`, `loss_guard_timeouts`, `loss_guard_max_wait_ms`, `keyframe_requests_sent`.
- **The heartbeat** (property set only): `&frames_after_dropped_reference=…&loss_guard_episodes=…&loss_guard_frames_held=…`.
- Interaction: B7's client stall monitor sends at output age 150; a guard freeze of 150-600 ms sends stalls; the host
  (B9) acts at 400. Stated, not changed.

## 2. The host (`PRIVYHUB_LOSS_GUARD=1`; absent = today: a `PHK1` datagram is a bad packet, as any unknown one)

New `companion/keyframe_request.py`; hooks in `native_session_io.py` (one guarded statement before the 36-byte check,
as B7), `plugins/games.py` (import + wire), `games/native_stream_heartbeat.py` + the plugin's heartbeat parse (the
fields, as B3's `LINK_FIELDS`).
- **The receive loop** parses and queues; one worker handles. Every request is counted; **at most one per 500 ms is
  acted on** (the rest counted `rate_limited`).
- **Acting = `control.force_idr()`** through an encoder-control seam. Today's control is **`NoRuntimeIdr`**: it
  returns `forced: false` with §0.3's reason — the host has no IDR-on-demand path that is not a restart, and the
  restart is refused because its gap exceeds the wait it would save. **A forced IDR is logged `keyframe_forced`**
  (via, client seq, request → forced ms) when a control that can force one is given (the tests' fake; a future
  encoder with a runtime keyframe API). A per-minute `keyframe_requests` row carries received / acted / rate-limited
  / forced / unforced and the reason.
- **The heartbeat fields** (`frames_after_dropped_reference`, `loss_guard_episodes`, `loss_guard_frames_held`) are
  recorded when `PRIVYHUB_LOSS_GUARD` is set, so a record can say "N corrupted frames" from the host's log.

## 3. The cost, stated

- **The freeze:** with the guard, each drop freezes the picture until the next natural IDR: ≤ 14 frames (233 ms),
  mean ~7 (~117 ms), up to the 600-ms cap if an IDR is lost. At e1's rate (~42 drops / min, ≤ 42 episodes) that is
  up to ~5 s / min of held picture — the same frames that today are drawn corrupted (~42 × 7 ≈ 300 frames / min).
  The trade is a stutter for a wrong picture; the counter says how many.
- **A forced IDR, if the host could:** the wait would shrink to one round trip + one frame (~20-30 ms on the LAN), at
  the IDR's bytes per request: ≤ 90,000 B (the frame cap, D-BASE-P6a) against a ~14.6-KB P-frame at 7 Mbps — ≤ +75 KB
  per request, ≤ 150 KB/s at the 500-ms limit (+1.2 Mbps worst case). Not available today (§0.3).
- **The datagram:** 24 bytes per episode on the uplink.

## 4. Tests

- **Client (JVM, `LossGuardTest`):** the flag (`1`, `count`, absent / others off); the 24-byte encoding; with a fake
  decoder (a list of queued AUs) driven through the guard: a drop → no non-IDR queued → the IDR queued → resumed;
  one request per episode, taken once by the sender tick; `count` queues everything and counts the same frames; the
  600-ms cap; the report / heartbeat strings; a resync's own wait is not double-counted.
- **Host (`tests/keyframe_request`):** the parse; through the real receive loop: absent → a `PHK1` datagram is a bad
  packet; on → not a controller packet, counted; with a fake encoder control: one request → one `keyframe_forced`,
  ten requests in 500 ms → one forced, the rest rate-limited; `NoRuntimeIdr` → unforced with the reason; the
  heartbeat fields recorded only with the flag; FlagAbsent (no import).
- **The APK** (B5 + B7 + B10) built offline in the /tmp copy with `--no-configuration-cache`, only the companion
  active, pinned by sha256, NOT installed; the JVM suite.
- **Proofs:** host AST (B10 items removed = the predecessors); client textual (only added lines, all in the allowed
  forms).
- **CL-B9 sketched:** install, a `loss-1@post-fec` cell with the guard on / `count`, the user watching.
