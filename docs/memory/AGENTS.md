---
memory_schema: 2
as_of: 2026-09-18
baseline_commit: 0206017cfd8f0fc57decb7a5e9e8632e6a4f6cdd
---

# Agent Operating Rules

## Authority

Treat `/home/privyhub/Projects/onn-stream-test` as authoritative between
checkpoints. GitHub is reference/history unless a clean synchronized checkpoint
has been validated.

Prefer current local source and the newest specific runtime evidence over
summaries. Never let stale documentation override newer validated state.

This applies to prose as much as to numbers. **Before restating what a
decision, gate, classification or constraint says, open the record that
defines it** — not `CURRENT.md`'s summary of it, and not a previous session's
paraphrase. Restating a summary propagates it; on 2026-09-19 a single
undefined gate phrase was copied into six files without the decision record
being opened once. See `LEARNINGS.md`, "A decision record is a source, not a
summary".

## Startup

For substantial work:

1. read `CURRENT.md`;
2. read only CURRENT-linked records relevant to the active task;
3. consult `MEMORY.md` selectively for durable architecture/rules;
4. consult handoffs, history, investigations, patches, and evidence only when
   needed.

Follow `MAINTENANCE.md`. Do not eagerly load the full memory hierarchy.

## Development method

Use:

**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect evidence -> one coherent patch**

Inspect exact current source before modifying it. Establish the expected
pre-state, make one logical change, validate installed/generated output, and
avoid unrelated cleanup.

Do not reopen resolved or explicitly deferred investigations without new
evidence. Raw measurements outrank classifiers when they disagree.

## Execution budget

State the plan in three lines before starting. Stop and ask if the work needs
more than **10 file reads, 15 commands, or one deliverable**.

Minimizing cost and maximizing usable work per unit of budget is a project
value, not just a ceiling to avoid hitting — the same preference the project
principles already state for local-first, reuse-over-rebuild work. Pause
proactively, well before the hard cap, rather than running until a limit is
already exceeded: when a sub-phase is large enough that it might approach the
budget, say so in the three-line plan and split it into explicit smaller
parts up front (e.g. investigate, then patch, then package/deliver), pausing
between parts for a go-ahead instead of continuing straight to a finished
deliverable. A session that notices it is approaching the cap mid-task stops
there, reports exactly what is done and what remains, and waits, rather than
finishing the remaining work to avoid leaving it half-done.

Do **not** build installer self-tests, synthetic fixtures, stub compilers or
mock Android frameworks to pre-validate a patch. The gates that decide
correctness run on the user's machine — predecessor SHA-256, the real
`./gradlew :app:assembleDebug`, `tools/check_memory_health.py` — and the
installer restores exact predecessor bytes if any of them fails. Re-proving them
in a sandbox costs the user real money and proves nothing the install will not
prove.

Earlier patch records in `patches/` list fixtures, stub compilation and
multi-check self-tests under "Validation performed". **Do not use them as a
model.** They are over-built, they are the reason sessions have run 20+ minutes
on single work items, and this rule supersedes that precedent.

"Memory" in this project means `docs/memory/`. It does not mean assistant
memory. Read the repository.

## Durable memory

- `CURRENT.md` — single active objective, current state, exact next action.
- `MEMORY.md` — long-lived rules and validated facts, not chronology.
- `YYYY-MM-DD.md` — detailed dated history, one file per date at the
  memory root.
- `handoffs/CURRENT_HANDOFF.md` — small transfer note only.
- `architecture/` — subsystem architecture.
- `decisions/` — decisions and status.
- `evidence/` — runtime/E2E proof.
- `investigations/` — active/closed/deferred investigation detail.
- `patches/` — patch/install history.
- `roadmap/` — current development position.
- `history/` — superseded deep-memory reference.
- `MAINTENANCE.md` — memory lifecycle and health policy.

Every meaningful patch ZIP must include the relevant durable-memory changes and
set `durable_memory_updated: true`.

## Stable subsystem boundary

Do not disturb validated video, audio, controller, Save/Load, pause/resume,
TV-state sync, VOD storage, or other stable paths for unrelated work.

A compile/build is not runtime validation.

## Privacy

Never ask the user to provide or paste IP addresses. Do not place private
network addresses, ADB endpoints, device identifiers, credentials, or secrets in
shareable diagnostics or durable memory.

## Commands

Current Linux companion launch:

`python3 ./companion/privyhub_service.py`

Keep commands narrow and copy/paste friendly. Every response that asks the
user to run something includes the exact command(s), inline, every time —
not a description of what to run.

**Patches are delivered as ZIP installers the user runs.** The ZIP is written
into the repository root and the response carries one complete copy/paste
block: SHA-256 verification, extraction, install, gates, commit, push, return
to the repo root. This is a deliberate control boundary the user has stated
twice — the user runs the zip, the install and the push. Do not replace it
with direct file-bridge writes and do not describe the step away.

Diagnostic and probe output that a script already persists to a file (e.g. `logs/`, `docs/memory/evidence/`) is read directly from the repository through the session's file bridge, not requested as a paste. Ask for a paste only when no such file exists.

## Patch discipline

Follow `patches/PATCH_PROTOCOL.md`.

Before modification:

1. inspect exact current state;
2. verify expected predecessor state/hash;
3. reject wrong state before writing.

Where applicable, installers must back up changed files, preserve line endings,
validate generated output, compile changed Python, run applicable real builds,
run `git diff --check`, and restore exact predecessor bytes on deterministic
failure.

Result classes remain explicit:

- `INSTALLED SUCCESSFULLY`
- `FAILED BEFORE MODIFICATION`
- `ROLLED BACK`

Checkpoint with an exact reviewed staging allowlist. Never use broad
`git add .` to choose checkpoint scope.

**Derive the allowlist from `git status --short`, and account for every path
it prints** — stage it, or state why it is excluded. An allowlist written from
what the current patch happens to touch will silently leave earlier
uncommitted work behind: on 2026-09-19 a memory-scoped allowlist left the
runtime-validated `C3.L3` source changes uncommitted, and the user found them.
End a checkpoint block with `git status --short`; it should print nothing.
