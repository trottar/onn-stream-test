#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:8765"

def request_json(
    path: str,
    *,
    method: str = "GET",
) -> dict[str, Any]:
    request = urllib.request.Request(
        BASE + path,
        method=method,
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            text = response.read().decode(
                "utf-8"
            )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        raise RuntimeError(
            f"HTTP {exc.code}: {body}"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            "Companion API is unavailable on localhost:8765"
        ) from exc

    payload = json.loads(
        text
    )
    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "Companion API returned a non-object payload"
        )
    return payload

def query_path(
    action: str,
    params: dict[str, str],
) -> str:
    return (
        "/plugins/games/"
        + action
        + "?"
        + urllib.parse.urlencode(
            params
        )
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
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
        / "a8_input_profiles_api_probe.txt"
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

    lines = [
        "PrivyHub A8.1 input profile localhost API probe",
        "Purpose: validate companion GET/POST profile endpoints without network-address logging.",
    ]
    result = "FAIL"
    restored = False

    try:
        status = request_json(
            "/plugins/games/status"
        )
        assert status.get(
            "ok"
        ) is True
        lines.append(
            "Companion Games API reachable: PASS"
        )

        games = request_json(
            query_path(
                "games",
                {
                    "system": "ps1",
                    "limit": "1",
                },
            )
        )

        nodes = games.get(
            "nodes",
            [],
        )
        game_id = ""

        if isinstance(
            nodes,
            list,
        ):
            for node in nodes:
                if (
                    isinstance(
                        node,
                        dict,
                    )
                    and node.get(
                        "node_type"
                    )
                    == "game"
                    and not str(
                        node.get(
                            "id",
                            "",
                        )
                    ).startswith(
                        "games_empty_"
                    )
                ):
                    game_id = str(
                        node.get(
                            "id",
                            "",
                        )
                    ).strip()
                    if game_id:
                        break

        if not game_id:
            raise RuntimeError(
                "No PS1 game was available for the A8.1 API assignment probe"
            )

        catalog = request_json(
            query_path(
                "input-profiles",
                {
                    "id": game_id,
                },
            )
        )
        assert catalog.get(
            "schema"
        ) == 1
        lines.append(
            "GET input-profiles: PASS"
        )

        mapping = json.dumps(
            {
                "player1": {
                    "a": "b",
                    "b": "a",
                },
                "player2": {},
            },
            separators=(
                ",",
                ":",
            ),
        )

        created = request_json(
            query_path(
                "input-profile-create",
                {
                    "name": (
                        "A8 API Probe"
                    ),
                    "mapping": mapping,
                },
            ),
            method="POST",
        )

        profile = created.get(
            "profile"
        )
        if not isinstance(
            profile,
            dict,
        ):
            raise RuntimeError(
                "Create endpoint did not return a profile"
            )

        profile_id = str(
            profile.get(
                "id",
                "",
            )
        ).strip()

        if not profile_id:
            raise RuntimeError(
                "Create endpoint returned no profile id"
            )

        lines.append(
            "POST input-profile-create: PASS"
        )

        assigned = request_json(
            query_path(
                "input-profile-assign",
                {
                    "id": game_id,
                    "profile_id": (
                        profile_id
                    ),
                },
            ),
            method="POST",
        )
        assert assigned.get(
            "profile_id"
        ) == profile_id
        lines.append(
            "POST input-profile-assign: PASS"
        )

        verified = request_json(
            query_path(
                "input-profiles",
                {
                    "id": game_id,
                },
            )
        )

        effective = verified.get(
            "effective"
        )
        if not isinstance(
            effective,
            dict,
        ):
            raise RuntimeError(
                "GET input-profiles returned no effective assignment"
            )

        assert effective.get(
            "profile_id"
        ) == profile_id
        lines.append(
            "GET effective assignment verification: PASS"
        )

        cleared = request_json(
            query_path(
                "input-profile-assign",
                {
                    "id": game_id,
                    "profile_id": (
                        "default"
                    ),
                },
            ),
            method="POST",
        )
        assert cleared.get(
            "profile_id"
        ) == "default"
        lines.append(
            "POST default reassignment: PASS"
        )

        deleted = request_json(
            query_path(
                "input-profile-delete",
                {
                    "profile_id": (
                        profile_id
                    ),
                },
            ),
            method="POST",
        )
        assert deleted.get(
            "deleted"
        ) is True
        lines.append(
            "POST input-profile-delete: PASS"
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
