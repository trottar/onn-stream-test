# Importing games from a USB stick or a folder

PrivyHub can copy games into the hub's game library from a USB stick, or straight from a folder such as the external
drive's games folders. It takes **PlayStation (PS1)** games and a PS1 BIOS, and **SNES**, **NES** and **Genesis**
games. The tool is `tools/import_usb.py`. It only reads the stick or the folder. It never deletes or changes anything
there, and it never replaces a file that is already in the library.

**PS2 games stay on the external drive and are listed from there.** They are not copied to the hub. If the tool sees
a PS2 folder, it says so and leaves it alone. N64 and GameCube folders are not supported yet: the tool lists them and
copies nothing.

It runs only when `PRIVYHUB_IMPORT=1` is set. Without that, every command stops with a message and does nothing.

## 1. Put the files on the stick

Make one folder called `PrivyHub-Import` at the top of the stick, laid out like this:

```text
PrivyHub-Import/
    games/
        ps1/
            Some Game.chd                    one file = one game
            Another Game/                    a game made of a .cue and its .bin tracks
                Another Game.cue
                Another Game (Track 1).bin
                Another Game (Track 2).bin
            Big Game/                        a game on several discs
                Big Game (Disc 1).chd
                Big Game (Disc 2).chd
    bios/
        ps1/
            scph5501.bin                     your own console's BIOS (scph5500 / 5501 / 5502)
```

The other systems go in their own folders next to `ps1/`, one file per game:

```text
PrivyHub-Import/
    games/
        snes/       Some Game.sfc   (or .smc)
        nes/        Some Game.nes
        genesis/    Some Game.md    (or .gen, or .bin)
```

- **SNES:** `.sfc` or `.smc`. A file with the old 512-byte copier header at the front is fine.
- **NES:** `.nes` files with the usual header.
- **Genesis:** `.md`, `.gen` or `.bin`.
- The tool checks each file's header. A file that does not look like a game for that system is not imported, and the
  tool says why. Zipped games are not imported: unzip them first.

- **Formats that work:** `.chd`, and `.cue` with its `.bin` tracks.
- **Several discs:** name each one `(Disc 1)`, `(Disc 2)` and so on, and keep them in one folder. The hub makes the
  playlist (`.m3u`) itself, so the game shows up once in the list. You can also bring your own `.m3u`.
- **Not imported:** an `.iso` (it does not start on this hub; if a `.chd` of the same game is there, the `.iso` is
  simply skipped), a `.pbp`, a `.bin` without its `.cue`, and any other kind of file. The tool tells you why for each
  one.
- Everything else on the stick is ignored.

## 2. The three commands

Run these at the hub, in the PrivyHub folder. Replace `/media/<you>/<stick>` with where the stick is mounted.

1. **Look:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py inspect /media/<you>/<stick>`
   - It lists what it found as `T1`, `T2`, … with the kind of game and the number of files, what it will not take
     and why, and whether there is a BIOS on the stick and in the hub.
   - Nothing is copied, and nothing is written anywhere.
2. **Plan:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py plan /media/<you>/<stick>`
   - It checks every file (its type, its header, a fingerprint of its contents).
   - It finds games you already have, even under another name, and skips them.
   - It checks there is enough space, and shows for each game `ACCEPT`, `DUPLICATE` or `REJECT` with the reason.
   - Add `--names` to see the game names next to the labels.
   - The plan is saved on the hub under `data/import/plans/`. Still nothing is copied.
3. **Import:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py apply`
   - It copies exactly what the last plan accepted, and only if those files have not changed since the plan.
   - It refuses while a game is being played.
   - Each game is copied under a hidden temporary name, checked, and only then put in place; the file you launch goes
     in last. If anything goes wrong halfway, that game's copied files are removed again, so you never get a half
     game.
   - Afterwards, `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py verify` re-checks every copied file.

Run `plan` again after an import: everything you just imported shows as a duplicate, and nothing is copied twice.

### From a folder instead of a stick

If the games are already in a folder, for example the external drive's `games/snes/`, point the tool at that folder.
Say which system it holds. No `PrivyHub-Import` folder and no links are needed:

```text
PRIVYHUB_IMPORT=1 python3 tools/import_usb.py inspect --source <the folder> --system snes
PRIVYHUB_IMPORT=1 python3 tools/import_usb.py plan --source <the folder> --system snes
PRIVYHUB_IMPORT=1 python3 tools/import_usb.py apply
```

- `--system` is one of `ps1`, `snes`, `nes` or `genesis`. Use one folder per system: run it again with the next
  folder.
- It works exactly like the stick, on the same files, with the same checks and the same duplicates. The folder is only
  read.
- A BIOS comes only from a stick's `bios/ps1/` folder.
- `--system ps2` only says that PS2 games stay on the drive. Nothing is planned.
- The hub's own library folder cannot be the source.

### If an import is interrupted

If the hub loses power or crashes in the middle of `apply`, nothing is left half-done for good:

- The game being copied is not shown in the list (while the import tool's setting is on for the companion).
- The next `apply` first removes what that game had copied so far.
- If the plan still includes that game, the next `apply` copies it again from the start. Games that were already
  complete are not copied twice.
- `inspect` and `plan` tell you when an interrupted import is waiting to be cleaned up.

## 3. What you see on the TV

- A new game appears in its system (**Games → PlayStation**, **SNES**, **NES** or **Genesis**) within a few seconds,
  with **"· NEW"** after its name for 7 days.
- If your library has an `.iso` and a `.chd` of the same PS1 game, the `.iso` is hidden, so the game appears once.
  For the other systems a game is never added twice, even in another format.
- Until a real BIOS is imported, the system reads **"PlayStation (OpenBIOS)"**. That means the games run on the
  emulator's own built-in BIOS. After a real BIOS is imported, it reads "PlayStation".

## 4. About the BIOS

- The BIOS is copied into the PS1 emulator's own BIOS folder on the hub. It is never put in a record or in the
  project's history.
- An existing BIOS file is never replaced.
- **A real BIOS changes how every PS1 game starts.** A save state (Game State → Save) made before the BIOS was
  imported may not load afterwards. Your in-game memory-card saves are not affected.

## 5. What the log shows

Each run writes a log under `data/import/logs/` on the hub. It holds only labels (`T1`, `T2`, …) and counts:

- the system and kind of each game, and how many files and bytes it has;
- whether it was accepted, a duplicate, or rejected, as a short code;
- whether it was placed;
- the BIOS as a region (JP / US / EU);
- the totals;
- whether an interrupted import was cleaned up or resumed.

It never contains a file name, a game title, a folder, a fingerprint, or where the stick was mounted. The names are
only in the saved plan on the hub, which is yours and is never shared.
