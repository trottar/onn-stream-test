# B82 — absent (none of `PRIVYHUB_PS2` / `PRIVYHUB_N64` / `PRIVYHUB_GAMECUBE`, no `PRIVYHUB_ART_SYSTEMS`) = today, hunk by hunk (`b82.diff`)

| file | hunk | absent |
| --- | --- | --- |
| `companion/plugins/games.py` | `listed_systems()` (the builder, moved out of `__init__`) | no flag module imported → returns the class dict itself; `__init__` sets no instance attribute (as HEAD) — `proof_init_systems_run.txt`: the constructed plugin's systems equal HEAD's for all 8 flag combinations, the instance attribute present exactly when HEAD's is |
| | `folder_available()` | read only by the dry run's `listed`, which exists only with `PRIVYHUB_ART_SYSTEMS=1` |
| `companion/games/metadata_importer.py` | `_games_plugin_module()` | the companion (`plugins` imported): HEAD's import. The tools: `plugins/__init__.py` no longer runs in their process — **the one deliberate difference with everything absent**: no `PLUGINS` registry, no `GamesPlugin()` for the code's root, no startup reconcile thread in a tool run (HEAD started one per run). The tools' output is unchanged (below) |
| | `scan_privyhub_games`: `scanner.SYSTEMS` from the builder | absent → the class dict → not assigned → HEAD's scan |
| | `listed_privyhub_systems()` | called only under `PRIVYHUB_ART_SYSTEMS=1` |
| | `run_metadata_dry_run`: zero rows + `listed` | only under `PRIVYHUB_ART_SYSTEMS=1`; absent → HEAD's report |
| `tools/update_game_metadata.py` | two text lines per system | only when the report has `listed` |
| `companion/games/cheat_importer.py` | the not-offered filter + `not_offered` | absent → every scanned system (the four) is in `cheat_system_specs()` → nothing filtered, no key |
| `tools/update_game_cheats.py` | one line per not-offered system | only when the report has `not_offered` |
| `companion/games/startup_reconcile.py` | — (unchanged) | |

**Byte for byte, measured** (`scripts/proof_absent.py` → `proof_absent_run.txt`): the same fixture tree built once with
HEAD's code (`/tmp/b_q20ad_base`) and once with B82's; each run in a child with no `PRIVYHUB_` value, the network
blocked; outputs compared after the tree's own path is replaced and `generated_unix_ms` masked:

- the scan's games (ids, titles, systems, relative paths);
- `update_game_metadata.py --dry-run --json`, `--dry-run` (text), `--dry-run --json --offline`;
- `update_game_cheats.py --no-download --offline --json` and its text.

All six **SAME**, return codes equal, 0 network attempts either side (`DIFFS 0`). The tests
`test_four_systems_without_the_flags`, `test_absent_is_todays_report`, `test_absent_flags_nothing_counted` pass on
HEAD's code too (`tests_on_head_regression.txt`).
