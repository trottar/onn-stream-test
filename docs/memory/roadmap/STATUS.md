# Roadmap Status

As of 2026-09-19, baseline `41bbc6acd3534f79283e328596115a02c3acc296`.

## Active

Phase C Linux continuation.

Active work item: **`C3.L3a`** — gameplay acceptance probe. REGISTERED / NEXT,
design complete 2026-09-19, build not yet authorized. It is the `C3.L4` gate
made performable: diagnostic-only, authorizes nothing. Scope in
`investigations/ACTIVE.md`; design in `architecture/ADAPTIVE_BITRATE.md`; gate
definition in `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.

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
  VALIDATED. The 287-318 ms figure recorded there is **not** actuator cost —
  falsified by `C3.L2a` E2.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`, authorized for start-time, manual, fallback and
  characterization use; not authorized for automatic in-game adaptation.
- `C3.L2a` first-IDR acceptance: **ANSWERED**; the IDR wait is falsified.
- `C3.L2b` decoder-report cycle retention: COMPLETE / RUNTIME VALIDATED.
- `C3.L2c` low-latency decode candidate: **FALSIFIED / ROLLED BACK**.
- `C3.L3` Linux fixed-bitrate port and characterization: COMPLETE / RUNTIME
  VALIDATED; three valid samples per bitrate.

## Phase C Linux sequence

| Item | State |
| --- | --- |
| `C3.L0` actuator boundary audit | COMPLETE |
| `C3.L1` encoder-only restart continuity probe | COMPLETE / RUNTIME VALIDATED |
| `C3.L2` Linux actuator capability classification | COMPLETE |
| `C3.L2a` first-IDR acceptance investigation | **ANSWERED**; IDR wait falsified |
| `C3.L2b` decoder-report cycle retention | COMPLETE / RUNTIME VALIDATED |
| `C3.L2c` low-latency decode candidate | **FALSIFIED / ROLLED BACK** |
| `C3.L3` Linux fixed-bitrate envelope characterization | COMPLETE / RUNTIME VALIDATED |
| `C3.L3a` gameplay acceptance probe | Part 1 **COMPLETE / RUNTIME VALIDATED**; Part 2 next. This is the `C3.L4` gate |
| `C3.L4` explainable fast-down/slow-up controller | **BLOCKED**; gate is `C3.L3a` |
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
wait is falsified and 287-318 ms is not actuator cost. Record:
`evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.

## C3.L2c result — 2026-09-19

Requesting `KEY_LOW_LATENCY` unconditionally cut `max_codec_ms` to 107 ms, the
best of eight same-day sessions, and eliminated 250 ms codec spikes entirely —
while `max_output_gap_ms` came out at 385 ms, the second worst of the eight.
Falsified and rolled back to exact predecessor bytes. `max_codec_ms` is not a
valid proxy for `max_output_gap_ms`. Record:
`evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`.

## C3.L3 result — 2026-09-19

The Linux fixed-bitrate cycle is ported and runtime validated: ten
trigger/finalize cycles across three runs at 5000/5500/6000 kbps, zero
cycle-level FEC/audio/controller errors in every one.

Characterization, `decoder_max_output_gap_ms` over three valid samples each:

| bitrate | run 1 | run 2 | run 3 | band |
| --- | ---: | ---: | ---: | --- |
| 5000 kbps | 367 | 292 | 242 | 242-367 (125 ms) |
| 5500 kbps | 219 | 584 | 335 | 219-584 (365 ms) |
| 6000 kbps | 331 | 291 | 307 | **291-331 (40 ms)** |

6000 kbps is the most consistent and never exceeded 331 ms. This is transport
and decoder timing only — no perceptual quality was measured, and **no bitrate
is accepted as a fallback level on this data**. Record:
`evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.

`C3.L4` remains blocked. Its gate is `C3.L3a`, a gameplay acceptance
observation; nothing in `C3.L2a`, `C3.L2c` or `C3.L3` performed one, and none
of them could have — all three measure transport and decoder timing, and
`C3.L2c` is the standing proof that timing and perception come apart.

## C3.L3a Part 1 result — 2026-09-19

Chained ladder transitions work on Linux. Six in one session,
`7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000`, every one clean on
both host and client, ending at reference. Upward transitions and
7000-as-target had never run on Linux and were impossible before the port.

Client first-IDR acceptance across the six: **18-65 ms**, all complete, none
FEC-repaired. With `C3.L2a` E2's 27 ms that is seven observations against
195-332 ms for ordinary sequence resyncs. Record:
`evidence/C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md`.

Part 2 — the gameplay acceptance probe — is the `C3.L4` gate and is next.
Part 1 advances that gate not at all; nothing perceptual was measured.

## Decision-record correction — 2026-09-19

`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` had not been updated since
it was written and was reasoning from the falsified 287-318 ms figure. Reason 1
is struck, reason 2 restated without a magnitude, the consequences table
refreshed, and the `C3.L4` gate given a definition that can actually be
satisfied. The classification itself is unchanged: `video_only_restart`,
manual use authorized, automatic use not. Record:
`patches/C3-L3R2_GATE_DEFINITION_AND_DECISION_SYNC.md`.
