# Active investigations

## C3 Linux actuator boundary

Record: `C3_LINUX_ACTUATOR_BOUNDARY.md`
Decision: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`
Evidence: `../evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`

Question: can the existing Linux streaming architecture expose safe
backend-neutral quality controls without disturbing validated playback?

State: source audit COMPLETE; Linux encoder-only actuator COMPLETE / RUNTIME
VALIDATED; `C3.L2` classification COMPLETE; `C3.L2a` E1 evidence pass COMPLETE
with its question still open.

Linux is `video_only_restart`: authorized for start-time profile selection,
manual and loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
characterization; not authorized for automatic adaptation during play.
`live_bitrate_reconfigure` is not available under the current architecture.

E1 changed what the open question is about. The decoder report's slow-event list
is a 128-entry ring that had already evicted the cycle's row, and in the
retained window — ordinary play, no actuator — output gap tracks codec time
one-to-one and reaches 238 ms. So 287-318 ms is not established as actuator
cost, and the existing probe cannot be re-run to settle it.

Next diagnostic: `C3.L2b` — make the decoder session report retain the cycle
(marked-window or segmented slow-event retention, `elapsed_ms` anchors for the
SSRC change and sequence resyncs, per-event IDR context for the first accepted
IDR after an SSRC change). Diagnostic-only client work; real Gradle build; one
clean cycle run afterwards.

Registered, not scheduled, not authorized: `C3.L2c`, enabling MediaCodec
low-latency decode. `low_latency_enabled` is false on
`c2.realtek.video.avc.decoder` while 2,696 of 3,847 frames took 20 ms or more to
decode. Production client behavior change; own hypothesis, own acceptance; must
not ride along inside `C3.L2b`.

Blocked downstream: the automatic bitrate controller (`C3.L4`), gated on
`C3.L2a`. `C3.L3` fixed-bitrate envelope revalidation is unblocked for manual
characterization and is sequenced after `C3.L2a` closes.

## Deferred, not active

- UDP burst/gap pathology — awaiting representative Linux replay. See
  `DEFERRED.md` and `docs/KNOWN_ISSUES.md`.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.
