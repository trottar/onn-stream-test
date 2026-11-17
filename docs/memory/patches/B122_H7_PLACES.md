---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: cb16e0c8
---

# B122 — the end-screen learner reads a place for every player (spec version 3)

**Result:** `evidence/B122_H7_PLACES_2026-11-17.md`.

- **Files:** `tools/h7_endscreen.py` (version 3: place rows learnt from labels alone — one screen per screen class, the
  row's spacing and cells from the between- / within-place variance, one reference per place pooled over the columns;
  a read with `places`, `unknown` for any unread or repeated place; `Ended` on the whole row; `score_places`; replay with
  places; versions 2 and 3 load), `tests/b122_h7_places/test_b122.py` (new); `evidence/b122_2026-11-17/b122.diff`
  (applies on `cb16e0c8`).
- **Switch:** labels whose end classes are place rows learn version 3; any other labels learn version 2 by today's code
  (T88's arrangement 3 identical with HEAD's tool).
- **Live:** the hub imports the tool only with `PRIVYHUB_H7=1`; not adopted.
- **Rollback:** `git apply -R` B124's, B123's, then this diff (a version-3 spec then refused as "not an end-screen spec
  this tool reads").
