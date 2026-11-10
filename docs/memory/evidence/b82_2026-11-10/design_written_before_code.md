# B82 — the game scan sees every system the hub lists (design, written and hashed before code)

**Baseline:** HEAD `8813f06a` (ART-1's stage 1 and its skip committed). No knob of its own: the scan follows the
three system flags (`PRIVYHUB_PS2` / `PRIVYHUB_N64` / `PRIVYHUB_GAMECUBE`) exactly as the running hub's list does;
B76's `PRIVYHUB_ART_SYSTEMS` keeps its meaning. **Absent** (none of the three flags, no `PRIVYHUB_ART_SYSTEMS`) = today's
scan and today's tool output, byte for byte.

## Settled (read in the code at HEAD; a scratch copy probed, no network, nothing of the hub's touched)

**The callers of `scan_privyhub_games(project_root)`** (`companion/games/metadata_importer.py`):

| caller | runs where | expects |
| --- | --- | --- |
| `run_metadata_update` (same module) | the tool `tools/update_game_metadata.py`; the startup reconcile | the list's games: id, title, system, relative path; a full run rewrites `metadata.json` from exactly these (records of games not scanned are dropped; `--system` / `--limit` runs keep the others) |
| `run_metadata_dry_run` (B76) | the tool's `--dry-run` | the same games, counted per system |
| `run_cheat_update` (`games/cheat_importer.py`) | the tool `tools/update_game_cheats.py` | the same games; for each with a matched metadata record, its system's cheat folder; **a system outside `cheat_system_specs()` with a matched record raises `CheatError("Unsupported game system")`, which the loop does not catch (only its subclass `ProviderUnavailable`)** |
| `run_startup_metadata_reconcile` (`games/startup_reconcile.py`) | a daemon thread `GamesPlugin.__init__` starts in the companion | the discovered ids, compared with `metadata.json`'s ids (`library_changed`) and its incomplete records |

No other caller in `companion/` or `tools/` (the tests: B76 / B78 patch it out).

**Why `GamesPlugin.__new__`:** the scan needs only `_scan` (its statics, `GAMES_ROOT`, the lock and cache fields).
`__init__` builds the emulator, stream and recovery objects against the class's own `PROJECT_ROOT` (the code's root,
not the argument), writes recovery config rows when knobs ask, and **starts the startup reconcile thread, which calls
`scan_privyhub_games` itself** — constructing in the scan would start a new reconcile per scan, without end. The
history has no rationale (it arrived with the Phase A7 checkpoint, 2026-09-09). The instance's `SYSTEMS` is set only in
`__init__` (B49 / B59 / B69), so `__new__` left the class's four: **the bug**.

**A second side effect found while settling (it decides the design):** `from plugins.games import GamesPlugin` first
runs `companion/plugins/__init__.py`, which **constructs every plugin** (`PLUGINS = {…, "games": GamesPlugin()}`). So
every run of either tool built a full `GamesPlugin()` for the code's own root — the hub's — and started the startup
reconcile in the tool's process. Probed on a scratch export of HEAD (network blocked): the scan's import left the thread
`PrivyHubGameMetadataReconcile` running, which ran a full metadata update on the copy's root and wrote
`data/games/metadata.json` and four logs there. On the hub, `logs/games/game_metadata_startup_reconcile.json` reads
`RUNNING`, written 00:33:31Z on 2026-11-10 — 79 s after ART-1's companion restart, 41 s into its dry-run step —
consistent with a tool process exiting mid-reconcile (counts only read; nothing of the hub's written). **With the
systems fixed and nothing else, A's next dry run (the three flags + `PRIVYHUB_ART_SYSTEMS=1` in its environment) would
start that reconcile in the background, see N64 / PS2 / GameCube as new (`library_changed`), and fetch their art —
titles sent to the picture server before the user's "fetch".** So B82 also stops the tools' scan from building the
companion's plugins.

## The change

1. **`companion/plugins/games.py`** — the shared systems builder, factored out of `__init__`:
   - `@classmethod listed_systems(cls) -> dict`: `cls.SYSTEMS` itself when none of `_ps2_session` / `_n64_session` /
     `_gc_session` is imported (absent); else `{**cls.SYSTEMS, ps2…, n64…, gamecube…}` in `__init__`'s order with
     `__init__`'s entries (name, `folder: None`, `extensions: set()`). The same import-time flags the running hub reads.
   - `__init__`: `systems = type(self).listed_systems()`; `self.SYSTEMS = systems` only when it is not the class dict
     (absent: no instance attribute, as today). The rest of `__init__` untouched.
   - `@classmethod folder_available(cls, project_root, system_id) -> bool`: read-only, the folder `_scan` reads for
     that system — `ps2`: `read_paths(root)["games_dir"]`; `n64` / `gamecube`: `read_dir(root)` (the paths file
     `PRIVYHUB_PS2_PATHS` names, else `runtime/h3_p1_paths.txt`, as the hub); the hub's own systems:
     `<root>/games/<folder>`; available = named and a directory. No `mkdir`, nothing written.
2. **`companion/games/metadata_importer.py`**:
   - `_games_plugin_module(project_root)`: the `plugins.games` module **without running `plugins/__init__.py`** when
     the package is not imported yet (the tools): a bare package object for `plugins` (its `__path__` the companion's
     `plugins/`) is placed in `sys.modules` for the import of `plugins.games` only, then removed (a later `import
     plugins` in the same process runs the real `__init__`, reusing the module). When `plugins` is already imported
     (the companion; its reconcile thread), the import is today's. The `sys.path` insert / removal as today.
   - `scan_privyhub_games`: the same `__new__` scanner (the reconcile recursion still rules out `__init__`) with
     `scanner.SYSTEMS = GamesPlugin.listed_systems()` when that is not the class dict. So **the scan's systems are the
     list's systems**, flags and paths file read the same way.
   - `listed_privyhub_systems(project_root) -> {system_id: {"folder": "available" | "unavailable"}}` over
     `listed_systems()` with `folder_available` (read-only).
   - `run_metadata_dry_run`: **with `PRIVYHUB_ART_SYSTEMS=1` only** (B76's knob; absent = today's report): every listed
     system in the fetcher's map gets a row even with zero titles (the same five counts); a new key
     `listed = {system_id: {"titles": n, "folder": "available" | "unavailable" | "not_listed", "list": "available" |
     "unavailable" | "not_needed"}}` for every row — `list` "unavailable" when the system's titles came back
     `provider_unavailable` (RetroArch's list could not be had), "not_needed" with zero titles (no list is read for an
     empty system), else "available"; `folder` from `listed_privyhub_systems` ("not_listed" only for a test's `games=`
     fixture system the hub does not list). **"list unavailable" and "folder unavailable" are told apart.**
3. **`tools/update_game_metadata.py`** (`--dry-run` text, not `--json`): when the report has `listed`, after a system's
   row one line `  folder unavailable (the drive or folder is not reachable)` or `  list unavailable (RetroArch's list
   could not be read)`. Without `listed`: today's text.
4. **`companion/games/cheat_importer.py`**, `run_cheat_update`: after the scan (and `--system` / `--limit` as today),
   games of a system outside `cheat_system_specs()` are not processed: counted per system in `not_offered`, which is in
   the report only when non-empty (absent: never). No record, no request, no error for them; manifest records outside
   the selection are kept as today (the partial-run rule). This removes the uncaught `CheatError` a full cheat run would
   hit on the first PS2 / GameCube title with a matched record (after ART-1's fetch), and on N64 with
   `PRIVYHUB_N64_CHEATS=0` (B78's kept refusal; its test changes to the new behaviour, disclosed).
   `tools/update_game_cheats.py` text: a line `<system>: n not offered (no cheat list for this system)` per entry when
   present.
5. **`companion/games/startup_reconcile.py`: unchanged.** It uses the scan, so with the flags its discovered ids include
   the three systems; without them, today's.

## What changes on the hub (for A; disclosed in the record)

- **The first companion start with B82** (the three flags on, `PRIVYHUB_ART_SYSTEMS` off in the companion): the
  reconcile discovers N64 / PS2 / GameCube titles absent from `metadata.json` → `library_changed` → one full metadata
  update in the companion. The three systems are not in the fetcher's map there, so their titles get
  `provider_unavailable` records **without any request**; PS1 / SNES are re-matched as on any library change (their art
  already cached). Those records count as incomplete, so the reconcile repeats the update at a companion start at most
  once per 7 days until ART-1's fetch replaces them (on "skip", it keeps doing so — a next-queue item, listed).
- **Tool runs stop starting a reconcile in their own process** (no `PLUGINS` built by the tools): the stale `RUNNING`
  status is rewritten at that restart.
- `metadata.json`'s records for a system whose drive folder is unreachable at a full update are dropped (today's rule
  for every system; listed for the next queue, not changed here).

## Tests (through the real path; `tests/art_systems/test_b82.py`; network blocked at the socket in every child)

A fixture tree per test: a copy of `companion/` and the two tools; `games/{nes,snes,genesis,ps1}` with fake files of the
right extensions; fake in-place folders for PS2 / N64 / GameCube named by a fake `runtime/h3_p1_paths.txt`; GameCube
files ≥ 1 MiB (sparse); made-up titles only; a fake provider = RetroArch's lists for all seven systems in the provider
cache (fresh), box art present. Each run is a child `python3 -I` with only the test's `PRIVYHUB_` values; a socket
connect / `urlopen` fails the child and is counted.

- `scan_privyhub_games` → seven systems with the three flags, four without (today's ids and titles); **the registry not
  built and no reconcile thread in the tool's process**; the in-place folder unreachable → that system's titles 0.
- The metadata CLI `--dry-run --json` with `PRIVYHUB_ART_SYSTEMS=1` + flags → counts for all seven (nes / genesis zero
  rows), `listed` folder / list states; one in-place folder missing → "folder unavailable"; one system's list missing →
  "list unavailable"; nothing written; no request. Absent → the report byte-equal to HEAD's tool on the same tree.
- The cheat CLI `--system n64 --no-download --json` with `PRIVYHUB_N64=1` → the N64 titles (total and the matched one);
  a full run with the three flags after matched records exist → no error, PS2 / GameCube `not_offered`.
- The startup reconcile through the companion's own construction (`from plugins import PLUGINS`, the thread joined) →
  without the flags: `SKIPPED_CURRENT` for the four (as HEAD); with them: `library_changed`, the three systems'
  titles included, their records `provider_unavailable`, the four's records still matched, no request.
- **The regression:** the seven-system scan and the no-registry test fail on HEAD's code (run and recorded).
- Absent: the scan, the dry run and the cheat report on a tree without the flags = HEAD's, byte for byte.
- Temp dirs removed at exit (B53's helper); the suite run 3 times; mutations of the new lines.
