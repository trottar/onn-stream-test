---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 0eb115d9 (B56 built in /tmp/b_q12t_b56; applied to the tree with queue T's combined diff, uncommitted)
---

# B56 — H0 import slice 1a, PS1: `tools/import_usb.py` inspect / plan / apply / verify, behind `PRIVYHUB_IMPORT=1`

**Classification: SETTLED + BUILT** behind `PRIVYHUB_IMPORT=1` (the tool and the list's marks). B45's contract with
the user's four answers (2026-11-08):
1. a real BIOS when present, OpenBIOS only as a labelled fallback;
2. multi-disc titles as one entry with an auto-made `.m3u`;
3. a "NEW" tag for 7 days;
4. an `.iso` hidden when a `.chd` of the title exists.

- **Tests:** `tests/import_usb` **21** green ×3. In the copy 20 run and the git-ignore check skips (the copy has no
  `.git`); in the tree all 21 run. Every host suite is as the baseline copy.
- **Mutations:** 10. **M10 survived the first run**: no test had a wrong-size BIOS file. The test was strengthened
  and M10 is caught; all 10 caught (`b56_2026-11-08/tests_mutations.txt`).
- **Proof:** absent = the tool refuses (exit 9) and writes nothing; the list is today's byte for byte
  (`b56_2026-11-08/proof_flag_absent.md`).
- **Nothing imported:** fixture trees only; no real USB, no real game file read. The library's file types were
  counted by name only.
- No client change needed (the list shows the host's names). NOT ADOPTED; nothing committed.

Design `b56_2026-11-08/design_written_before_code.md`, sha256 `7ce3bd8d…4484e37f`, hashed **18:36:30Z, before any
B56 code**.

## 0. Settled

- **The library** is `<repo>/games/ps1/`, on the hub's own disk (`/`, ext4; not the drive).
  - Today it holds cue sets only: 80 `.cue`, 338 `.bin`, no `.chd` / `.iso` / `.m3u` / `.pbp` (counts only).
  - The list takes `.chd .cue .m3u .iso`; the launch takes `.chd .cue .m3u`.
- **The PS1 BIOS folder** (RetroArch's `system_directory`, `data/games/retroarch/system/`) **is empty**, so the core
  runs on its built-in OpenBIOS (B45's inference).
  - The real names: `scph5500.bin` (JP), `scph5501.bin` (US), `scph5502.bin` (EU), each 524,288 bytes.
  - BIOS files are checked by name and size only; no content hash appears in any record (the queue's rule).
- **The metadata the list reads.**
  - The onn shows each node's host-given name, so "· NEW" and "(OpenBIOS)" need no client change.
  - `metadata.json` cannot hold the marks: the metadata update rebuilds each entry and drops unknown keys.
  - So the marks are **`data/import/marks.json`**, which the list reads beside it, behind the same flag in the
    companion.
- **The duplicate check against the library is size-gated.** Only library files whose size equals a candidate file's
  are hashed, so the 80-title library is never read wholesale.
- **The title rule.**
  - An `.iso` whose title has a `.chd` (library or stick) → "duplicate: chd present".
  - A library `.iso` alone gives way to an arriving `.chd`, and the `.iso` is hidden.
  - Any other title already listed → "duplicate: title present" (two entries for one title would split saves and play
    counts; to replace one, the user removes the old one first — disclosed).
- **Paths.**
  - Plans: `data/import/plans/`. Logs: `data/import/logs/`. Applied records: `data/import/applied/`. Marks:
    `data/import/marks.json`.
  - All of them, the library and the BIOS folder are git-ignored (`git check-ignore` in the tree,
    `b56_2026-11-08/git_check_ignore.txt`).
  - **A hand-copied `PrivyHub-Import/` in the repo would not be ignored:** a one-line `.gitignore` follow-up (not done
    here: outside the item's files).

## 1. Built (`b56_2026-11-08/b56.diff`, 5 files)

**`tools/import_usb.py` (new).** Every command first requires `PRIVYHUB_IMPORT=1`, else exit 9 before any path is
opened.

- **`inspect <mount>`** (no hashing, no writes):
  - the candidates `chd` / `cue_set` / `m3u_set` (a stick `.m3u`, or discs grouped by `(Disc N)` with the `.m3u` to be
    made) / `iso`;
  - the rejections: `unknown_type`, `bin_without_cue`, `pbp_not_supported`, `cue_missing_file`, `cue_case_mismatch`,
    `cue_outside`, `bin_claimed_twice`, `multidisc_gap`, `symlink`, `bad_name`, `m3u_bad_entry`; hidden helper files
    are counted and ignored;
  - the BIOS on the stick (region labels) and in the core's folder.
- **`plan <mount>`:**
  - the headers: CHD `MComprHD` v4/5; the cue's data track sector 16 `\x01CD001` + `PLAYSTATION` (MODE2 +24 / MODE1
    +16), track sizes a multiple of 2,352 → `bad_header` / `not_ps1_disc`;
  - sha256 of every file;
  - the duplicates: the library first (size-gated), then inside the stick, then the title rule, then a target with
    other bytes (`target_exists_different`, never renamed);
  - the destinations under `games/ps1/` (the stick's relative path), the made `.m3u` beside its discs, the files'
    order (tracks / discs first, **the entry last**);
  - the game ids (the plugin's rule; a test holds them equal);
  - `hide` (library `.iso`s with a `.chd` title);
  - the BIOS to copy (never over an existing file);
  - the space (+10 %);
  - written to `data/import/plans/<UTC>.json` (names inside: local, ignored), with a **labels-only** summary on the
    terminal (`--names` adds the names).
- **`apply [<plan>]`:**
  - refuses while a game is active (`--while-playing` overrides); runs at `nice 10`;
  - every accepted source is re-hashed against the plan (`source_changed`); the space is checked again;
  - per file: a `.import-<cid>-<n>.part` beside the target (opened `x`, so a stale part is never ours), copied with
    the hash, `fsync`, the directory `fsync`ed, verified, then `os.link` into place (never over a file) and the part
    removed. The entry goes last, then the made `.m3u` the same way;
  - **a failure rolls back that candidate:** only this run's parts and finals, and the directories it made and left
    empty;
  - then the BIOS (the same way, into the core's folder), `marks.json` (temp + rename: `new`, `hide`), the applied
    record, and **the sanitized log** (labels, kinds, counts, bytes, decisions, codes, BIOS regions; no filename,
    title, folder, hash, mount or volume).
- **`verify [<plan>]`:** re-hashes what apply placed.
- **Exit codes** as B45 §3.2, plus 9 (the flag).

**`companion/import_marks.py` (new) and `plugins/games.py` (4 hunks, all behind `_import_marks is not None`):**
- `_scan` leaves out the hidden ids;
- the game nodes get " · NEW" within 7 days of import;
- the PlayStation node reads "PlayStation (OpenBIOS) (N)" while no real BIOS file (name and size) is in the core's
  folder.

**`docs/IMPORT.md`** (new): the user's steps in plain words — the layout, the commands, what the TV shows, the BIOS
and save states, what the log shows.

## 2. Tests (`tests/import_usb/test_import_usb.py`, fixtures built from bytes in a temp dir, removed at exit)

- **The flag:** four non-`1` values × the four commands → exit 9, the fixture tree unchanged.
- **inspect:** every type and rejection code; labels only without `--names`; a bin named by two cues; the BIOS report
  (a real US file, an unknown name, a wrong size; "the core uses its built-in OpenBIOS").
- **plan:**
  - the headers (CHD v3, another system id, no `CD001`, a short track);
  - the destinations, the made `.m3u`, the entry last;
  - **the ids equal the plugin's `_stable_id`** and `_clean_name`;
  - the space;
  - **the duplicates:** by hash under another name (`duplicate_of` the library id), inside the stick, **a library
    file of another size never hashed**;
  - **the `.iso` rules and hide:** `.iso` + `.chd` on the stick, a lone `.iso`, a library `.iso` giving way to an
    arriving `.chd`, a library `.iso` beside its `.chd`, a title already present;
  - a target with other bytes → `target_exists_different`.
- **apply:**
  - **end to end** (the stick made read-only and unchanged; the files, the `.m3u`'s text, no `.part` left, the BIOS
    copied, three NEW marks, verify OK, a second plan accepts nothing, **the real plugin `_scan` lists the disc set
    once**);
  - **a copy failing midway leaves nothing half-written** (the failed candidates' files and new directories gone; the
    one placed before the failure kept);
  - a verify mismatch → exit 5, rolled back;
  - a stale part never removed;
  - a source changed after the plan → not copied;
  - an existing final never overwritten;
  - a game active → exit 8;
  - a BIOS already in the core's folder → not copied.
- **The log:** no fixture name, title word, extension, BIOS name, path, the stick folder's name, sha256 or game id;
  labels and BIOS regions present.
- **The list:** " · NEW" at 1 day and not at 8; the hidden `.iso` gone; "(OpenBIOS)" with no BIOS and with a
  wrong-size file, gone with a real one; **the flag absent → today's list** (the `.iso` listed, no tag,
  "PlayStation (3)").
- **Git:** the five import paths are ignored (run in the tree).

## 3. For A (IMPORT-1, with the user's hand; `SESSION_B_DONE_2026-11-08T.md`)

The bench drop-in `PRIVYHUB_IMPORT=1` for the companion (the list's marks) and the same variable on the tool's
command line. The commands and rows are in the hand-off.

## 4. Files

`b56_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b56.diff`, **`queue_t_combined.diff`** (B54 + B55 + B56 against the baseline; applied to the tree);
- `proof_flag_absent.md`;
- `tests_import_usb_x3.txt`, `tests_in_the_tree.txt`, `tests_host_b56.txt`, `tests_host_combined.txt`,
  `tests_mutations.txt`, `git_check_ignore.txt`;
- `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B56_IMPORT_SLICE_1A.md`. The user's page: `docs/IMPORT.md`.
