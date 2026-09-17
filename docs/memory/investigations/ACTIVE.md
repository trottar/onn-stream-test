---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-127 incorrect-guide runtime validation

Development implementation is installed when this file is present.

Validate:

- `Mark Guide Incorrect` does not hide or disable the channel;
- current-program and Program Guide presentation are suppressed while marked;
- rejected guide-source fingerprint is durable through Linux TV-state sync;
- app/companion restart preserves the mark;
- delayed rejected-guide prefetch does not silently clear intent;
- Retry does not silently trust the same rejected source;
- explicit Accept/Clear restores trust deliberately.

Canonical design record:
`D127_INCORRECT_GUIDE_INTENT.md`.

## Queued after D-127

1. guide-style paged Favorites/category presentation;
2. corrected/expanded EPG coverage status semantics;
3. focused TV/media regression and D5 checkpoint.

## Observed but not active

Top-level TV entry still spends a few seconds on `Loading TV catalog...`.
Favorites itself loads immediately after D-126. Reopen entry-latency diagnosis
only if it remains materially problematic after the bounded D5 work or new
evidence localizes the delay.
