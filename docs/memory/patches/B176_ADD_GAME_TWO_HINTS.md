---
memory_schema: 1
as_of: 2026-11-20
baseline_commit: dbbc316b (this repo)
---

# B176 — a save in the wrong role; the same match saved twice

**Result:** in `evidence/B175_ADD_GAME_LEFT_OUT_2026-11-20.md` (§B176).

- **Files:** `tools/party_add_game.py` (`_matches` with `SAME_PICTURE` (1.0 grey, H7-V1's kept number; not a bar) and the
  cell `no two saves of one ending the same picture`; `_held_out_wrong`, `_relabel_fixes` and the wrong-role rule; the
  one line in the order wrong role, the same match twice, one more save, the cap; `recorded.line`); tests in
  `tests/b175_left_out/`. In `evidence/b175_2026-11-20/b175_b176.diff` with B175.
- **Switch:** none — the tool.
- **Rollback:** with B175's diff.
