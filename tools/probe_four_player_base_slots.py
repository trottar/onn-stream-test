#!/usr/bin/env python3
from __future__ import annotations

import ctypes
import json
import os
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = PROJECT_ROOT / "logs" / "games" / "four_player_controller_probe.txt"
JSON_PATH = PROJECT_ROOT / "logs" / "games" / "four_player_controller_probe.json"
PACKET = struct.Struct("<4sBBHIQIhhhhHH")
FACE_MASK = 0xF000
FACE_BUTTONS = [0x1000, 0x2000, 0x4000, 0x8000]
FACE_NAMES = {
    0x1000: "A",
    0x2000: "B",
    0x4000: "X",
    0x8000: "Y",
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


def face_name(mask: int) -> str:
    selected = [
        name
        for bit, name in FACE_NAMES.items()
        if mask & bit
    ]
    return "+".join(selected) if selected else "none"


def load_xinput():
    if os.name != "nt":
        raise RuntimeError("Windows XInput measurement is Windows-only")

    errors: list[str] = []
    for name in (
        "xinput1_4.dll",
        "xinput1_3.dll",
        "xinput9_1_0.dll",
    ):
        try:
            dll = ctypes.WinDLL(name)
            fn = dll.XInputGetState
            fn.argtypes = [
                ctypes.c_uint,
                ctypes.POINTER(XINPUT_STATE),
            ]
            fn.restype = ctypes.c_uint
            return fn, name
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    raise RuntimeError(
        "Unable to load XInputGetState: "
        + "; ".join(errors)
    )


def xinput_states(get_state) -> dict[int, int]:
    result: dict[int, int] = {}
    for index in range(4):
        state = XINPUT_STATE()
        if int(get_state(index, ctypes.byref(state))) == 0:
            result[index] = int(state.Gamepad.wButtons)
    return result


def wait_for_slots(
    get_state,
    expected: set[int],
    timeout: float = 4.0,
) -> set[int]:
    deadline = time.monotonic() + timeout
    current: set[int] = set()
    while time.monotonic() < deadline:
        current = set(xinput_states(get_state))
        if current == expected:
            return current
        time.sleep(0.05)
    return current


def retroarch_running() -> bool:
    if os.name != "nt":
        return False

    completed = subprocess.run(
        [
            "tasklist",
            "/FI",
            "IMAGENAME eq retroarch.exe",
            "/FO",
            "CSV",
            "/NH",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return "retroarch.exe" in (completed.stdout or "").casefold()


def free_udp_port() -> int:
    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM,
    )
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def send_phi1(
    sock: socket.socket,
    port: int,
    sequence: int,
    player: int,
    buttons: int,
) -> None:
    data = PACKET.pack(
        b"PHI1",
        1,
        player,
        0,
        sequence,
        int(time.monotonic_ns() // 1000),
        buttons,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    sock.sendto(
        data,
        ("127.0.0.1", port),
    )


def format_slots(slots: set[int]) -> str:
    if not slots:
        return "none"
    return ", ".join(str(slot + 1) for slot in sorted(slots))


def write_result(payload: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        "PrivyHub Phase A four-player base-slot probe",
        f"Generated: {payload['generated']}",
        f"Classification: {payload['classification']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
        f"Bridge MAX_PLAYERS: {payload.get('bridge_max_players', 'unknown')}",
        f"PHI1 packet bytes: {payload.get('packet_bytes', 'unknown')}",
        f"XInput DLL: {payload.get('xinput_dll', 'unknown')}",
        f"Baseline occupied XInput slots: {payload.get('baseline_slots', 'unknown')}",
        f"Slots present after bridge start: {payload.get('started_slots', 'unknown')}",
        f"Synthetic face buttons by slot: {payload.get('observed_faces', 'unknown')}",
        f"Expected face buttons by slot: {payload.get('expected_faces', 'unknown')}",
        f"ViGEm updates by player: {payload.get('updates_by_player', 'unknown')}",
        f"Packets received: {payload.get('packets_received', 'unknown')}",
        f"Lost packets: {payload.get('lost_packets', 'unknown')}",
        f"Rejected packets: {payload.get('rejected_packets', 'unknown')}",
        f"Bad packets: {payload.get('bad_packets', 'unknown')}",
        f"Neutral after synthetic release: {payload.get('neutral_after_release', 'unknown')}",
        f"Slots restored after stop: {payload.get('slots_restored_after_stop', 'unknown')}",
    ]

    detail = str(payload.get("detail", "")).strip()
    if detail:
        lines += ["", "=== DETAIL ===", detail]

    LOG_PATH.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    JSON_PATH.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def self_test() -> int:
    assert PACKET.size == 36
    packed = PACKET.pack(
        b"PHI1",
        1,
        3,
        0,
        123,
        456,
        0x8000,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    assert len(packed) == 36
    unpacked = PACKET.unpack(packed)
    assert unpacked[0] == b"PHI1"
    assert unpacked[1] == 1
    assert unpacked[2] == 3
    assert face_name(0x1000) == "A"
    assert face_name(0x2000) == "B"
    assert face_name(0x4000) == "X"
    assert face_name(0x8000) == "Y"
    assert format_slots(set()) == "none"
    assert format_slots({0, 1, 2, 3}) == "1, 2, 3, 4"
    print("SELF-TEST PASSED")
    return 0


def run_probe() -> int:
    payload: dict[str, Any] = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "classification": "PROBE_FAILED",
        "packet_bytes": PACKET.size,
    }

    bridge = None
    sender = None
    get_state = None
    baseline_slots: set[int] = set()

    try:
        if os.name != "nt":
            raise RuntimeError(
                "Four-player base-slot runtime probe requires Windows."
            )

        if retroarch_running():
            payload["classification"] = "BLOCKED_RETROARCH_RUNNING"
            payload["detail"] = (
                "RetroArch is running. End the game before this isolated slot probe."
            )
            return 2

        get_state, dll_name = load_xinput()
        payload["xinput_dll"] = dll_name

        baseline_slots = set(xinput_states(get_state))
        payload["baseline_slots"] = format_slots(baseline_slots)

        if baseline_slots:
            payload["classification"] = "BLOCKED_EXISTING_XINPUT_SLOTS"
            payload["detail"] = (
                "One or more XInput slots were already occupied before the isolated "
                "probe. Stop any active companion controller bridge and disconnect "
                "host-side XInput controllers, then rerun."
            )
            return 2

        sys.path.insert(0, str(PROJECT_ROOT))
        from companion.native_session_io import NativeControllerBridge

        payload["bridge_max_players"] = NativeControllerBridge.MAX_PLAYERS
        if NativeControllerBridge.MAX_PLAYERS != 4:
            payload["classification"] = "WRONG_PRODUCTION_STATE"
            payload["detail"] = (
                "NativeControllerBridge.MAX_PLAYERS is not 4."
            )
            return 3
        if NativeControllerBridge.PACKET.size != 36:
            payload["classification"] = "WRONG_PROTOCOL_STATE"
            payload["detail"] = (
                "NativeControllerBridge PHI1 packet size is not 36 bytes."
            )
            return 3

        port = free_udp_port()
        bridge = NativeControllerBridge(PROJECT_ROOT)
        start_status = bridge.start(
            client_ip="127.0.0.1",
            port=port,
        )

        started_slots = wait_for_slots(
            get_state,
            {0, 1, 2, 3},
        )
        payload["started_slots"] = format_slots(started_slots)
        payload["bridge_start_active"] = bool(
            start_status.get("active", False)
        )
        payload["bridge_start_players"] = int(
            start_status.get("players", 0)
        )

        sender = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sequence = 0
        for _ in range(30):
            for player, buttons in enumerate(FACE_BUTTONS):
                send_phi1(
                    sender,
                    port,
                    sequence,
                    player,
                    buttons,
                )
                sequence = (sequence + 1) & 0xFFFFFFFF
            time.sleep(0.008)

        observed_states = xinput_states(get_state)
        observed = [
            int(observed_states.get(index, 0)) & FACE_MASK
            for index in range(4)
        ]
        payload["observed_faces"] = ", ".join(
            f"slot {index + 1}={face_name(mask)}"
            for index, mask in enumerate(observed)
        )
        payload["expected_faces"] = (
            "slot 1=A, slot 2=B, slot 3=X, slot 4=Y"
        )

        status = bridge.status()
        payload["updates_by_player"] = list(
            status.get("vigem_updates_by_player", [])
        )
        payload["packets_received"] = int(
            status.get("packets_received", 0)
        )
        payload["lost_packets"] = int(
            status.get("lost_packets", 0)
        )
        payload["rejected_packets"] = int(
            status.get("rejected_packets", 0)
        )
        payload["bad_packets"] = int(
            status.get("bad_packets", 0)
        )

        for _ in range(12):
            for player in range(4):
                send_phi1(
                    sender,
                    port,
                    sequence,
                    player,
                    0,
                )
                sequence = (sequence + 1) & 0xFFFFFFFF
            time.sleep(0.008)

        neutral_deadline = time.monotonic() + 1.0
        neutral = False
        while time.monotonic() < neutral_deadline:
            states = xinput_states(get_state)
            neutral = all(
                (int(states.get(index, 0)) & FACE_MASK) == 0
                for index in range(4)
            )
            if neutral:
                break
            time.sleep(0.02)
        payload["neutral_after_release"] = neutral

        expected_updates = payload["updates_by_player"]
        route_ok = observed == FACE_BUTTONS
        update_ok = (
            isinstance(expected_updates, list)
            and len(expected_updates) == 4
            and all(int(value) > 0 for value in expected_updates)
        )
        counters_ok = (
            payload["rejected_packets"] == 0
            and payload["bad_packets"] == 0
            and payload["lost_packets"] == 0
        )
        start_ok = (
            payload["bridge_start_active"]
            and payload["bridge_start_players"] == 4
            and started_slots == {0, 1, 2, 3}
        )

        if start_ok and route_ok and update_ok and counters_ok and neutral:
            payload["classification"] = "FOUR_PLAYER_BASE_SLOTS_CONFIRMED"
        else:
            payload["classification"] = "FOUR_PLAYER_BASE_SLOT_MISMATCH"
            payload["detail"] = (
                "At least one raw slot, routing, counter, or neutralization "
                "measurement did not match the four-player base expectation."
            )

    except Exception as exc:
        payload["classification"] = "PROBE_FAILED"
        payload["detail"] = f"{type(exc).__name__}: {exc}"
    finally:
        if sender is not None:
            try:
                sender.close()
            except Exception:
                pass

        if bridge is not None:
            try:
                bridge.stop()
            except Exception as exc:
                existing = str(payload.get("detail", "")).strip()
                suffix = f"Bridge stop error: {type(exc).__name__}: {exc}"
                payload["detail"] = (
                    existing + "\n" + suffix
                    if existing
                    else suffix
                )

        if get_state is not None:
            restored = wait_for_slots(
                get_state,
                baseline_slots,
                timeout=4.0,
            ) == baseline_slots
            payload["slots_restored_after_stop"] = restored
            if (
                payload.get("classification")
                == "FOUR_PLAYER_BASE_SLOTS_CONFIRMED"
                and not restored
            ):
                payload["classification"] = "FOUR_PLAYER_BASE_SLOT_MISMATCH"
                payload["detail"] = (
                    "Synthetic routing passed, but XInput slots did not return "
                    "to the pre-probe baseline after bridge shutdown."
                )

        write_result(payload)

    print(f"Classification: {payload['classification']}")
    print(f"Log: {LOG_PATH}")
    return (
        0
        if payload["classification"] == "FOUR_PLAYER_BASE_SLOTS_CONFIRMED"
        else 2
    )


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    return run_probe()


if __name__ == "__main__":
    raise SystemExit(main())
