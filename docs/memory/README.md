---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# PrivyHub Durable Memory

This directory is the durable operational memory for the PrivyHub / Safe IoT project. It is intentionally stored in the repository so development does not depend on any chat system retaining context.

The design is OpenClaw-inspired: keep a compact curated memory, separate current state from historical session logs, keep user/collaboration preferences explicit, and preserve detailed evidence in indexed subdirectories instead of continuously growing one monolithic file.

## Authority order

When sources disagree, use this order:

1. The actual local working tree at `L:\Projects\onn-stream-test` plus fresh runtime evidence.
2. Successful local installer receipts and exact installed-output hashes.
3. `CURRENT.md`, `MEMORY.md`, and the current dated memory log when updated for the same checkpoint.
4. Feature-specific documentation and runtime evidence files.
5. Git/GitHub checkpoint history.
6. Older project documents and chat summaries.

Never silently merge contradictory states. Record the discrepancy, identify which evidence is newer, and mark old material as superseded or historical.

## What belongs here

- `MEMORY.md`: compact durable facts and decisions worth loading first.
- `CURRENT.md`: exactly where development is now and what happens next.
- `AGENTS.md`: operating rules for future development/chat agents.
- `USER.md`: project collaboration and communication preferences only.
- `TOOLS.md`: proven commands, diagnostics, and evidence entry points.
- `LEARNINGS.md`: durable lessons from failures and successful investigations.
- `COMMUNICATION.md`: how chat handoffs and memory updates are maintained.
- `architecture/`: subsystem maps and stable boundaries.
- `decisions/`: decision ledger with active/superseded/deferred status.
- `investigations/`: active, closed, and deferred investigations.
- `evidence/`: runtime validation ledger.
- `patches/`: packaging protocol and patch/checkpoint index.
- `repository/`: code map, audits, and technical debt.
- `roadmap/`: current authoritative status.
- `chats/`: concise summaries of project chats, not raw transcripts.
- `handoffs/`: current context package for a new chat.
- `memory/`: dated running session notes.
- `templates/`: consistent future update formats.

## Freshness policy

Core status files should carry `as_of` and `baseline_commit`. Historical files are not rewritten to pretend they were current; newer files explicitly supersede them. `docs/DEBUGGING_MEMORY.md` remains valuable historical evidence and the predecessor to this structure, but this directory is intended to prevent future append-only status drift.

## ZIP invariant

Every meaningful future PrivyHub ZIP update must include the memory files changed by that work. At minimum, update the current dated session log and any affected current/decision/evidence file. The ZIP manifest must state `durable_memory_updated: true`.
