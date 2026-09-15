# D-076 Linux uinput controller backend

Date: 2026-09-15
Status: **HOST-SIDE MANAGED RUNTIME VALIDATED / ONN E2E PENDING**

## Purpose

Add the Linux production controller-output backend without changing Android or
PHI1. Windows retains the existing ViGEm VX360 path.

## Evidence preceding the patch

- Baseline 42 measured the exact Linux joystick button/axis layout.
- Baseline 43 validated canonical PHI1/XUSB -> Linux uinput translation: 20/20
  controls, 40 packets, zero bad packets.
- Baseline 44 validated four pre-created PrivyHub uinput pads autoconfigure in
  RetroArch ports 1-4 with the udev joypad driver.
- Baseline 45 validated that the RetroArch autoconfig directory may be project
  relative, avoiding a machine-specific home path.

## Production change

`NativeControllerBridge` now chooses a host backend:

- Windows: existing project-local `vgamepad` / ViGEm VX360 devices.
- Linux/POSIX: `python3-evdev` UInput devices named
  `PrivyHub Virtual Gamepad P1` through `P4`.

The Linux mapping preserves canonical PHI1/XUSB semantics:

- A/B/X/Y -> BTN_SOUTH/BTN_EAST/BTN_WEST/BTN_NORTH;
- L1/R1 -> BTN_TL/BTN_TR;
- Back/Start/L3/R3 -> BTN_SELECT/BTN_START/BTN_THUMBL/BTN_THUMBR;
- LX/LY -> ABS_X/ABS_Y with XInput-to-Linux Y inversion;
- RX/RY -> ABS_RX/ABS_RY with Y inversion;
- LT/RT -> ABS_Z/ABS_RZ, 0..255;
- D-pad -> ABS_HAT0X/ABS_HAT0Y.

Timeout neutralization and companion-injected RetroArch meta-hotkey overlays are
preserved. Existing `vigem_updates*` status keys remain as compatibility aliases;
new backend-neutral `updates*` keys and `backend` identify Linux correctly.

The project Linux RetroArch config now selects `udev` and points at:

`data/games/retroarch/autoconfig`

Four project-owned udev profiles are installed there.

## Intentionally unchanged

- Android `NativeControllerSender.kt`;
- PHI1 v1 36-byte wire format;
- Windows ViGEm mapping and lifecycle;
- native video/FEC;
- native audio and D-075R1 scheduler behavior;
- EmulatorManager lifecycle;
- A8 named gameplay-profile semantics;
- host telemetry.

## Permission boundary

Production code does not invoke `sudo`. Current `/dev/uinput` permissions still
require the later durable service/device-permission design. Runtime validation of
D-076 may temporarily grant only the minimum uinput access needed for the probe.

## Isolated production-backend runtime result

The installed D-076 production controller bridge passed an isolated Linux
runtime probe:

- backend: `linux_uinput`;
- four production virtual pads created with P1-P4 names;
- one PHI1 update reached each player;
- 4 packets received, zero bad/rejected packets;
- backend-neutral and legacy ViGEm-named update counters both reported
  `[1, 1, 1, 1]`;
- staged Save hotkey emitted modifier-down, action-down, action-up,
  modifier-up;
- stop removed all four virtual pads.

Result: **D-076 ISOLATED PRODUCTION BACKEND RUNTIME VALIDATED**

Real managed RetroArch host integration subsequently passed under D-076R2.

## Runtime acceptance still required

1. real managed RetroArch launch sees P1-P4 before input initialization;
2. gameplay controls including triggers work;
3. Save/Load/Pause/End meta-hotkeys work through the Linux backend;
4. four-player ordering remains stable;
5. stop neutralizes and removes all four virtual devices;
6. validated Linux video/audio paths remain unaffected.

## D-076 managed-launch follow-up

The first real managed RetroArch probe found P1-P4 present before launch but not configured because the relative autoconfig directory was resolved from `executable.parent`. D-076R1 corrects only generated Linux session-path resolution. D-076 controller creation/mapping remains authoritative.

## D-076R2 managed-launch follow-up

D-076R1's first runtime revalidation failed before RetroArch launch due solely
to a missing `sys` import in EmulatorManager. D-076R2 fixes that deterministic
implementation defect; D-076 controller creation/mapping remains unchanged.

## Authoritative managed runtime result

D-076/R1/R2 passed host-side managed RetroArch validation: P1-P4 configured in
ports 1-4, live PHI1 updates were clean for all four players, Pause/Resume worked,
RetroArch logged a real 284304-byte slot-0 save and load, normal
`EmulatorManager.stop()` completed `SAVE_FILES` -> `OK` and graceful SIGTERM
return code 0, and all virtual pads were removed.

The probe's final false classification is not authoritative: it selected the
`.state.png` screenshot sidecar and required the optional controller `quit` chord.
Full onn E2E remains pending.
