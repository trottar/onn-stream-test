---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: dbbc316b (this repo)
---

# B175 — a cell for a match the spec did not learn from

**Result:** `evidence/B175_ADD_GAME_LEFT_OUT_2026-11-20.md`.

- **Files:** `tools/party_add_game.py` (`_left_out_cells`, `_replay_all`: every ending's every save — grouped by match —
  read by the spec learnt without it, one cell `left out: <role>` per save, the replay's own bar `ended_within_s`; the
  line for one more save follows it; the spec written still from every save); `tests/b175_left_out/` (new);
  `tests/b171_more_saves/near_capture.py` (a cursor and a begin-only mark for the made-up titles); B157's, B163's,
  B171's tests updated (disclosed). The diff: `evidence/b175_2026-11-20/b175_b176.diff` (with B176).
- **Switch:** none — the tool; no bar lowered or changed; the learner not changed; rehearse carries the cell, bench
  unchanged (it learns nothing).
- **Rollback:** `git apply -R evidence/b175_2026-11-20/b175_b176.diff`.
