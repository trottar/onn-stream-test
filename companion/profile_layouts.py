"""B77: an Input Profile (the onn's, PS1's) translated onto PCSX2's DualShock 2 bindings and Dolphin's GameCube pad.

Pure: no I/O. A profile's mapping is `{player: {target: source}}`: the target is a RetroPad name (`b` the bottom face
button, `a` right, `y` left, `x` top, ...), the source the physical pad's Xbox-style name (`a` bottom, `b` right, `x`
left, `y` top, ...). A target the mapping leaves out keeps its default source (the editor's default: the physical
identity). The legacy whole-axis targets (`left_x` ...) are applied after the directional ones, as RetroArch reads
the lines. The default resolution gives today's tables exactly (`ps2_session.DS2_BINDINGS`,
`gamecube_session.PAD_LAYOUT`), so the Default profile writes today's files byte for byte.

Design: `docs/memory/evidence/b77_2026-11-09/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import os
from typing import Any, Mapping

KNOB_ENV = "PRIVYHUB_PROFILES_EXT"   # default on; "0" = today (no profile read at a PCSX2 / Dolphin launch)

STICK_DIRS = ("left_stick_left", "left_stick_right", "left_stick_up", "left_stick_down",
              "right_stick_left", "right_stick_right", "right_stick_up", "right_stick_down")
DIRECTIONAL = ("up", "down", "left", "right", "a", "b", "x", "y", "l", "r", "l2", "r2", "l3", "r3",
               "select", "start", *STICK_DIRS)
LEGACY_AXES = ("left_x", "left_y", "right_x", "right_y")
# a legacy whole-axis target / source -> its (minus, plus) directional names
AXIS_DIRS = {"left_x": ("left_stick_left", "left_stick_right"), "left_y": ("left_stick_up", "left_stick_down"),
             "right_x": ("right_stick_left", "right_stick_right"), "right_y": ("right_stick_up", "right_stick_down")}

# the editor's default: the physical identity in RetroPad terms
DEFAULT_SOURCE = {t: t for t in DIRECTIONAL}
DEFAULT_SOURCE.update({"a": "b", "b": "a", "x": "y", "y": "x"})

# the physical source -> PCSX2 2.8.2's SDL name (B50's names)
PHYSICAL_SDL = {
    "a": "FaceSouth", "b": "FaceEast", "x": "FaceWest", "y": "FaceNorth",
    "l": "LeftShoulder", "r": "RightShoulder", "l2": "+LeftTrigger", "r2": "+RightTrigger",
    "l3": "LeftStick", "r3": "RightStick", "select": "Back", "start": "Start",
    "up": "DPadUp", "down": "DPadDown", "left": "DPadLeft", "right": "DPadRight",
    "left_stick_left": "-LeftX", "left_stick_right": "+LeftX", "left_stick_up": "-LeftY", "left_stick_down": "+LeftY",
    "right_stick_left": "-RightX", "right_stick_right": "+RightX", "right_stick_up": "-RightY",
    "right_stick_down": "+RightY",
}
# the physical source -> Dolphin's evdev name on the companion's pad (B69's names)
PHYSICAL_EVDEV = {
    "a": "SOUTH", "b": "EAST", "x": "WEST", "y": "NORTH",
    "l": "TL", "r": "TR", "l2": "Axis 2-+", "r2": "Axis 5-+",
    "l3": "THUMBL", "r3": "THUMBR", "select": "SELECT", "start": "START",
    "up": "Axis 7-", "down": "Axis 7+", "left": "Axis 6-", "right": "Axis 6+",
    "left_stick_left": "Axis 0-", "left_stick_right": "Axis 0+", "left_stick_up": "Axis 1-", "left_stick_down": "Axis 1+",
    "right_stick_left": "Axis 3-", "right_stick_right": "Axis 3+", "right_stick_up": "Axis 4-",
    "right_stick_down": "Axis 4+",
}
# PCSX2's DualShock 2 binding name -> its RetroPad target (the PS layout, as PS1's core reads the RetroPad)
DS2_TARGETS = {
    "Up": "up", "Right": "right", "Down": "down", "Left": "left",
    "Triangle": "x", "Circle": "a", "Cross": "b", "Square": "y",
    "Select": "select", "Start": "start",
    "L1": "l", "L2": "l2", "R1": "r", "R2": "r2", "L3": "l3", "R3": "r3",
    "LUp": "left_stick_up", "LRight": "left_stick_right", "LDown": "left_stick_down", "LLeft": "left_stick_left",
    "RUp": "right_stick_up", "RRight": "right_stick_right", "RDown": "right_stick_down", "RLeft": "right_stick_left",
}
# Dolphin's GameCube key -> its RetroPad target (chosen so the default gives B69's PAD_LAYOUT)
GC_TARGETS = {
    "Buttons/A": "b", "Buttons/B": "y", "Buttons/X": "a", "Buttons/Y": "x",
    "Buttons/Z": "r", "Buttons/Start": "start",
    "Main Stick/Up": "left_stick_up", "Main Stick/Down": "left_stick_down",
    "Main Stick/Left": "left_stick_left", "Main Stick/Right": "left_stick_right",
    "C-Stick/Up": "right_stick_up", "C-Stick/Down": "right_stick_down",
    "C-Stick/Left": "right_stick_left", "C-Stick/Right": "right_stick_right",
    "Triggers/L": "l2", "Triggers/R": "r2", "Triggers/L-Analog": "l2", "Triggers/R-Analog": "r2",
    "D-Pad/Up": "up", "D-Pad/Down": "down", "D-Pad/Left": "left", "D-Pad/Right": "right",
}
PLAYERS = ("player1", "player2", "player3", "player4")


def enabled(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get(KNOB_ENV, "")).strip() != "0"


def resolve(player_mapping: Mapping[str, str] | None) -> dict[str, str]:
    """target -> physical source for every directional target: the default, the mapping's directional entries, then
    its legacy whole axes (both directions of the target stick from the source stick's)."""
    out = dict(DEFAULT_SOURCE)
    pm = dict(player_mapping or {})
    for target, source in pm.items():
        if target in DEFAULT_SOURCE and source in PHYSICAL_SDL:
            out[target] = source
    for target in LEGACY_AXES:
        source = pm.get(target)
        if source in AXIS_DIRS:
            t_minus, t_plus = AXIS_DIRS[target]
            s_minus, s_plus = AXIS_DIRS[source]
            out[t_minus], out[t_plus] = s_minus, s_plus
    return out


def ds2_bindings(player_mapping: Mapping[str, str] | None, order: tuple[tuple[str, str], ...]) -> tuple:
    """PCSX2's `(name, sdl)` pairs in `order`'s order (`ps2_session.DS2_BINDINGS`)."""
    r = resolve(player_mapping)
    return tuple((name, PHYSICAL_SDL[r[DS2_TARGETS[name]]]) for name, _sdl in order)


def gc_layout(player_mapping: Mapping[str, str] | None, order: tuple[tuple[str, str], ...]) -> tuple:
    """Dolphin's `(key, evdev)` pairs in `order`'s order (`gamecube_session.PAD_LAYOUT`)."""
    r = resolve(player_mapping)
    return tuple((key, PHYSICAL_EVDEV[r[GC_TARGETS[key]]]) for key, _ev in order)


def is_default(mapping: Mapping[str, Mapping[str, str]] | None) -> bool:
    m = mapping or {}
    return all(resolve(m.get(p)) == DEFAULT_SOURCE for p in PLAYERS)


def overridden_players(mapping: Mapping[str, Mapping[str, str]] | None) -> int:
    m = mapping or {}
    return sum(resolve(m.get(p)) != DEFAULT_SOURCE for p in PLAYERS)


def per_player(mapping: Mapping[str, Mapping[str, str]] | None, kind: str, order: tuple) -> list[tuple]:
    """The four players' tables (`kind` "ps2" or "gamecube")."""
    m = mapping or {}
    fn = ds2_bindings if kind == "ps2" else gc_layout
    return [fn(m.get(p), order) for p in PLAYERS]
