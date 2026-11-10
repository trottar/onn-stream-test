---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B81 — the drop-in folders: the user's PS2 `.pnach` per game, the user's own `.cht` on PS1 / SNES (NOT adopted; default on, `PRIVYHUB_CHEAT_DROPINS=0` = today)

**Result:** `evidence/B81_CHEAT_DROPINS_2026-11-09.md`; the user's guide `docs/CHEATS.md`.

- **Apply:** `git apply evidence/b81_2026-11-09/b81.diff`, after `b80.diff` (it includes `docs/CHEATS.md`).
- **Live:** at the companion's next restart: the folders appear (empty) at the first Cheats list; files the user adds
  show in Extras → Cheats. No client change.
- **Off:** `PRIVYHUB_CHEAT_DROPINS=0`.
- **Writes outside the code:** the empty folders; on a PS2 cheat launch `config/PCSX2/cheats/<SERIAL>_<CRC>.pnach`
  and B80's game settings file.
- **Rollback:** `git apply -R` in order (81 first). The folders and any staged file stay.
