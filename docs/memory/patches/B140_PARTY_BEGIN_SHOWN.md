---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: c1a66bc9 (this repo) + B139's diff
---

# B140 — the paused begin made sure of before it is read (PRIVYHUB_PARTY=1)

**Result:** `evidence/B140_PARTY_BEGIN_SHOWN_2026-11-17.md`.

- **Files:** `companion/party_minigame.py` (`_grab`, `_moved`, `_advance` in `ADVANCE_STEPS` until the window moved
  `BEGIN_MOVED` from its pre-load grab or the start is read, the cap; `_prepare`'s pre-load grab, the row's new fields,
  `NO_BEGIN`), `tests/b140_party_begin_shown/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the fake title's
  `show_after`, its steady boot / fight pictures, the 0 / 2 / 12 / never cases and the ways back),
  `tests/b137_party_no_press/test_b137.py` (the N64-shaped case: 0 frames); `evidence/b140_2026-11-17/b140.diff`
  (applies after b139.diff).
- **Switch:** as B139; a start without `hold` → B110's order.
- **Rollback:** `git apply -R` b141.diff, then b140.diff (B137's fixed 2 frames back).
