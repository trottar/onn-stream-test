---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 020d86a0c0792653e2ce4d976244098981419648
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126 and D-127 are runtime accepted.
- D-128 rev1 failed compile on a duplicate `formatTvGuideTime(Long)` overload and rolled back exactly.
- D-128 rev2 corrected the transform but the supplied Bash wrapper could terminate the interactive session before installation. Rev3 passed the Android build but failed the repository memory-health gate because its generated `CURRENT.md` omitted two required headings; rollback restored the predecessor. Rev4 corrects that memory contract.
- D-128 is Android presentation-only and requires runtime validation after APK
  installation.
- D-128 consumes cached guide data only; acquisition/prefetch remains owned by
  the validated D-125/D-126 paths.

## Resume

Run the D-128 Favorites UI validation in `CURRENT.md`. On acceptance, proceed to
EPG coverage/status semantics, then the focused D5 regression/checkpoint.
