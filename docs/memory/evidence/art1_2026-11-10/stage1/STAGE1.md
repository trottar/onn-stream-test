# ART-1 stage 1 (2026-11-10 00:31-00:45Z, unattended, no TV; outside 04:30-05:30Z)

- The read line ~00:31Z (`read_line_at.txt`). HEAD `c9dcd8fd` (queue AC = B76-B81, committed; `head.txt`); the tree
  clean (`git_status_before.txt`: only this record's own new dir, made first).
- **Preconditions** (`check_before.json`, `units_before.txt`, `drop_ins_before.txt`, `tmp_free.txt`,
  `keeper_before.txt`, `systems_nodes_before.txt`, `drive_before.txt`): `/tmp` 5.7 GB free (the tools ran with
  `TMPDIR` on the main disk, off the repo); **eighteen** environ lines / drop-ins, `--check` (`tools/e3_state.py`) ok,
  `apk` **CONFIRMED** (the pin `85220f99…`); only the two units; no game, no movie (RetroArch 0, encoder 0, the games
  status inactive). The drive's folders: counts / bytes / listing hashes only.
- **The companion restart 00:32:12Z** (`restart_at.txt`; B77-B81's host parts live; no drop-in; nothing adopted):
  MainPID owns 8765; eighteen environ lines (`environ_after_restart.txt`); `--check` ok, CONFIRMED
  (`check_after_restart.json`); the drop-ins the same; the journal clean (`journal.txt`: 33 lines, 0 error / warning /
  traceback; the raw journal kept off the repo); the keeper not restarted (read again, unchanged); the systems' counts
  as before (`systems_nodes_after.txt`: SNES 44, PlayStation 72, PlayStation 2 115, Nintendo 64 13, GameCube 27).
- **The dry run 00:32:50Z** (`dry_run_at.txt`, `dry_run.json`): the companion's eighteen `PRIVYHUB_` lines plus
  `PRIVYHUB_ART_SYSTEMS=1` in that command only, `TMPDIR` on the main disk:
  `python3 tools/update_game_metadata.py --dry-run --json` → exit 0.

| system | total | matched | ambiguous | no match | list unavailable |
| --- | --- | --- | --- | --- | --- |
| PS1 | 72 | 66 | 6 (`ps1-miss-1`…`-6`) | 0 | 0 |
| SNES | 44 | 44 | 0 | 0 | 0 |
| **N64** | **not seen** | — | — | — | — |
| **PS2** | **not seen** | — | — | — | — |
| **GameCube** | **not seen** | — | — | — | — |

  `source_stats`: cache hits 8, **downloads 0**, unavailable 4. No RetroArch list was downloaded (PS1 / SNES from the
  cache of 2026-11-06, inside its seven days; the three new systems' lists never requested). Nothing about any title
  sent.

## Finding — B76's scan does not see N64 / PS2 / GameCube (blocks stage 2)

`scan_privyhub_games` (`companion/games/metadata_importer.py`, ~line 1268) builds the scanner with
`GamesPlugin.__new__(GamesPlugin)`, skipping `__init__` — and `__init__` is where PS2 / N64 / GameCube are added to the
instance's `SYSTEMS` (`companion/plugins/games.py` ~lines 200-208). The class `SYSTEMS` holds only the four original
systems, so the scan returns none of the three, and the dry run's `not_offered` is empty (they are not even counted).
Read-only diagnosis with the same environment (`scan_diagnosis.txt`): the scan → `ps1` 72, `snes` 44; class `SYSTEMS`
= genesis / nes / ps1 / snes; `system_specs()` with the knob = all seven. B76's tests pass `games=` fixtures, so they
never exercised the real scan.

The same scan feeds `companion/games/cheat_importer.py` (~line 1068, B78's N64 cheats) and
`companion/games/startup_reconcile.py` (~line 242). So stage 2 as written (`--system n64 / ps2 / gamecube`, then the
N64 cheat tool) would find no titles: nothing sent, nothing fetched — and HOME-12's C44 (art) and C46 (an N64 cheat)
have nothing to show.

**Stopped here** (no fetch; nothing patched, nothing adopted, nothing committed). The fix is session B's: the scan
must give the scanner the instance `SYSTEMS` `__init__` builds (or construct the plugin properly), with a test on the
real scan path, not a fixture. Then ART-1 runs again from stage 1.
