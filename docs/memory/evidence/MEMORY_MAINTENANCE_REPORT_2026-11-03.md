---
memory_schema: 1
as_of: 2026-11-03
status: MEMORY_MAINTENANCE_HEALTHY — DOCS-APPLY (session C, docs only): the docs audit's plan in its option (b), the user's approval of 2026-11-02 ("b is the better choice"). 83 files archived by git mv, 36 rewritten, 13 created; tools/check_memory_health.py went from maintenance_required to healthy. No code file edited, nothing deleted, no record moved or edited, nothing adopted, nothing committed
---

# Memory maintenance report — 2026-11-03

Task: `handoffs/DOCS-APPLY_2026-11-03_TASK.md`. Plan: `evidence/DOCS_AUDIT_2026-11-02.md` §2, option (b).
Predecessor: commit `b20729b8`; every file named below is recoverable at that commit (the git history is the
predecessor copy; the verbatim moves below keep the text in the tree as well). This report has the same shape as
`MEMORY_MAINTENANCE_REPORT_2026-09-17.md`.

## Precondition

- Only `privyhub-companion` and `privyhub-diag` were active.
- `SESSION_B_STATUS.txt`'s last line read 2026-11-03T03:11:36Z, "queue M … done ok".
- `git status --short` was empty.
- HEAD was `b20729b8`.

## `tools/check_memory_health.py`

Full output is in `docs_apply_2026-11-03/before.txt` and `after.txt`.

| File | Before | After |
|---|---|---|
| `CURRENT.md` | 1,320 lines / 99,298 B — **HARD_LIMIT** | 155 lines / 10,226 B — healthy |
| `handoffs/CURRENT_HANDOFF.md` | 224 lines / 14,010 B — **SOFT_LIMIT** | 18 lines / 752 B — healthy |
| `MEMORY.md` | 660 lines / 35,818 B — healthy (22 B under the soft limit) | 544 lines / 30,146 B — healthy |
| Structure (CURRENT.md's required headings, each exactly once) | True | True |
| **Overall** | **maintenance_required** | **healthy** |

## What was done

**1. The archive (`git mv`, 83 files).**

| Destination | Files |
|---|---|
| `archive/docs/` | 5 |
| `archive/memory/` | 72: the 25 daily logs, CHECKPOINT_PROPOSAL, PHASE_C_CONTEXT, manifest.json, 39 closed investigations, repository/AUDIT, roadmap/D5_MEDIA_SERVER_SUBSTEPS, roadmap/STATUS, templates/SESSION_LOG, chats/CHAT_INDEX |
| `archive/prompts/` | 1 |
| `archive/scratch/` | 1 (the root STOP) |
| `archive/windows-scripts/` | 4 |

- Each file is listed in `archive/INDEX.md` (old path → new path, verdict, reason), together with its "open items carried out" section.
- `.gitignore` line 26 `archive/` became `/archive/`. One exact rule keeps ignored the one nested evidence dir the old pattern had matched (`evidence/lan_r1_2026-10-21/inputs/archive/`: 3 raw heartbeat logs, never committed).
- `handoffs/` and `patches/` stay in place. `handoffs/README.md` (new, 249 rows) and `patches/PATCH_INDEX.md` (rewritten, 241 rows) index them.

**2. The verbatim moves.** Each was made by mechanical line slicing and each was checked byte-equal to the source.

| Moved from | To | Size moved | Check |
|---|---|---|---|
| CURRENT.md | `archive/current/CURRENT_HISTORY_2026-11-02.md` | 1,270 lines | five ranges, each `cmp`-equal |
| KNOWN_ISSUES.md | `archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` | 1,138 lines in 15 closed sections, including the misfiled LAN-R1 chronology | kept + moved = 2,564 lines |
| TOOLS.md | `archive/memory/TOOLS_HISTORY_2026-11-02.md` | 1,814 lines | — |
| MEMORY.md | `history/MEMORY_SECTIONS_MOVED_2026-11-03.md` | 217 lines | — |
| CURRENT_HANDOFF.md | `history/HANDOFF_SECTIONS_THROUGH_2026-10-16.md` | all 224 lines | — |
| `investigations/ACTIVE.md` | `history/ACTIVE_INVESTIGATIONS_THROUGH_2026-10-15.md` | the whole body | sha256 equal |

Each destination file names commit `b20729b8` as its source.

**3. The memory core.**
- **CURRENT.md** keeps the seven headings exactly and contains:
  - the fourteen-line table, with records;
  - the one off switch;
  - the client (`fcd924c2…` CONFIRMED, `554ccf61…` not, `0132b944…` pinned and not installed);
  - the units (`privyhub-diag` running);
  - B33 live;
  - the built-not-adopted list;
  - HOME-2 next;
  - the Do-Not-Reopen list whole, plus G-A6.
- **MEMORY.md:** Phase C is now marked closed, and 5.4 KB of Phase E / G durable facts were added, each with its record.
- **AGENTS.md:** git commits rather than ZIPs; the companion as a unit; the chronology in `evidence/`.
- **TOOLS.md:** the 14-row drop-in / off-switch table and the live tools.
- **MAINTENANCE.md:** a "Front matter (memory_schema)" section.
- **COMMUNICATION.md:** the user's working rules, carried from `COWORK_HANDOFF_2026-10-05.md`.
- **Also rewritten:** USER.md, templates/MEMORY_UPDATE.md, repository/CODE_MAP.md and repository/DEBT.md.

**4. The READMEs and the runbook.**
- Rewritten: `README.md` (what PrivyHub is today, how to run it, the fourteen lines, the diagnostics, the records), `docs/README.md`, `docs/memory/README.md`, `docs/memory/history/README.md`.
- New: `companion/README.md`, `tools/README.md`, `tests/README.md`, `PrivyHub/README.md` (Markdown only).
- New: `docs/RUNBOOK.md`, generalized from `handoffs/TRIP_RUNBOOK_2026-10-30.md` and G4_RUNBOOK_HOTSPOT §A, with placeholders only.

**5. The docs pages.**
- **ROADMAP:** §0 and §1 refreshed; 22 superseded markers; nothing deleted.
- **KNOWN_ISSUES:** an open index on top, with the carried-out items.
- **REMOTE_TRUST:** markers on §4–§6, §8 and §14; a new §8a for G-A1.
- **Also updated:** CAPABILITY_MODEL §7, WAN_ADAPTATION_RULES (header and §3), DIAGNOSTICS (rewritten around `privyhub-diag`), A8_INPUT_PROFILES (the status block).
- **Under `docs/memory/`:** status headers on 9 `architecture/` files, the DECISION_LOG header, D083's status line, and `investigations/ACTIVE.md` as a short index.

## QUEUE_2026-10-19B's memory maintenance (audit §2.7)

| Item | Outcome |
|---|---|
| M-2, CURRENT.md under its limit with nothing lost | **done here.** The headings are unchanged, the Do-Not-Reopen list is whole, nothing was deleted, and the history moved verbatim. |
| The same pass for MEMORY.md and CURRENT_HANDOFF.md | **done here.** Both are now under their soft limits. |
| Preserve the predecessors and write a report in the 09-17 shape | **done:** this report, the predecessor commit `b20729b8`, the verbatim archive files, and `docs_apply_2026-11-03/`. |
| "Write nothing new into Next Action" | Overtaken; it applied to that night only. |
| **G9-D1, the G9 checkpoint draft** | **not done here; still wanted as its own task.** Its inputs moved on (audit §2.7): G4-S4 and the trip; line 13 adopted; G5-S2-L and G8-S6 never run; the reconnect read; the handheld; Steam deferred; the overlay-down LAN row never scored. |
| The ROADMAP §G9 status line | Goes with G9-D1. |

## Not done, and why

- **Patch-note and handoff status lines that are wrong today were not edited.** Option (b) leaves those files untouched; the truth is recorded in `patches/PATCH_INDEX.md` and `handoffs/README.md` instead.
- **Code comments that name handoff files were not touched**, because no code file is edited. They still resolve, since `handoffs/` did not move.
- **Two KNOWN_ISSUES sections the audit had listed as closed were kept OPEN:** CL-B4 (its heading still says "SPIKES OPEN", and no later record closes the spikes) and the C3.L0 audit (Linux host telemetry still starts only on the Windows path, as the code reads). The 2026-09-22 and 09-23 lists were also kept open (CURRENT still lists items from them).
- **The audit's rewrite count of 37** was one higher than its own list, which comes to 36 including `.gitignore`. All 36 were done.
- **Agent scratch copies** under `/tmp/` are outside the repository and were left in place; nothing was deleted.
