# B127 — the mini games under each title's cheat setup: the design (written and hashed before any code)

T88 = H7's 2-player PS1 title; T89 = the users' N64 four-player title. No title, serial, game id, character name,
cheat name or path in this folder. Only with PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1 (the party routes) / PRIVYHUB_H7=1
(`h7-start`); either flag absent → today byte for byte; **a sidecar without `cheat` and a session without a cheat setup
→ today's answers and rows, byte for byte** (every new field only when a setup is in play).

## Settled from the code (HEAD `d9e95e66`)

1. **How `party-minigame-start` launches its title** (`party_minigame.py` `_start_steps`): the board's session set
   aside (`_party_stash_begin` — it clears `_active_cheat_session` with the other session fields), then
   `emu.launch(game)` under the manager's lock for that call only — **no cheat arguments**: today the title always
   runs in the normal setup (the normal `states/` and `saves/`). Then pause, route, switch, `h7-start` (load, watch),
   release.
2. **The onn's Extras launch** (`plugins/games.py` `launch`): `POST launch?id=…&cheat_source=<source_index>&cheat_indexes=
   <enabled indexes, comma-joined>` → `_parse_cheat_launch_request` → **B85's expansion** (`cheat_clean.expand` over the
   cleaned catalog, unless `PRIVYHUB_CHEAT_CLEAN=0` or `cheat_raw=1`; a saved setup's indexes are already the file's
   own, so the expansion gives them back) → `emu.launch(game, cheat_source_index=…, cheat_enabled_indexes=…)` →
   `_prepare_cheat_profile_storage`: **the `profile_id` = sha256 of (schema, game id, system, relative path, source
   index, source sha256, the enabled indexes)** — the same inputs give the same setup; different ones would make **a new
   setup folder** (written to the drive) → RetroArch's session config with exactly one `savefile_directory` /
   `savestate_directory`, **the setup's own** → B87 / B90 activation; `_active_cheat_session` holds `profile_id`,
   `source_index`, `enabled_cheat_indexes`, the folders.
3. **Where `h7-start`'s load writes under a setup** (`h7_minigame._start` → B101's `_load`): `emu._state_root() /
   <core folder>` / `<stem>.state8`; `_state_root()` returns **the setup's `states/`** while a cheat session is active,
   and RetroArch (`sort_savestates`) reads `<savestate_directory>/<core>/<stem>.state8` — **the same file: the load
   lands.** Today under a setup it loads the normal begin `<game id>.state` (T89's stays locked under the setup).
4. **`launch_orphaned`** (B90): only the HTTP launch route's answer to a client that has gone; the mini game's launch
   is the actor's own call (no client connection) — never orphaned; under a setup the orphaned launch's stop is
   `emu.stop()` as below.
5. **Stop under a setup** (`emu.stop`): `SAVE_FILES` (RetroArch flushes the in-game save **into the setup's
   `saves/<core>/`**) then `QUIT`; the mini game's end stops its title the same way. A match played in the mini game
   writes whatever the game itself writes to its in-game save (as any play of that setup does); no save state is
   written by a stop.
6. **The save routes during a mini game** (`save-state` / `load-state` — not taken by the mini game, B114's `TAKEN` is
   Home / RESUME / END only): today's path against the running title — **under a setup, a SAVE writes the setup's slot
   N and rewrites its slot 0 (`<stem>.state`), a LOAD loads the setup's slot into the mini game.** Not changed here
   (reported; the queue's item is the launch).

## Build (behind the flags)

- **The sidecar:** `<game id>.party.json` may carry `"cheat": {"source_index": n, "enabled_cheat_indexes": [...],
  "profile_id": "<the setup's id>"}` beside `players` / `scores` / `places_to_scores`. Checked as the other fields:
  `source_index` a non-negative integer; the indexes non-negative integers, distinct, at least one (kept sorted);
  `profile_id` 64 hex characters (compared case-blind; the hub writes upper case). Malformed → not listed (as a
  malformed sidecar today). No cheat name anywhere.
- **The setup's begin:** `<game id>.<the profile_id's first 12 characters, upper case>.state` in the rules folder,
  beside `<game id>.state`. A sidecar with `cheat` is listed only when the setup's begin is there (the normal begin is
  then not needed). The listing's answer unchanged (`id`, `players`).
- **The start** (`party-minigame-start`, the HTTP thread, before anything is set aside): with `cheat`, the setup is
  checked through the manager (`cheat_profiles(game)`, one bounded call ≤ 1.5 s): a profile with that `profile_id`,
  the same `source_index` and the same enabled indexes, valid on the hub; and the launch's own expansion (B85, as the
  route does it) of those indexes gives them back. Else **400 "the cheat setup this mini game names is not on the hub
  (or its cheats changed): nothing was launched"** and one `minigame_refused` row — nothing set aside, nothing
  launched, no folder made.
- **The launch:** with `cheat`, the actor's launch step is **the plugin's own launch path** (`handle_post("launch",
  "id=<game id>&cheat_source=<n>&cheat_indexes=<a,b,…>")`, under the manager's lock for that call only, as today's
  launch) — exactly the onn's Extras call. After it, **the session's `cheat_session.profile_id` must be the sidecar's**,
  else the mini game is given up ("the title did not start under its cheat setup") and the hub's end stops the title.
  `minigame_launch` carries `"cheat": true, "profile_matches": true` only then. Without `cheat`: today's `emu.launch(game)`.
- **`h7-start`'s load under a setup:** while a cheat session is active, the begin is **`<game id>.<prefix>.state` when
  it is there, else `<game id>.state`** (today's); the answer and the `watching` row carry `"begin": "setup"` /
  `"normal"` only under a setup. Into the setup's `states/<core>/<stem>.state8` (as now), the scratch removed (as now);
  N64 only into a core answering PAUSED (B123, unchanged).
- **The spec per setup:** not built — B126: one spec per title reads the locked and the unlocked select screens alike.

## Tests (`tests/b127_party_cheat_setups/`, a `cheat` mode in B114's scenario)

The real HTTP server on loopback; B101 / B103's fake RetroArch, **its states folder read from the session config the
launch wrote** (`savestate_directory` + the core folder — where RetroArch itself would look, not the hub's
`_state_root()`); RetroArch's network side of the cheat toggles stubbed as B83's harness does (disclosed); B108's
stand-in board; B114's onn thread and the calls every 0.1 s; the fixture titles' made-up `.cht` (B85).

1. The two setups made as the user made them: the onn's Extras launch from loopback (PS1 picks → the file's indexes
   with the required code; N64 a split cheat + the required code), stopped; read back through `cheat-profiles` (the
   onn's read): their `profile_id` / `source_index` / `enabled_cheat_indexes` into the sidecars. Each setup's slots
   (`.state`, `.state1`), slot pictures and in-game save written with random bytes; every file under both setups and
   the normal `states/` hashed.
2. `h7-start?bench=1` under the PS1 setup with no setup begin → `"begin": "normal"`; with it → `"begin": "setup"`, the
   load through `<setup>/states/<core>/<stem>.state8` (the fake's load line naming it; the memory the setup begin's),
   the scratch gone. Under the N64 setup: running → 400 B123's line, no `LOAD_STATE_SLOT` sent; paused → loaded from
   the setup's folder.
3. Refusals, each 400 with the plain line, nothing launched (no RetroArch started, the board still the session, no new
   folder under the setups' root): a sidecar naming a `profile_id` not on the hub; the setup's folder moved away; the
   setup's indexes changed in the sidecar.
4. **Two back to back with B114's concurrent calls:** a two-player mini game under the PS1 setup (seats 2,1) then a
   four-player one under the N64 setup (seats 3,1,4,2, Home / RESUME during it): the launch's query carrying
   `cheat_source` / `cheat_indexes`; the session's `profile_id` the setup's (status and the manager); the begin loaded
   from the setup's folder; ended with the right class / places and scores; every hand-over planned (two switches
   `planned`, no recovery act, no key to the board); every route < 2 s while a mini game is on.
5. After: every file under both setups and the normal `states/` byte-equal (the fake's `SAVE_FILES` writes nothing —
   the real flush is item 5 above, disclosed); no `.state8` anywhere; nothing left running.
6. **Today:** each flag absent → HEAD's answers byte for byte through the real routes (the cheat launch, `cheat-profiles`,
   the H7 / party routes, status, stop) on HEAD's companion against mine; **a sidecar without `cheat`** → B124's four-
   player run on HEAD's code and mine: the same rows (steps and fields), the same answers but clocks. The other suites
   green (B103, B105, B110-B115, B122-B124, B85, B83, the neighbours).

Record `evidence/B127_PARTY_CHEAT_SETUPS_2026-11-17.md` + this folder; `patches/B127_PARTY_CHEAT_SETUPS.md`.
