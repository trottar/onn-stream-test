---
memory_schema: 1
as_of: 2026-09-16
status: development-evidence
---

# D-084 Linux A8 platform-adapter evidence

## Root cause

The current A8 adapter contains comments and tables explicitly tied to the
validated PHI1 -> ViGEm/XInput path. Its numeric source tables are correct for
Windows but were still selected after D-076 changed the Linux frontend to
uinput/udev.

The current project-owned Linux P1 autoconfig is the authoritative frontend map:

- `input_b_btn = "0"`
- `input_a_btn = "1"`
- `input_x_btn = "2"`
- `input_y_btn = "3"`
- `input_select_btn = "6"`
- `input_start_btn = "7"`
- `input_l2_axis = "+2"`
- `input_r2_axis = "+5"`
- D-pad X/Y axes = 6/7
- left stick X/Y axes = 0/1
- right stick X/Y axes = 3/4

Combined with D-076's canonical mapping
A/B/X/Y -> BTN_SOUTH/BTN_EAST/BTN_WEST/BTN_NORTH, this means canonical physical
X/Y correspond to Linux joystick indices 3/2, while the RetroPad autoconfig
targets X/Y use 2/3. That distinction is exactly what A8's semantic profile
layer is meant to preserve.

## Fix boundary

Only the final canonical-source -> RetroArch-bind adapter becomes
platform-specific.

Unchanged:
- input profile schema/storage;
- Android A8 editor;
- PHI1 wire format;
- Android physical-controller transport;
- Windows ViGEm backend and Windows A8 translation;
- Linux uinput event generation;
- RetroArch device enumeration/autoconfig;
- PS1 Digital/DualShock device selection;
- Save/Load/Pause/Resume/End;
- video/audio/network paths.

## Acceptance

Deterministic acceptance:
- updated A8 adapter probe passes on Linux;
- profile/config probe artifacts restore byte-for-byte;
- Python compilation passes;
- `git diff --check` passes.

Runtime acceptance:
- restart companion;
- launch an existing custom-profile game;
- verify the intended gameplay permutation on the onn.
