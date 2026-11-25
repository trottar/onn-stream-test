---
memory_schema: 1
as_of: 2026-11-25
status: BUILT by Cowork (not session B) — B223's fix only: bench's expected numbers for a score ending on a surveyed title. Session B's queue BT stopped at its 25-minute limit with the sweep read and nothing built (SESSION_B_DONE_2026-11-25BT.md); its sweep found this one read of an old record and no other in bench, solo or close. Nothing adopted
---

# B223 — bench reads a surveyed title's expected scores from the regions' label record

**The fault (session A, ADD_T92_2026-11-25.md):** `cmd_bench` took a score ending's expected numbers from
`_numbers()` → the old path's `label.json`. An ending only the new path's label read (`regions_label.json`) gave
`None`, and `max(None)` ended bench in a TypeError with no verdict.

**The change (`tools/party_add_game.py`, two places):**
- `_bench_numbers(code, b, role)`: a surveyed title → the regions' label record (`"03-01"` → `[3, 1]`), never the old
  `label.json`; a title without a survey → `_numbers()`, as before; `None` when there is no reading.
- `cmd_bench`: no reading for an ending → a cell not met ("the label's reading"), the stage goes on and ends with its
  verdict and page — never a traceback.

**Why Cowork made it:** session B's limit was spent on reading; the fix is the one B's own design names, and the
user had waited two days on this title. No bar, gate, rule file or hub code changed.

**Test:** `tests/b223_bench_numbers/test_b223.py` (5 tests, no hub, no title): the regions' record read; a stale old
record never read; no old record at all; no reading → None; a title without a survey as before. OK on the changed
tool; 5 errors on the tool before the change.

**Not done (session B's own list):** `_expected()` can still raise a KeyError for a letters title whose sidecar
lacks an ending; the callees of `_held_ready`, `_scratch_load`, `_token` and `party_rows` were not read in the sweep.
