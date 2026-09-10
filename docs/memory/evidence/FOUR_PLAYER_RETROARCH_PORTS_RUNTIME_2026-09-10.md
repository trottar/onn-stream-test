---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Four-Player RetroArch Port Runtime Evidence — 2026-09-10

## Result

`RETROARCH_FOUR_PLAYER_PORTS_CONFIRMED`

A fresh normal PrivyHub game session exposed all four already-proven ViGEm/XInput devices to RetroArch as ports 1 through 4.

## Measurements

- Live host XInput slots during probe: 1, 2, 3, 4.
- RetroArch startup log age: 11.7 seconds.
- Xbox autoconfiguration observed in ports 1, 2, 3, and 4.
- RetroArch selected the `xinput` joypad driver.
- XInput startup fallback: false.
- Probe modified no production files and logged no network addresses.

## Interpretation

This closes the four-player transport/device-enumeration chain below the A8 gameplay-mapping layer:

`Android InputDevice -> PHI1 -> ViGEm/XInput slots 1-4 -> RetroArch ports 1-4`.

It does not by itself validate P3/P4 named input-profile storage/editor behavior, generated P3/P4 session remaps, or four-player gameplay/core multitap behavior. Those remain separate acceptance steps.

The exact raw probe output is retained at `evidence/raw/four_player_retroarch_ports_probe_2026-09-10.txt`.
