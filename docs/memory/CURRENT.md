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

`C3.L2b` — decoder-report cycle retention. **CODE INSTALLED; RUNTIME EVIDENCE
NOT YET COLLECTED.**

`docs/memory/patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md` installed the
segmented slow-event buffer, `elapsed_ms`-anchored discontinuity events and
per-event first-IDR-after-discontinuity context described there. The installer
ran a real `sh ./gradlew :app:assembleDebug --no-daemon`, but no APK has been
installed on the onn device and no actuator cycle has been run against the
rebuilt client yet. `C3.L2a` stays open until that cycle is run and its report
is read.

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

Install the rebuilt APK and produce the evidence `C3.L2b` was installed to
collect:

```bash
sh ./gradlew :app:assembleDebug --no-daemon
adb install -r PrivyHub/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop com.safeiot.privyhub
```

Then run one clean `C3.L1`-style encoder-only actuator cycle (trigger phase,
no flag; `--finalize` after a normal Back), and re-attempt the `C3.L2a`
evidence pass by reading the new decoder session report: check
`stream_discontinuities` for the SSRC change and resync `elapsed_ms`, check
`first_idr_after_discontinuity` for `resync_to_idr_ms` and whether the
accepted IDR's access unit was FEC-recovered or sat behind an unrecoverable
group, and confirm `slow_event_retained_marked` is nonzero and covers the
cycle's `elapsed_ms` window this time.

Do not re-run `tools/probe_c3_actuator_continuity.py` against the *old* APK;
it must be the rebuilt one, or the same eviction the `C3.L2a` E1 pass found
will recur.

`C3.L2c`, the low-latency decode candidate, is registered and **not
authorized**. It changes production client behavior and needs its own
hypothesis and its own focused gameplay acceptance. It was not folded into
`C3.L2b`.

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
