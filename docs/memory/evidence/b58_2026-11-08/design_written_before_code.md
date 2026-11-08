# B58 — design, written before any B58 code (import slice 1b: the plain source folder, SNES / NES / Genesis, the journal)

Queue: `handoffs/QUEUE_2026-11-08U.md` §B58. Baseline `d618a20a`. Built in `/tmp/b_q13u_b58` (companion/, tools/,
tests/, PrivyHub/ only), on B56's `tools/import_usb.py`; the tree gets the diff at the end, uncommitted. Behind
`PRIVYHUB_IMPORT=1`. Fixture trees only: no real game file read, nothing imported, nothing written to the drive.

## 0. Settled

**The systems the hub lists today** (`companion/plugins/games.py` `SYSTEMS`; the library is `<repo>/games/<folder>/`,
scanned recursively; a file is listed when its suffix is the system's and its name does not start with `.`):

| system | folder | listed extensions | the core (`emulators.json`) | today's library (counts by name only) |
| --- | --- | --- | --- | --- |
| NES | `games/nes/` | `.nes` | fceumm | empty |
| SNES | `games/snes/` | `.sfc` `.smc` | bsnes | 44 `.sfc` |
| Genesis | `games/genesis/` | `.md` `.gen` `.bin` | blastem | empty |
| PlayStation | `games/ps1/` | `.chd` `.cue` `.m3u` `.iso` (B56) | mednafen psx hw | 80 `.cue`, 338 `.bin`, 1 other |
| PlayStation 2 | none: listed in place from the drive (B49, `PRIVYHUB_PS2=1`) | — | PCSX2 | — |

**The header checks (B45 §3.4, practical ones):**
- **NES `.nes`:** `NES\x1a` at 0 (iNES and NES 2.0 both), else `bad_header`.
- **SNES `.sfc` / `.smc`:** the size less a 512-byte copier header (present when `size % 1024 == 512`) is a whole
  number of KiB and ≥ 32 KiB, else `bad_header`; and the internal header's checksum + complement = 0xFFFF at LoROM
  (0x7FDC), HiROM (0xFFDC) or ExHiROM (0x40FFDC), counted after the copier header, else `bad_header`. The plan records
  `copier_header` true / false.
- **Genesis `.md` / `.gen` / `.bin`:** `SEGA` within 0x100-0x10F (`SEGA MEGA DRIVE`, `SEGA GENESIS`, ` SEGA …`), else
  `bad_header` — a `.bin` without it is refused (the most ambiguous suffix; an interleaved `.smd`-style dump too).
- Anything else in a cartridge folder (an archive, a `.txt`, a save) → `unknown_type` (rejected files, by reason).

**N64 / GameCube:** B45 reserves `games/n64/`, `games/gamecube/`; no core yet → `inspect` lists each such folder as
"not supported yet" with its file count; `plan` plans nothing for it (a row `unsupported_system`). Nothing planned,
now or later in this slice.

**PS2: not imported.** PS2 titles live on the external drive by design (B49 lists them in place). A `games/ps2/`
folder → `inspect` says "PS2 games stay on the external drive and are listed from there — not imported"; `plan`
plans nothing.

**The duplicate check per system** (B56's, per system's library folder):
1. by hash against the system's library, **size-gated** (only library files whose size equals a candidate file's are
   hashed);
2. inside the source (the same content twice: the first by path kept);
3. by title (the plugin's `_clean_name`, case-folded; PS1 also drops the disc number): two entries for one title
   would split saves and play counts → "duplicate: title present";
4. a target with other bytes → `target_exists_different` (never renamed, never overwritten).
- A headered and a headerless dump of one SNES title differ by hash; the title rule catches the same name. Not
  stripped for the hash (disclosed).

**The NEW tag and the hidden-duplicate rule per system:**
- **NEW: every system.** `marks.json` `new` is keyed by game id; the list's tag (B56, `plugins/games.py`) is by id and
  system-blind. A placed SNES / NES / Genesis title gets " · NEW" for 7 days, as PS1.
- **Hidden duplicates: PS1 only.** B56's rule (a library `.iso` hidden when a `.chd` of the title exists) is the only
  "lesser format of one title" pair. A cartridge title arriving in a second format (an `.smc` beside an `.sfc` of the
  same title) is "duplicate: title present" and is not placed, so nothing needs hiding.

**The journal (B45 §3.7.6; B56 had in-process rollback only).** Today a crash or power loss mid-apply leaves its
`.import-*.part` (B56 never removes a part it did not make in this run) and any finals linked before it; a multi-disc
set whose made `.m3u` had not landed shows its placed discs as separate entries.
- **`data/import/journal.json`** (git-ignored under `data/`), written atomically (temp + `fsync` + rename) **before a
  candidate's first file**: `{cid: {system, label, plan, started_utc, targets: [rel], parts: [rel], preexisting:
  [rel], dirs_new: [rel], sha256: {rel: hash}, list_ids: [game ids the list would show]}}`; the entry is removed after
  the candidate's last file is placed, or after its in-process rollback.
- **The next `apply` reads it first** (after the active-game check, before anything else): for each entry it removes
  that candidate's own parts (exact names `.import-<cid>-…`), the finals it linked (only targets not pre-existing and
  only when their bytes equal the journal's hash; any other file is left and reported `journal_conflict`), and the
  directories it made if empty; then the entry. If this apply's plan accepts the same candidate, it is copied again
  from the start → **resumed**; otherwise it is **cleaned**. Nothing outside the journal's paths is touched.
- **`plan` / `inspect`** report an interrupted import ("the next apply cleans it up first"); `plan` treats the
  journal's non-pre-existing targets as absent (not a library duplicate, not a target clash), so the interrupted title
  is accepted again.
- **Never a half-placed title in the list:** the list (behind the same flag, `companion/import_marks.py`) leaves out
  the journal's `list_ids` — a title being copied, or one interrupted, is not listed until it is whole. Without the
  companion's flag the list does not read the journal: an interrupted multi-disc set could show its placed discs until
  the next apply cleans them (disclosed; single-file titles and cue sets appear only at their last link anyway).

## 1. The design, behind `PRIVYHUB_IMPORT=1`

`tools/import_usb.py`:
1. **Two source forms**, the same inspect / plan / apply / verify:
   - **the stick form (as now):** `inspect|plan <mount>` — a mount holding `PrivyHub-Import/` (or that folder itself);
     every system folder under its `games/` is read: `ps1`, `snes`, `nes`, `genesis` planned; `n64`, `gamecube`
     reported "not supported yet"; `ps2` reported "stays on the external drive"; another name reported
     `unknown_system_folder`. PS1's BIOS from `bios/ps1/` as B56.
   - **the plain-folder form (new):** `inspect|plan --source <folder> --system <ps1|snes|nes|genesis>` — the folder is
     that system's games folder itself (e.g. the drive's `games/snes/`), read in place: **no symlink root**. `--system
     ps2|n64|gamecube` is accepted only to report it (nothing planned, exit 3). A source inside the hub's own
     `games/` is refused (exit 2). The plain form reads no BIOS (B56's BIOS stays the stick form's `bios/ps1/`; the
     drive has none, IMPORT-1).
   - `<mount>` and `--source` exclude each other; `--source` needs `--system`.
2. **Per system:** PS1 exactly as B56 (cue sets, CHD, `.m3u` sets, `.iso` rules, BIOS). SNES / NES / Genesis: one
   candidate per file (kind `rom`), the target `games/<system>/<the relative path>`, the header checks above, the
   duplicate check above. The labels `T1…` run across systems in the source's order; every candidate row carries its
   `system`. The game ids are the plugin's `_stable_id(system, "games/<folder>/<rel>")`.
3. **The plan:** `source_form` (`stick` / `plain`), `systems` (planned), `reported` (`{folder: why}` for ps2 / n64 /
   gamecube / unknown), `journal_pending` (count). The plain form's plan equals the stick form's on the same files in
   everything but `source_root`, `source_form`, the sources' paths and `created_utc`.
4. **apply:** the journal's recovery first; then each candidate as B56 (parts `x`-opened, hashed, `fsync`, verified,
   `os.link`, the entry last) inside its journal entry; the marks (`new` for every placed title, any system; `hide`
   PS1 only); the applied record; the sanitized log (+ `system` per row, `journal_cleaned`, `journal_resumed`).
5. **The terminal / the log:** labels, systems, kinds, counts, codes; never a name, path, hash or mount.

`companion/import_marks.py` gets `pending(project_root)` (the journal's `list_ids`, never raises); `plugins/games.py`'s
B56 hidden-ids hunk leaves those out too (inside `_import_marks is not None`).

`docs/IMPORT.md` extended in plain words: the plain-folder form; the systems; "PS2 games stay on the external drive
and are listed from there"; N64 / GameCube not yet; what an interrupted import does.

**Absent:** every command refuses (exit 9) before any path is opened (both forms); the companion never imports
`import_marks` (B56), so the list ignores the journal and is today's byte for byte.

## 2. Tests (fixture trees built from bytes in temp dirs, removed at exit; no real game file)

`tests/import_usb/test_b58.py`:
- **each system's accept / reject by extension and header:** SNES LoROM `.sfc`, HiROM `.smc` with a copier header
  (accepted, `copier_header` true), a bad checksum, a bad size; NES with / without `NES\x1a`; Genesis `.md` / `.gen` /
  `.bin` with `SEGA`, a `.bin` without; an archive / a `.txt` → `unknown_type`;
- **the duplicates per system:** by hash under another name (`duplicate_of` the library id), a library file of
  another size never hashed, the same title, inside the source, a target with other bytes;
- **the plain-folder form equals the stick form** on the same files (every system), and needs no symlink;
- **the interrupted apply:** a crash mid-copy leaves a `.import-*` part and a journal entry; a crash after one disc of
  a made-`.m3u` set leaves a linked disc, **which the real plugin's `_scan` (flag on) does not list**; the next `plan`
  accepts the title again; the next `apply` cleans and resumes (placed, no part, the journal empty, verify ok); an
  `apply` of another plan cleans only (files and new dirs gone); a changed final is left (`journal_conflict`);
- **PS2 and N64 folders reported, nothing planned** (stick form; `--system ps2` / `n64` in the plain form → exit 3);
- **NEW for a placed SNES title** in the real plugin's node names;
- **absent → the tool refuses** (both forms, exit 9) and nothing else changes; the plugin without the flag lists a
  journaled file (today);
- **the log:** no fixture name, title word, path, hash or game id; systems and labels present;
- a source inside the library refused.
- B56's 21 tests unchanged and green.

## 3. Record

`evidence/B58_IMPORT_SLICE_1B_2026-11-08.md` + `b58_2026-11-08/` (design + hash, diff, proof absent, tests ×3,
mutations, host suites against the baseline copy, `redact_check.txt`, `manifest.sha256`);
`patches/B58_IMPORT_SLICE_1B.md`; `docs/IMPORT.md`.
