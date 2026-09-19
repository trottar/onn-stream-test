---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# Current State

Section headings below are fixed by `tools/check_memory_health.py`. Do not
rename or duplicate them; the checker requires each exactly once.

## Active Objective

Phase C Linux continuation: establish a safe, backend-neutral adaptive decision
boundary for the validated Linux native game stream.

## Current Work Item

`C3.L2a` — first-IDR acceptance investigation.

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
- `C3.L2a` E1 evidence pass: COMPLETE, question **not** answered. The decoder
  report's slow-event list is a 128-entry ring that had already evicted the
  cycle's row. In ordinary play with no actuator, output gap tracks codec time
  one-to-one and reaches 238 ms, so the cycle's 287 ms is not established as
  actuator cost. Record:
  `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.
- D4 Games and D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.

Blocked or incomplete:

- the automatic fast-down/slow-up controller (`C3.L4`) is **blocked**; its gate
  is the `C3.L2a` result;
- `C3.L3` Linux fixed-bitrate envelope revalidation is unblocked for manual
  characterization but is sequenced after `C3.L2a`;
- the recorded "request an immediate IDR" lead is **premise-corrected**: a fresh
  FFmpeg RTP stream already begins with in-band parameter sets and an IDR, so
  the late first IDR needs a cause before any remedy;
- the cycle's interruption cost is **not separable** from the client's own
  decoder-spike baseline with the current instrumentation;
- the Android receiver's resync and IDR-acceptance policy has not been
  re-audited since `C3.L0`;
- `low_latency_enabled` is false on `c2.realtek.video.avc.decoder`; a separate
  candidate with its own hypothesis, **not authorized** and not to be folded
  into diagnostics work;
- Linux host resource telemetry never starts; see `docs/KNOWN_ISSUES.md`.

## Next Action

Patch the Android decoder session report so an actuator cycle survives into the
evidence, then re-run the continuity probe.

The report must gain marked-window retention or a segmented slow-event buffer,
`elapsed_ms` anchors for the SSRC change and sequence resyncs, and per-event IDR
context for the first accepted IDR after an SSRC change. Diagnostic-only client
work: it changes the report, not decoder configuration or any streaming
constant. It needs a real Gradle build and its own patch.

Do not re-run `tools/probe_c3_actuator_continuity.py` first. The E1 pass
established that the existing report discards the cycle's row, so an unchanged
re-run cannot answer the question.

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

## Relevant References

- `PHASE_C_CONTEXT.md` — **start here**; compact Phase C continuation brief.
- `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — classification and the
  pre-registered `C3.L2a` boundary.
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — actuator boundary map.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and history.
- `architecture/STREAM_TELEMETRY.md` — C2 measurement contract.
- `evidence/C3_L1R1_LINUX_ACTUATOR_RUNTIME_2026-09-18.md` — corrected run.
- `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md` — E1 evidence pass
  and the retention defect that blocks `C3.L2a`.
- `roadmap/STATUS.md` — roadmap position.
- `MAINTENANCE.md` — memory maintenance policy and required validation gate.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
