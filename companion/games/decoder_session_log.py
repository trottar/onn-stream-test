from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_REPORT_CHARS = 32_000
SCHEMA = "privyhub_native_decoder_session_log_v1"


def write_decoder_session_log(
    project_root: Path,
    report_text: str,
) -> dict[str, Any]:
    if not report_text:
        raise ValueError(
            "Missing decoder session report"
        )

    if len(report_text) > MAX_REPORT_CHARS:
        raise ValueError(
            "Decoder session report is too large"
        )

    try:
        report = json.loads(
            report_text
        )
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid decoder session report"
        ) from exc

    if not isinstance(
        report,
        dict,
    ):
        raise ValueError(
            "Decoder session report must be a JSON object"
        )

    received_at = datetime.now(
        timezone.utc
    )

    log_root = (
        Path(project_root)
        / "logs"
        / "games"
        / "decoder_sessions"
    )
    log_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        "native_decoder_"
        + received_at.strftime(
            "%Y%m%d_%H%M%S_%f"
        )[:-3]
        + ".json"
    )

    path = log_root / filename

    document = {
        "schema": SCHEMA,
        "received_at_utc": (
            received_at
            .isoformat(
                timespec="milliseconds"
            )
            .replace(
                "+00:00",
                "Z",
            )
        ),
        "report": report,
    }

    temporary = path.with_suffix(
        ".json.tmp"
    )

    temporary.write_text(
        json.dumps(
            document,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)

    relative = path.relative_to(
        project_root
    )

    print(
        "Native decoder session log: "
        + str(relative)
    )

    return {
        "ok": True,
        "saved": True,
        "log_path": (
            relative.as_posix()
        ),
    }
