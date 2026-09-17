---
memory_schema: 2
as_of: 2026-09-17
---

# Active Investigations and Queued Work

## Active — D-129 single-column TV guide

D-128 runtime failed with `D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`. Inspection showed
that D-128 changed only channel text; the actual renderer remained the generic
`GridLayout` with three columns and fixed-width source buttons.

D-129 therefore changes the rendering seam:

- TV result pages: one column, full-width focusable guide rows;
- non-TV pages: unchanged three-column tile layout;
- row content: channel + current/next programme when available, explicit
  unavailable/incorrect-guide state otherwise;
- Android guide cache: bounded companion-only hydration before result render.

Canonical investigation: `D129_SINGLE_COLUMN_TV_GUIDE.md`.

## Queued after D-129

1. corrected/expanded EPG coverage/status presentation;
2. focused TV/media regression and D5 checkpoint.

## Observed but not active

Top-level TV entry still spends a few seconds on `Loading TV catalog...`.
Do not reopen that path without new evidence during this bounded guide UI change.
