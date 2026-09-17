---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: 0c9d1aee1f4d9d65c2ee15729a52fbbb32861dd8
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126, D-127, D-129 and D-131 are runtime accepted.
- D-128 is superseded.
- D-130 measured the old TV-entry bottleneck.
- D-131 runtime acceptance: UI ready 330 ms; catalog 19 ms; state sync 24,050 ms;
  sync complete 24,754 ms; reconcile 25,073 ms; action `pulled`; local state
  changed; UI became ready before sync completion.
- User reports TV entry now feels like roughly one or two seconds and other Live
  TV behavior appears normal.
- D-132 is diagnostic-only and classifies Favorites EPG coverage/status reasons.

## Resume

Run `tools/probes/d132_favorites_epg_coverage_probe.py --repo .` and inspect
`logs/tv/d132_favorites_epg_coverage_probe.txt`.
