#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import socket
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "companion"))

from companion.games.emulator_manager import EmulatorManager
from companion.native_stream import NativeStreamManager

GAME_ID = "game_snes_84cbb2d09db83cb9"
GAME_REL = "games/snes/Donkey Kong Country (USA).sfc"
INPUT_PORT = 48102
APPIMAGE_REL = (
    "runtime/emulators/retroarch-nightly-20260907-linux/"
    "RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
)
CORES_REL = "runtime/emulators/retroarch/cores-linux"
PROBE_ROOT = ROOT / "logs" / "games" / "d076r1_managed_probe_runtime"
PROBE_CONFIG = PROBE_ROOT / "retroarch.cfg"
PROBE_DESCRIPTOR = PROBE_ROOT / "emulators_linux.json"
PROBE_SAVES = PROBE_ROOT / "saves"
PROBE_STATES = PROBE_ROOT / "states"
PHI1 = struct.Struct("<4sBBHIQIhhhhHH")
XUSB_A = 0x1000
XUSB_B = 0x2000
XUSB_X = 0x4000
XUSB_Y = 0x8000


def fail(message: str) -> None:
    print("probe_error=", message)
    raise RuntimeError(message)


def wait_for_state_file(timeout: float = 4.0) -> Path:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        matches = [
            p for p in PROBE_STATES.rglob("*")
            if p.is_file() and p.name.casefold().endswith(".state") and p.stat().st_size > 0
        ]
        if matches:
            return max(matches, key=lambda p: p.stat().st_mtime_ns)
        time.sleep(0.05)
    raise RuntimeError("Save hotkey did not create a non-zero isolated state file")


def latest_game_log(started_ns: int) -> Path | None:
    candidates = []
    for path in (ROOT / "logs" / "games").glob(f"*-{GAME_ID}.log"):
        try:
            if path.stat().st_mtime_ns >= started_ns:
                candidates.append(path)
        except OSError:
            continue
    return max(candidates, key=lambda p: p.stat().st_mtime_ns) if candidates else None


def wait_process_exit(manager: EmulatorManager, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        process = manager.process
        if process is None:
            return True
        if process.poll() is not None:
            manager.status()
            return True
        time.sleep(0.05)
    return False


def snapshot_generated_configs() -> dict[Path, bytes | None]:
    config_dir = ROOT / "data/games/retroarch/config"
    paths = [
        config_dir / "privyhub-session.cfg",
        config_dir / "privyhub-input.cfg",
    ]
    snap: dict[Path, bytes | None] = {}
    for path in paths:
        snap[path] = path.read_bytes() if path.is_file() else None
    return snap


def restore_generated_configs(snapshot: dict[Path, bytes | None]) -> None:
    for path, data in snapshot.items():
        if data is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)


print("=== PRIVYHUB D-076R1 MANAGED RETROARCH INTEGRATION PROBE ===")

game_path = ROOT / GAME_REL
appimage = ROOT / APPIMAGE_REL
core = ROOT / CORES_REL / "bsnes_libretro.so"
base_config = ROOT / "data/games/retroarch/retroarch.cfg"
descriptor = ROOT / "companion/games/config/emulators.json"
autoconfig = ROOT / "data/games/retroarch/autoconfig/udev"

for path, label in (
    (game_path, "real SNES content"),
    (appimage, "Linux RetroArch AppImage"),
    (core, "Linux bsnes core"),
    (base_config, "project RetroArch config"),
    (descriptor, "emulator descriptor"),
):
    if not path.is_file():
        fail(f"{label} missing: {path}")

config_text = base_config.read_text(encoding="utf-8-sig")
if 'input_joypad_driver = "udev"' not in config_text:
    fail("D-076 udev joypad configuration is missing")
if 'joypad_autoconfig_dir = "data/games/retroarch/autoconfig"' not in config_text:
    fail("portable D-076 project autoconfig setting is missing")
for player in range(1, 5):
    profile = autoconfig / f"PrivyHub Virtual Gamepad P{player}.cfg"
    if not profile.is_file():
        fail(f"missing D-076 RetroArch profile for P{player}")

# Production controller port must be free. Never kill another owner.
test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    test_socket.bind(("0.0.0.0", INPUT_PORT))
except OSError as exc:
    fail(f"UDP {INPUT_PORT} is already in use; stop the companion before this probe: {exc}")
finally:
    test_socket.close()

if PROBE_ROOT.exists():
    shutil.rmtree(PROBE_ROOT)
PROBE_SAVES.mkdir(parents=True, exist_ok=True)
PROBE_STATES.mkdir(parents=True, exist_ok=True)

lines = []
for raw in config_text.splitlines():
    if raw.startswith("savefile_directory = "):
        lines.append(f'savefile_directory = "{PROBE_SAVES}"')
    elif raw.startswith("savestate_directory = "):
        lines.append(f'savestate_directory = "{PROBE_STATES}"')
    else:
        lines.append(raw)
lines.extend([
    "",
    "# D-076R1 managed probe isolation",
    'audio_enable = "false"',
    'config_save_on_exit = "false"',
])
PROBE_CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")

payload = json.loads(descriptor.read_text(encoding="utf-8-sig"))
payload["retroarch"]["executable"] = APPIMAGE_REL
payload["retroarch"]["cores_directory"] = CORES_REL
payload["retroarch"]["config"] = str(PROBE_CONFIG.relative_to(ROOT)).replace("\\", "/")
for system in payload["systems"].values():
    core_name = system.get("core")
    if isinstance(core_name, str) and core_name.casefold().endswith(".dll"):
        system["core"] = core_name[:-4] + ".so"
PROBE_DESCRIPTOR.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

game = {
    "id": GAME_ID,
    "title": "Donkey Kong Country",
    "system": "snes",
    "relative_path": GAME_REL,
}

native_stream = NativeStreamManager(ROOT)
manager = EmulatorManager(ROOT, config_path=PROBE_DESCRIPTOR)
manager.set_hotkey_sender(native_stream.retroarch_hotkey)
sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sequence = 0
generated_snapshot = snapshot_generated_configs()
started_ns = time.time_ns()

try:
    controller = native_stream.ensure_game_controller("127.0.0.1")
    print("controller_preflight_active=", controller.get("active"))
    print("controller_backend=", controller.get("backend"))
    print("controller_players=", controller.get("players"))

    launch = manager.launch(game)
    print("launch_active=", launch.get("active"))
    print("launch_pid=", launch.get("pid"))
    print("launch_retroarch_state=", launch.get("retroarch_command_state"))
    if not launch.get("active"):
        fail("EmulatorManager launch did not become active")

    time.sleep(1.0)
    game_log = latest_game_log(started_ns)
    if game_log is None:
        fail("fresh managed RetroArch game log not found")
    log_text = game_log.read_text(encoding="utf-8", errors="replace")

    configured_ports = []
    for player in range(1, 5):
        marker = (
            f"[Autoconf] PrivyHub Virtual Gamepad P{player} "
            f"configured in port {player}."
        )
        configured = marker in log_text
        print(f"retroarch_p{player}_configured=", configured)
        if configured:
            configured_ports.append(player)
    print("retroarch_configured_ports=", configured_ports)
    if configured_ports != [1, 2, 3, 4]:
        fail("RetroArch did not configure P1-P4 in deterministic ports 1-4")

    # Prove the generated session config contains the absolute project-owned path.
    session_config = ROOT / "data/games/retroarch/config/privyhub-session.cfg"
    session_text = session_config.read_text(encoding="utf-8", errors="replace")
    expected_abs = str((ROOT / "data/games/retroarch/autoconfig").resolve()).replace("\\", "/")
    session_abs_ok = f'joypad_autoconfig_dir = "{expected_abs}"' in session_text
    print("session_autoconfig_absolute=", session_abs_ok)
    if not session_abs_ok:
        fail("generated Linux session config did not contain the absolute project autoconfig path")

    tests = [
        (0, XUSB_A, 255, 255),
        (1, XUSB_B, 255, 0),
        (2, XUSB_X, 0, 255),
        (3, XUSB_Y, 255, 255),
    ]
    for player, buttons, lt, rt in tests:
        sender.sendto(PHI1.pack(b"PHI1", 1, player, 0, sequence, 0, buttons, 12000, 14000, -12000, -14000, lt, rt), ("127.0.0.1", INPUT_PORT))
        sequence += 1
        time.sleep(0.05)
        sender.sendto(PHI1.pack(b"PHI1", 1, player, 0, sequence, 0, 0, 0, 0, 0, 0, 0, 0), ("127.0.0.1", INPUT_PORT))
        sequence += 1
        time.sleep(0.05)

    live_status = native_stream._session_io.controller.status()
    print("live_packets_received=", live_status.get("packets_received"))
    print("live_bad_packets=", live_status.get("bad_packets"))
    print("live_updates_by_player=", live_status.get("updates_by_player"))

    pause_result = native_stream.retroarch_hotkey("pause")
    pause_state = manager._wait_for_retroarch_state("PAUSED", timeout=2.5)
    print("pause_hotkey_state=", pause_state)
    print("pause_hotkey_edges=", pause_result.get("edge_sequence"))

    resume_result = native_stream.retroarch_hotkey("pause")
    resume_state = manager._wait_for_retroarch_state("PLAYING", timeout=2.5)
    print("resume_hotkey_state=", resume_state)
    print("resume_hotkey_edges=", resume_result.get("edge_sequence"))

    save_result = native_stream.retroarch_hotkey("save")
    saved_state = wait_for_state_file()
    print("save_hotkey_state_file=", str(saved_state.relative_to(PROBE_ROOT)))
    print("save_hotkey_state_size=", saved_state.stat().st_size)
    print("save_hotkey_edges=", save_result.get("edge_sequence"))

    native_stream.retroarch_hotkey("pause")
    manager._wait_for_retroarch_state("PAUSED", timeout=2.5)
    before_load_mtime = saved_state.stat().st_mtime_ns
    load_result = native_stream.retroarch_hotkey("load")
    time.sleep(0.75)
    after_load_exists = saved_state.is_file() and saved_state.stat().st_size > 0
    load_preserved = after_load_exists and saved_state.stat().st_mtime_ns == before_load_mtime
    print("load_hotkey_state_file_present=", after_load_exists)
    print("load_hotkey_preserved_state_file=", load_preserved)
    print("load_hotkey_edges=", load_result.get("edge_sequence"))

    stop_result = manager.stop()
    production_end_graceful = bool(stop_result.get("graceful"))
    print("production_end_graceful=", production_end_graceful)

    updates = live_status.get("updates_by_player") or []
    accepted = (
        controller.get("active") is True
        and controller.get("backend") == "linux_uinput"
        and configured_ports == [1, 2, 3, 4]
        and session_abs_ok
        and live_status.get("bad_packets") == 0
        and len(updates) == 4
        and all(value >= 2 for value in updates)
        and pause_state == "PAUSED"
        and resume_state == "PLAYING"
        and saved_state.is_file()
        and saved_state.stat().st_size > 0
        and after_load_exists
        and load_preserved
        and production_end_graceful
    )
    print("d076r1_managed_retroarch_validated=", accepted)
    if not accepted:
        fail("D-076R1 managed RetroArch acceptance conditions were not all met")

finally:
    sender.close()
    try:
        if manager.process is not None and manager.process.poll() is None:
            stop = manager.stop()
            print("fallback_manager_stop_graceful=", stop.get("graceful"))
    except Exception as exc:
        print("fallback_manager_stop_error=", str(exc))
    try:
        native_stream.end_game_session()
    except Exception as exc:
        print("controller_cleanup_error=", str(exc))
    time.sleep(0.25)
    after = native_stream._session_io.controller.status()
    print("controller_active_after_cleanup=", after.get("active"))
    names = []
    try:
        for node in sorted(Path("/sys/class/input").glob("event*")):
            name_path = node / "device/name"
            try:
                name = name_path.read_text().strip()
            except OSError:
                continue
            if name.startswith("PrivyHub Virtual Gamepad P"):
                names.append(name)
    except Exception as exc:
        print("cleanup_measurement_error=", str(exc))
    print("virtual_pads_after_cleanup=", names)
    restore_generated_configs(generated_snapshot)
    if PROBE_ROOT.exists():
        shutil.rmtree(PROBE_ROOT, ignore_errors=True)
    print("probe_runtime_directory_removed=", not PROBE_ROOT.exists())
