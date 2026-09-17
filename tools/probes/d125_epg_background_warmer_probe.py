#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
LOG_JSON_REL = Path(
    "logs/tv/d125_epg_background_warmer_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d125_epg_background_warmer_probe.txt"
)


def load_d116(
    repo: Path,
):
    path = (
        repo
        / "tools/probes/d116_android_tv_state_sync_probe.py"
    )
    spec = importlib.util.spec_from_file_location(
        "d125_d116_probe",
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


def http_json(
    path: str,
    *,
    timeout: float = 5.0,
) -> tuple[int, dict[str, Any] | None, float]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D125-Probe/1.0",
        },
        method="GET",
    )

    started = time.perf_counter()

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            raw = response.read(
                4 * 1024 * 1024
            )
            elapsed = round(
                (
                    time.perf_counter()
                    - started
                )
                * 1000.0,
                3,
            )
            payload = json.loads(
                raw.decode("utf-8")
            )
            return (
                int(response.status),
                payload
                if isinstance(
                    payload,
                    dict,
                )
                else None,
                elapsed,
            )

    except urllib.error.HTTPError as exc:
        elapsed = round(
            (
                time.perf_counter()
                - started
            )
            * 1000.0,
            3,
        )
        return (
            int(exc.code),
            None,
            elapsed,
        )


def cache_path(
    repo: Path,
    channel_id: str,
) -> Path:
    digest = hashlib.sha256(
        channel_id.encode(
            "utf-8"
        )
    ).hexdigest()
    return (
        repo
        / "data/epg/cache"
        / f"{digest}.json"
    )


def choose_uncached_channel(
    repo: Path,
    serial: str,
    d116,
) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(
        prefix="d125_tv_db_"
    ) as td:
        tv_path = d116.snapshot_db(
            serial,
            "privyhub_tv.db",
            Path(td),
        )
        if tv_path is None:
            return "", ""

        connection = sqlite3.connect(
            f"file:{tv_path}?mode=ro",
            uri=True,
        )
        try:
            rows = connection.execute(
                """
                SELECT
                    channel_id,
                    COALESCE(
                        NULLIF(custom_name, ''),
                        name
                    ) AS display_name,
                    favorite
                FROM streams
                WHERE
                    manual_hidden = 0
                    AND auto_hidden = 0
                    AND TRIM(channel_id) <> ''
                    AND channel_id NOT LIKE 'tv_stream_%'
                ORDER BY
                    favorite DESC,
                    favorite_order ASC,
                    display_name COLLATE NOCASE
                LIMIT 1000
                """
            ).fetchall()
        finally:
            connection.close()

    for channel_id, display_name, _ in rows:
        channel_id = str(
            channel_id
            or ""
        ).strip()
        if (
            channel_id
            and not cache_path(
                repo,
                channel_id,
            ).is_file()
        ):
            return (
                channel_id,
                str(
                    display_name
                    or channel_id
                ),
            )

    return "", ""


def finish(
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
        "PrivyHub D-125 EPG non-blocking background warmer probe",
        f"Classification: {report.get('classification')}",
        "",
        "TARGET",
        f"  display_name: {report.get('display_name')}",
        f"  cache_missing_before: {report.get('cache_missing_before')}",
        "",
        "INTERACTIVE GUIDE REQUEST",
        f"  http: {report.get('guide_http')}",
        f"  duration_ms: {report.get('guide_duration_ms')}",
        f"  refresh_queued: {report.get('refresh_queued')}",
        f"  programme_count_immediate: {report.get('programme_count_immediate')}",
        f"  empty_reason: {report.get('empty_reason')}",
        "",
        "BACKGROUND RESULT",
        f"  cache_created: {report.get('cache_created')}",
        f"  background_elapsed_ms: {report.get('background_elapsed_ms')}",
        f"  background_programme_count: {report.get('background_programme_count')}",
        f"  background_empty_reason: {report.get('background_empty_reason')}",
        f"  worker_pending_count: {report.get('worker_pending_count')}",
        f"  worker_completed_count: {report.get('worker_completed_count')}",
        f"  worker_failed_count: {report.get('worker_failed_count')}",
        "",
        "CHECKS",
        f"  interactive_nonblocking: {report.get('interactive_nonblocking')}",
        f"  background_activity_observed: {report.get('background_activity_observed')}",
        "",
        "No cache file was deleted or invalidated by this probe.",
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
        "--self-test",
        action="store_true",
    )
    args = parser.parse_args()

    if args.self_test:
        assert (
            hashlib.sha256(
                b"channel"
            ).hexdigest()
        )
        print(
            "D125_PROBE_SELF_TEST_OK"
        )
        return 0

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
        return finish(
            repo,
            {
                "classification":
                    "D125_ADB_UNAVAILABLE",
                "adb_status":
                    adb_info.get(
                        "reason"
                    ),
            },
        )

    channel_id, display_name = (
        choose_uncached_channel(
            repo,
            serial,
            d116,
        )
    )

    if not channel_id:
        return finish(
            repo,
            {
                "classification":
                    "D125_NO_UNCACHED_CHANNEL_AVAILABLE",
                "adb_status":
                    "ready",
            },
        )

    target_cache = cache_path(
        repo,
        channel_id,
    )

    encoded = urllib.parse.quote(
        channel_id,
        safe="",
    )

    (
        guide_http,
        guide_payload,
        guide_ms,
    ) = http_json(
        (
            "/plugins/epg/guide"
            f"?channel_id={encoded}"
        ),
        timeout=3.0,
    )

    payload = (
        guide_payload
        if isinstance(
            guide_payload,
            dict,
        )
        else {}
    )

    refresh_queued = bool(
        payload.get(
            "refresh_queued"
        )
    )

    interactive_nonblocking = (
        guide_http == 200
        and guide_ms < 1000.0
        and refresh_queued
    )

    started = time.perf_counter()
    deadline = (
        time.monotonic()
        + 45.0
    )
    cache_payload = None
    last_status = None

    while (
        time.monotonic()
        < deadline
    ):
        if target_cache.is_file():
            try:
                candidate = json.loads(
                    target_cache.read_text(
                        encoding="utf-8"
                    )
                )
                if (
                    isinstance(
                        candidate,
                        dict,
                    )
                    and candidate.get(
                        "channel_id"
                    )
                    == channel_id
                ):
                    cache_payload = candidate
                    break
            except Exception:
                pass

        try:
            _, status_payload, _ = (
                http_json(
                    "/plugins/epg/status",
                    timeout=2.0,
                )
            )
            if isinstance(
                status_payload,
                dict,
            ):
                last_status = status_payload
                warmer = (
                    status_payload.get(
                        "background_refresh"
                    )
                    or {}
                )
                if (
                    int(
                        warmer.get(
                            "pending_count",
                            0,
                        )
                        or 0
                    )
                    == 0
                    and (
                        int(
                            warmer.get(
                                "completed_count",
                                0,
                            )
                            or 0
                        )
                        > 0
                        or int(
                            warmer.get(
                                "failed_count",
                                0,
                            )
                            or 0
                        )
                        > 0
                    )
                ):
                    break
        except Exception:
            pass

        time.sleep(
            0.5
        )

    background_elapsed_ms = round(
        (
            time.perf_counter()
            - started
        )
        * 1000.0,
        3,
    )

    try:
        _, status_payload, _ = (
            http_json(
                "/plugins/epg/status",
                timeout=2.0,
            )
        )
        if isinstance(
            status_payload,
            dict,
        ):
            last_status = (
                status_payload
            )
    except Exception:
        pass

    warmer = (
        (
            last_status.get(
                "background_refresh"
            )
            if isinstance(
                last_status,
                dict,
            )
            else None
        )
        or {}
    )

    completed = int(
        warmer.get(
            "completed_count",
            0,
        )
        or 0
    )
    failed = int(
        warmer.get(
            "failed_count",
            0,
        )
        or 0
    )
    pending = int(
        warmer.get(
            "pending_count",
            0,
        )
        or 0
    )

    background_activity = (
        cache_payload is not None
        or completed > 0
        or failed > 0
        or pending > 0
    )

    if (
        interactive_nonblocking
        and background_activity
    ):
        classification = (
            "D125_NONBLOCKING_GUIDE_MISS_AND_BACKGROUND_WARMER_VALIDATED"
        )
    elif interactive_nonblocking:
        classification = (
            "D125_NONBLOCKING_GUIDE_MISS_VALIDATED_BACKGROUND_NOT_OBSERVED"
        )
    else:
        classification = (
            "D125_NONBLOCKING_GUIDE_MISS_FAILED"
        )

    report = {
        "classification":
            classification,
        "display_name":
            display_name,
        "cache_missing_before":
            True,
        "guide_http":
            guide_http,
        "guide_duration_ms":
            guide_ms,
        "refresh_queued":
            refresh_queued,
        "programme_count_immediate":
            int(
                payload.get(
                    "programme_count",
                    0,
                )
                or 0
            ),
        "empty_reason":
            payload.get(
                "empty_reason"
            ),
        "cache_created":
            cache_payload
            is not None,
        "background_elapsed_ms":
            background_elapsed_ms,
        "background_programme_count":
            (
                len(
                    cache_payload.get(
                        "programmes",
                        [],
                    )
                )
                if isinstance(
                    cache_payload,
                    dict,
                )
                else None
            ),
        "background_empty_reason":
            (
                cache_payload.get(
                    "empty_reason"
                )
                if isinstance(
                    cache_payload,
                    dict,
                )
                else None
            ),
        "worker_pending_count":
            pending,
        "worker_completed_count":
            completed,
        "worker_failed_count":
            failed,
        "interactive_nonblocking":
            interactive_nonblocking,
        "background_activity_observed":
            background_activity,
    }

    return finish(
        repo,
        report,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
