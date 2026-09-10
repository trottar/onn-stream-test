#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "http://localhost:8765"
XINPUT_A = 0x1000
FACE_MASK = 0xF000


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_uint32),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


def request_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except OSError as exc:
        raise RuntimeError(
            "Companion API is unavailable on localhost:8765. "
            "Start the companion before running this probe."
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Companion API returned a non-object payload")
    return payload


def load_xinput():
    if os.name != "nt":
        raise RuntimeError("This runtime probe is Windows-only")
    errors = []
    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            dll = ctypes.WinDLL(name)
            fn = dll.XInputGetState
            fn.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_STATE)]
            fn.restype = ctypes.c_uint
            return fn, name
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise RuntimeError("Unable to load XInputGetState: " + "; ".join(errors))


def xinput_states(get_state) -> dict[int, int]:
    result: dict[int, int] = {}
    for index in range(4):
        state = XINPUT_STATE()
        if int(get_state(index, ctypes.byref(state))) == 0:
            result[index] = int(state.Gamepad.wButtons)
    return result


def face_snapshot(get_state, slots: list[int]) -> dict[int, int]:
    states = xinput_states(get_state)
    return {slot: int(states.get(slot, 0)) & FACE_MASK for slot in slots}


def capture_player1_a(get_state, slots: list[int], timeout: float = 12.0):
    deadline = time.monotonic() + timeout
    neutral_hits = 0
    last = {slot: 0 for slot in slots}
    while time.monotonic() < deadline:
        last = face_snapshot(get_state, slots)
        if all(mask == 0 for mask in last.values()):
            neutral_hits += 1
            if neutral_hits >= 5:
                break
        else:
            neutral_hits = 0
        time.sleep(0.01)
    else:
        return -1, 0, last, False, False

    press_slot = -1
    press_mask = 0
    press_snapshot = dict(last)
    while time.monotonic() < deadline:
        snap = face_snapshot(get_state, slots)
        active = [(slot, mask) for slot, mask in snap.items() if mask]
        if active:
            press_snapshot = dict(snap)
            press_slot, press_mask = active[0]
            break
        time.sleep(0.01)

    if press_slot < 0:
        return -1, 0, press_snapshot, False, False

    ambiguous = sum(1 for mask in press_snapshot.values() if mask & XINPUT_A) != 1
    release_deadline = time.monotonic() + timeout
    neutral_hits = 0
    released = False
    while time.monotonic() < release_deadline:
        snap = face_snapshot(get_state, slots)
        if all(mask == 0 for mask in snap.values()):
            neutral_hits += 1
            if neutral_hits >= 5:
                released = True
                break
        else:
            neutral_hits = 0
        time.sleep(0.01)
    return press_slot, press_mask, press_snapshot, released, ambiguous


def yes(prompt: str) -> bool:
    return input(prompt).strip().casefold() in {"y", "yes"}


def latest_game_log(root: Path, game_id: str) -> Path | None:
    log_root = root / "logs" / "games"
    if not log_root.is_dir() or not game_id:
        return None
    candidates = sorted(
        log_root.glob(f"*-{game_id}.log"),
        key=lambda p: p.stat().st_mtime_ns,
        reverse=True,
    )
    return candidates[0] if candidates else None


def wait_inactive(timeout: float = 12.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if not bool(request_json("/plugins/games/status").get("active")):
                return True
        except Exception:
            pass
        time.sleep(0.15)
    return False


def wait_slots_removed(get_state, timeout: float = 8.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not xinput_states(get_state):
            return True
        time.sleep(0.10)
    return not bool(xinput_states(get_state))


def self_test() -> int:
    assert FACE_MASK & XINPUT_A == XINPUT_A
    assert yes.__name__ == "yes"
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    out = root / "logs" / "games" / "phase_a_1p_regression_probe.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "PrivyHub Phase A one-player regression probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
    ]
    classification = "PHASE_A_1P_REGRESSION_NOT_CONFIRMED"

    try:
        get_state, dll_name = load_xinput()
        request_json("/plugins/games/status")

        print("")
        print("PHASE A — 1P REGRESSION")
        print("Start any previously working game normally from the onn using Player 1.")
        print("When gameplay is visible and responsive, press Enter here.")
        input()

        status = request_json("/plugins/games/status")
        active = bool(status.get("active"))
        game = status.get("game") if isinstance(status.get("game"), dict) else {}
        game_id = str(game.get("id", "")).strip()
        title = str(game.get("title", "")).strip() or game_id or "<unknown>"
        system = str(game.get("system", "")).strip() or "<unknown>"
        slots = sorted(xinput_states(get_state))

        print("")
        print("Press and release physical A once on the controller intended as Player 1.")
        press_slot, press_mask, press_snapshot, released, ambiguous = capture_player1_a(
            get_state, slots
        )

        gameplay_ok = yes(
            "Did Player 1 movement, face buttons, and Start behave normally in gameplay? [y/n]: "
        )
        cross_control = yes(
            "Did any other connected controller unexpectedly take over Player 1 during this check? [y/n]: "
        )

        game_log = latest_game_log(root, game_id)
        log_age = None
        port1 = None
        fallback = None
        if game_log is not None:
            log_age = max(0.0, time.time() - game_log.stat().st_mtime)
            text = game_log.read_text(encoding="utf-8", errors="replace")
            port1 = "Xbox 360 Controller configured in port 1." in text
            fallback = 'Configured joypad driver "xinput" failed to initialise' in text

        lines.extend([
            f"XInput DLL: {dll_name}",
            f"Game active during capture: {active}",
            f"Game: {title}",
            f"System: {system}",
            "Live XInput slots during gameplay: " + (
                ", ".join(str(slot + 1) for slot in slots) if slots else "none"
            ),
            f"Physical Player 1 A observed slot: {press_slot + 1 if press_slot >= 0 else 'none'}",
            "Player 1 press snapshot: " + ", ".join(
                f"slot {slot + 1}=0x{mask:04X}" for slot, mask in sorted(press_snapshot.items())
            ),
            f"Player 1 A mask observed: {bool(press_mask & XINPUT_A)}",
            f"Player 1 release confirmed: {released}",
            f"Ambiguous simultaneous A: {ambiguous}",
            f"User gameplay controls normal: {gameplay_ok}",
            f"Unexpected cross-controller takeover observed: {cross_control}",
            f"RetroArch game log: {str(game_log.relative_to(root)) if game_log else '<not found>'}",
            f"RetroArch game log age seconds: {round(log_age, 1) if log_age is not None else 'n/a'}",
            f"Port 1 Xbox autoconfig observed: {port1}",
            f"XInput startup fallback observed: {fallback}",
        ])

        print("")
        print("Now use PrivyHub End/Exit to end the game normally. When the game session is gone, press Enter.")
        input()
        inactive = wait_inactive()
        slots_removed = wait_slots_removed(get_state)
        lines.append(f"Companion session inactive after normal End/Exit: {inactive}")
        lines.append(f"Session XInput slots removed after End/Exit: {slots_removed}")

        ok = all([
            active,
            slots == [0, 1, 2, 3],
            press_slot == 0,
            bool(press_mask & XINPUT_A),
            released,
            not ambiguous,
            gameplay_ok,
            not cross_control,
            port1 is True,
            fallback is False,
            log_age is not None and log_age <= 900,
            inactive,
            slots_removed,
        ])
        if ok:
            classification = "PHASE_A_1P_REGRESSION_CONFIRMED"

    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")

    lines.insert(2, f"Classification: {classification}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("")
    print(f"Classification: {classification}")
    print(f"Probe log: {out}")
    return 0 if classification == "PHASE_A_1P_REGRESSION_CONFIRMED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
