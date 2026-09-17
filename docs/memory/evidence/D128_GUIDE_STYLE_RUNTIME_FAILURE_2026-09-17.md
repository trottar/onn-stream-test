# D-128 guide-style UI runtime failure — 2026-09-17

Classification:

`D128_GUIDE_STYLE_ROWS_NOT_OBSERVED`

Observed probe values:

- `now_row_count: 0`
- `next_row_count: 0`
- `marked_incorrect_visible_count: 0`
- `now_rows_present: False`
- `next_rows_present: False`

Manual observation: the Favorites screen looked unchanged from the prior
three-column button UI; it did not resemble a one-column television guide.

Interpretation: D-128's text-only row enrichment did not change the actual
layout seam and is not accepted. D-129 supersedes it.
