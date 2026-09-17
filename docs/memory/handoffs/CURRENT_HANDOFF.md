---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 821796701d534e5cee127f43edf85342e1f7998c
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126 and D-127 are runtime accepted.
- D-128 built/installed but runtime probe returned
  `D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`; the UI still looked like the old
  three-column button grid.
- D-129 corrects the rendering seam itself: one-column full-width TV guide rows,
  while non-TV pages remain three-column.
- D-129 adds bounded companion-only Android guide-cache hydration; it does not
  change Linux acquisition policy or TV-state authority.

## Resume

Install and runtime-validate D-129 using the probe in `CURRENT.md`. If layout
passes without programme data, continue into the already-planned EPG
coverage/status investigation rather than reverting the list presentation.
