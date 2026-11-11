# HOME-12T close (2026-11-11 00:03Z-, after the user's C46 line)

- The N64 game stopped by A through the hub's own stop route 00:03:32Z (C46). The watcher stopped (its raw log off the
  repo).
- **The rule, part (a):** C51 met, C52 met, **C53 not met** (the labels too small to read from the couch) →
  **`3f21e2c6…` NOT CONFIRMED** → `85220f99…` reinstalled from `home12t_previous/` (`reinstall_at.txt`
  00:04Z, `reinstall_sha256.txt`; `adb install -r -d` Success, `reinstall.log`); read back **`85220f99…`**, paired,
  identity v2 (`client_close.json`). The pin unchanged; the patch notes not indexed.
- **Part (b):** C46 not met → **B87 not confirmed** (the APK's verdict unchanged by it); C52's hub half met → **B88
  met**.
- **Every property empty — twenty** (`properties_before_reinstall.txt` with `3f21e2c6…` on; `properties_close.txt`
  after); no `setprop`.
- `--check` ok, **CONFIRMED** (on `85220f99…`), eighteen environ lines (`check_close.json`); the two units
  (`units_close.txt`); the keeper not restarted (since 2026-11-08); the drop-ins the same (`drop_ins_close.txt`); no
  `e3_flag.conf`; nothing running (`processes_close.txt`); **the drive's folders before = after** (`drive_after.txt`).
- **No profile changed:** the profiles file's sha256 = stage 1's (`profiles_close.txt`; rewritten in place at C53 with
  the same bytes).
- **Left on the hub by design:** the companion runs queue AF's host parts (B87, B88; default on) since the stage-1
  restart; T82's widescreen toggle stays saved (`ps2_patches.on` `ws`; the user's own setting, made at C52) with its two
  PCSX2 `gamesettings/` files; `Dolphin.ini` `EnableCheats = True` and one Dolphin `GameSettings/` file left from
  HOME-12R's C47 (the next plain GameCube launch writes `False`).
- Nothing adopted, fetched, deleted or written to the drive by A; nothing committed.
