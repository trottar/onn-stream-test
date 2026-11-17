---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: d321b2d (the board's repo; this repo not touched by B135)
---

# B135 — the board's script: choose → load, ready or practise → play (the board's repo, my two files)

**Result:** `evidence/B135_BOARD_CHOOSE_LOAD_READY_2026-11-17.md`.

- **Files (the board's repo, uncommitted there):** `minigames/hub_minigame.gd` (sha256 `e580c3e1…`),
  `checks/hub_minigame_check.gd` (sha256 `76018a20…`, PASS 81); `evidence/b135_2026-11-17/b135_board.diff` (applies on
  `d321b2d`).
- **The user, in the board's repo:** `git add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m
  "Hub mini game: choose, load screen, ready or practise, then play - the hub prepares behind the board, with its check"`.
- **Switch:** the stage's methods — a presenter without the screens plays as before (no `hold`).
- **Rollback:** revert that commit.
