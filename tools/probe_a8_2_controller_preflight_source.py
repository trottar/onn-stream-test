#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path

MARKER = "# PRIVYHUB_A8_PATCH_02B_CONTROLLER_PREFLIGHT_ORDER_V1"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    games = root / "companion" / "plugins" / "games.py"
    log = root / "logs" / "games" / "a8_2_controller_preflight_source_probe.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "PrivyHub A8.2 controller-preflight source probe",
        "Purpose: verify controller readiness occurs before normal RetroArch launch.",
    ]
    result = "FAIL"
    try:
        text = games.read_text(encoding="utf-8-sig")
        marker_count = text.count(MARKER)
        marker = text.find(MARKER)
        ensure = text.find("self._native_stream.ensure_game_controller(client_ip)", marker)
        launch = text.find("payload = self.handle_post(action, raw_query)", marker)
        pause = text.find("paused = self._emulator.pause()", marker)
        ok = marker_count == 1 and 0 <= marker < ensure < launch < pause
        lines.append(f"Marker count: {marker_count}")
        lines.append(f"Controller preflight before launch: {ok}")
        if not ok:
            raise RuntimeError("Controller-preflight ordering invariant failed")
        result = "PASS"
    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")
    lines.append(f"Result: {result}")
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Result: {result}")
    print(f"Probe log: {log}")
    return 0 if result == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
