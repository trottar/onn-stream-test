"""B54: the multitap at once -- the same title relaunched mid-session with new ports, play resuming where it was.

Only `native-stream-relaunch-ports` calls this, and only a hold-to-join client (`debug.privyhub.player_prompt`, on by
default) asks it, when a pad holds for a port the session does not have (P3 on two ports). **No request = nothing
here runs: today byte for byte.** RetroArch cannot change a port device or a core option mid-session (B46 S2), so the
core is stopped and the title launched again with the new ports; the encoder (which captures the core's own window)
is restarted on the new window; the controller session stays up. Design:
`docs/memory/evidence/b54_2026-11-08/design_written_before_code.md` (hashed before this code).

The sequence: pause -> the state (RetroArch: `save_relaunch_state`; PS2: none, the title restarts -- B55's reserved
PINE slot is the follow-up) -> the encoder stopped -> the core stopped -> the launch with the new ports -> resume, a
1.0-s settle, the running-core load of the relaunch save (D-BASE-R3c2's way), pause -> the encoder started for the
remembered client on the new window. The new launch failing -> the previous ports again (the same load); that failing
too -> the session ends and the error is the answer. The load failing -> the title runs from its start (`restarted`).
"""

from __future__ import annotations

import time
from typing import Any, Callable

import players_session as _players_session

BUDGET_S = 15.0        # from the join to play (the client's gate included); the row's steps are what A reads
SETTLE_S = 1.0         # RECOVERY_LOAD_SETTLE_S: the running-core load after the relaunch


class RelaunchRefused(Exception):
    """A request the host will not act on (nothing was touched)."""


def _ms(t0: float, clock: Callable[[], float]) -> int:
    return int(round((clock() - t0) * 1000.0))


def run(plugin: Any, players: int, players_joined: int | None = None, *,
        clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """The relaunch for `players` ports (2 or 4). Raises RelaunchRefused (untouched) or RuntimeError (ended)."""
    emulator = plugin._emulator
    stream = plugin._native_stream
    status = emulator.status()
    if not status.get("active", False):
        raise RelaunchRefused("No game is running")
    game = getattr(emulator, "active_game", None)
    if not isinstance(game, dict) or not game.get("id"):
        raise RelaunchRefused("No game is running")
    target = int(players)
    if target not in (2, 4):
        raise RelaunchRefused("players must be 2 or 4")
    system = str(game.get("system", "")).strip().casefold()
    if target == 4 and system not in _players_session.MULTITAP_SYSTEMS:
        raise RelaunchRefused("No multitap on this system")
    args = getattr(plugin, "_recovery_start_args", None)
    if not isinstance(args, dict) or not args.get("client_ip"):
        raise RelaunchRefused("No stream client to restart the picture for")
    if getattr(emulator, "_active_cheat_session", None) is not None:
        raise RelaunchRefused("A cheat or mod session is not relaunched")
    current = _players_session.ports_set(emulator, status)["ports_set"]
    if int(current.get("ports", current.get("players", 2))) == target:
        raise RelaunchRefused("The session already has these ports")
    previous = 4 if current.get("multitap") else 2
    kind = "pcsx2" if getattr(emulator, "_launch_kind", None) == "pcsx2" else "retroarch"

    steps: dict[str, int] = {}
    t_all = clock()
    row: dict[str, Any] = {"players": target, "players_joined": players_joined, "kind": kind, "steps_ms": steps}

    def step(name: str, fn: Callable[[], Any]) -> Any:
        t0 = clock()
        try:
            return fn()
        finally:
            steps[name] = _ms(t0, clock)

    if not status.get("paused", False):
        step("pause", emulator.pause)
    state_path = None
    if kind == "retroarch":
        try:
            saved = step("save", emulator.save_relaunch_state)
        except Exception as exc:
            # nothing stopped: the client's gate releases and the game resumes as it was
            raise RelaunchRefused(f"The game's state could not be saved; nothing was changed: {exc}") from exc
        state_path = saved.get("state_path")
    else:
        row["reason"] = "ps2_no_relaunch_state"
    step("stream_stop", stream.stop)
    step("stop", emulator.stop)

    ok = True
    try:
        step("launch", lambda: emulator.launch(game, players_chosen=target))
        landed = target
    except Exception as exc:
        ok = False
        row["fallback"] = "previous_ports"
        row["launch_error"] = str(exc)[:200]
        try:
            step("launch_previous", lambda: emulator.launch(game, players_chosen=previous))
            landed = previous
        except Exception as exc2:
            row["ok"] = False
            row["total_ms"] = _ms(t_all, clock)
            row["ended"] = True
            plugin._recovery._log("relaunch_ports", **row)
            try:
                stream.end_game_session()
            except Exception:
                pass
            raise RuntimeError(f"The game could not restart with {target} players and was stopped: {exc2}") from exc2
    session = getattr(emulator, "_players_session", None)
    if isinstance(session, dict):
        session["source"] = "relaunch"

    state = "restarted"
    if state_path is not None:
        try:
            step("resume", emulator.resume)
            step("settle", lambda: sleep(SETTLE_S))
            step("load", lambda: emulator.load_recovery_state_running(source=state_path))
            state = "loaded"
        except Exception as exc:
            row["load_error"] = str(exc)[:200]
        step("pause_after", emulator.pause)
    else:
        step("pause_after", emulator.pause)

    pid = emulator.status().get("pid")
    port = int(args.get("port") or getattr(stream, "DEFAULT_PORT", 0))
    try:
        step("stream_start", lambda: stream.start(client_ip=str(args["client_ip"]), port=port, managed_process_id=pid))
    except Exception as exc:
        row.update({"ok": False, "state": state, "stream_error": str(exc)[:200], "total_ms": _ms(t_all, clock)})
        plugin._recovery._log("relaunch_ports", **row)
        raise RuntimeError(f"The game restarted but its picture did not: {exc}") from exc
    ports = _players_session.ports_set(emulator, emulator.status())["ports_set"]
    total = _ms(t_all, clock)
    row.update({"ok": ok, "state": state, "landed_ports": landed, "total_ms": total,
                "within_budget": total <= BUDGET_S * 1000.0})
    plugin._recovery._log("relaunch_ports", **row)
    plugin._recovery._log("ports_set", **ports)
    return {"ok": ok, "relaunch": {k: row[k] for k in ("state", "steps_ms", "total_ms", "landed_ports", "kind")
                                   if k in row} | ({"fallback": row["fallback"]} if "fallback" in row else {}),
            "ports_set": ports}
