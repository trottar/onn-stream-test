# Project Memory Maintenance Policy

Any assistant, automation, or contributor operating on this repository should
follow this maintenance policy.

The repository is the durable source of project continuity. Memory maintenance
must not depend on a particular model, chat product, context-window mechanism,
or external runtime.

## Information classes

### Active state

`CURRENT.md` is the single authoritative resumable state. It should answer:

- What is the active objective?
- What work item is active?
- What directly relevant state is already verified?
- What is modified, incomplete, or blocked?
- What is the exact next action?
- What defines success?
- What should not be reopened without new evidence?
- Where is the supporting detail?

### Durable knowledge

`MEMORY.md`, `architecture/`, and `decisions/` contain long-lived rules,
invariants, subsystem boundaries, accepted design decisions, and repeatedly
useful validated facts.

`MEMORY.md` is not a chronological development log.

### Historical chronology

Dated memory files, `patches/`, and `history/` preserve completed work and
superseded state. Historical files are not startup requirements.

### Canonical evidence

`evidence/`, `investigations/`, probe output, logs, and dedicated validation
records contain detailed proof. Active memory references them instead of copying
their full contents.

## Startup reading policy

For substantial work:

1. Read `AGENTS.md`.
2. Read `CURRENT.md`.
3. Read only the files explicitly referenced by `CURRENT.md` that are relevant
   to the active task.
4. Consult `MEMORY.md` selectively when durable architecture or operating rules
   are needed.
5. Read handoffs, dated history, patch history, investigations, and evidence only
   when the active task requires them.

Do not eagerly load the full memory hierarchy.

## Maintenance triggers

Thresholds are guardrails. Semantic clarity takes precedence over exact byte or
line counts.

| File | Soft trigger | Hard trigger | Normal target |
| --- | ---: | ---: | ---: |
| `CURRENT.md` | ~10 KB or ~200 lines | ~20 KB or ~400 lines | ~2–8 KB |
| `handoffs/CURRENT_HANDOFF.md` | ~8 KB | ~15 KB | as small as practical |
| `MEMORY.md` | ~35 KB | ~60 KB | below soft limit when practical |

Maintenance is also triggered when:

- more than one objective is presented as current;
- more than one next action is authoritative;
- completed work accumulates in `CURRENT.md`;
- stale phase descriptions coexist with newer state;
- contradictory project-status statements exist;
- the same result is repeated across active-memory files;
- a fresh reader needs historical files merely to determine the next action;
- a major phase or milestone completes;
- a significant handoff is about to occur;
- the active task materially changes direction.

If a hard limit is exceeded, memory maintenance becomes the next repository
maintenance task after reaching the nearest safe checkpoint. Do not interrupt an
unsafe intermediate code state, partially applied migration, destructive
operation, or diagnostic step whose state would be lost.

## Required maintenance procedure

1. **Identify active truth.** Determine one current objective, one work item,
   verified state, repository/patch state, blockers, next action, and success
   criteria.
2. **Preserve canonical detail.** Before removing active detail, verify that
   important information exists in dated memory, evidence, investigations,
   decisions, architecture, patch history, or Git history.
3. **Move chronology out.** Completed task-by-task history belongs in dated or
   historical records, not the bootstrap.
4. **Promote durable conclusions.** Keep the long-lived lesson, not the entire
   investigation.
5. **Replace detail with pointers.** Active memory should index canonical
   knowledge rather than reproduce it.
6. **Remove duplication.** Maintain one authoritative current statement.
7. **Rewrite active state.** Rebuild `CURRENT.md` as a standalone bootstrap;
   do not merely delete random old paragraphs.
8. **Review handoff duplication.** `CURRENT_HANDOFF.md` contains only
   handoff-specific information not already obvious from `CURRENT.md`.
9. **Run the memory health check.** Use `tools/check_memory_health.py`.

## Avoid recursive summarization

Do not repeatedly summarize a summary.

Before removing important detail from active memory:

1. locate the canonical evidence, history, decision, or patch record;
2. verify it preserves the necessary qualifiers;
3. reference it;
4. then shorten active memory.

Raw evidence and specific validated records outrank later generalized summaries
when they conflict.

## Handoff policy

`CURRENT.md` is the authoritative resumable state.

Retain `CURRENT_HANDOFF.md` only as a small transfer note when a handoff is
useful. It must not become a second `CURRENT.md` or append-only chronology.

## Memory health check

- [ ] `CURRENT.md` contains exactly one active objective.
- [ ] `CURRENT.md` contains exactly one authoritative next action.
- [ ] Completed chronology is outside active state.
- [ ] Detailed evidence lives outside active memory.
- [ ] Durable findings are represented in long-term memory or decisions.
- [ ] No contradictory active phase/status declarations remain.
- [ ] Active-state files do not unnecessarily duplicate one another.
- [ ] Historical material is loaded only when needed.
- [ ] A fresh reader can resume work from the bootstrap files alone.
- [ ] Active-memory files remain below their maintenance thresholds.

## Safety

Memory maintenance must:

- preserve unique project knowledge;
- preserve evidence;
- avoid unrelated documentation redesign;
- avoid application/runtime behavior changes;
- use existing directory conventions;
- prefer Git history and existing canonical records over copying large old
  documents into new archives;
- preserve uncertain information in history rather than silently deleting it.

Automatic destructive rewriting is not part of this policy.

## Negative-result policy

Durable memory records failures alongside successes. This is a maintenance
requirement, not a stylistic preference: a repository that preserves only
successful outcomes cannot prevent a future session from retrying a path that
was already measured and rejected.

Every meaningful patch, probe, diagnostic, discussion outcome or roadmap change
records, in the same work:

1. what was attempted, and the narrow hypothesis behind it;
2. what succeeded, with the measurements that establish it;
3. what failed, was rejected, was rolled back, or was rejected before
   modification, with the measurement or reason that decided it;
4. what remains unknown;
5. the durable lesson, promoted to `LEARNINGS.md` when it generalizes beyond the
   immediate work item.

Rules:

- a rejected candidate, a rolled-back installer and a wrong-state rejection are
  all results and are written down;
- state explicitly when a run was clean, so that an absent failure section means
  "none occurred" rather than "none were recorded";
- preserve superseded records; mark newer state authoritative rather than
  deleting the old one;
- raw measurements outrank later generalized summaries when they conflict;
- before shortening an active file, verify the canonical evidence record holds
  the measurements being removed.

Patch result classes remain `INSTALLED SUCCESSFULLY`,
`FAILED BEFORE MODIFICATION` and `ROLLED BACK`. Whichever occurred is recorded.

## Generated indexes

Where the source of truth for a memory file is a directory, prefer generating
that file and validating the generated output over hand-transcribing it.
`patches/PATCH_INDEX.md` is generated from `docs/memory/patches/*.md`.
Hand transcription of a large directory listing is a known failure mode.
