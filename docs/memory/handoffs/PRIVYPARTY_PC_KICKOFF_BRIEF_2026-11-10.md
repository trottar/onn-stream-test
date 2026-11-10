# PrivyParty — kickoff brief for the PC side (2026-11-10)

**Who this is for:** the Claude working with the user on their Windows PC, in the Claude desktop app with ONE connected
folder: the PrivyParty project folder. You cannot see the hub, the external drive or the rest of the PC, and you do not
need to.

**What PrivyParty is:** a Mario Party-like board game for PrivyHub, the user's home game-streaming system. It is built
in Godot, runs on the user's hub (a Linux x86-64 box) and is streamed to the TV. Its mini games will be the board's own
plus short scored bursts of emulator games. This brief covers the part that can be built on the PC now. The hub side
(launching it from the TV, the stream, the pads, emulator mini games) starts later, in a different session.

**Source of the decisions below:** the user's design notes of 2026-11-10, recorded in the PrivyHub repo
(`docs/memory/architecture/H7_PRIVYPARTY_DESIGN_NOTES_2026-11-10.md`). If this brief and the user disagree, the user
wins; ask before changing a decision.

## Rules that do not bend

1. **A separate repo.** PrivyParty lives in its own git repo. Never commit into the PrivyHub repo and never ask for
   access to it.
2. **Real player photos never go into git.** They stay in an ignored folder (`private/`, in `.gitignore` from the first
   commit) or on the external drive. Commit placeholder faces only.
3. **Licenses.** Code you bring in must be MIT / BSD / Apache / GPL. Art, sound and fonts must be CC0 / CC-BY / OFL.
   Nothing marked non-commercial or no-redistribution. Mixamo is out. Before using any outside asset or add-on, read its
   license at its source and record it in `ASSETS.md` (what, where from, which license, the date). If you cannot
   confirm the license, do not use it.
4. **The project's own license is not decided.** The user leans toward restricting commercial use and will choose
   later. Do not add a LICENSE file or license headers; say "license undecided" in the README.
5. **Nothing perceptual is a gate.** Acceptance is scripted checks. How it looks and feels is the user's call; ask
   them, do not judge it yourself.
6. **Nothing is adopted without the user's say-so.** Propose, show, then wait.
7. **No addresses, credentials or identifiers** in any file: no IPs, MACs, SSIDs, serials, passwords, tokens.
8. **Keep replies short.** When the user has to do something by hand, give numbered steps, one action each, and say
   what they should see.

## What is decided

- **Look:** photo textures wrapped on rough low-polygon models; a funny, quirky tone; a fixed camera; "it's all about
  the character". Build only what the fixed camera sees, stage-set style: flat photo cutouts for background characters
  and props, blob shadows, painted backdrops. Textures about 256-512 px square per character.
- **Characters:** ONE template body, built and rigged once, with segmented rigid limbs (PS1 style, no skin weighting).
  A character = the template + a photo + proportion numbers (head size, leg length, torso width). No per-character
  modeling. UV by simple projection of the photo.
- **Animation:** one shared set of about a dozen clips (idle, walk, jump, cheer, sulk, dice roll, get hit…) from a CC0
  library, retargeted onto the template skeleton with Godot's humanoid retarget profile. The rest is code-driven: bob,
  wobble, squash and stretch, spin, pop. Proportion tweaks are rules in code driven by the proportion numbers (a big
  head leans back and wobbles late; short legs take faster, smaller steps; a wide torso holds its arms out; tiny
  characters play faster and bouncier). No blended variants, no physics-driven movement.
- **Speech:** a nonsense language with subtitles: a small set of short clips, shuffled and pitch-shifted per
  character; new dialogue is subtitle text only.
- **Props and scenery:** a kit of about 20 primitive shapes with photos applied.
- **Players:** up to four. Later, each home's own photos become the players; the template-body design already allows it.

## Build order, each step with its scripted check

0. **Setup.** The user installs Godot (the current stable 4.x), Blender and git. Create the repo with `.gitignore`
   (Godot's cache folder, exports, `private/`), a README (what it is, the exact Godot version, "license undecided") and
   an empty `ASSETS.md`. *Check:* a fresh clone opens in that Godot version with no errors; `private/` is ignored.
1. **The rules, no graphics.** The board as a graph of spaces; dice; turn order; coins or points; the end of a game.
   One seam for mini games: a function that takes the players and returns the result, stubbed for now (the hub's
   emulator mini games will sit behind it later). A seeded random source so a game can be replayed.
   *Check:* a headless script plays whole games from fixed seeds and asserts the outcomes; the same seed gives the same
   game.
2. **The template body.** In Blender: the segmented body and one skeleton with bone names Godot's humanoid profile
   accepts. In Godot: a character resource (photo path, the proportion numbers) and a scene that builds a character
   from it. Placeholder faces only. *Check:* a script builds characters from several resources and asserts the bone
   scales match the numbers.
3. **Animation.** Retarget the shared set; add the code-driven motion and the proportion rules. *Check:* every clip in
   the list exists and plays on the template; the proportion rules return the expected values for sample numbers.
4. **Props and a first board scene.** The primitive kit; one small board under the fixed camera with blob shadows and a
   backdrop. *Check:* the scene loads headless; every space in the rules' graph has a place in the scene.
5. **Input and joining.** Up to four pads through Godot's ordinary joypad input (devices 0-3), with a keyboard
   fallback for the PC. Joining is press-and-hold: hold any button for half a second to join as the next player; a tap
   does nothing. Pause and quit are each a single input action. *Check:* a script feeds fake input events and asserts
   the join order, that a tap does not join, and that pause and quit fire.
6. **Speech and subtitles.** The clip shuffler with per-character pitch; subtitle lines as text resources. *Check:* the
   same seed gives the same clip sequence; every subtitle key used in the scenes exists.
7. **A playable loop.** Board, dice, movement, a stub mini game, scoring, an ending, for 1-4 players. *Check:* the
   headless playthrough from step 1 still passes with the scenes attached. Then the user plays it on the PC and says
   what they think.

Stop after any step and show the user; they decide what comes next.

## Keep the hub in mind

- **Target:** a Linux x86-64 export, fixed 1080p at 60 frames a second, with a host load around PS2-era games. Avoid
  heavy post-processing. Keep the renderer choice easy to switch; the hub's graphics ran Vulkan well for other
  emulators, but Godot has not been tried there.
- **The stream:** the picture is video-encoded on its way to the TV. Busy, noisy textures in motion cost bitrate. This
  will be measured on the hub; until then prefer clean shapes and calm backgrounds where the look allows.
- **Control from outside:** the hub will need to pause, resume and close the game without a keyboard. Make the game
  close cleanly when the operating system asks it to, and keep pause and quit as single input actions.
- **Same Godot version on both sides:** the hub will build and run headless with the version named in the README.

## What waits for the hub side (do not start)

Launching from the TV; the capture and the stream; pads arriving through the TV box; emulator games as mini games and
reading the winner from game memory; measuring the stream's bitrate; headless builds on the hub.

## What to hand back when the hub side starts

The repo's address; the exact Godot version; the list of input actions; how to run the scripted checks headless; the
`ASSETS.md` ledger; anything in the build that turned out harder or different from this brief.
