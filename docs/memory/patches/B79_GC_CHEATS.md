---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B79 — GameCube cheats from Dolphin's bundled codes, no download (NOT adopted; inside `PRIVYHUB_GAMECUBE=1`, `PRIVYHUB_GC_CHEATS=0` = today)

**Result:** `evidence/B79_GC_CHEATS_2026-11-09.md`.

- **Apply:** `git apply evidence/b79_2026-11-09/b79.diff`, after `b78.diff`.
- **Live:** at the companion's next restart: Extras → Cheats on a GameCube title lists Dolphin's own code names for
  its disc id; a cheat launch writes the user dir's `GameSettings/<id>.ini` enabled sections and `EnableCheats =
  True` for that launch. No client change.
- **Off:** `PRIVYHUB_GC_CHEATS=0`.
- **Writes outside the code:** `data/games/gamecube/user/GameSettings/<id>.ini` on a cheat launch only (never
  deleted; inert on a plain launch).
- **Rollback:** `git apply -R` in order. A written user file stays, inert with `EnableCheats = False`.
