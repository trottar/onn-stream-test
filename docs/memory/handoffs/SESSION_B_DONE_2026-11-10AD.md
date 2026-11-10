# SESSION B — done, 2026-11-10 AD (QUEUE_2026-11-10AD: B82 the scan sees every system, B83 the real-entry-point audit of B76-B81; run 01:32-02:15Z)

- **Baseline:** `8813f06a` (ART-1's stage 1 and its skip committed).
- **Checked first:** only the companion and `privyhub-diag` active. The first two reads found ART-1's close
  uncommitted (`CURRENT.md`, `art1_2026-11-10/redact_check.txt`); B stopped and said so both times. The third read
  found `git status --short` empty (the prompt files tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no companion or keeper restart; no stream, no adb, no sudo, no nft; no APK;
  - `privyhub-diag` and `~/privyhub_diag/` untouched;
  - **nothing fetched** (providers faked); **no emulator started**; nothing written to the drive;
  - **the real drive and library not scanned by B** (fixture trees only; the title check does not list them either);
  - of the hub's own, B read only the reconcile status file's result and time, and the names of the companion's
    `PRIVYHUB_` lines (from ART-1's record); nothing of A's touched; nothing deleted.

## What was broken, and what the audit found

| Item | What was broken / found | Done |
| --- | --- | --- |
| **B82** (ART-1's defect) | `scan_privyhub_games` built its scanner with `__new__`, so it saw the class's four systems only: no N64, PS2 or GameCube for the art tool, the N64 cheat tool or the startup reconcile | `GamesPlugin.listed_systems()` is now the one systems builder (the constructor and the scan); the dry run lists every system, zero-title ones too, and tells "folder unavailable" from "list unavailable" (with the art knob) |
| **B82** (found while settling) | the scan's import ran `plugins/__init__.py`, which **builds every plugin**: every tool run built a `GamesPlugin()` for the hub and **ran the startup reconcile — a full metadata update — inside the tool**. On the hub the reconcile's status has read `RUNNING` since ART-1's tool runs. **With the scan fixed alone, A's next dry run would have fetched the three systems' art in the background before your "fetch".** | the tools load the plugin module without building the registry; the companion's import unchanged |
| **B82** (found) | a full cheat run would stop with `CheatError` at the first PS2 / GameCube title with a matched record (after the fetch), and on N64 with `PRIVYHUB_N64_CHEATS=0` | such systems are counted as `not_offered` and skipped |
| **B83** B76 | tested in-process with fixture games; the scan and the CLI never reached → **broken (the scan)** | fixed by B82; now the CLI dry run (B82) and the CLI fetch → art cache → the plugin's details (B83) |
| **B83** B77 | the launch reached; the profile made off the plugin, on a made-up id | sound; now the plugin's create / assign handlers → launch → PCSX2 / Dolphin pad files |
| **B83** B78 | the tool with the scan patched out; the list and the staging off the plugin and off the launch → **broken (the tool's scan)** | fixed by B82; now the handler's list → launch → `.cht` staged for Mupen64Plus-Next |
| **B83** B79 | the launch reached; the list off the plugin; the bundled reader faked | sound; now the handler with a fake Dolphin AppImage read by the real `7z` → launch |
| **B83** B80 | the plugin built with `object.__new__` and its parts replaced by lambdas; `7z` faked | sound; now `details` / `ps2-patches` on the real plugin, a real `patches.zip` read by `7z` → launch. **Its own suite missed a wrong bundle path** (B83's catches it) |
| **B83** B81 | the list off the plugin; PS1 staging internal | sound; now the folders at the handler's first list; a `.pnach` and a `.cht` listed and staged by launches |

- **Tests:** B82 15 (×3), regression: 12 of 15 fail on HEAD's code (the three absent ones pass); mutations 10 / 10. B83
  8 (×3); on HEAD: B76 and B78 fail, the rest pass; mutations of the items' code 7 / 7. `tests/art_systems` 112 / 112.
  Every child run blocked the network: 0 attempts throughout.
- **Absent:** with none of the three system flags and no `PRIVYHUB_ART_SYSTEMS`, the scan and both tools' output are
  byte-equal to HEAD's (6 / 6); the plugin's systems equal HEAD's for all 8 flag combinations.
- **The tree checks:** HEAD + `b82.diff` + `b83.diff` in order = the work copy; reversed → HEAD's export (0
  differences; `git diff --check` clean). Every host suite on full exports of HEAD and of HEAD + B82 + B83: 73 each,
  the 72 others read the same, `tests/art_systems` 89 → 112 green, the same six `tools/` suites fail in both (as queues
  AA / AC: fixtures under `docs/` / `logs/`) — `b83_2026-11-10/tests_host_compare.txt`.
- **Listed for the next queue (B82's record):**
  - the restart's reconcile writes 155 `provider_unavailable` records for the three systems; they are retried at a
    companion start at most once per 7 days until ART-1's fetch replaces them (for good after a "skip");
  - a full metadata update drops the records of titles it did not scan (a drive folder unreachable at that moment).

**One line for the user:** the box-art tool can now see your N64, PlayStation 2 and GameCube games. It also no longer
does a hidden library update of its own each time it runs — that would have fetched pictures before you said "fetch".
Everything else built yesterday was checked the way the hub really uses it and works.

## A — ART-1 again, from stage 1 as written (`SESSION_B_DONE_2026-11-09AC.md` § "A — ART-1"), with these changes

1. **Preconditions:** HEAD with **queue AD committed** and the tree clean — if B82 / B83's files are uncommitted, stop
   with "YOU, now: commit queue AD first, then send the read line again". The rest as written (`/tmp` ≥ 1 GB free,
   `TMPDIR` on the main disk; **eighteen** `PRIVYHUB_` lines — queue AD adds none; `--check` ok; `85220f99…` CONFIRMED;
   only the two units).
2. **The companion restart loads B82** (`systemctl --user restart privyhub-companion`); the checks as written.
   **Expected, new:** the startup reconcile finds the three systems' titles new and runs one full metadata update —
   read `logs/games/game_metadata_startup_reconcile.json` (counts only) until its result is not `RUNNING` (its stale
   `RUNNING` from ART-1's tool runs is rewritten): `RECONCILED`, reasons `library_changed`, discovered = the list's
   total, `metadata_update_counts.provider_unavailable` = **155** (N64 13 + PS2 115 + GameCube 27: no request — the art
   knob is not in the companion). Any other result → stop and report. Then the dry run.
3. **The dry run** as written (the companion's `PRIVYHUB_` environment plus `PRIVYHUB_ART_SYSTEMS=1` in that command
   only; `--dry-run --json`; the disclosure of RetroArch's three whole lists). **It must show seven systems before the
   reply:** `listed` holds `nes`, `genesis`, `ps1`, `snes`, `n64`, `ps2`, `gamecube`; `listed[s].titles` = **the
   list's counts — N64 13, PS2 115, GameCube 27** (PS1 72, SNES 44; NES / Genesis 0), equal to the onn's systems
   list; every `folder` "available". A `folder` "unavailable" → stop ("YOU, now: the games drive is not reachable");
   a `list` "unavailable" → report it in the reply (RetroArch's list for that system could not be read). The tool no
   longer starts a reconcile of its own (check: the reconcile status file unchanged by the dry run).
4. **Reply, fetch, record:** as written. On "fetch": `--system n64`, `--system ps2`, `--system gamecube` (the art knob
   in each command only); then `PRIVYHUB_N64=1 tools/update_game_cheats.py --system n64 --no-download` (now: the N64
   titles, with cheats for those with a matched record), then without `--no-download`. The read-back as written.

## A — HOME-12 (as queue AC sketched it in `SESSION_B_DONE_2026-11-09AC.md` § "A — HOME-12")

- **B83 changed no cell.** C44 (art / details) needs ART-1's fetch, as before. C46's N64 cheat list exists only after
  ART-1's cheat fetch; the drop-in folders in C46 appear at the first Cheats list (B83 confirmed it through the
  plugin's handler). The stage-1 precondition reads "the companion restarted with queue AD (ART-1 step 2)".
- The APK is still `de6682dbaf00237c2f6477b68df4fa00e320c0a403ccb2d28863344dee86de28` (queue AD has no client part);
  the CONFIRMED rule, the properties (eighteen) and the close as written.

## Files

- **Records:** `evidence/B82_SCAN_ALL_SYSTEMS_2026-11-10.md`, `evidence/B83_REAL_ENTRY_AUDIT_2026-11-10.md`, each with
  its dir (the design + hash, the diff, the absent proof, the tests ×3, the regression / HEAD runs, the mutations, the
  scripts, redact / title checks, the manifest); the host-suite comparison and the tree checks in `b83_2026-11-10/`.
- **Patch notes:** `patches/B82_SCAN_ALL_SYSTEMS.md`, `patches/B83_REAL_ENTRY_AUDIT.md` (not indexed: nothing adopted).
- **The tree:** `b82.diff` then `b83.diff` applied, uncommitted (`companion/plugins/games.py`,
  `companion/games/metadata_importer.py`, `companion/games/cheat_importer.py`, the two tools,
  `tests/art_systems/test_b78.py`, new `test_b82.py` / `test_b83.py`).
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue AD line and section), `docs/ROADMAP.md` (§H6, the queue AD
  paragraph). **Logs:** `logs/b82_git_status.txt`, `logs/b83_git_status.txt`; `handoffs/SESSION_B_STATUS.txt` (the
  queue line and B's checklist with the new standing rule).
- **Left (not deleted):** `/tmp/b_q20ad_base`, `_after_b82`, `_work`, `_scratch` (companion/, tools/, tests/; the base
  and the work copy also hold the `docs/CHEATS.md` copy and the `logs/` the host suites wrote — see the comparison
  file); `~/.cache/b_q20ad_tmp/` (the runs' outputs, the `docs/CHEATS.md` copy, the older suites' own temp dirs, which
  they do not remove). B82's and B83's own tests leave no temp dir.
