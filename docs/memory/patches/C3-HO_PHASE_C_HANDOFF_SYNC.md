---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 62b8b6014c23a7cd895d89d38b6f83e822aa6f31
durable_memory_updated: true
---

# C3.HO — Phase C handoff sync

## Purpose

Bring every active-state file into agreement after the `C3.L2a` E1 evidence
pass, register `C3.L2b` and `C3.L2c`, and leave a handoff note a fresh session
can resume from without reconstructing the argument.

The active files still named `C3.L2a` as the next thing to do. E1 established
that it cannot proceed until the decoder report retains the cycle, so following
that instruction would have produced a re-run that loses the same row again.

Durable memory only. No production source change, no probe change, no tool
change, no new evidence and no new claim.

## Expected predecessor

`62b8b6014c23a7cd895d89d38b6f83e822aa6f31`

Predecessor identity is enforced by per-file SHA-256.

## Changed scope

Replaced:

- `docs/memory/CURRENT.md` — work item advances to `C3.L2b`, `C3.L2c` recorded
  as unauthorized;
- `docs/memory/PHASE_C_CONTEXT.md` — sub-phase table, next item, E1 pointer;
- `docs/memory/roadmap/STATUS.md` — active item and Phase C sequence;
- `docs/memory/investigations/ACTIVE.md` — state and next diagnostic;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — `C3.L2b` and
  `C3.L2c` registration;
- `docs/memory/handoffs/CURRENT_HANDOFF.md` — rewritten as a real transfer note;
- `docs/memory/CURRENT_HANDOFF.md` — root pointer refreshed;
- `docs/memory/2026-09-18.md` — install results and this sync.

Added:

- `docs/memory/patches/C3-HO_PHASE_C_HANDOFF_SYNC.md` — this record.

Generated and validated: `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

All companion and Android production source, all probes and tools, `.gitignore`,
`AGENTS.md`, `MAINTENANCE.md`, `TOOLS.md`, `MEMORY.md`, `LEARNINGS.md`,
`docs/KNOWN_ISSUES.md`, the `C3.L2` decision record, and every evidence record.

No measurement, classification or authorization is restated or altered.

## State recorded

| Item | State |
| --- | --- |
| `C3.L2a` first-IDR acceptance | OPEN; blocked on `C3.L2b` |
| `C3.L2b` decoder-report cycle retention | **NEXT** |
| `C3.L2c` low-latency decode candidate | REGISTERED, NOT SCHEDULED, NOT AUTHORIZED |
| `C3.L3` fixed-bitrate envelope revalidation | UNBLOCKED for manual characterization; after `C3.L2a` closes |
| `C3.L4` fast-down/slow-up controller | BLOCKED; gate is `C3.L2a` |

The handoff note carries one correction forward in its own section, because it
is the finding most likely to be lost in a fresh session: **287-318 ms is not
established as the cost of the actuator**, since steady-state play in the same
session reached 238 ms output gaps with no actuator involved and the cycle's row
was evicted before the report was written. It also repeats the two corrected
framings — a fresh FFmpeg RTP stream already starts with parameter sets and an
IDR, and `max_frames_between_idr` 27 against GOP 15 makes the worst-case
keyframe wait ~450 ms.

## Install results recorded in the dated file

`C3.L2` (committed ahead of `e1c3776`), `MEM-TOOLS` (`e1c3776`) and
`C3.L2a E1` (`62b8b60`) each reported `INSTALLED SUCCESSFULLY` with the memory
health gate returning `healthy`. The `FAILED BEFORE MODIFICATION` and
`ROLLED BACK` lines in those transcripts are self-test negative paths, not
install failures, and the dated record says so explicitly.

## Negative results

- No new evidence was produced and none is claimed.
- `C3.L2a` is recorded as open and blocked rather than quietly re-scoped into
  `C3.L2b`. The question it asks is still unanswered.
- `C3.L2c` is registered as unauthorized rather than started, even though E1
  suggests it may be a larger lever on perceived smoothness than the actuator
  question. That judgement is the user's, and folding a production behavior
  change into a diagnostics patch is exactly the failure mode this workflow
  guards against.
- The `_patches/` and `_probes/` `.gitignore` coverage gap remains open and is
  still not fixed here.

## Validation performed

- installer Python compile;
- installer self-test against a fixture built from the current installed bytes:
  wrong-state rejection before modification with a byte-identical snapshot,
  clean install, installed-hash verification, generated-index correctness and
  exclusions, idempotent reinstall, memory-health gate failure forcing rollback,
  forced-validation rollback restoring exact predecessor bytes and removing the
  added file;
- `CURRENT.md` heading structure asserted: all seven required headings present
  exactly once;
- cross-file agreement asserted: no active-state file still names `C3.L2a` as
  the next item, and every one of them names `C3.L2b`;
- `tools/check_memory_health.py` executed as a post-write gate;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
