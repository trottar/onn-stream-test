---
memory_schema: 1
as_of: 2026-11-02
status: TASK HANDOFF — DOCS-AUDIT (session C, docs only, READ-ONLY, runs in parallel with A and B): an inventory of every README, doc, memory file, handoff and patch note against the real state (fourteen adopted lines, APK `fcd924c2…` CONFIRMED, `privyhub-diag` running, the records), and a cleanup plan for the user to approve. Writes ONE file, `docs/memory/evidence/DOCS_AUDIT_2026-11-02.md`; touches nothing else; deletes nothing; proposes archiving by `git mv`, never deletion. The apply pass is a later prompt, after the user's approval, when no A or B session is running
---

# DOCS-AUDIT — what the repo says vs what is true

**Why:** the user, 2026-11-02: "There are some really outdated readmes, memories, etc. … an audit and try to clean things up a bit". `CURRENT.md` has been over its size limit since before 2026-10-23; `QUEUE_2026-10-19B.md` (memory maintenance, the G9 checkpoint draft) was written and never run; the READMEs predate most of the adopted state.

**Hard rules:** read-only but the one output file; no code, no tests, no stream, no restart, no adb; nothing moved, renamed or deleted; nothing of A's or B's touched (both may be running — do not open their files for writing; read is fine); no addresses or identifiers in the output.

## 1. The inventory (a table per group, every file, one line each: path, last commit date, size, what it claims, true / stale / duplicate / done, the proposed action)

- **Top-level and per-directory READMEs** (`README.md`, `companion/`, `tools/`, `tests/`, `PrivyHub/`, `docs/`): what each says the product is, how to run it, which flags and settings it names — against `tools/e1_suite.py` `ADOPTED` (fourteen), the drop-ins, the APK pin, the keeper, the runbooks.
- **`docs/`:** `ROADMAP.md`, `KNOWN_ISSUES.md`, `CAPABILITY_MODEL.md`, `REMOTE_TRUST.md` and the rest: which sections are current, which describe superseded states (eight lines, the per-run WAN flags, the guard default, the old recovery), duplicates between them.
- **`docs/memory/`:** `CURRENT.md` (its size against the limit; which sections are live, which are history that belongs in the records), `handoffs/` (every TASK / QUEUE / DONE / RUNBOOK file: done, held, superseded, or live — `QUEUE_2026-10-19B.md` and `QUEUE_2026-10-19N.md` named explicitly; the `COWORK_HANDOFF_*` and `CURRENT_HANDOFF.md` files), `patches/` (applied, prepared-unapplied, superseded), `evidence/` (count and size only — records are never moved; the `reads/` dir), the memory schema files and `MEMORY_MAINTENANCE_REPORT_2026-09-17.md`.
- **Scratch and leftovers in the tree:** `_cowork_prompt*.txt` (which are live: `_cowork_prompt.txt`, `_cowork_prompt_b.txt`; which are historical: `_cowork_prompt_offsite.txt`), `logs/*_git_status.txt` (count), anything untracked.

## 2. The plan (for the user's approval; nothing applied here)

- **Archive** (by `git mv` into `docs/memory/archive/<group>/`, with a one-line index): the done and superseded handoffs, the applied patch notes, the historical prompt files, the old handoff summaries — each named.
- **Rewrite:** `README.md` → what the product is today (the hub, the onn app, LAN and away-from-home play, the diagnostics), how to run it, where the records are; the per-directory READMEs to the files that exist; `docs/` pages: the superseded sections marked or moved to the archive with a pointer.
- **`CURRENT.md`:** the proposed structure under the limit — the adopted state (fourteen lines, the APK, the keeper, the off switches), the open items, the next actions, an index to the records — with the history moved to a dated `CURRENT_HISTORY_<date>.md` in the archive.
- **One user-facing runbook:** `docs/RUNBOOK.md` from `TRIP_RUNBOOK_2026-10-30.md` generalized (at home, away, if it breaks, the one-line reads), placeholders only.
- **The memory maintenance** QUEUE_2026-10-19B asked for: what of it still applies.
- **Risks:** which files other sessions write (CURRENT.md, KNOWN_ISSUES, ROADMAP, SESSION_B_STATUS) and that the apply pass must run only when A and B are idle; which tools read paths that would move (none expected for `handoffs/`; check `tools/` and `tests/` for hard-coded doc paths before any move — list the hits).
- **The estimate:** files touched, files moved, and the apply pass's length.

Write `docs/memory/evidence/DOCS_AUDIT_2026-11-02.md` with the tables and the plan; `logs/docs_audit_git_status.txt` is NOT written (A may be writing `logs/`); exit. The reply begins "YOU, now: read docs/memory/evidence/DOCS_AUDIT_2026-11-02.md and say approve / change" and gives the counts: files inventoried, stale, to archive, to rewrite.
