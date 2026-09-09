#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IPV4_RE = re.compile(
    r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"
)


def redact(text: str) -> str:
    return IPV4_RE.sub("<IP_REDACTED>", text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest().upper()


def append_text(
    output: list[str],
    title: str,
    text: str,
) -> None:
    output.append("")
    output.append("=" * 78)
    output.append(title)
    output.append("=" * 78)
    output.append(redact(text.rstrip()))


def safe_read(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )
    except OSError as exc:
        return f"[unable to read {path}: {exc}]"


def latest_file(
    root: Path,
    pattern: str,
    *,
    exclude: set[str] | None = None,
) -> Path | None:
    excluded = exclude or set()
    candidates = [
        path
        for path in root.glob(pattern)
        if path.is_file()
        and path.name not in excluded
    ]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda path: path.stat().st_mtime_ns,
    )


def state_inventory(
    project_root: Path,
) -> list[dict[str, Any]]:
    state_root = (
        project_root
        / "data"
        / "games"
        / "retroarch"
        / "states"
    )
    if not state_root.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    for path in state_root.rglob("*"):
        if not path.is_file():
            continue
        folded = path.name.casefold()
        if ".state" not in folded:
            continue

        try:
            stat = path.stat()
            relative = str(
                path.relative_to(project_root)
            ).replace("\\", "/")
        except (OSError, ValueError):
            continue

        row: dict[str, Any] = {
            "path": relative,
            "size_bytes": int(stat.st_size),
            "mtime_ns": int(stat.st_mtime_ns),
        }

        if path.suffix.casefold() != ".png":
            try:
                row["sha256"] = (
                    sha256_file(path)
                    if stat.st_size > 0
                    else None
                )
            except OSError as exc:
                row["sha256_error"] = str(exc)

        rows.append(row)

    rows.sort(
        key=lambda item: int(
            item.get("mtime_ns", 0)
        ),
        reverse=True,
    )
    return rows[:80]


def selected_runtime_details(
    project_root: Path,
) -> dict[str, Any]:
    config_path = (
        project_root
        / "companion"
        / "games"
        / "config"
        / "emulators.json"
    )
    result: dict[str, Any] = {
        "config_path": str(
            config_path.relative_to(project_root)
        ).replace("\\", "/")
    }

    try:
        payload = json.loads(
            config_path.read_text(
                encoding="utf-8-sig"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        result["error"] = str(exc)
        return result

    retro = (
        payload.get("retroarch")
        if isinstance(payload, dict)
        else None
    )
    if not isinstance(retro, dict):
        result["error"] = (
            "retroarch profile missing"
        )
        return result

    result["profile"] = retro

    executable_rel = retro.get("executable")
    if isinstance(
        executable_rel,
        str,
    ) and executable_rel.strip():
        executable = (
            project_root
            / executable_rel
        ).resolve()
        try:
            executable.relative_to(
                project_root
            )
            result[
                "executable_exists"
            ] = executable.is_file()
            if executable.is_file():
                result[
                    "executable_size_bytes"
                ] = executable.stat().st_size
                result[
                    "executable_sha256"
                ] = sha256_file(executable)
        except (
            OSError,
            ValueError,
        ) as exc:
            result[
                "executable_error"
            ] = str(exc)

    return result


def filtered_session_config(
    project_root: Path,
) -> str:
    path = (
        project_root
        / "data"
        / "games"
        / "retroarch"
        / "config"
        / "privyhub-session.cfg"
    )
    if not path.is_file():
        return "[privyhub-session.cfg missing]"

    wanted = (
        "network_cmd_",
        "state_slot",
        "savestate_",
        "savefile_",
        "input_joypad_driver",
        "input_player",
        "video_driver",
        "video_shared_context",
        "video_fullscreen",
        "video_windowed_fullscreen",
    )

    lines = []
    for raw in safe_read(path).splitlines():
        stripped = raw.strip()
        folded = stripped.casefold()
        if any(
            key in folded
            for key in wanted
        ):
            lines.append(stripped)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        default=".",
        help="PrivyHub project root",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    games_log = root / "logs" / "games"
    games_log.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        games_log
        / "latest_game_diagnostic_bundle.txt"
    )

    output: list[str] = [
        "PrivyHub game diagnostic bundle",
        "Generated UTC: "
        + datetime.now(
            timezone.utc
        ).isoformat(
            timespec="milliseconds"
        ).replace(
            "+00:00",
            "Z",
        ),
        "Project root: <ROOT>",
    ]

    runtime = selected_runtime_details(
        root
    )
    append_text(
        output,
        "SELECTED RETROARCH RUNTIME",
        json.dumps(
            runtime,
            indent=2,
            default=str,
        ),
    )

    append_text(
        output,
        "SESSION-CRITICAL RETROARCH CONFIG",
        filtered_session_config(root),
    )

    trace = (
        games_log
        / "save_state_probe.txt"
    )
    append_text(
        output,
        "UNIFIED GAME SESSION TRACE",
        safe_read(trace)
        if trace.is_file()
        else "[save_state_probe.txt missing]",
    )

    control = (
        games_log
        / "retroarch_control_probe.txt"
    )
    append_text(
        output,
        "RETROARCH NETWORK CONTROL TRACE",
        safe_read(control)
        if control.is_file()
        else "[retroarch_control_probe.txt missing]",
    )

    session_log = latest_file(
        games_log,
        "*.log",
        exclude={
            "native_video_alpha.log",
        },
    )
    append_text(
        output,
        "LATEST RETROARCH VERBOSE SESSION LOG",
        (
            safe_read(session_log)
            if session_log is not None
            else "[no RetroArch session log]"
        ),
    )

    native_video = (
        games_log
        / "native_video_alpha.log"
    )
    append_text(
        output,
        "NATIVE VIDEO HOST LOG",
        (
            "\n".join(
                safe_read(
                    native_video
                ).splitlines()[-500:]
            )
            if native_video.is_file()
            else "[native_video_alpha.log missing]"
        ),
    )

    decoder_dir = (
        games_log
        / "decoder_sessions"
    )
    decoder = (
        latest_file(
            decoder_dir,
            "native_decoder_*.json",
        )
        if decoder_dir.is_dir()
        else None
    )
    append_text(
        output,
        "LATEST ANDROID DECODER SESSION",
        (
            safe_read(decoder)
            if decoder is not None
            else "[no decoder session log]"
        ),
    )

    slot_index = (
        root
        / "data"
        / "games"
        / "retroarch"
        / "privyhub_state_slots.json"
    )
    append_text(
        output,
        "PRIVYHUB PER-GAME STATE SLOT INDEX",
        (
            safe_read(slot_index)
            if slot_index.is_file()
            else "[state-slot index missing]"
        ),
    )

    append_text(
        output,
        "SAVESTATE FILE INVENTORY",
        json.dumps(
            state_inventory(root),
            indent=2,
            default=str,
        ),
    )

    text = "\n".join(output) + "\n"
    text = text.replace(
        str(root),
        "<ROOT>",
    )
    text = redact(text)

    output_path.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Game diagnostic bundle: "
        + str(
            output_path.relative_to(root)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
