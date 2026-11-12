---
memory_schema: 1
as_of: 2026-11-12
status: REFERENCE — the PC side's hand-back for PrivyParty (written on the PC side 2026-11-12; pasted to Cowork by the user the same day and filed here unchanged, below the line), with Cowork's note on what was set up on the hub by the user's own hand on 2026-11-12. Nothing in it has been run on the hub. No address, title or identifier
---

# PrivyParty — the PC side's hand-back, and where things are on the hub

## Cowork's note (2026-11-12) — what the user set up on the hub by hand, and what is agreed

- **The repo is on the hub** at `~/Projects/privyparty` (beside this repo, separate from it), cloned from a bare copy at `~/git/privyparty.git` that the user pushed to straight from the PC over the existing SSH connection (the PC's remote for it is named `hub`). Updating: `git push hub` on the PC, then `git -C ~/Projects/privyparty pull` on the hub. The repo's hosted address is in no file.
- **The owner's pictures are on the hub's own disk** at `~/privyparty_content/private` (about 15 MB; outside both repos; never in git), copied from the PC by the user. The game is pointed at it with `--content=` or the `PRIVYPARTY_CONTENT` setting. The external drive was not used for this (it is mounted read-only as a whole; the user chose the hub's disk — "Perhaps just put directly on hub").
- **The user's go for the hub probe's two downloads, in the user's words:** asked "Do I have your go for the Godot and repo downloads when we reach step 1?" — **"Yes you have my permission when step 1 is reached"**. The repo is already on the hub; **Godot 4.7.2-stable (the standard build) is still to be fetched**, by session A in the probe task, checked against its published checksum.
- **The order agreed for the hub side:** (1) a probe with no stream — Godot, the 25 scripted checks, the game on the hub's display, frame rate and load for both renderers; (2) a streamed probe — the virtual pads as Godot's devices 0-3, pause and quit from the onn, capture and sound, the encoder's cost; (3) the adapter — a mini-game script behind the seam `play(players) -> scores` that calls the hub's start and result (B103) and returns the winner; (4) switching the stream between the board's window and the emulator's window, which neither side has yet.
- **For the hub's launch kind:** close the game with its `quit` action (F10), never SIGTERM (no game code runs on it).

---

# PrivyParty: hand-back to the hub side

Written 2026-11-12, when the PC-side prototype was judged about ready to hand over. It answers the list at the
end of the kickoff brief (`PRIVYPARTY_PC_KICKOFF_BRIEF_2026-11-10.md`, "What to hand back when the hub side
starts") and adds what the hub side will want to know before it runs the game. The README has the detail;
this is the short way in.

Nothing here has been run on the hub. Every "works" below means: on the PC, and in the scripted checks.

## The six things the brief asked for

1. **The repo's address.** Not written in any file (no addresses in this repo). The repo is its own git repo,
   separate from the PrivyHub repo; the owner says where it is when the hub side starts.
2. **The exact Godot version.** 4.7.2-stable, the standard build (not .NET). Scripts are GDScript. The PC and
   the hub must use the same version (README, "Tools").
3. **The input actions.**
   - In Godot's input map (`project.godot`), each a single action: `pause` (Esc, P, Start on any pad) and
     `quit` (F10).
   - Per player, sent with the player's number and not in the input map: `confirm`, `back`, `map`, `up`,
     `down`, `left`, `right`. On a pad: A, B, Y, the d-pad or the left stick. Pads are Godot joypad devices 0
     to 3; there are four keyboard seats for a PC with no pads (README, "Controls").
   - Joining is press-and-hold: any button for half a second joins as the next player.
4. **How to run the scripted checks headless.** From the repo root, with `GODOT` standing for the Godot 4.7.2
   executable:

       GODOT --headless --path . --import
       GODOT --headless --path . --script res://checks/step0_setup.gd

   and so on for each file in `checks/` (there are 25, `step0` to `step24`). Each prints what it checks and
   ends with one line, `STEP N CHECK: PASS (K assertions)`, and exit code 0; a failure lists what failed and
   exits 1. All 25 pass at this hand-back. Together they take about ten minutes; the ones that play a whole
   game on screen are the slow ones. They use none of the owner's pictures.
5. **The `ASSETS.md` ledger.** One outside asset: the Quaternius Universal Animation Library (CC0), 11 of its
   clips used. Everything else is made in this repo: the body (a Blender script), the props and scenery (a kit
   of shapes), the speech syllables (a formula), fog and mist (code).
6. **What turned out harder or different from the brief.** See the next section.

## Different from the brief

- **It grew.** The brief ends at step 7, a playable loop on one small board. The owner kept going: a second
  board (Witch Hill, 78 spaces, a hill, a path that turns round), stars, items, banks, shops, armorers, duels,
  Jeb, keepers and a host who speak, places away from the board (Jeb's lair, the ending island), bonus stars,
  an options window, a map, and the game in numbers at the end. Steps 8 to 24 of the checks cover it.
- **The camera is not fixed.** The brief asked for a fixed camera. The owner chose one that follows whoever is
  up and glides between views; the whole-board view is the intro and the map.
- **Closing on SIGTERM cannot be made clean.** On Linux, Godot 4.7.2 ends at once on SIGTERM: no game code
  runs, and GDScript cannot catch it. Close the game with the `quit` action or a window close request, and
  never rely on the game saving anything as it exits (README, "Control from outside").
- **Everything is a module.** Boards, characters, rule sets, space types, items, features and mini games are
  each a file in a known folder; the core names none of them (README, "Modules"). Data-only content (characters,
  boards, rule sets, pictures) can also live outside the repo.
- **The owner's pictures are not in the repo, and the game does not need them.** Faces, body pictures, scene
  textures and NPC pictures live in `private/` (ignored by git) or another content folder, and are found when
  the game runs. Without them it is placeholder faces and flat colours. On the hub, name the folder that holds
  them when starting the game, or in the `PRIVYPARTY_CONTENT` setting of the computer:

      GODOT --path . -- --content=PATH_TO_FOLDER

- **The body is built by a Blender script,** and the built file (`models/template_body.glb`) is in the repo.
  The hub does not need Blender.
- **The project's license is still undecided.** No LICENSE file, no headers.

## Where the hub side plugs in

- **Mini games: one seam.** The rules call `play(players) -> scores` once a round, and for every duel with
  the two players in it (`rules/minigame.gd`). The answer is one number per player, higher is better; anything
  else counts as a draw. The rules wait for the answer however long it takes, so a burst of an emulator game
  fits behind it. A mini game is a script in `minigames/` (the contract is at the top of `core/registry.gd`);
  `game/minigame_picker.gd` stands at the seam and picks one, seeded. The only one there now is a stub,
  `minigames/mash.gd` (press confirm fast). Real ones are the hub side's.
- **Saving: a seam with nothing behind it.** `main.save_state()` returns all it takes to play the game again
  up to now, as plain data (board, rule set, players, seed, the rules' record so far). Give `main.saver` any
  object with `save(state) -> bool` and the options window's "Save the game" hands it that. Loading a save
  back is not built. The same seed, choices and scores give the same game (`rules/replay.gd`).
- **Control from outside.** `pause` and `quit` are single input actions. `pause` also brings up the options
  window, which any device can work while the game is paused.
- **A game with nobody at the controls.** `main.play_headless(seed, players, config)` plays a whole game at
  once with the scenes attached; the checks use it.

## What to measure on the hub first

- **The renderer.** The project is set to Godot's default (Forward+, Vulkan). It is not tied to it:
  `--rendering-method` and `--rendering-driver` switch it per run. Off the PC the game has only been drawn
  with the Compatibility renderer in software, for pictures.
- **The picture.** Fixed 1920x1080, up to 60 frames a second, scaled to the window.
- **Fog, mist and lamps.** The dark half of Witch Hill has fog by distance, two see-through layers of ground
  mist, and eight small lights with no shadows. In software a frame took about twice as long with all of
  it on, at its thickest. That is the worst case for this kind of drawing and a graphics card should make
  light of it, but it is not measured on the hub. One line of the options window, "Fog and lamps", turns it
  all off.
- **The stream.** The owner's pictures are shown with their pixels square (not smoothed), and the ground and
  scenery carry them: busy texture in motion, which the brief warned costs bitrate. The drifting mist adds
  slow motion over the dark half. Neither has been seen through the encoder.
- **Load.** No shadows are cast anywhere (blob shadows only), there is no post-processing, and a board is a
  few hundred small pieces.

## Not done on this side

- **Sound effects: planned, not started.** A short pass made in code, the way the speech syllables are
  (a formula writes the files, nothing from outside, so nothing for the ledger): dice, hops, berries, stars,
  the wheel, items, Jeb, fireworks, menu blips. The game already has the three sound buses ("Speech", "Music",
  "Sound") and their switches in the options window, so the hub can take the game as it is and the effects
  arrive later without anything else changing.
- **Music: not planned yet.** It needs outside tracks (CC0 or CC-BY, each read at its source and recorded in
  `ASSETS.md`), which is the owner's to pick.
- **Real mini games, loading a save, an export preset** (when one is made, leave `private/*` out of it).
- **Every rule number and every spoken line is a placeholder** the owner has tuned by playing, and may tune
  again (`boards/witch_hill_notes.md` lists each number and where it lives).

## Rules that still hold

A separate repo; real photos never in git; outside code MIT / BSD / Apache / GPL and outside art, sound and
fonts CC0 / CC-BY / OFL, each recorded in `ASSETS.md` first; no license file until the owner chooses; nothing
perceptual is a gate; nothing adopted without the owner's say-so; no addresses, credentials or identifiers in
any file.
