# B83 — the real-entry-point audit of B76-B81 (design, written and hashed before code)

**Baseline:** HEAD `8813f06a` + B82 (`b82.diff`, in the work copy). **The rule this audit applies:** a coded item is
tested through the entry point A or the hub actually calls — the tool's CLI, the plugin constructed the way the
companion constructs it (`privyhub_service` imports `plugins`, whose `__init__` builds `PLUGINS`), and the launch
through `EmulatorManager.launch` with the system's kind on the game the plugin's own `_find_game_by_id` returns — on
fixture trees and fake emulator files; no network, no emulator, nothing of the hub's read or written.

## The audit, read from B76-B81's records and tests (before any new test)

| item | the entry point A / the hub calls | its tests before B83 | gap |
| --- | --- | --- | --- |
| **B76** art + details | `tools/update_game_metadata.py --dry-run --json`, then `--system <s>` (the fetch); the onn reads `details` / `games` from the plugin | `run_metadata_dry_run(…, games=<fixture>)` and `LibretroProvider` in process; `scan_privyhub_games` patched out; the CLI never run (its source text read) | **the scan and the CLI never reached → the bug ART-1 hit** (fixed in B82; B82's CLI dry-run test covers the first half) |
| **B77** profiles PS2 / GameCube | the onn: `input-profile-create` / `input-profile-assign` (the plugin's `handle_post`) → the launch | `EmulatorManager.launch` reached (B49's / B69's rigs) — but the profile written by a manager the test built, assigned to a made-up game id, the game dict hand-made | the plugin's handlers and the scan's game ids never reached |
| **B78** N64 cheats | the cheat tool (`--system n64`); the onn: `cheat-catalog` (the plugin's `handle_post_request`) → `launch` with `cheat_source` / `cheat_indexes` | `run_cheat_update` with the scan patched out; `EmulatorManager.cheat_catalog` on a manager the test built; the staging through `_prepare_cheat_runtime` (internal), not the launch | the scan (fixed in B82), the plugin's handler and the launch never reached |
| **B79** GameCube cheats | `cheat-catalog` → the launch | `EmulatorManager.cheat_catalog` and `.launch` reached (B69's rig) with the bundled reader faked (`fake_reader`) | the plugin's handler and the real reader (the AppImage through `7z`) never reached |
| **B80** PS2 patches | `details` (the plugin's `handle`) → the "Patches…" entry; `ps2-patches`; the launch | the plugin built with `object.__new__` and `details`, `_find_game_by_id`, `_emulator` replaced by lambdas; the manager reached with `7z` faked; the launch reached (B49's rig) with a hand-made game | the plugin as the companion builds it, its real `details` and the real bundle reader never reached |
| **B81** drop-ins | `cheat-catalog` (the folders are made there) → the launch | `EmulatorManager.cheat_catalog` on a test-built manager; PS1 staging through `_prepare_cheat_runtime`; PS2 launch reached (B49's rig) | the plugin's handler (where the folders appear) and the PS1 launch never reached |

## The tests (`tests/art_systems/test_b83.py`, one class per item, each through the real entry point)

A fixture tree per test from B82's builder (its own `companion/` copy and the two tools, so `PLUGINS` and the tools
run with the tree as their root; the hub's folders; fake in-place PS2 / N64 / GameCube folders named by a fake paths
file; RetroArch's lists for the seven systems in the provider cache; box art pre-placed so the companion's own startup
reconcile requests nothing). Every run is a child `python3 -I` with only the test's `PRIVYHUB_` values; socket
connects / `urlopen` blocked and counted (must be 0, except B76's fake picture server). Emulators never run: a fake
`Popen`; PCSX2's and Dolphin's session objects with B49's / B69's fakes (`tests/gamecube_session/fake_dolphin.py`);
RetroArch's command-port wait and its cheat-toggle exchange (`_apply_active_cheat_profile`, RetroArch's network side,
PS1's code tested before) stubbed. The fake AppImages are real archives (zip) holding the bundle at the path the code
reads (`usr/bin/resources/patches.zip`, `usr/share/dolphin-emu/Sys/GameSettings/`), so the real readers run `7z`.

- **B76:** the CLI `--system n64` with the art knob and the flags; a fake picture server answers only RetroArch's
  thumbnail host (any other request fails and is counted) → the matched title's art in `media/games/box_art/<id>.png`,
  its record matched; then `PLUGINS["games"].handle("details", id)` → year, genre, players, `box_art_available` from
  the fixture's details fragments; an unmatched N64 title's details carry none.
- **B77:** `handle_post("input-profile-create")` (a bottom / right swap, the onn's JSON) and `input-profile-assign` for
  a PS2 and a GameCube title found by the plugin's scan → `launch` on the plugin's own manager → PCSX2's `[Pad1]`
  Cross / Circle swapped and Dolphin's `GCPad1` A / X swapped, written by the launch; the log lines.
- **B78:** the cheat manifest made by the real `run_cheat_update` (the fetchers faked) → `handle_post_request(
  "cheat-catalog", id)` on the N64 title → the entries; `launch` with the plugin's own `_parse_cheat_launch_request`
  (`cheat_source=0&cheat_indexes=0`) → the `.cht` staged for Mupen64Plus-Next, byte-equal to the stored file.
- **B79:** a GameCube title with a made-up disc header; the fake Dolphin AppImage holding `<ID3>.ini` / `<ID6>.ini` →
  `cheat-catalog` lists the names (no disc id in the reply) → `launch` with two ticked → the user `GameSettings/<ID6>
  .ini` enabled sections, `EnableCheats = True`, `GC cheats: 2 enabled`.
- **B80:** a PS2 title seen in a fixture PCSX2 log; the fake PCSX2 AppImage holding a `patches.zip` with its `.pnach`
  → `handle("details", id)["ps2_patches"]`, `handle("ps2-patches", …ws=1)` → `launch` → the game settings file with
  `EnableWideScreenPatches = true`, the log line.
- **B81:** the drop-in folders absent → the first `cheat-catalog` through the handler makes them, empty; a fixture
  `.pnach` (PS2) and `.cht` (PS1) placed → listed by the handler → a PS2 cheat launch stages the `.pnach`, a PS1 cheat
  launch stages the `.cht` for Beetle PSX HW.

## What is done with a finding

An item found broken on its real path: if the fix is about a line, a short design addendum hashed before the fix, the
fix in B83's diff, disclosed; if larger, listed for the next queue with the reason, its test kept as an expected
failure (`unittest.expectedFailure`, named in the record). The record's table: item, entry point, reached before / now,
found broken yes / no.
