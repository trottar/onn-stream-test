---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: e347ed6b7055ef78d9620fe8970fb231c22c0820
durable_memory_updated: true
---

# C3-L3A-P1R1 — ladder transition runtime evidence

## Purpose

Record the runtime result that promotes `C3.L3a` Part 1 from development
patch to COMPLETE / RUNTIME VALIDATED, and correct a stale Next Action that
survived the Part 1 patch.

Durable memory only. No source change.

## Expected predecessor

`e347ed6b7055ef78d9620fe8970fb231c22c0820`

## Result recorded

The gate specified by `C3-L3A-P1` ran and passed:
`7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000`.

Host: every transition `ok`, `from_bitrate_kbps` chaining exactly, zero
FEC/audio/controller deltas, spawn spread 0.45 ms across five restarts, ending
at reference. Client: `ssrc_changes` 6, all six discontinuities typed
`ssrc_change` with `jump_packets` 0, first IDRs at 18/24/24/29/30/65 ms, all
complete and unrepaired.

Upward transitions and 7000-as-target both work — neither had ever run on
Linux and both were impossible under the `C3.L3` precondition.

`C3.L2a`'s answer moves from one observation to seven.

## Changed scope

Added:

- `docs/memory/evidence/C3_L3A_P1_LADDER_TRANSITION_RUNTIME_2026-09-19.md`;
- this record.

Replaced:

- `docs/memory/CURRENT.md` — Part 1 promoted; Next Action rewritten; Success
  Criteria rewritten; trimmed back under both soft limits;
- `docs/memory/investigations/ACTIVE.md` — gate marked passed with figures;
- `docs/memory/roadmap/STATUS.md` — state and a result section;
- `docs/memory/MEMORY.md` — durable-fact block for chained ladder transitions;
- `docs/memory/2026-09-19.md` — dated record.

Generated: `docs/memory/patches/PATCH_INDEX.md`.

Unchanged: all source, all tools, the `C3.L2` classification, the `C3.L4`
gate and its definition, every evidence file.

## A stale Next Action the Part 1 patch missed

`CURRENT.md`'s Next Action still described the superseded build plan — a
`ladder_transition` flag, a new Linux-only dispatch method, a new loopback
route, and a five-file scope. None of that shipped, because the seam already
existed. `C3-L3A-P1` updated the Current Work Item and the Success Criteria
and left the Next Action alone.

That is the third instance this session of a section being updated while a
neighbouring one carrying the same claim was not. It is now rewritten to the
actual Part 2 scope: two new tools files, no companion source change expected.

## Negative results

- **Part 1 advances the `C3.L4` gate not at all.** No perceptual quantity was
  measured, nobody judged the picture, no marks were taken. Recorded in three
  places because the temptation to read a clean mechanism result as progress
  toward acceptance is exactly what `C3.L2c` punished.
- **The walk session's 440 ms worst gap is unattributed.** Six ordinary
  sequence resyncs occurred alongside the six transitions and the slow-event
  rows were not correlated against the discontinuity list. Not pursued.
- **Direction is confounded with ordering.** The two downward transitions
  resumed at ~427.9 ms and the three upward at ~417.8 ms, but the downward
  pair were also the first two executed. Part 2 randomizes order and can
  separate it.
- **Two of the three reused guards are still source-verified only.**
  `validated_transition_requires_validated_start` and
  `unsupported_validated_bitrate` are unreachable over HTTP because the route
  allowlist and the Linux ladder are now the same set.
- **Transport conditions today are worse than during `C3.L3`** — 1,089-2,462
  lost packets per session against 2-425 yesterday. Gap figures must not be
  compared across the two days, and Part 2 runs should record conditions.
- **`CURRENT.md` needed four rounds of trimming to stay under 10 KB.** It is
  carrying a full state history that `investigations/ACTIVE.md` now holds
  authoritatively. Moving the settled `Verified State` entries there is worth
  doing as its own item; it was not done here, under a patch deadline, on
  purpose.

## Validation performed

- installer Python compile;
- payload and installed SHA-256 per file, wrong-state rejection before
  modification;
- every figure re-derived from the raw artifacts — the ladder walk log, the
  native video host log, and the decoder session JSON — not transcribed from
  the conversation;
- generated index regenerated and verified after writing;
- LF line endings and trailing newline on every written file;
- `tools/check_memory_health.py` post-write gate with exact-byte rollback;
- `CURRENT.md` re-measured at 10,212 B / 195 lines, `MEMORY.md` at 21,140 B,
  both inside their soft limits;
- ZIP integrity.

**Deliberately not performed:** no self-test, no fixture, no sandbox install.
Tier 1.

No runtime validation applies to this patch itself; it records one.

## Privacy

No network addresses appear in this patch or in any file it writes.

## Result

Recorded on install.
