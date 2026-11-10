# SESSION B — done, 2026-11-09 AC (QUEUE_2026-11-09AC: B76-B81, the first H6 parity queue; the PS2 disc change designed; run 23:17-23:55Z)

- **Baseline:** `a96c816c` (HOME-11 committed).
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files
  tracked and unchanged).
- **Not done:**
  - nothing committed, adopted or installed; no drop-in written; no companion or keeper restart; no stream, no adb, no
    sudo, no nft;
  - `privyhub-diag` and `~/privyhub_diag/` untouched;
  - **no emulator started.** PCSX2's and Dolphin's AppImages were read with `7z` into memory (strings, the bundled
    `patches.zip` and `GameSettings/`), the drive's GameCube disc headers read (0x8100 bytes each), PCSX2's kept logs
    read — counts only printed, no id, serial, title or code name;
  - **nothing fetched** (B76's and B78's tests use fixture catalogs / indexes behind fakes); nothing written to the
    drive; nothing of A's touched; nothing deleted; **no folder or file created in the hub's `data/`** (the drop-in
    folders appear at A's first Cheats list after the restart).

## What was built (six diffs applied to the tree in order, uncommitted)

| Item | What | Knob (absent / `0` = today) | Tests ×3 | Mutations |
| --- | --- | --- | --- | --- |
| **B76** | N64 / PS2 / GameCube in the hub's art + details fetcher (RetroArch's names; matched by file name; details as PS1's; cache per system); `--dry-run` (counts per system, misses as labels, nothing per title) | `PRIVYHUB_ART_SYSTEMS=1` (opt-in) | 20 | 7 / 7 |
| **B77** | the assigned Input Profile onto PCSX2's `[PadN]` and Dolphin's `GCPadNew.ini` (B69's map = the identity; Default = today's files); N64's path confirmed | `PRIVYHUB_PROFILES_EXT=0` | 17 | 8 / 9 (1 equivalent) |
| **B78** | N64 in the cheat tool and the launch (Mupen64Plus-Next), the rest PS1's | inside `PRIVYHUB_N64=1`; `PRIVYHUB_N64_CHEATS=0` | 8 | 6 / 6 |
| **B79** | GameCube: disc id → Dolphin's bundled code names in Extras → Cheats; the ticked ones written per launch; `GC cheats: n enabled`; no download | inside `PRIVYHUB_GAMECUBE=1`; `PRIVYHUB_GC_CHEATS=0` | 14 | 9 / 9 |
| **B80** | PS2 widescreen / no-interlacing / 60-fps from PCSX2's bundle per title: Extras → "Patches…" (client), remembered on the hub, the game's settings file per launch; `PS2 patches: …` | inside `PRIVYHUB_PS2=1`; `PRIVYHUB_PS2_PATCHES=0`; `debug.privyhub.ps2_patches=0` | 15 + JVM 5 | 8 / 8 + JVM 3 / 3 |
| **B81** | the drop-in folders: PS2 `.pnach` per serial; the user's `.cht` on PS1 / SNES launchable; `docs/CHEATS.md` | `PRIVYHUB_CHEAT_DROPINS=0` | 15 | 10 / 10 |

- **Read on the hub (counts only):** GameCube — 26 disc ids, **16 titles with Dolphin codes, 540 codes**; PS2 — 115
  titles, **5 seen in PCSX2's logs, 4 with a bundled patch** (widescreen 4, no interlacing 1, 60 fps 1).
- **The tree checks:** HEAD + the six diffs in order = the tree; reversed → HEAD. Every host suite on full exports of
  HEAD and of HEAD + B76 … B81: the 72 shared suites read the same; `tests/art_systems` (89) new and green; the same
  six `tools/` suites fail in both, as queue AA's (fixtures under `docs/` / `logs/`).
- **Designed only:** `docs/memory/architecture/H6_PS2_DISC_CHANGE_DESIGN_2026-11-09.md` — PINE has no disc message,
  every PCSX2 2.8.2 change-disc path ends in a GUI chooser, a state carried across discs is unsafe → **a relaunch on
  the next disc with the memory card carrying the game** (size M). One complete two-disc PS2 set on the drive.
  GameCube deferred.

**The APK `de6682dbaf00237c2f6477b68df4fa00e320c0a403ccb2d28863344dee86de28`:**
- contents: B5 … + B54 + B67 + B70 + B71 + B72 (a) + B73 + B74 + **B80's client part**; B27 / B29 out (B77 / B79 /
  B81 have no client part);
- built offline with `--no-configuration-cache`, twice → the same bytes; the baseline rebuilds `85220f99…` byte for
  byte; the same signer (`455bde4e…`);
- JVM 265 / 265 in the APK tree (276 / 276 in the working copy);
- pinned at `PrivyHub/app/build/queue_ac_built/app-debug.apk`, **NOT installed**.

**Disclosed (details in the records):**
- **B81 deviates from its hashed design:** the drop-in folders are made at the first Cheats list, not in the plugin's
  constructor (another suite constructs the plugin by importing the package).
- B80's diff carries a one-line fix to B79's `read_bundled` default (same behaviour).
- The mutation runner gained a copy of `docs/CHEATS.md` at B81 (B76-B80's runs predate it and did not need it).
- **Today's cheat tool, kept with B78's knob 0:** with N64 records present and `PRIVYHUB_N64=1` in its environment it
  stops at the first N64 title.
- A PS2 / GameCube cheat session saves into the title's own slots and memory card; a PS2 title's patches and cheat
  files show after its first PrivyHub launch; B77 adds one game-log line per PS2 / GameCube launch.

**One line for the user:**
- N64, PS2 and GameCube can get box art and details the same way PS1 did — the hub asks first (counts only), then
  fetches on your word;
- your Input Profiles now work on PS2 and GameCube games too;
- N64 cheats come from RetroArch's list like PS1's; GameCube cheats come from Dolphin's own built-in codes (16 of your
  GameCube games have some), with nothing downloaded;
- PS2 games that have a widescreen (or 60-fps) fix get a "Patches…" entry under Extras once you've played them once;
- you can drop your own PS2 cheat files, and your own PS1 / SNES cheat files, into folders on the hub —
  `docs/CHEATS.md` says where.

## A — ART-1 (unattended, no TV; outside 04:30-05:30Z)

1. **Preconditions:**
   - HEAD with queue AC committed and the tree clean. If B76-B81's files are uncommitted, stop with "YOU, now: commit
     queue AC first, then send the read line again";
   - `/tmp` ≥ 1 GB free (run the tools with `TMPDIR` on the main disk);
   - **eighteen** `PRIVYHUB_` lines (queue AC adds none); `--check` ok; `85220f99…` CONFIRMED on the onn; only the two
     units.
2. **The companion restart** (B77-B81's host parts live; nothing adopted, no drop-in): `systemctl --user restart
   privyhub-companion`. Then eighteen lines, `--check` ok, the journal clean, the systems' counts as before; the
   keeper not restarted.
3. **The dry run** — the tool with the companion's own `PRIVYHUB_` environment (from its drop-ins) **plus
   `PRIVYHUB_ART_SYSTEMS=1`, in that command only**:
   `tools/update_game_metadata.py --dry-run --json` (per system: matched / ambiguous / no match / list unavailable;
   the misses as labels). **Disclose in the reply:** this step downloads RetroArch's three whole system lists (one
   file per system, cached per system); nothing about the titles is sent. Record the counts and the labels only.
4. **Reply:** "YOU, now: box art and details — N64 a of b titles found in RetroArch's library, PS2 c of d, GameCube
   e of f (the rest are listed as labels). Fetching sends each found title's name to RetroArch's picture server, as
   for PS1, and also fetches the N64 cheat lists the same way. Send 'fetch' to go ahead, or 'skip'."
5. **On "fetch"** (the same environment, `PRIVYHUB_ART_SYSTEMS=1` in the command only):
   - `tools/update_game_metadata.py --system n64`, then `--system ps2`, then `--system gamecube`;
   - then `PRIVYHUB_N64=1 tools/update_game_cheats.py --system n64 --no-download` (the report), then without
     `--no-download`;
   - read back: the art downloaded / cached / missing per system; one title's `details` per system (by label: year,
     genre, players, `box_art_available`); the N64 titles with cheats (count);
   - **the cache populated**: `provider_cache/libretro/<n64|ps2|gamecube>/` present; box-art files counted.
   - Nothing else is sent; no title in any record (labels and counts).
6. **The record:** `evidence/ART_1_<date>.md` + dir (the counts, the labels, the commands, the restart's checks).

## A — HOME-12 (~30 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (read back empty at the start and the close): **eighteen** = HOME-11's seventeen +
`debug.privyhub.ps2_patches`.

**T-labels:** ART-1's; one N64, one PS2 and one GameCube title chosen by A for each cell (by label), each with what
the cell needs (art; a cheat with a visible effect; a PS2 title with a widescreen patch — one of the 4 already
played).

### Stage 1 — unattended

1. **Preconditions:** ART-1 done (or the user's "skip": then C44 is not run); the companion restarted with queue AC
   (ART-1 step 2).
2. **The install:** preserve `85220f99…` in `home12_previous/`; copy `queue_ac_built/app-debug.apk` to
   `home12_installed/`; `adb install -r`; read back **`de6682dbaf00237c2f6477b68df4fa00e320c0a403ccb2d28863344dee86de28`**,
   paired; **every property empty (eighteen)**. adb is for the install and state reads only; no setprop.
3. **Pre-register** C44-C48, hashed: the rows below, the validity rules, the CONFIRMED rule.
4. **Reply:** "YOU, now: open Games → N64 and look at a few titles. Tell me whether they show box art, and open one
   title's details: does it show a year, a genre and the number of players? Then do the same in PlayStation 2 and
   GameCube. Send 'Stage 2'."

### C44 — box art and details on N64 / PS2 / GameCube

- **You should see:** box art on the found titles; in the details a year, a genre, players (as PS1's).
- **Hub:** the details' fields for the T-labels; `box_art_available` true.
- **Met:** the user's line, per system.
- **Reply:** "YOU, now: pick the PS2 game I name (T-label's words), press Options → Input Profile → Create New Profile,
  call it Swap, Edit Player 1 Mapping and swap the bottom and the right face buttons, save, then Assign to This Game.
  Start it (Launch on Companion → Start Fresh) and press the bottom button where the game expects the right one:
  does it act as the right one? END. Do the same on the GameCube game I name (Assign the same Swap profile). Then
  start any other PS2 game: do its buttons work as normal? Send 'Stage 3'."

### C45 — an Input Profile with a swap on PS2 and GameCube

- **You should see:** the swapped button acts swapped on both; another game unchanged.
- **Hub:** the game logs `PS2 input profile: assigned overrides=1` / `GC input profile: assigned overrides=1`; the
  other game `default overrides=0`; PCSX2's `[Pad1]` Cross / Circle and `GCPadNew.ini` `GCPad1` A / X swapped (the
  binding names only).
- **Met:** the user's line on both, and the unchanged game.
- **Reply:** "YOU, now: on the N64 game I name, press Launch on Companion → Extras → Cheats → New Cheat Session, tick
  the cheat I name (something you can see, like infinite lives), and Launch Cheat Session. Tell me whether you see it
  work. END. Send 'Stage 4'."

### C46 — an N64 cheat seen in-game

- **Hub:** the staged file under `cheat_runtime/Mupen64Plus-Next/`; RetroArch's cheat toggles checked (PS1's
  verification); then **the drop-in folders** `data/games/retroarch/cheats/ps1`, `…/snes`, `data/games/ps2/cheats`
  read **present and empty** (they appear at the first Cheats list).
- **Met:** the user's line (the visible effect).
- **Reply:** "YOU, now: the same on the GameCube game I name: Extras → Cheats → New Cheat Session, tick the one I name,
  Launch Cheat Session. Tell me whether it works. END. Send 'Stage 5'."

### C47 — a GameCube cheat from Dolphin's list, seen

- **Hub:** `GC cheats: 1 enabled` in the game log; the user dir's `GameSettings/<id>.ini` written (its section names
  only); `Dolphin.ini` `EnableCheats = True` for that launch, `False` at the next plain launch.
- **Met:** the user's line.
- **Reply:** "YOU, now: on the PS2 game I name, press Launch on Companion → Extras → Patches…, tick Widescreen, Save.
  Then Start Fresh and tell me whether the picture fills the TV from side to side (it was narrower before). END."

### C48 — PS2 widescreen on a title that has it

- **Hub:** the details' `ps2_patches` for the label; the game log `PS2 patches: ws=on …`; the game's settings file's
  `EnableWideScreenPatches = true` (the key only).
- **Met:** the user's line (the picture fills the TV). A note if a 60 fps toggle exists on that title (offered, not
  scored).
- **Reply (the close):** "YOU, now: that's all, thank you. Your own cheat folders are ready and empty — docs/CHEATS.md
  says where to put files when you find them. I'll tidy up on the hub."

### The close

- **Every property empty** (eighteen); nothing running; the drive before = after.
- **The CONFIRMED rule for `de6682db…`:** C44-C48 valid and met with every property empty (C44 skipped only on the
  user's 'skip' at ART-1; C48 is the APK's own cell) → **`de6682db…` CONFIRMED**; the pin moves in the three places
  (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test; green; the patch
  notes indexed). Otherwise `85220f99…` is reinstalled from `home12_previous/`, read back, paired, and the user told
  why.
- **The verdicts:** C44 → B76; C45 → B77; C46 → B78; C47 → B79; C48 → B80; the folders → B81.
- **The record:** `evidence/HOME_12_<date>.md` + dir: the cells, the user's lines verbatim, T-labels. No title, serial,
  game id, code name or path.
- Then KNOWN_ISSUES insertions, the ROADMAP §H6 lines, CURRENT.md, `logs/home12_git_status.txt`; nothing committed.

## Files

- **Records:** `evidence/B76_ART_THREE_SYSTEMS_2026-11-09.md`, `B77_PROFILES_PS2_GC_…`, `B78_N64_CHEATS_…`,
  `B79_GC_CHEATS_…`, `B80_PS2_PATCHES_…`, `B81_CHEAT_DROPINS_…`, each with its dir (the design + hash, the diff, the
  proof, tests, mutations, redact / title checks, the manifest); the APK's files in `b80_2026-11-09/`, the queue's
  tree checks in `b81_2026-11-09/`.
- **Design:** `docs/memory/architecture/H6_PS2_DISC_CHANGE_DESIGN_2026-11-09.md`. **User guide:** `docs/CHEATS.md`.
- **Patch notes:** `patches/B76_ART_THREE_SYSTEMS.md` … `B81_CHEAT_DROPINS.md` (not indexed: nothing adopted).
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue AC line and section); `docs/ROADMAP.md` (§H6 in full;
  B75's status line kept below it).
- **Logs:** `logs/b76_git_status.txt` … `logs/b81_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q19ac_base`, `_after_b76` … `_after_b81` (companion/, tools/, tests/, PrivyHub/),
  `/tmp/b_q19ac_work`, `/tmp/b_q19ac_apk`, `/tmp/b_q19ac_apko` (PrivyHub/ only) with their build outputs;
  `~/.cache/b_q19ac_tmp/` (the runs' outputs, the three APK builds, the host suites' `logs/` and the `docs/CHEATS.md`
  copy moved out of the copies after their runs, and the older suites' own temp dirs, which they do not remove).
  `tests/art_systems` leaves no temp dir.
