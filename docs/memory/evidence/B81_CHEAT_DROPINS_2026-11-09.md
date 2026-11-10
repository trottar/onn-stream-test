---
memory_schema: 1
as_of: 2026-11-09
status: BUILT, NOT ADOPTED (session B, queue AC) — the drop-in folders: the user's PS2 .pnach per game (staged as PCSX2's cheats file per launch) and the user's own .cht on PS1 / SNES (launchable as the database's); docs/CHEATS.md in plain words. Default on, PRIVYHUB_CHEAT_DROPINS=0 = today. Nothing fetched, no emulator started, no folder created on the hub by B; nothing committed. No title, serial, path or identifier in this record
---

# B81 — the drop-in folders (2026-11-09)

**The user's answer (G3c):** the PS2 `.pnach` drop-in and their own `.cht` on PS1 / SNES — "Maybe, I'll have to find
them": **the mechanism is built; the files are the user's, later.**

**Design** hashed before code at 23:36:27Z.

## What was built (`b81.diff`, with `docs/CHEATS.md`)

- **`companion/cheat_dropins.py`:** the folders, the file lists (sorted by name, hidden names skipped), the `.pnach`
  groups, the staging of the ticked `.pnach` files as one `<SERIAL>_<CRC>.pnach` (each file headed by its number, not
  its name), and `ensure_folders` (the empty folders only).
- **PS1 / SNES:** `.cht` files under `data/games/retroarch/cheats/<ps1|snes>/<the game's file name without its
  ending>/` are appended to the Cheats list after the database's (`provider: user`, the file name, its sha at
  listing). A file that fails the database files' own checks (a bad count, a cheat already switched on) is left out
  and counted (`user_files_skipped`). They launch exactly as a database file (the catalog is the launch's input), with
  their own cheat profile and saves. A missing manifest no longer hides them. With no user file the catalog is
  today's dict.
- **PS2:** `.pnach` files under `data/games/ps2/cheats/<serial>/` (or the paths file's `PS2_CHEATS_DIR=`, then
  `<serial>/`) are listed by file name in Extras → Cheats (the serial from B80's PCSX2-log ids; unseen title →
  nothing listed). A cheat launch checks the pick first, stages the ticked files into PCSX2's `cheats/`, writes B80's
  game settings file with `EnableCheats = true` and every `[group]` of the files under `[Cheats] Enable`, and logs
  `PS2 cheats: n files enabled` (no name). The next plain launch rewrites that file with `EnableCheats = false` (B80's
  writer rewrites a file carrying its marker), so the cheats never carry into a normal start.
- **The folders** appear (empty) at the first Cheats list a companion process serves, with the knob on.
- **`docs/CHEATS.md`:** where cheats come from per system; where to put PS2 and PS1 / SNES files; the naming; that
  the hub downloads nothing for them; that every cheat in a `.cht` must start switched off; the knobs.
- **The onn:** no client change (the existing Cheats list).

## Tests (`tests/art_systems/test_b81.py`, 15)

PS1: appended after the database (index 1, its entries), staged for Beetle PSX HW byte equal, a pre-enabled file
skipped and counted, no user file = today's dict (and the knob 0), no manifest + a user file listed (the knob 0 → the
manifest error as today); only PS1 / SNES and no `..`; the folders made empty once, none with the knob 0; the `.pnach`
staging (both files' text, the groups, the name, no file name inside; a bad serial refused); the user's own PS2
folder from the paths file. **B49's rig:** listed by name with no serial in the reply, an unseen title "unavailable";
a cheat launch stages one file, `EnableCheats = true`, `[Cheats] Enable = <group>`, the line; the next plain launch
`EnableCheats = false` and no line; the knob 0 → nothing staged, nothing written; a bad pick refused before any write
and before PCSX2 starts; a plain launch without a written file is today; `docs/CHEATS.md` names the folders.

- 3 runs: 15 / 15 each. Mutations: **10 / 10 caught** (the runner copies `docs/CHEATS.md` from this item on; B76-B80's
  mutation runs predate that line and did not need it).

## The queue's tree checks (recorded here, the last item)

- `diffs_apply_in_order.txt`: HEAD + `b76.diff` … `b81.diff` in order = the tree's companion/, tools/, tests/,
  PrivyHub/ and `docs/CHEATS.md`; reversed in the opposite order → HEAD's export byte for byte.
- `tests_host_compare.txt`: every host suite on full exports of HEAD and of HEAD + B76 … B81 — the 72 shared suites
  read the same; `tests/art_systems` (89) is new and green; the same six `tools/` suites fail in both, as queue AA's.
  The tree's own runs of the touched suites are green (PS2 93, GameCube 54, B72 25, relaunch 19, N64 28).

## Disclosed

- **Deviation from the hashed design:** the folders are made at the first Cheats list, not in the games plugin's
  constructor (other suites construct the plugin through the package import, which would have written into the
  tree's `data/` during tests).
- A PS2 cheat session saves into the title's own slots and memory card.
- The older list-only folder (`data/games/user_content/<id>/cheats/`) is unchanged.
- PS2 `.pnach` files are concatenated as given; a file whose codes conflict with another is the user's to sort out
  (the TV lists files, not codes).

## Files

`b81_2026-11-09/`: the design + hash, `b81.diff`, `proof_flag_absent.md`, `tests_x3.txt`, `tests_mutations.txt`,
`tests_host_*`, `diffs_apply_in_order.txt`, `scripts/` (`run_host.sh`, `mutations.json`), checks, manifest. Patch
note: `patches/B81_CHEAT_DROPINS.md`.
