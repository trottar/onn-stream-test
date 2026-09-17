---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-127 incorrect-guide intent

Question:

How should a user explicitly distrust an incorrect guide while keeping the
channel visible/playable and allowing a later controlled recheck?

Required boundaries:

- separate from Hide;
- durable across restart and TV-state synchronization;
- rejected guide not presented as trusted;
- later retry/recheck possible;
- no speculative remapping heuristic;
- no guide-grid redesign in the same change.

See `../CURRENT.md`.

## Queued after D-127

1. guide-style paged Favorites/category presentation;
2. corrected/expanded EPG coverage status semantics;
3. focused TV/media regression and D5 checkpoint.

## Observed but not active

Top-level TV entry still spends a few seconds on `Loading TV catalog...`.
Favorites itself loads immediately after D-126. Reopen entry-latency diagnosis
only if it remains materially problematic after the bounded D5 work or new
evidence localizes the delay.
