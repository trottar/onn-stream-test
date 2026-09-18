# Roadmap Status

As of 2026-09-18, baseline `6abe47d2f7adf1eae847d3b23b12b760586f6d41`.

## Active

Phase C Linux continuation.

Active work item: `C3.L2a` — first-IDR acceptance investigation.

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
  VALIDATED. Interruption 287-318 ms decoder output gap.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`, authorized for start-time, manual, fallback and
  characterization use; not authorized for automatic in-game adaptation.

## Phase C Linux sequence

| Item | State |
| --- | --- |
| `C3.L0` actuator boundary audit | COMPLETE |
| `C3.L1` encoder-only restart continuity probe | COMPLETE / RUNTIME VALIDATED |
| `C3.L2` Linux actuator capability classification | COMPLETE |
| `C3.L2a` first-IDR acceptance investigation | **NEXT** |
| `C3.L3` Linux fixed-bitrate envelope revalidation | UNBLOCKED for manual characterization; sequenced after `C3.L2a` |
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
