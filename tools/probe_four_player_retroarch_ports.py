#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import os
import re
import time
from pathlib import Path

FALLBACK_TEXT = 'Configured joypad driver "xinput" failed to initialise'
PORT_RE = re.compile(r"Xbox 360 Controller configured in port ([1-9][0-9]*)\.")
MAX_LOG_AGE_SECONDS = 900.0

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

def xinput_slots(get_state) -> list[int]:
    slots = []
    for index in range(4):
        state = XINPUT_STATE()
        if int(get_state(index, ctypes.byref(state))) == 0:
            slots.append(index + 1)
    return slots

def analyze_log_text(text: str) -> tuple[list[int], bool, list[str]]:
    ports = sorted({int(match.group(1)) for match in PORT_RE.finditer(text)})
    fallback = FALLBACK_TEXT in text
    relevant = []
    for raw in text.splitlines():
        line = raw.strip()
        if (
            "Xbox 360 Controller configured in port" in line
            or FALLBACK_TEXT in line
            or "joypad driver" in line.casefold()
        ):
            relevant.append(line)
    return ports, fallback, relevant[-40:]

def find_latest_game_log(root: Path) -> Path | None:
    log_root = root / "logs" / "games"
    if not log_root.is_dir():
        return None
    candidates = []
    for path in log_root.glob("*-game_*.log"):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        ports, fallback, relevant = analyze_log_text(text)
        if ports or fallback or relevant:
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime_ns)

def self_test() -> int:
    sample = "\n".join(
        [f"[INFO] Xbox 360 Controller configured in port {i}." for i in range(1, 5)]
    ) + "\n"
    ports, fallback, relevant = analyze_log_text(sample)
    assert ports == [1, 2, 3, 4]
    assert fallback is False
    assert len(relevant) == 4
    bad = sample + FALLBACK_TEXT + "\n"
    ports2, fallback2, _ = analyze_log_text(bad)
    assert ports2 == [1, 2, 3, 4]
    assert fallback2 is True
    print("SELF-TEST PASSED")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    out = root / "logs" / "games" / "four_player_retroarch_ports_probe.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "PrivyHub Phase A RetroArch four-player port enumeration probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
    ]
    classification = "RETROARCH_FOUR_PLAYER_PORTS_UNVERIFIED"
    try:
        get_state, dll_name = load_xinput()
        slots = xinput_slots(get_state)
        lines.append(f"XInput DLL: {dll_name}")
        lines.append("Live XInput slots during probe: " + (", ".join(map(str, slots)) if slots else "none"))

        log_path = find_latest_game_log(root)
        if log_path is None:
            lines.append("RetroArch game log: <not found>")
            classification = "RETROARCH_GAME_LOG_NOT_FOUND"
        else:
            stat = log_path.stat()
            age = max(0.0, time.time() - stat.st_mtime)
            text = log_path.read_text(encoding="utf-8", errors="replace")
            ports, fallback, relevant = analyze_log_text(text)
            rel = str(log_path.relative_to(root)).replace("\\", "/")
            lines.append(f"RetroArch game log: {rel}")
            lines.append(f"RetroArch game log age seconds: {age:.1f}")
            lines.append("Configured Xbox ports observed: " + (", ".join(map(str, ports)) if ports else "none"))
            for port in range(1, 5):
                lines.append(f"Port {port} Xbox autoconfig observed: {port in ports}")
            lines.append(f"XInput startup fallback observed: {fallback}")
            lines.append(f"Fresh log within {int(MAX_LOG_AGE_SECONDS)} seconds: {age <= MAX_LOG_AGE_SECONDS}")
            lines.append("Relevant RetroArch input lines:")
            if relevant:
                for item in relevant:
                    lines.append("  " + item)
            else:
                lines.append("  <none>")

            if slots != [1, 2, 3, 4]:
                classification = "RETROARCH_FOUR_PLAYER_HOST_SLOTS_INCOMPLETE"
            elif age > MAX_LOG_AGE_SECONDS:
                classification = "RETROARCH_FOUR_PLAYER_LOG_STALE"
            elif fallback:
                classification = "RETROARCH_FOUR_PLAYER_XINPUT_STARTUP_FALLBACK"
            elif all(port in ports for port in range(1, 5)):
                classification = "RETROARCH_FOUR_PLAYER_PORTS_CONFIRMED"
            else:
                classification = "RETROARCH_FOUR_PLAYER_PORTS_INCOMPLETE"
    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")
        classification = "RETROARCH_FOUR_PLAYER_PORTS_UNVERIFIED"

    lines.insert(2, f"Classification: {classification}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Classification: {classification}")
    print(f"Probe log: {out}")
    return 0 if classification == "RETROARCH_FOUR_PLAYER_PORTS_CONFIRMED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
