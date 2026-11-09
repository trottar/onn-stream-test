# B74 — the disc change made safe (design, written before any B74 code)

## 0. Settled (read-only; RetroArch and the core not started)

### (1) A lid cycle on a PS1 and on Beetle; the HOME-10 black screens

- **The core on the hub** is `Beetle PSX HW 0.9.44.1 82d8e05`. That is its library name and version, read from the
  core file's own strings (`strings`; nothing run).
- **Its state names** are in the same file:
  - `DiscChanged` and `DiscStartupDelay` in the CD controller's state;
  - `CD_TrayOpen` and `CD_SelectedDisc` in the console's state.
  So a save state carries the tray and the selected disc. B71's "after a LOAD the disc is unknown" stays.
- **What these do**, from Beetle's upstream source (libretro `beetle-psx-libretro`: `libretro.cpp`'s disk-control
  callbacks and `mednafen/psx/cdc.cpp` `PS_CDC::SetDisc`). This is recalled: no source is on the hub and nothing was
  fetched. The field names above are the part confirmed on the hub.
  - **`set_eject_state(true)`** (the tray opens) sets `CD_TrayOpen` and calls `SetDisc(tray open, no disc)` at once.
    The drive is stopped: its status is STOPPED, a read in flight is dropped and the sector pipe is cleared. This is
    the console's state from that instant.
  - **`set_image_index(i)`** works only with the tray open. It sets `CD_SelectedDisc` and nothing else; the CD
    controller still has no disc. **So the in-between discs of a multi-step change (3/4 in 2 → 4) are never seen.**
  - **`set_eject_state(false)`** (the tray closes) calls `SetDisc(closed, disc i)`:
    - the controller gets the new disc and reads its TOC;
    - **`DiscChanged = true`**: the status byte's "shell open" bit is latched and stays set until the game's next
      Getstat reads it;
    - **`DiscStartupDelay`** is about 1 s of emulated time, during which commands answer "not ready" (the spin-up).
  - **Nothing needs emulated frames between the open and the close.** Every effect is applied to the core's state at
    the call, and the latch keeps the "lid was opened" fact until the game looks.
  - **With the core paused through the sequence**, the game wakes at RESUME to: its read stopped, the lid-opened bit,
    about 1 s of spin-up, and the new disc. That is what a fast lid cycle on a console looks like to a game.
  - **The 0.4-s spacing** happens while the core is frozen, so it is zero emulated time. It only paces RetroArch's
    loop.
- **A real PS1:**
  - a game reads its files by sector address on the disc in the drive;
  - opening the lid outside the game's own "insert disc N" prompt stops the drive under it. The game then waits, shows
    its own lid message, or crashes; there is no system-level recovery;
  - after the close, those sector addresses hold another disc's data, so the game crashes or shows black;
  - **at its own prompt** the game polls the drive status, sees the lid-opened bit, waits for the spin-up, checks the
    new disc and carries on.
- **The rows** (`home10_2026-11-09/c38/`):
  - **the sequence was the same in all five changes**: the eject, each step confirmed by RetroArch's own
    `Setting disc in tray: k/4`, the close, all while paused;
  - **two carried on and three went black.** 1 → 4 (3 steps, 1854 ms) carried on, while 2 → 4 (2 steps, 1407 ms) went
    black. So neither the step count nor the time explains the outcome;
  - what differs is the game. The black 2 → 4 sitting had **booted from disc 2** (RetroArch's restore). The 4 → 1 after
    it was a change on a game already gone black. The last 4 → 1 was **disc 4's code at its title screen** reading
    disc 1's sectors;
  - the two that carried on were changes **away from disc 1 during its intro**, which kept playing. A movie already
    buffered, or the same data at the same place on each disc, would do that; which one is not knowable from the
    rows.
- **Settled: the black screens were the game's reaction to a lid cycle outside its prompt, not a fault of the
  sequence.**
  - **The host sequence stays as built** (eject, the steps, close, 0.4 s apart, with the game left paused).
  - **The running-core variant is not adopted.** Beetle does not need frames with the lid open. Running the core
    with the tray open would let the game run its no-disc path, with sound and timers, while the onn shows it paused.
    It would not make an unprompted change safe either.
  - Disclosed: the dropped read raises no interrupt in Beetle at the open, where a console's drive would report an
    error. That is the same in either variant, and the game's next command still sees "not ready" for about 1 s.

### (2) The restored disc

- RetroArch keeps a **disk index record** per content: `<savefile dir>/<core library name>/<content stem>.ldci`, a JSON
  `{"version", "image_index", "image_path"}`. It is written when the content closes, read at the next launch, and
  handed to the core's `set_initial_image`. Beetle uses it only when `image_path` equals its own `.m3u` entry at that
  index.
- **On the hub:** one such record, for the 4-disc set, under `saves/Beetle PSX HW/`. Its `image_index` is **0 now**,
  because HOME-10's last change was 4 → 1. Its `image_path` equals the `.m3u`'s folder joined with the entry; that was
  checked as a boolean, and neither path is recorded.
  - **So HOME-11's C41 must first leave the set on another disc** (below) to read anything.
- **The host's override at a set's launch:** before RetroArch starts, the record is set to `image_index j − 1` and
  entry j's path. j is 1 unless the user chose a disc.
  - It is written only when the record differs. With no record and j = 1 nothing is written, because disc 1 is
    RetroArch's own start.
  - The write is atomic (a temp file in the same folder, then a replace). The record's other keys are kept. Nothing is
    ever deleted.
  - **Where:** an existing `<stem>.ldci` in the savefile dir or any folder directly under it. Otherwise (only when
    j > 1) the core's library folder: `mednafen_psx_hw_libretro` → `Beetle PSX HW`, `mednafen_psx_libretro` →
    `Beetle PSX`; for an unknown core, the savefile dir itself.
  - The savefile dir is the `savefile_directory` of the session config the launch has just written, so an isolated
    cheat / mod session uses its own.
- **Only the library launch sets it.** The plugin's `launch` passes `start_disc` = the `disc` query, or 1 without one.
  - The recovery launch goes through the same action, so disc 1; its state then loads its own disc.
  - **B54's relaunch for the players** (`relaunch_ports`) calls `launch()` without it, so RetroArch's restore (the disc
    at that stop) is kept.
- **Read back:** the launch's own `Setting disc in tray: k/n` is the **`launched_disc`**. It is the first such line
  after the launch, kept on the session and on the rows.

### (3) The legitimate case

The game's own "insert disc N" prompt cannot be reached without a save near one, and the user has none. The design is
safe without it: the chooser warns first, and the TV says what to do if the game freezes.

## 1. The design

**Host** (`PRIVYHUB_DISC_SWAP=0` = today: no multi-disc session, nothing written, the unknown action):
1. `disc_swap.py`:
   - `parse_start_disc(value, discs)`: 1..n, else 1;
   - `m3u_entries(path)`;
   - `ldci_set(savefile_dir, core_name, content_path, disc)` → `"set"` / `"kept"` / `"none"` / `"error"`. Paths never
     returned or logged;
   - `first_index(text, discs)`.
2. `emulator_manager.launch(…, start_disc=None)`: for a multi-disc session with `start_disc` given, `ldci_set` runs
   before the Popen.
   - The game log gets `PS1 start disc: j of n (record <set|kept|none|error>)`.
   - The session is `{"discs": n, "disc": j, "start_disc": j, "launched_disc": None}`.
   - `start_disc` None (the relaunch) → B71's session and no write.
   - `_disc_refresh` sets `launched_disc` from the first launch line, and `disc` from the newest as before.
3. `disc_swap` rows: B71's keys **plus `launched_disc`**. `launch_ports`: plus `start_disc` / `launched_disc` on a set
   only.
4. The plugin:
   - `launch` passes `start_disc` = `parse_start_disc(query disc)` when the knob is on. Off → today's call;
   - `details` gains `discs` for a multi-disc set, so the client can offer "Start on disc…".
5. **The swap sequence is unchanged** (the settled (1)).

**Client** (`debug.privyhub.disc_safe`, default on; `0` = B71's flow):
1. **CHANGE DISC** (DISC on B73's bar):
   - the first time on this onn: a dialog "Change disc" with **"Change discs only when the game asks for the next one —
     changing at any other time can freeze the game"**, and the buttons **"I understand"** and "Cancel";
   - "I understand" is remembered in the app's preferences (once per onn), then the chooser;
   - after that, the chooser straight away.
2. **After a change** the status line reads **"Disc j of n — if the game freezes, use LOAD or END"**; the bar keeps
   "Disc j of n".
3. **"Start on disc…"**:
   - shown only for a set (the details' `discs > 1`), as an item of the launch's Extras menu (Start Fresh / Load Save /
     **Extras** → Cheats, Mods, **Start on disc…**);
   - its chooser "Disc 1" … "Disc n" → the normal launch with `&disc=j`.
   - Read: "the Back menu … at launch". The in-game bar has no room for a fifth button (B73), and a start from inside a
     game would throw the sitting away; disclosed.
4. **A one-disc session is untouched by all three** (no `discs`), byte for byte.

## 2. Tests

**Host** (`tests/b74_disc_safe`, a fake RetroArch port and a fake RetroArch boot that reads the record as RetroArch
does):
- a set left on disc 4 → the launch sets disc 1, and the fake boot's launch line is 1/4 → `launched_disc` 1;
- disc 1 already → the record's bytes and mtime unchanged;
- no record and disc 1 → none written;
- disc 3 chosen → created in the core's folder → 3/4;
- a malformed record; the other keys kept;
- the knob off → nothing; the relaunch (`start_disc` None) → nothing;
- the settled sequence on the fake port: eject / steps / close, no `PAUSE_TOGGLE`, the row with `launched_disc`;
- the plugin's `disc` query, the default 1, and the knob → today's call; `details` with `discs` only on a set;
- a one-disc `.cue` launch → no record touched, no key, today's row;
- no path or label in any row or line.

**Client** (`B74DiscSafeTest`):
- the warning once (not acknowledged → shown; acknowledged → not; the property off → never);
- the text;
- the chooser (B71's rows);
- the line after a change;
- "Start on disc…" only with `discs > 1`, its query `&disc=j`;
- the property's parse.
