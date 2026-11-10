---
memory_schema: 1
as_of: 2026-11-10
baseline_commit: 051bb4d0
---

# B87 — the N64 cheat launch: RetroArch's name for the cheat file, and a wait for RetroArch's evidence before any cheat command (NOT adopted; default on, `PRIVYHUB_CHEAT_READY=0` = today)

**Result:** `evidence/B87_N64_CHEAT_LAUNCH_2026-11-10.md`.

- **Apply:** `git apply evidence/b87_2026-11-10/b87.diff` (on `051bb4d0`).
- **Live:** at the companion's next restart (every RetroArch cheat launch).
- **Off:** `PRIVYHUB_CHEAT_READY=0`.
- **Rollback:** `git apply -R` in order (89, 88, 87).
