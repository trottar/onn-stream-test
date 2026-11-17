# How a launch picks a cheat setup — read from the code (2026-11-17 ~02:50Z; no names)

- **The onn's Extras → Cheats → a saved setup → launch** (`MainActivity.kt` `showExistingGameCheatProfileDialog` →
  the launch at ~12660): it reads the setup from `POST /plugins/games/cheat-profiles?id=<game id>` (its fields
  `profile_id`, `source_index`, `enabled_cheat_indexes`, `occupied_slots`, `persistent_save_present`) and launches with
  **`POST /plugins/games/launch?id=<game id>&cheat_source=<source_index>&cheat_indexes=<enabled_cheat_indexes, distinct,
  sorted, comma-joined>`** (plus the title's last joined count as `players_joined` when the onn has one — not sent here;
  T89 then gets four ports as every N64 launch). No onn is needed: the same call from loopback.
- **The hub** (`plugins/games.py` `launch`, `_parse_cheat_launch_request`): `cheat_source` a non-negative integer,
  `cheat_indexes` the picks (B85: the cleaned list's picks expanded to the file's own indexes unless `cheat_raw=1`);
  the emulator manager derives the setup from (the source file's hash, the enabled set) — **the same `profile_id`** —
  and starts RetroArch with that setup's own folders.
- **The folders under a setup:** `data/games/retroarch/cheat_profiles/<game id>/<profile_id>/` with `profile.json`,
  `privyhub_state_slots.json`, `saves/<core>/` (the in-game save) and `states/<core>/` — the session's config carries
  exactly one `savefile_directory` and one `savestate_directory`, the setup's own (`emulator_manager.py` ~5560-5590;
  "RetroArch did not honor duplicate … assignments"); **RetroArch reads and writes states in `states/<core>/` of the
  setup**; `_state_root()` returns the setup's `states` folder while a cheat session is active.
- **The hub's own LOAD under a setup** (`load_state`): copies `<stem>.stateN` to `<stem>.state` (slot 0) **in the
  setup's states folder**, verifies it, then `LOAD_STATE_SLOT 0` (so a hub LOAD rewrites the setup's `.state`). This
  task does not use it: each load is by hand into scratch **slot 8** (`<stem>.state8` in the setup's `states/<core>/`),
  removed after.
- **The two setups** (read only): **T88's cheat setup** — one cheat, made 01:05Z, slot 1 occupied (01:06Z); T88's other
  setup (one cheat, no slot) is not used. **T89's cheat setup** — two cheats, slot 1 occupied (01:07Z). Each setup's
  states folder holds `.state1` + picture and the hub's slot-0 `.state` + picture (from the users' SAVE).
