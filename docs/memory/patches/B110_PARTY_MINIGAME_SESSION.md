---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: 0a3d78e2
---

# B110 — the hub's party mini game (an emulator title played from inside the board), behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1

**Result:** `evidence/B110_PARTY_MINIGAME_SESSION_2026-11-16.md` (and B111's board files, B112's bench).

- **Files:** `companion/party_minigame.py` (new), `companion/plugins/games.py` (four routes), `companion/games/
  emulator_manager.py` (the board's session set aside / back, the stop hook, the refusals widened),
  `companion/native_session_io.py` (the pads' route, None = today), `tests/b110_party_minigame/test_b110.py`,
  `tests/b111_party_board/test_b111.py` (new); `evidence/b110_2026-11-16/b110.diff` (applies on `0a3d78e2`) and
  `evidence/b111_2026-11-16/b111_test.diff`.
- **Switch:** both flags → `GET party-minigames`, `POST party-minigame-start?id=&seats=`, `GET party-minigame-result`,
  `POST party-minigame-end`; either absent → today, proved byte for byte through the real HTTP routes against
  `0a3d78e2`'s companion (four flag combinations).
- **Needs:** in the rules folder per title: the version-2 spec, the kept begin state, `<game id>.party.json`
  (`{"players": n, "scores": {end class: [n numbers]}}`); the board's `minigames/hub_minigame.gd` (B111).
- **Live:** not adopted; PP-H3 sets both bench flags for its sitting only (twenty lines).
- **Rollback:** `git apply -R` B112's diff, then B110's; `logs/games/party.jsonl` is git-ignored.
