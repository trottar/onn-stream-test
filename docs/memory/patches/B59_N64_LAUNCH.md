---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: a8a505e5
---

# B59 — H1: N64 through RetroArch (behind `PRIVYHUB_N64=1`)

**Result: SETTLED + BUILT; `tests/n64_session` 28 green ×3; 7 mutations caught (M5 after a strengthened test); absent
= today PROVEN hunk by hunk.** Record: `evidence/B59_N64_LAUNCH_2026-11-08.md`.

- **Files:**
  - new: `companion/n64_session.py`, `companion/inplace_library.py`, `tools/n64_core_check.py`,
    `tools/n64_frames.py`, `tests/n64_session/`;
  - changed: `companion/games/emulator_manager.py`, `companion/plugins/games.py`, `companion/players_session.py`
    (one source value), `tools/diag_read.py` (one label).
- **Apply:** `git apply evidence/b59_2026-11-08/b59_code.diff` (applied to the tree, uncommitted).
- **Before it is live (A, the user's go):**
  1. the core `mupen64plus_next_libretro.so` in `runtime/emulators/retroarch/cores-linux/` (the buildbot zip, the
     sha256 recorded), then `python3 tools/n64_core_check.py --keys`;
  2. `N64_DIR=<the drive's N64 folder>` in the gitignored paths file;
  3. the bench drop-in `b59-n64.conf` (`PRIVYHUB_N64=1`) and a companion restart.
- **Rollback:**
  - reverse the diff;
  - remove the drop-in;
  - `~/.config/retroarch/config/Mupen64Plus-Next/` is then unread (it exists only after a first N64 launch).
