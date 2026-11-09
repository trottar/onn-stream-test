# B68 — design, written before any B68 code (one entry per multi-disc PS1 title: `.m3u` files in the library)

Queue: `handoffs/QUEUE_2026-11-09X.md` §B68, run because the user's message began **"go m3u"**. Built after B67 in
`/tmp/b_q16x_work` (the diff against the after-B67 snapshot). A tool behind `PRIVYHUB_IMPORT=1`. **B does not apply
it** (A applies at HOME-9 on the user's word). No title here: sets are `S1…`.

## 0. Settled (the hub's library and stores, read by name and count only)

- **The library's multi-disc sets** (`games/ps1/`, by B56's `(Disc N)` pattern, the same folder and title):
  - **6 sets**: five of 2 discs, one of 4, so **14 disc `.cue`s**;
  - all at the folder's top level, numbered from 1 with no gap;
  - **no `.m3u`**, no `.chd` discs.
- **The list already does the rest** (`plugins/games.py` `_scan`, every build, no flag):
  - an `.m3u`'s named files are hidden and the `.m3u` is the entry;
  - its title is `_clean_name` of the `.m3u`'s stem. Named "<title>.m3u", the set reads as the title without
    "(Disc N)". **No list change is needed.**
- **Beetle PSX HW reads an `.m3u`** (one disc file per line, relative to it).
- **Disc swap:**
  - RetroArch has `DISK_EJECT_TOGGLE` / `DISK_NEXT` / `DISK_PREV` among its commands (strings in its binary);
  - **the onn cannot reach a disc swap today:** the companion sends none of them, the onn's Back menu has no disc
    entry, and RetroArch's own menu is not on the stream;
  - **listed for the next APK** (a host `disc-swap` action and a "Change disc" entry in the Back menu). Until then a
    set plays disc 1 and changes disc only where the game itself asks through the core.
- **What an `.m3u` changes for a title's saved things, in plain words:**
  - PrivyHub keys a title by its list entry's id (from its file path) and its save states by the loaded content's
    name. **An `.m3u` is a new entry with a new id and a new name;**
  - **save states:** **none** exist today for any of the 14 disc entries (0 state files; 0 slot-index entries), so
    nothing to move;
  - **in-game memory cards:** Beetle names the card after the loaded content. **One card file exists today (one set,
    disc 1).** With the `.m3u` the game would start with an empty card, and that title's in-game saves would not
    show until the card is copied to the set's name;
  - **play counts / favorites / metadata (B63's capability, controller profile):** 0 entries today for the disc
    entries.

## 1. Built: `tools/library_m3u.py`

- **`plan`** (read-only; refuses without `PRIVYHUB_IMPORT=1`, exit 9):
  - groups the library's PS1 `.cue` / `.chd` files by (folder, B56's `title_key`) with a disc number; a set is ≥ 2
    discs numbered 1…n;
  - **reported, never planned:** a gap (`disc_gap`); a disc already named by another `.m3u` (`covered`); an `.m3u`
    of that name already present with the same lines (`already`, so it is idempotent) or other lines
    (`m3u_differs`, left alone);
  - for each set, the `.m3u` "<title>.m3u" beside its discs, the lines the disc file names in disc order (B56's
    `m3u_bytes`);
  - the per-title stores of its disc entries (counts);
  - **the migration it would do:** the state files `<disc stem>.state1-3` (and their `.png`) and their slot-index
    entries (the newest per slot across the set's discs), and the card files (`.srm` / `.mcr`, the newest across the
    discs), each to the set's name, **only where the target is absent**;
  - printed as labels `S1…` and counts; `--json` writes `data/import/m3u_plan.json`.
- **`apply`** (the latest plan, re-checked):
  - writes each planned `.m3u` with B56's no-overwrite placement (temp + link, never replacing a file);
  - **never moves, renames or deletes a disc**;
  - **`--migrate-states`** (the user's word) also copies the states / cards / slot entries in the plan. Without it,
    the output says plainly "<n> card / state file(s) would no longer show for <k> set(s); run again with
    --migrate-states";
  - the record `data/import/m3u_applied.json` (the `.m3u`s and copies it made, with their hashes);
  - a second `apply` → everything `already`.
- **`undo`:** removes only the `.m3u` files and copies the record lists, and only if their bytes still match. Never a
  disc or a source file.
- **The log** `data/import/logs/library_m3u_<UTC>.log`: counts, labels and codes only (no name, path or id).
- **Absent** (`PRIVYHUB_IMPORT` not `1`): every command exits 9 and writes nothing.

## 2. Tests (`tests/b68_library_m3u/`, fixture libraries in temp dirs)

- **The plan:**
  - two sets (2 and 4 discs) → two `.m3u`s with the lines in disc order; a single "(Disc 1)" → nothing;
  - a gap → `disc_gap`; a subfolder set → its `.m3u` beside it;
  - an existing equal `.m3u` → `already`; a different one → `m3u_differs`; a disc named by another `.m3u` →
    `covered`.
- **`apply`:**
  - the `.m3u` bytes; **every disc's bytes and mtime unchanged**;
  - **the real plugin's `_scan` in a fresh interpreter → one entry per set, titled without "(Disc N)", the discs
    hidden**;
  - a second apply → `already`, nothing written.
- **The migration:** a card on disc 1 and a newer one on disc 2 → the set gets disc 2's (newest), the originals
  untouched; a present target never overwritten; a state + slot entry copied to the set's id; without
  `--migrate-states` nothing copied, and the line says so.
- **`undo`:** only its `.m3u` / copies go; a changed `.m3u` is left.
- **Absent:** exit 9 for each command, nothing written.
- **The log:** no fixture title, file name or id.
- **Mutations:** the gap check removed; overwrite allowed; the disc order reversed; the migration ignoring
  "newest"; undo removing a changed file.
