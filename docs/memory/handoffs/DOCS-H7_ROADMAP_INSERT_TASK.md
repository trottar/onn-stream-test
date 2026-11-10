---
memory_schema: 1
as_of: 2026-11-10
status: TASK HANDOFF — DOCS-H7 (session C, docs only, ~5 min, unattended): insert the adopted §H7 (PrivyHub-native games; first: PrivyParty) into docs/ROADMAP.md after §H6, verbatim from `handoffs/H7_PRIVYPARTY_ROADMAP_TEXT.md` — the user's "Adopt" (2026-11-10) after seeing the wording. PLANNED only: no work starts on H7 until the user says. No code; nothing adopted; nothing committed
---

# DOCS-H7 — the roadmap insert

**The user's decisions (2026-11-10):** the idea added as the LAST sub-item of the current phase (Phase H → **H7**); the engine Godot on the hub (a probe first); mini games from SNES, N64, PS1, PS2 and GameCube in that order; the user's house only in the first version; the name **PrivyParty**; "Adopt". **No work on H7 until the user says** ("I might just do it next").

## Hard rules

Docs only. First `git status --short`: only the prompt files, this task and the text file may be uncommitted — **if session B's queue AE files (B84-B86) or any A record are uncommitted, stop and say so** (B edits §H6; this insert goes in after B's commit). No code, no test run but `tools/check_memory_health.py`, no unit touched, no adb, no sudo, no network; nothing deleted; nothing adopted; nothing committed.

## The steps

1. `docs/ROADMAP.md`: insert the whole of `docs/memory/handoffs/H7_PRIVYPARTY_ROADMAP_TEXT.md` **verbatim** as a new section **after the end of §H6** (after its last paragraph, before the `---` that precedes "# Phase I — Home Infrastructure / Broader Plugin Expansion"), with one blank line before and after. Nothing in §H6 or any other section changed.
2. `docs/ROADMAP.md` §1's phase table, the H row: append to its status cell " ; **H7 PrivyParty PLANNED 2026-11-10** (not started)". If the H row's status still reads "OPEN 2026-11-07 …", leave the rest of the cell as it is (its refresh is not this task's).
3. `docs/memory/CURRENT.md`: one line where the roadmap's open sections are named (or at the end of Next Action): "H7 (PrivyHub-native games; first PrivyParty) PLANNED 2026-11-10 — not started; the user's word starts it (`docs/ROADMAP.md` §H7)". Headings kept; under its limit; `tools/check_memory_health.py` healthy after.
4. Checks: `grep -n "^## H7" docs/ROADMAP.md` → one hit, after `## H6`, before `# Phase I`; `diff` of the inserted block against the text file → identical; `git diff --stat` → the two docs only (plus this task's files); no address, title, serial or path added.
5. `logs/docs_h7_git_status.txt`. The reply: "YOU, now: commit" plus the three places changed and the health check's result.
