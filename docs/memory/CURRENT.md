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

`C3.L3a` — gameplay acceptance probe. **Part 1 COMPLETE / RUNTIME VALIDATED.
Part 2 next, not yet built.**

Start from `PHASE_C_CONTEXT.md`. It is the compact, self-sufficient Phase C
continuation brief and should not require reading the wider memory hierarchy.

**Part 1 (`C3-L3A-P1`) passed its gate 2026-09-19.** The six-transition round
trip `7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000` ran clean: every
transition `ok`, `from_bitrate_kbps` chaining exactly, zero
FEC/audio/controller deltas, ending at reference. The client recorded
`ssrc_changes` 6 with all six discontinuities typed `ssrc_change`,
`jump_packets` 0, and first IDRs accepted in **18-65 ms**, all complete and
unrepaired. Upward transitions and 7000-as-target both work — neither had
ever run on Linux. Record:
`evidence/C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md`.

Mechanism: `architecture/ADAPTIVE_BITRATE.md`, section "C3.L3a design". No new
companion method and no new route were needed — both already existed and
dispatched to the Windows implementation unconditionally.

`C3.L3a` is the `C3.L4` gate made performable. Diagnostic-only; it authorizes
nothing and adds no controller logic. Required shape of the Part 2 session:
several transitions, fired at intervals the player does not know in advance,
a control interval that fires nothing, the player's marks compared against
`stream_discontinuities` `elapsed_ms` **after** the session, and time parked
at 5000/5500/6000 kbps so the picture itself can be judged. Jump and ramp
sequences are recorded separately and never pooled.

`C3.L4` stays **BLOCKED**, gate `C3.L3a`. A manual cycle with a subjective read
does not satisfy it — that was done on 2026-09-18 and ruled insufficient — and
neither does transport/decoder timing at any sample size. Full gate definition:
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, section "The `C3.L4` gate,
stated so it can be satisfied".

## Verified State

- C1 profile/backend, C2 telemetry: COMPLETE / RUNTIME VALIDATED.
  `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.
- `C3.L0` boundary audit: COMPLETE.
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.
- `C3.L1` / `C3.L1R1` encoder-only actuator: COMPLETE / RUNTIME VALIDATED,
  two clean cycles, lifecycle preserved, one SSRC change each.
- `C3.L2` classification: COMPLETE. Linux is `video_only_restart`;
  `live_bitrate_reconfigure` is unavailable under the current architecture.
  Authorized for start-time, manual/loopback, fallback-recovery and
  characterization use. **Not** authorized for automatic adaptation during
  play. Reason 1 of that record is falsified; it stands on reasons 2-4.
  `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.
- `C3.L2a` E1: COMPLETE, question not answered by it — the old 128-entry ring
  had evicted the cycle's row.
  `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.
- `C3.L2b` decoder-report cycle retention: COMPLETE / RUNTIME VALIDATED.
  `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.
- `C3.L2a` first-IDR acceptance: **ANSWERED**, and since reinforced to seven
  observations by `C3.L3a` Part 1. The actuator's first IDR is accepted in
  18-65 ms, complete and unrepaired, against 195-332 ms for ordinary sequence
  resyncs. **The 287-318 ms figure from `C3.L1` / `C3.L1R1` was never actuator
  cost and must not be cited as such.** Records:
  `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`,
  `evidence/C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md`.
- `C3.L2c` low-latency decode: **FALSIFIED / ROLLED BACK**, 2026-09-19.
  `max_codec_ms` 107 (best of eight same-day sessions, `spike_250_ms` zero)
  but `max_output_gap_ms` 385 ms, second worst, and the gameplay report
  matched. Source restored to exact predecessor bytes. Do not retry the
  unconditional `KEY_LOW_LATENCY` request without new evidence. Records:
  `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
  `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.
- `C3.L3` fixed-bitrate cycle: **COMPLETE / RUNTIME VALIDATED**. Ten
  trigger/finalize cycles across three runs, zero cycle-level errors.
  `patches/C3-L3_LINUX_FIXED_BITRATE_PORT.md`.
- `C3.L3` fixed-bitrate characterization: **COMPLETE**, three valid samples
  per bitrate. `decoder_max_output_gap_ms` bands — 5000 kbps 242-367 (125 ms);
  5500 kbps 219-584 (365 ms, the only session over 400 ms at any bitrate);
  **6000 kbps 291-331 (40 ms)**, the most consistent, never over 331 ms.
  Transport and decoder timing only — no perceptual quality was measured and
  no bitrate is accepted as a fallback level on this data. Record:
  `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`.
- D4 Games and D5 media/server restoration: COMPLETE / RUNTIME VALIDATED.

Blocked or incomplete:

- `C3.L4` automatic fast-down/slow-up controller: **BLOCKED**. Gate is
  `C3.L3a`, not the IDR question and not the `C3.L3` data;
- **no perceptual quantity has been measured anywhere in Phase C.** Every
  figure on record is transport or decoder timing;
- the "request an immediate IDR" lead is **premise-corrected and now moot**:
  a fresh FFmpeg RTP stream already begins with parameter sets and an IDR, and
  seven measured transitions accept it in 18-65 ms;
- `max_codec_ms` is falsified as a proxy for `max_output_gap_ms` (`C3.L2c`).
  Any future candidate justified by "it lowers decode time" must measure the
  gap directly before acceptance;
- a 385 ms gap in a session with zero 250 ms codec spikes is unexplained; no
  work item owns it;
- the Android receiver's resync/IDR policy is un-audited since `C3.L0`;
- Linux host resource telemetry never starts; see `docs/KNOWN_ISSUES.md`.

## Next Action

Build `C3.L3a` Part 2: the new `tools/probe_c3_l3a_gameplay_acceptance.py`
and a new shared `tools/manual_checkout.py`. Tools only — Part 1 supplied the
companion primitive and is runtime validated, so **no companion source change
is expected**. Existing checkout probes are not touched; the shared module is
additive and only the new probe uses it. Session design is settled and
recorded below. `C3.L3` needs no further runs.

This supersedes the earlier build plan, which named a `ladder_transition`
flag, a new dispatch method and a new route. None of those shipped: the seam
already existed. See `architecture/ADAPTIVE_BITRATE.md`.

**Record current transport conditions in any Part 2 run.** The host is in a
worse state today than during `C3.L3`: 1,089-2,462 lost packets per session,
0-5 unrecoverable FEC groups, and one actuator-free session at a 1,271 ms
worst gap, against `C3.L3`'s 2-425 lost and 219-584 ms yesterday. Do not
compare gap figures across the two days.

Two open defects are recorded and neither blocks: `slow_events_marked` is
emitted as an empty array while `slow_event_retained_marked` reports 30 of 64,
and `tools/probe_c3_fixed_*_characterization.py --finalize` matched the wrong
decoder-session file once when run back to back after another bitrate's
finalize. Both are in `docs/KNOWN_ISSUES.md`.

`C3.L2c` remains closed as a falsified, rolled-back candidate. Do not reopen it
without new evidence.

## Success Criteria

`C3.L3a` Part 1 was accepted 2026-09-19: the six-chained-transition round
trip ran clean on both host and client, lifecycle preserved throughout, ending
at 7000.

Part 2 is accepted when a session produces a readable contingency table —
marks against real sequences, decoys and neither — plus a picture judgment at
each destination bitrate. **The probe encodes no threshold.** Whether the gate
is met is the user's call on that table, not the probe's.

The `C3.L2a` pre-registered gap boundary (<=120 ms / 120-250 ms / unchanged)
is **spent**: the run landed outside all three branches because the gap was
never the actuator's. Do not reason from it. The live criterion is the
`C3.L4` gate in `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, section
"The `C3.L4` gate, stated so it can be satisfied", which `C3.L3a` Part 2
performs.

Do not change during C3: resolution, frame rate, GOP, B-frames, FEC wire
format, RTP payload type, packet size, ports, process audio, controller
transport, emulator lifecycle, Android streaming constants, or any
non-loopback control surface.

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
- `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — classification, the
  falsified-premise correction, and the `C3.L4` gate definition.
- `investigations/ACTIVE.md` — current sub-item states and `C3.L3a` scope.
- `architecture/ADAPTIVE_BITRATE.md` — adaptation architecture, the
  fast-down/slow-up rule, and the `C3.L3a` design.
- `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md` — all
  three characterization runs.
- `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md` — the
  falsification against seven same-day baseline sessions.
- `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md` — the 27 ms
  actuator IDR.
- `patches/PATCH_INDEX.md` — every patch record.
- `roadmap/STATUS.md` — roadmap position.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
