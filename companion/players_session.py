"""B46: the session's ports from the player chooser's pick (`players_chosen`), set at the launch.

The client (`debug.privyhub.player_prompt`, on by default) sends `players_chosen=<1|2|4>` on a `launch` when the onn
holds the title's last pick; **without the key nothing here runs and the launch is today's byte for byte**. With it:
- PS1: the per-content Beetle `.opt` is written for this launch with the port-1 multitap on (4) or off (1 / 2) -- the
  same write D087's metadata path does, fed from the pick instead of `controller_overrides.json`, which is not touched;
  the `--device` arguments are the pick's ports (1 -> port 2 None);
- SNES: 1 -> `--device=2:0`; 4 -> port 2 the core's multitap device (257: bsnes "Super Multitap", snes9x "Multitap");
- other systems: 1 -> `--device=2:0`; no multitap (2 ports).
RetroArch cannot change a core option or a port device mid-session (no network command does), so a pick made at the
chooser after the launch applies at the next launch (the client says so). Design:
`docs/memory/evidence/b46_2026-11-07/design_written_before_code.md` (hashed before this code). Never raises.
"""

from __future__ import annotations

from typing import Any

CHOICES = (1, 2, 4)
SNES_MULTITAP_DEVICE = 257   # RETRO_DEVICE_SUBCLASS(RETRO_DEVICE_JOYPAD, 0) in both SNES cores' libretro sources
NONE_DEVICE = 0              # RETRO_DEVICE_NONE
MULTITAP_SYSTEMS = ("ps1", "snes", "ps2")   # B49: ps2 = PCSX2's [Pad] MultitapPort1, no --device


def parse(raw: Any) -> int | None:
    """1 / 2 / 4, else None (multitap is sent as 4)."""
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return n if n in CHOICES else None


def plan(system: str, players_chosen: int, libretro_device: int | None) -> dict[str, Any]:
    """The launch's ports for the pick: the `.opt` mode (PS1), the `--device` arguments, the ports read."""
    system = str(system or "").strip().casefold()
    n = int(players_chosen)
    available = system in MULTITAP_SYSTEMS
    multitap = n == 4 and available
    args: list[str] = []
    if system == "ps1" and isinstance(libretro_device, int) and not isinstance(libretro_device, bool):
        ports = 4 if multitap else 2
        for player in range(1, ports + 1):
            args.append(f"--device={player}:{libretro_device}" if (n > 1 or player == 1) else f"--device=2:{NONE_DEVICE}")
    elif system == "ps2":
        pass   # B49: PCSX2 takes its ports from its ini (ps2_session.pad_sections), not RetroArch's --device
    elif system == "snes" and multitap:
        args.append(f"--device=2:{SNES_MULTITAP_DEVICE}")
    elif n == 1:
        args.append(f"--device=2:{NONE_DEVICE}")
    return {
        "players_chosen": n,
        "ports": 4 if multitap else (1 if n == 1 else 2),
        "multitap": multitap,
        "multitap_available": available,
        "ps1_mode": ("port1" if multitap else "off") if system == "ps1" else None,
        "device_args": args,
        "source": "launch",
    }


def ports_set(emulator: Any, game_status: dict[str, Any] | None) -> dict[str, Any]:
    """The start response's echo: the launch's plan, else the metadata's ports (4 with the PS1 multitap on, else 2)."""
    try:
        session = getattr(emulator, "_players_session", None)
        if isinstance(session, dict) and session.get("source") == "launch":
            return {"ports_set": {k: session[k] for k in ("players_chosen", "ports", "multitap", "multitap_available",
                                                          "source")} | {"players": int(session["ports"])}}
        game = getattr(emulator, "active_game", None) or (game_status or {}).get("game") or {}
        system = str(game.get("system", "")).strip().casefold()
        multitap = False
        if system == "ps1":
            try:
                multitap = bool(emulator.ps1_multitap(game).get("enabled", False))
            except Exception:
                multitap = False
        return {"ports_set": {"players": 4 if multitap else 2, "ports": 4 if multitap else 2, "multitap": multitap,
                              "multitap_available": system in MULTITAP_SYSTEMS, "source": "metadata"}}
    except Exception:
        return {"ports_set": {"players": 2, "ports": 2, "multitap": False, "multitap_available": False,
                              "source": "default"}}
