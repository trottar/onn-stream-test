#!/usr/bin/env python3
from __future__ import annotations
import ctypes
import json
import os
import re
import time
from pathlib import Path

TITLE = "CTR - Crash Team Racing (USA)"
CORE = "Beetle PSX HW"
PORT1 = "beetle_psx_hw_enable_multitap_port1"
PORT2 = "beetle_psx_hw_enable_multitap_port2"

def yes(prompt: str) -> bool:
    value = input(prompt + " [y/N]: ").strip().casefold()
    return value in {"y", "yes"}

def latest_ctr_log(root: Path) -> Path | None:
    logs = sorted(
        (root / "logs/games").glob("*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in logs[:100]:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if TITLE in text:
            return path
    return None

def xinput_slots() -> list[int]:
    if os.name != "nt":
        return []
    class State(ctypes.Structure):
        _fields_ = [
            ("packet", ctypes.c_uint32),
            ("gamepad", ctypes.c_ubyte * 12),
        ]
    dll = None
    for name in (
        "xinput1_4.dll",
        "xinput1_3.dll",
        "xinput9_1_0.dll",
    ):
        try:
            dll = ctypes.WinDLL(name)
            break
        except OSError:
            pass
    if dll is None:
        return []
    dll.XInputGetState.argtypes = [
        ctypes.c_uint32,
        ctypes.POINTER(State),
    ]
    dll.XInputGetState.restype = ctypes.c_uint32
    found = []
    for index in range(4):
        state = State()
        if dll.XInputGetState(index, ctypes.byref(state)) == 0:
            found.append(index + 1)
    return found

def option_value(text: str, key: str) -> str:
    pattern = re.compile(
        rf'(?m)^\s*{re.escape(key)}\s*=\s*"([^"]+)"\s*$'
    )
    match = pattern.search(text)
    return match.group(1).strip().casefold() if match else ""

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    log_dir = root / "logs/games"
    log_dir.mkdir(parents=True, exist_ok=True)
    output = log_dir / "ps1_multitap_onoff_runtime.txt"

    print("On the onn: open CTR -> Options -> Multitap -> On, launch CTR Battle,")
    print("and reach player/character selection with four controllers connected.")
    input("Press Enter when CTR is active and Players 3/4 should be available... ")

    game_log = latest_ctr_log(root)
    log_text = ""
    if game_log is not None:
        log_text = game_log.read_text(
            encoding="utf-8",
            errors="replace",
        )

    game_id = ""
    match = re.search(
        r"(?m)^Game ID:\s*(\S+)\s*$",
        log_text,
    )
    if match:
        game_id = match.group(1).strip()

    ctrl_path = (
        root
        / "data/games/retroarch/controller_overrides.json"
    )
    try:
        ctrl = json.loads(
            ctrl_path.read_text(
                encoding="utf-8-sig"
            )
        )
    except Exception:
        ctrl = {}

    entry = {}
    if game_id and isinstance(ctrl, dict):
        games = ctrl.get("games", {})
        if (
            isinstance(games, dict)
            and isinstance(games.get(game_id), dict)
        ):
            entry = games[game_id]

    override_mode = str(
        entry.get(
            "ps1_multitap",
            "",
        )
    ).strip().casefold()

    opt_candidates = sorted(
        (root / "runtime/emulators").glob(
            f"*/config/{CORE}/{TITLE}.opt"
        ),
        key=lambda p: (
            p.stat().st_mtime
            if p.exists()
            else 0
        ),
        reverse=True,
    )
    opt_path = (
        opt_candidates[0]
        if opt_candidates
        else None
    )
    opt_text = ""
    if opt_path is not None and opt_path.is_file():
        opt_text = opt_path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )

    port1 = option_value(
        opt_text,
        PORT1,
    )
    port2 = option_value(
        opt_text,
        PORT2,
    )
    slots = xinput_slots()

    p34_visible = yes(
        "Are Players 3 and 4 available (not greyed out) in CTR?"
    )
    independent = yes(
        "Do all four controllers operate their own players independently?"
    )

    backend_text = (
        root
        / "companion/games/emulator_manager.py"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )
    plugin_text = (
        root
        / "companion/plugins/games.py"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )
    android_text = (
        root
        / "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )

    markers = {
        "backend": (
            "PRIVYHUB_PHASE_A_PS1_MULTITAP_ONOFF_FLAG"
            in backend_text
        ),
        "plugin": (
            "PRIVYHUB_PHASE_A_PS1_MULTITAP_ONOFF_API"
            in plugin_text
        ),
        "android": (
            "PRIVYHUB_PHASE_A_PS1_MULTITAP_ONOFF_UI"
            in android_text
        ),
    }

    checks = {
        "ctr_log_found": game_log is not None,
        "ctr_game_id_found": bool(game_id),
        "override_port1": override_mode == "port1",
        "port1_enabled": port1 == "enabled",
        "port2_disabled": port2 == "disabled",
        "four_xinput_slots": slots == [1, 2, 3, 4],
        "players_3_4_visible": p34_visible,
        "four_independent": independent,
        "source_markers": all(markers.values()),
    }

    confirmed = all(checks.values())
    classification = (
        "PS1_MULTITAP_ONOFF_CTR_CONFIRMED"
        if confirmed
        else "PS1_MULTITAP_ONOFF_CTR_NOT_CONFIRMED"
    )

    lines = [
        "PrivyHub Phase A PS1 Multitap On/Off CTR runtime probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Classification: {classification}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
        f"CTR log found: {checks['ctr_log_found']}",
        f"CTR game id found: {checks['ctr_game_id_found']}",
        f"Per-game multitap override: {override_mode or '<none>'}",
        f"Game-specific options file found: {opt_path is not None}",
        f"Port 1 core option: {port1 or '<missing>'}",
        f"Port 2 core option: {port2 or '<missing>'}",
        (
            "Live XInput slots: "
            + (
                ", ".join(map(str, slots))
                if slots
                else "<none>"
            )
        ),
        f"Players 3/4 available in CTR: {p34_visible}",
        f"Four controllers independently normal: {independent}",
        f"Backend On/Off marker: {markers['backend']}",
        f"Games API On/Off marker: {markers['plugin']}",
        f"Android On/Off marker: {markers['android']}",
    ]
    output.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(classification)
    print("Log:", output)
    return 0 if confirmed else 1

if __name__ == "__main__":
    raise SystemExit(main())
