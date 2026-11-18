---
memory_schema: 1
as_of: 2026-11-18
baseline_commit: 246c67da (this repo) + B143's and B144's diffs; the board's repo 4140949
---

# B145 — Select through a practice; the load screen behind a practice; the board's log lines

**Result:** `evidence/B145_PARTY_SMALL_THINGS_2026-11-18.md`.

- **This repo:** `companion/party_minigame.py` (`_handover` clears the Select hold only for a real go),
  `tests/b145_party_small_things/` (new), `tests/b114_party_minigame_hang/b114_scenario.py` (the practice case in
  `nopress`), `tests/b111_party_board/test_b111.py` (the check's counts 89 / 63, the lines);
  `evidence/b145_2026-11-18/b145.diff` (applies after b144.diff).
- **The board's repo (my two files, uncommitted there):** `minigames/hub_minigame.gd` (the load screen shown again at
  a practice's hand-over; `cards <n>, chose <0 | 1 | random>` and `start` / `practice` lines),
  `checks/hub_minigame_check.gd` (PASS 89); `evidence/b145_2026-11-18/b145_board.diff` (against `4140949`).
- **Switch:** the hub's part behind `PRIVYHUB_PARTY=1`; the board's part only with a stage that has the screens (a
  stage without them plays as before).
- **Rollback:** `git apply -R evidence/b145_2026-11-18/b145.diff`; in the board's repo `git checkout --
  minigames/hub_minigame.gd checks/hub_minigame_check.gd` (to `4140949`'s).
