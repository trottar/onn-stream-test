---
memory_schema: 1
as_of: 2026-11-17
baseline_commit: cb16e0c8 (this repo); f1adc44 (the board's repo)
---

# B124 — four seats on the board, and who plays what (PRIVYHUB_PARTY=1)

**Result:** `evidence/B124_PARTY_FOUR_SEATS_2026-11-17.md`.

- **Files (this repo):** `companion/players_session.py`, `companion/player_count.py` (the board — or a mini game that
  set it aside — answers four players / four ports; reached only with the party module loaded),
  `companion/party_session.py` (`PRIVYPARTY_ON_HUB=1` in the board's launch environment),
  `tests/b124_party_four_seats/test_b124.py` (new), `tests/b114_party_minigame_hang/` (the harness's `four` mode, the
  flag test's ports), `tests/b111_party_board/test_b111.py`; `evidence/b124_2026-11-17/b124.diff` (applies after
  `b123.diff`).
- **Files (the board's repo, uncommitted there — the user commits):** `minigames/hub_minigame.gd` (sha256 `e246478b…`,
  `MAX_PLAYERS` 4), `checks/hub_minigame_check.gd` (sha256 `b016167d…`, PASS 40); `b124_board.diff` (applies on
  `f1adc44`). **The PC side's one line** in `game/minigame_picker.gd` (not written): in the record.
- **The user, in the board's repo:** `git add minigames/hub_minigame.gd checks/hub_minigame_check.gd && git commit -m
  "Hub mini game: four players get the hub's four-player games, two its two-player ones, with its check"`.
- **Switch:** `PRIVYHUB_PARTY=1` (and `PRIVYHUB_H7=1` for the mini games); either absent → today.
- **Rollback:** `git apply -R` this diff; in the board's repo, revert its commit.
