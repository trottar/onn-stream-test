#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    sys.path.insert(0, str(root))

    from companion.games.emulator_manager import (
        EmulatorManager,
    )

    profile_path = (
        root
        / "data"
        / "games"
        / "input_profiles.json"
    )
    config_path = (
        root
        / "data"
        / "games"
        / "retroarch"
        / "config"
        / "privyhub-input.cfg"
    )
    log_path = (
        root
        / "logs"
        / "games"
        / "a8_2_input_adapter_probe.txt"
    )
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    originals = {}
    for path in (
        profile_path,
        config_path,
    ):
        originals[path] = (
            path.read_bytes()
            if path.is_file()
            else None
        )

    lines = [
        "PrivyHub A8.2 RetroArch input adapter probe",
        "Purpose: validate session-only generated binds and exact restoration.",
    ]
    result = "FAIL"
    restored = False

    try:
        manager = EmulatorManager(
            root
        )
        runtime = (
            manager._runtime_details()
        )
        game = {
            "id": "game_a8_adapter_probe_000001",
            "system": "ps1",
        }

        created = (
            manager.create_input_profile(
                "A8 Adapter Probe",
                {
                    "player1": {
                        "a": "b",
                        "b": "a",
                        "left_x": "right_x",
                    },
                    "player2": {
                        "start": "select",
                    },
                },
            )
        )
        profile_id = str(
            created["id"]
        )
        manager.assign_input_profile(
            game,
            profile_id,
        )

        generated_path, metadata = (
            manager._prepare_input_override(
                game,
                runtime,
            )
        )
        text = generated_path.read_text(
            encoding="utf-8"
        )

        expected = (
            'input_player1_a_btn = "1"',
            'input_player1_a_axis = "nul"',
            'input_player1_b_btn = "0"',
            'input_player1_b_axis = "nul"',
            'input_player1_l_x_plus_axis = "+2"',
            'input_player1_l_x_minus_axis = "-2"',
            'input_player2_start_btn = "7"',
            'input_player2_start_axis = "nul"',
        )
        missing = [
            item
            for item in expected
            if item not in text
        ]
        if missing:
            raise RuntimeError(
                "Generated config is missing expected binds: "
                + ", ".join(missing)
            )

        if metadata.get(
            "input_profile_id"
        ) != profile_id:
            raise RuntimeError(
                "Generated metadata did not report the assigned profile"
            )

        if metadata.get(
            "input_profile_source"
        ) != "game_assignment":
            raise RuntimeError(
                "Generated metadata did not report game_assignment"
            )

        lines.append(
            "Assigned profile generated expected P1/P2 binds: PASS"
        )
        lines.append(
            "Generated profile metadata: PASS"
        )

        manager.assign_input_profile(
            game,
            "default",
        )
        default_path, default_metadata = (
            manager._prepare_input_override(
                game,
                runtime,
            )
        )
        default_text = default_path.read_text(
            encoding="utf-8"
        )

        if (
            "PrivyHub A8.2 named gameplay input profile"
            in default_text
        ):
            raise RuntimeError(
                "Default profile unexpectedly emitted explicit A8 binds"
            )

        if default_metadata.get(
            "input_profile_id"
        ) != "default":
            raise RuntimeError(
                "Default profile metadata is incorrect"
            )

        lines.append(
            "Default profile preserves RetroArch autoconfig: PASS"
        )

        incompatible = (
            manager.create_input_profile(
                "A8 Invalid Runtime",
                {
                    "player1": {
                        "left_x": "a",
                    },
                },
            )
        )
        manager.assign_input_profile(
            game,
            str(
                incompatible[
                    "id"
                ]
            ),
        )

        rejected = False
        try:
            manager._prepare_input_override(
                game,
                runtime,
            )
        except Exception:
            rejected = True

        if not rejected:
            raise RuntimeError(
                "Incompatible analog mapping did not fail closed"
            )

        lines.append(
            "Incompatible runtime mapping fails closed: PASS"
        )
        result = "PASS"

    except Exception as exc:
        lines.append(
            f"ERROR: {type(exc).__name__}: {exc}"
        )

    finally:
        restore_ok = True
        for path, original in originals.items():
            try:
                if original is None:
                    path.unlink(
                        missing_ok=True
                    )
                else:
                    path.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )
                    path.write_bytes(
                        original
                    )
            except Exception as exc:
                restore_ok = False
                lines.append(
                    "RESTORE ERROR: "
                    f"{path}: {type(exc).__name__}: {exc}"
                )

        restored = restore_ok and all(
            (
                path.read_bytes() == original
                if original is not None
                and path.is_file()
                else (
                    not path.exists()
                    if original is None
                    else False
                )
            )
            for path, original in originals.items()
        )

    lines.append(
        f"Result: {result}"
    )
    lines.append(
        "Files restored: "
        + str(
            restored
        )
    )

    log_path.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

    print(
        "\n".join(lines)
    )
    print(
        f"Probe log: {log_path}"
    )

    return (
        0
        if result == "PASS"
        and restored
        else 1
    )

if __name__ == "__main__":
    raise SystemExit(main())
