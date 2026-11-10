---
memory_schema: 1
as_of: 2026-11-10
status: BUILT, NOT ADOPTED (session B, queue AD) — the tools' game scan sees every system the hub lists (the systems builder shared with the plugin's constructor), and no longer builds the companion's plugins inside the tool's process. Fixture trees only; nothing fetched; the real drive and library not scanned by B; nothing committed. No title, serial, path or identifier in this record
---

# B82 — the game scan sees every system the hub lists (2026-11-10)

**Why:** ART-1's stage 1 (`art1_2026-11-10/stage1/STAGE1.md`): the dry run saw PS1 and SNES only. `scan_privyhub_games`
built its scanner with `GamesPlugin.__new__`, skipping `__init__`, the only place PS2 / N64 / GameCube were added.

**Baseline:** HEAD `8813f06a`; `git status --short` empty at the check (the line it shows is this record's own dir,
`b82_2026-11-10/git_status_at_start*.txt`); only the companion and `privyhub-diag` active (`units_at_start.txt`).
**Design** hashed before code at 01:36:34Z (`design.sha256`).

## Settled

- **The callers** (all four use the scan; nothing else does): the metadata update (the tool; the startup reconcile),
  B76's dry run, the cheat update, the startup reconcile's decision. The table is in the design.
- **Why `__new__`:** `__init__` starts the startup reconcile thread, which calls the scan, so constructing inside the
  scan would start another reconcile per scan, without end. It also builds the emulator / stream / recovery objects
  for the class's own root. No recorded rationale (it dates from the A7 checkpoint).
- **Found while settling — a second, larger defect:** `from plugins.games import GamesPlugin` runs
  `companion/plugins/__init__.py`, which **constructs every plugin**. So each run of either tool built a full
  `GamesPlugin()` for the hub's own root and **ran the startup reconcile — a full metadata update — inside the tool's
  process** (probed on a scratch export: the thread, `metadata.json` and four logs written). On the hub the reconcile's
  status file has read `RUNNING` since 00:33:31Z, during ART-1's tool runs (counts only read). **With the systems fixed
  and only that, A's next dry run would have fetched N64 / PS2 / GameCube art in the background before the user's
  "fetch".** B82 fixes both.
- **Also found:** once the scan includes PS2 / GameCube, a full cheat run would stop with an uncaught
  `CheatError("Unsupported game system")` at the first such title with a matched record (after ART-1's fetch), and on
  N64 with `PRIVYHUB_N64_CHEATS=0` (B78's kept refusal).

## What was built (`b82.diff`)

- **`plugins/games.py`:** `GamesPlugin.listed_systems()` — the in-place systems their flags imported, on the class's
  four; `__init__` calls it (instance attribute only when it differs, as before). `folder_available(root, system)` —
  the folder the scan reads for that system (the paths file `PRIVYHUB_PS2_PATHS` names, else the gitignored default;
  the hub's own `games/<folder>`), read-only.
- **`metadata_importer.py`:** `_games_plugin_module()` loads `plugins.games` with a bare `plugins` package for that one
  import when the package is not loaded yet (the tools), so `plugins/__init__.py` does not run. The companion's
  import is unchanged. `scan_privyhub_games` gives its `__new__` scanner the builder's systems. `listed_privyhub_systems()`.
  The dry run, **with `PRIVYHUB_ART_SYSTEMS=1` only**: a row for every listed system in the map, zero titles too, and
  `listed[system] = {titles, folder: available | unavailable, list: available | unavailable | not_needed}`.
- **`tools/update_game_metadata.py`:** the dry run's text says `folder unavailable (…)` / `list unavailable (…)` under
  a system when so.
- **`cheat_importer.py` + `tools/update_game_cheats.py`:** systems without a cheat list (PS2, GameCube, N64 with
  `PRIVYHUB_N64_CHEATS=0`) are counted as `not_offered` and not processed; a text line per system.
- `startup_reconcile.py` unchanged: it now sees the three systems with the flags.

## Absent = today

`proof_flag_absent.md`: with none of the four knobs, the scan and both tools' outputs (JSON and text) are **byte-equal
to HEAD's** on the same fixture tree (6 / 6, `proof_absent_run.txt`); the plugin as the companion constructs it holds
the same systems as HEAD's for all 8 flag combinations (`proof_init_systems_run.txt`). **The one deliberate
difference:** the tools no longer start the startup reconcile in their own process.

## Tests (`tests/art_systems/test_b82.py`, 15, all through the real entry points)

Fixture trees holding their own `companion/` and the two tools; the hub's four folders with fake files; fake in-place
folders named by a fake paths file (GameCube files sparse ≥ 1 MiB); RetroArch's lists for all seven systems in the
provider cache; the cheat index seeded through the real provider with fake fetchers; made-up titles. Every run is a
child `python3 -I` with only the test's `PRIVYHUB_` values, socket connects and `urlopen` blocked and counted (0
throughout).

- the scan: seven systems with the flags, four without, each flag its own system; an unreachable folder → no titles
  and "unavailable", never created; **the companion's plugins not built, no reconcile thread, nothing written**;
- **the list the onn reads** (`systems()` of the plugin as the companion constructs it) = the scan's systems and
  counts = the dry run's `listed` titles, with and without the flags;
- the metadata CLI `--dry-run --json` (online, as A runs it) → counts for all seven, nothing written; "folder
  unavailable" and "list unavailable" told apart (JSON and text); without the art knob the three `not_offered`;
  absent → today's keys;
- the cheat CLI `--system n64 --no-download --json` → the 3 N64 titles (1 with cheats, 2 without a matched record); a
  full run with the flags → completes, `not_offered` PS2 2 / GameCube 2, text line; absent → nothing counted;
- the startup reconcile through `from plugins import PLUGINS` (the thread joined): without the flags `RECONCILED` then
  `SKIPPED_CURRENT` (the four); with them `library_changed`, 11 discovered, the three systems `provider_unavailable`
  (no art knob → no request), the four's matches unchanged.
- **The regression, kept:** on HEAD's code the same file fails 12 of 15 (`tests_on_head_regression.txt`): the scan
  returns `{ps1, snes}` with the flags; the registry is built in the tool's process (HEAD's reconcile had already
  written the fixture's `metadata.json`, so the first explicit reconcile read `SKIPPED_CURRENT`); the cheat tool sees 0
  N64 titles. The three absent tests pass on HEAD.
- 3 runs: 15 / 15, and `tests/art_systems` 104 / 104 each (`tests_x3.txt`); no temp dir left.
- Mutations: **10 / 10 caught** (`tests_mutations.txt`; `scripts/mutate.py`, `scripts/mutations.json`).

## Disclosed

- **B78's test changed:** `test_knob_zero_is_todays_refusal` → `test_knob_zero_skips_n64_as_not_offered` (the
  refusal it kept is gone by design).
- The design's helper signature `_games_plugin_module(project_root)` became `_games_plugin_module()`: its first
  version pointed the bare package at `<root>/companion/plugins` and broke B76's in-process dry-run tests (their
  fixture roots hold no `companion/`). It now finds `plugins` as the plain import does (`importlib.util.find_spec`,
  which does not execute it).
- **What A will see at the restart that loads B82** (the three flags on, the art knob off in the companion): the
  startup reconcile finds the three systems' titles new (`library_changed`) and runs one full metadata update: the
  three get `provider_unavailable` records **without any request**; PS1 / SNES are re-matched from the cached lists as
  on any library change, their art already cached. Those 155 records count as incomplete, so the update repeats at a
  companion start at most once per 7 days until ART-1's fetch replaces them (and for good after a "skip") — listed for
  the next queue.
- **Not changed, listed for the next queue:** a full metadata update drops the records of titles it does not scan, so
  a run with the drive's folder unreachable loses those systems' fetched details until the next fetch (today's rule
  for every system; with HEAD's scan it happened on every full update).
- The tools' text output gained lines only when the new keys are present.

## Files

`b82_2026-11-10/`: start files, the design + hash, `b82.diff`, `proof_flag_absent.md`, `proof_absent_run.txt`,
`proof_init_systems_run.txt`, `tests_x3.txt`, `tests_on_head_regression.txt`, `tests_mutations.txt`, `scripts/`
(`mutate.py`, `mutations.json`, `proof_absent.py`, `proof_init_systems.py`), redact / title checks,
`manifest.sha256`. Patch note: `patches/B82_SCAN_ALL_SYSTEMS.md`.
