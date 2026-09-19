---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: e1c37768718030af7266e2d37dad5473166e2987
durable_memory_updated: true
---

# C3.L2a E1 — first-IDR evidence pass

## Purpose

Record the first `C3.L2a` evidence pass over the `C3.L1R1` session bundle: the
question is not answered, the reason is a diagnostic retention defect, and the
pass found that the actuator's interruption cost is not separable from the
client's own decoder-spike baseline.

Durable memory only. No production source change, no probe change, no tool
change, no new runtime run.

## Expected predecessor

`e1c37768718030af7266e2d37dad5473166e2987`

This patch stacks on `C3.L2` and on `MEM-TOOLS`; both must be installed.
Predecessor identity is enforced by per-file SHA-256, not by the commit hash.

## Changed scope

Added:

- `docs/memory/evidence/C3_L2A_E1_DECODER_EVIDENCE_PASS_2026-09-18.md`;
- `docs/memory/patches/C3-L2A-E1_FIRST_IDR_EVIDENCE_PASS.md` — this record.

Replaced:

- `docs/memory/CURRENT.md` — next action becomes the instrumentation patch;
- `docs/memory/PHASE_C_CONTEXT.md` — section 6 carries the E1 result;
- `docs/memory/MEMORY.md` — durable retention and baseline facts;
- `docs/memory/LEARNINGS.md` — two generalized lessons;
- `docs/memory/2026-09-18.md` — dated chronology;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — E1 section;
- `docs/KNOWN_ISSUES.md` — three open diagnostic findings.

Generated and validated: `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

All companion and Android production source, all probes and tools, `.gitignore`,
`AGENTS.md`, `MAINTENANCE.md`, `TOOLS.md`, `roadmap/STATUS.md`,
`investigations/ACTIVE.md`, `handoffs/CURRENT_HANDOFF.md`, the `C3.L2` decision
record, and every earlier evidence record.

`roadmap/STATUS.md` is deliberately untouched: `C3.L2a` was already the active
item and still is.

## Result recorded

The `C3.L2a` question is not answered. The decoder session report's slow-event
list is a 128-entry ring which, in the `C3.L1R1` session, was full and retained
only elapsed 35,421-64,813 ms of a 64,842 ms session, so the row explaining
`max_output_gap_ms` 287 was evicted before the report was written.

What the retained window does establish: in ordinary play with no actuator
activity, `output_gap_ms` tracks `codec_ms` one-to-one — 238/247, 200/211,
133/142 — with feed delay near zero and an empty app queue. Against a baseline
that reaches 238 ms unaided, the cycle's 287 ms is either ~50 ms of attributable
cost or not separately visible.

`C3.L2` stands. Its conservatism is what makes this cheap to revisit.

## Negative results recorded by this work item

- The narrow question was not answered, and no re-run is requested, because the
  existing probe would lose the same row again.
- Two `C3.L1` / `C3.L1R1` framings are further qualified: 287-318 ms is not
  established as actuator cost, and the one-GOP reasoning understated its own
  worst case, since `max_frames_between_idr` is 27 against GOP 15.
- The encoder swap is not visible in the host log's retained 500-line tail. That
  is recorded as an open question for the probe source, not as a claim that no
  swap occurred.
- The Android receiver's resync and IDR-acceptance policy still has not been
  re-audited. Recorded again rather than quietly dropped.
- No production defect was found. Everything here is diagnostic-only.

## Validation performed

- installer Python compile;
- installer self-test against a fixture built from the current installed bytes:
  wrong-state rejection before modification with a byte-identical snapshot,
  clean install, installed-hash verification, generated-index correctness and
  exclusions, idempotent reinstall, memory-health gate failure forcing rollback,
  forced-validation rollback restoring exact predecessor bytes and removing
  added files;
- `CURRENT.md` heading structure asserted: all seven required headings present
  exactly once;
- every figure in the evidence record re-derived from the supplied bundle by
  parsing its decoder JSON, not transcribed by hand;
- `tools/check_memory_health.py` executed as a post-write gate;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
