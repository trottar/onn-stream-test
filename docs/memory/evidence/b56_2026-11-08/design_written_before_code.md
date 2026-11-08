# B56 — H0 import slice 1a, PS1 only: `tools/import_usb.py` inspect / plan / apply / verify, behind `PRIVYHUB_IMPORT=1` (design, hashed before code)

Queue: `handoffs/QUEUE_2026-11-08T.md` §B56; B45's contract `architecture/H0_IMPORT_CONTRACT_DESIGN_2026-11-06.md`; the
user's four answers to B45 §9 (2026-11-08): **a real BIOS when present, OpenBIOS only as a labelled fallback;
multi-disc titles as one entry with an auto-made `.m3u`; a "NEW" tag for 7 days; an `.iso` hidden when a `.chd` of the
same title exists.** Baseline `0eb115d9`; built in `/tmp/b_q12t_b56`. **`PRIVYHUB_IMPORT` absent (anything but `1`) =
the tool refuses and writes nothing; the companion's list is today's byte for byte.** Built and tested against
fixture trees only: no real USB, no real game file read, nothing imported.

## 0. Settled (the code and the hub read in place, names never printed)

- **The PS1 library is `<repo>/games/ps1/`** (the plugin's `GAMES_ROOT` / `SYSTEMS["ps1"]`), on the hub's own disk
  (`/`, ext4; not the drive). Today it holds cue sets only (counts: 80 `.cue`, 338 `.bin`, 0 `.chd` / `.iso` / `.m3u`
  / `.pbp`). The list takes `.chd .cue .m3u .iso`; the launch `.chd .cue .m3u` (an `.iso` is listed but refused, B45
  §0); a file named in an `.m3u` is hidden behind it. Ids: `game_ps1_` + sha1(`ps1:<relative path, casefolded>`)[:16].
- **The BIOS folder the PS1 core reads** is RetroArch's `system_directory`, `data/games/retroarch/system/`. **It is
  empty today**; Beetle PSX HW then runs on its built-in OpenBIOS (B45's inference from the core's strings and the
  "Firmware is missing" log line). The core's real-BIOS names: `scph5500.bin` (JP), `scph5501.bin` (US),
  `scph5502.bin` (EU), each **524,288 bytes**.
- **The metadata the list reads.** The onn shows each node's host-given `name` (the client's `SourceNode.name`): a
  game node's name is its title, a system node's "PlayStation (N)". So the host can show "NEW" and "(OpenBIOS)" with
  **no client change**. `data/games/metadata.json` is not the place: `metadata_importer.run_metadata_update` rebuilds
  each entry from scratch (unknown keys dropped). The marks therefore live in **`data/import/marks.json`**, which the
  list reads beside `metadata.json` — behind `PRIVYHUB_IMPORT=1` in the companion too (a bench drop-in for IMPORT-1).
- **No client change is needed**, so none is listed for the next APK.

## 1. The USB layout (B45 §1, PS1 only in this slice)

```text
PrivyHub-Import/
    games/ps1/      <title>.chd | <title>.cue + its .bin tracks | <title> (Disc N).chd|.cue … | <title>.m3u | (.iso, .pbp)
    bios/ps1/       scph5500.bin / scph5501.bin / scph5502.bin
    (anything else: reported, never read further)
```
`<mount>` may be the stick's mount point (holding `PrivyHub-Import/`) or the `PrivyHub-Import/` folder itself.

## 2. The commands (`python3 tools/import_usb.py <command> …`; every command refuses without `PRIVYHUB_IMPORT=1`)

- **`inspect <mount>`** (no hashing, writes nothing): the files under `games/ps1/` by type; the candidates —
  `chd`, `cue_set` (a cue + the files it names), `m3u_set` (a stick `.m3u`, or discs grouped by `(Disc N)` with the
  `.m3u` to be made); **the rejections with a reason code**: `unknown_type`, `bin_without_cue`, `iso_not_launchable`,
  `pbp_not_supported`, `cue_missing_file`, `cue_case_mismatch`, `cue_outside`, `bin_claimed_twice`,
  `multidisc_gap`, `symlink`, `bad_name`; the BIOS report: which of the three are on the stick by name + size (JP / US /
  EU labels), others named `bios_unknown` by count; and whether the core's folder already holds one.
- **`plan <mount>`** (reads the stick and the library; writes only the plan): everything `inspect` does, plus:
  - **the headers** (`bad_header`): `.chd` = `MComprHD` and version 5 (4 accepted); a cue's first track must be data,
    and sector 16 (MODE2/2352: +24; MODE1/2352: +16) holds `\x01CD001` with the system id `PLAYSTATION`
    (`not_ps1_disc` otherwise); track files a multiple of 2,352 bytes;
  - **the hashes:** sha256 of every candidate file (1-MiB blocks);
  - **duplicates against the library:**
    - by hash, size-gated (only library files of a candidate file's exact size are hashed; the library is never read
      wholesale) → `duplicate` with `duplicate_of` (the library title's id);
    - by title (the plugin's `_clean_name` of the entry, disc tags dropped, casefolded):
      - an `.iso` whose title has a `.chd` (library or stick) → skipped, `"duplicate: chd present"`;
      - any other candidate whose title is already listed → skipped, `"duplicate: title present"` (two entries for one
        title would split saves and play counts; the user removes the old one first if they want the new one —
        disclosed);
    - inside the stick: the same content twice → the second is `duplicate`;
    - the target path exists with other bytes → `target_exists_different` (never renamed);
  - **"hide":** every library `.iso` whose title has a `.chd` in the library or in this plan → listed in the plan's
    `hide` (by game id), for the marks;
  - **the destination:** under `games/ps1/`, the same relative path as on the stick; a disc group's `.m3u` is
    `<title>.m3u` beside its discs, listing them in disc order;
  - **NEW:** each accepted title's game id (the plugin's exact rule over its target path), marked at apply;
  - **space:** `statvfs` of `games/ps1/`'s filesystem ≥ the bytes to copy + 10 % (`no_space` → exit 7);
  - the plan written to **`data/import/plans/<UTC>.json`** (names inside: the user's own local data under `data/`,
    git-ignored) and a **summary in labels only** on the terminal (`T1 chd 1 file 512 MB accept`, …); `--names` adds
    the names for the user at the hub.
- **`apply <plan>`** (refuses while a game is active — the loopback `/plugins/games/status`; `--while-playing`
  overrides): `os.nice(10)`; every accepted source re-hashed against the plan (changed → `source_changed`, not
  copied); the space checked again; per candidate, files in plan order, **the entry last**:
  1. copy to `<target dir>/.import-<cid>-<n>.part` (a dot name: the scanner skips it), hashing while copying,
     `fsync`, the directory `fsync`ed;
  2. the copy's hash must equal the plan's;
  3. `os.link(part, final)` — fails if the final exists (no overwrite) — then the tool's own `.part` removed;
  4. a disc group's `.m3u` written the same way (temp, verify, link), after its discs;
  5. **any failure → that candidate rolled back:** only the files this run created for it (its `.part`s and the
     finals it linked) and a directory it created and left empty are removed; nothing else is ever unlinked;
  - then **the marks** (`data/import/marks.json`, written to a temp name and renamed): `new[game_id] =
    imported_unix_ms` for each placed title, `hide[game_id] = "chd present"` for the plan's hide list;
  - **the BIOS:** each real file on the stick (by name and size) copied the same atomic way into
    `data/games/retroarch/system/`, never over an existing file; the label "(OpenBIOS)" then goes;
  - **the sanitized log** `data/import/logs/<UTC>.jsonl`: per candidate its label (`T1`…), kind, file count, bytes,
    decision and reason code; the BIOS as region labels and counts; the totals; **no filename, title, folder, hash,
    mount path or volume name**;
  - the applied record `data/import/applied/<plan name>` (what was placed, for `verify`).
- **`verify <plan>`** (read-only): every placed file re-hashed against the plan → `ok` / `mismatch` per label.
- **Exit codes** (B45 §3.2): 0 done; 2 usage / source not found; 3 nothing importable; 4 partial; 5 a verify failure
  (rolled back); 6 the source unreadable mid-run; 7 no space; 8 a game active; **9 `PRIVYHUB_IMPORT=1` not set
  (nothing read or written)**.

## 3. The companion (behind `PRIVYHUB_IMPORT=1`; absent = nothing imported, the list byte for byte)

`companion/import_marks.py` (new), used by `plugins/games.py` only when the flag is `1`:
- `_scan`: a game whose id is in `hide` is left out;
- the game nodes: a title in `new` within **7 days** of its import gets **" · NEW"** after its name;
- the PlayStation system node: **"PlayStation (OpenBIOS) (N)"** while none of the three real files is in the BIOS
  folder; "PlayStation (N)" once one is.

## 4. BIOS and save states (said to the user in `docs/IMPORT.md`)

A real BIOS changes the firmware every PS1 title boots with. **A save state made under OpenBIOS may not load under the
real BIOS** (B45 §3.5); the in-game memory-card saves are not affected. The plan and `apply` print that line when a
BIOS is to be copied.

## 5. Tests (`tests/import_usb/`, fixture trees built from bytes in a temp dir, removed at exit)

inspect / plan / apply / verify end to end on a fixture stick (a CHD v5 header, a cue + two bins with a synthetic
`CD001` / `PLAYSTATION` sector, a two-disc set); every rejection code; the multi-disc `.m3u` written and the scanner
(the real plugin `_scan` on the temp root) listing one entry; the duplicate rules (hash, size-gated; `.iso` +
`.chd` → "duplicate: chd present"; the library's `.iso` beside a `.chd` → hide; the title rule; inside the stick;
`target_exists_different`); **a copy failing midway leaves nothing half-written** (a hook raises during the second
file; no `.part`, no final, no new dir); a pre-existing final never overwritten; a source changed after the plan →
`source_changed`; the sanitized log greps clean of every fixture name and hash; the game ids equal the plugin's
`_stable_id`; the marks → " · NEW" within 7 days and not after, the hidden `.iso` gone from the list, "(OpenBIOS)"
until a BIOS file is present; the BIOS copy (never over an existing file); the stick never written (made read-only);
**absent → the tool refuses with exit 9 and writes nothing, and the plugin's list is today's** (flag unset).
