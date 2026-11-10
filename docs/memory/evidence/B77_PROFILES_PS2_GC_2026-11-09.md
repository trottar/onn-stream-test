---
memory_schema: 1
as_of: 2026-11-09
status: BUILT, NOT ADOPTED (session B, queue AC) — the onn's Input Profiles applied at PS2 (PCSX2 PAD bindings) and GameCube (Dolphin GCPadNew.ini) launches; N64's path confirmed by a test. Default on, PRIVYHUB_PROFILES_EXT=0 = today. No emulator started; nothing committed. No title, serial, path or identifier in this record
---

# B77 — Input Profiles on PS2 and GameCube (2026-11-09)

**The user's answer (G2):** PS2 / GameCube use the **same** Input Profiles — **yes**.

**Design** hashed before code at 23:22:09Z.

## What was built (`b77.diff`)

- **`companion/profile_layouts.py`** (pure): a profile's mapping (RetroPad target ← the physical button, PS1's own
  format; an unmapped target keeps its default; the legacy whole-stick targets applied after the directional ones, as
  RetroArch reads them) resolved per player, then:
  - onto PCSX2's DualShock 2 names (Cross = the bottom RetroPad button, Circle = right, Square = left, Triangle =
    top, L1 / R1 / L2 / R2 / L3 / R3, Select, Start, the d-pad, both sticks) as PCSX2's SDL names;
  - onto Dolphin's GameCube keys, chosen so the default gives **B69's map exactly** (A = bottom, B = left, X = right,
    Y = top, Z = R1, L / R triggers = L2 / R2, Main stick = left stick, C-stick = right stick, the d-pad) as Dolphin's
    evdev names.
- **PCSX2:** `pad_sections` / `settings_for` take the four players' tables; the launch passes the assigned profile's.
- **Dolphin:** `gcpad_ini` / `config_files` / `write_config` take the four tables.
- **The launch:** `_ext_profile_layouts(game, kind)` reads the effective profile with the RetroArch path's own checks.
  The Default profile, or one equal to the identity → today's tables (byte for byte). An unusable profile → today's
  tables and a log line; the launch goes on. The game log gets `PS2 input profile: assigned|default overrides=<n>` /
  `GC input profile: …` (no profile name).
- **The onn:** Options → "Input Profile" already shows for every title: **no client change**.
- **N64:** the RetroArch launch reaches `_prepare_input_override` for N64 as for PS1 (B59's branch, before the
  override); the profile's lines carry a swap (`input_player1_b_btn` / `_a_btn`), beside B62's core remap.

## Tests (`tests/art_systems/test_b77.py`, 17)

- Translation: the default and the identity give today's tables; a bottom / right swap gives Cross = `FaceEast`,
  Circle = `FaceSouth`, and Dolphin's A = `EAST`, X = `SOUTH`, every other key unchanged; the sticks (legacy and
  directional); a trigger onto a button; per player; today's text byte for byte; the knob.
- **PCSX2's launch (B49's rig, a fake PCSX2 in a subprocess):** a swap reaches `[Pad1]` and leaves `[Pad2]`; the
  Default profile, the identity and the knob 0 write the same ini as the knob-0 launch; the log line has no name.
- **Dolphin's launch (B69's rig, a fake Dolphin):** the swap reaches `GCPad1`, not `GCPad2`; the default and the
  knob 0 write today's `GCPadNew.ini`; the other config files unchanged; an unusable profile → today's file + the line.
- **N64:** the profile's RetroArch lines carry the swap; the N64 branch reaches the input override.
- 3 runs: 17 / 17 each. Mutations: **8 / 9 caught**; M5 (the default short-circuit removed) is an equivalent mutant
  (the tables equal today's by value and the line is the same), noted in `tests_mutations.txt`.
- B49-B57's `ps2_session` (93), B69's `gamecube_session` (54), `b72_small_readings` (25), `relaunch_ports` (19),
  `n64_session` (28): green in the tree.

## Disclosed

- With the knob on (its default), every PS2 / GameCube launch writes one more game-log line (the profile's source).
- The GameCube pad has no Select, L1 or L3 / R3: a profile mapping onto those RetroPad targets has nothing to drive
  there; Z is R1's target.

## Files

`b77_2026-11-09/`: the design + hash, `b77.diff`, `proof_flag_absent.md`, `tests_x3.txt`, `tests_mutations.txt`,
`scripts/mutations.json`, checks, manifest. Patch note: `patches/B77_PROFILES_PS2_GC.md`.
