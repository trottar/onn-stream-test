# B81 — the drop-in folders: PS2 `.pnach` per game; the user's own `.cht` on PS1 / SNES (design, hashed before code)

**Knob:** `PRIVYHUB_CHEAT_DROPINS` default on; `0` = today. The PS2 half is also inside `PRIVYHUB_PS2=1` (and uses
B80's game-settings writer, so `PRIVYHUB_PS2_PATCHES=0` turns the PS2 half off with it). PS1 / SNES have no system
flag: with no file in the folders, everything is today's (the catalog gains nothing).

## What exists (read at HEAD and in this queue's B79 / B80)

- **PS1 / SNES:** the cheat list is `_cheat_catalog_unlocked(game)`: the manifest's sources (RetroArch's database
  files the tool fetched), each `{source_index, provider, filename, local_path, sha256, cheat_count, entries}`; it
  raises when `data/games/cheats.json` is missing. A launch stages `sources[i]` (re-read, sha-checked, refused when a
  cheat is pre-enabled) for the core and turns the ticked indexes on through RetroArch. Files in
  `data/games/user_content/<id>/cheats/` are listed (counted) only (A7.1). `data/games/retroarch/cheats/` does not
  exist on the hub.
- **PS2:** PCSX2 2.8.2 loads cheats from `config/PCSX2/cheats/<SERIAL>_<CRC>.pnach` (its log names the folder; its
  binary formats `{}_{:08X}{}.pnach`) when `EnableCheats` is on (global `false` on the hub). Labelled groups are
  enabled by `[Cheats] Enable = <group>` in the game's settings file; unlabelled codes "automatically activate"
  (its strings). B80 gives the title's serial / CRC (from PCSX2's logs) and writes `gamesettings/<CRC>.ini` +
  `<SERIAL>_<CRC>.ini`. B79 gives `_ext_cheat_catalog` (the onn's shape for non-RetroArch cheats, no profiles).

## The change

1. New `companion/cheat_dropins.py` (pure + small file reads):
   - `KNOB_ENV`, `enabled()`;
   - `retro_dir(root, system, stem)` = `data/games/retroarch/cheats/<system>/<title stem>/` (systems `ps1`, `snes`);
     `user_cht_files(root, game)` → the `.cht` files there, sorted by name, hidden names skipped;
   - `ps2_dir(root, serial)` = the paths file's `PS2_CHEATS_DIR=` folder if named, else `data/games/ps2/cheats`,
     then `<serial>/`; `pnach_files(...)` → its `.pnach` files sorted by name;
   - `pnach_groups(text)` → the `[group]` names (for `[Cheats] Enable`);
   - `stage_pnach(cheats_dir, serial, crc, files)` → one `<SERIAL>_<CRC>.pnach` = the ticked files' text in order,
     each headed by a comment with its index (not its name), written atomically;
   - `ensure_folders(root, ps2)` → creates the empty folders (`data/games/retroarch/cheats/ps1`, `…/snes`, and
     `data/games/ps2/cheats` with PS2 on) when missing; never writes inside them.
2. `emulator_manager`:
   - `_cheat_catalog_unlocked`: with the knob on and a PS1 / SNES title, the user's `.cht` files are appended as
     sources after the manifest's (`provider: "user"`, the file name, its sha computed at listing, its entries; a file
     that fails the same parse — bad count, a pre-enabled cheat — is left out and counted in `user_files_skipped`).
     A missing manifest no longer hides them (the base is then today's "no_manifest_record" shape). With no user file
     the returned dict is today's, key for key. The launch, the profiles and the toggles then work as for a database
     file (they read the same catalog).
   - `_ext_cheat_catalog`: a PS2 title (knob on, `_ps2` loaded, B80's knob on) → one source `{"provider":
     "user_pnach", "filename": "Your PS2 cheat files", "entries": [{"index", "description": <file name>, "kind":
     "pnach"}]}`; the serial unknown (no PrivyHub launch seen yet) → status "unavailable", no source.
   - `launch()`: a PS2 title with the knob on passes the cheat arguments to `_launch_pcsx2`; knob 0 → today's call.
   - `_launch_pcsx2(…, cheat_source_index=None, cheat_enabled_indexes=None)`: the pick checked (source 0, indexes in
     range, at least one) before anything is written → `stage_pnach` into `config/PCSX2/cheats/`, and B80's game
     settings file with `EnableCheats = true` and the files' groups under `[Cheats]`; the game log
     `PS2 cheats: n files enabled` (no name). B80's writer also rewrites a game settings file **it wrote before**
     (its marker line) when the title has no toggle record and no cheat pick, with `EnableCheats = false`, so a cheat
     launch's switch never carries into a plain launch (the staged `.pnach` stays, inert).
3. `plugins/games.py` `__init__`: `ensure_folders` with the knob on (after the systems are set).
4. `docs/CHEATS.md`: plain words — where each folder is, the naming (the folder per game: PS1 / SNES by the game's
   file name without its ending; PS2 by the game's serial, which the hub learns the first time the game is played
   through PrivyHub), what shows on the TV, and that the hub never downloads these.

## Disclosed

- A PS2 cheat session, like B79's GameCube one, saves into the title's own slots and memory card.
- A PS2 title's cheats show after its first PrivyHub launch (the serial comes from PCSX2's log).
- The queue's PS1 / SNES folder is new; the older `data/games/user_content/<id>/cheats/` stays list-only, unchanged.

## Tests (`tests/art_systems/test_b81.py`, fixture folders, B49's rig; nothing fetched, nothing started)

- PS1 / SNES: a user `.cht` beside a manifest file → appended as the next source with its entries; staged by
  `_prepare_cheat_runtime` like a database file; a pre-enabled file skipped and counted; no user file → the catalog
  equals today's (the same call with the knob 0); no manifest + a user file → listed;
- PS2: the files listed by name; the launch (B49's rig) stages one `<SERIAL>_<CRC>.pnach` with both files' text,
  the game ini with `EnableCheats = true` and `[Cheats] Enable = <group>`, the log line; the next plain launch
  rewrites the ini with `EnableCheats = false`; knob 0 → nothing staged, today's call; the serial unknown → no source;
  the user's own folder from the paths file;
- `ensure_folders` creates only the empty folders and nothing inside; knob 0 → nothing created.
