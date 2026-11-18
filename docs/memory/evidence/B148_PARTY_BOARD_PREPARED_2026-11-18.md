---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AY) — the board prepared before its launch, behind PRIVYHUB_PARTY=1 (the board's launch exists only then). Godot finds an imported resource through its sidecar `<file>.import` (tracked) and the files it names under the git-ignored `.godot/imported/` with a `.md5` holding the source's md5; a pull brings sources and sidecars but no imported files (PP-H3d: six sounds, a silent board). The hub's test reads every sidecar (its dests there, their source_md5 the source's) and every importable file's sidecar: 22 ms on the board's real folder. When it says so, Godot's `--headless --import` runs first, bounded at 20 s, with a `board_import` row; a failure or timeout still launches as today; never while the board runs; nothing to prepare → the launch as today. The import costs 3.8 s cold and 2.9 s warm on a scratch clone and writes only `.godot/` (0 status lines). Tests: a fake Godot through the real launch route (order, row, rc, bound, running, HEAD's argv); once, disclosed, a cold scratch clone of the real board: needed 24 → 3.87 s rc 0 → 0, step26 PASS (117), 0 status lines. Nothing adopted; nothing committed
---

# B148 — the board prepared before its launch

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B148. The directory is `b148_2026-11-18/`: the design + `.sha256` (hashed
07:41:35Z, before any code), `b148.diff`, `real_board_once.json`, the checks, `manifest.sha256`. The runs are in
`b147_2026-11-18/`. Patch: `patches/B148_PARTY_BOARD_PREPARED.md`. **The board's own folder was not written** (its cache
included). Godot ran headless on scratch clones only (a `git clone --no-hardlinks` reads the board's repo), with Godot's
own folders in the scratch, and every scratch was removed.

## Settled

- **How Godot knows a resource is not imported:** each imported file has a sidecar `<file>.import` beside it (24 tracked
  in the board's repo, one per picture, sound, model and font). Its `[deps]` give `source_file` and `dest_files` under
  `res://.godot/imported/`. Beside each dest Godot keeps `<dest stem>.md5` with `source_md5` (the source's md5 when it
  was imported). `.godot/` is git-ignored, so a pull brings the sources and their sidecars but not what they import to.
  The running game loads the sidecar's `path=`, and a missing dest is a missing resource. Godot re-imports when a dest
  is missing or the md5 differs, and a source with no sidecar is new. The board uses no `class_name` (its class cache
  is empty), so no script cache needs testing.
- **The cheap test** (`party_session.import_needed`): walk the project, skipping `.godot/` and any folder with a
  `.gdignore` (the board's `blender/`, `incoming/`). For every sidecar, each dest must be present with its `.md5`, and
  its `source_md5` must equal the source's md5. Every file with an importable extension must have its sidecar. On the
  board's real folder (read only): **22 ms, 0 needed** (A's import at PP-H3d).
- **What the import costs** (a scratch clone at `32d5329`, Godot 4.7.2): **cold 3.82 s, warm 2.93 s**, rc 0, 48 files
  in `.godot/imported` (1.9 MB). **It writes only `.godot/`: the clone's `git status --short` was 0 lines after it.**

## Built (`b148.diff`)

- `companion/party_session.py`: `IMPORT_LIMIT_S = 20.0`, `IMPORTABLE`, `import_needed(project)`,
  `_board_running(cfg)` (a `/proc` scan for a process naming the config's `godot`, first or after its interpreter, and
  its project), and `prepare(cfg, row, log, environ)`:
  - nothing needed → `None`: **no row, no import, the launch as today** (the test's ~20 ms the only difference);
  - the board running on that project → no import, row `board_import` `{"needed": true, "files": n, "skipped": "the
    board is running"}`;
  - else `[godot, "--headless", "--path", project, "--import"]` in the board's own environment, its output into the
    launch's own log, **bounded at 20 s** (killed past it), and row `board_import` `{"needed": true, "files": n,
    "seconds": s, "rc": rc}`, with `"timeout": true` / `"rc": null` past the bound and `"error"` if it cannot start.
- `companion/games/emulator_manager.py` (`_launch_party`): `prepare` runs after the config is read and before the board
  starts. **Whatever its end, the board is launched as today**; if it ever raised, a `board_import` row says so.
- **Never while the board runs:** the launch holds the manager's lock and refuses when a session is running, and
  `prepare` also skips if any process has Godot open on the project.
- **What the onn shows meanwhile:** its own launching wait. When an import runs, the launch answers that much later:
  ~3-4 s cold for the board's 24 resources, less for a pull's few new files, at most the 20-s bound. The onn waits
  60 s for a launch's answer; the board's window and sound waits are 15 s each.

## Tests (`tests/b148_party_board_prepared/`, 6)

| test | shown |
| --- | --- |
| nothing needed | B108's harness through the real launch route, its stand-in board taught `--import`: **only the launch, no row, the launch's argv equal to HEAD's** (the same scenario on the baseline's companion); the board's starter the real `Popen` |
| needed | a dest missing → **the import, then the launch, in that order** (`--headless … --import`), the row `needed` true, `files` 1, `rc` 0, `seconds` < 5, the row before `launch`; nothing needed after; the launch's argv as today; a changed source → needed and imported again |
| failing / slow | rc 1 → launched, the row's rc 1; a 5-s import with the bound at 1 s → **killed, launched, `timeout` true, `rc` null, `seconds` < 3** |
| running | the stand-in already running on the project (outside the hub) → no import, `skipped` "the board is running", launched |
| the test itself | a missing dest, a changed source, a source without its sidecar, a new `.ogg` each counted; a `.gdignore`d folder ignored |
| **once, disclosed: the real board** | a scratch clone of the board's repo at `32d5329`, cold: **needed 24 → `prepare` with the real Godot 3.87 s rc 0 → needed 0 → `step26_sound_and_ready` PASS (117) → the clone's status 0 lines**; the scratch removed (`real_board_once.json`; 07:45:09-07:45:47Z) |

The three-times runs skip the real-board class (Godot not named for them), so it ran once. The flags absent → today:
B108's `FlagAbsentIsToday` and B114's flag test in `tests_others.txt`.
