---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a5c51e37 (B74 built in /tmp/b_q19aa_work after B73; its diff against the after-B73 snapshot; applied to the tree second, uncommitted)
---

# B74 — the disc change made safe: the sequence settled, a set starts on disc 1, the warning, "Start on disc…"

**Classification: SETTLED + BUILT**, host + client, both default on:
- the host: `PRIVYHUB_DISC_SWAP=0` = today (B71's knob);
- the client: `debug.privyhub.disc_safe=0` = B71's flow.

**A one-disc session is today's byte for byte**, including the emulator's `launch()` call.

**Tests:**
- host `tests/b74_disc_safe` 22 green ×3 (a fake RetroArch boot that reads the record as RetroArch does, and B71's
  fake command port), with B71's 21 and B54's `players_session` 19 green in the same copy and in the tree;
- every host suite on full exports of HEAD and HEAD + B73 + B74: the same, apart from the new suite;
- client `B74DiscSafeTest` 6, inside JVM 271 / 271 and 260 / 260.

**Mutations:** host 8 of 9 caught (M5 is an equivalent mutant, explained); client 3 / 3.

**The APK `85220f99f92f893968647c185ed98e17456fe9e9bc9cc7bdb550c7c735c04864`** (B5 … + B54 + B67 + B70 + B71 + B72 (a) +
**B73 + B74**; B27 / B29 out): built twice to the same bytes; the baseline rebuilds `64d02f31…` byte for byte; pinned
at `PrivyHub/app/build/queue_aa_built/app-debug.apk`, **NOT installed**.

RetroArch and the core were not started; their files were read as data only. Nothing was fetched, and nothing was
written to the drive.

Design `b74_2026-11-09/design_written_before_code.md`, sha256 `54429724…fc6078cd`, hashed
**17:53:59Z, before any B74 code**.

## 0. Settled

### (1) The black screens were the game, not the sequence. The host sequence stays as built.

- **The core on the hub is `Beetle PSX HW 0.9.44.1 82d8e05`** (its own library name and version, read with `strings`).
  Its state names are in the same file: `DiscChanged` and `DiscStartupDelay` (the CD controller), and `CD_TrayOpen`
  and `CD_SelectedDisc` (the console). So a state carries its disc, and B71's "after a LOAD the disc is unknown"
  stands.
- **How Beetle handles a lid cycle.** This is from Beetle's upstream source as recalled: `libretro.cpp`'s
  disk-control callbacks and `cdc.cpp` `PS_CDC::SetDisc`. No source is on the hub and nothing was fetched; the field
  names above are the part confirmed on the hub.
  - **The open** stops the drive at once: STOPPED, the read in flight dropped, the sector pipe cleared.
  - **The index** changes only the selected disc while the tray is open. The controller has no disc, so **the
    in-between discs of a multi-step change are never seen**.
  - **The close** gives the controller the new disc. It **latches `DiscChanged`** (the status byte's "shell open" bit,
    held until the game's next Getstat) and starts **`DiscStartupDelay`** (about 1 s of "not ready", the spin-up).
- **No emulated frames are needed between the open and the close**; every effect is set in the core's state at the
  call. Done while paused, the game wakes at RESUME to its read stopped, the lid-opened bit, about 1 s of spin-up, and
  the new disc. That is a fast lid cycle as a console's game sees it. The 0.4-s spacing is zero emulated time.
- **A real PS1:**
  - a game reads its files by sector address;
  - a lid cycle outside its own "insert disc N" prompt leaves it reading another disc's data at those addresses, and
    it crashes or goes black;
  - at its prompt, it polls the status, sees the latched bit, waits out the spin-up and checks the new disc.
- **The rows** (`home10_2026-11-09/c38/`):
  - the same sequence in all five changes (eject, each step confirmed by `Setting disc in tray: k/4`, close, paused);
  - **1 → 4 (3 steps, 1854 ms) carried on, and 2 → 4 (2 steps, 1407 ms) went black.** Neither the step count nor the
    time decides the outcome;
  - what differs is the game: the black 2 → 4 sitting had **booted from disc 2** (RetroArch's restore); the next 4 → 1
    was on a game already black; the last 4 → 1 was **disc 4's code at its title screen**;
  - the two that carried on were changes away from disc 1 during its intro.
- **So the running-core variant is not adopted.**
  - Beetle does not need frames with the lid open.
  - Running the core with the tray open would let the game run its no-disc path, with sound and timers, while the onn
    shows it paused.
  - It would not make an unprompted change safe.
- **Disclosed:** Beetle's dropped read raises no interrupt at the open, where a console's drive reports an error. That
  is the same in either variant, and the game's next command still meets "not ready".

### (2) The restored disc: RetroArch's disk index record

- RetroArch keeps `<savefile dir>/<core library name>/<content stem>.ldci`, a JSON `{version, image_index,
  image_path}`. It is written at close, read at the next launch and handed to the core, which uses it only when
  `image_path` equals its `.m3u` entry.
- **On the hub there is one record**, for the 4-disc set, under `saves/Beetle PSX HW/`.
  - **Its `image_index` is 0 today**, because HOME-10's last change was 4 → 1.
  - Its path equals the `.m3u`'s folder joined with the entry. That was checked as a boolean; no path is recorded.
  - **So "the set left on disc 4" no longer holds: HOME-11's C41 first leaves it on disc 4** (below).
- **The host now sets the record before RetroArch starts**: index j − 1 and entry j's path, j = 1 unless the user
  chose a disc.
  - It is written only when it differs; with no record and j = 1 nothing is written. The write is a temp file plus a
    replace in the same folder, and the record's other keys are kept. **Nothing is deleted.**
  - It looks for an existing record in the savefile dir or a folder directly under it. Otherwise it writes to the
    core's library folder (`Beetle PSX HW` / `Beetle PSX`), or the savefile dir for an unknown core.
  - The savefile dir is the one in the session config the launch has just written, so an isolated cheat / mod session
    uses its own.
- **Only a library launch of a set** sets it. B54's relaunch for the players keeps RetroArch's restore, which is the
  disc at that stop. The recovery launch starts on disc 1 and then loads its state, which carries its own disc.
- **Read back:** the launch's own first `Setting disc in tray: k/n` is **`launched_disc`**. Only text read before the
  first swap counts, so a swap's line is never taken for it.

### (3) The legitimate case

The game's own prompt cannot be reached without a save near one, and the user has none. The design is safe without it.

## 1. Built (`b74_2026-11-09/b74.diff`, 8 files; `DiscSafe.kt` and `tests/b74_disc_safe/` new)

**Host:**
1. **`disc_swap.py`:** `parse_start_disc` (1..n, else 1), `m3u_entries`, `savefile_dir_from_config` (the last
   `savefile_directory`), `ldci_set` (→ `set` / `kept` / `none` / `error`; it never returns or logs a path), and
   `first_index`.
2. **`emulator_manager.launch(…, start_disc=None)`:**
   - `_disc_start_prepare` sets the record **before the Popen**, for a multi-disc set with `start_disc` given;
   - the game log gets `PS1 start disc: j of n (record set|kept|none|error)`;
   - the session gets `start_disc`, `disc` = j and `launched_disc`;
   - `_disc_refresh` sets `launched_disc` from the first line while the launch line is open;
   - `disc_swap` closes the launch line first.
3. **The rows:** `disc_swap` = B71's keys **+ `launched_disc`** (ok and failure). `launch_ports` gets `start_disc` /
   `launched_disc` on a B74 set's launch only.
4. **The plugin:**
   - `launch` passes `start_disc` = the `disc` query, or 1, **only when the game is a multi-disc set** and the knob is
     on;
   - `details` gains `discs` (> 1) for a set.
5. **The swap sequence (`Swapper`) is unchanged.**

**Client** (`DiscSafe.kt` + `MainActivity`):
1. **CHANGE DISC (DISC)**:
   - the first time on this onn: "Change disc", **"Change discs only when the game asks for the next one — changing at
     any other time can freeze the game"**, with **"I understand"** / "Cancel";
   - "I understand" is stored in the app's preferences (`disc_change_warning_understood`), then B71's chooser;
   - after that, the chooser at once.
2. **After a change:** the status line reads **"Disc j of n — if the game freezes, use LOAD or END"**; the bar keeps
   "Disc j of n".
3. **"Start on disc…":** a third item in the launch's **Extras** (Start Fresh / Load Save / Extras → Cheats, Mods,
   **Start on disc…**), only for a set (`discs > 1` in the details). It opens a chooser "Disc 1" … "Disc n", and the
   pick launches with `&disc=j`. Without a pick, the URL is today's.
   - **Read:** the queue's "a 'Start on disc…' option in the Back menu" together with "unless the user chose a disc
     at launch". The paused bar has no room for a fifth button (B73), and a start from inside a game would throw the
     sitting away. So it sits where a launch is chosen. Disclosed; the user may want it elsewhere.

## 2. Tests and mutations

**Host** (`tests_x3.txt`, `tests_in_the_tree.txt`, `tests_host_compare.txt`, `tests_mutations_host.txt`):
- **a set left on disc 4** (the fake boot reads 4/4 today) → the record set to disc 1 → the boot's line 1/4 →
  `launched_disc` 1, and the game-log line;
- disc 1 already → the bytes and mtime unchanged; no record and disc 1 → nothing written;
- disc 3 chosen → created in `Beetle PSX HW/` → 3/4; the folder map (`Beetle PSX`, an unknown core → the savefile
  dir);
- a malformed record; other keys kept; no temp file left; a record in the savefile dir itself; an isolated session's
  own dir (the last `savefile_directory` wins);
- the start-disc parse; the relaunch (`None`) and the knob → nothing written; a one-disc `.cue` / `.m3u` → nothing, no
  line;
- `ldci_set` deletes nothing and returns only the four words;
- the wiring: the record before the Popen, the start line before the Popen, `relaunch_ports` without it;
- **the settled sequence on the fake port**: 1 → 3 = EJECT, NEXT, NEXT, EJECT; no `PAUSE_TOGGLE`; the spacing; the
  row's keys = B71's + `launched_disc`; no label;
- `launched_disc` = the first line of a read, and never a line after the first swap; the failure row;
- **the plugin:**
  - `start_disc` 1 / "3" for a set;
  - **a one-disc game's call and the knob's call are today's exact kwargs**;
  - `launch_ports` with / without;
  - `details` `discs` only on a set.
- **Full host runs:** the first B74 broke `tests/players_session` (3 failures). B54's tests pin `launch()`'s kwargs,
  and the first build passed `start_disc=1` on every launch. Fixed so that only a set's launch passes it. Re-run: HEAD
  = HEAD + B73 + B74 apart from the new suite.
  - The same six `tools/` suites fail in both. They read fixtures under `docs/` and `logs/`, which the four-folder
    copies do not hold.
- **Mutations** (each alone, the file restored):
  - **caught:** M1 the record never set; M2 the path not written; M3 `launched_disc` from the newest line; M4 the
    default 1 removed; M6 the launch-line guard removed; M7 a right record rewritten; M8 `start_disc` on every launch;
    M9 the knob removed in `session_for`;
  - **M5** (the plugin's own knob check removed) is equivalent: `session_for` checks the same knob.
  - History: the first pass missed M3 / M6, so two tests were added; M8 / M9 came with the fix.

**Client** (`tests_jvm.txt`, `tests_jvm_apk_copy.txt`, `tests_mutations_jvm.txt`):
- the warning once (the property off → never); the text; B71's chooser; the line after a change (and with an unknown
  disc); "Start on disc…" only for `discs > 1`; `&disc=j`; the property.
- Mutations caught: J1 the warning every time; J2 one-disc games offered "Start on disc…"; J3 the line without the
  advice.

## 3. The APK (`apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`)

- **The tree:** HEAD's client (B70 + B71 + B72 (a) on B5 … B67) + B73 + B74, with `b29.diff` / `b27.diff` reversed on
  the client paths. That is queue Z's composition plus the two.
- **Built:** `:app:assembleDebug --offline --rerun-tasks --no-configuration-cache`, **twice → the same bytes**
  `85220f99…4864` (9,722,372 B, 945 entries).
- **The baseline** (HEAD, B29 / B27 reversed) rebuilds **`64d02f31…` byte for byte**. The only source difference is the
  5 files in `apk_source_diff.txt`.
- **`apksigner verify`:** Verifies (v2), with the same signer certificate (`455bde4e…`) as `5f72af4b…`.
- **Not installed.** `5f72af4b…` stays CONFIRMED, on the onn.

## 4. Files

`b74_2026-11-09/`:
- the start files; the design and its hash;
- `b74.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_x3.txt`, `tests_in_the_tree.txt`, `tests_host_full_export_head.txt`,
  `…_after_b74_first.txt`, `…_after_b73_b74.txt`, `tests_host_compare.txt`, `tests_jvm.txt`,
  `tests_jvm_apk_copy.txt`, `tests_mutations_host.txt`, `tests_mutations_jvm.txt`;
- `apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`;
- `scripts/`;
- `redact_check` / `title_check` (+ `.txt`), `manifest.sha256`.

Patch note: `patches/B74_DISC_CHANGE_SAFE.md`.

**One line for the user:** a game with several discs now always starts on disc 1, unless you pick another under
Launch → Extras → "Start on disc…". CHANGE DISC first warns once that changing discs outside the game's own request
can freeze the game. After a change the TV says to use LOAD or END if it freezes. The black screens at HOME-10 were the
game reacting to a disc change it did not ask for, as a real PlayStation would; the hub's change itself was right.
