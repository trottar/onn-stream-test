# B77 — Input Profiles on PS2 and GameCube (design, written and hashed before code)

**Knob:** default on; `PRIVYHUB_PROFILES_EXT=0` = today (no profile read at a PCSX2 / Dolphin launch). Reached only
inside `PRIVYHUB_PS2=1` / `PRIVYHUB_GAMECUBE=1` (the launches exist only there).

## What exists (read at HEAD)

- **The profile:** `data/games/input_profiles.json`, read through `EmulatorManager.input_profile_for_game(game)` →
  `{"profile": {"mapping": {"player1".."player4": {target: source}}}, ...}`. Targets are RetroPad names (`b` = the
  bottom face button, `a` = right, `y` = left, `x` = top, `l` / `r`, `l2` / `r2`, `l3` / `r3`, `select`, `start`,
  the d-pad, `left_stick_*` / `right_stick_*`, and the legacy whole axes `left_x` … `right_y`); sources are the
  physical pad's Xbox-style names (`a` = bottom, `b` = right, `x` = left, `y` = top, same for the rest). The editor's
  default is the physical identity (`b ← a`, `a ← b`, `y ← x`, `x ← y`, the rest to themselves). The Default profile
  has an empty mapping. **A target left unmapped keeps its default source** (RetroArch's autoconfig); RetroArch's
  lines are applied directional first, then the legacy whole axes (the later line wins).
- **PS2:** `_launch_pcsx2` merges `ps2_session.settings_for(…)` into `PCSX2.ini` every launch; `pad_sections`
  writes `[Pad1]…[Pad8]`, each used pad `SDL-<k>/<name>` from `DS2_BINDINGS` (k = the player index - 1).
- **GameCube:** `_launch_dolphin` writes `GCPadNew.ini` whole every launch from `gamecube_session.PAD_LAYOUT`
  (B69's map) for `GCPad1`-`GCPad4`, by evdev names.
- **The onn:** Options → "Input Profile" is offered for every title (no system gate in `MainActivity.kt`): **no
  client change.**
- **N64:** a RetroArch launch; `launch()` calls `_prepare_input_override` for every RetroArch system, N64 included,
  so the assigned profile's lines go into the session's append config, beside B62's core remap.

## The change

1. New `companion/profile_layouts.py` (pure, no I/O):
   - `PHYSICAL_SDL` (source → PCSX2's SDL name: `a`→`FaceSouth`, `b`→`FaceEast`, `x`→`FaceWest`, `y`→`FaceNorth`,
     `l`→`LeftShoulder`, `r`→`RightShoulder`, `l2`→`+LeftTrigger`, `r2`→`+RightTrigger`, `l3`→`LeftStick`,
     `r3`→`RightStick`, `select`→`Back`, `start`→`Start`, d-pad → `DPad*`, stick directions → `±LeftX` …);
   - `PHYSICAL_EVDEV` (source → Dolphin's evdev name, B69's: `a`→`SOUTH`, `b`→`EAST`, `x`→`WEST`, `y`→`NORTH`,
     `l`→`TL`, `r`→`TR`, `select`→`SELECT`, `start`→`START`, `l3`→`THUMBL`, `r3`→`THUMBR`, d-pad → `Axis 7-/7+/6-/6+`,
     `l2`→`Axis 2-+`, `r2`→`Axis 5-+`, sticks → `Axis 0-/0+/1-/1+/3-/3+/4-/4+`);
   - `DEFAULT_SOURCE` (target → its source in the editor's default);
   - `DS2_TARGETS` (each PCSX2 DualShock 2 binding name → its RetroPad target: Cross→`b`, Circle→`a`, Square→`y`,
     Triangle→`x`, L1→`l`, R1→`r`, L2→`l2`, R2→`r2`, L3→`l3`, R3→`r3`, Select, Start, the d-pad, `LUp`…→
     `left_stick_*`, `RUp`…→`right_stick_*`);
   - `GC_TARGETS` (each Dolphin GameCube key → its target, so that the default gives B69's map: A→`b`, B→`y`,
     X→`a`, Y→`x`, Z→`r`, Start→`start`, Main Stick→`left_stick_*`, C-Stick→`right_stick_*`, Triggers/L and
     L-Analog→`l2`, Triggers/R and R-Analog→`r2`, D-Pad→the d-pad);
   - `resolve(player_mapping)` → target → source for every target: the default, then the mapping's directional
     entries, then its legacy whole axes (each sets both directions of the target stick from the source stick);
   - `ds2_bindings(player_mapping)` → the `(name, sdl)` tuple in `DS2_BINDINGS`' order;
     `gc_layout(player_mapping)` → the `(key, evdev)` tuple in `PAD_LAYOUT`'s order;
   - `is_default(mapping)` → every player's resolved map equals the default.
2. `ps2_session.pad_sections(players, multitap, bindings=None)` / `settings_for(…, bindings=None)`: `bindings[k]`
   (k = 0..3) replaces `DS2_BINDINGS` for the k-th used pad; None = today.
3. `gamecube_session.gcpad_ini(layouts=None)`, `config_files(gcpad_layouts=None)`,
   `write_config(user_dir, gcpad_layouts=None)`: `layouts[n-1]` replaces `PAD_LAYOUT` for `GCPad<n>`; None = today.
4. `emulator_manager`: `_ext_profile_layouts(game, kind)`:
   - knob `0` → None;
   - else the effective profile's normalized + validated mapping (the RetroArch path's own checks); a mapping whose
     resolution is the default (the Default profile, or a profile equal to the identity) → None (today's files);
   - else the four players' `ds2_bindings` (PS2) / `gc_layout` (GameCube);
   - a profile that fails the checks → None and a log line (the launch goes on with today's layout; never refused).
   `_launch_pcsx2` passes it to `settings_for`; `_launch_dolphin` to `write_config`. The game log gets
   `PS2 input profile: <assigned|default> overrides=<n players>` / `GC input profile: …` (no profile name).

## Tests (`tests/art_systems/test_b77.py`, fixtures only)

- the default (empty) and the identity mapping → `ds2_bindings` == `DS2_BINDINGS`, `gc_layout` == `PAD_LAYOUT`,
  and `settings_for` / `gcpad_ini` text byte for byte today's;
- a swap (`b ← b`, `a ← a`: the bottom and right buttons swapped) → PCSX2's Cross = `FaceEast`, Circle =
  `FaceSouth`; Dolphin's A = `EAST`, X = `SOUTH`; every other key unchanged;
- the sticks: `left_x ← right_x` (legacy) and `left_stick_up ← right_stick_up` (directional) honoured on both;
- a trigger onto a button (`l2 ← a`): Dolphin's Triggers/L and L-Analog = `SOUTH`;
- per player: a mapping on player 2 only changes pad 2;
- the manager: a fake project with an assigned swap profile → the PCSX2 ini's `[Pad1]` and `GCPadNew.ini` carry the
  swap (the launch halves called directly with the emulators faked: nothing started); the knob `0` → today's files;
  the Default profile → today's files byte for byte; an invalid profile → today's files and the log line;
- N64: the same swap profile on an N64 game → `_a8_retroarch_profile_lines` gives the swapped
  `input_player1_a_btn` / `_b_btn` lines (the path the N64 launch takes), and `launch()`'s N64 branch reaches
  `_prepare_input_override` (read from the source).
