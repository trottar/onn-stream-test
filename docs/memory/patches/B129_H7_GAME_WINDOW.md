---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: 1fc0ced0 (this repo); the board's repo not touched
---

# B129 — the watcher reads the game's own window (PRIVYHUB_H7=1)

**Result:** `evidence/B129_H7_GAME_WINDOW_2026-11-17.md`.

- **Files:** `companion/h7_minigame.py` (`WindowPicture`: the window owned by the game's own process — `getwindowpid`,
  the stream's check —, found again for every new game process, after a failed grab and every `REFIND_S` = 10 s; none →
  a picture failure, no read), `tests/b129_h7_game_window/` (new: `test_b129.py`, `b129_scenario.py`);
  `evidence/b129_2026-11-17/b129.diff` (applies on `1fc0ced0`; it also carries B130's hunks in the same file).
- **Switch:** `PRIVYHUB_H7=1`; absent → today (the module is not imported).
- **Rollback:** `git apply -R` the diffs in reverse order (b131, b130, b129).
