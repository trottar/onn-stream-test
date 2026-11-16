---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: 8fa398c8
---

# B114 — the party mini game can no longer hang the companion, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1

**Result:** `evidence/B114_PARTY_MINIGAME_HANG_2026-11-16.md`.

- **Files:** `companion/party_minigame.py` (the start on its own actor: no lock across a launch, a stream start or
  stop, or a wait on another thread; the taken calls; the stuck-start give-up; END always), `companion/plugins/games.py`
  (two blocks: `status` / `native-stream-status` bounded with a snapshot; Home / RESUME / END taken onto the mini
  game's queue — both only under `_party_minigame is not None`), `tests/b114_party_minigame_hang/` (new);
  `evidence/b114_2026-11-16/b114.diff` (applies on `8fa398c8`).
- **The lock it removes:** the manager's lock held across the stream switch, whose end waits on the live bitrate
  controller's lock, held by a client-health report waiting on the manager's lock.
- **Switch:** both flags → the four party routes as B110 with the properties above; either absent → today, proved
  through the real HTTP routes against `8fa398c8`'s companion (four flag combinations).
- **Live:** not adopted; PP-H3b sets both bench flags for its sitting only (twenty lines).
- **Rollback:** `git apply -R` B116's test diff, B115's diff, then this one.
