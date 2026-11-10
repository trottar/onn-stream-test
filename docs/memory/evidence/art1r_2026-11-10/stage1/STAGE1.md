# ART-1R stage 1 (2026-11-10 02:16-02:21Z, unattended, no TV; outside 04:30-05:30Z)

The second ART-1, after queue AD (B82 / B83). The first run's record (`../art1_2026-11-10/`, `ART_1_2026-11-10.md`) is
kept as it is. No title, serial, game id or path in this folder.

- The read line ~02:16Z (`read_line_at.txt`). HEAD `1739c816` (queue AD = B82 / B83, committed; `head.txt`); the tree
  clean (`git_status_before.txt`: only this record's own new dir, made first).
- **Preconditions** (`check_before.json`, `units_before.txt`, `drop_ins_before.txt`, `tmp_free.txt`,
  `keeper_before.txt`, `systems_nodes_before.txt`, `drive_before.txt`): `/tmp` 5.7 GB free (the tools ran with
  `TMPDIR` on the main disk, off the repo); **eighteen** environ lines / drop-ins, `--check` (`tools/e3_state.py`) ok,
  `apk` **CONFIRMED** (`85220f99…`); only the two units; no game, no movie (RetroArch 0, encoder 0).

## ADDITION 1 — the hidden update inside the first ART-1's tool runs (read-only, before the restart; `addition1.txt`)

**None: no request, no record.** From the hub's own files:

- the reconcile status file (json + txt — the only two files written in 00:30-00:50Z): `RUNNING`, written
  00:33:31Z, reasons 0, discovered 0, metadata before 0, incomplete before 0, `metadata_update_invoked` false,
  `catalog_cache_invalidated` false, no `metadata_update_counts` — the tool's process ended before the reconcile
  even reached its decision (the decision writes `SKIPPED_CURRENT` or the counts; neither was written);
- the provider cache: PS1 2 files, SNES 6 files, **0 written in the window** (or since 00:30Z); no N64 / PS2 /
  GameCube folder existed;
- box art: 119 files, 0 written in the window;
- the metadata records: the file unchanged since 2026-11-09T06:54Z; 116 records (PS1 72, SNES 44), **0 stamped**
  since 00:30Z;
- the companion's journal: its own 00:32Z restart reconcile `SKIPPED_CURRENT` (1 line); nothing else.

## The companion restart 02:18:55Z (`restart_at.txt`; B82 live; no drop-in; nothing adopted)

- Up in ~2 s; MainPID serves 8765; eighteen environ lines, no `PRIVYHUB_ART_SYSTEMS` (`environ_after_restart.txt`);
  `--check` ok, CONFIRMED (`check_after_restart.json`); the drop-ins the same; the journal clean (`journal.txt`: 34
  lines, 0 error / warning / traceback); the keeper not restarted (unchanged); the systems' counts as before
  (`systems_nodes_after.txt`: SNES 44, PlayStation 72, PlayStation 2 115, Nintendo 64 13, GameCube 27).
- **The reconcile** (`reconcile_after_restart.json`, done 02:19:01Z, ~6 s): `RECONCILED`, reasons
  `library_changed`, discovered **271** (= the list's total 72 + 44 + 115 + 13 + 27), metadata before 116,
  incomplete before 3; the update's counts: total 271, matched 110, ambiguous 6, no match 0,
  **provider_unavailable 155** (N64 13 + PS2 115 + GameCube 27, no request: the art knob is not in the companion),
  art downloaded 0, cached 107, missing 3, errors 0 — as B expected. 0 cache or box-art files written by it.

## The dry run 02:19:27Z (`dry_run_at.txt`, `dry_run.json`, `dry_run_side_effects.txt`)

The companion's eighteen `PRIVYHUB_` lines plus `PRIVYHUB_ART_SYSTEMS=1` in that command only, `TMPDIR` on the main
disk: `python3 tools/update_game_metadata.py --dry-run --json` → exit 0, stderr empty.

**Seven systems listed**, every folder `available`:

| system | titles (= the list) | list | matched | ambiguous | no match | list unavailable | the misses (labels) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **N64** | 13 | available | **13** | 0 | 0 | 0 | — |
| **PS2** | 115 | available | **105** | 10 | 0 | 0 | `ps2-miss-1` … `ps2-miss-10` |
| **GameCube** | 27 | available | **26** | 0 | 1 | 0 | `gamecube-miss-1` |
| PS1 | 72 | available | 66 | 6 | 0 | 0 | `ps1-miss-1` … `ps1-miss-6` |
| SNES | 44 | available | 44 | 0 | 0 | 0 | — |
| NES | 0 | not needed | — | — | — | — | — |
| Genesis | 0 | not needed | — | — | — | — | — |

- `source_stats`: cache hits 8 (PS1 / SNES, inside their seven days), **downloads 9**, unavailable 13.
- **What it downloaded:** RetroArch's whole database files for the three new systems, cached per system — N64 the
  catalog + 5 detail lists (6 files), PS2 the catalog + 1 detail list (2), GameCube the catalog (1). (B's wording "one
  file per system" was the catalog; the detail lists come with it.) The 13 unavailable are detail lists that could not
  be fetched (PS1 4, PS2 4, GameCube 5) — so PS2 / GameCube details may carry fewer fields. **Nothing about the titles
  was sent.**
- **The reconcile status file unchanged by the dry run** (hash and mtime): the tool starts no reconcile now (B82).
  No box art written; the metadata records not written by it.
- The drive's folders after = before (`drive_after.txt`).

Waiting for the user's "fetch" or "skip".
