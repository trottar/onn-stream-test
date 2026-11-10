# B78 — N64 cheats from RetroArch's database (design, written and hashed before code)

**Knobs:** inside `PRIVYHUB_N64=1` (the N64 system exists only there); default on within it, `PRIVYHUB_N64_CHEATS=0`
= today. Absent `PRIVYHUB_N64` = today byte for byte (nothing below is reachable).

## What exists (read at HEAD)

- **The fetch tool** (`tools/update_game_cheats.py` → `games/cheat_importer.run_cheat_update`), run by hand:
  - it reads the cached root index of RetroArch's cheat database and the system's folder tree (the hub's cache has a
    `Nintendo - Nintendo 64` folder, B75);
  - it matches each title by **the metadata record's canonical title** (`_metadata_identity`: no record → 
    `metadata_missing`), so an N64 title needs B76's record first;
  - it downloads the matched `.cht` files into `data/games/user_content/<game id>/cheats/libretro/`, forces every
    cheat disabled, and writes the manifest `data/games/cheats.json`;
  - the system → folder name comes from `SYSTEM_SPECS` (nes / snes / genesis / ps1): **N64 is refused**
    ("Unsupported game system").
- **The onn's Cheats list:** `cheat-catalog` / `cheat-profiles` read the manifest for any game id; **no system gate**.
- **The launch:** `launch(…, cheat_source_index, cheat_enabled_indexes)` → `_prepare_cheat_runtime` stages the file
  as `cheat_runtime/<core library name>/<content stem>.cht`, the profile's isolated saves, then the ticked cheats are
  turned on through RetroArch's network commands and checked. The core library name comes from
  `CHEAT_CORE_LIBRARY_NAMES` (FCEUmm / bsnes / BlastEm / Beetle PSX HW): **N64 is refused** ("No validated RetroArch
  cheat library name"). The N64 launch otherwise takes the same RetroArch path (B59: `_resolve_n64`, then the shared
  cheat / mod / input code). The core's library name on the hub is **Mupen64Plus-Next** (its `.info` `corename`, its
  binary's string, `n64_session.OPTIONS_LIBRARY`).

## The change

1. `cheat_importer.py`: `cheat_system_specs(environ=None)` = `SYSTEM_SPECS`'s four, plus
   `n64 → {"database_name": "Nintendo - Nintendo 64", …}` (B76's spec, imported from `metadata_importer`) when
   `PRIVYHUB_N64=1` and `PRIVYHUB_N64_CHEATS` is not `0`. `LibretroCheatProvider.prepare_system` reads it.
   `tools/update_game_cheats.py` `--system` choices from it.
2. `emulator_manager.py`: `_cheat_core_library_name(system_id)`: the class table's value; for `n64` →
   `"Mupen64Plus-Next"` only when the N64 module is loaded (`_n64 is not None`, i.e. `PRIVYHUB_N64=1`) and
   `PRIVYHUB_N64_CHEATS` is not `0`. `_prepare_cheat_runtime` uses it.
3. Nothing else: the list, the profiles, the toggles, the saves are PS1's code unchanged.

## What A does with it (not B)

The N64 cheat fetch is the user's "yes" (G3a), run by A after B76's fetch has given N64 titles their records: the
tool with `--system n64` (its own report mode first), each matched title's database name sent, as PS1's.

## Tests (`tests/art_systems/test_b78.py`, fixtures only, the fetchers faked; nothing fetched)

- the map: `PRIVYHUB_N64=1` → n64 → "Nintendo - Nintendo 64"; absent / `PRIVYHUB_N64_CHEATS=0` → today's four;
- a fixture cheat index (root + an N64 tree with made-up `.cht` names) and a fixture metadata record → the tool
  (offline, the fake fetchers) matches the title, stores the file under the game's user content, writes the manifest;
  absent the flag → the N64 game is `provider_unavailable` / refused as today;
- the manager: `_cheat_core_library_name("n64")` = "Mupen64Plus-Next" with the flags, None without, None with the
  knob 0; `_prepare_cheat_runtime` for an N64 game stages `cheat_runtime/Mupen64Plus-Next/<stem>.cht` (byte equal to
  the manifest's file) and returns the session with the ticked indexes;
- `cheat_catalog` for the N64 game lists the file's entries in the onn's shape (`sources[].entries[]`).
