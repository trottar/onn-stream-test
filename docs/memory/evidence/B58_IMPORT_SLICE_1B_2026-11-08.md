---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: d618a20a (B58 built in /tmp/b_q13u_b58 on the baseline; applied to the tree after B57, uncommitted)
---

# B58 — H0 import slice 1b: a plain source folder, SNES / NES / Genesis, the journal's resume — behind `PRIVYHUB_IMPORT=1`

**Classification: SETTLED + BUILT** behind `PRIVYHUB_IMPORT=1` (the tool; the list's journal hiding).
- **Tests:** `tests/import_usb` **40** green ×3 (B56's 21 unchanged + B58's 19). In the copy 38 run and the two git
  checks skip (no `.git`); in the tree all 40 run. Every host suite as the baseline copy, the combined copy too.
- **Mutations:** 16. **M10 and M16 survived the first run** (no test put a matching hub file outside `games/` in the
  journal; none re-applied a plan after a complete apply). Both tests strengthened; all 16 caught
  (`b58_2026-11-08/tests_mutations.txt`).
- **Proof:** absent = the tool refuses (exit 9) in both forms and writes nothing; the list is today's
  (`b58_2026-11-08/proof_flag_absent.md`).
- **Nothing imported:** fixture trees only (synthetic cartridge headers made in the tests); no real game file read,
  nothing written to the drive. The hub's library was counted by file name only.
- No client change (the list shows the host's names). NOT ADOPTED; nothing committed.

Design `b58_2026-11-08/design_written_before_code.md`, sha256 `f07fb24a…6a18cfdb`, hashed **19:53:20Z, before any
B58 code**.

## 0. Settled

**The systems the hub lists today** (`plugins/games.py` `SYSTEMS`; the library is `<repo>/games/<folder>/`, scanned
recursively, a file listed when its suffix is the system's and its name does not start with `.`):

| system | library folder | accepted | header check | today's library (by name) |
| --- | --- | --- | --- | --- |
| NES | `games/nes/` | `.nes` | `NES\x1a` at 0 | empty |
| SNES | `games/snes/` | `.sfc` `.smc` | the size less a 512-byte copier header (present when `size % 1024 == 512`) a whole KiB count ≥ 32; the internal checksum + complement = 0xFFFF at LoROM / HiROM / ExHiROM | 44 `.sfc` |
| Genesis | `games/genesis/` | `.md` `.gen` `.bin` | `SEGA` within 0x100-0x10F (a `.bin` without it refused) | empty |
| PlayStation | `games/ps1/` | B56's (`.chd`, cue sets, `.m3u` sets; `.iso` rules) | B56's | 80 `.cue`, 338 `.bin`, 1 other |

- The tool's extensions equal the plugin's (a test reads `SYSTEMS`).
- **Anything else in a cartridge folder** (an archive, a text file, a save) → `unknown_type`; zipped games are not
  imported (the list does not take archives either).
- **N64 / GameCube:** the layout only (B45's reserved `games/n64/`, `games/gamecube/`); `inspect` lists such a folder
  "not supported yet" with its file count; `plan` plans nothing.
- **PS2: not imported.** A `games/ps2/` folder → "PS2 games stay on the external drive and are listed from there - not
  imported"; nothing planned (B49 lists PS2 in place).
- Another folder → reported as "not a system the hub lists" (its name only with `--names`; the log has the code
  `unknown_system_folder`).
- **The duplicate check per system** (B56's, against that system's library folder): by hash (size-gated), inside the
  source, by title (the plugin's clean name; PS1 also drops the disc number), a target with other bytes. A headered and
  a headerless SNES dump of one title differ by hash; the title rule catches the same name (disclosed).
- **NEW: every system** (`marks.json` `new` is by game id; the list's tag is system-blind). **Hidden duplicates: PS1
  only** (B56's `.iso` beside a `.chd`); a cartridge title in a second format is "duplicate: title present" and is not
  placed, so nothing needs hiding.
- **The journal.** Before B58 a crash or power loss mid-apply left its `.import-*.part` (never removed by B56: not this
  run's) and any finals linked before it; a multi-disc set whose made `.m3u` had not landed showed its placed discs as
  separate entries.

## 1. Built (`b58_2026-11-08/b58.diff`: `b58_code.diff` + `b58_docs.diff`; 5 files)

**`tools/import_usb.py`:**
- **Two source forms, the same inspect / plan / apply / verify:**
  - **the stick (as B56):** `inspect|plan <mount>` — every system folder under `PrivyHub-Import/games/` (ps1, snes,
    nes, genesis planned; n64, gamecube, ps2 and others reported); PS1's BIOS from `bios/ps1/`;
  - **a plain folder (new):** `inspect|plan --source <folder> --system <ps1|snes|nes|genesis>` — that system's games
    folder itself, read in place (**no symlink root**); `--system ps2|n64|gamecube` reports and plans nothing (exit
    3); the hub's own library refused as a source (exit 2); no BIOS (the stick's `bios/ps1/` only). A mount and
    `--source` exclude each other; `--source` needs `--system`.
- **Per system:** PS1 as B56; a cartridge file = one candidate (kind `rom`), the target `games/<system>/<the relative
  path>`, the header check, `copier_header` recorded for SNES; the labels `T1…` run across systems; every row carries
  its `system`; the ids are the plugin's.
- **The plan** adds `source_form`, `systems`, `reported`, `journal_pending`; the plain form's plan equals the stick
  form's on the same files in all else (a test, per system).
- **The journal `data/import/journal.json`** (durable: temp + `fsync` + rename + the folder `fsync`):
  - an entry per candidate **before its first file** (targets, parts, pre-existing targets, the folders it would make,
    the hashes, the list ids) and removed after its last file or its in-process rollback; the BIOS copy too;
  - **the next `apply` reads it first** (after the active-game check): that candidate's own parts, the finals it
    linked (only targets not pre-existing, only with the journal's bytes; any other file is left and reported
    `journal_conflict`, exit 4) and the folders it made (if empty) are removed; the entry dropped. Paths outside
    `games/<system>/` (or the PS1 BIOS folder) are never followed;
  - if this apply's plan accepts the candidate, it is copied again from the start → **resumed**; otherwise
    **cleaned**;
  - **a title an interrupted run placed whole** (every target with the plan's bytes) is `already_placed`, not copied
    again, and gets the NEW mark that run never wrote (a NEW date already there is kept);
  - `inspect` / `plan` report "An interrupted import was found (N title(s))"; `plan` treats the journal's half-placed
    files as absent (not "already in the library", not a target clash), so the title is accepted again.
- **The log:** + the form, the systems, the reported folders by code (never a folder's name), the journal's results;
  still no name, path, hash, id or mount.

**`companion/import_marks.py`:** `pending(project_root)` — the journal's list ids (never raises).
**`plugins/games.py`:** B56's hidden-ids line also leaves out `pending` (inside `_import_marks is not None`): **a title
being copied, or left half-placed, is not listed.** Without the companion's flag the list reads no journal: an
interrupted multi-disc set could show its placed discs until the next apply cleans them (disclosed; a single-file
title or a cue set appears only at its last link anyway).

**`docs/IMPORT.md`** (the user's page), in plain words: the title "Importing games from a USB stick or a folder"; the
systems and their files; "PS2 games stay on the external drive and are listed from there"; N64 / GameCube not yet;
"From a folder instead of a stick"; "If an import is interrupted"; the TV per system; the log's new lines.

**Two PS1 behaviour changes under the flag, disclosed:** re-applying a plan whose titles are already whole is
`already_placed` (exit 0) where B56 said `target_exists` (exit 4) — a final with other bytes is still never
overwritten; the free-space check reads `games/` instead of `games/ps1/` (one filesystem on the hub).

## 2. Tests (`tests/import_usb/test_b58.py`, 19; fixtures built from bytes in temp dirs, removed at exit)

- **Headers:** SNES LoROM `.sfc` and HiROM `.smc` with a copier header accepted (`copier_header` false / true); a bad
  checksum and a bad size → `bad_header`; NES with / without `NES\x1a`; Genesis `.md` / `.gen` / `.bin` with `SEGA`, a
  `.bin` without → `bad_header`; a `.zip` and a `.txt` → `unknown_type`; the targets, the plugin's id, labels across
  systems; **the extensions equal the plugin's `SYSTEMS`**.
- **Duplicates per system:** the library's bytes under another name (`duplicate_of` its id), the same title in a second
  format, the same bytes twice in the source, NES by hash, **a library file of another size never hashed**, no
  `hide` for cartridges; a target with other bytes never overwritten.
- **The plain form equals the stick form** on the same files for each of the four systems (the plan without its
  source paths, form and time), with no symlink in the source; the plain form end to end through the CLI (inspect
  labels only, no BIOS line; plan; apply; verify); the forms exclusive; the library refused as a source.
- **Reported:** ps2 / n64 / gamecube / an unknown folder in the stick → the lines, the unknown name hidden, nothing
  planned, exit 3; `--system ps2|n64|gamecube` in the plain form → exit 3, "nothing planned"; nothing made under
  `games/ps2`.
- **The journal:**
  - a crash mid-copy (a `KeyboardInterrupt` with the part written) → one `.import-*` part and one entry; the title
    placed before it kept; `inspect` reports it; the same plan's next apply → `resumed`, the earlier title
    `already_placed`, both NEW, no part, no journal, verify ok;
  - a crash after disc 1 of a made-`.m3u` set → disc 1 linked, no `.m3u`; **the real plugin's `_scan` with the flag
    lists only the two whole titles**, without the flag disc 1 shows (today); the next plan accepts the set again
    (`journal_pending` 1); the next apply resumes it, listed once;
  - an apply of another plan cleans only (the set's files and its new folder gone; the placed titles kept);
  - a changed final is left, `journal_conflict`, exit 4;
  - a journal naming paths outside the library (`../`, absolute, `data/import/marks.json` with matching bytes) and a
    part not named for its cid → nothing outside touched;
  - an apply refused while playing leaves the journal as it was.
- **NEW:** a placed SNES title reads "· NEW" in the real plugin with the flag (not without); `hide` empty; a re-apply
  keeps the NEW date.
- **Absent:** four non-`1` values × five commands (both forms) → exit 9, the fixture tree's listing unchanged.
- **The log:** no fixture title, extension, folder name, path, hash, game id or cid; the systems, `resumed`,
  `unknown_system_folder` and `source_form` present.
- **Git:** the journal, the three cartridge libraries and a `PrivyHub-Import/` folder are ignored (in the tree).

## 3. For A (HOME-7 C19; IMPORT-2 later — `SESSION_B_DONE_2026-11-08U.md`)

- At HOME-7's companion restart the list's journal hiding is live with the bench drop-in (no journal exists on the
  hub, so nothing changes on the TV).
- **IMPORT-2** (a later day, unattended with the user's word): the drive's `games/snes/`, `games/nes/`,
  `games/genesis/` through `--source <folder> --system <s>` — no symlink root; duplicates expected (the per-system
  check's test); nothing written to the drive.

## 4. Files

`b58_2026-11-08/`:
- `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
- the design + `design.sha256` + `design_hashed_at.txt`;
- `b58.diff` (= `b58_code.diff` + `b58_docs.diff`), `applied_to_tree_at.txt`;
- `proof_flag_absent.md`, `absent_cli.txt`, `diff_check.txt` (both diffs reverse-apply on the tree);
- `tests_x3.txt`, `tests_in_the_tree.txt`, `tests_host_baseline.txt`, `tests_host_b58.txt`,
  `tests_host_combined.txt` (B57 + B58), `tests_mutations.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

Patch note: `patches/B58_IMPORT_SLICE_1B.md`. The user's page: `docs/IMPORT.md`.
