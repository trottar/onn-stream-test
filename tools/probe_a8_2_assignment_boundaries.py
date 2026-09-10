#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:8765"
XINPUT_A = 0x1000
XINPUT_B = 0x2000
FACE_MASK = 0xF000
EXPECTED_SWAP = {
    "input_player1_a_btn": "0",
    "input_player1_a_axis": "nul",
    "input_player1_b_btn": "1",
    "input_player1_b_axis": "nul",
}

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

def request_json(path: str, *, method: str = "GET") -> dict[str, Any]:
    request = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except OSError as exc:
        raise RuntimeError(
            "Companion API is unavailable on localhost:8765. "
            "Run the companion before this probe."
        ) from exc
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuntimeError("Companion API returned a non-object payload")
    return payload

def query_path(action: str, params: dict[str, str]) -> str:
    query = urllib.parse.urlencode(params)
    return "/plugins/games/" + action + ("?" + query if query else "")

def parse_cfg(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        values[key] = value
    return values

def expected_swap_present(values: dict[str, str]) -> bool:
    return all(values.get(key) == value for key, value in EXPECTED_SWAP.items())

def face_names(mask: int) -> str:
    names = []
    if mask & XINPUT_A:
        names.append("A")
    if mask & XINPUT_B:
        names.append("B")
    if mask & 0x4000:
        names.append("X")
    if mask & 0x8000:
        names.append("Y")
    return "+".join(names) if names else "none"

def load_xinput():
    if os.name != "nt":
        raise RuntimeError("Windows XInput measurement is Windows-only")
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

def wait_new_slots(get_state, baseline: set[int], timeout: float = 4.0) -> list[int]:
    deadline = time.monotonic() + timeout
    newest: list[int] = []
    while time.monotonic() < deadline:
        current = set(xinput_states(get_state))
        newest = sorted(current - baseline)
        if newest:
            return newest
        time.sleep(0.05)
    return newest

def free_udp_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()

def send_phi1(sock: socket.socket, port: int, sequence: int, player: int, buttons: int) -> None:
    packet = struct.pack(
        "<4sBBHIQIhhhhHH",
        b"PHI1",
        1,
        player,
        0,
        sequence,
        int(time.monotonic_ns() // 1000),
        buttons,
        0, 0, 0, 0,
        0, 0,
    )
    sock.sendto(packet, ("127.0.0.1", port))

def synthetic_press(get_state, slots: list[int], sock: socket.socket, port: int, buttons: int, seq: int) -> tuple[int, int]:
    for offset in range(12):
        send_phi1(sock, port, seq + offset, 0, buttons)
        send_phi1(sock, port, seq + 100 + offset, 1, 0)
        time.sleep(0.01)
    deadline = time.monotonic() + 1.0
    observed_slot = -1
    observed_mask = 0
    while time.monotonic() < deadline:
        states = xinput_states(get_state)
        for slot in slots:
            mask = states.get(slot, 0) & FACE_MASK
            if mask:
                observed_slot = slot
                observed_mask |= mask
        if observed_mask:
            break
        time.sleep(0.01)
    for offset in range(8):
        send_phi1(sock, port, seq + 300 + offset, 0, 0)
        send_phi1(sock, port, seq + 400 + offset, 1, 0)
        time.sleep(0.01)
    return observed_slot, observed_mask

def _face_snapshot(
    states: dict[int, int],
    slots: list[int],
) -> dict[int, int]:
    return {
        slot: int(states.get(slot, 0)) & FACE_MASK
        for slot in slots
    }

def _format_face_snapshot(
    snapshot: dict[int, int],
) -> str:
    return ", ".join(
        f"slot {slot}={face_names(mask)}"
        for slot, mask in sorted(snapshot.items())
    )

def capture_single_face_press(
    state_reader,
    slots: list[int],
    timeout: float = 10.0,
    poll_interval: float = 0.01,
) -> tuple[int, int, dict[int, int], bool]:
    # First require a stable neutral state so a stale held button from the
    # previous prompt cannot contaminate the next capture.
    deadline = time.monotonic() + timeout
    neutral_samples = 0

    while time.monotonic() < deadline:
        snapshot = _face_snapshot(
            state_reader(),
            slots,
        )

        if all(
            mask == 0
            for mask in snapshot.values()
        ):
            neutral_samples += 1
            if neutral_samples >= 5:
                break
        else:
            neutral_samples = 0

        time.sleep(poll_interval)
    else:
        return -1, 0, snapshot, False

    # Capture the first actual face-button transition after neutral.
    pressed_slot = -1
    pressed_mask = 0
    pressed_snapshot = {
        slot: 0
        for slot in slots
    }

    while time.monotonic() < deadline:
        snapshot = _face_snapshot(
            state_reader(),
            slots,
        )
        active = [
            (slot, mask)
            for slot, mask in snapshot.items()
            if mask != 0
        ]

        if active:
            pressed_snapshot = dict(snapshot)
            pressed_slot, pressed_mask = active[0]
            break

        time.sleep(poll_interval)

    if pressed_slot < 0:
        return -1, 0, pressed_snapshot, False

    # Require a stable release before the capture is considered complete.
    release_deadline = time.monotonic() + timeout
    neutral_samples = 0
    released = False

    while time.monotonic() < release_deadline:
        snapshot = _face_snapshot(
            state_reader(),
            slots,
        )

        if all(
            mask == 0
            for mask in snapshot.values()
        ):
            neutral_samples += 1
            if neutral_samples >= 5:
                released = True
                break
        else:
            neutral_samples = 0

        time.sleep(poll_interval)

    return (
        pressed_slot,
        pressed_mask,
        pressed_snapshot,
        released,
    )

def retroarch_running() -> bool:
    if os.name != "nt":
        return False
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq retroarch.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (completed.stdout or "").casefold()
    return "retroarch.exe" in text

def restore_path(path: Path, original: bytes | None) -> bool:
    if original is None:
        path.unlink(missing_ok=True)
        return not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(original)
    return path.is_file() and path.read_bytes() == original

def self_test() -> int:
    with __import__("tempfile").TemporaryDirectory() as td:
        p = Path(td) / "x.cfg"
        p.write_text(
            '# test\n'
            'input_player1_a_btn = "0"\n'
            'input_player1_a_axis = "nul"\n'
            'input_player1_b_btn = "1"\n'
            'input_player1_b_axis = "nul"\n',
            encoding="utf-8",
        )
        values = parse_cfg(p)
        assert expected_swap_present(values)
        assert face_names(XINPUT_A) == "A"
        assert face_names(XINPUT_B) == "B"
        packet = struct.pack(
            "<4sBBHIQIhhhhHH",
            b"PHI1", 1, 0, 0, 1, 2, XINPUT_A,
            0, 0, 0, 0, 0, 0,
        )
        assert len(packet) == 36

        samples = (
            [{0: 0}] * 5
            + [{0: XINPUT_A}]
            + [{0: 0}] * 5
        )
        index = 0

        def reader():
            nonlocal index
            if index < len(samples):
                value = samples[index]
                index += 1
                return value
            return samples[-1]

        slot, mask, snapshot, released = capture_single_face_press(
            reader,
            [0],
            timeout=0.5,
            poll_interval=0.0,
        )
        assert slot == 0
        assert mask == XINPUT_A
        assert snapshot == {0: XINPUT_A}
        assert released

    print("A8.2 assignment-boundary probe self-test: PASS")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    sys.path.insert(0, str(root))

    profile_path = root / "data/games/input_profiles.json"
    input_cfg = root / "data/games/retroarch/config/privyhub-input.cfg"
    session_cfg = root / "data/games/retroarch/config/privyhub-session.cfg"
    log_path = root / "logs/games/a8_2_assignment_boundaries.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    originals = {
        path: path.read_bytes() if path.is_file() else None
        for path in (profile_path, input_cfg, session_cfg)
    }

    lines = [
        "PrivyHub A8.2 assignment-boundary probe",
        "Purpose: measure controller assignment before launch and after normal RetroArch/game launch.",
        "Network addresses: not logged.",
    ]
    result = "FAIL"
    restored = False
    cleanup_stopped_game = False
    temp_profile_id = ""

    standalone_bridge = None
    standalone_socket = None

    try:
        status = request_json("/plugins/games/status")
        if status.get("active"):
            raise RuntimeError("End the active game before starting this probe")
        if retroarch_running():
            raise RuntimeError("RetroArch is already running before the probe")

        games_payload = request_json(
            query_path(
                "games",
                {"view": "search", "q": "Crash Team Racing", "limit": "20"},
            )
        )
        selected = None
        for node in games_payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            title = str(node.get("name") or node.get("title") or "").strip()
            if node.get("node_type") == "game" and "crash team racing" in title.casefold():
                selected = node
                break
        if selected is None:
            raise RuntimeError("Crash Team Racing was not found in the companion catalog")
        game_id = str(selected.get("id", "")).strip()
        game_name = str(selected.get("name") or selected.get("title") or game_id).strip()
        if not game_id:
            raise RuntimeError("CTR catalog record has no game id")

        from companion.native_session_io import NativeControllerBridge
        from companion.games.emulator_manager import EmulatorManager

        get_state, xinput_dll = load_xinput()
        baseline_slots = set(xinput_states(get_state))
        lines.append(f"XInput DLL: {xinput_dll}")
        lines.append(f"Baseline connected XInput slots: {sorted(baseline_slots)}")

        # CHECKPOINT 0: actual NativeControllerBridge + ViGEm, no RetroArch/game.
        standalone_bridge = NativeControllerBridge(root)
        probe_port = free_udp_port()
        standalone_bridge.start(client_ip="127.0.0.1", port=probe_port)
        standalone_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        new_slots = wait_new_slots(get_state, baseline_slots)
        if not new_slots:
            raise RuntimeError("No new XInput slot appeared after standalone ViGEm bridge start")

        a_slot, a_mask = synthetic_press(
            get_state, new_slots, standalone_socket, probe_port, XINPUT_A, 1000
        )
        b_slot, b_mask = synthetic_press(
            get_state, new_slots, standalone_socket, probe_port, XINPUT_B, 3000
        )
        pre_transport_ok = (
            a_slot >= 0
            and b_slot == a_slot
            and a_mask == XINPUT_A
            and b_mask == XINPUT_B
        )
        lines.extend([
            "",
            "CHECKPOINT 0 — PRE-RETROARCH CANONICAL TRANSPORT",
            f"Synthetic PHI1 A -> XInput face buttons: {face_names(a_mask)}",
            f"Synthetic PHI1 B -> XInput face buttons: {face_names(b_mask)}",
            f"Same Player 1 XInput slot: {a_slot >= 0 and b_slot == a_slot}",
            f"Canonical transport result: {'PASS' if pre_transport_ok else 'FAIL'}",
        ])
        standalone_bridge.stop()
        standalone_bridge = None
        standalone_socket.close()
        standalone_socket = None

        # Wait for probe-owned virtual devices to disappear before real launch.
        deadline = time.monotonic() + 4.0
        while time.monotonic() < deadline:
            if set(xinput_states(get_state)) == baseline_slots:
                break
            time.sleep(0.05)

        if not pre_transport_ok:
            result = "PRELAUNCH_TRANSPORT_FAIL"
            raise RuntimeError("Canonical PHI1 -> ViGEm/XInput A/B assignment failed")

        # CHECKPOINT 1: production A8 generator, still no RetroArch/game.
        manager = EmulatorManager(root)
        runtime = manager._runtime_details()
        game = {"id": game_id, "system": "ps1", "title": game_name}
        created = manager.create_input_profile(
            "A8 Boundary Probe Physical Swap A-B",
            {"player1": {"a": "a", "b": "b"}, "player2": {}},
        )
        temp_profile_id = str(created["id"])
        manager.assign_input_profile(game, temp_profile_id)
        generated_path, metadata = manager._prepare_input_override(game, runtime)
        if generated_path.resolve() != input_cfg.resolve():
            raise RuntimeError("Production A8 generator returned an unexpected config path")
        pre_values = parse_cfg(input_cfg)
        pre_assignment_ok = expected_swap_present(pre_values)
        pre_snapshot = {
            key: pre_values.get(key, "<missing>")
            for key in EXPECTED_SWAP
        }
        lines.extend([
            "",
            "CHECKPOINT 1 — A8 ASSIGNMENT BEFORE RETROARCH/GAME LAUNCH",
            f"Game: {game_name}",
            f"Temporary profile id: {temp_profile_id}",
            f"Profile source: {metadata.get('input_profile_source')}",
            f"input_player1_a_btn: {pre_snapshot['input_player1_a_btn']}",
            f"input_player1_a_axis: {pre_snapshot['input_player1_a_axis']}",
            f"input_player1_b_btn: {pre_snapshot['input_player1_b_btn']}",
            f"input_player1_b_axis: {pre_snapshot['input_player1_b_axis']}",
            f"Prelaunch A8 assignment result: {'PASS' if pre_assignment_ok else 'FAIL'}",
        ])
        if not pre_assignment_ok:
            result = "PRELAUNCH_ASSIGNMENT_FAIL"
            raise RuntimeError("Production A8 generator did not create the expected prelaunch swap")
        if retroarch_running():
            result = "PRELAUNCH_RETROARCH_UNEXPECTED"
            raise RuntimeError("RetroArch appeared during the prelaunch assignment checkpoint")

        post_baseline_slots = set(xinput_states(get_state))
        print("")
        print("CHECKPOINTS 0 AND 1 PASSED")
        print("")
        print("On the onn, launch this game normally and open the stream:")
        print(f"  {game_name}")
        print("Once gameplay is visible, return here.")
        input("Press Enter when CTR gameplay is visible: ")

        status = request_json("/plugins/games/status")
        if not status.get("active"):
            raise RuntimeError("No active game was reported after the launch checkpoint")
        if not retroarch_running():
            raise RuntimeError("RetroArch is not running after the game launch checkpoint")

        current_slots = set(xinput_states(get_state))
        game_slots = sorted(current_slots - post_baseline_slots)
        if not game_slots:
            # XInput slot numbering can be reused; if no delta exists, use all connected
            # slots but record that discovery was ambiguous.
            game_slots = sorted(current_slots)
            slot_delta = False
        else:
            slot_delta = True

        print("")
        print("POST-LAUNCH ANDROID -> XINPUT MEASUREMENT")
        print("Leave CTR on any visible screen. Do not start a race or load a state.")
        print("Release the controller, then follow each one-button prompt.")
        print("")
        print("Tap Player 1 physical A once now.")
        a_slot, a_mask, a_snapshot, a_released = capture_single_face_press(
            lambda: xinput_states(get_state),
            game_slots,
        )
        print(
            "Captured A: "
            + _format_face_snapshot(a_snapshot)
        )

        print("")
        print("Tap Player 1 physical B once now.")
        b_slot, b_mask, b_snapshot, b_released = capture_single_face_press(
            lambda: xinput_states(get_state),
            game_slots,
        )
        print(
            "Captured B: "
            + _format_face_snapshot(b_snapshot)
        )

        android_xinput_ok = (
            a_slot >= 0
            and b_slot >= 0
            and a_slot == b_slot
            and a_mask == XINPUT_A
            and b_mask == XINPUT_B
            and a_released
            and b_released
        )

        post_input_values = parse_cfg(input_cfg)
        post_session_values = parse_cfg(session_cfg)
        post_input_ok = expected_swap_present(post_input_values)
        post_session_ok = expected_swap_present(post_session_values)
        assignment_unchanged = all(
            post_input_values.get(key) == pre_values.get(key)
            for key in EXPECTED_SWAP
        )

        log_root = root / "logs/games"
        candidates = sorted(
            log_root.glob(f"*-{game_id}.log"),
            key=lambda item: item.stat().st_mtime_ns,
            reverse=True,
        )
        game_log = candidates[0] if candidates else None
        xinput_fallback = None
        xbox_autoconfig = None
        if game_log is not None:
            text = game_log.read_text(encoding="utf-8", errors="replace")
            xinput_fallback = (
                'Configured joypad driver "xinput" failed to initialise' in text
            )
            xbox_autoconfig = (
                "Xbox 360 Controller configured in port 1." in text
                and "Xbox 360 Controller configured in port 2." in text
            )

        lines.extend([
            "",
            "CHECKPOINT 2 — AFTER NORMAL RETROARCH/GAME LAUNCH",
            f"New XInput slot delta observed: {slot_delta}",
            f"Physical A XInput slot: {a_slot}",
            f"Physical A press face buttons: {face_names(a_mask)}",
            f"Physical A press raw per-slot: {_format_face_snapshot(a_snapshot)}",
            f"Physical A release observed: {a_released}",
            f"Physical B XInput slot: {b_slot}",
            f"Physical B press face buttons: {face_names(b_mask)}",
            f"Physical B press raw per-slot: {_format_face_snapshot(b_snapshot)}",
            f"Physical B release observed: {b_released}",
            f"Same XInput slot for physical A/B: {a_slot >= 0 and a_slot == b_slot}",
            f"Android -> PHI1 -> ViGEm canonical A/B: {'PASS' if android_xinput_ok else 'FAIL'}",
            f"Postlaunch privyhub-input.cfg retains swap: {post_input_ok}",
            f"Postlaunch privyhub-session.cfg contains swap: {post_session_ok}",
            f"A8 input assignment unchanged from prelaunch snapshot: {assignment_unchanged}",
            f"XInput startup fallback observed: {xinput_fallback}",
            f"Xbox controllers autoconfigured: {xbox_autoconfig}",
            "RetroArch game log: " + (str(game_log) if game_log else "<not found>"),
        ])

        # Stop here. This probe is intentionally limited to controller
        # assignment boundaries. Gameplay/core behavior is tested only after
        # both prelaunch and postlaunch assignment checkpoints pass.
        if not android_xinput_ok:
            result = "POSTLAUNCH_ANDROID_XINPUT_FAIL"
        elif not post_input_ok or not post_session_ok or not assignment_unchanged:
            result = "POSTLAUNCH_ASSIGNMENT_CHANGED"
        elif xinput_fallback is True:
            result = "POSTLAUNCH_XINPUT_STARTUP_FALLBACK"
        else:
            result = "ASSIGNMENTS_PASS_READY_FOR_GAMEPLAY_TEST"

    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")

    finally:
        try:
            status = request_json("/plugins/games/status")
            if status.get("active"):
                try:
                    request_json("/plugins/games/stop", method="POST")
                    cleanup_stopped_game = True
                    time.sleep(0.5)
                except Exception as exc:
                    lines.append(f"CLEANUP STOP ERROR: {type(exc).__name__}: {exc}")
        except Exception:
            pass

        if standalone_bridge is not None:
            try:
                standalone_bridge.stop()
            except Exception:
                pass
        if standalone_socket is not None:
            try:
                standalone_socket.close()
            except Exception:
                pass

        restore_results = []
        for path, original in originals.items():
            try:
                restore_results.append(restore_path(path, original))
            except Exception as exc:
                restore_results.append(False)
                lines.append(f"RESTORE ERROR: {path}: {type(exc).__name__}: {exc}")
        restored = all(restore_results)

    lines.append("")
    lines.append(f"Cleanup stopped active probe game: {cleanup_stopped_game}")
    lines.append(f"Input/profile/session files restored: {restored}")
    lines.append(f"Result: {result}")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("")
    print(f"Result: {result}")
    print(f"Input/profile/session files restored: {restored}")
    print(f"Probe log: {log_path}")
    return 0 if result == "BOUNDARY_END_TO_END_PASS" and restored else 1

if __name__ == "__main__":
    raise SystemExit(main())
