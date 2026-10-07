---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
durable_memory_updated: true
---

# E3-S4: the SNES core by name, behind `PRIVYHUB_SNES_CORE=<core>` (the 2026-10-06 prepared diff, now applied)

## Purpose

E3-S4 (`handoffs/E3-S4_SNES_LIGHTER_CORE_TASK.md`, record
`evidence/E3_S4_SNES_LIGHTER_CORE_2026-10-07.md`, which supersedes the
2026-10-06 NOT RUN record). The user placed `snes9x_libretro.so` in the
cores directory by hand on 2026-10-07.

**NOT ADOPTED (the user's decision; the core is also a look).**

## Change

`companion/games/emulator_manager.py`, `_resolve_game` (+7 lines; diff
`evidence/e3_s4_2026-10-07/e3_s4_snes_core.diff`, identical to
`evidence/e3_s4_2026-10-06/e3_s4_snes_core_PROPOSED_NOT_APPLIED.diff`):

- With `PRIVYHUB_SNES_CORE=<name>` (`[a-z0-9_]+`, else an
  `EmulatorError`), the SNES core is `<name>_libretro.so`, from the same
  cores directory.
- Absent: the configured core (`bsnes_libretro.so`), unchanged.

The runner's half (`SNES_CORENAMES`, the counter override in the core's
corename directory) is `E3-S4_SNES_CORE_RUNNER_SUPPORT.md` (2026-10-06).

**On the host, outside git, additive:** `runtime/emulators/retroarch/cores-linux/snes9x_libretro.so`
and its `.zip` (the user's). RetroArch itself wrote
`~/.config/retroarch/config/Snes9x/Snes9x.opt` (default core options) and
`data/games/retroarch/saves/Snes9x/` on first use.

## Validation

- `py_compile`.
- The smoke: the core loads (title "RetroArch Snes9x 1.63 fae2fea"),
  60.0 fps, PLAYING.
- The benchmark: see the record.

## Rollback

Unset the flag. To remove the code, reverse `e3_s4_snes_core.diff`. The
`.so` and RetroArch's `Snes9x/` dirs may stay; bsnes never reads them.
