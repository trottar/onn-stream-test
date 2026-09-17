---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-128 guide-style Favorites/category presentation

Rev1 compile failure was diagnostic-only: duplicate `formatTvGuideTime(Long)`; installer rollback restored the predecessor. Rev2 corrected the transform but its user-facing shell wrapper could terminate the interactive Bash session before installation. Rev3 passed the Android build but failed `tools/check_memory_health.py` because generated `CURRENT.md` omitted two required headings, and rolled back. Rev4 keeps the established function/`return` procedure and validates the exact required heading set during installer self-test.

Validate the Android presentation-only change:

- shared TV rows show cached current programme start/end/title;
- shared TV rows show cached next programme start/end/title when available;
- marked-incorrect rows remain untrusted and suppress Now/Next;
- rendering does not initiate acquisition or mutate channel state.

Canonical investigation: `D128_GUIDE_STYLE_CATEGORY_PRESENTATION.md`.

## Queued after D-128

1. corrected/expanded EPG coverage/status presentation;
2. focused TV/media regression and D5 checkpoint.

## Observed but not active

Top-level TV entry still spends a few seconds on `Loading TV catalog...`.
Do not reopen that path without new evidence during this bounded presentation
change.
