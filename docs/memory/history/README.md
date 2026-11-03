---
memory_schema: 1
as_of: 2026-11-03
---

# Deep Memory / Superseded History

This directory keeps superseded snapshots, and sections moved out verbatim. They stay useful for reconstructing the
history. They are not the authoritative current state, which is `../CURRENT.md`.

## Trust order

When history conflicts with current material, prefer:

1. current local source and fresh runtime evidence;
2. newest specific evidence/decision/architecture records;
3. `CURRENT.md`;
4. durable rules in `MEMORY.md`;
5. dated/patch history;
6. this directory.

Do not copy an old guardrail, roadmap phase, baseline commit, classifier result, or investigation status back into
current memory without checking newer evidence.

## Files

| File | What it holds |
|---|---|
| `ACTIVE_INVESTIGATIONS_SUPERSEDED_THROUGH_2026-09-11.md` | the active-investigations list as of 2026-09-10 (Phase A, the A9 checkpoint) |
| `ACTIVE_INVESTIGATIONS_THROUGH_2026-10-15.md` | the whole of `investigations/ACTIVE.md` at commit `b20729b8`, last changed 2026-10-15; copied by `git show` on 2026-11-03, when ACTIVE.md became a short index |
| `HANDOFF_SECTIONS_THROUGH_2026-09-22.md` | the sections moved verbatim out of `handoffs/CURRENT_HANDOFF.md` on 2026-09-23 (size limit) |
| `HANDOFF_SECTIONS_THROUGH_2026-10-16.md` | the sections moved verbatim out of `handoffs/CURRENT_HANDOFF.md` at commit `b20729b8` (DOCS-APPLY, 2026-11-03): its sections from 2026-10-16 back to Phase C |
| `MEMORY_SECTIONS_MOVED_2026-09-23.md` | the sections moved verbatim out of `MEMORY.md` on 2026-09-23, to bring it under its soft size limit; each left a one-line pointer |
| `MEMORY_SECTIONS_MOVED_2026-11-03.md` | the sections moved verbatim out of `MEMORY.md` at commit `b20729b8` (DOCS-APPLY, 2026-11-03): the closed D-BASE-era detail; each left a one-line pointer |
| `MEMORY_SUPERSEDED_THROUGH_2026-09-11.md` | the curated project memory as of 2026-09-10 (the Windows-companion era) |
| `README.md` | this file |

The other history moved on 2026-11-03 is under `../archive/`, indexed by `../archive/INDEX.md`:
- `archive/current/CURRENT_HISTORY_2026-11-02.md` (CURRENT.md's history);
- `archive/memory/TOOLS_HISTORY_2026-11-02.md`;
- `archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md`.

## 2026-09-17 bootstrap maintenance

The exact active-memory state just before the 2026-09-17 memory-maintenance rewrite is kept in Git, in commit
`0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd`.

That commit holds the pre-maintenance `CURRENT.md`, `MEMORY.md`, `CURRENT_HANDOFF.md`, active investigation index and
roadmap status. Do not copy those large files into a second archive just to shorten the live bootstrap.

The specific technical detail is also kept in the dated memory (now `archive/memory/daily/`), the evidence, the
investigations, the patch records, the architecture and the decisions.
