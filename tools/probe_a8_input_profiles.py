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
        EmulatorError,
        EmulatorManager,
    )

    profile_path = (
        root
        / "data"
        / "games"
        / "input_profiles.json"
    )
    log_path = (
        root
        / "logs"
        / "games"
        / "a8_input_profiles_probe.txt"
    )
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_exists = (
        profile_path.is_file()
    )
    original_bytes = (
        profile_path.read_bytes()
        if original_exists
        else None
    )

    result = "FAIL"
    restored = False
    lines = [
        "PrivyHub A8.1 input profile storage probe",
        "Purpose: validate schema, CRUD, assignment, fail-closed behavior, and exact restoration.",
    ]

    try:
        manager = EmulatorManager(
            root
        )
        fake_game = {
            "id": "game_a8_probe_000001",
        }

        catalog = (
            manager.input_profiles()
        )
        assert catalog[
            "schema"
        ] == 1
        assert len(
            catalog[
                "profiles"
            ]
        ) >= 1
        default = (
            catalog[
                "profiles"
            ][0]
        )
        assert default[
            "id"
        ] == "default"
        assert default[
            "builtin"
        ] is True
        assert default[
            "mapping"
        ] == {
            "player1": {},
            "player2": {},
        }
        lines.append(
            "Default virtual profile: PASS"
        )

        created = (
            manager.create_input_profile(
                "A8 Probe",
                {
                    "player1": {
                        "a": "b",
                        "b": "a",
                    },
                    "player2": {},
                },
            )
        )
        profile_id = str(
            created[
                "id"
            ]
        )
        assert profile_id.startswith(
            "profile_"
        )
        lines.append(
            "Create custom profile: PASS"
        )

        assigned = (
            manager.assign_input_profile(
                fake_game,
                profile_id,
            )
        )
        assert assigned[
            "profile_id"
        ] == profile_id
        assert assigned[
            "source"
        ] == "game_assignment"
        lines.append(
            "Per-game assignment: PASS"
        )

        rejected_delete = False
        try:
            manager.delete_input_profile(
                profile_id
            )
        except EmulatorError:
            rejected_delete = True

        assert rejected_delete
        lines.append(
            "Assigned deletion rejection: PASS"
        )

        updated = (
            manager.update_input_profile(
                profile_id,
                name=(
                    "A8 Probe Updated"
                ),
                mapping={
                    "player1": {
                        "x": "y",
                        "y": "x",
                    },
                    "player2": {
                        "a": "b",
                    },
                },
                mapping_supplied=True,
            )
        )
        assert updated[
            "name"
        ] == "A8 Probe Updated"
        lines.append(
            "Update profile: PASS"
        )

        duplicate_source_rejected = (
            False
        )
        try:
            manager.create_input_profile(
                "Bad Mapping",
                {
                    "player1": {
                        "a": "b",
                        "x": "b",
                    }
                },
            )
        except EmulatorError:
            duplicate_source_rejected = (
                True
            )

        assert duplicate_source_rejected
        lines.append(
            "Malformed/conflicting mapping fail-closed: PASS"
        )

        cleared = (
            manager.assign_input_profile(
                fake_game,
                "default",
            )
        )
        assert cleared[
            "profile_id"
        ] == "default"
        assert cleared[
            "source"
        ] == "default"
        lines.append(
            "Default reassignment clears override: PASS"
        )

        deleted = (
            manager.delete_input_profile(
                profile_id
            )
        )
        assert deleted[
            "deleted"
        ] is True
        lines.append(
            "Delete unassigned profile: PASS"
        )

        result = "PASS"

    except Exception as exc:
        lines.append(
            f"ERROR: {type(exc).__name__}: {exc}"
        )

    finally:
        try:
            if original_exists:
                profile_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                profile_path.write_bytes(
                    original_bytes
                    if original_bytes
                    is not None
                    else b""
                )
            else:
                profile_path.unlink(
                    missing_ok=True
                )

            restored = (
                (
                    profile_path.is_file()
                    and profile_path.read_bytes()
                    == original_bytes
                )
                if original_exists
                else not profile_path.exists()
            )
        except Exception as exc:
            lines.append(
                "RESTORE ERROR: "
                f"{type(exc).__name__}: {exc}"
            )
            restored = False

    lines.append(
        f"Result: {result}"
    )
    lines.append(
        "Storage restored: "
        + str(
            restored
        )
    )

    log_path.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        "\n".join(
            lines
        )
    )
    print(
        f"Probe log: {log_path}"
    )

    return (
        0
        if (
            result == "PASS"
            and restored
        )
        else 1
    )

if __name__ == "__main__":
    raise SystemExit(main())
