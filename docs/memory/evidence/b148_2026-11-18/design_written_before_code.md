# B148 — the board prepared before its launch: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AY.md` §B148. Baseline `baseline_head.txt`. Behind `PRIVYHUB_PARTY=1`: the board's
launch kind exists only then. Absent = today.

## Settled

- **How Godot knows a resource is not imported:** every imported file has a sidecar `<file>.import` beside it (tracked
  in the board's repo: 24, one per tracked picture / sound / model / font). Its `[deps]` name the source and the
  `dest_files` under `res://.godot/imported/`; beside each dest Godot keeps `<dest stem>.md5` with `source_md5` (the
  source's md5 when it was imported) and `dest_md5`. The `.godot/` cache is git-ignored, so a pull brings new sources
  and sidecars but no imported files. At a launch the game loads `path=` from the sidecar: **a missing dest is a missing
  resource** (PP-H3d: six sounds, a silent board). Godot's editor / `--import` re-imports when a dest is missing or the
  source's md5 differs from `source_md5`; a source with no sidecar at all is new.
- **A cheap test the hub can make** (`party_session.import_needed(project)`): walk the project (skipping `.godot/` and
  any folder with a `.gdignore`); for every `*.import` sidecar: each `dest_files` entry exists, its `.md5` exists, and
  its `source_md5` equals the md5 of the source; and every file with an importable extension (png, jpg, jpeg, webp,
  svg, bmp, tga, wav, ogg, mp3, glb, gltf, fbx, obj, ttf, otf, woff, woff2) has its sidecar. Any failure → "needed"
  (with a count). On the board's real tree (24 sidecars, read only): **17.7 ms, nothing needed** (A's import of
  PP-H3d). The board uses no `class_name` (its class cache is empty): no script cache to test.
- **What `--headless --import` costs** (a scratch clone of the board at `32d5329`, Godot 4.7.2, Godot's own folders in
  the scratch): **cold 3.82 s, warm 2.93 s** (rc 0, 48 files in `.godot/imported`, 1.9 MB); **it writes only `.godot/`
  — the clone's `git status --short` 0 lines after it**. (A source added without a sidecar would get one written beside
  it: a tracked-tree change; the board's push carries its sidecars.)

## The design

- In `EmulatorManager._launch_party`, after the config is read and before `_party.start`: `party_session.prepare(cfg,
  row)` —
  - **never while the board runs:** the manager holds its lock and has no process (the launch refuses otherwise), and
    a scan of `/proc` for a process whose command line names the config's `godot` and `project` → found: no import,
    row `board_import` `{"needed": true, "skipped": "the board is running"}`;
  - the test → **not needed: no import, no row, the launch's command and timing as today** (the test's own cost, ~20
    ms, the only difference);
  - needed → `[godot, "--headless", "--path", project, "--import"]` (the board's own environment, stdout / stderr to
    the launch's own log file), **bounded by IMPORT_LIMIT_S = 20 s** (the onn waits 60 s for a launch's answer; the
    window and the sound waits are 15 s each); row `board_import` `{"needed": true, "seconds": s, "rc": rc}`; a
    timeout → the import killed, `{"needed": true, "seconds": 20.0, "rc": null, "timeout": true}`; an error starting it
    → `{"needed": true, "rc": null, "error": "<type>"}`. **Whatever the import's end, the board is launched as today.**
  - What the onn shows meanwhile: its own launching wait (the launch's answer comes ~3-4 s later than today when an
    import runs — a pull's few new files, or a cold cache).
- The test and the import are module functions (fakeable): `party_session.IMPORT_LIMIT_S`, `import_needed`, `prepare`.

## Tests (`tests/b148_party_board_prepared/`)

- A fake Godot (a script recording its argv, with an `--import` mode that writes the dests and `.md5`s it is told to)
  over a scratch tree, through the real HTTP launch route (B108's harness): **needed → the import, then the launch, in
  that order**, the row with `needed`, `seconds`, `rc` 0; **not needed → no import, no row, the launch's argv equal to
  HEAD's**; the import failing (rc 1) → launched, the row's rc; running past a shortened bound → killed, launched, the
  row's `timeout`; the board's process already running with that project → no import, the row's `skipped`.
- The test itself: a missing dest, a changed source, a source without a sidecar, a `.gdignore`d folder ignored.
- The flags absent → today (B108's / B114's flag tests).
- **Once, disclosed, on a scratch clone of the board's real tree with a cold cache:** the test says needed; `prepare`
  runs the real Godot's import; the test then says not needed; `checks/step26_sound_and_ready.gd` PASS; the clone's
  `git status --short` 0 lines; the scratch removed.
