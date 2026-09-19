# Roadmap Status

As of 2026-09-18, baseline `e220d3e39c896bac89bc8d286279b480cba50669`.

## Active

Phase C Linux continuation.

Active work item: `C3.L2c` — low-latency decode candidate (needs authorization).
`C3.L2b` code is installed; the actuator cycle against the rebuilt client has
not yet been run.

## Completed

- Phase A — games/emulator subsystem.
- Phase B — diagnostics and clean native baseline.
- D1-D5 — Linux migration through media/server restoration.
  - D4 Games: COMPLETE / RUNTIME VALIDATED.
  - D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.
- C1 Linux profile/backend: COMPLETE / RUNTIME VALIDATED.
- C2 stream telemetry: COMPLETE / RUNTIME VALIDATED.
- `C3.L0` Linux actuator boundary audit: COMPLETE (source audit only).
- `C3.L1` / `C3.L1R1` Linux encoder-only actuator: COMPLETE / RUNTIME
  VALIDATED. Interruption 287-318 ms decoder output gap, not established as
  actuator cost — see `C3.L2a` E1.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`, authorized for start-time, manual, fallback and
  characterization use; not authorized for automatic in-game adaptation.
- `C3.L2a` E1 evidence pass: COMPLETE. The question is not answered and the
  reason is a diagnostic retention defect.
- `C3.L2b` decoder-report cycle retention: **CODE INSTALLED**, not yet
  runtime validated. See `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.

## Phase C Linux sequence

| Item | State |
| --- | --- |
| `C3.L0` actuator boundary audit | COMPLETE |
| `C3.L1` encoder-only restart continuity probe | COMPLETE / RUNTIME VALIDATED |
| `C3.L2` Linux actuator capability classification | COMPLETE |
| `C3.L2a` first-IDR acceptance investigation | **ANSWERED**; IDR wait falsified |
| `C3.L2b` decoder-report cycle retention | COMPLETE / RUNTIME VALIDATED |
| `C3.L2c` low-latency decode candidate | **NEXT**; needs authorization first |
| `C3.L3` Linux fixed-bitrate envelope revalidation | UNBLOCKED for manual characterization; sequenced after `C3.L2a` closes |
| `C3.L4` explainable fast-down/slow-up controller | BLOCKED; gate is `C3.L2a` |
| C4 adaptive FEC | DEFERRED |

## Historical / reassigned

- D6 UDP replay: history preserved; active ownership moved into Phase C
  transport validation. Not an active Phase D task.
- Windows-era C3 (D-063 through D-071): closed; authoritative as history only.
  The Windows 5500/6000/7000 ladder is evidence, not a Linux constant.

## Gated

Phase E resource characterization does not begin until the streaming
architecture is stable, diagnostics are mature, source/capture boundaries are
settled, transport behavior is understood, and runtime shaping is complete or
bounded.

Phase E answers how much hardware the finalized architecture requires, not how
much a partially completed architecture requires.

## After Phase C

Remaining D baseline checkpoints, then Phase E.

## C3.L2a result — 2026-09-18

The actuator's first IDR is accepted 27 ms after the SSRC change, complete and
unrepaired, against 195 ms and 210 ms for ordinary sequence resyncs. The IDR
wait is falsified and 287-318 ms is not actuator cost. Decoder time is now the
largest measured contributor to perceptible interruption. Record:
`evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.
