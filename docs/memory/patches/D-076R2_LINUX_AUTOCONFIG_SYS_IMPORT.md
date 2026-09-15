# D-076R2 Linux managed RetroArch sys import correction

Date: 2026-09-15
Status: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**

## Purpose

Correct a deterministic D-076R1 implementation defect without changing the
D-076 controller architecture or D-076R1 path-resolution design.

## Fresh failure evidence

The first D-076R1 managed probe reached the production Linux controller preflight:

- controller active: true;
- backend: `linux_uinput`;
- players: 4;
- cleanup removed all virtual pads.

`EmulatorManager.launch()` then failed before RetroArch startup when
`_prepare_retroarch_session_config()` evaluated:

`sys.platform.startswith("linux")`

but `companion/games/emulator_manager.py` did not import `sys`.

Result: **D-076R1 IMPLEMENTATION DEFECT — MISSING STANDARD-LIBRARY IMPORT**

## Production correction

D-076R2 adds only the missing top-level `import sys` beside the existing standard
library imports in `companion/games/emulator_manager.py`.

The D-076R1 generated-session autoconfig-path block remains byte-for-byte
unchanged. No controller mapping, PHI1, Android, video/FEC, audio, RetroArch
persistent configuration, autoconfig profile, process cwd, or runtime descriptor
change is part of D-076R2.

## Runtime acceptance

Managed runtime revalidation passed. The generated session config resolved the
project-owned autoconfig path and P1-P4 configured in ports 1-4. Live PHI1,
Pause/Resume, raw RetroArch Save/Load evidence, graceful production End, and
cleanup passed. The probe final classifier was false only because its matcher
selected `.state.png` and it required the non-production controller `quit` chord.
Full onn E2E remains pending.
