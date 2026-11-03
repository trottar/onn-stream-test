# B34 settle — the PS1 pad setup, read-only (nothing changed)

Read 2026-10-31 ~17:45Z. Sources: `companion/games/emulator_manager.py` and `companion/games/config/emulators.json`
(the tree); `data/games/retroarch/controller_overrides.json` (the per-title overrides; read, not written); the
RetroArch Beetle PSX HW core-options files (the default `.opt` and nine per-title `.opt`; read, not written); the trip
read's copies (`evidence/trip_r2_2026-10-31/copies/`: `companion_journal.txt`, `game_logs/`), read only. Titles are
named by class; the football title is the one TRIP-R2 §3 names ("Blitz").

## How port 2 is set (the code)

- **The device type** is one per title: `controller_profile` in the title's override, else the system default.
  `emulators.json` → ps1: `controller_default: "digital"`; profiles `digital` = "PlayStation Controller"
  (libretro device 1) and `dualshock` = "DualShock" (517).
- **Port 2 always equals port 1:** at launch the core gets `--device=<n>:<device>` for ports 1-2, or for players 1-4
  with multitap (`emulator_manager.py:5485-5508`). There is no per-port choice.
- **Multitap** is per title: `ps1_multitap` in the override, `off` (default) or `port1`
  (`emulator_manager.py:2114-2200`). Port 2's multitap is always forced off (the four-player ceiling,
  `:2623-2624`). At launch the title's core-options file is written with `beetle_psx_hw_enable_multitap_port1` to
  match (`_prepare_ps1_multitap_options`, `:2483`).
- **The analog toggle** (`beetle_psx_hw_analog_toggle`) is `"disabled"` in the default and in all nine per-title
  options files, with the combo `l1+r1+select`. PrivyHub does not set it per title. Friday did not change it.

## Per title in the tree now (20 PS1 overrides; nine per-title core-options files)

- **Overrides (20 entries):** 15 have `controller_profile: dualshock`; 5 have `ps1_multitap: port1` (two of them
  with dualshock as well); 3 have `ps1_multitap: off` explicitly (one of them with dualshock). A title with no entry
  runs the defaults: digital, multitap off.
- **Core-options files:** multitap port 1 is `enabled` in 6 (the party, kart, racing and soccer class).
  It is `disabled` in the default, the football title and the car-combat title. Port 2 is `disabled` in all nine.
- **The football title:**
  - the override now reads `{"ps1_multitap": "off"}` and has no `controller_profile`, so it runs the system default
    **digital**;
  - its options file has multitap port 1 and port 2 `disabled` and the analog toggle `disabled`. The file is
    identical to the core default and was last written at its 03:34Z launch.

## Friday's four changes in 17 minutes (the journal's POSTs; the game logs' launch lines)

| UTC | the change (the client's request) | the next launch's log |
| --- | --- | --- |
| 01:07:54 | (first launch; nothing changed yet) | "Controller: PlayStation Controller (system_default)"; no multitap line |
| **01:15:33** | `ps1-multitap … enabled=true` (**multitap on, port 1**) | 01:15:41: "PS1 multitap: port1"; digital |
| **01:17:33** | `ps1-multitap … enabled=false` (**multitap off**) | (no launch in between) |
| **01:17:40** | `controller-profile … profile=dualshock` (**DualShock**) | 01:18:09: "Controller: DualShock (game_override)", "PS1 multitap: off"; the core: "Controller 1: DualShock", "Controller 2: DualShock" |
| **01:22:44** | `controller-profile … profile=digital` (**back to the digital pad**) | 01:23:05: "PlayStation Controller (system_default)", "PS1 multitap: off" |
| 03:32 / 03:34 | (no change) | both "PlayStation Controller (system_default)", "PS1 multitap: off" (the 35-min session) |

- TRIP-R2 §3 listed three steps because it counted 01:17:33 and 01:17:40 as one. The client sent four separate
  requests.
- The analog toggle was `disabled` throughout. It belongs to the core options and is not something Friday changed.
- **The final state** is the default setup: multitap off, digital "PlayStation Controller" on ports 1 and 2.
  The only override left is the explicit `ps1_multitap: off`. The 35-minute session at 03:34Z ran on it.

## The right setting for a two-player PS1 title without multitap

- **Multitap off** (`ps1_multitap: off`, or no override). With port 1's multitap on, the second player is on the
  tap's port 1-B, not on port 2, so a title that reads port 2 does not see player 2.
- **The same device type on both ports.** The code always gives port 2 the same type as port 1.
  - Use **digital "PlayStation Controller"** for a title that does not use the sticks. The football title is one.
  - Use DualShock only for a title that needs analog. With the analog toggle disabled, the pad cannot be switched
    to analog from the pad itself.
- **The two real pads on P1 and P2.** The host makes "PrivyHub Virtual Gamepad P1-P4", and RetroArch puts P1 on
  port 1 and P2 on port 2. A title without multitap reads only P1 and P2.
  - Today the client gives out slots in first-input order, any stick-axis device can take one, and the slots reset at
    every start. A real pad can therefore land on P3 or swap with the other.
  - B34's `debug.privyhub.pad_slots=stable` fixes the client side: gamepads only, in the system's controller-number
    order, kept across restarts.
- **Nothing in the config needs changing.** It already reads correctly for the football title. Friday's trouble was
  the slots, not the setting (inference, as TRIP-R2 §3).
