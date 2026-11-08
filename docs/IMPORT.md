# Importing PS1 games from a USB stick

PrivyHub can copy PlayStation (PS1) games, and a PS1 BIOS, from a USB stick into the hub's game library. The tool is
`tools/import_usb.py`. It only reads the stick. It never deletes or changes anything on it, and it never replaces a
file that is already in the library.

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

## 3. What you see on the TV

- A new game appears in **Games → PlayStation** within a few seconds, with **"· NEW"** after its name for 7 days.
- If your library has an `.iso` and a `.chd` of the same game, the `.iso` is hidden, so the game appears once.
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

- the kind of each game and how many files and bytes it has;
- whether it was accepted, a duplicate, or rejected, as a short code;
- whether it was placed;
- the BIOS as a region (JP / US / EU);
- the totals.

It never contains a file name, a game title, a folder, a fingerprint, or where the stick was mounted. The names are
only in the saved plan on the hub, which is yours and is never shared.
