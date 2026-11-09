---
memory_schema: 1
as_of: 2026-11-09
status: DESIGN (B75, session B queue AB) — the feature-parity matrix. Each per-game feature a PS1 / SNES game has on the onn today, read from the code and checked against N64 (RetroArch), PS2 (PCSX2 2.8.2) and GameCube (Dolphin 2609b). READ-ONLY. No code; nothing fetched (the databases are named, not queried); nothing adopted; nothing committed. No title, serial, path of the user's files, address or game identifier is written here. The user ranks the gaps; the full §H6 text in the ROADMAP waits for that ranking
---

# H6 — the feature-parity matrix (PS1 / SNES → N64 / PS2 / GameCube)

**The user (2026-11-09):** "There are still some things that need to be done. Everything ps1/SNES can do the PS2, etc
should as well. For instance, cheats, custom controls, artwork, etc". On the artwork today: "Hub fetched them". On the
cheats: "I believe the cheats were fetched that too but I guess that was through retroarch so that might be a
constraint".

**Baseline:** HEAD `6885189c` (queue AA committed); the tree clean at the start (`logs/b75_git_status.txt`, empty).

**How it was read:**
- **The onn:** the game list, the details dialog, Options, the launch dialog, Extras, the paused bar
  (`MainActivity.kt`, `streaming/`).
- **The host:** the list, details, favourites and history (`plugins/games.py`); the launch and the per-game data
  (`games/emulator_manager.py`); the fetchers (`games/metadata_importer.py`, `games/cheat_importer.py`,
  `games/startup_reconcile.py`); the three system modules; `emulators.json`.
- **The hub's own data, read for shape and counts only:** the cheat manifest, the metadata file, the library state,
  the input profiles, the controller overrides, and the cheat provider's cached index of RetroArch's cheat database
  (fetched by the hub on 2026-09-09, read here from disk).
- **PCSX2 2.8.2 and Dolphin 2609b:**
  - their data folders on the hub (folder names and file counts);
  - their AppImages, read as data: listed with `7z`, and the binaries and bundled files streamed into memory for
    strings and section counts. Neither emulator was started and nothing was extracted to disk.

**Cell words:**
- **present:** it works for that system today, through the same onn screen.
- **missing:** it could exist and does not. The mechanism, source, privacy bearing and size are given.
- **impossible:** nothing to have on that system (a cartridge has no discs; a system with one pad type has nothing to
  choose; four built-in ports need no multitap).

**Sizes:**
- **S:** a config line or a system line at launch.
- **M:** one B item, host only.
- **L:** a queue with an APK.

---

## 1. What PS1 / SNES have today, by where it shows

### The list (a tile = the box art + the host-given name)

| Feature | How it works today on PS1 / SNES (mechanism; source) |
|---|---|
| **Box art** | The tile's picture comes from the hub's box-art cache, keyed by the game's PrivyHub id. It is filled by the **hub's metadata fetcher**, which runs by itself at companion start when titles are new or incomplete (7-day retry). The fetcher: (1) downloads **RetroArch's database** system list for the system (no-intro for SNES; redump for PS1), which says nothing about the user's titles; (2) matches each title (SNES by checksum, PS1 by its file name); (3) downloads the matched title's box art from **RetroArch's thumbnail server**, with the database's title name in the request. The importer knows **NES, SNES, Genesis, PS1 only**. On the hub: 64 PS1 and 43 SNES titles have cached art. A picture placed by hand in the cache (or beside the title) shows too. |
| **Details line** | Built by the onn from the host's details: system, catalog title, region, release year, genre, developer, publisher, metadata source, players, box art, cheat / mod file counts, format, size, favourite, play count, "save state: available", the controller. The descriptive fields come from **RetroArch's database** (the same fetch as the art). |
| **Players (single / multi)** | From the database's max-players field. Options → **Players** overrides it per game (stored on the hub). It drives the "Single Player" / "Multiplayer" views and B46 / hold-to-join's port count. |
| **Name suffixes** | " - <System>" in the mixed views (Favourites, Recent, Continue, Search). |
| **"NEW"** | " · NEW" for 7 days after a title was imported by the import tool (B56). Behind `PRIVYHUB_IMPORT=1`, which is **not** an adopted line (the bench drop-in was removed at HOME-7). **It shows on no system today.** |
| **Favourites** | Options → Add / Remove from Favourites; the Favourites view. Hub library state, any system. |
| **Recently played / Continue / play count** | Each launch records the last-played time and play count on the hub. The Recent view, the Continue view (the game has a PrivyHub save state) and "Play count" in the details. Any system. |
| **Play time** | **None on any system.** Only a play count. |

### The launch dialog

| Feature | How it works today on PS1 / SNES |
|---|---|
| **Start Fresh / Load Save** | "Launch on Companion" → **Start Fresh** / **Load Save** / **Extras**. A live session of the same title shows **Resume** instead. A recovery save shows the recovery prompt (Resume / Copy / Discard) before any launch. |
| **Extras → Cheats** | (1) The cheat files are **fetched from RetroArch's cheat database** (by system folder, matched by title) by a tool run by hand. Unlike the art, it is not run at companion start. The hub holds files for 67 PS1 and 4 SNES titles. (2) On the onn, Extras → Cheats lists the game's **cheat profiles**. "New Cheat Session" picks a source file and ticks its entries. (3) The launch runs RetroArch with that file and turns the ticked cheats on through RetroArch's network commands, checked afterwards. A cheat profile keeps **its own save slots**, apart from the clean game's. Files the user drops into the game's own user-content folder are **listed only** (Options → "Cheats / Mods: n / m"). They cannot be launched, on PS1 or anywhere. |
| **Extras → Mods** | Soft-patches (.ips / .bps / .ups / .xdelta) the user drops into the game's user-content folder, chosen per session ("New Mod Session"). **NES / SNES / Genesis only:** PS1's core (Beetle PSX HW) reports softpatching unsupported, so a PS1 game's Mods reads "unsupported". |
| **Extras → Start on disc…** | B74: a multi-disc PS1 set (.m3u) starts on disc 1 or on the disc picked. The host part is in the tree; the onn part is in the pinned APK, waiting for HOME-11. |

### In-game

| Feature | How it works today on PS1 / SNES |
|---|---|
| **Paused bar SAVE / LOAD / END** | PrivyHub's own save slots 1-3, through RetroArch's network commands. |
| **DISC** | B71 / B73 / B74: a multi-disc PS1 set only. The host's disc swap is on; the onn's button is in the pinned APK (HOME-11). |
| **The hold's return** | The adopted link-recovery line: a scratch state (slot 9) at 400 ms of controller silence, loaded at the release. B33 skips the load when there was no loss. This "state" method is the only rewind in use: RetroArch's own rewind keys are off, and the user has no rewind button. |
| **The stall resume / the give-up save** | The same scratch state on a stall; slot 8 on a link give-up → the recovery prompt. |
| **Hold-to-join** | "Hold any button to join" fills P1…Pn. PS1 relaunches into the multitap when a third player joins. |
| **Fast-forward / slow motion / screenshot / user rewind** | **None on any system.** Not on the bar; no hotkey sent. |

### Custom controls (what a PS1 game can remap today, and how)

| Feature | How it works today on PS1 / SNES |
|---|---|
| **Input Profile** | Options → **Input Profile**: named profiles, created and edited on the onn ("Create New Profile", "Edit Player n Mapping", "Assign to This Game"). Each one maps every button for players 1-4: the d-pad, A / B / X / Y, L / R / L2 / R2 / L3 / R3, Select / Start and both sticks' directions. A profile is assigned per game. At launch the hub writes the mapping into **RetroArch's launch config** for that session. On the hub: 4 profiles, assigned to 5 PS1 titles. |
| **Controller type** | Options → **Controller**: PS1 only, *PlayStation Controller* (digital) or *DualShock* per game, passed as RetroArch's device type at launch. SNES has one pad type and no such option. |

### Host-side per game

| Feature | How it works today on PS1 / SNES |
|---|---|
| **Multitap** | Options → **Multitap: On / Off**, PS1 only, per game (a core option merged at launch); since B46 / B54 it also follows the joined player count. |
| **Per-game core options / audio-video settings** | **None per game on any system.** Core options are per system (written at launch). The PS1 "look" (C5) is built, not adopted. |

---

## 2. The matrix

| # | Feature | N64 (RetroArch) | PS2 (PCSX2 2.8.2) | GameCube (Dolphin 2609b) |
|---|---|---|---|---|
| 1 | Box art on the tile | **missing** (G1) | **missing** (G1) | **missing** (G1) |
| 2 | Details line (region, year, genre, developer, publisher) | **missing** (G1) | **missing** (G1) | **missing** (G1) |
| 3 | Players from the database (and the Single / Multi views) | **missing** (G1); the override is present | **missing** (G1); the override is present | **missing** (G1); the override is present |
| 4 | " - <System>" in the mixed views | present | present | present |
| 5 | " · NEW" | **missing** (G7) | **missing** (G7) | **missing** (G7) |
| 6 | Favourites | present | present | present |
| 7 | Recently played / Continue view / play count | present (plays recorded on the hub) | present (plays recorded) | present (plays recorded) |
| 8 | Search | present | present | present |
| 9 | Start Fresh | present | present | present |
| 10 | Load Save | present (HOME-7) | present (B51 / B52, HOME-6) | present (B69, HOME-9) |
| 11 | Recovery prompt (Resume / Copy / Discard) | present (RetroArch's, as PS1's) | present (B55, slot 8 through PINE) | present (B69, Dolphin's hotkeys) |
| 12 | Extras → Cheats | **missing** (G3a) | **missing** (G3c) | **missing** (G3b) |
| 13 | Extras → Mods (SNES's soft-patches) | **missing** (G5a) | **missing** (G5b) | **missing** (G5c) |
| 14 | Extras → Start on disc… | impossible (cartridge) | **missing** (G6b) | **missing** (G6a) |
| 15 | Paused bar SAVE / LOAD / END | present | present | present |
| 16 | DISC on the paused bar | impossible (cartridge) | **missing** (G6b) | **missing** (G6a) |
| 17 | The hold's return | present | present (B55: PINE's slot 9) | present (B69: the hotkey slot 9) |
| 18 | The stall resume | present | present (B55) | present (B69) |
| 19 | Hold-to-join | present (four ports, no relaunch) | present (the multitap by the count, B57's relaunch) | present (four ports) |
| 20 | Custom controls: Input Profile | present (G2c: RetroArch's path runs on N64; not yet seen on an N64 title) | **missing** (G2a): the menu shows and does nothing | **missing** (G2b): the menu shows and does nothing |
| 21 | Controller type (PS1's Digital / DualShock) | impossible (one pad type) | impossible (DualShock 2 covers both) | impossible (one pad type) |
| 22 | Multitap per game | impossible (four ports built in) | present (automatic from the player count) | impossible (four ports built in) |
| 23 | Players override (Options → Players) | present | present | present |

**Counts (23 rows):**

| | present | missing | impossible |
|---|---|---|---|
| **N64** | 13 | 6 | 4 |
| **PS2** | 13 | 9 | 1 |
| **GameCube** | 12 | 9 | 2 |

**Found while reading. These are not on PS1 / SNES either, so they are not parity rows:**
- **Play time:** no system has it. PCSX2 and Dolphin each keep their own play time on the hub (their own files);
  PrivyHub shows neither.
- **Fast-forward, slow motion, screenshot, a user-held rewind:** no system has them.
- **Per-game core options and per-game audio-video settings:** no system has them.

---

## 3. The gaps: mechanism, source, privacy, size

### G1 — Artwork and the details line for N64 / PS2 / GameCube (rows 1-3)

- **Mechanism:**
  - add the three systems to the hub's **existing fetcher**: its system table (the database name and the system list
    to read) and a match by file name, as PS1 does. No hashing of large images on the drive;
  - the rest is today's path: the art cached on the hub by game id, the details' fields and players filled by the
    same records;
  - **the onn needs nothing:** it shows whatever box art and details the host gives.
  - The user's files already follow the database naming.
- **Source:** **RetroArch's databases.** The thumbnail sets are named (not queried here) as *Nintendo - Nintendo 64*,
  *Sony - PlayStation 2* and *Nintendo - GameCube*. The system lists are no-intro (N64) and redump (PS2, GameCube).
  The first run confirms each set.
- **Alternative source, GameCube only:** Dolphin 2609b's binary names GameTDB's cover server, keyed by the 6-character
  game id. PCSX2 has none (the user must supply a cover-URL template).
- **Privacy:** the same as today's PS1 fetch:
  - the system list is downloaded whole, so it sends nothing about the user's titles;
  - then one request per matched title, with the **database's title name** in the request, to RetroArch's thumbnail
    server.
  - A GameTDB fetch would send the **game id** instead (identifying in the same way).
- **Size:** **M** (one B item, host only; it runs at the next companion start like today's).
- **Note:** a picture placed by hand in the hub's box-art cache under the game's id already shows on any system today.

### G2 — Custom controls (row 20)

The onn's Input Profile editor and assignment already work for **every** title: Options shows "Input Profile" on PS2 and
GameCube games too. But the PCSX2 and Dolphin launches skip the step that applies it. **Today an assigned profile is
silently ignored on PS2 and GameCube.**

- **G2a, PS2:**
  - *Mechanism:* the hub already writes PCSX2's pad bindings at every launch (the four virtual pads, SDL, the
    DualShock 2 layout). A per-game profile = the assigned Input Profile translated into those bindings at launch.
    PCSX2's own per-game route also exists (a named input profile in its `inputprofiles/`, chosen by an
    `InputProfileName` line in the game's settings file), but writing the bindings directly needs no game identity.
  - *Source:* the user (the onn's editor).
  - *Privacy:* none (local).
  - *Size:* **M**.
- **G2b, GameCube:**
  - *Mechanism:* the hub writes Dolphin's pad config (`GCPadNew.ini`, four virtual pads) at every launch. A per-game
    profile = the assigned profile translated into those bindings at launch. Dolphin's own route also exists (a pad
    profile under its profiles folder, chosen per game by a `PadProfile<n>` line in the game's settings).
    The GameCube pad has fewer buttons (A / B / X / Y / Z / L / R / Start, the C-stick), so the translation needs a
    table.
  - *Source:* the user.
  - *Privacy:* none.
  - *Size:* **M**.
- **G2c, N64:**
  - *Present by the code:* the RetroArch launch applies the assigned profile on N64 as on PS1. It sits with B62's
    per-title layout (the C-buttons; the "face_c" / "core" choice, set in the hub's controller overrides with no onn
    menu).
  - *To do:* one look on the TV with an assigned profile.
  - *Size:* **S** (a check, no code).

### G3 — Cheats (row 12): the honest constraint

The cached index of RetroArch's cheat database, read from the hub's disk, **has a "Nintendo - Nintendo 64" folder and no
PlayStation 2 or GameCube folder**. So RetroArch's database covers N64 only. PS2 and GameCube need another source.

- **G3a, N64: fetch, as PS1.**
  - *Mechanism:* add N64 to the cheat fetcher's systems, then run the tool. The onn's Cheats menu, the cheat profiles
    with their own saves, and the toggles through RetroArch are all unchanged. The N64 core (Mupen64Plus-Next) carries
    cheat handling and its own code list (read from its file as data).
  - *Source:* RetroArch's cheat database.
  - *Privacy:* as PS1's. The folder listing sends nothing about the user's titles; each matched file's request
    carries the database's title name.
  - *Size:* **S** (a system line + the tool's run + one look on the TV).
- **G3b, GameCube: no fetch needed for many titles.**
  - *Source on the hub already:* **Dolphin 2609b ships its own per-game settings files (1,883 of them, GameCube and Wii
    together).** 852 have an Action Replay section and 168 a Gecko section, about 4,990 named codes in all, keyed by
    the game id (3- or 6-character). These are counted in memory from the AppImage, not extracted.
  - *Optional feed:* Dolphin's binary names a public code server that it downloads Gecko codes from by game id.
  - *Fallback:* a drop-in.
  - *Mechanism:*
    - the hub reads the game id from the disc header (or from Dolphin's log at the first launch);
    - it lists the codes for that id in the onn's existing Cheats menu, in the shape the menu already reads;
    - at launch it writes the user's per-game settings file with `[ActionReplay_Enabled]` / `[Gecko_Enabled]` lines
      for the ticked codes, and `EnableCheats = True` in Dolphin's config (False today).
    - The codes apply from the boot.
  - *Privacy:* the bundled codes send nothing; the code-server download would send the game id.
  - *Size:* **M** (host only, if the menu's shape holds).
- **G3c, PS2: a drop-in folder.**
  - *Constraint:* no feed exists in either database PrivyHub uses. PCSX2 2.8.2 names no cheat download. Its bundled
    `patches.zip` (4,709 files keyed by serial + CRC) holds widescreen, 60-fps and no-interlace patches, not cheats.
  - *Mechanism:*
    - the user drops `.pnach` files into a per-game folder that PrivyHub reads and shows in the Cheats menu (each
      `[group]` an entry, ticked like PS1's);
    - at launch the hub copies the ticked ones into PCSX2's `cheats/` as `<serial>_<CRC>.pnach` and sets
      `EnableCheats` (false today).
    - PCSX2 2.8.2 also loads `<serial>_*.pnach` when "show cheats for all CRCs" is on, so the serial alone can
      suffice.
    - The serial and CRC come from PCSX2's own log at the first launch: the hub already reads that log for the ELF
      line.
  - *Source:* the user (community `.pnach` collections exist on public git hosts; none is named or queried here).
  - *Privacy:* none (local).
  - *Size:* **M ×2** (the game identity, then the cheats).
- **A drop-in for every system:** PS1's own cheat folder is list-only today. One drop-in route (G3c's) could also make
  user-supplied `.cht` files launchable on PS1 / SNES / N64.

### G5 — Mods (row 13; SNES has them, PS1 does not)

- **G5a, N64:**
  - *Mechanism:* RetroArch's soft-patch flags on the launch, or PrivyHub's own IPS-to-a-derived-copy path (it exists
    for IPS; N64 images are small).
  - *Source:* the user (the game's user-content folder, as SNES).
  - *Privacy:* none.
  - *Size:* **M**.
- **G5b, PS2:**
  - *Mechanism:* PCSX2's patches. The bundled widescreen / 60-fps / no-interlace patches are **on the hub already,
    off** (`EnableWideScreenPatches = false`), plus user `.pnach` patches in its `patches/`.
  - *Source:* PCSX2's bundle / the user.
  - *Privacy:* none.
  - *Size:* **S** (widescreen as a per-game line at launch) to **M** (a Mods list).
- **G5c, GameCube:**
  - *Mechanism:* Dolphin's texture packs and graphics mods (its `Load/` folders, per game id).
  - *Source:* the user.
  - *Privacy:* none.
  - *Size:* **M**.

### G6 — Multi-disc (rows 14, 16)

- **G6a, GameCube:**
  - *Mechanism:* Dolphin 2609b opens `.m3u` playlists and has "Change Discs Automatically" (`AutoDiscChange`). With
    both, the game's own disc prompt is answered by Dolphin.
  - *To do:* list a `.m3u` as one title (the in-place listing takes `.rvz` / `.gcm` / `.iso` / `.ciso` today) and set
    the line at launch.
  - *Size:* **S-M**.
- **G6b, PS2:**
  - *Constraint:* PCSX2 2.8.2 has a "Change Disc" action (menu / fullscreen UI) and no playlist. Whether it can be
    reached from outside (a hotkey) is to be read at build time.
  - *Size:* **M-L**.
  - Multi-disc PS2 titles are rare.

### G7 — "NEW" (row 5)

- *Mechanism:* a "first seen" mark for in-place titles (they are never imported), on the same 7-day rule.
- *Constraint:* the tag is off on **every** system today (its flag is not adopted).
- *Size:* **M**, and only if the user wants the tag at all.

---

## 4. The reading for the user, in plain words

**Artwork.** Your PS1 and SNES pictures come from the hub's own fetcher. It asks RetroArch's picture library for each
title by its name, at companion start. That fetcher knows only NES, SNES, Genesis and PS1, which is why N64, PS2 and
GameCube show no box art and no genre / year / players. RetroArch's library has sets for all three. Adding them is
one host item. The onn needs no update. The fetch sends the same thing as today: each title's name.

**Custom controls.** On PS1 you make Input Profiles on the onn and assign one per game. That already works on N64 by the
code (one look on the TV to confirm). On PS2 and GameCube the menu shows, but the emulator never receives the profile.
The hub writes both emulators' pad settings at every launch already, so wiring your assigned profile in is one host
item each. No fetch is involved.

**Cheats.** You were right that PS1's cheats came through RetroArch: the hub downloaded them from RetroArch's cheat
database. That database covers **N64** (so N64 works the same way, a small step) but has **no PS2 and no GameCube
folder**. The honest picture:
- **GameCube** is better off than expected. Dolphin comes with thousands of codes for GameCube and Wii games built
  in, already on the hub, keyed by the game's id. PrivyHub can list them in the same Cheats menu with no download.
  Dolphin can also download more codes by game id if you want that.
- **PS2** has no database PrivyHub can use. You would drop `.pnach` cheat files into a folder per game, and PrivyHub
  shows them in the Cheats menu like PS1's and turns on the ones you tick.

**Everything else:**
- Favourites, recently played, Continue, Start Fresh / Load Save, SAVE / LOAD / END, the hold, the stall recovery and
  hold-to-join already match on all three.
- The gaps besides the three you named: Mods (SNES-style patches; PS2's widescreen patches are already on the hub,
  switched off), the disc change on GameCube (Dolphin can swap discs itself), and the "NEW" tag (off everywhere today).
- No system has play time, fast-forward, screenshots or a rewind button, so those are not parity gaps.

## 5. A suggested order (a suggestion, cheapest and most visible first; the user ranks)

1. **Artwork + details for N64 / PS2 / GameCube**: G1, M, host only. It changes every tile.
2. **Custom controls**: the N64 look (G2c, S); then PS2 (G2a, M) and GameCube (G2b, M).
3. **Cheats**: N64 (G3a, S); then GameCube from Dolphin's bundled codes (G3b, M); then the PS2 drop-in (G3c, M ×2).
4. After those, if wanted: PS2 widescreen (G5b, S), the GameCube disc change (G6a, S-M), the other Mods (G5a / G5c, M),
   the PS2 disc change (G6b), "NEW" (G7).

## 6. The one question per gap that needs the user's word

- **G1 (artwork):** may the hub fetch N64 / PS2 / GameCube box art and details from RetroArch's library as it does for
  PS1 (each title's name is sent)?
- **G2 (custom controls):** should PS2 and GameCube use the **same** Input Profiles you already made (one profile,
  translated per system), or separate profiles per system?
- **G3a (N64 cheats):** fetch N64 cheats from RetroArch's database as PS1's were (each matched title's name is sent)?
- **G3b (GameCube cheats):** Dolphin's built-in codes only (no download), or also allow Dolphin's code download (the
  game's id is sent)?
- **G3c (PS2 cheats):** is a drop-in folder per game, where you supply the `.pnach` files, acceptable? And should the same
  drop-in make your own `.cht` files launchable on PS1 / SNES (today they are only listed)?
- **G5 (mods):** do you want PS2's widescreen patches (already on the hub) offered per game, and Mods on N64 / GameCube
  at all?
- **G6 (multi-disc):** does any GameCube or PS2 title you play span two discs?
- **G7 ("NEW"):** do you want the "NEW" tag at all (it is off on every system today)?
