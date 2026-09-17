---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-130 top-level TV-entry latency

D-129 is runtime accepted. The one-column guide renderer is not the remaining
latency source: Favorites/category result pages load within a few seconds and the
specific persistent delay is top-level `Loading TV catalog...`.

D-130 measures one existing `openTvHome()` execution:

- initial `ensureCatalog()`;
- Linux TV-state synchronize/import;
- optional second `ensureCatalog()` after sync reports local state changed;
- UI render / total entry time.

Source inspection shows the initialized TV-state sync path currently imports the
Linux envelope and reports `localStateChanged = true`; `openTvHome()` then reruns
`ensureCatalog()`. This is a hypothesis only until D-130 measures the stages.

Canonical investigation: `D130_TV_ENTRY_LATENCY.md`.

## Queued after D-130

1. one production fix for the measured TV-entry bottleneck;
2. corrected/expanded EPG coverage/status presentation;
3. focused TV/media regression and D5 checkpoint.

## Observed but not active

No separate ADB, playback, Games, VOD, or transport regression is indicated by
the current evidence.
