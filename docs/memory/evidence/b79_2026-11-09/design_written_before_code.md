# B79 — GameCube cheats from Dolphin's bundled codes (design, written and hashed before code)

**Knobs:** inside `PRIVYHUB_GAMECUBE=1` (the system exists only there); default on within it, `PRIVYHUB_GC_CHEATS=0`
= today. **No download** of any kind (Dolphin's code server is never named in a request; nothing is fetched).

## What exists (read at HEAD and on the hub, as data)

- **Dolphin 2609b's bundled codes:** the AppImage holds `usr/share/dolphin-emu/Sys/GameSettings/<id>.ini` (1,883
  files: 1,431 by the 3-character id, 403 by the 6-character id, a few others). `[ActionReplay]` lines `$<name>`
  each begin a code; `[Gecko]` lines `$<name> [<author>]`. Read on the hub with `7z x -so` in ~0.01-0.03 s per file
  (the AppImage is a squashfs; 7z is installed). Dolphin's own rule: the codes come from the global and the user
  files for `<ID3>.ini`, `<ID6>.ini`; the **enabled** lists only from the user dir's files, `[ActionReplay_Enabled]`
  / `[Gecko_Enabled]`, one `$<name>` per line (a Gecko code's name without its `[author]`); cheats apply only with
  `[Core] EnableCheats = True` in `Dolphin.ini`.
- **PrivyHub's Dolphin:** `-u data/games/gamecube/user` (its `GameSettings/` exists and is empty on the hub);
  `gamecube_session.write_config` writes `Dolphin.ini` whole each launch with `EnableCheats = False`.
- **The title's id:** in the disc header — the first 6 bytes of the disc. In an `.rvz` (and `.wia`) the disc's first
  0x80 bytes are stored uncompressed at file offset 0x58 (after the 0x48-byte header 1 and 0x10 bytes of header 2);
  `.iso` / `.gcm` at 0; `.ciso` at 0x8000. The GameCube magic `C2 33 9F 3D` sits at the disc's 0x1C. Read on the hub
  (read-only, 0x8100 bytes per file, nothing printed): 26 of the drive's 27 `.rvz` files give a valid id; the 27th
  is the small non-title file B69 already skips (`MIN_TITLE_BYTES`).
- **The onn:** Extras → Cheats calls `cheat-profiles` and `cheat-catalog`, shows "New Cheat Session" when `sources`
  is non-empty, a multi-choice of `sources[i].entries[].description`, then launches with `cheat_source` /
  `cheat_indexes`; it needs only `active` back. **No client change.**
- **The launch:** `launch()` returns `_launch_dolphin(game, players_chosen)` early for a GameCube title; the cheat
  arguments are dropped today.

## The change

1. New `companion/gc_cheats.py`:
   - `KNOB_ENV = "PRIVYHUB_GC_CHEATS"`, `enabled(environ)` (not "0");
   - `disc_id(path)` → the 6-character id or None (the header rules above; the magic checked; read-only);
   - `read_bundled(appimage, name, run=subprocess.run)` → the bundled file's text or None (`7z x -so`, 10-s
     timeout; any failure → None);
   - `parse_codes(text)` → `[("ar", name), ("gecko", name)]` in file order;
   - `codes_for(gid, reader)` → `<ID3>.ini` then `<ID6>.ini`, de-duplicated by (kind, name), each
     `{"index", "description", "kind"}`;
   - `enabled_text(existing, ar, gecko)` → the user file: every other section of an existing file kept as it was,
     the two `_Enabled` sections replaced (written only when non-empty);
   - `write_enabled(user_dir, gid, ar, gecko)` → `GameSettings/<gid>.ini` written atomically **only when at least
     one code is enabled** (None otherwise); never touches anything else.
2. `gamecube_session`: `dolphin_ini(cheats=False)` → `EnableCheats = True` only when asked; `config_files(…,
   cheats=False)`, `write_config(user_dir, gcpad_layouts=None, cheats=False)`. Default = today's bytes.
3. `emulator_manager`:
   - `_ext_cheat_catalog(game)` → for a GameCube title (`_gc` loaded, knob on): the catalog in the onn's shape —
     one source `{"source_index": 0, "provider": "dolphin_bundled", "filename": "Dolphin's built-in codes",
     "cheat_count": n, "entries": […]}`, `status` "cached" (or "no_codes" with no source when none); cached in
     memory per (game id, the title file's size and mtime, the AppImage's mtime). `cheat_catalog` / `cheat_profiles`
     return it (profiles always `[]`: the session has no isolated saves, disclosed) before today's code; any other
     title → today's code unchanged.
   - `launch()`: a GameCube title with the knob on passes `cheat_source_index` / `cheat_enabled_indexes` to
     `_launch_dolphin`; knob 0 → today's call (the arguments dropped, as today).
   - `_launch_dolphin(game, players_chosen, cheat_source_index=None, cheat_enabled_indexes=None)`: with indexes →
     checked against the catalog (source 0, every index in range, at least one), the user file written, `write_config(
     …, cheats=True)`, the game log `GC cheats: n enabled` (the count only: no code name, no id). Without → today's
     files and log. The payload gets `gc_cheats: n` only on a cheat launch.

## Disclosed limits

- A GameCube cheat session saves into the title's own SAVE / LOAD slots and memory card (PS1's cheat profiles keep
  their own; Dolphin's states are per game id). The onn shows no saved cheat profiles for GameCube.
- A code that needs a specific disc revision is listed for every revision (Dolphin's own `<ID6>r<rev>.ini` files are
  not read).
- The user file from the last cheat launch stays in `GameSettings/`; a later launch without cheats writes
  `EnableCheats = False`, so it is inert.

## Tests (`tests/art_systems/test_b79.py`, fixtures only: a fake bundled reader, fixture disc headers, B69's rig)

- `disc_id`: an `.rvz` fixture header → the id; `.iso` / `.ciso` offsets; a wrong magic / short file → None;
- the names listed from a fixture bundled ini (AR + Gecko, the author stripped, ID3 + ID6 merged, duplicates once);
- the enabled sections written; an existing user file's other sections kept; none enabled → no file;
- the manager (B69's rig, a fake reader): the catalog in the onn's shape; a cheat launch writes the user file,
  `EnableCheats = True`, `GC cheats: 2 enabled`; a plain launch → today's `Dolphin.ini` bytes, no file, no line;
  knob 0 → today's catalog code (no GameCube catalog) and the cheat launch writes nothing; a bad index refuses;
  the `7z` command line names only the bundled path (no network tool).
