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
    query = urllib.parse.urlencode(
        params
    )
    return (
        "/plugins/games/"
        + action
        + (
            "?"
            + query
            if query
            else ""
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
        / "a8_2_runtime_mapping_probe.txt"
    )
    log_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original = (
        profile_path.read_bytes()
        if profile_path.is_file()
        else None
    )

    lines = [
        "PrivyHub A8.2 runtime mapping probe",
        "Purpose: validate a named profile through normal Android -> companion -> RetroArch launch.",
    ]
    result = "FAIL"
    restored = False

    try:
        status = request_json(
            "/plugins/games/status"
        )
        if status.get(
            "active"
        ):
            raise RuntimeError(
                "End the active game before starting the A8.2 runtime probe"
            )

        # Deliberately require Crash Team Racing for this runtime check.
        # CTR is present in the catalog and provides an unambiguous gameplay
        # control surface for observing the P1 A/B swap.
        games = request_json(
            query_path(
                "games",
                {
                    "view": "search",
                    "q": "Crash Team Racing",
                    "limit": "20",
                },
            )
        )
        nodes = games.get(
            "nodes",
            []
        )

        selected = None
        if isinstance(
            nodes,
            list,
        ):
            for node in nodes:
                if not isinstance(
                    node,
                    dict,
                ):
                    continue

                title = str(
                    node.get(
                        "name",
                        "",
                    )
                ).strip()

                if not title:
                    title = str(
                        node.get(
                            "title",
                            "",
                        )
                    ).strip()

                if (
                    node.get(
                        "node_type"
                    )
                    == "game"
                    and "crash team racing"
                    in title.casefold()
                ):
                    selected = node
                    break

        if selected is None:
            raise RuntimeError(
                "Crash Team Racing was not found in the companion catalog"
            )

        game_id = str(
            selected.get(
                "id",
                "",
            )
        ).strip()
        game_name = str(
            selected.get(
                "name",
                game_id,
            )
        ).strip()

        # A8 mapping semantics are:
        #   RetroPad target <- physical XUSB source
        #
        # Normal Xbox autoconfig is:
        #   RetroPad B <- physical A (button 0)
        #   RetroPad A <- physical B (button 1)
        #
        # Therefore a physical A/B gameplay swap relative to the normal
        # Xbox mapping is intentionally:
        #   RetroPad A <- physical A
        #   RetroPad B <- physical B
        mapping = json.dumps(
            {
                "player1": {
                    "a": "a",
                    "b": "b",
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
                    "name": "A8 Runtime Physical Swap A-B",
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
                "Profile create endpoint did not return a profile"
            )
        profile_id = str(
            profile.get(
                "id",
                "",
            )
        ).strip()
        if not profile_id:
            raise RuntimeError(
                "Runtime probe profile has no id"
            )

        request_json(
            query_path(
                "input-profile-assign",
                {
                    "id": game_id,
                    "profile_id": profile_id,
                },
            ),
            method="POST",
        )

        print("")
        print("A8.2 RUNTIME TEST")
        print("")
        print(
            "On the onn, launch this game normally:"
        )
        print(
            f"  {game_name}"
        )
        print("")
        print(
            "Player 1 physical A and B should be swapped in gameplay."
        )
        print(
            "Save / Load / Pause / End should behave normally."
        )
        print(
            "After checking, END/EXIT the game normally."
        )
        print("")

        answer = input(
            "Was the A/B swap observed with normal meta controls? [y/n]: "
        ).strip().casefold()

        observed = answer in {
            "y",
            "yes",
        }

        config_path = (
            root
            / "data"
            / "games"
            / "retroarch"
            / "config"
            / "privyhub-input.cfg"
        )
        expected_runtime_binds = (
            'input_player1_a_btn = "0"',
            'input_player1_a_axis = "nul"',
            'input_player1_b_btn = "1"',
            'input_player1_b_axis = "nul"',
        )
        generated_swap = False

        if config_path.is_file():
            config_text = config_path.read_text(
                encoding="utf-8",
            )
            generated_swap = all(
                item in config_text
                for item in expected_runtime_binds
            )

        game_log_path = None
        xinput_fallback = None
        xinput_autoconfigured = None

        log_root = (
            root
            / "logs"
            / "games"
        )

        candidates = (
            sorted(
                log_root.glob(
                    f"*-{game_id}.log"
                ),
                key=lambda item: (
                    item.stat().st_mtime_ns
                ),
                reverse=True,
            )
            if log_root.is_dir()
            else []
        )

        if candidates:
            game_log_path = candidates[0]
            game_log_text = (
                game_log_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
            xinput_fallback = (
                'Configured joypad driver "xinput" '
                'failed to initialise'
                in game_log_text
            )
            xinput_autoconfigured = (
                "Xbox 360 Controller configured in port 1."
                in game_log_text
                and
                "Xbox 360 Controller configured in port 2."
                in game_log_text
            )

        lines.append(
            f"Game: {game_name}"
        )
        lines.append(
            f"A/B swap observed: {observed}"
        )
        lines.append(
            f"Generated swapped RetroPad binds: {generated_swap}"
        )
        lines.append(
            "XInput startup fallback observed: "
            + str(
                xinput_fallback
            )
        )
        lines.append(
            "Xbox controllers autoconfigured: "
            + str(
                xinput_autoconfigured
            )
        )
        lines.append(
            "RetroArch game log: "
            + (
                str(
                    game_log_path
                )
                if game_log_path
                is not None
                else "<not found>"
            )
        )

        if observed:
            lines.append(
                "Meta controls reported normal: True"
            )

        if not generated_swap:
            result = (
                "A8_RUNTIME_MAPPING_CONFIG_NOT_SWAPPED"
            )
        elif xinput_fallback is True:
            result = (
                "A8_RUNTIME_XINPUT_STARTUP_FALLBACK"
            )
        elif xinput_fallback is None:
            result = (
                "A8_RUNTIME_INPUT_DRIVER_UNVERIFIED"
            )
        elif observed:
            result = (
                "A8_RUNTIME_MAPPING_OBSERVED"
            )
        else:
            result = (
                "A8_RUNTIME_MAPPING_NOT_CONFIRMED"
            )

    except Exception as exc:
        lines.append(
            f"ERROR: {type(exc).__name__}: {exc}"
        )

    finally:
        try:
            if original is None:
                profile_path.unlink(
                    missing_ok=True
                )
            else:
                profile_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
                profile_path.write_bytes(
                    original
                )

            restored = (
                (
                    profile_path.read_bytes()
                    == original
                )
                if original is not None
                and profile_path.is_file()
                else (
                    not profile_path.exists()
                    if original is None
                    else False
                )
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
        "Input profile storage restored: "
        + str(
            restored
        )
    )
    log_path.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

    print("")
    print(
        f"Result: {result}"
    )
    print(
        "Input profile storage restored: "
        + str(
            restored
        )
    )
    print(
        f"Probe log: {log_path}"
    )

    return (
        0
        if result
        == "A8_RUNTIME_MAPPING_OBSERVED"
        and restored
        else 1
    )

if __name__ == "__main__":
    raise SystemExit(main())
