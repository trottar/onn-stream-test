#!/usr/bin/env python3
from __future__ import annotations

import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPANION = ROOT / "companion"
if str(COMPANION) not in sys.path:
    sys.path.insert(0, str(COMPANION))

from native_session_io import NativeControllerBridge  # noqa: E402


def choose_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def privyhub_js_names() -> list[str]:
    names: list[str] = []
    for path in sorted(Path("/sys/class/input").glob("js*/device/name")):
        try:
            name = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if name.startswith("PrivyHub Virtual Gamepad P"):
            names.append(name)
    return names


def wait_names(expected: int, timeout: float = 2.0) -> list[str]:
    deadline = time.monotonic() + timeout
    latest: list[str] = []
    while time.monotonic() < deadline:
        latest = privyhub_js_names()
        if len(latest) == expected:
            return latest
        time.sleep(0.05)
    return latest


def main() -> int:
    bridge = NativeControllerBridge(ROOT)
    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = choose_port()
    result = False

    print("=== PRIVYHUB D-076 LINUX CONTROLLER RUNTIME PROBE ===")

    try:
        start = bridge.start(
            client_ip="127.0.0.1",
            port=port,
        )
        names = wait_names(4)

        print("start_active=", start.get("active"))
        print("controller_backend=", start.get("backend"))
        print("controller_sink=", start.get("sink"))
        print("virtual_pad_count=", len(names))
        print("virtual_pad_names=", names)

        for player in range(bridge.MAX_PLAYERS):
            payload = bridge.PACKET.pack(
                bridge.MAGIC,
                bridge.VERSION,
                player,
                0,
                player,
                0,
                bridge.XUSB_A,
                1000 + player,
                2000 + player,
                3000 + player,
                4000 + player,
                64 + player,
                128 + player,
            )
            sender.sendto(payload, ("127.0.0.1", port))

        time.sleep(0.12)

        pulse = bridge.pulse_retroarch_hotkey(
            "save",
            player=0,
            hold_seconds=0.08,
            modifier_settle_seconds=0.04,
            release_gap_seconds=0.03,
        )

        status = bridge.status()
        updates = list(status.get("updates_by_player", []))
        legacy_updates = list(status.get("vigem_updates_by_player", []))

        print("packets_received=", status.get("packets_received"))
        print("bad_packets=", status.get("bad_packets"))
        print("rejected_packets=", status.get("rejected_packets"))
        print("updates_by_player=", updates)
        print("legacy_updates_by_player=", legacy_updates)
        print("hotkey_action=", pulse.get("action"))
        print("hotkey_edge_sequence=", pulse.get("edge_sequence"))

        result = bool(
            start.get("active") is True
            and start.get("backend") == "linux_uinput"
            and start.get("sink") == "uinput_quad"
            and names
            == [
                "PrivyHub Virtual Gamepad P1",
                "PrivyHub Virtual Gamepad P2",
                "PrivyHub Virtual Gamepad P3",
                "PrivyHub Virtual Gamepad P4",
            ]
            and int(status.get("packets_received", 0)) == 4
            and int(status.get("bad_packets", 0)) == 0
            and int(status.get("rejected_packets", 0)) == 0
            and updates == [1, 1, 1, 1]
            and legacy_updates == updates
            and pulse.get("edge_sequence")
            == [
                "modifier_down",
                "action_down",
                "action_up",
                "modifier_up",
            ]
        )
    finally:
        sender.close()
        bridge.stop()
        remaining = wait_names(0)
        print("virtual_pads_after_stop=", remaining)
        print("cleanup_validated=", remaining == [])
        result = result and remaining == []

    print("d076_isolated_runtime_validated=", result)
    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
