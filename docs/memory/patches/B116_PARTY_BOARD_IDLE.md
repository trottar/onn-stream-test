---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: 8fa398c8 (this repo); 820673c (the board's repo)
---

# B116 — the board draws at 10 fps while the hub's mini game is on the TV (the board's own script)

**Result:** `evidence/B116_PARTY_BOARD_IDLE_2026-11-16.md`.

- **Files (the board's repo, uncommitted there — the user commits):** `minigames/hub_minigame.gd` (sha256
  `4706a28b…`), `checks/hub_minigame_check.gd` (sha256 `c09036b7…`, PASS 34 assertions);
  `evidence/b116_2026-11-16/b116_board.diff` (applies on `820673c`). **This repo:** `tests/b111_party_board/test_b111.py`
  (the counts 34 / 23, eight end calls, the fake hub's "silent" and "teardown" scenarios);
  `evidence/b116_2026-11-16/b116_this_repo_test.diff` (applies after `b115.diff`).
- **The user, in the board's repo:** `git add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m
  "Hub mini game: the board draws at 10 fps while the hub's game is on the TV, with its check"`.
- **Switch:** none on the hub; the board's script caps only while it waits for a hub mini game.
- **Rollback:** in the board's repo, `git apply -R` the board diff (or revert its commit); here `git apply -R` the test diff.
