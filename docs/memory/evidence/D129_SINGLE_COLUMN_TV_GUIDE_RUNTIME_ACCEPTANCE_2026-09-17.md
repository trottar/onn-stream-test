# D-129 — Single-column TV guide runtime acceptance

**Date:** 2026-09-17

Classification:

`D129_SINGLE_COLUMN_TV_GUIDE_RUNTIME_VALIDATED`

Runtime measurements from `logs/tv/d129_single_column_tv_guide_probe.txt`:

- `guide_row_count: 4`
- `full_width_row_count: 4`
- `one_column: True`
- `now_row_count: 3`
- `guide_unavailable_row_count: 1`
- `marked_incorrect_visible_count: 0`

Conclusion: the requested TV result presentation is runtime validated as a
single vertical column of full-width guide rows. Current-programme data was
visible on three measured rows and absence of guide data was represented
explicitly on one row. This accepts D-129 and preserves D-128 as superseded.
