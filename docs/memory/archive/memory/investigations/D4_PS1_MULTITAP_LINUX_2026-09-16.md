---
memory_schema: 1
as_of: 2026-09-16
status: active
scope: Phase D / PS1 multiplayer
---

# D4 PS1 multitap parity on Linux

## Symptom

User reports PS1 multitap does not work on the Linux runtime.

No narrower failure classification is established yet. Do not infer whether the
failure is storage, core-option generation, libretro device assignment,
RetroArch port configuration, physical controller routing, or in-game topology
until measured.

## Known-good reference

Windows Phase A previously runtime validated manual Multitap On/Off using CTR:

- per-game override `ps1_multitap = port1`;
- `beetle_psx_hw_enable_multitap_port1 = enabled`;
- `beetle_psx_hw_enable_multitap_port2 = disabled`;
- four host controller slots present;
- Players 3/4 available;
- all four controllers independent;
- `PS1_MULTITAP_ONOFF_CTR_CONFIRMED`.

That reference is behavioral evidence, not a requirement to retain Windows
XInput implementation details.

## Linux lower boundary already accepted

D-085 runtime acceptance across three games / three profiles means the ordinary
controller path should be preserved while multitap is investigated:

- Android/PHI1;
- Linux uinput generation;
- RetroArch udev autoconfig;
- default and named A8 gameplay mapping.

## Next diagnostic

Adapt the old semantic multitap runtime probe to Linux. In one representative
multitap launch, capture:

1. game ID;
2. stored `controller_overrides.json` record and `ps1_multitap` value;
3. actual content-specific Beetle PSX HW `.opt` path;
4. exact values of:
   - `beetle_psx_hw_enable_multitap_port1`
   - `beetle_psx_hw_enable_multitap_port2`
5. P1-P4 PrivyHub virtual pads present before RetroArch input initialization;
6. RetroArch configuration result for ports 1-4;
7. whether Players 3/4 are available in-game;
8. whether four physical controllers remain independently routed.

Classify the first boundary that differs from the Windows behavioral reference.
Make no production change until that evidence exists.
