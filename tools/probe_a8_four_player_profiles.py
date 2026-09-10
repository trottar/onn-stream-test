#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:8765"
EXPECTED_PLAYERS = [
    "player1",
    "player2",
    "player3",
    "player4",
]


def request_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(BASE + path, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except OSError as exc:
        raise RuntimeError(
            "Companion API is unavailable on localhost:8765. "
            "Restart the companion after installing the patch."
        ) from exc
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise RuntimeError("Companion API returned a non-object payload")
    return payload


def complete_default(capabilities: dict[str, Any]) -> dict[str, dict[str, str]]:
    players = capabilities.get("players")
    default = capabilities.get("editor_default_mapping")
    targets = capabilities.get("editor_targets")
    if players != EXPECTED_PLAYERS:
        raise RuntimeError(f"Unexpected players capability: {players!r}")
    if not isinstance(default, dict) or not isinstance(targets, list) or not targets:
        raise RuntimeError("Directional editor capabilities are incomplete")
    mapping = {}
    for player in EXPECTED_PLAYERS:
        mapping[player] = {
            str(target): str(default[str(target)])
            for target in targets
        }
    return mapping


def direct_generation_test(project_root: Path) -> dict[str, Any]:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from companion.games.emulator_manager import EmulatorManager

    if EmulatorManager.INPUT_PROFILE_SCHEMA != 1:
        raise RuntimeError("Input profile schema unexpectedly changed")
    if list(EmulatorManager.INPUT_PROFILE_PLAYERS) != EXPECTED_PLAYERS:
        raise RuntimeError(
            "Installed EmulatorManager does not expose four input-profile players"
        )

    legacy = EmulatorManager._normalize_input_mapping(
        {
            "player1": {"a": "b", "b": "a"},
            "player2": {"a": "b", "b": "a"},
        }
    )
    if list(legacy) != EXPECTED_PLAYERS:
        raise RuntimeError("Legacy P1/P2 profile did not normalize to four players")
    if legacy["player3"] != {} or legacy["player4"] != {}:
        raise RuntimeError("Legacy P3/P4 defaults were not preserved as empty maps")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        config_path = root / "companion" / "games" / "config" / "emulators.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config = {
            "retroarch": {
                "executable": "runtime/retroarch/retroarch.exe",
                "config": "runtime/retroarch/retroarch.cfg",
                "cores_directory": "runtime/retroarch/cores",
            },
            "systems": {
                "probe": {
                    "controls": {
                        "analog_dpad": "none",
                    }
                }
            },
        }
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8",
        )

        manager = EmulatorManager(root)
        caps = manager.input_profiles()["capabilities"]
        mapping = complete_default(caps)

        # Make P3/P4 explicit and distinguishable while preserving one-to-one
        # source use within each player mapping.
        mapping["player3"]["a"] = "a"
        mapping["player3"]["b"] = "b"
        mapping["player4"]["x"] = "x"
        mapping["player4"]["y"] = "y"

        created = manager.create_input_profile(
            "Four Player Probe",
            mapping,
        )
        game = {
            "id": "game_probe_four_player",
            "title": "Four Player Probe",
            "system": "probe",
            "relative_path": "games/probe.rom",
        }
        effective = manager.assign_input_profile(
            game,
            str(created["id"]),
        )
        public_mapping = effective["profile"]["mapping"]
        if list(public_mapping) != EXPECTED_PLAYERS:
            raise RuntimeError("Stored public profile did not retain four players")

        path, metadata = manager._prepare_input_override(
            game,
            {"config": config},
        )
        text = path.read_text(encoding="utf-8")

        expected_lines = [
            'input_player1_analog_dpad_mode = "0"',
            'input_player2_analog_dpad_mode = "0"',
            'input_player3_analog_dpad_mode = "0"',
            'input_player4_analog_dpad_mode = "0"',
            'input_player3_a_btn = "0"',
            'input_player3_b_btn = "1"',
            'input_player4_x_btn = "2"',
            'input_player4_y_btn = "3"',
        ]
        missing = [line for line in expected_lines if line not in text]
        if missing:
            raise RuntimeError(
                "Generated four-player RetroArch override is incomplete: "
                + "; ".join(missing)
            )
        if "input_player5_" in text:
            raise RuntimeError("Generated override unexpectedly contains Player 5")

        return {
            "legacy_p1_p2_normalized_to_four": True,
            "schema": EmulatorManager.INPUT_PROFILE_SCHEMA,
            "players": list(EmulatorManager.INPUT_PROFILE_PLAYERS),
            "generated_override_lines": len(text.splitlines()),
            "profile_override_count": int(metadata["input_profile_override_count"]),
            "p3_explicit_bind": True,
            "p4_explicit_bind": True,
            "analog_dpad_players_1_4": True,
        }


def self_test() -> int:
    capabilities = {
        "players": EXPECTED_PLAYERS,
        "editor_targets": ["a", "b"],
        "editor_default_mapping": {"a": "b", "b": "a"},
    }
    mapping = complete_default(capabilities)
    assert list(mapping) == EXPECTED_PLAYERS
    assert mapping["player3"] == {"a": "b", "b": "a"}
    assert mapping["player4"] == {"a": "b", "b": "a"}
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
    log_path = root / "logs" / "games" / "a8_four_player_profiles_probe.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "PrivyHub Phase A A8 four-player profile/backend probe",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== RAW MEASUREMENTS ===",
    ]
    classification = "A8_FOUR_PLAYER_PROFILE_BACKEND_NOT_CONFIRMED"

    try:
        payload = request_json("/plugins/games/input-profiles")
        capabilities = payload.get("capabilities")
        if not isinstance(capabilities, dict):
            raise RuntimeError("Live companion did not return input-profile capabilities")
        players = capabilities.get("players")
        if players != EXPECTED_PLAYERS:
            raise RuntimeError(f"Live companion players capability: {players!r}")

        profiles = payload.get("profiles")
        if not isinstance(profiles, list):
            raise RuntimeError("Live companion profiles entry is not an array")
        profile_player_keys_ok = True
        for profile in profiles:
            if not isinstance(profile, dict):
                profile_player_keys_ok = False
                break
            mapping = profile.get("mapping")
            if not isinstance(mapping, dict) or list(mapping) != EXPECTED_PLAYERS:
                profile_player_keys_ok = False
                break
        if not profile_player_keys_ok:
            raise RuntimeError("At least one live profile did not expose Player 1-4 mapping keys")

        direct = direct_generation_test(root)

        lines.extend(
            [
                "Live companion schema: " + str(payload.get("schema")),
                "Live companion players: " + ", ".join(players),
                "Live profile count inspected: " + str(len(profiles)),
                "Every live profile exposes P1-P4 keys: True",
                "Legacy P1/P2 profile normalizes to four: "
                + str(direct["legacy_p1_p2_normalized_to_four"]),
                "Direct installed backend schema: " + str(direct["schema"]),
                "Direct installed backend players: " + ", ".join(direct["players"]),
                "Generated P1-P4 analog-D-pad lines: "
                + str(direct["analog_dpad_players_1_4"]),
                "Generated explicit Player 3 bind: " + str(direct["p3_explicit_bind"]),
                "Generated explicit Player 4 bind: " + str(direct["p4_explicit_bind"]),
                "Generated profile override line count: "
                + str(direct["profile_override_count"]),
                "User profile storage modified by probe: False",
            ]
        )

        print("")
        print("A8 FOUR-PLAYER UI CHECK")
        print("")
        print("On the onn, open an existing custom Input Profile.")
        print("Confirm its actions expose Edit Player 1, 2, 3, and 4 Mapping.")
        print("Open Player 3 or Player 4 and confirm the editor shows:")
        print("  Copy Mapping From Another Player")
        print("Cancel the editor; you do not need to save any mapping.")
        print("")
        answer = input("Were both UI checks observed? [y/n]: ").strip().casefold()
        ui_confirmed = answer in {"y", "yes"}
        lines.append("Android Player 1-4 edit actions observed: " + str(ui_confirmed))
        lines.append(
            "Android copy-from-another-player control observed: "
            + str(ui_confirmed)
        )

        classification = (
            "A8_FOUR_PLAYER_PROFILE_EDITOR_CONFIRMED"
            if ui_confirmed
            else "A8_FOUR_PLAYER_PROFILE_BACKEND_ONLY"
        )
    except Exception as exc:
        lines.append(f"ERROR: {type(exc).__name__}: {exc}")

    lines.insert(1, "Classification: " + classification)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Classification: " + classification)
    print("Probe log: " + str(log_path))
    return 0 if classification == "A8_FOUR_PLAYER_PROFILE_EDITOR_CONFIRMED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
