---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a96c816c
---

# B78 — N64 cheats from RetroArch's cheat database, wired as PS1's (NOT adopted; inside `PRIVYHUB_N64=1`, `PRIVYHUB_N64_CHEATS=0` = today)

**Result:** `evidence/B78_N64_CHEATS_2026-11-09.md`.

- **Apply:** `git apply evidence/b78_2026-11-09/b78.diff`, after `b77.diff`.
- **Live:** the cheat tool accepts `--system n64` (with `PRIVYHUB_N64=1` in its environment) once N64 titles have
  B76's records; the companion (next restart) stages an N64 cheat file for Mupen64Plus-Next. The onn's Cheats list is
  unchanged code.
- **Off:** `PRIVYHUB_N64_CHEATS=0` (or no `PRIVYHUB_N64`).
- **Writes outside the code:** the tool's usual files for N64 titles (user content, the manifest), only when run.
- **Rollback:** `git apply -R` in order.
