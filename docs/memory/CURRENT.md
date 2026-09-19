---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e220d3e39c896bac89bc8d286279b480cba50669
---

# Current State

Section headings below are fixed by `tools/check_memory_health.py`. Do not
rename or duplicate them; the checker requires each exactly once.

## Active Objective

Phase C Linux continuation: establish a safe, backend-neutral adaptive decision
boundary for the validated Linux native game stream.

## Current Work Item

`C3.L2c` — low-latency decode candidate.

`C3.L2b` is COMPLETE / RUNTIME VALIDATED and `C3.L2a` is ANSWERED. The actuator's
first IDR after the SSRC change was accepted in **27 ms**, complete, with no FEC
repair — against 195 ms and 210 ms for the two ordinary sequence resyncs in the
same session. The IDR-wait explanation is falsified.

Record: `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

Start from `PHASE_C_CONTEXT.md`. It is the compact, self-sufficient Phase C
continuation brief and should not require reading the wider memory hierarchy.

## Verified State

- C1 Linux profile/backend and C2 stream telemetry: COMPLETE / RUNTIME
  VALIDATED. Baseline measurements in
  `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.
- `C3.L0` actuator boundary audit: COMPLETE. Map in
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.
- `C3.L1` / `C3.L1R1` Linux encoder-only actuator: COMPLETE / RUNTIME
  VALIDATED across two clean cycles. Lifecycle preserved both times: FEC,
  process audio, controller and emulator survived with zero errors and exactly
  one SSRC change per cycle.
- Interruption cost: **287-318 ms decoder output gap**, against Windows 791 ms
  on the directly comparable D-062 same-bitrate run. The `C3.L0` boundary is
  met.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`; `live_bitrate_reconfigure` is not available under the
  current architecture. Authorized for start-time profile selection, manual and
  loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
  characterization. Not authorized for automatic adaptation during play.
  Record: `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.
- `C3.L2a` E1 evidence pass: COMPLETE, question **not yet** answered. The old
  decoder report's slow-event list was a 128-entry flat ring that had already
  evicted the cycle's row. In ordinary play with no actuator, output gap
  tracked codec time one-to-one and reached 238 ms, so the cycle's 287 ms was
  not established as actuator cost. Record:
  `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.
- `C3.L2b` decoder-report cycle retention: **CODE INSTALLED**, this session.
  `AvcLowLatencyDecoder` now keeps a 64-entry marked segment (protected while
  a cycle window is open) alongside a 64-entry recent segment, instead of one
  flat 128-entry ring; `RtpH264Receiver` anchors every SSRC change and
  sequence resync in `elapsed_ms` and records per-event IDR context after
  each. Record: `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`. The three
  changed Kotlin files were compiled for real with the Kotlin compiler
  (`RtpH264Receiver.kt` standalone, no Android dependency;
  `AvcLowLatencyDecoder.kt` against hand-written Android API stubs; the
  `NativeStreamActivity.kt` report-building addition re-verified in an
  isolated harness against the real compiled types) — this is evidence the
  new code is not obviously broken, **not** a substitute for the installer's
  own `sh ./gradlew :app:assembleDebug --no-daemon` gate, which is the first
  real compile against the actual Android/Activity framework.
- `C3.L2b` decoder-report cycle retention: **COMPLETE / RUNTIME VALIDATED**.
  The recent buffer did not overflow (94 of 128) and the new
  `stream_discontinuities` and `first_idr_after_discontinuity` arrays were
  populated on first use.
- `C3.L2a` first-IDR acceptance: **ANSWERED**. SSRC change at 43,443 ms, first
  IDR accepted at 43,471 ms — 27 ms, AU complete, no FEC repair, no
  unrecoverable group. The two ordinary resyncs took 195 ms and 210 ms. The
  session's worst gaps, 359 ms and 352 ms, followed those resyncs and tracked
  `codec_ms`; nothing registered at the cycle. Record: `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.
- D4 Games and D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.

Blocked or incomplete:

- the automatic fast-down/slow-up controller (`C3.L4`) is **blocked**; its gate
  is the `C3.L2a` result;
- `C3.L3` Linux fixed-bitrate envelope revalidation is unblocked for manual
  characterization but is sequenced after `C3.L2a`;
- the recorded "request an immediate IDR" lead is **premise-corrected**: a fresh
  FFmpeg RTP stream already begins with in-band parameter sets and an IDR, so
  the late first IDR needs a cause before any remedy;
- the cycle's interruption cost is **still not separated** from the client's
  own decoder-spike baseline — `C3.L2b` removed the instrumentation defect
  that blocked the measurement, it did not perform the measurement;
- the Android receiver's resync and IDR-acceptance policy has not been
  re-audited since `C3.L0`;
- `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`; a separate
  candidate with its own hypothesis, **not authorized** and not to be folded
  into diagnostics work;
- Linux host resource telemetry never starts; see `docs/KNOWN_ISSUES.md`.

## Next Action

Decide whether to authorize `C3.L2c`, then run it.

`low_latency_enabled` is **false** on `c2.realtek.video.avc.decoder` while
`max_codec_ms` was 367 in the last session and the two largest output gaps —
359 ms and 352 ms — tracked `codec_ms` to within 8 ms with feed delay at zero.
Decoder time on a single frame is now the largest measured contributor to
perceptible interruption, and it is larger than anything the actuator does.

`C3.L2c` enables MediaCodec low-latency mode. It changes production client
behavior, so it needs its own narrow hypothesis, its own focused gameplay
acceptance, and it must not be folded into unrelated work. It is **not yet
authorized**; authorizing it is the decision this item waits on.

Open and not blocking: `slow_events_marked` is emitted as an empty array while
`slow_event_retained_marked` reports 30 of 64. The marked window's rows are
counted and dropped. Recorded in `docs/KNOWN_ISSUES.md`.

## Success Criteria

The cause of the late first-IDR acceptance is identified from evidence, or the
candidate causes are narrowed to one that a single loopback-only probe can
discriminate. Raw measurements stay visible and the classification's whole-session
qualifications are preserved.

Decision boundary, pre-registered in
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`:

- decoder output gap reproducibly at or below ~120 ms with lifecycle preserved —
  reopen the automatic-adaptation question, with a focused gameplay observation
  required before acceptance;
- ~120-250 ms — the remaining cost is not first-IDR acceptance; the actuator
  stays non-automatic and the next question is pipeline re-establishment;
- unchanged, or lifecycle regressed — the lead is falsified and closed, and the
  next real item is the encoder-host architecture question.

Do not change during C3: resolution, frame rate, GOP, B-frames, FEC wire format,
RTP payload type, packet size, ports, process audio, controller transport,
emulator lifecycle, Android streaming constants, or any non-loopback control
surface.

## Do Not Reopen Without New Evidence

- D4 Games and D5 media/server restoration.
- The Windows-era C3 record (D-063, D-067, D-068, D-069, D-070, D-071).
- The deferred UDP burst/gap pathology, which is a Windows measurement awaiting
  representative Linux replay.
- The `C3.L2` classification itself, including the decision not to authorize
  automatic in-game adaptation at the currently measured cost.
- The `C3.L2b` code design itself (marked/recent segmentation, discontinuity
  and IDR-context bounded lists) without a runtime finding that it is
  insufficient — e.g. the 2000 ms cycle window proving too short, or a
  discontinuity/IDR-context list overflowing its 64-entry capacity in a real
  session.

## Relevant References

- `PHASE_C_CONTEXT.md` — **start here**; compact Phase C continuation brief.
- `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md` — this session's
  installed patch: what changed in the report and why.
- `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — classification and the
  pre-registered `C3.L2a` boundary.
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — actuator boundary map.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and history.
- `architecture/STREAM_TELEMETRY.md` — C2 measurement contract.
- `evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` — corrected run.
- `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md` — E1 evidence pass
  and the retention defect `C3.L2b` addresses.
- `roadmap/STATUS.md` — roadmap position.
- `MAINTENANCE.md` — memory maintenance policy and required validation gate.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
