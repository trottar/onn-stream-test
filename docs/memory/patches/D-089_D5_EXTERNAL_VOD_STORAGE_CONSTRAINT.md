---
memory_schema: 1
as_of: 2026-09-16
patch: D-089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT
durable_memory_updated: true
production_code_changed: false
---

# D-089 D5 external VOD storage constraint

Purpose:
- record the temporary external-hard-drive deployment for bulk VOD on the Linux
  Prototype 1;
- preserve storage-root portability for later server-like infrastructure;
- update the Phase-D roadmap so D4 final Games regression is the immediate next
  step and D5 carries the storage constraint before implementation begins.

Predecessor checkpoint:
`c6f28864e9b0446a4877d1b60aa41750256c2b12`

No production code is modified.

Updated durable surfaces:
- `docs/ROADMAP.md`
- `docs/memory/CURRENT.md`
- `docs/memory/MEMORY.md`
- `docs/memory/2026-09-16.md`
- `docs/memory/handoffs/CURRENT_HANDOFF.md`
- `docs/memory/roadmap/STATUS.md`
- `docs/memory/architecture/TV_MEDIA.md`

No external mount path is recorded or standardized.
