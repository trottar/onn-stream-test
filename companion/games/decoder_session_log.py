from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# C3-L3A-R2B: was 32_000, which refused a 24-transition session's report
# (32,057 chars; each SSRC change adds ~270-310). The client sends the report
# URL-encoded in the request target (~1.58 encoded chars per decoded char),
# and http.server answers 414 to a request line over 65,536 bytes before any
# handler runs, so the transport itself stops at ~41K decoded chars. 48_000
# sits above that ceiling: this check never refuses what the transport can
# carry. Lifting the ceiling is the client's change (report in the body).
#
# CL-B1: the report now also arrives as a POST body, so the request line is
# no longer the ceiling and this is the only limit. The largest report seen
# is 32,435 chars (C3.L3a rerun session 3, 24 SSRC changes). The same client
# change grows the slow-event rings from 64 + 64 to 256 marked + 1,024
# recent rows (~23.3 chars each), adding up to ~26.8K when both fill, so a
# 24-transition session with full rings is ~59K. 128,000 is ~2.2x that.
MAX_REPORT_CHARS = 128_000
SCHEMA = "privyhub_native_decoder_session_log_v1"


def _host_thermal_c(
    project_root: Path,
) -> float | None:
    """D-BASE-T1: the hottest host sensor at the moment the report lands.

    Recorded beside the report rather than inside it, so a reader can see
    both ends' temperatures — the onn's in `report.thermal`, the host's
    here — without correlating two files. Any failure reads as None.
    """

    try:
        import sys

        sys.path.insert(
            0,
            str(Path(project_root) / "tools"),
        )

        from host_resource_sampler import (  # noqa: PLC0415
            hottest_c,
            read_hwmon,
        )

        return hottest_c(read_hwmon())
    except Exception:
        return None


def write_decoder_session_log(
    project_root: Path,
    report_text: str,
    host_extra: dict[str, Any] | None = None,
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
        "host": {
            "host_thermal_c": _host_thermal_c(
                project_root
            ),
            # D-BASE-P3: whichever arm this session ran in, recorded beside
            # the report so a reader never has to infer it.
            **(host_extra or {}),
        },
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
