---
memory_schema: 1
as_of: 2026-09-16
status: development-evidence
---

# D-085 Linux udev D-pad evidence

## Older validated reference

Phase-A Windows evidence reached actual normal gameplay:
- 1P Crash Bash gameplay regression confirmed;
- 2P independent gameplay confirmed;
- final four-player gameplay confirmed after PS1 multitap topology was handled.

## Linux validation gap

D-076's own patch record separates host-side managed validation from still
required onn gameplay validation. Its host result proved P1-P4 creation and
RetroArch configuration, live PHI1 updates, meta controls, Save/Load, graceful
stop, and pad cleanup. It did not prove each gameplay binding.

## Raw Linux measurement

Baseline 42 measured:
- axis 0 ABS_X
- axis 1 ABS_Y
- axis 2 ABS_Z
- axis 3 ABS_RX
- axis 4 ABS_RY
- axis 5 ABS_RZ
- axis 6 ABS_HAT0X
- axis 7 ABS_HAT0Y

That measurement remains correct.

## Fault

The four project RetroArch udev profiles used ordinary directional axis binds
`-7/+7/-6/+6` for the D-pad. RetroArch udev represents ABS_HAT directions with
`h0up/h0down/h0left/h0right` button tokens.

The same incorrect assumption was inherited by D-084's Linux A8 translator.

## Change boundary

Correct only the RetroArch frontend translation:
- four project udev autoconfig files;
- Linux A8 D-pad source translation;
- deterministic A8 probe expectations.

Unchanged:
- Android input;
- PHI1;
- Linux UInput capabilities/event generation;
- Windows ViGEm/XInput;
- analog stick/trigger udev indexes;
- PS1 Digital/DualShock profile selection;
- save/meta controls;
- A/V/networking.
