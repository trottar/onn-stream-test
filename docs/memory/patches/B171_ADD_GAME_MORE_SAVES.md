---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: 6d4a6c44 (this repo)
---

# B171 — several saves per ending; learn says which save to add

**Result:** `evidence/B171_ADD_GAME_MORE_SAVES_2026-11-20.md`.

- **Files:** `tools/party_add_game.py` (roles `end_P<k>_2..4` / `end_r<row>_2..4`, `SAVES_PER_ENDING_MAX = 4` beside
  `BARS` — not a bar; register's two per ending; learn's one plain line and `recorded`; pictures kept per save; rehearse's
  usable kept extras as sources, its collected saves kept, learn's line carried; bench reads each save by its class);
  `tests/b171_more_saves/` (new: `near_capture.py`, `test_b171.py`); B157's, B162's, B163's, B169's tests updated (disclosed
  in the record). The diff: `evidence/b171_2026-11-20/b171_b172.diff` (with B172).
- **Switch:** none — the tool; no companion change; no bar changed; the learner (`tools/h7_endscreen.py`) not changed.
- **Rollback:** `git apply -R evidence/b171_2026-11-20/b171_b172.diff`. A title's add_game folder may then hold a
  `kept/` copy of a rehearse save (the tool's own, off the repo) that the old tool ignores.
