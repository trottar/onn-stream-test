---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B80 — PS2 widescreen / no-interlacing / 60-fps patches per title (NOT adopted; inside `PRIVYHUB_PS2=1`, `PRIVYHUB_PS2_PATCHES=0` = today; client `debug.privyhub.ps2_patches=0`)

**Result:** `evidence/B80_PS2_PATCHES_2026-11-09.md`.

- **Apply:** `git apply evidence/b80_2026-11-09/b80.diff`, after `b79.diff`.
- **Live:** the host at the next restart (details' `ps2_patches`, the `ps2-patches` action, the game settings file at
  launch); the client with the queue AC APK (Extras → "Patches…").
- **Off:** `PRIVYHUB_PS2_PATCHES=0`; `debug.privyhub.ps2_patches=0`.
- **Writes outside the code:** `data/games/ps2/title_ids.json` (learned from PCSX2's logs), `…/patch_toggles.json`,
  and `config/PCSX2/gamesettings/<CRC>.ini` + `<SERIAL>_<CRC>.ini` for a title with toggles.
- **Rollback:** `git apply -R` in order; a written game settings file stays (delete it by hand to drop the toggles).
