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

B57 (a PS2 session only, so only with `PRIVYHUB_PS2=1`): the state goes through PINE's reserved slot 7 -- the save
with B52's file-complete check, SIGTERM, the launch with `MultitapPort1` per the count, resume, the load holding until
the game's ELF is up, B52's picture check -> `loaded`. No 1.0-s settle (the ELF hold is it). Any failed step -> the
title restarts without the state (B54's PS2 behaviour) with `state: restarted` and a `reason`: a save failure is not
a refusal on PS2; a loaded state whose picture is static / faulted -> the title launched once more, clean. Design:
`docs/memory/evidence/b57_2026-11-08/design_written_before_code.md` (hashed before this code).
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
    # B69: a GameCube session has its four native ports from the launch: never relaunched (PRIVYHUB_GAMECUBE=1 only)
    if getattr(emulator, "_launch_kind", None) == "dolphin":
        raise RelaunchRefused("GameCube has four ports; no relaunch")
    system = str(game.get("system", "")).strip().casefold()
    if target == 4 and system not in _players_session.MULTITAP_SYSTEMS:
        raise RelaunchRefused("No multitap on this system")
    # B63: a PS1 title not multitap-capable is never relaunched onto the multitap (its player 2 would be dead)
    capable = getattr(emulator, "ps1_multitap_capable", None)
    if (target == 4 and system == "ps1" and _players_session.capability_rule_on() and callable(capable)
            and not capable(game)):
        raise RelaunchRefused("This game supports 2 players")
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
        # B57: PINE's slot 7; a failure is not a refusal on PS2 -- the title restarts without the state (B54's PS2 path)
        try:
            saved = step("save", emulator.save_relaunch_state)
            state_path = saved.get("state_path")
            row["ps2_states"] = "pine"
            row["slot"] = saved.get("slot")
        except Exception as exc:
            row["reason"] = "ps2_relaunch_save_failed"
            row["save_error"] = str(exc)[:200]
    step("stream_stop", stream.stop)
    step("stop", emulator.stop)

    ok = True

    def launch_ports(name: str, ports: int) -> int:
        nonlocal ok
        try:
            step(name, lambda: emulator.launch(game, players_chosen=ports))
            return ports
        except Exception as exc:
            ok = False
            row["fallback"] = "previous_ports"
            row["launch_error"] = str(exc)[:200]
            try:
                step(name + "_previous", lambda: emulator.launch(game, players_chosen=previous))
                return previous
            except Exception as exc2:
                row["ok"] = False
                row["total_ms"] = _ms(t_all, clock)
                row["ended"] = True
                plugin._recovery._log("relaunch_ports", **row)
                try:
                    stream.end_game_session()
                except Exception:
                    pass
                raise RuntimeError(
                    f"The game could not restart with {target} players and was stopped: {exc2}") from exc2

    landed = launch_ports("launch", target)
    session = getattr(emulator, "_players_session", None)
    if isinstance(session, dict):
        session["source"] = "relaunch"

    state = "restarted"
    if state_path is not None and kind == "pcsx2":
        # B57: resume (PCSX2 boots on), the load holds until the ELF, B52's picture check; no settle
        try:
            step("resume", emulator.resume)
            step("load", lambda: emulator.load_recovery_state_running(source=state_path))
            state = "loaded"
        except Exception as exc:
            row["load_error"] = str(exc)[:200]
            picture = getattr(exc, "ps2_picture", None)
            if picture:
                # the loaded state did not run: the title once more, clean (today's restart)
                row["reason"] = f"ps2_relaunch_picture_{picture}"
                step("stop_clean", emulator.stop)
                landed = launch_ports("launch_clean", landed)
                session = getattr(emulator, "_players_session", None)
                if isinstance(session, dict):
                    session["source"] = "relaunch"
            else:
                row["reason"] = "ps2_relaunch_load_failed"
        step("pause_after", emulator.pause)
    elif state_path is not None:
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
    keys = ("state", "steps_ms", "total_ms", "landed_ports", "kind", "reason")    # B57: + reason (only PS2 sets it)
    return {"ok": ok, "relaunch": {k: row[k] for k in keys
                                   if k in row} | ({"fallback": row["fallback"]} if "fallback" in row else {}),
            "ports_set": ports}
