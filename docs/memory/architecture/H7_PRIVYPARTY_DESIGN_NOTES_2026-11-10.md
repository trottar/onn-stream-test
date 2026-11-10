---
memory_schema: 1
as_of: 2026-11-10
status: DESIGN NOTES for ROADMAP §H7 (PrivyHub-native games; first: PrivyParty). Decisions from the user's planning chat of 2026-11-10 (a chat with no access to the repo), recorded on the user's "Adopt" after the wording was shown. PC-SIDE PREPARATION STARTED on the user's word (2026-11-10), in a separate repo; THE HUB SIDE NOT STARTED. Nothing here was checked against the code unless a line says so
---

# H7 — PrivyParty: design and workflow decisions (2026-11-10)

**Legend:** [USER] = the user said it. [AGREED] = proposed in the planning chat and accepted by the user. [CHECK] =
unverified, to confirm when work starts. [KNOWN] = read from this project's own records.

**Two rules, stated once:**
- **Real player photos never go into git** (the repo is public): an ignored folder or the external drive only;
  placeholder faces are what is committed.
- **Acceptance stays scripted and non-perceptual** (dice, turns, scoring, the mini-game winner). How it looks is the
  user's call on the PC.

## 1. Art direction

- [USER] Photo textures wrapped on rough low-polygon models. Funny, quirky tone: "funny pictures wrapped on rough
  polygon models."
- [USER] NPC chatter in a nonsense language, with subtitles.
- [USER] Fixed camera (Mario Party style).
- [USER] Custom heads, bodies, etc. per character. "It's all about the character."
- [AGREED] Build only what the fixed camera sees, stage-set style: flat photo cutouts for background characters and
  props, blob shadows, painted backdrops, simpler models for far-off objects.
- [AGREED] Textures small, about 256-512 px square per character.
- [AGREED] Gibberish speech = a small set of short clips, shuffled and pitch-shifted per character; new dialogue is
  subtitle text only. Clips could be the players' own recorded voices.

## 2. Models

- [AGREED] ONE template body, built and rigged once. Each character = the template + a photo + proportion numbers
  (bone scaling: head size, leg length, torso width). No per-character modeling.
- [AGREED] Segmented rigid limbs (PS1 style), to avoid skin weighting.
- [AGREED] Props and scenery from a small kit of primitives (about 20 shapes) with photos applied.
- [AGREED] UV mapping by simple projection of the photo; only camera-facing sides need a proper texture.

## 3. Animation

- [AGREED] One shared animation set for all characters, about a dozen: idle, walk, jump, cheer, sulk, dice roll, get
  hit, etc.
- [AGREED] Source: a CC0 library (Quaternius Universal Animation Library was named), retargeted onto the template
  skeleton with Godot's humanoid retarget profile. Not hand-animated.
- [AGREED] Code-driven motion for the rest: bob, wobble, squash and stretch, spin, pop.
- [USER] Proportion-based animation tweaks: the EASY route. Rules in code driven by the proportion numbers (examples:
  a big head leans back and wobbles late; short legs take faster, smaller steps; a wide torso holds its arms out; tiny
  characters play faster and bouncier).
- Not chosen: blended animation variants (a possible later upgrade). Rejected: physically simulated / fully procedural
  movement.

## 4. Licensing rule

- [USER] "Everything we use is open source too with no limits on distribution."
- [AGREED] Working rule: code must be MIT / BSD / Apache / GPL; art, sound and fonts must be CC0 / CC-BY / OFL.
  Nothing marked non-commercial or no-redistribution.
- [AGREED] Godot (MIT), Blender (output unrestricted), CC0 animations and the user's own assets pass. Mixamo is OUT (no
  redistribution of raw files).
- [CHECK] **Audit the emulators PrivyHub actually uses against this rule.** [KNOWN] the ones in use: snes9x (SNES, the
  adopted `SNES_CORE=snes9x`), Beetle PSX HW (PS1), Mupen64Plus-Next (N64), PCSX2 (PS2), Dolphin (GameCube), run by
  RetroArch or standalone. [KNOWN] none of them is in the public repo: they sit in an ignored folder on the hub,
  fetched there. The planning chat singled out snes9x: its license is generally described as non-commercial — **to
  confirm from the core's own license file**, not read here. Game images and BIOS stay user-supplied.
- [USER] **The project's own license, to weigh together with the asset rule:** "Commercial use restricted ideally,
  since I'd want to eventually release" (2026-11-10); decided later. [KNOWN] the repo has no license file and the
  README no license statement today (the top level and the README checked, 2026-11-10). **A tension to weigh at that
  point, not settled here:** "everything open source with no limits on distribution" and "commercial use restricted"
  pull in different directions; a proper check is needed when the license is chosen.

## 5. Future feature

- [USER] May become part of the future PrivyHub with each home's own custom images as the players.
- [AGREED] Falls out of the template-body design: a home's photos are just another texture. Photos stay on that home's
  hub and never leave it.

## 6. Development workflow

- [USER] The server is limited; the user works remotely from a Windows 10 PC.
- [USER] Wants Claude's help on the PC side, but full file access stays on the server; only a restricted version on the
  PC is acceptable.
- [USER] Suggested the external hard drive (already read by PrivyHub for games and video) as the link between the two
  sides.
- [AGREED] The split:
  1. **PC:** the Godot editor and Blender installed there (they need a screen). The user does the template body, the
     photos, the proportions and the look.
  2. **Hub:** no editor, only the built game. Godot runs headless for builds and scripted checks. Claude Code writes
     the game logic as it does now. Real tests go through the onn and the stream.
  3. **Git:** carries scripts and scenes between the PC and the hub (history, merging two editors, backup). The Godot
     project sits on the PC's own disk, not a network folder.
     [USER] 2026-11-10: **the game lives in its own repo, separate from the PrivyHub repo.** The hub pulls it only
     when H7's hub side starts; the hub's Code sessions and the PrivyHub repo's history are not touched by PC work.
  4. **External drive:** player photos, raw art sources and finished builds. Reached from the PC over the existing SSH
     connection (SFTP). The drive stays plugged into the hub; it is not carried to the PC.
  5. **Claude on the PC:** the Claude desktop app with ONE connected folder, the game project folder. It never sees
     the drive or the rest of the PC. The planning chat set Claude Code on native Windows aside for this, giving as its
     reason that its folder limit does not cover shell commands — **the planning chat's statement, not verified
     here.**

## 6b. What goes ahead on the PC now, and what waits (the user, 2026-11-10)

- [USER] "since a lot of this work will be on my pc … we can probably have a parallel workflow on PC to finish what we
  can over there so it's ready when we hit h7".
- **On the PC now:** the setup (Godot, Blender, git, the Claude desktop app with the one folder, an SFTP tool); the
  template body with placeholder faces and proportion numbers; the shared animation set and the code-driven motion; the
  kit of primitive props and a first board scene under the fixed camera; the board's rules in code (dice, turns,
  scoring) with scripted checks that run on the PC. The kickoff brief for the PC side:
  `docs/memory/handoffs/PRIVYPARTY_PC_KICKOFF_BRIEF_2026-11-10.md`.
- **Waits for H7 on the hub:** launching from the onn, the capture, the pads through the onn; emulator mini games and
  the winner read from game memory; the stream's bitrate with photo textures; headless builds on the hub.

## 7. Open items

- [KNOWN] **Answered:** the stream captures the window (and the audio) of whatever process the hub launches, not
  RetroArch specifically — PCSX2 and Dolphin already run that way (H3-P1's and H2-P1's parts tables; B49, B69). A Godot
  game fits the existing pipeline through a new launch kind. Godot itself is not checked on the hub.
- [CHECK] One measurement during the proof of concept: the stream's bitrate with photo textures in motion.
- [CHECK] Whether the hub can run Godot headless builds within its limits.
- [CHECK] Godot's fit on the hub: the four virtual pads, pause and exit from the onn, host cost (ROADMAP §H7).
- PC setup still to do by the user when work starts: Godot, Blender, git, the Claude desktop app with the one folder
  connected, an SFTP tool.
- Carry-over rules apply: placeholders only (no IPs, MACs, SSIDs, ADB endpoints, serials, credentials); nothing
  adopted without the user's say-so.
- Open (the user's, from §H7): which games become mini games.
