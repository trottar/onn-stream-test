#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import tempfile
import time

from pathlib import Path
from typing import Any


SESSION_REL = Path(
    "logs/tv/d126_android_epg_prefetch_session.json"
)
LOG_JSON_REL = Path(
    "logs/tv/d126_android_epg_prefetch_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d126_android_epg_prefetch_probe.txt"
)


def load_d116(repo: Path):
    path = (
        repo
        / "tools/probes/d116_android_tv_state_sync_probe.py"
    )
    spec = importlib.util.spec_from_file_location(
        "d126_d116_probe",
        path,
    )
    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load D-116 ADB helper"
        )
    module = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(
        module
    )
    return module


def read_meta(
    db_path: Path,
) -> dict[str, str]:
    connection = sqlite3.connect(
        f"file:{db_path}?mode=ro",
        uri=True,
    )
    try:
        rows = connection.execute(
            """
            SELECT key, value
            FROM meta
            WHERE key IN (
                'companion_epg_last_prefetch_at_ms',
                'companion_epg_last_prefetch_requested',
                'companion_epg_last_prefetch_queued'
            )
            """
        ).fetchall()
        return {
            str(key):
                str(value)
            for key, value in rows
        }
    finally:
        connection.close()


def snapshot_meta(
    repo: Path,
    d116,
    serial: str,
) -> dict[str, str]:
    with tempfile.TemporaryDirectory(
        prefix="d126_epg_db_"
    ) as td:
        path = d116.snapshot_db(
            serial,
            "privyhub_epg.db",
            Path(td),
        )
        if path is None:
            raise RuntimeError(
                "Unable to snapshot privyhub_epg.db"
            )
        return read_meta(path)


def int_meta(
    meta: dict[str, str],
    key: str,
) -> int:
    try:
        return int(
            meta.get(
                key,
                "0",
            )
            or "0"
        )
    except ValueError:
        return 0


def write_report(
    repo: Path,
    report: dict[str, Any],
) -> int:
    json_path = repo / LOG_JSON_REL
    text_path = repo / LOG_TEXT_REL
    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report["json_path"] = str(
        json_path
    )
    report["text_path"] = str(
        text_path
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub D-126 Android EPG prefetch probe",
        f"Classification: {report.get('classification')}",
        "",
        "PREFETCH META",
        f"  baseline_at_ms: {report.get('baseline_at_ms')}",
        f"  observed_at_ms: {report.get('observed_at_ms')}",
        f"  requested: {report.get('requested')}",
        f"  queued: {report.get('queued')}",
        "",
        "CHECKS",
        f"  newer_prefetch_observed: {report.get('newer_prefetch_observed')}",
        f"  requested_positive: {report.get('requested_positive')}",
        f"  queued_positive: {report.get('queued_positive')}",
        "",
        "No network address or device identifier is written to this report.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ]

    text = "\n".join(
        lines
    ) + "\n"

    text_path.write_text(
        text,
        encoding="utf-8",
    )
    print(
        text,
        end="",
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo",
        default=".",
    )
    parser.add_argument(
        "--prepare",
        action="store_true",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
    )
    args = parser.parse_args()

    if args.self_test:
        assert int_meta(
            {"x": "7"},
            "x",
        ) == 7
        assert int_meta(
            {},
            "x",
        ) == 0
        print(
            "D126_PROBE_SELF_TEST_OK"
        )
        return 0

    if args.prepare == args.verify:
        print(
            "Use exactly one of --prepare or --verify"
        )
        return 2

    repo = Path(
        args.repo
    ).resolve()
    d116 = load_d116(
        repo
    )
    serial, adb_info = (
        d116.adb_serial()
    )
    if not serial:
        return write_report(
            repo,
            {
                "classification":
                    "D126_ADB_UNAVAILABLE",
                "adb_status":
                    adb_info.get(
                        "reason"
                    ),
            },
        )

    meta = snapshot_meta(
        repo,
        d116,
        serial,
    )
    current_at = int_meta(
        meta,
        "companion_epg_last_prefetch_at_ms",
    )

    session_path = (
        repo
        / SESSION_REL
    )
    session_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.prepare:
        session = {
            "baseline_at_ms":
                current_at,
            "prepared_at_ms":
                int(
                    time.time()
                    * 1000
                ),
        }
        session_path.write_text(
            json.dumps(
                session,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return write_report(
            repo,
            {
                "classification":
                    "D126_ANDROID_EPG_PREFETCH_TEST_PREPARED",
                "baseline_at_ms":
                    current_at,
                "observed_at_ms":
                    current_at,
                "requested":
                    int_meta(
                        meta,
                        "companion_epg_last_prefetch_requested",
                    ),
                "queued":
                    int_meta(
                        meta,
                        "companion_epg_last_prefetch_queued",
                    ),
                "newer_prefetch_observed":
                    False,
                "requested_positive":
                    False,
                "queued_positive":
                    False,
            },
        )

    if not session_path.is_file():
        return write_report(
            repo,
            {
                "classification":
                    "D126_PREPARE_REQUIRED",
            },
        )

    session = json.loads(
        session_path.read_text(
            encoding="utf-8"
        )
    )
    baseline = int(
        session.get(
            "baseline_at_ms",
            0,
        )
        or 0
    )
    requested = int_meta(
        meta,
        "companion_epg_last_prefetch_requested",
    )
    queued = int_meta(
        meta,
        "companion_epg_last_prefetch_queued",
    )

    newer = current_at > baseline
    requested_positive = requested > 0
    queued_positive = queued > 0

    classification = (
        "D126_ANDROID_TV_ENTRY_AND_PAGE_PREFETCH_VALIDATED"
        if (
            newer
            and requested_positive
            and queued_positive
        )
        else "D126_ANDROID_PREFETCH_NOT_OBSERVED"
    )

    return write_report(
        repo,
        {
            "classification":
                classification,
            "baseline_at_ms":
                baseline,
            "observed_at_ms":
                current_at,
            "requested":
                requested,
            "queued":
                queued,
            "newer_prefetch_observed":
                newer,
            "requested_positive":
                requested_positive,
            "queued_positive":
                queued_positive,
        },
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
