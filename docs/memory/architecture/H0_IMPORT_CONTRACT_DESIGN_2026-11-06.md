---
memory_schema: 1
as_of: 2026-11-06
status: DESIGN (session B, queue N, B45) — the H0 user-content import contract for this hub. No code. Nothing applied to the ROADMAP. The first implementation slice is for the next queue
---

# H0 — the user-content import contract, designed for this hub

**What this is.** ROADMAP §H0 asks for a removable-media import that inspects before copying, hashes, validates,
copies atomically, verifies, never deletes the source and logs without private names. It must feed **the existing**
games library, not a second one.

This record designs that as `tools/import_usb.py`, against what the code does today. Facts are from the code and the
hub, read-only; each carries its source. Inference is marked as such. User content is named only by placeholders
(`<title>`, `<disc>`).

## 0. What the hub does today (the facts the contract must fit)

| fact | source |
| --- | --- |
| **The library is `<repo>/games/<folder>/`**, scanned recursively. The folders are `nes`, `snes`, `genesis`, `ps1`. A file is listed if its suffix is the system's and its name does not start with `.` | `companion/plugins/games.py` `GAMES_ROOT`, `SYSTEMS`, `_scan` (`rglob("*")`) |
| **PS1 list extensions:** `.chd`, `.cue`, `.m3u`, `.iso`. `.bin` is not listed: a cue's tracks are not separate titles. A file referenced by an `.m3u` is hidden behind the playlist | `games.py` `SYSTEMS["ps1"]`, `_m3u_references` |
| **PS1 launch extensions:** `.chd`, `.cue`, `.m3u` only. **A bare `.iso` is listed but refused at launch** ("Unsupported ps1 content format") — an existing mismatch | `companion/games/config/emulators.json` `systems.ps1.extensions`; `emulator_manager.py` the launch check (~l. 498-525) |
| **A launch is confined to `games/`:** the content path must resolve inside it | `emulator_manager.py` "Game content escaped the trusted games library" |
| **A title's id is `game_<system>_` + sha1(`<system>:<relative path, casefolded>`)[:16].** It keys `data/games/library_state.json` (last played, play count), `data/games/metadata.json`, `data/games/user_content/<id>/` (cheats) and the cheat / mod profiles. **Moving or renaming a file changes its id** and orphans all of these | `games.py` `_stable_id`; the data dirs |
| **Saves and states:** `data/games/retroarch/saves/<core name>/` (PS1: `Beetle PSX HW/`, `<title>.srm` and `.mcr`) and `…/states/`, **keyed by the content's basename** (RetroArch's naming). Profiles: `data/games/retroarch/cheat_profiles/<id>/<profile>/saves | states` | `data/games/retroarch/`; `emulator_manager.py` ~l. 4397 |
| **The PS1 core** is `mednafen_psx_hw_libretro.so` (Beetle PSX HW). **The BIOS directory `data/games/retroarch/system/` is empty.** RetroArch's check logs "Firmware is missing: scph5501.bin" at every PS1 start. **Inference** (the core's strings embed OpenBIOS): PS1 titles run today on the core's built-in OpenBIOS | `retroarch.cfg` `system_directory`; a PS1 game log; the core binary's strings |
| **Player count:** `data/games/metadata.json` per id (`max_players` from the libretro database's `maxusers`, `player_mode_suggested`), written by `games/metadata_importer.py` `run_metadata_update`. Keyed by crc / sha1 / md5 / serial | `metadata_importer.py` ~l. 360-725, 1244-1401 |
| **How titles reach the onn:** the plugin's `games` action returns the scanned list (5-s cache), with artwork / metadata merged. The onn's games screen shows it. There is no "new" mark; `library_state.json` holds only `last_played_unix_ms` and `play_count` | `games.py` `action == "games"`; `library_state.json` keys |
| **Git:** `/games/`, `data/`, `media/`, `runtime/`, `logs/` are ignored. A ROM / disc image / BIOS under them cannot be committed by `git add` of a path list | `.gitignore` (`git check-ignore` on a fake path under each: all ignored) |
| **USB on this hub:** `udisks2` is active, the user's `gvfs-udisks2-volume-monitor` is active, `udisksctl` and `gio` are installed, and `/media/<user>/` exists. A removable stick should mount there without sudo. **Not checked:** whether it auto-mounts with no graphical seat; HOME-3 can confirm with one stick | `systemctl`; `ls` (names elided) |

## 1. The USB layout

```text
PrivyHub-Import/                  # the only folder the tool reads; anything else on the stick is ignored
    games/
        ps1/                      # = <repo>/games/ps1/ (today)
            <title>.chd                       # one file = one candidate
            <title>/                          # one folder = one candidate (a cue + its tracks, or a multi-disc set)
                <title>.cue
                <title> (Track 1).bin
                <title> (Track 2).bin
            <title> (multi-disc)/
                <title>.m3u                   # required for a multi-disc set (§4)
                <title> (Disc 1).chd
                <title> (Disc 2).chd
        snes/  nes/  genesis/     # = today's folders; same rules, simpler validation (§3.4)
        n64/  gamecube/  ps2/     # H1-H3: reserved names; refused until the plugin lists the system (§1.1)
    bios/
        ps1/                      # → data/games/retroarch/system/ (§3.5; off in the first slice)
        ps2/                      # H3: waits for the core
    saves/                        # reported, never imported in H0 (§5)
    artwork/  metadata/           # reported, not imported in the first slice
```

**Why `games/<system>/` and not the roadmap example's `roms/` + `isos/`.**
- It mirrors the library exactly (`games/<folder>`). The mapping is then one rule, not a table.
- It avoids the ambiguity of a PS1 CHD, which is a disc image but not an `.iso`.

### 1.1 H1-H3: what is known now, and what waits for the core

| system | folder (known) | content (likely; **waits for the core choice**) | firmware |
| --- | --- | --- | --- |
| N64 (H1) | `games/n64/` | `.z64` `.n64` `.v64` (byte order is checkable from the first 4 bytes) | none needed |
| GameCube (H2) | `games/gamecube/` | `.iso` `.gcm` `.rvz` `.gcz` `.ciso` (the Dolphin family; the `DVD magic` at 0x1C is checkable) | IPL optional; the location waits for the core |
| PS2 (H3) | `games/ps2/` | `.iso` `.chd` `.cso` | **BIOS required**; the core's sub-folder of `system/` waits for the core |

**Until a system is in the plugin's `SYSTEMS` and in `emulators.json`, its folder is reported as "not yet supported" and
nothing is copied.** The import never creates a second path, and never adds a system by itself.

## 2. The ROADMAP §H0 list, item by item

| §H0 requirement | the design |
| --- | --- |
| ordinary USB mass storage | any mounted filesystem; `--source` a mounted path or auto (§3.1); read-only use (never written) |
| inspect before copying | `inspect` → `dry-run` is the default command; `copy` needs a manifest from a dry run (§3) |
| a dry-run / manifest | JSON manifest (§3.3) + a plain summary on the terminal |
| hash files | sha256 of every candidate file, streamed (1 MiB blocks); the manifest records it |
| detect duplicates | against the library by content hash (§3.6) and inside the stick |
| validate extensions / types | the system's launch extensions (`emulators.json`), not the list's: a PS1 `.iso` is refused (§0) |
| stronger format / signature validation | CHD magic and version; cue sheet parsed and every `FILE` resolved; the PS1 data track's ISO9660 descriptor and system id; NES `NES\x1a`; SNES / Genesis header checks (§3.4) |
| map into the existing user-data layout | `games/<system>/<candidate>` only; saves / states / ids untouched (§5) |
| copy atomically | dot-prefixed temp files on the target filesystem, fsync, verify, then a no-replace link into the final name; the playable entry (`.cue` / `.chd` / `.m3u`) placed **last** (§3.7) |
| verify copied bytes | sha256 of each placed file against the manifest; on a mismatch every file of that candidate is rolled back (§3.7) |
| safely repeatable / idempotent | a re-run finds the same hashes in the library → "already imported", nothing copied, exit 0 |
| never delete source files | the source is opened read-only; the tool has no code path that writes or unlinks under `--source` (a test enforces it, §7) |
| preserve user saves / states separately | `data/games/retroarch/saves|states` and the profile trees are never opened for write; a USB `saves/` is reported only |
| reject ambiguous / unknown files | §4: every rejection has a code; nothing is guessed |
| ROM / ISO / BIOS out of Git and bundles | §6 |
| sanitized logs | §6: hashed ids, sizes, codes; no names |
| integrate with existing infrastructure | the scanner picks the files up unchanged (§8); no new library path, no new list endpoint |

## 3. `tools/import_usb.py` — the pipeline

### 3.1 CLI

```text
python3 tools/import_usb.py inspect  [--source <dir>]               # what is there; no hashing
python3 tools/import_usb.py dry-run  [--source <dir>] [--system ps1] # hash + validate + duplicates → a manifest
python3 tools/import_usb.py copy     --manifest <file> [--yes]       # re-checks, then copies exactly what the manifest accepted
python3 tools/import_usb.py verify   --manifest <file>               # re-hashes what a copy placed (read-only)
```

- **`--source`** defaults to the first `PrivyHub-Import/` found at depth 1 under `/media/<user>/*` or
  `/run/media/<user>/*`. More than one found → exit 2 with "several sticks; pass --source". The tool **never mounts**:
  if nothing is mounted it says to insert the stick, or to run `udisksctl mount -b <device>` (no sudo, polkit
  permitting).
- **`copy` takes only a manifest.** It re-hashes each accepted source file and refuses any whose size or hash changed
  since the dry run (exit 4 for that candidate). What is copied is exactly what was shown.
- **The library root** is `<repo>/games/` (`GAMES_ROOT`), resolved from the tool's own location. There is no
  `--target`: the import cannot be pointed elsewhere.
- **Refuses while a game is active.** The local `/plugins/games/status` on loopback reads `active` → exit 8, unless
  `--while-playing`. Copies run under `ionice -c3` / `nice 19`, so a copy never competes with a stream.
- **No network** beyond that loopback status read: no metadata fetch, no artwork fetch. The existing metadata update
  is the user's separate action.

### 3.2 Exit codes

| code | meaning |
| --- | --- |
| 0 | done: a dry run written, or everything accepted copied and verified (including "nothing new") |
| 2 | usage / source not found / several sources |
| 3 | nothing importable: every candidate rejected |
| 4 | partial: some candidates copied, some rejected or changed since the dry run |
| 5 | a verify failure: that candidate rolled back (others may be placed; the manifest says which) |
| 6 | the source is unreadable mid-run (stick pulled): the in-flight candidate rolled back, the placed ones kept |
| 7 | not enough space on the library filesystem (the sum of accepted sizes + 10 %); nothing copied |
| 8 | a game is active (without `--while-playing`) |

### 3.3 The manifest (`data/games/import/manifests/<UTC>.json`; under `data/`, so never in Git)

```json
{
  "schema": "privyhub.import.manifest/1",
  "created_utc": "2026-11-07T12:00:00Z",
  "source_id": "src_<sha256(volume uuid or label + root)[:12]>",
  "library_root": "games",
  "candidates": [
    {
      "cid": "c_<sha256(relative source path)[:12]>",
      "system": "ps1",
      "kind": "chd | cue_set | m3u_set | rom",
      "source_rel": "games/ps1/<title>.chd",
      "target_rel": "games/ps1/<title>.chd",
      "files": [
        {"source_rel": "…", "target_rel": "…", "bytes": 0, "sha256": "…", "role": "entry | track | disc | playlist"}
      ],
      "content_sha256": "<sha256 over the sorted file hashes>",
      "game_id": "game_ps1_<the scanner's _stable_id(system, target_rel)>",
      "checks": {"extension": "ok", "header": "ok | n/a", "cue_refs": "ok | n/a", "system_id": "PLAYSTATION | n/a"},
      "decision": "accept | duplicate | reject",
      "reason": "<code, §4>",
      "duplicate_of": "game_ps1_… | null"
    }
  ],
  "reported_not_imported": {"saves": 0, "artwork": 0, "metadata": 0, "bios": 0, "unsupported_system": 0},
  "totals": {"accept": 0, "duplicate": 0, "reject": 0, "bytes_to_copy": 0}
}
```

- **Names appear in the manifest:** it is the user's own local data under `data/` (ignored), and the user needs it to
  read the dry run. **They never appear in the log** (§6).
- **`game_id` is precomputed** with the scanner's exact rule, so the record can join `library_state` / `metadata`
  afterwards.

### 3.4 Validation, per system

- **PS1 `.chd`:**
  - the first 8 bytes are `MComprHD`;
  - the header version (big-endian u32 at 12) is 5 (4 accepted, others refused);
  - the logical size in the header ≥ one CD sector.
  - **Not decoded:** CHD hunks are compressed, so the ISO9660 check does not apply.
- **PS1 `.cue` set:**
  - the cue sheet is parsed (`FILE "<x>" BINARY`, `TRACK nn MODE2/2352 | MODE1/2352 | AUDIO`);
  - **every `FILE` must resolve to a file in the same candidate folder:** no `..`, no absolute path, case-exact on
    Linux, case-insensitive match offered as a reject reason with the fix;
  - each track file's size is a multiple of 2352;
  - **track 1 must be data;** its sector 16 (byte 16 × 2352 + 24 for MODE2, + 16 for MODE1) holds `\x01CD001`, and the
    system identifier at +8 reads `PLAYSTATION`;
  - a data track with no `CD001`, or another system id, is refused (`not_ps1_disc`).
- **PS1 `.m3u` set:** every line resolves to a `.chd` or `.cue` in the same folder, each one validated as above. The
  playlist is the candidate's entry.
- **NES `.nes`:** `NES\x1a` at 0. **SNES `.sfc` / `.smc`:** size sane (a 512-byte copier header detected), the internal
  header checksum + complement = 0xFFFF at LoROM or HiROM. **Genesis `.md` / `.gen` / `.bin`:** `SEGA` at 0x100. A
  Genesis `.bin` without `SEGA` is refused: it is the most ambiguous suffix.
- **Every file:**
  - a regular file;
  - **not a symlink** (a symlink anywhere in the candidate is refused: it can point outside the stick);
  - a name of ≤ 200 bytes with no control characters and no leading `.`;
  - readable to the end.

### 3.5 BIOS (`bios/ps1/` → `data/games/retroarch/system/`) — designed, **off in the first slice**

- **What is accepted:** only the core's expected names, `scph5500.bin` / `scph5501.bin` / `scph5502.bin`
  (case-normalized to lower), each 524,288 bytes, whose sha1 matches RetroArch's firmware list for the core (the check
  the game log prints). An unknown hash is refused (`bios_unknown_hash`).
- **Never overwrites** an existing BIOS file.
- **A user decision first:** importing a real BIOS changes every PS1 title's firmware from the embedded OpenBIOS
  (inference, §0). Compatibility is generally better, but **a save state made under one BIOS may not load under the
  other.** The B9 / B33 scratch states are per session, but the user's own slot states are not. So the BIOS import is
  its own subcommand and its own queue item, with the state question answered first.

### 3.6 Duplicates

- **Against the library.** A hash index `data/games/import/library_index.json` maps
  `{relative path → (size, mtime_ns, sha256)}`. It is built lazily and re-hashes only changed files; the first build
  over today's PS1 library is a one-time read of the existing files. A candidate whose `content_sha256` matches an
  existing title's → `duplicate`, with `duplicate_of` set to that title's id. Never copied.
- **Inside the stick:** two candidates with the same content → the first by path accepted, the rest `duplicate`.
- **Name collision with different content:** the target path exists with other bytes → `reject:
  target_exists_different`. **Never renamed automatically.** A rename would change the id and the save basename, so
  the user renames on the stick.
- **The same content under a new name:** a `duplicate`, not a second copy. Two copies would split saves and play
  counts.

### 3.7 The copy, atomic and verified

For each accepted candidate, in manifest order:
1. **Space:** `statvfs` of the `games/` filesystem ≥ the bytes + 10 %, checked once for the whole run (exit 7).
2. **Temp files:** each file is copied to `games/<system>/<target dir>/.import-<cid>-<n>.part`. The leading `.` keeps
   the scanner from listing it: it skips names starting with `.`, and the dir is the target's own, so it sits on the
   same filesystem. The copy is streamed and hashed while copying, then `fsync`, then the dir is fsynced.
3. **Verify:** the copied hash must equal the manifest's. If it does not, the candidate is rolled back.
4. **Place:** for each file, `os.link(part, final)`, which **fails if `final` exists: the no-overwrite guarantee**,
   then remove the tool's own `.part`. The track / disc files go first, **the entry (`.cue` / `.chd` / `.m3u`) last.**
   So the scanner sees the title only when every file it needs is in place.
5. **Rollback** (verify failure, a link failure, source read error, Ctrl-C):
   - the tool removes **only** files it created in this run (its own `.part` files and the finals it linked, both
     recorded as it goes);
   - an empty target dir it created is removed;
   - nothing else is ever unlinked.
   - These are the only deletions the tool can make. They are confined to `games/<system>/` paths recorded in this
     run's journal, and a test enforces it.
6. **Journal:** `data/games/import/journal/<UTC>.jsonl`, one line per step. A crash mid-run leaves a journal that the
   next `copy` reads first, to finish or roll back that candidate (idempotent).

## 4. Rejections (codes; the manifest's `reason`)

| code | what | the fix the dry run prints |
| --- | --- | --- |
| `unsupported_system` | a folder under `games/` the plugin does not list (today: anything but nes / snes / genesis / ps1) | wait for H1-H3 |
| `bad_extension` | not the system's launch extension (**a PS1 `.iso`; a lone `.bin`**) | a cue sheet, or a CHD conversion (outside the tool) |
| `bad_header` / `not_ps1_disc` | the signature check fails | — |
| `cue_missing_file` / `cue_case_mismatch` / `cue_outside` | a `FILE` line does not resolve inside the candidate | fix the cue or the names |
| `multidisc_no_m3u` | **a folder with more than one entry file (`.cue` / `.chd`) and no `.m3u`** — decided: refused, not guessed | add `<title>.m3u` listing the discs in order |
| `ambiguous_entries` | a folder with entry files of different titles, or a `.m3u` plus extra unlisted entries | one title per folder |
| `symlink` / `bad_name` / `unreadable` | §3.4 | — |
| `target_exists_different` | §3.6 | rename on the stick |
| `duplicate` (not an error) | §3.6 | — |
| `bios_*` | §3.5 (later slice) | — |

**Files that are not candidates** (a `.txt`, `.jpg` or `.sav` next to a game) are listed in the manifest's
`ignored` count by suffix only. They are never copied.

## 5. The user-data layout it maps into

- **Written:** `games/<system>/…` (the new titles only), `data/games/import/` (manifests, the journal, the hash index)
  and `logs/import/` (the sanitized log).
- **Never written:**
  - `data/games/retroarch/saves/`, `states/`, `system/` (until §3.5's slice), the cheat / mod profile trees;
  - `data/games/library_state.json`, `metadata.json`, `user_content/`;
  - any existing file under `games/`.
- **An existing title is never moved or renamed** (its id and save basename depend on its path, §0).
- **Saves on the stick** (`saves/`) are counted and reported, never imported, in H0. A save import needs a mapping to
  the core's names and a conflict rule, and is its own design.

## 6. Privacy

- **Git:** the library, `data/` and `logs/` are already ignored (§0). The tool adds nothing tracked.
  - **Add to `.gitignore`:** `PrivyHub-Import/`, in case a stick's folder is ever copied into the repo by hand.
  - **Add as a check:** a `tools/` test that `git check-ignore` covers `games/ps1/x.chd`,
    `data/games/retroarch/system/x.bin` and `data/games/import/x.json`.
- **Bundles:** the support / diagnostic bundles (B30 / B36 keepers, the patch ZIPs) take from `logs/` and evidence.
  `logs/import/` holds no names. `data/games/import/` and `games/` are never in a bundle; B36's keeper list does not
  name them, and must not.
- **The log** (`logs/import/import_<UTC>.jsonl`): per candidate `cid`, `system`, `kind`, file count, bytes,
  `content_sha256[:12]`, decision, reason, timings, and the resulting `game_id`.
  - It never carries a filename, a title, a folder name, a volume label or UUID (`source_id` is a hash), or a mount
    path.
  - The redactor from B30 runs over it before any copy leaves the hub.
- **The terminal** shows names to the user at the hub (their own content). Nothing on the terminal is persisted except
  through the manifest (local, ignored).
- **No ROM, ISO or BIOS byte** is ever read into a log, a row or a test fixture. Tests synthesize headers from bytes
  (§7).

## 7. The first implementation slice (next queue): PS1 only, dry run and manifest, then the copy

**Slice 1a — `inspect` + `dry-run` for `games/ps1/` (read-only on the stick and on the library):**
- source discovery (§3.1), candidates (chd / cue_set / m3u_set), §3.4's PS1 checks, sha256;
- the library hash index over `games/ps1/` (§3.6), the manifest (§3.3), the sanitized log (§6), the exit codes;
- `.gitignore` + the ignore test.

**Tests (fixtures built in /tmp from bytes, never real content):**
- a fake CHD v5 header (+ v3 refused);
- a cue + two `.bin` with a synthetic `CD001` / `PLAYSTATION` sector 16 (MODE2/2352);
- a cue whose `FILE` is missing / in another case / `../`;
- a data track with `CD001` but another system id;
- a bare `.iso` and a lone `.bin` → `bad_extension`;
- two `.chd` in one folder with no `.m3u` → `multidisc_no_m3u`; the same with an `.m3u` → one `m3u_set`;
- a symlink to outside;
- a candidate byte-equal to a library title → `duplicate` with the right `game_id`;
- a target name that exists with other bytes → `target_exists_different`;
- the manifest's schema;
- **`game_id` equals `GamesPlugin._stable_id` for the target path;**
- **no filename or title string in the log** (the test greps for every fixture name);
- the stick mounted read-only (chmod) and the run still succeeds: the tool writes nothing there.

**Slice 1b — `copy` + `verify` for PS1 (after 1a's bench read):**
- §3.7 complete: the re-check against the manifest, space, `.part`, link-no-replace, the entry last, the rollback, the
  journal and its resume.

**Tests:**
- the copy then a re-run → all `duplicate`, exit 0 (idempotent);
- the scanner (the real `_scan` on a temp root) lists the title only after the entry is linked; mid-copy it lists
  nothing;
- a verify failure (a hook that flips one byte in a `.part`) → rolled back, nothing left, exit 5;
- a pre-existing final → no overwrite, exit 4;
- a source file changed since the dry run → refused;
- a killed run → the next run's journal finishes or rolls back;
- the deletion audit: every unlink the tool makes is under `games/ps1/` and in its own journal (a wrapper records
  them);
- active game → exit 8.

**Bench for A (after 1b):** a stick with one PS1 title (a CHD) and one deliberate duplicate. `dry-run`, read the
summary, `copy`, then the title on the onn's list within ~5 s, launch it, and a second `copy` reports "already
imported".

## 8. On the onn

- **How an imported title appears:** exactly as today's titles. The scanner lists it within its 5-s cache, sorted by
  system then title, with `_clean_name`'s title (from the entry file's basename). The `games` action and the onn's list
  are unchanged.
- **Artwork and player count** come from the existing metadata update when the user runs it (the import does not
  fetch). Until then the title shows without art, and B41's prompt uses the default player count.
- **A "new" mark (proposed, a later slice, the user's choice):**
  - the import writes `data/games/import/imported.json` (`game_id → imported_unix_ms`);
  - the `games` payload gains `new: true` for a title imported in the last 7 days with no `play_count`;
  - the onn shows a small "NEW" tag. Client work, so behind a property first.
- **No import UI on the onn in H0:** the stick goes into the hub, and the user (or A) runs the tool at the hub. An
  onn-side "Import from USB" button would need the hub to accept a command over the API. That is a remote-trust change,
  out of H0.

## 9. Open questions for the user

1. **The PS1 BIOS:** keep today's built-in OpenBIOS (inferred), or import a real BIOS from your own console's dump
   (better compatibility; old save states may not load)? This decides when §3.5 is built.
2. **Multi-disc without a playlist:** refused with the fix printed (decided here). Or should the dry run offer to
   write the `.m3u` for you, on the hub, never on the stick?
3. **A "NEW" tag** on the onn for a week after an import: wanted?
4. **The existing `.iso` mismatch** (listed, refused at launch): should the list stop showing PS1 `.iso` files? A
   one-line change outside H0, for a queue.
