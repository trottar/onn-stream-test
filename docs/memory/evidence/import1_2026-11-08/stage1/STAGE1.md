# IMPORT-1 stage 1 (2026-11-08 19:04-19:xxZ, unattended)

- The read line at ~19:04Z. HEAD `017153b6` (queue T committed: B54 / B55 / B56), the tree clean. The pin still
  `cfe0211c…` (queue T's APK `9aa00ba2…` is built for HOME-7, not installed).
- **Precondition** (`check_before.json`, `client_before.json`, `properties_before.txt`, `drop_ins_before.txt`,
  `tmp_free.txt`): sixteen adopted lines, `--check` ok, `cfe0211c…` CONFIRMED, the eleven properties empty, the two
  units only, no game, no movie; `/tmp` 6.7 GB free. **The drive mounted read-only** (exFAT `ro` under its automount).
- **The library before** (`library_before.txt`): the PS1 folder 419 files, 46963917095 B; the core's BIOS folder empty.
- **The bench drop-in** `b56-import.conf` (B's printf, `b56-import.conf.copy`), `daemon-reload`, restart
  (`restart_at.txt`): **seventeen** lines; `--check` not ok on the environ only, the extra line `PRIVYHUB_IMPORT=1` (the
  bench flag); the journal clean; the games list "PlayStation (OpenBIOS) (80)".
- **The source:** the drive's PS1 folder (no subfolders; 80 `.cue`, 338 `.bin`, 1 other) linked as
  `/tmp/privyhub_import_root/PrivyHub-Import/games/ps1`. **No PS1 BIOS on the drive** (no `games/ps1/bios/`, no
  `bios/ps1/` or `bios/` at the top, no PS1 `scph*` name; the drive's only BIOS files are the PS2 folder's), so no
  `bios/ps1` link.
- **Read-only, confirmed:** the tool opens source files `rb` only and rejects only files that are themselves symlinks
  (the root's `games/ps1` link is followed; its files are plain). **Disclosed:** one write probe (`touch` of a dot-file
  through the link) was refused "Read-only file system" — nothing was written; the hash below proves it.
- **The drive's PS1 folder listing hash before** (`find -printf '%P %s %T@\n' | sort | sha256sum`):
  `9fafa53e…6df7` (`drive_hash_before.txt`).
- **Pre-registration** `../preregistration.md` hashed 19:06:33Z, before `inspect` / `plan`.
- **I1 inspect** (`inspect_output.txt`, labels only): exit 0; **72 candidates** — 66 `cue_set` (2-58 files each) and
  **6 `m3u_set`** (multi-disc, 4-8 files, an `.m3u` made on the hub): T6, T18, T20, T33, T45, T49; **1 rejected file,
  `unknown_type`**; "BIOS on the stick: none"; "BIOS in the PS1 core's folder: none (the core uses its built-in
  OpenBIOS)". **I1 met.**
- The user's PS1 save states (the slot index): 19 slots over 12 titles.
- **I2 plan** (`plan_output.txt`, labels only; 19:06:47-19:14:05Z, ~7.3 min hashing ~47 GB from the drive): exit 0;
  **Accept 0, duplicate 72, reject 0; 1 other file rejected** (the `unknown_type` above); every T "duplicate: already
  in the library", the six multi-disc sets included; "BIOS: none to copy; PlayStation keeps its built-in OpenBIOS";
  space 0 MB needed, ok; the plan file and the log under `data/import/plans/` / `data/import/logs/` (one UTC name each).
  **I2 met, as pre-registered** (every title already in the library; no ACCEPT, so no duplicate-check miss).
- The drive's PS1 folder listing hash after `plan`: equal to before.
