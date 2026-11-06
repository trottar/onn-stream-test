"""B41: a title's player count for the client's player prompt ("Player N — press any button").

No host flag: the client's key is the switch. A client with `debug.privyhub.player_prompt=1` sends `player_prompt=1`
on its `native-stream-start`; only then does the start response carry `players` (1-4) and `players_source`. **A
client without it sends no key: nothing imports this module and the response is today's byte for byte.** Design:
`docs/memory/evidence/b41_2026-11-06/design_written_before_code.md` (hashed before this code).

The rule (no per-title "players" field exists on this hub):
- the library's `player_mode` `single` (the user's manual choice, or suggested from the metadata's `max_players` 1)
  -> 1;
- else the ports the core reads: 4 for a PS1 title with the multitap on (`ps1_multitap` mode `port1`, D087 / D087R1),
  else 2;
- `players` = min(ports, max_players) when the metadata's `max_players` is 2 or more, else the ports.
An unknown title is therefore 2. Any failure to read -> 2, `players_source` "default". Never raises.
"""

from __future__ import annotations

from typing import Any

DEFAULT = 2


def rule(player_mode: str, mode_source: str, max_players: int, ps1_multitap_on: bool) -> tuple[int, str]:
    """(players, source) from the library / metadata / multitap reads."""
    if player_mode == "single":
        return 1, (mode_source if mode_source in ("manual", "metadata") else "metadata")
    ports = 4 if ps1_multitap_on else 2
    if max_players >= 2:
        return min(ports, max_players), ("multitap" if ps1_multitap_on else "metadata")
    if ps1_multitap_on:
        return ports, "multitap"
    return ports, ("manual" if mode_source == "manual" and player_mode == "multi" else "default")


def for_start(plugin: Any, game_status: dict[str, Any] | None) -> dict[str, Any]:
    """{"players": n, "players_source": src} for the running title; 2 / "default" on any failure."""
    try:
        emulator = getattr(plugin, "_emulator", None)
        game = getattr(emulator, "active_game", None) or (game_status or {}).get("game")
        if not isinstance(game, dict) or not game.get("id"):
            return {"players": DEFAULT, "players_source": "default"}
        library = plugin._read_library_state()["games"]
        decorated = plugin._decorate_game(game, library, {}, None)
        player_mode = str(decorated.get("player_mode", "") or "").strip().casefold()
        mode_source = str(decorated.get("player_mode_source", "") or "").strip().casefold()
        try:
            max_players = int(decorated.get("max_players", 0) or 0)
        except (TypeError, ValueError):
            max_players = 0
        multitap_on = False
        if str(game.get("system", "")).strip().casefold() == "ps1":
            try:
                multitap_on = bool(emulator.ps1_multitap(game).get("enabled", False))
            except Exception:
                multitap_on = False
        players, source = rule(player_mode, mode_source, max_players, multitap_on)
        return {"players": int(players), "players_source": source}
    except Exception:
        return {"players": DEFAULT, "players_source": "default"}
