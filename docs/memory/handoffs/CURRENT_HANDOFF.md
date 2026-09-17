---
memory_schema: 2
as_of: 2026-09-17
baseline_commit: bfc62a6c5b815ecbd9427af0117d5c22906e2998
---

# Current Handoff

The authoritative resumable state is `../CURRENT.md`. Read it first.

## Handoff-specific state

- Authoritative Linux worktree: `/home/privyhub/Projects/onn-stream-test`.
- D-125, D-126, D-127 and D-129 are runtime accepted.
- D-128 is superseded after `D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`.
- D-129 runtime acceptance: four visible guide rows, all full-width/one-column;
  three rows had current-programme data and one explicitly reported unavailable
  guide data.
- Remaining Live TV usability observation: top-level `Loading TV catalog...`
  still takes a few seconds while result-page navigation is otherwise responsive.
- D-130 is diagnostic-only timing instrumentation for the existing TV-entry
  stages; do not change sync/catalog policy until its measurements are inspected.

## Resume

Run the D-130 prepare/open-TV/verify sequence in `CURRENT.md`, inspect the raw
stage timings, then make one production change against the measured bottleneck.
