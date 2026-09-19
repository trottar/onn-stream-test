---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: 41bbc6acd3534f79283e328596115a02c3acc296
---

# Current State

Section headings below are fixed by `tools/check_memory_health.py`. Do not
rename or duplicate them; the checker requires each exactly once.

## Active Objective

Phase C Linux continuation: establish a safe, backend-neutral adaptive decision
boundary for the validated Linux native game stream.

## Current Work Item

None authorized. `C3.L3` closed 2026-09-19; the next item is not yet chosen.

Start from `PHASE_C_CONTEXT.md`. It is the compact, self-sufficient Phase C
continuation brief and should not require reading the wider memory hierarchy.

`C3.L4` (automatic fast-down/slow-up controller) is **still blocked**. Its gate
is a focused gameplay acceptance observation, which neither `C3.L2a`, `C3.L2c`
nor `C3.L3` performed. Re-read the gate in
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` before assuming otherwise.

## Verified State

- C1 Linux profile/backend and C2 stream telemetry: COMPLETE / RUNTIME
  VALIDATED. Baseline in `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.
- `C3.L0` actuator boundary audit: COMPLETE. Map in
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.
- `C3.L1` / `C3.L1R1` Linux encoder-only actuator: COMPLETE / RUNTIME
  VALIDATED across two clean cycles. Lifecycle preserved both times: FEC,
  process audio, controller and emulator survived with zero errors and exactly
  one SSRC change per cycle.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`; `live_bitrate_reconfigure` is not available under the
  current architecture. Authorized for start-time profile selection, manual and
  loopback-only diagnostic changes, fallback and recovery, and `C3.L3`
  characterization. **Not** authorized for automatic adaptation during play.
  Record: `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.
- `C3.L2a` E1 evidence pass: COMPLETE, question not answered by it. The old
  decoder report's slow-event list was a 128-entry flat ring that had already
  evicted the cycle's row. Record:
  `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.
- `C3.L2b` decoder-report cycle retention: COMPLETE / RUNTIME VALIDATED. The
  recent buffer did not overflow (94 of 128) and the new
  `stream_discontinuities` and `first_idr_after_discontinuity` arrays were
  populated on first use. Record:
  `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.
- `C3.L2a` first-IDR acceptance: **ANSWERED**. SSRC change at 43,443 ms, first
  IDR accepted at 43,471 ms — 27 ms, AU complete, no FEC repair, no
  unrecoverable group. The two ordinary resyncs took 195 ms and 210 ms. The
  session's worst gaps, 359 ms and 352 ms, followed those resyncs and tracked
  `codec_ms`; nothing registered at the cycle. **The 287-318 ms figure from
  `C3.L1` / `C3.L1R1` was never actuator cost and must not be cited as such.**
  Record: `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.
- `C3.L2c` low-latency decode: **FALSIFIED / ROLLED BACK**, 2026-09-19.
  `low_latency_enabled` did flip true and per-frame decode improved sharply
  (`max_codec_ms` 107, best of eight same-day sessions; `spike_250_ms` zero,
  the only session with none), but `max_output_gap_ms` was 385 ms — second
  worst of the eight — and the user's gameplay report matched. Source restored
  to exact predecessor bytes. Do not retry the unconditional `KEY_LOW_LATENCY`
  request without new evidence. Records:
  `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
  `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.
- `C3.L3` Linux fixed-bitrate cycle: **COMPLETE / RUNTIME VALIDATED**. The
  Windows-only WGC implementation was ported to Linux by reusing the validated
  `C3.L1`/`C3.L1R1` encoder-only restart primitive. Ten trigger/finalize cycles
  across three runs at 5000/5500/6000 kbps, zero cycle-level
  FEC/audio/controller errors in every one. Record:
  `patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md`.
- `C3.L3` fixed-bitrate characterization: **COMPLETE**, three valid samples per
  bitrate. `decoder_max_output_gap_ms` by run — 5000 kbps 367/292/242 (band
  125 ms); 5500 kbps 219/584/335 (band 365 ms, includes the only session over
  400 ms recorded at any bitrate); **6000 kbps 331/291/307 (band 40 ms)**.
  6000 kbps is the most consistent of the three and never exceeded 331 ms.
  This is transport and decoder timing only — no perceptual quality was
  measured, and no bitrate is accepted as a fallback level on this data.
  Record: `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.
- D4 Games and D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.

Blocked or incomplete:

- `C3.L4` automatic fast-down/slow-up controller: **BLOCKED**. Gate is a
  focused gameplay acceptance observation, not the IDR question and not the
  `C3.L3` data;
- the recorded "request an immediate IDR" lead is **premise-corrected**: a
  fresh FFmpeg RTP stream already begins with in-band parameter sets and an
  IDR, so a late first IDR needs a cause before any remedy;
- `max_codec_ms` is falsified as a proxy for `max_output_gap_ms` (`C3.L2c`).
  Any future candidate justified by "it lowers decode time" must measure the
  gap directly before acceptance;
- the cause of a 385 ms output gap in a session with zero 250 ms codec spikes
  is unexplained. No work item opened;
- the Android receiver's resync and IDR-acceptance policy has not been
  re-audited since `C3.L0`;
- Linux host resource telemetry never starts; see `docs/KNOWN_ISSUES.md`.

## Next Action

Choose the next Phase C item. `C3.L3` needs no further runs.

Two open defects are recorded and neither blocks: `slow_events_marked` is
emitted as an empty array while `slow_event_retained_marked` reports 30 of 64,
and `tools/probe_c3_fixed_*_characterization.py --finalize` matched the wrong
decoder-session file once when run back to back after another bitrate's
finalize. Both are in `docs/KNOWN_ISSUES.md`.

`C3.L2c` remains closed as a falsified, rolled-back candidate. Do not reopen it
without new evidence.

## Success Criteria

The next item is chosen against the pre-registered decision boundary in
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, with raw measurements kept
visible and whole-session qualifications preserved:

- decoder output gap reproducibly at or below ~120 ms with lifecycle preserved
  — reopen the automatic-adaptation question, with a focused gameplay
  observation required before acceptance;
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
  insufficient.
- `C3.L2c`'s unconditional `KEY_LOW_LATENCY` request.

## Relevant References

- `PHASE_C_CONTEXT.md` — **start here**; compact Phase C continuation brief.
- `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md` — all
  three characterization runs and the corrected three-run reading.
- `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md` — the
  falsification, measured against seven same-day baseline sessions.
- `patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md` — the Linux port of the
  fixed-bitrate cycle.
- `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md` — the `C3.L2c` install and
  revert.
- `patches/C3-L3R1_CHARACTERIZATION_CORRECTION.md` — the memory correction that
  added the omitted 6000 kbps rerun.
- `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — classification and the
  pre-registered boundary.
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — actuator boundary map.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture and history.
- `architecture/STREAM_TELEMETRY.md` — C2 measurement contract.
- `roadmap/STATUS.md` — roadmap position.
- `MAINTENANCE.md` — memory maintenance policy and required validation gate.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
