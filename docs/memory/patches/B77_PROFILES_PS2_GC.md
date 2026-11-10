---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B77 — Input Profiles on PS2 and GameCube launches (NOT adopted; default on, `PRIVYHUB_PROFILES_EXT=0` = today)

**Result:** `evidence/B77_PROFILES_PS2_GC_2026-11-09.md`.

- **Apply:** `git apply evidence/b77_2026-11-09/b77.diff`, after `b76.diff`.
- **Live:** at the companion's next restart (inside `PRIVYHUB_PS2=1` / `PRIVYHUB_GAMECUBE=1`): a title's assigned
  Input Profile is written into PCSX2's `[PadN]` bindings / Dolphin's `GCPadNew.ini` at each launch. The Default
  profile writes today's files; one game-log line per launch says which profile applied (no name). No client change.
- **Off:** `PRIVYHUB_PROFILES_EXT=0`.
- **Writes outside the code:** none new (the same two files the launches already write).
- **Rollback:** `git apply -R` in order.
