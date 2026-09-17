---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 85cfc89e6327c156df4d9d6fa3bbf7f6b3ac577b
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126, D-127, D-129 and D-131 are runtime accepted.
- D-128 is superseded; D-130 is a closed latency diagnostic.
- D-132 classified 21 Favorites: 11 current, 5 schedule-gap with future guide,
  5 no known guide coverage.
- D-133 changes only the status wording for schedule-gap rows.

## Resume

Runtime-validate D-133 in TV -> Favorites with
`tools/probes/d133_epg_status_accuracy_probe.py`.
