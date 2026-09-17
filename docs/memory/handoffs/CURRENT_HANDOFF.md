---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 6da5c4506128b2518370de0f46e7b719bd967850
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126, D-127 and D-129 are runtime accepted.
- D-128 is superseded after runtime UI failure.
- D-130 measured TV entry at 24,525 ms: catalog 7 ms, state sync 24,214 ms,
  post-sync catalog 3 ms, UI render 291 ms.
- D-131 moves the unchanged Linux TV-state pull/import off the first-render
  critical path and reconciles afterward.
- D-131 does not change TV-state schemas, revision authority, conflict semantics,
  playback, guide acquisition or the D-129 layout.

## Resume

Runtime-validate D-131 with `tools/probes/d131_tv_entry_nonblocking_probe.py`.
Target: `D131_TV_ENTRY_NONBLOCKING_SYNC_VALIDATED`.
