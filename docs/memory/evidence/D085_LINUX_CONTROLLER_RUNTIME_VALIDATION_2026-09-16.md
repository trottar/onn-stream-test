---
memory_schema: 1
as_of: 2026-09-16
status: runtime-validated
classification: LINUX_GAMEPLAY_CONTROLLER_PARITY_CONFIRMED_FOR_TESTED_PROFILES
---

# D-085 Linux gameplay controller runtime validation

## Runtime result

After D-085 was installed and the companion restarted, the user exercised:

- three different games;
- three different input profiles.

User acceptance: all three ran correctly.

This is integrated onn gameplay evidence, not only a host-side probe.

## Interpretation

The tested runtime path is accepted through:

`Android InputDevice -> PHI1 -> Linux uinput -> RetroArch udev -> Default/A8 profile -> core/game`

The result runtime-validates the D-085 Linux udev hat correction and provides
integrated acceptance for the D-084 platform-specific A8 adapter when combined
with D-085.

## Scope

Validated:
- representative default/autoconfig gameplay input;
- representative named input-profile gameplay;
- Linux uinput/udev integration in real game sessions.

Not established by this result alone:
- every game/core/control endpoint;
- PS1 four-player/multitap topology;
- NES/Genesis fixture coverage.

## Next regression

PS1 multitap/multiplayer currently does not work on Linux. Keep that as a
separate topology/session investigation above the now-validated lower controller
path.
