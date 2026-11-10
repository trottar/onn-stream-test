# Cheats — where they come from, and how to add your own

PrivyHub shows cheats on the TV under a game's **Launch on Companion → Extras → Cheats**. You tick the ones you want
and press **Launch Cheat Session**. The game then starts with those cheats on. A normal start (Start Fresh / Load
Save) never has cheats on.

## Where the cheats come from, by system

| System | Where the list comes from | Anything downloaded? |
| --- | --- | --- |
| PlayStation, SNES, NES, Genesis | RetroArch's cheat collection, fetched by the hub when someone runs the cheat update | yes, when the update runs (each game's name is sent) |
| N64 | the same RetroArch collection | yes, the same way |
| GameCube | the codes that come with Dolphin, already on the hub | **no** |
| PlayStation 2 | **your own files only** (below) | **no** |
| PlayStation, SNES | **also your own files** (below), listed after RetroArch's | **no** |

The hub never downloads anything for your own files. It only reads the folders below.

## Picking cheats on the TV

On a game, press **Launch on Companion → Extras → Cheats → New Cheat Session**. The cheat list opens on its own screen:

- **"Launch Cheat Session" and "Cancel" are always at the top.** From anywhere in the list, press **Left** to jump to
  Launch, then **OK** to start. On a game pad, **Start** launches straight away and **Back** (or B) cancels.
- **The list is split into sections:** General, Player 1, Player 2, Player 3, Player 4, Other and Your files. Each
  section starts closed with the number of cheats in it — press **OK** on a section to open or close it.
- **To find a cheat by name,** go up to the filter line, press **OK** and type a word or two (for example "lives"):
  the list shows only the cheats with those words. On the filter line, press **Right** to show only the cheats you
  have ticked.
- **To move faster,** the shoulder buttons (L1 / R1) or the remote's channel buttons jump a screen at a time.
- **OK on a cheat** ticks or unticks it. "n selected" at the top counts your ticks.

The hub tidies the lists before they reach the TV. Cheats that do nothing on their own (a cheat cartridge's button
triggers) are left out. "Must be on" codes are switched on for you whenever you pick any cheat. "P1" is written
"Player 1". A cheat split into parts ("Part 1", "Part 2") shows once. When a list has the same name more than once with
different codes, the others appear under the first as "variant 2", "variant 3" — they usually do the same thing for
another character, player or slot, so try the first one, then a variant if it doesn't work. Your own files are shown
exactly as you wrote them.

## Your own PlayStation 2 cheats (`.pnach` files)

1. Find the game's **serial**. It looks like `SLUS-12345` (four letters, a dash, five numbers). PCSX2 shows it, and so
   do most cheat sites.
2. Put your `.pnach` files in a folder named after that serial, inside the hub's PS2 cheat folder:

   `data/games/ps2/cheats/SLUS-12345/`

   (the `data/games/ps2/cheats/` folder appears by itself the first time the TV opens a Cheats list). If you
   prefer a folder of your own, add a line `PS2_CHEATS_DIR=<your folder>` to the hub's paths file; the serial folders
   then go inside your folder.
3. On the TV, each file shows as one entry, by its file name. Tick the files you want.

**Note:** the hub learns a PS2 game's serial from PCSX2 the first time the game is played through PrivyHub. Until
then, its Cheats list is empty. Play it once (a minute is enough), and the files show from then on.

The ticked files are joined into one cheat file for PCSX2, just for that game. Cheats inside a file that has a name in
square brackets (`[Infinite Health]`) are switched on by that name; lines without a name are always on.

## Your own PlayStation and SNES cheats (`.cht` files)

1. Use RetroArch's cheat file format (`.cht`), the same as the files RetroArch's collection has.
2. Put them in a folder named after the **game's file name without its ending**, inside:

   `data/games/retroarch/cheats/ps1/` for PlayStation, or `data/games/retroarch/cheats/snes/` for SNES.

   For a game file called `My Game (USA).chd`, the folder is
   `data/games/retroarch/cheats/ps1/My Game (USA)/`.
3. On the TV, your files show after RetroArch's in the Cheats list, each with its own cheats to tick, as usual.

**Every cheat in your file must start switched off** (`cheat0_enable = false`, and so on). The TV switches on only
the ones you tick. A file with a cheat already switched on is left out of the list.

## Good to know

- A PS2 or GameCube cheat session saves into the game's normal save slots and memory card. PlayStation and SNES
  cheat sessions keep their own save slots, as before.
- To stop using cheats, start the game normally (Start Fresh or Load Save).
- To switch this off on the hub: `PRIVYHUB_CHEAT_DROPINS=0` (your own files), `PRIVYHUB_GC_CHEATS=0` (GameCube),
  `PRIVYHUB_N64_CHEATS=0` (N64).
