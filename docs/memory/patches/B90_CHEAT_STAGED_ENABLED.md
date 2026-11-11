---
memory_schema: 1
as_of: 2026-11-11
baseline_commit: d1df1f86
---

# B90 — the cheat launch without walking the list (only the session's cheats staged, enabled, applied by RetroArch at load, verified from its own evidence), and no game left running when the onn has hung up (NOT adopted; default on, `PRIVYHUB_CHEAT_STAGED=0` = today)

**Result:** `evidence/B90_CHEAT_STAGED_ENABLED_2026-11-11.md`.

- **Apply:** `git apply evidence/b90_2026-11-11/b90.diff` (on `d1df1f86`; B91's diff is client-only and independent).
- **Live:** at the companion's next restart — every RetroArch cheat launch on Mupen64Plus-Next, snes9x and Beetle PSX
  HW; every games `launch` answer (the hang-up check).
- **Off:** `PRIVYHUB_CHEAT_STAGED=0` (today's whole file, `bsnes/` folder, walk and launch answer — 5 / 5 byte-equal to
  HEAD on the same fixtures).
- **Also changes:** `tests/b87_cheat_ready/test_b87.py` pins `PRIVYHUB_CHEAT_STAGED=0` (one line: that suite tests the
  walk; `tests/b90_cheat_staged/` tests the staged path).
- **Rollback:** `git apply -R evidence/b90_2026-11-11/b90.diff`.
