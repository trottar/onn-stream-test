---
memory_schema: 1
as_of: 2026-11-03
status: TASK HANDOFF — DOCS-APPLY (session C, docs only, ~2½ h, unattended; the user's approval 2026-11-02 of `DOCS_AUDIT_2026-11-02.md`'s plan in its option (b): clean without moving `handoffs/` or `patches/`). Runs ONLY when no A or B session is running and their work is committed. No code file is edited; no file is deleted (archiving is `git mv`); the records under `evidence/` are never moved or edited. One session, five steps, the user's commit at the end
---

# DOCS-APPLY — the audit's plan, option (b)

**The user's decision (2026-11-02):** "b is the better choice". So: **§2.1's archive without the `handoffs/` and `patches/` groups** (83 moves: `archive/docs/` 5, `archive/memory/` 72, `archive/prompts/` 1, `archive/scratch/` 1, `archive/windows-scripts/` 4), the status indexes in place (`handoffs/README.md` as a status index of every handoff — done / held / superseded / live — and the rewritten `patches/PATCH_INDEX.md`), **§2.2's 37 rewrites and 8 new files, §2.3's markers, §2.4's CURRENT.md (the verbatim history move), §2.5's RUNBOOK, §2.6 the schema, §2.7 the maintenance report.** `manifest.json` and `roadmap/STATUS.md` are archived (the two September probes are already broken by today's content; the audit §2.8 accepts it). `docs_flat/` is ignored and local: left alone.

Read first: `evidence/DOCS_AUDIT_2026-11-02.md` in full (§0 the real state; §1 every verdict; §2 the plan; §2.8 the risks — the tools that read doc paths and the headings `check_memory_health` requires), `docs/memory/MAINTENANCE.md`, `tools/check_memory_health.py`, the newest records for the facts the rewrites state (`G_A10_…`, `HOME_1_…`, `SESSION_B_DONE_2026-11-02M.md` if it exists, `TRIP_R2_…`, `B36_…`).

## 0. Precondition (stop if any fails; say which)

- No `privyhub-*` unit but the companion and `privyhub-diag` is active (A idle); `handoffs/SESSION_B_STATUS.txt`'s last line says queue M is done or B is idle (no "running" line newer than its DONE file); **`git status --short` shows nothing but the `_cowork_prompt*.txt` files** (A's and B's work committed by the user); HEAD named.
- `tools/check_memory_health.py` run before, its output kept (`before.txt`).
- **Every fact written below comes from the records named in the audit §0** (fourteen lines and their records; APK `fcd924c2…` CONFIRMED, `554ccf61…` not; `privyhub-diag` running; B33 live; the built-not-adopted list) — re-read §0 and, if queue M's DONE exists, its state too. Nothing invented; where a fact is not in a record, write "not recorded".

## 1. The archive and the indexes (~40 min)

- `.gitignore` line 26 `archive/` → `/archive/` (the first change; `git check-ignore docs/memory/archive/x` must then say not ignored).
- `git mv` the 83 files of §2.1 (b) into `docs/memory/archive/<group>/` exactly as the audit lists them; `docs/memory/archive/INDEX.md`: one line per moved file (old path → new path, verdict, reason) and the "open items carried out" section (QUEUE_19N's G8-S6 and G5-S2-L, LINK-N1's nights not written up, G4_RUNBOOK §18's overlay-down check); each open item also into KNOWN_ISSUES' open index (step 4).
- `docs/memory/handoffs/README.md` (new): every handoff by name with its status (done / held / superseded / live) and the record that closed it, from §1.5; `patches/PATCH_INDEX.md` rewritten per §2.2 (every note, its status today). The files themselves stay.

## 2. The memory core (~45 min)

- **CURRENT.md** per §2.4: the seven headings kept exactly; the proposed structure (~9.5 KB / ~170 lines); the history lines moved **verbatim, newest first,** to `docs/memory/archive/current/CURRENT_HISTORY_2026-11-02.md` with the source commit named in its header; the "Do Not Reopen" list kept whole, plus G-A6. `CURRENT_HANDOFF.md` and `MEMORY.md` per §2.2 (Phase E / G durable facts in; closed-phase detail to `history/HANDOFF_SECTIONS_THROUGH_2026-10-16.md`); `AGENTS.md`, `TOOLS.md` (the 14-row drop-in / off-switch table; the history to `archive/memory/TOOLS_HISTORY_2026-11-02.md`), `MAINTENANCE.md` (§2.6), `USER.md` (the one line), the other small memory files §2.2 names.
- `tools/check_memory_health.py` after: CURRENT.md OK (no SOFT / HARD), all headings present; MEMORY.md and CURRENT_HANDOFF.md under their soft limits (`after.txt`). If it fails, fix the size, not the headings.

## 3. The READMEs and the RUNBOOK (~35 min)

- `README.md` per §2.2 (what PrivyHub is today, how to run it, the fourteen lines and the one off switch, the diagnostics, where the records are, the away-from-home steps in one paragraph pointing to the RUNBOOK); `docs/README.md`, `docs/memory/README.md`, `docs/memory/history/README.md`; the four new directory READMEs (`companion/`, `tools/`, `tests/`, `PrivyHub/`) listing the files that exist — **these are new Markdown files in code directories, not code edits**.
- `docs/RUNBOOK.md` per §2.5, placeholders only (`<home-value>`, `<hub-overlay-name>`, `<away-5ghz-network>`); the climb-time wording checked against the adopted state (the remote line; step in place).

## 4. The docs pages (~45 min)

- ROADMAP (§0 / §1 refreshed; superseded sections get a one-line "superseded by … (date)" marker; nothing deleted); KNOWN_ISSUES (an "Open items" index on top including the archive's carried-out items; the closed sections moved verbatim to `archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` with a pointer; the misfiled LAN-R1 chronology with them); REMOTE_TRUST, CAPABILITY_MODEL §7, WAN_ADAPTATION_RULES, DIAGNOSTICS, A8_INPUT_PROFILES per §2.2 / §2.3; the `architecture/` status headers; `decisions/DECISION_LOG.md` header and D083's status line; `investigations/ACTIVE.md` as a short index.

## 5. The close (~10 min)

- `evidence/MEMORY_MAINTENANCE_REPORT_2026-11-03.md` (§2.7: what was done, what of QUEUE_2026-10-19B still applies and was done here, the G9 checkpoint draft as its own later task); `git diff --stat` and `git status --short` kept in `evidence/docs_apply_2026-11-03/`; `tools/check_memory_health.py` once more; **no commit**. The reply begins **"YOU, now: read `git diff --stat`, then commit"** and gives the counts (moved, rewritten, created), the health check's before / after lines, and anything the audit asked for that was not done and why.

No code file edited (`companion/`, `tools/*.py`, `tests/`, `PrivyHub/` sources untouched — the new READMEs there are the only additions); no tests run beyond `check_memory_health`; no stream, no restart, no adb; nothing deleted (`git mv` only); the records never moved or edited; no addresses or identifiers anywhere; nothing adopted; nothing committed.
