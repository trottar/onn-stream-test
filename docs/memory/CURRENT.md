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

`C3.L3a` — gameplay acceptance probe. **Part 1 INSTALLED, development only.
Part 2 not yet built.**

Start from `PHASE_C_CONTEXT.md`. It is the compact, self-sufficient Phase C
continuation brief and should not require reading the wider memory hierarchy.

**Part 1 (`C3-L3A-P1`) is installed and needs a runtime gate before Part 2.**
It ported the D-069 validated-ladder seam to Linux so several transitions can
run in one session. No new companion method and no new route were needed —
both already existed and simply dispatched to the Windows implementation
unconditionally. Mechanism:
`architecture/ADAPTIVE_BITRATE.md`, section "C3.L3a design".

Required gate before Part 2 is built — one manual round trip, chaining and
both directions, ending at reference:

    7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000

Six chained transitions. Chaining has never run on Linux and must not debut
inside a blinded gameplay session.

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

- C1 Linux profile/backend and C2 stream telemetry: COMPLETE / RUNTIME
  VALIDATED. Baseline in `evidence/C1_C2_LINUX_REVALIDATION_2026-09-18.md`.
- `C3.L0` actuator boundary audit: COMPLETE. Map in
  `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`.
- `C3.L1` / `C3.L1R1` Linux encoder-only actuator: COMPLETE / RUNTIME
  VALIDATED across two clean cycles, lifecycle preserved both times with zero
  FEC/audio/controller errors and one SSRC change per cycle.
- `C3.L2` Linux actuator classification: COMPLETE. Linux is
  `video_only_restart`; `live_bitrate_reconfigure` is unavailable under the
  current architecture. Authorized for start-time selection, manual and
  loopback-only changes, fallback/recovery and characterization. **Not**
  authorized for automatic adaptation during play. Reason 1 of that record is
  falsified; the decision stands on reasons 2-4. Record:
  `decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`.
- `C3.L2a` E1 evidence pass: COMPLETE, question not answered by it — the old
  128-entry flat ring had evicted the cycle's row. Record:
  `evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`.
- `C3.L2b` decoder-report cycle retention: COMPLETE / RUNTIME VALIDATED.
  `stream_discontinuities` and `first_idr_after_discontinuity` populated on
  first use. Record: `patches/C3-L2B_DECODER_REPORT_CYCLE_RETENTION.md`.
- `C3.L2a` first-IDR acceptance: **ANSWERED**. SSRC change at 43,443 ms, first
  IDR accepted at 43,471 ms — 27 ms, AU complete, no FEC repair, no
  unrecoverable group. The two ordinary resyncs took 195 ms and 210 ms. The
  session's worst gaps, 359 ms and 352 ms, followed those resyncs and tracked
  `codec_ms`; nothing registered at the cycle. **The 287-318 ms figure from
  `C3.L1` / `C3.L1R1` was never actuator cost and must not be cited as such.**
  Record: `evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`.
- `C3.L2c` low-latency decode: **FALSIFIED / ROLLED BACK**, 2026-09-19.
  `max_codec_ms` 107 (best of eight same-day sessions, `spike_250_ms` zero)
  but `max_output_gap_ms` 385 ms, second worst, and the gameplay report
  matched. Source restored to exact predecessor bytes. Do not retry the
  unconditional `KEY_LOW_LATENCY` request without new evidence. Records:
  `evidence/C3_L2C_LOW_LATENCY_DECODE_FALSIFIED_2026-09-19.md`,
  `patches/C3-L2C_LOW_LATENCY_DECODE_ENABLE.md`.
- `C3.L3` Linux fixed-bitrate cycle: **COMPLETE / RUNTIME VALIDATED**. Ported
  from the Windows-only WGC implementation by reusing the `C3.L1`/`C3.L1R1`
  encoder-only restart primitive. Ten trigger/finalize cycles across three
  runs, zero cycle-level errors in every one. Record:
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

The `C3.L3a` design is complete and presented; see
`architecture/ADAPTIVE_BITRATE.md`. Awaiting authorization to build it as a
Tier 1 patch touching `companion/diagnostics/c3_linux_actuator_probe.py`
(`ladder_transition` flag on the existing, unchanged-by-default cycle
function), `companion/native_stream.py` (one new Linux-only dispatch method),
`companion/plugins/games.py` (one new loopback-only route), a new shared
`tools/manual_checkout.py`, and the new
`tools/probe_c3_l3a_gameplay_acceptance.py`. `C3.L3` needs no further runs.

Two open defects are recorded and neither blocks: `slow_events_marked` is
emitted as an empty array while `slow_event_retained_marked` reports 30 of 64,
and `tools/probe_c3_fixed_*_characterization.py --finalize` matched the wrong
decoder-session file once when run back to back after another bitrate's
finalize. Both are in `docs/KNOWN_ISSUES.md`.

`C3.L2c` remains closed as a falsified, rolled-back candidate. Do not reopen it
without new evidence.

## Success Criteria

`C3.L3a` Part 1 is accepted when the six-chained-transition round trip above
runs clean — every transition returning `ok`, lifecycle preserved, and the
stream back at 7000 — and the `C3.L3` characterization path is confirmed
unchanged.

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
- `investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — actuator boundary map.
- `patches/PATCH_INDEX.md` — every patch record, including `C3-L3A-P1`.
- `roadmap/STATUS.md` — roadmap position.
- `docs/KNOWN_ISSUES.md` — open gaps and deferred work.
