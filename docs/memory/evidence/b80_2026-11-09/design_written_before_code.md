# B80 — PS2 widescreen / no-interlacing / 60-fps patches per game (design, written and hashed before code)

**Knobs:** host inside `PRIVYHUB_PS2=1`; default on within it, `PRIVYHUB_PS2_PATCHES=0` = today. Client
`debug.privyhub.ps2_patches=0` = today's Extras (the entry only shows when the host offers patches anyway).

## What exists (read at HEAD and on the hub, as data)

- **PCSX2 2.8.2's bundle:** `usr/bin/resources/patches.zip` in the AppImage (read with `7z x -so` into memory,
  ~0.01 s): 4,709 `.pnach` files named `<SERIAL>_<CRC>.pnach` (a few by CRC only). Group names counted across the
  bundle: `[Widescreen 16:9]` 4,279, `[60 FPS]` 339, `[No-Interlacing]` 333 (others: `50 FPS`, `NTSC Mode`, …).
- **How PCSX2 enables them** (its binary's strings: `EnableWideScreenPatches`, `EnableNoInterlacingPatches`,
  `Widescreen 16:9`, `No-Interlacing`, `Patches`, `Enable`, `{}_{:08X}.ini`, `{:08X}.ini`, `gamesettings`): the
  widescreen group by `EnableWideScreenPatches`, the no-interlacing group by `EnableNoInterlacingPatches`, any other
  named group by `[Patches] Enable = <name>` in the game's settings file. The hub's `PCSX2.ini` has `EnablePatches =
  true`, both switches `false`.
- **The game's settings file:** `data/games/ps2/config/PCSX2/gamesettings/`. PCSX2's own log reads
  `gamesettings/<CRC>.ini` at the disc change — **12 of 12 kept logs** ("No game settings found (tried
  '…/gamesettings/<CRC>.ini')"), with a non-empty serial each time. Its binary also formats `<serial>_<CRC>.ini`.
- **The title's serial and CRC:** only PCSX2 knows them (a `.chd` needs decompressing). Its per-launch log (B53,
  `data/games/ps2/logs/`, kept 30 days) carries `Disc changed to <file name>.`, then `  Serial: <serial>` and
  `  CRC: <crc>`. **So a title's patches show after its first PrivyHub launch.**
- **The onn:** Extras = "Cheats", "Mods" (+ "Start on disc…" for a PS1 set); the details JSON reaches the launch
  dialog (B74 passes `discs`). **A client part is needed** (a new Extras entry).

## The change

**Host** — new `companion/ps2_patches.py`:
- `KNOB_ENV`, `enabled()`;
- `ids_from_logs(logs_dir)` → `{file name: (serial, crc)}` from PCSX2's logs (the last launch wins);
- `title_ids(project_root, game, logs_dir)` → `(serial, crc)` or None: the hub's own cache
  `data/games/ps2/title_ids.json` (keyed by the game id), filled from the logs by the title's file name, written
  atomically when it learns one (hub data, gitignored, never in a record);
- `bundle_groups(appimage, serial, crc, run)` → the group names of `<SERIAL>_<CRC>.pnach` in `patches.zip`
  (the zip read once per AppImage mtime into memory; nothing extracted);
- `available(groups)` → the subset of `["ws", "ni", "60"]` (`Widescreen 16:9`, `No-Interlacing`, `60 FPS`);
- the toggles per title: `data/games/ps2/patch_toggles.json` (`{game id: {"ws", "ni", "60"}}`), `get_toggles` /
  `set_toggles` (only the available ones can be on);
- `game_ini_text(toggles, extra=None)` → a marker comment, `[EmuCore]` `EnableWideScreenPatches` /
  `EnableNoInterlacingPatches`, and `[Patches] Enable = 60 FPS` when on (B81 adds its cheat keys through `extra`);
- `write_game_ini(gamesettings, serial, crc, text)` → `<CRC>.ini` (the name 2.8.2 was seen to read) and
  `<SERIAL>_<CRC>.ini`, the same text, atomically.
- `emulator_manager._launch_pcsx2`: knob on and the title's ids known and **a toggle record for the title** → the
  game ini written before the Popen and `PS2 patches: ws=on|off ni=… 60=…` in the game log. No record → nothing
  written, no line (today).
- `plugins/games.py`: `details` gets `ps2_patches: {"available": […], "on": […]}` only for a PS2 title with the
  knob on and at least one patch available; action **`ps2-patches`** (`id`, `ws`, `ni`, `fps60` as 0 / 1) stores
  the toggles and returns them (refused for a title without a patch).

**Client** — new `streaming/Ps2Patches.kt` + `MainActivity.kt`:
- `Ps2Patches.PROPERTY = "debug.privyhub.ps2_patches"`; the labels "Widescreen", "No interlacing", "60 fps"; the
  Extras entry **"Patches…"** only when the details' `ps2_patches.available` is non-empty and the property is not 0;
- the entry opens a multi-choice of the available ones, the current state ticked, "Save" posts
  `/plugins/games/ps2-patches?id=…&ws=…&ni=…&fps60=…`; the launch is unchanged (the host reads the record);
- Extras' list built from the same labels in the same order: without patches it is today's array exactly.

## Tests

- host `tests/art_systems/test_b80.py`: the ids from fixture logs (the last launch wins; a title absent from the
  logs → None); the groups from a fixture zip; `available`; the toggles stored (an unavailable one refused); the
  ini's keys from the toggles; both file names; the PCSX2 launch (B49's rig) writes the ini and the line with a
  record, nothing without one, nothing with the knob 0; details: the key only with a patch; the action;
- client `B80Ps2PatchesTest.kt`: the entry's condition, the labels, the query, the parse of the details' arrays;
  today's Extras list without patches.
