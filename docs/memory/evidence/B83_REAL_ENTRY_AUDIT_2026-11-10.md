---
memory_schema: 1
as_of: 2026-11-10
status: DONE (session B, queue AD) — the real-entry-point audit of B76-B81: one test per item through the entry point A or the hub calls (8 tests); broken on the real path at HEAD: B76 and B78's tool part (the scan — fixed by B82); B77, B79, B80, B81 sound. No product code changed by B83. Fixture trees only; nothing fetched; no emulator started; nothing committed. No title, serial, path or identifier in this record
---

# B83 — the real-entry-point audit of B76-B81 (2026-11-10)

**Why:** B76's tests passed fixture games straight to the dry run and never ran the scan or the CLI; ART-1 then found
the scan blind to three systems (B82). The same question for every item of queue AC: does its test reach the code the
hub actually runs?

**Baseline:** HEAD `8813f06a` + B82 (in the work copy). Only the companion and `privyhub-diag` active (B82's check, the
same run). **Design** (the audit table, the tests, the rule for findings) hashed before any test at 01:52:33Z
(`b83_2026-11-10/design.sha256`).

## The audit

| item | the entry point A / the hub calls | reached before | reached now | found broken |
| --- | --- | --- | --- | --- |
| **B76** art + details | `tools/update_game_metadata.py --dry-run --json`, `--system <s>`; the plugin's `details` | **no** — `run_metadata_dry_run(games=<fixture>)` in process, the scan patched out, the CLI's source text read | **yes** — B82: the CLI dry run on a fixture library; B83: the CLI fetch of one title through a fake picture server → the art cache → the plugin's `details` (year, genre, players, box art) | **yes: the scan** (three systems unseen) — **fixed by B82** |
| **B77** profiles PS2 / GameCube | the plugin's `input-profile-create` / `-assign` → `EmulatorManager.launch` (`pcsx2` / `dolphin`) | partly — the launch yes (B49's / B69's rigs); the profile made by a test-built manager, a made-up game id, a hand-made game | **yes** — the plugin's two handlers on the scan's game id → the plugin's own manager's launch → PCSX2's `[Pad1]` / Dolphin's `GCPad1` swapped, the log lines | no |
| **B78** N64 cheats | `tools/update_game_cheats.py --system n64`; the plugin's `cheat-catalog` → launch (RetroArch) | **no** — the tool with the scan patched out; the list on a test-built manager; the staging through `_prepare_cheat_runtime` (internal) | **yes** — B82: the CLI on a fixture library; B83: the real `run_cheat_update` (fetchers faked) → the handler's list → a launch with the plugin's own parse of `cheat_source=0&cheat_indexes=0` → the `.cht` staged for Mupen64Plus-Next | **yes: the tool's scan** (no N64 title) — **fixed by B82**; the list and the launch sound |
| **B79** GameCube cheats | `cheat-catalog` → launch (Dolphin) | partly — the launch yes; the list on a test-built manager; the bundled reader faked | **yes** — a made-up disc header; a fake Dolphin AppImage that is a real zip with `Sys/GameSettings/<ID3>/<ID6>.ini` read by the real `7z` → the handler lists the names (no disc id) → the launch writes the user file, `EnableCheats = True`, `GC cheats: 2 enabled` | no |
| **B80** PS2 patches | the plugin's `details` / `ps2-patches` → launch (PCSX2) | **no** for the plugin — built with `object.__new__`, `details`, `_find_game_by_id` and the manager replaced by lambdas; `7z` faked; the launch yes (hand-made game) | **yes** — a fixture PCSX2 log; a fake PCSX2 AppImage holding a real `patches.zip` → `details` offers `ws` / `60` → `ps2-patches ws=1` → the launch writes `EnableWideScreenPatches = true` and the log line | no — but **its own suite misses a wrong bundle path** (mutation M6: B80's suite passes, B83's fails) |
| **B81** drop-ins | `cheat-catalog` (the folders appear there) → launch (PCSX2 / RetroArch) | partly — the list on a test-built manager; PS1 staging internal; the PS2 launch yes | **yes** — the folders absent → made, empty, by the handler's first list → a `.pnach` listed and staged by a PS2 launch (`PS2 cheats: 1 files enabled`); a PS1 `.cht` listed (provider user) and staged for Beetle PSX HW by a launch | no |

**On HEAD's code** (`tests_on_head.txt`, the same 8 tests, B82 not applied): B76 fails (`0 != 2` matched — the CLI's
scan) and B78 fails (the cheat tool finds no N64 title); B77, B79, B80, B81 pass — their real paths were sound.

## The tests (`tests/art_systems/test_b83.py`, 8)

Fixture trees from B82's builder (each with its own `companion/` and the two tools, so `PLUGINS` and the tools have the
tree as their root); the ids are taken from the plugin's own scan in the companion's construction. Every run is a
child `python3 -I` with only the test's `PRIVYHUB_` values; socket connects / `urlopen` counted — 0 in every test
(B76's fake picture server answers RetroArch's thumbnail host only, 1 request served).

**What is still faked** (no emulator, no network): `Popen`; PCSX2's and Dolphin's session objects (B49's / B69's rigs,
`tests/gamecube_session/fake_dolphin.py`); RetroArch's command-port wait and its cheat-toggle exchange
(`_apply_active_cheat_profile`, RetroArch's network side — PS1's code, called once per cheat launch, checked); the
cheat index's two fetchers (B78's seed); the picture server (B76). The plugin's POST `launch` handler itself is not
called (it also starts the stream); the tests call the plugin's own manager's `launch` with the plugin's own
`_find_game_by_id` and `_parse_cheat_launch_request`, which is what that handler passes.

- 3 runs: 8 / 8 each; `tests/art_systems` 112 / 112 each (`tests_x3.txt`); no temp dir left.
- Mutations of the items' own code (`tests_mutations.txt`): **7 / 7 caught** by `test_b83.py` alone — B76's set name,
  B77's PS2 and GameCube profile hooks, B78's core folder name, B79's bundle path, B80's bundle path, B81's folder call
  at the list. Against the items' own suites (`tests_mutations_old_suites.txt`): B79's catches its path, B77's its
  hook, **B80's misses its bundle path**.

## Fixes

None in B83: the only breakage on a real path was the scan, fixed in B82 (its own design, tests and record). Nothing
listed for the next queue from the audit itself; B82's record lists two (the incomplete-record retry after a "skip",
records dropped when a drive folder is unreachable at a full update).

## Absent

B83 adds one test file and changes no product code (`b83.diff` = `tests/art_systems/test_b83.py` only): absent = today
by construction (`proof_flag_absent.md`).

## Disclosed

- The design said a broken item's test would be kept as an expected failure; none was needed.
- The fixture's persistent `retroarch.cfg` names a save and a state folder (the hub's has them; a cheat session
  replaces them) — the first run stopped there on the fixture, not on the code.
- A RetroArch launch reports no `launch_kind`; its tests check `active` and the started RetroArch AppImage instead.

## Files

`b83_2026-11-10/`: start files, the design + hash, `b83.diff`, `proof_flag_absent.md`, `tests_x3.txt`,
`tests_on_head.txt`, `tests_mutations.txt`, `tests_mutations_old_suites.txt`, the host-suite comparison, the queue's
tree checks, `scripts/` (`mutate.py`, `mutations*.json`, `run_host.sh`), redact / title checks, `manifest.sha256`.
Patch note: `patches/B83_REAL_ENTRY_AUDIT.md`.
