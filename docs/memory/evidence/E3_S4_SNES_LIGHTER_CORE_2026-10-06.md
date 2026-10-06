---
memory_schema: 1
as_of: 2026-10-06
baseline_commit: d9fdbdd
---

# E3-S4 — a lighter SNES core: NOT RUN (no lighter core available)

**Classification:**

- **NOT RUN (no lighter core available)**, by the task's own rule.
- None of the three candidates is installed on this host.
- The one fetch the task allows (`snes9x_libretro.so` from the libretro
  buildbot) **was refused by this session's permission policy before
  any request was sent**. It did not "fail twice" over the network:
  - no byte was downloaded;
  - no second attempt was made;
  - nothing was worked around. Downloading an external binary is the
    user's call.
- No benchmark ran. No pre-registration was hashed, because there was
  nothing to run. Nothing was adopted or committed.
- **bsnes and its files are untouched.** E2's final state holds.

**Context:**

- Task: `handoffs/E3-S4_SNES_LIGHTER_CORE_TASK.md`, queue item 4 ("4
  lighter core").
- Baseline commit: `d9fdbdd`.
- Files: `e3_s4_2026-10-06/`.
- Timeline: 06:38:39Z preconditions held (`precondition.json`); then the
  inventory; then the refused fetch.

## 1. Inventory (`e3_s4_2026-10-06/inventory.txt`)

- **Installed cores** (`runtime/emulators/retroarch/cores-linux`, the
  Linux `cores_directory` of `companion/games/config/emulators.json`):

  | core | bytes |
  | --- | --- |
  | `blastem_libretro.so` | 11,505,752 |
  | **`bsnes_libretro.so`** (`ab130614…b4f8`) | 5,914,928 |
  | `fceumm_libretro.so` | 4,461,880 |
  | `mednafen_psx_hw_libretro.so` | 18,251,664 |

  The only SNES core is bsnes.
- **The candidates, in the task's order:** `snes9x`, `snes9x2010`,
  `snes9x2005_plus`. None is installed, and a search of the host
  filesystem found no copy.
- **RetroArch's bundled `.info` files**, held in the AppImage home's
  `cores/`, which contains `.info` only:

  | core | corename | version | license |
  | --- | --- | --- | --- |
  | snes9x | "Snes9x" | 1.61 | **"Non-commercial"** |
  | snes9x2010 | "Snes9x 2010" | v1.52.4 | Non-commercial |
  | snes9x2005_plus | "Snes9x 2005 Plus" | v1.36 | Non-commercial |
  | bsnes, for comparison | | 115 | GPLv3 |

  **The licence is a point for the user's decision as much as the look.**
- **How the row selects the core today:**
  - `emulators.json` `platforms.linux.cores.snes = "bsnes_libretro.so"`;
  - `EmulatorManager._resolve_game` reads `system_config["core"]`;
  - the suite's counter override is
    `~/.config/retroarch/config/bsnes/Super Mario World (USA).cfg`,
    written and removed by the runner.
  - Saves are sorted per core (`data/games/retroarch/saves/bsnes/`), so
    another core would write only its own directory.
- **The one line that would select another**, prepared and **NOT
  APPLIED**: `e3_s4_snes_core_PROPOSED_NOT_APPLIED.diff`.
  - It sits in `_resolve_game`: with `PRIVYHUB_SNES_CORE=snes9x`, the
    SNES core is `snes9x_libretro.so` from the same cores directory.
  - Absent = bsnes, byte for byte.
  - The runner already supports it: `tools/e1_suite.py` puts the counter
    override in the core's corename directory (`SNES_CORENAMES`) and
    creates that directory.

## 2. To run it later (the user's choice)

1. Fetch the core yourself (the task's URL pattern, no tokens):
   `https://buildbot.libretro.com/nightly/linux/x86_64/latest/snes9x_libretro.so.zip`.
   Unzip it into `runtime/emulators/retroarch/cores-linux/`, and record
   the zip's and the `.so`'s sha256.
2. Apply the proposed diff.
3. Run the task as written: a 3-min smoke, the pre-registration hashed,
   then `--plan E1-SNES-STREAM:2:600:PRIVYHUB_SNES_CORE=snes9x`.
4. **For a look by hand:** set the flag in a drop-in, restart the unit,
   and launch Super Mario World from the launcher.
5. **Revert:** unset the flag. The `.so` may stay.

## 3. State at the end

- Unchanged from E3-S3's end:
  - manager none; environ exactly the live default;
  - no e3 drop-in; no game;
  - the PS1 files identical; **APK CONFIRMED** (06:38:39Z).
- No core was added; no config dir was created.
- No `nft`, no `sudo`, the Opal untouched.
- Git status: `logs/e3_s4_git_status.txt`.
