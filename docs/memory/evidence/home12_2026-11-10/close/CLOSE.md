# HOME-12 close (2026-11-10 20:52-, unattended after the user's "Wrap up")

- The watcher stopped 20:52:42Z (its log off the repo; the label-only excerpt is `../c45/watch_lines.txt`).
- **The rule (CL-B7 §6):** C46, C47 and C48 not run → **`de6682db…` NOT CONFIRMED** → `85220f99…` reinstalled from
  `home12_previous/` 20:53Z (`reinstall_at.txt`, `reinstall_sha256.txt`, `adb install -r -d` Success, `reinstall.log`);
  read back **`85220f99…`**, paired, identity v2 (`client_close.json`). The pin unchanged (nothing to move).
- **Every property empty — eighteen** (`properties_before_reinstall.txt` with `de6682db…` on, `properties_close.txt`
  after); no `setprop` this session.
- `--check` ok, **CONFIRMED** (on `85220f99…`), eighteen environ lines (`check_close.json`); the two units
  (`units_close.txt`), the keeper not restarted (running since 2026-11-08), the companion not restarted this session;
  the drop-ins the same as stage 1 (`drop_ins_close.txt`); nothing running (`processes_close.txt`: no RetroArch,
  Dolphin, PCSX2, encoder or AppImage helper); **the drive's folders before = after** (`drive_after.txt` = stage 1's).
- **The user's test profiles:** "Swap" deleted by the user (20:43:30Z); T82 and T83 on Default; **no game carries a
  test profile.** The emulators' own files keep the last launch's pads until their next launch rewrites them:
  PCSX2 `[Pad1]` Square / Triangle swapped, `GCPad1` A / X swapped (the next PS2 / GameCube launch writes the pads
  from that game's profile, Default = the normal layout).
- **Made by the hub this session (the companion, by design):** the three empty drop-in folders (B81, at the first
  Cheats list). Nothing else written to the hub's `data/` by A; nothing deleted, fetched or adopted.
