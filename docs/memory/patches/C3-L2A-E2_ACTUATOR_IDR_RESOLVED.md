---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e92bc42988f744191ae1321b05aaa04663222209
durable_memory_updated: true
---

# C3.L2a E2 — actuator IDR resolved

## Purpose

Record the runtime result that closes `C3.L2a` and move the active item to
`C3.L2c`. `C3.L2b` shipped the instrumentation; one cycle against it produced
the measurement, and the measurement falsifies the explanation three prior
records were built on.

Durable memory only. No source change, no probe change, no new tool.

## Expected predecessor

`e92bc42988f744191ae1321b05aaa04663222209`

Per-file SHA-256 is enforced by the installer.

## Changed scope

Added:

- `docs/memory/evidence/C3_L2A_E2_ACTUATOR_IDR_RESOLVED_2026-09-18.md`;
- this record.

Replaced:

- `docs/memory/CURRENT.md` — work item advances to `C3.L2c`;
- `docs/memory/PHASE_C_CONTEXT.md` — section 6 becomes the answer;
- `docs/memory/MEMORY.md` — durable fact;
- `docs/memory/2026-09-18.md` — dated record;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md`;
- `docs/memory/investigations/ACTIVE.md`;
- `docs/memory/handoffs/CURRENT_HANDOFF.md`;
- `docs/memory/roadmap/STATUS.md`;
- `docs/KNOWN_ISSUES.md` — the `slow_events_marked` defect and the decoder-time
  finding.

Generated: `docs/memory/patches/PATCH_INDEX.md`.

## Result recorded

The actuator's first IDR after the SSRC change was accepted in **27 ms**,
access unit complete, no FEC repair, no unrecoverable group. The two ordinary
sequence resyncs in the same session took 195 ms and 210 ms.

The session's worst output gaps — 359 ms and 352 ms — followed those resyncs and
tracked `codec_ms` to within 8 ms with feed delay at zero. Nothing registered at
the cycle.

`C3.L2a`: ANSWERED. `C3.L2b`: COMPLETE / RUNTIME VALIDATED. `C3.L2c`: NEXT,
pending authorization.

## Negative results

- The IDR-wait explanation is falsified. It was carried through `C3.L1`,
  `C3.L1R1` and the `C3.L2` registration of `C3.L2a`, and all three reasoned
  from a whole-session maximum that belonged to a different event.
- The damaged-first-keyframe candidate is falsified for this cycle.
- `C3.L2b` shipped with a reporting defect exposed by its own first use:
  `slow_events_marked` emitted empty while `slow_event_retained_marked` reports
  30 of 64. Recorded, not fixed here.
- This session is not like-for-like with `C3.L1R1` — 530 lost packets and 38
  sequence-gap AU drops against zero unrecoverable FEC groups. Stated so a later
  reader does not compare them directly.
- `C3.L2` is **not** reopened. One cycle removes a mechanism; it does not
  authorize automatic adaptation.

## Validation performed

- installer Python compile;
- installer self-test against a fixture built from the current installed bytes:
  wrong-state rejection before modification with a byte-identical snapshot,
  clean install, installed-hash verification, generated-index correctness,
  idempotent reinstall, memory-health gate failure and forced validation failure
  each returning `ROLLED BACK` with exact predecessor bytes restored;
- `CURRENT.md` heading structure asserted: seven required headings, each once;
- cross-file agreement asserted: every active-state file names `C3.L2c`;
- every figure re-derived by parsing the decoder JSON in
  `logs/games/latest_game_diagnostic_bundle.txt`, not transcribed;
- `tools/check_memory_health.py` executed as a post-write gate;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved;
- ZIP integrity.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
