---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
durable_memory_updated: true
---

# C3.L2 — Linux actuator capability classification

## Purpose

Record the `C3.L2` classification decision, correct two ways the `C3.L1` /
`C3.L1R1` figures were being read, register `C3.L2a` with a pre-registered
decision boundary, and bring the stale active-state files back into agreement
with it.

Durable memory only. No production source change, no new tool, no probe change,
no new runtime evidence.

## Expected predecessor

`6abe47d2f7adf1eae847d3b23b12b760586f6d41`

Predecessor identity is enforced by per-file SHA-256 in `manifest.json`, not by
the commit hash; the installer rejects any unexpected content before modifying
anything.

## Changed scope

Added:

- `docs/memory/decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — the decision;
- `docs/memory/patches/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md` — this record.

Replaced:

- `docs/memory/CURRENT.md` — work item advances to `C3.L2a`;
- `docs/memory/PHASE_C_CONTEXT.md` — sub-phase table, the settled
  classification, the corrected open question;
- `docs/memory/MEMORY.md` — durable classification block;
- `docs/memory/LEARNINGS.md` — two generalized lessons;
- `docs/memory/2026-09-18.md` — dated chronology;
- `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` — `C3.L2` and
  `C3.L2a` sections, status header refreshed;
- `docs/memory/investigations/ACTIVE.md` — was still naming `C3.L1` as next;
- `docs/memory/roadmap/STATUS.md` — was still naming `C3.L1` as next;
- `docs/memory/architecture/ADAPTIVE_BITRATE.md` — Linux runtime result and
  Linux capability classification;
- `docs/memory/handoffs/CURRENT_HANDOFF.md` — was still naming `C3.L1` as next;
- `docs/memory/CURRENT_HANDOFF.md` — stale duplicate at the memory root that
  still named the `C3.L0` audit as next; reduced to a pointer plus current
  state.

Generated and validated: `docs/memory/patches/PATCH_INDEX.md`.

## Intentionally unchanged scope

All companion and Android production source, all diagnostics and probes,
`tools/`, `.gitignore`, `docs/memory/AGENTS.md`, `docs/memory/MAINTENANCE.md`,
`docs/KNOWN_ISSUES.md`, `docs/PROJECT_STATUS.md`, `docs/ROADMAP.md`, and every
evidence record.

No evidence file is added, because no measurement was taken.

## Result recorded

Linux is classified `video_only_restart`: authorized for start-time profile
selection before `READY`, manual and loopback-only diagnostic changes, fallback
and recovery, and `C3.L3` characterization; not authorized for automatic
adaptation during `PLAYING`. `live_bitrate_reconfigure` remains unavailable
under the current architecture. `C3.L4` stays blocked with `C3.L2a` as its gate.

## Negative results recorded by this work item

- The `C3.L1R1` "request an immediate IDR" lead is premise-corrected: a fresh
  FFmpeg RTP stream already begins with in-band parameter sets and an IDR, so
  the lead named a remedy without an established cause.
- `max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are re-qualified
  as whole-session values against two sequence resyncs per session, not per-cycle
  measurements. The 287-318 ms decoder output gap is unaffected.
- Spawn, RTP silence and decoder output gap were being read as additive; they
  overlap, and 152 + 191 exceeding 287 was the visible tell.
- The Android receiver's resync and IDR-acceptance policy was not re-audited for
  this classification. Recorded as a gap and made the first task of `C3.L2a`.

## Validation performed

- installer Python compile;
- installer self-test against a fixture: wrong-state rejection before
  modification with a byte-identical snapshot before and after, clean install,
  installed-hash verification, generated-index correctness and exclusions,
  idempotent reinstall changing nothing, memory-health gate failure forcing
  rollback, forced-validation rollback restoring exact predecessor bytes and
  removing added files;
- `CURRENT.md` heading structure asserted: all seven required headings present
  exactly once;
- `tools/check_memory_health.py` executed as a post-write gate, not documented
  as a manual step;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved on every touched file;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime validation applies; this patch changes no executable behavior. None
is claimed.

## Result

Recorded on install.
