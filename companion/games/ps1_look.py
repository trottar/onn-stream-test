"""C5-M5B section 4: the PS1 look, per session, behind PRIVYHUB_PS1_LOOK.

Pre-registered in docs/memory/evidence/c5_m5b_2026-10-03/c5_m5b_preregistration.txt
(section 5). Pure: no I/O; the emulator manager reads the adopted options file,
writes the session file and removes it.

The mechanism: for a Beetle PSX HW launch with a preset that changes keys, the
session core-options file is the ADOPTED `Beetle PSX HW.opt` (read, never
written) with the preset's keys replaced; the regenerated privyhub-session.cfg
points that launch at it (`global_core_options` + `core_options_path`). The
file lives beside privyhub-session.cfg in the project's data directory and is
removed at the session's end and at the next launch. Nothing in the RetroArch
config directory is written. A title with its own per-title .opt keeps
RetroArch's precedence (its own file wins), so the look applies to titles
without one.

Unset (or "4x") -> no keys, no file, a session cfg byte-identical to today's.
An unknown value is ignored (flagged), exactly like unset.
"""

from __future__ import annotations

import os
import re

LOOK_ENV = "PRIVYHUB_PS1_LOOK"
CORE_LIBRARY = "Beetle PSX HW"
SESSION_OPTIONS_NAME = "privyhub-look-session.opt"

# The presets offered to the user: "4x" is the adopted config (the same as
# unset); "remaster" is the full preset of the cost table (section 5), offered
# only because it held 60 in its 720p hold. Values are this core build's own.
PRESETS: dict[str, dict[str, str]] = {
    "4x": {},
    # C5-M5B: the full preset held 60 in its 720p hold (b_full: RetroArch 59.999 fps,
    # longest 256-frame interval 4,276 ms of 4,278.7; encoder 60.0, 0 dup/drop; GPU 25.2 % / p95 34).
    "remaster": {"beetle_psx_hw_filter": "bilinear",
                 "beetle_psx_hw_dither_mode": "disabled",
                 "beetle_psx_hw_pgxp_mode": "memory only",
                 "beetle_psx_hw_pgxp_texture": "enabled",
                 "beetle_psx_hw_pgxp_vertex": "enabled"},
}

# "remaster-1080p" in tools/ps1_look.sh: offered only if the full preset also
# held 60 at the rung (section 5's rung hold). It did NOT (c_full_rung: one
# 256-frame interval of 4,283 ms, 102 s after the entry, against the 4,278.7 bar;
# 59.998 fps), so it is not offered.
REMASTER_AT_RUNG_OFFERED = False

# The cost table's levers, one per hold (measurement only, never offered;
# the helper does not name them). Filled with this core build's values.
MEASURE: dict[str, dict[str, str]] = {
    "measure-dither-off": {"beetle_psx_hw_dither_mode": "disabled"},
    "measure-filter-xbr": {"beetle_psx_hw_filter": "xBR"},
    "measure-filter-sabr": {"beetle_psx_hw_filter": "SABR"},
    "measure-filter-bilinear": {"beetle_psx_hw_filter": "bilinear"},
    "measure-filter-3point": {"beetle_psx_hw_filter": "3-point"},
    "measure-filter-jinc2": {"beetle_psx_hw_filter": "JINC2"},
    "measure-pgxp": {"beetle_psx_hw_pgxp_mode": "memory only",
                     "beetle_psx_hw_pgxp_texture": "enabled",
                     "beetle_psx_hw_pgxp_vertex": "enabled"},
    "measure-msaa-4x": {"beetle_psx_hw_msaa": "4x"},
    # The full preset (section 5's rule): 4x + the best-cost filter (bilinear: the lowest GPU busy
    # mean of the filters that held 60 -- SABR, bilinear, 3-point; xBR and JINC2 missed) + dither off
    # + PGXP. Written after the filter holds, before its own hold.
    "measure-full": {"beetle_psx_hw_filter": "bilinear",
                     "beetle_psx_hw_dither_mode": "disabled",
                     "beetle_psx_hw_pgxp_mode": "memory only",
                     "beetle_psx_hw_pgxp_texture": "enabled",
                     "beetle_psx_hw_pgxp_vertex": "enabled"},
    # The mechanism's smoke: a lever whose effect RetroArch's log shows (the
    # render target is 2048^2 at 2x, 4096^2 at the adopted 4x).
    "measure-smoke-2x": {"beetle_psx_hw_internal_resolution": "2x"},
}


def look_from_env(environ: dict[str, str] | None = None) -> tuple[str | None, dict[str, str], bool]:
    """(preset name or None, the keys it replaces, ignored-unknown flag)."""
    raw = (environ if environ is not None else os.environ).get(LOOK_ENV)
    if raw is None or raw.strip() == "":
        return None, {}, False
    name = raw.strip().lower()
    if name in PRESETS:
        return name, dict(PRESETS[name]), False
    if name in MEASURE:
        return name, dict(MEASURE[name]), False
    return None, {}, True


def session_options_text(base_text: str, keys: dict[str, str]) -> str:
    """The adopted options with each key's value replaced. Every key must be
    present exactly once in the adopted file (no new keys, no guessing)."""
    out = base_text
    for key, value in keys.items():
        if '"' in value or "\n" in value:
            raise ValueError(f"unsafe option value for {key}")
        pattern = re.compile(rf'(?m)^{re.escape(key)} = "[^"\n]*"$')
        if len(pattern.findall(out)) != 1:
            raise ValueError(f"{key} is not exactly once in the adopted options")
        out = pattern.sub(f'{key} = "{value}"', out, count=1)
    return out


def session_cfg_text(name: str, options_path: str) -> str:
    """The lines appended to privyhub-session.cfg for this launch."""
    if '"' in options_path or "\n" in options_path:
        raise ValueError("unsafe options path")
    return ("\n\n# PrivyHub C5-M5B session-only PS1 look (" + LOOK_ENV + "=" + name + ")\n"
            + 'global_core_options = "true"\n'
            + f'core_options_path = "{options_path}"\n')
