---
memory_schema: 1
as_of: 2026-11-10
status: TASK HANDOFF — DOCS-H7B (session C, docs only, ~5 min, unattended): record the PrivyParty design and workflow decisions (the user's second planning handoff, 2026-11-10; the user's "Adopt" after the wording was shown) and the user's decision to start PC-side preparation in a SEPARATE repo — the notes file and the PC kickoff brief are already in place; this task adds the pointer and the status line in ROADMAP §H7 (inserting §H7 first if DOCS-H7 has not run) and one CURRENT.md line. The hub side of H7 stays not started. No code; nothing adopted; nothing committed
---

# DOCS-H7B — the PrivyParty notes, pointed to

## Hard rules

Docs only. First `git status --short`: only the prompt files, this task, `docs/memory/architecture/H7_PRIVYPARTY_DESIGN_NOTES_2026-11-10.md`, `docs/memory/handoffs/PRIVYPARTY_PC_KICKOFF_BRIEF_2026-11-10.md`, and (if DOCS-H7 has not run) `handoffs/DOCS-H7_ROADMAP_INSERT_TASK.md` and `handoffs/H7_PRIVYPARTY_ROADMAP_TEXT.md` may be uncommitted — **if session B's queue files (B87-B89 or earlier) or any session A record are uncommitted, stop and say so.** The notes file and the brief are NOT edited (their wording is the user's). No code, no test run but `tools/check_memory_health.py`, no unit touched, no adb, no sudo, no network; nothing deleted; nothing adopted; nothing committed.

## The steps

1. **§H7 present?** `grep -n "^## H7" docs/ROADMAP.md`. If there is no hit, run `handoffs/DOCS-H7_ROADMAP_INSERT_TASK.md`'s steps 1-4 first (the verbatim insert after §H6, the phase table's H row, the CURRENT line, the checks), then continue. If there is one hit, leave §H7's existing text as it is.
2. **The status line:** in `docs/ROADMAP.md` §H7, directly under its **Status** paragraph, add: "**PC-side preparation started on the user's word (2026-11-10), in a separate repo; the hub side not started.** The PrivyHub repo and the hub's Code sessions are not touched by the PC work; the hub pulls the game repo only when H7's hub side starts."
3. **The pointer:** directly under that, add: "**Design notes:** `docs/memory/architecture/H7_PRIVYPARTY_DESIGN_NOTES_2026-11-10.md` — the art direction (photo textures on low-polygon models, a fixed camera, gibberish speech with subtitles), one template body with proportion numbers, one shared animation set, the licensing rule and the emulator audit it needs, the PC / hub / drive workflow, what goes ahead on the PC and what waits, the open measurements. **The PC side's kickoff brief:** `docs/memory/handoffs/PRIVYPARTY_PC_KICKOFF_BRIEF_2026-11-10.md`. Real player photos never go into git." Nothing else in §H7 changed.
4. **The phase table's H row:** where DOCS-H7 wrote "H7 PrivyParty PLANNED 2026-11-10 (not started)", make it "H7 PrivyParty: PC-side preparation started 2026-11-10 (separate repo); hub side not started".
5. **`docs/memory/CURRENT.md`:** the H7 line reads: "H7 (PrivyHub-native games; first PrivyParty): PC-side preparation started 2026-11-10 in a separate repo; the hub side not started — the user's word starts it (`docs/ROADMAP.md` §H7; design notes `architecture/H7_PRIVYPARTY_DESIGN_NOTES_2026-11-10.md`)". Headings kept; under its limit; `tools/check_memory_health.py` healthy after.
6. **Checks:** the notes file's and the brief's sha256 before = after (not edited); `git diff --stat` shows `docs/ROADMAP.md`, `docs/memory/CURRENT.md` and the new files only; no address, title, serial or path added; the redactor over the two new files finds nothing.
7. `logs/docs_h7b_git_status.txt`. The reply: "YOU, now: commit" plus whether §H7 had to be inserted, the places changed, and the health check's result.
