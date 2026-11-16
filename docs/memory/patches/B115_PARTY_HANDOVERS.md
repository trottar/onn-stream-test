---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: 8fa398c8
---

# B115 — the mini game's hand-overs made planned, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1

**Result:** `evidence/B115_PARTY_HANDOVERS_2026-11-16.md`.

- **Files:** `companion/party_minigame.py` (the way back: the stream switched to the board's own window, then the title
  stopped; both ways the stream's start for the window's own pid; the planned-switch window on the recovery; the
  bitrate told it is no recovery restart), `companion/stall_signal.py` (one block: a stall / stall end inside a planned
  window not taken — reads `recovery._planned_switch`, which only the mini-game layer sets; absent → today's code
  path), `companion/plugins/games.py` (the desync route: the same, under `_party_minigame is not None`),
  `tests/b115_party_handovers/` (new); `evidence/b115_2026-11-16/b115.diff` (applies on `8fa398c8` + `b114.diff`).
- **Switch:** both flags → planned hand-overs; either absent → today (B114's flag test on the tree; the stall worker's
  suites green).
- **Live:** not adopted; PP-H3b only.
- **Rollback:** `git apply -R` B116's test diff, then this one (B114's stays).
