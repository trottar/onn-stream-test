# Active investigations

## C3 Linux actuator boundary

Record: `C3_LINUX_ACTUATOR_BOUNDARY.md`
Decision: `../decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`
Evidence: `../evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`
Patch: `../patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`

Question: can the existing Linux streaming architecture expose safe
backend-neutral quality controls without disturbing validated playback?

State: source audit COMPLETE; Linux encoder-only actuator COMPLETE / RUNTIME
VALIDATED; `C3.L2` classification COMPLETE; `C3.L2a` E1 evidence pass COMPLETE
with its question still open; `C3.L2b` decoder-report retention CODE
INSTALLED, runtime evidence not yet collected.

Linux is `video_only_restart`: authorized for start-time profile selection,
manual and loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
characterization; not authorized for automatic adaptation during play.
`live_bitrate_reconfigure` is not available under the current architecture.

E1 changed what the open question is about. The decoder report's slow-event list
was a 128-entry ring that had already evicted the cycle's row, and in the
retained window — ordinary play, no actuator — output gap tracks codec time
one-to-one and reaches 238 ms. So 287-318 ms is not established as actuator
cost, and the existing probe could not be re-run to settle it.

`C3.L2b` fixed the retention defect: a 64-entry marked segment (protected by a
2000 ms window opened on every SSRC change and sequence resync) alongside a
64-entry recent segment, `elapsed_ms`-anchored `stream_discontinuities`, and a
bounded `first_idr_after_discontinuity` list with per-event `resync_to_idr_ms`
and FEC-recovery/completeness context. It is installed as code — three Kotlin
files compiled for real with the Kotlin compiler — but no APK built with the
real Android/Gradle toolchain has been installed on the onn device, and no
actuator cycle has run against it. `C3.L2a` stays open until that happens.

Next diagnostic: build (`sh ./gradlew :app:assembleDebug --no-daemon`),
install (`adb install -r`), run one clean `C3.L1`-style encoder-only actuator
cycle against the rebuilt client, and re-read the decoder session report's new
fields. Do not run `tools/probe_c3_actuator_continuity.py` against the old
APK; the same eviction the E1 pass found will recur against unchanged code.

Registered, not scheduled, not authorized: `C3.L2c`, enabling MediaCodec
low-latency decode. `low_latency_enabled` is false on
`c2.realtek.video.avc.decoder` while 2,696 of 3,847 frames took 20 ms or more to
decode. Production client behavior change; own hypothesis, own acceptance; was
not folded into `C3.L2b`.

Blocked downstream: the automatic bitrate controller (`C3.L4`), gated on
`C3.L2a`. `C3.L3` fixed-bitrate envelope revalidation is unblocked for manual
characterization and is sequenced after `C3.L2a` closes.

## Deferred, not active

- UDP burst/gap pathology — awaiting representative Linux replay. See
  `DEFERRED.md` and `docs/KNOWN_ISSUES.md`.
- Adaptive FEC — C4.
- Linux host resource telemetry gap — recorded in `docs/KNOWN_ISSUES.md`; not an
  active investigation.

## C3.L2a — CLOSED 2026-09-18

Answered by one encoder-only cycle against the `C3.L2b` client. The replacement
encoder's first IDR was accepted 27 ms after the SSRC change, access unit
complete, no FEC repair; the two ordinary sequence resyncs in the same session
took 195 ms and 210 ms. The IDR-wait and damaged-first-keyframe explanations are
both falsified, and the session's worst gaps (359 ms, 352 ms) followed the
resyncs and tracked `codec_ms`, not the cycle.

Record: `../evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

Next diagnostic: `C3.L2c` — MediaCodec low-latency decode. `low_latency_enabled`
is false on `c2.realtek.video.avc.decoder` and `max_codec_ms` was 367. It changes
production client behavior; not yet authorized.

Open, not blocking: `slow_events_marked` emitted empty while
`slow_event_retained_marked` reports 30 of 64. See `docs/KNOWN_ISSUES.md`.
