#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companion.games.emulator_manager import EmulatorManager  # noqa: E402

EXPECTED_APPIMAGE = (
    "runtime/emulators/retroarch-nightly-20260907-linux/"
    "RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
)
EXPECTED_CORES_DIR = "runtime/emulators/retroarch/cores-linux"
EXPECTED_LINUX_CORES = {
    "nes": "fceumm_libretro.so",
    "snes": "bsnes_libretro.so",
    "genesis": "blastem_libretro.so",
    "ps1": "mednafen_psx_hw_libretro.so",
}
EXPECTED_WINDOWS_CORES = {
    "nes": "fceumm_libretro.dll",
    "snes": "bsnes_libretro.dll",
    "genesis": "blastem_libretro.dll",
    "ps1": "mednafen_psx_hw_libretro.dll",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def relative_to_root(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def validate_effective_runtime(
    manager: EmulatorManager,
    *,
    root: Path,
    require_files: bool,
) -> dict[str, object]:
    runtime = manager._runtime_details()
    effective = runtime["config"]
    systems = effective.get("systems")
    if not isinstance(systems, dict):
        fail("effective systems config is missing")

    executable_rel = relative_to_root(root, runtime["executable"])
    cores_rel = relative_to_root(root, runtime["cores_directory"])
    selected_cores = {
        system_id: (systems.get(system_id) or {}).get("core")
        for system_id in EXPECTED_LINUX_CORES
    }

    if executable_rel != EXPECTED_APPIMAGE:
        fail(f"normal Linux runtime selected unexpected executable: {executable_rel}")
    if cores_rel != EXPECTED_CORES_DIR:
        fail(f"normal Linux runtime selected unexpected cores directory: {cores_rel}")
    if selected_cores != EXPECTED_LINUX_CORES:
        fail(f"normal Linux runtime selected unexpected cores: {selected_cores!r}")

    status = manager.status()
    if require_files:
        if status.get("ready") is not True:
            fail(f"normal Linux EmulatorManager is not ready: {status.get('runtime_error')!r}")
        if status.get("retroarch_installed") is not True:
            fail("Linux RetroArch AppImage is not installed at the selected normal path")
        if status.get("retroarch_configured") is not True:
            fail("project-owned RetroArch config is not present at the selected normal path")
        if status.get("missing_cores") != []:
            fail(f"selected Linux runtime has missing cores: {status.get('missing_cores')!r}")
        status_cores = status.get("cores") or {}
        for system_id, expected_core in EXPECTED_LINUX_CORES.items():
            item = status_cores.get(system_id) or {}
            if item.get("core") != expected_core or item.get("installed") is not True:
                fail(f"status did not confirm installed Linux core for {system_id}: {item!r}")

    return {
        "executable": executable_rel,
        "cores_directory": cores_rel,
        "cores": selected_cores,
        "ready": bool(status.get("ready")),
    }


def fixture_probe(source_config: Path) -> None:
    payload = json.loads(source_config.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="privyhub_d077_fixture_") as temp_dir:
        root = Path(temp_dir)
        fixture_config = root / "emulators.json"
        fixture_config.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        # Linux selected runtime fixture.
        appimage = root / EXPECTED_APPIMAGE
        appimage.parent.mkdir(parents=True, exist_ok=True)
        appimage.write_bytes(b"fixture")
        cores_dir = root / EXPECTED_CORES_DIR
        cores_dir.mkdir(parents=True, exist_ok=True)
        for core in EXPECTED_LINUX_CORES.values():
            (cores_dir / core).write_bytes(b"fixture")
        retroarch_cfg = root / "data/games/retroarch/retroarch.cfg"
        retroarch_cfg.parent.mkdir(parents=True, exist_ok=True)
        retroarch_cfg.write_text("# fixture\n", encoding="utf-8")

        manager = EmulatorManager(root, config_path=fixture_config)
        linux = validate_effective_runtime(manager, root=root, require_files=True)

        # The base descriptor remains the Windows contract. Force only the
        # selector key in this isolated fixture; no production global is changed.
        windows_exe = root / "runtime/emulators/retroarch-nightly-20260907/retroarch.exe"
        windows_exe.parent.mkdir(parents=True, exist_ok=True)
        windows_exe.write_bytes(b"fixture")
        windows_cores = root / "runtime/emulators/retroarch/cores"
        windows_cores.mkdir(parents=True, exist_ok=True)
        for core in EXPECTED_WINDOWS_CORES.values():
            (windows_cores / core).write_bytes(b"fixture")

        manager._runtime_platform_key = lambda: "windows"  # type: ignore[method-assign]
        windows_runtime = manager._runtime_details()
        windows_systems = windows_runtime["config"]["systems"]
        windows_selected = {
            system_id: windows_systems[system_id]["core"]
            for system_id in EXPECTED_WINDOWS_CORES
        }
        if relative_to_root(root, windows_runtime["executable"]) != (
            "runtime/emulators/retroarch-nightly-20260907/retroarch.exe"
        ):
            fail("Windows base executable changed during Linux override selection")
        if windows_selected != EXPECTED_WINDOWS_CORES:
            fail(f"Windows base core mapping changed: {windows_selected!r}")

        print("fixture_linux_executable=", linux["executable"])
        print("fixture_linux_cores=", linux["cores"])
        print("fixture_windows_cores=", windows_selected)
        print("D077_FIXTURE_PASS")


def live_probe() -> None:
    if not sys.platform.startswith("linux"):
        fail(f"D-077 live probe must run on Linux, not {sys.platform!r}")

    descriptor = ROOT / "companion/games/config/emulators.json"
    raw = json.loads(descriptor.read_text(encoding="utf-8"))
    base_retroarch = raw.get("retroarch") or {}
    if base_retroarch.get("executable") != (
        "runtime/emulators/retroarch-nightly-20260907/retroarch.exe"
    ):
        fail("tracked Windows base executable was not preserved")
    for system_id, expected_core in EXPECTED_WINDOWS_CORES.items():
        if ((raw.get("systems") or {}).get(system_id) or {}).get("core") != expected_core:
            fail(f"tracked Windows base core changed for {system_id}")

    manager = EmulatorManager(ROOT)
    result = validate_effective_runtime(manager, root=ROOT, require_files=True)
    expected_config_path = (ROOT / "companion/games/config/emulators.json").resolve()
    if manager.config_path != expected_config_path:
        fail("normal default EmulatorManager is not using the production descriptor")

    print("normal_config= companion/games/config/emulators.json")
    print("selected_executable=", result["executable"])
    print("selected_cores_directory=", result["cores_directory"])
    print("selected_cores=", result["cores"])
    print("ready=", result["ready"])
    print("D077_LINUX_RUNTIME_SELECTION_READY")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", action="store_true")
    args = parser.parse_args()
    try:
        source_config = ROOT / "companion/games/config/emulators.json"
        if args.fixture:
            fixture_probe(source_config)
        else:
            live_probe()
        return 0
    except Exception as exc:
        print("D077_FAIL:", str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
