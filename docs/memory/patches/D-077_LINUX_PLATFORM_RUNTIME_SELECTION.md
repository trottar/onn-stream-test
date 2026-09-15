# D-077 Linux platform-aware RetroArch runtime selection

Date: 2026-09-15
Status after successful installer validation: **NORMAL-PATH RUNTIME SELECTION VALIDATED / ONN E2E PENDING**

## Purpose

Close the remaining production-path gap between the already validated Linux
RetroArch runtime and the normal `GamesPlugin -> EmulatorManager` launch path.

The pushed descriptor remains Windows-compatible by default. D-077 adds one
optional `platforms.linux` override containing only the validated Linux
RetroArch executable/core-directory and Linux core filenames. `EmulatorManager`
constructs one effective runtime config from that trusted descriptor before
readiness, core resolution, or launch uses it.

## Required invariant

`_resolve_game()` reads the selected core from `runtime["config"]["systems"]`.
Therefore D-077 must merge platform core overrides into the effective config;
changing only readiness/status metadata would be insufficient and could report
Linux readiness while attempting to launch a Windows `.dll` core.

## Linux selection

- RetroArch frontend: project-owned 1.22.2 AppImage already validated in Phase D;
- executable: `runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage`;
- cores directory: `runtime/emulators/retroarch/cores-linux`;
- NES: `fceumm_libretro.so`;
- SNES: `bsnes_libretro.so`;
- Genesis: `blastem_libretro.so`;
- PS1: `mednafen_psx_hw_libretro.so`.

## Compatibility behavior

- existing Windows `retroarch` fields and `.dll` system cores remain the base
  descriptor and are unchanged;
- descriptors without `platforms` retain prior behavior;
- an incomplete/malformed platform override fails closed;
- unknown platform override core names are rejected;
- game/content trust boundaries and project-root path validation are unchanged.

## Intentionally unchanged

- `GamesPlugin` launch ordering;
- EmulatorManager lifecycle, Save/Load/Pause/End and cheat/mod/profile behavior;
- D-074 Linux exact-window x11grab/VAAPI video;
- D-075R1 Linux PulseAudio/PHA1 scheduler path;
- D-076 Linux PHI1/uinput controller backend;
- Android code/protocols;
- FEC/wire formats;
- host telemetry;
- persistent Linux service/device permissions.

## Validation gate

The installer retains D-077 only when all of the following pass:

1. exact predecessor source/config/memory blob checks;
2. Python compilation;
3. JSON validation;
4. isolated fixture proving Linux override selection and preservation of the
   Windows base mapping;
5. live read-only normal-path probe proving `EmulatorManager(project_root)`
   selects the installed Linux AppImage and all four `.so` cores with
   `ready=True`;
6. `git diff --check`.

No game is launched by the D-077 validation probe. After D-077 passes, the next
acceptance boundary is the integrated onn Linux E2E session.
