#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sqlite3
import statistics
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 8 * 1024 * 1024
GUIDE_TIMEOUT_S = 32

LOG_JSON_REL = Path(
    "logs/tv/d124_tv_epg_latency_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d124_tv_epg_latency_probe.txt"
)


def elapsed_ms(
    started: float,
) -> float:
    return round(
        (
            time.perf_counter()
            - started
        )
        * 1000.0,
        3,
    )


def load_module(
    path: Path,
    module_name: str,
):
    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            f"Unable to load {path.name}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def load_d116(
    repo: Path,
):
    return load_module(
        repo
        / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d124_d116_probe",
    )


def http_json(
    path: str,
    timeout_s: int = GUIDE_TIMEOUT_S,
) -> tuple[
    int,
    Any,
    float,
    str | None,
]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D124-Probe/1.0",
        },
        method="GET",
    )

    started = time.perf_counter()

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_s,
        ) as response:
            raw = response.read(
                MAX_RESPONSE_BYTES + 1
            )

            duration = elapsed_ms(
                started
            )

            if len(raw) > MAX_RESPONSE_BYTES:
                return (
                    int(response.status),
                    None,
                    duration,
                    "response_exceeds_probe_cap",
                )

            try:
                payload = json.loads(
                    raw.decode("utf-8")
                )
            except Exception as exc:
                return (
                    int(response.status),
                    None,
                    duration,
                    f"json_decode_failed:{type(exc).__name__}",
                )

            return (
                int(response.status),
                payload,
                duration,
                None,
            )

    except urllib.error.HTTPError as exc:
        duration = elapsed_ms(
            started
        )

        raw = exc.read(
            MAX_RESPONSE_BYTES + 1
        )

        try:
            payload = json.loads(
                raw.decode("utf-8")
            )
        except Exception:
            payload = None

        return (
            int(exc.code),
            payload,
            duration,
            f"http_error:{exc.code}",
        )

    except Exception as exc:
        return (
            0,
            None,
            elapsed_ms(
                started
            ),
            type(exc).__name__,
        )


def open_ro(
    path: Path,
) -> sqlite3.Connection:
    connection = sqlite3.connect(
        f"file:{path}?mode=ro",
        uri=True,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA query_only = ON"
    )

    return connection


def one_int(
    connection: sqlite3.Connection,
    sql: str,
    args: tuple[Any, ...] = (),
) -> int:
    row = connection.execute(
        sql,
        args,
    ).fetchone()

    if row is None:
        return 0

    return int(
        row[0]
        or 0
    )


def timed_query(
    connection: sqlite3.Connection,
    sql: str,
    args: tuple[Any, ...] = (),
    repeats: int = 5,
) -> dict[str, Any]:
    durations: list[float] = []
    row_count = 0

    for _ in range(
        repeats
    ):
        started = (
            time.perf_counter()
        )

        rows = connection.execute(
            sql,
            args,
        ).fetchall()

        durations.append(
            elapsed_ms(
                started
            )
        )

        row_count = len(
            rows
        )

    return {
        "repeats":
            repeats,
        "row_count":
            row_count,
        "durations_ms":
            durations,
        "median_ms":
            round(
                statistics.median(
                    durations
                ),
                3,
            ),
        "max_ms":
            round(
                max(
                    durations
                ),
                3,
            ),
    }


def choose_samples(
    tv: sqlite3.Connection,
    epg: sqlite3.Connection,
    now_ms: int,
) -> list[dict[str, Any]]:
    favorite_rows = tv.execute(
        """
        SELECT
            channel_id,
            COALESCE(
                NULLIF(custom_name, ''),
                name
            ) AS display_name
        FROM streams
        WHERE
            favorite = 1
            AND manual_hidden = 0
            AND auto_hidden = 0
            AND TRIM(channel_id) <> ''
        ORDER BY
            favorite_group COLLATE NOCASE,
            favorite_order ASC,
            display_name COLLATE NOCASE
        LIMIT 40
        """
    ).fetchall()

    visible_rows = tv.execute(
        """
        SELECT
            channel_id,
            COALESCE(
                NULLIF(custom_name, ''),
                name
            ) AS display_name
        FROM streams
        WHERE
            manual_hidden = 0
            AND auto_hidden = 0
            AND TRIM(channel_id) <> ''
        ORDER BY
            display_name COLLATE NOCASE
        LIMIT 100
        """
    ).fetchall()

    cached_ids = {
        str(
            row[0]
        )
        for row in epg.execute(
            """
            SELECT DISTINCT channel_id
            FROM programmes
            WHERE stop_ms > ?
            """,
            (
                now_ms
                - 2 * 60 * 60 * 1000,
            ),
        ).fetchall()
    }

    samples: list[
        dict[str, Any]
    ] = []

    used: set[
        str
    ] = set()

    def add(
        row: sqlite3.Row,
        reason: str,
    ) -> None:
        channel_id = str(
            row[
                "channel_id"
            ]
            or ""
        ).strip()

        if (
            not channel_id
            or channel_id
                in used
            or len(samples)
                >= 3
        ):
            return

        used.add(
            channel_id
        )

        samples.append(
            {
                "channel_id":
                    channel_id,
                "display_name":
                    str(
                        row[
                            "display_name"
                        ]
                        or ""
                    ),
                "selection_reason":
                    reason,
                "android_cached_programmes":
                    channel_id
                    in cached_ids,
            }
        )

    for row in favorite_rows:
        channel_id = str(
            row[
                "channel_id"
            ]
            or ""
        ).strip()

        if (
            channel_id
            and channel_id
                in cached_ids
        ):
            add(
                row,
                "favorite_with_android_cache",
            )
            break

    for row in favorite_rows:
        channel_id = str(
            row[
                "channel_id"
            ]
            or ""
        ).strip()

        if (
            channel_id
            and channel_id
                not in cached_ids
        ):
            add(
                row,
                "favorite_without_android_cache",
            )
            break

    for row in favorite_rows:
        add(
            row,
            "additional_favorite",
        )

    for row in visible_rows:
        add(
            row,
            "visible_channel_fallback",
        )

    return samples


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

    repo = Path(
        args.repo
    ).resolve()

    d116 = load_d116(
        repo
    )

    if args.self_test:
        assert round(
            statistics.median(
                [
                    1.0,
                    2.0,
                    3.0,
                ]
            ),
            3,
        ) == 2.0

        print(
            "D124_PROBE_SELF_TEST_OK"
        )
        return 0

    report: dict[
        str,
        Any,
    ] = {
        "probe":
            "D124 TV/EPG latency",
        "read_only":
            True,
        "limitations": [
            (
                "SQLite timings run against read-only onn snapshots on Linux, "
                "so they can identify expensive query shapes but do not equal "
                "onn CPU/render timings."
            ),
            (
                "This probe cannot directly measure Android view construction "
                "or render time. If DB/API stages are fast, Android-side "
                "instrumentation is the next diagnostic."
            ),
        ],
    }

    status_http, status_payload, status_ms, status_error = (
        http_json(
            "/status",
            timeout_s=10,
        )
    )

    epg_status_http, epg_status, epg_status_ms, epg_status_error = (
        http_json(
            "/plugins/epg/status",
            timeout_s=10,
        )
    )

    report[
        "companion"
    ] = {
        "status_http":
            status_http,
        "status_ms":
            status_ms,
        "status_error":
            status_error,
        "epg_status_http":
            epg_status_http,
        "epg_status_ms":
            epg_status_ms,
        "epg_status_error":
            epg_status_error,
        "epg_ready":
            (
                bool(
                    epg_status.get(
                        "ready"
                    )
                )
                if isinstance(
                    epg_status,
                    dict,
                )
                else False
            ),
    }

    serial, adb_info = (
        d116.adb_serial()
    )

    report[
        "adb"
    ] = {
        "status":
            adb_info.get(
                "reason"
            ),
        "ready":
            bool(
                serial
            ),
    }

    if not serial:
        report[
            "classification"
        ] = (
            "D124_ADB_UNAVAILABLE"
        )

        return finish(
            repo,
            report,
        )

    with tempfile.TemporaryDirectory(
        prefix="d124_tv_epg_"
    ) as temp_dir:
        temp = Path(
            temp_dir
        )

        started = (
            time.perf_counter()
        )

        tv_path = d116.snapshot_db(
            serial,
            "privyhub_tv.db",
            temp,
        )

        tv_snapshot_ms = elapsed_ms(
            started
        )

        started = (
            time.perf_counter()
        )

        epg_path = d116.snapshot_db(
            serial,
            "privyhub_epg.db",
            temp,
        )

        epg_snapshot_ms = elapsed_ms(
            started
        )

        report[
            "adb_snapshots"
        ] = {
            "tv_db_ok":
                tv_path is not None,
            "tv_db_ms":
                tv_snapshot_ms,
            "epg_db_ok":
                epg_path is not None,
            "epg_db_ms":
                epg_snapshot_ms,
        }

        if (
            tv_path is None
            or epg_path is None
        ):
            report[
                "classification"
            ] = (
                "D124_ADB_SNAPSHOT_FAILED"
            )

            return finish(
                repo,
                report,
            )

        now_ms = int(
            time.time()
            * 1000
        )

        with (
            open_ro(
                tv_path
            ) as tv,
            open_ro(
                epg_path
            ) as epg,
        ):
            total_streams = one_int(
                tv,
                """
                SELECT COUNT(*)
                FROM streams
                WHERE
                    manual_hidden = 0
                    AND auto_hidden = 0
                """,
            )

            favorite_streams = one_int(
                tv,
                """
                SELECT COUNT(*)
                FROM streams
                WHERE
                    favorite = 1
                    AND manual_hidden = 0
                    AND auto_hidden = 0
                """,
            )

            fallback_mappings = one_int(
                epg,
                """
                SELECT COUNT(*)
                FROM guide_mappings
                """,
            )

            programme_rows = one_int(
                epg,
                """
                SELECT COUNT(*)
                FROM programmes
                """,
            )

            programme_channels = one_int(
                epg,
                """
                SELECT COUNT(
                    DISTINCT channel_id
                )
                FROM programmes
                """,
            )

            active_programme_channels = one_int(
                epg,
                """
                SELECT COUNT(
                    DISTINCT channel_id
                )
                FROM programmes
                WHERE
                    stop_ms > ?
                    AND start_ms < ?
                """,
                (
                    now_ms,
                    now_ms
                    + 48 * 60 * 60 * 1000,
                ),
            )

            favorite_channel_count = one_int(
                tv,
                """
                SELECT COUNT(
                    DISTINCT channel_id
                )
                FROM streams
                WHERE
                    favorite = 1
                    AND manual_hidden = 0
                    AND auto_hidden = 0
                    AND TRIM(channel_id) <> ''
                """,
            )

            favorite_cached_channels = one_int(
                tv,
                """
                SELECT COUNT(
                    DISTINCT s.channel_id
                )
                FROM streams AS s
                WHERE
                    s.favorite = 1
                    AND s.manual_hidden = 0
                    AND s.auto_hidden = 0
                    AND TRIM(
                        s.channel_id
                    ) <> ''
                    AND EXISTS (
                        SELECT 1
                        FROM programmes AS p
                        WHERE
                            p.channel_id =
                                s.channel_id
                            AND p.stop_ms > ?
                    )
                """,
                (
                    now_ms,
                ),
            )

            favorite_cache_ratio = (
                round(
                    favorite_cached_channels
                    / favorite_channel_count,
                    4,
                )
                if favorite_channel_count > 0
                else None
            )

            favorite_count_query = timed_query(
                tv,
                """
                SELECT COUNT(*)
                FROM (
                    SELECT
                        CASE
                            WHEN TRIM(channel_id) <> ''
                                THEN channel_id
                            ELSE url
                        END AS identity
                    FROM streams
                    WHERE
                        favorite = 1
                        AND manual_hidden = 0
                        AND auto_hidden = 0
                    GROUP BY identity
                )
                """,
            )

            favorite_page_query = timed_query(
                tv,
                """
                SELECT
                    channel_id,
                    COALESCE(
                        NULLIF(custom_name, ''),
                        name
                    ) AS display_name,
                    favorite_group,
                    favorite_order
                FROM streams
                WHERE
                    favorite = 1
                    AND manual_hidden = 0
                    AND auto_hidden = 0
                GROUP BY
                    CASE
                        WHEN TRIM(channel_id) <> ''
                            THEN channel_id
                        ELSE url
                    END
                ORDER BY
                    favorite_group COLLATE NOCASE,
                    favorite_order ASC,
                    display_name COLLATE NOCASE
                LIMIT 50
                """,
            )

            epg_cached_page_query = timed_query(
                epg,
                """
                SELECT
                    channel_id,
                    start_ms,
                    stop_ms,
                    title
                FROM programmes
                WHERE
                    stop_ms > ?
                ORDER BY
                    channel_id,
                    start_ms
                LIMIT 500
                """,
                (
                    now_ms,
                ),
            )

            samples = choose_samples(
                tv,
                epg,
                now_ms,
            )

            for sample in samples:
                channel_id = sample[
                    "channel_id"
                ]

                sample[
                    "android_programme_rows"
                ] = one_int(
                    epg,
                    """
                    SELECT COUNT(*)
                    FROM programmes
                    WHERE
                        channel_id = ?
                        AND stop_ms > ?
                    """,
                    (
                        channel_id,
                        now_ms
                        - 2 * 60 * 60 * 1000,
                    ),
                )

                refresh_key = (
                    "channel_refresh:"
                    + channel_id
                )

                row = epg.execute(
                    """
                    SELECT value
                    FROM meta
                    WHERE key = ?
                    LIMIT 1
                    """,
                    (
                        refresh_key,
                    ),
                ).fetchone()

                refresh_ms = (
                    int(
                        row[
                            "value"
                        ]
                    )
                    if (
                        row is not None
                        and str(
                            row[
                                "value"
                            ]
                        ).isdigit()
                    )
                    else 0
                )

                sample[
                    "android_refresh_age_ms"
                ] = (
                    max(
                        0,
                        now_ms
                        - refresh_ms,
                    )
                    if refresh_ms > 0
                    else None
                )

            report[
                "android_snapshot"
            ] = {
                "visible_streams":
                    total_streams,
                "favorite_streams":
                    favorite_streams,
                "favorite_distinct_channel_ids":
                    favorite_channel_count,
                "fallback_guide_mappings":
                    fallback_mappings,
                "programme_rows":
                    programme_rows,
                "programme_channels":
                    programme_channels,
                "active_programme_channels":
                    active_programme_channels,
                "favorite_channels_with_current_or_future_programmes":
                    favorite_cached_channels,
                "favorite_programme_cache_ratio":
                    favorite_cache_ratio,
                "representative_query_timings": {
                    "favorite_dedup_count":
                        favorite_count_query,
                    "favorite_first_50":
                        favorite_page_query,
                    "epg_first_500_active_rows":
                        epg_cached_page_query,
                },
            }

            report[
                "samples"
            ] = samples

        guide_results: list[
            dict[str, Any]
        ] = []

        for sample in report[
            "samples"
        ]:
            encoded = urllib.parse.quote(
                sample[
                    "channel_id"
                ],
                safe="",
            )

            (
                guide_http,
                guide_payload,
                guide_ms,
                guide_error,
            ) = http_json(
                (
                    "/plugins/epg/guide"
                    f"?channel_id={encoded}"
                ),
                timeout_s=GUIDE_TIMEOUT_S,
            )

            programmes = (
                guide_payload.get(
                    "programmes"
                )
                if isinstance(
                    guide_payload,
                    dict,
                )
                else None
            )

            guide_results.append(
                {
                    "channel_id":
                        sample[
                            "channel_id"
                        ],
                    "display_name":
                        sample[
                            "display_name"
                        ],
                    "selection_reason":
                        sample[
                            "selection_reason"
                        ],
                    "android_cached_programmes":
                        sample[
                            "android_cached_programmes"
                        ],
                    "http":
                        guide_http,
                    "duration_ms":
                        guide_ms,
                    "error":
                        guide_error,
                    "ok":
                        (
                            bool(
                                guide_payload.get(
                                    "ok"
                                )
                            )
                            if isinstance(
                                guide_payload,
                                dict,
                            )
                            else False
                        ),
                    "cached":
                        (
                            guide_payload.get(
                                "cached"
                            )
                            if isinstance(
                                guide_payload,
                                dict,
                            )
                            else None
                        ),
                    "stale":
                        (
                            guide_payload.get(
                                "stale"
                            )
                            if isinstance(
                                guide_payload,
                                dict,
                            )
                            else None
                        ),
                    "programme_count":
                        (
                            len(
                                programmes
                            )
                            if isinstance(
                                programmes,
                                list,
                            )
                            else 0
                        ),
                    "source":
                        (
                            guide_payload.get(
                                "source"
                            )
                            if isinstance(
                                guide_payload,
                                dict,
                            )
                            else None
                        ),
                    "empty_reason":
                        (
                            guide_payload.get(
                                "empty_reason"
                            )
                            if isinstance(
                                guide_payload,
                                dict,
                            )
                            else None
                        ),
                }
            )

        report[
            "companion_guide_samples"
        ] = guide_results

    guide_durations = [
        float(
            item[
                "duration_ms"
            ]
        )
        for item in report.get(
            "companion_guide_samples",
            []
        )
        if item.get(
            "http"
        ) == 200
    ]

    max_guide_ms = (
        max(
            guide_durations
        )
        if guide_durations
        else None
    )

    android_snapshot = report.get(
        "android_snapshot",
        {}
    )

    favorite_ratio = android_snapshot.get(
        "favorite_programme_cache_ratio"
    )

    query_timings = android_snapshot.get(
        "representative_query_timings",
        {}
    )

    max_host_query_ms = 0.0

    for value in query_timings.values():
        if isinstance(
            value,
            dict,
        ):
            max_host_query_ms = max(
                max_host_query_ms,
                float(
                    value.get(
                        "max_ms",
                        0.0,
                    )
                    or 0.0
                ),
            )

    epg_ready = bool(
        report[
            "companion"
        ][
            "epg_ready"
        ]
    )

    if (
        status_http != 200
        or epg_status_http != 200
        or not epg_ready
    ):
        classification = (
            "D124_COMPANION_EPG_UNAVAILABLE"
        )
    elif not guide_results:
        classification = (
            "D124_NO_GUIDE_SAMPLE_CHANNELS"
        )
    elif (
        max_guide_ms is not None
        and max_guide_ms >= 2000.0
    ):
        classification = (
            "D124_COMPANION_GUIDE_FETCH_LATENCY_OBSERVED"
        )
    elif (
        favorite_ratio is not None
        and favorite_ratio < 0.5
    ):
        classification = (
            "D124_ANDROID_EPG_CACHE_COVERAGE_GAP"
        )
    elif max_host_query_ms >= 200.0:
        classification = (
            "D124_REPRESENTATIVE_SQLITE_QUERY_EXPENSIVE"
        )
    else:
        classification = (
            "D124_EXTERNAL_TIMING_DOES_NOT_EXPLAIN_UI_LATENCY"
        )

    report[
        "classification"
    ] = classification

    report[
        "analysis"
    ] = {
        "max_successful_companion_guide_ms":
            (
                round(
                    max_guide_ms,
                    3,
                )
                if max_guide_ms is not None
                else None
            ),
        "max_host_snapshot_query_ms":
            round(
                max_host_query_ms,
                3,
            ),
        "favorite_programme_cache_ratio":
            favorite_ratio,
        "next_diagnostic":
            (
                "Android-side timing instrumentation is justified if the "
                "classification is D124_EXTERNAL_TIMING_DOES_NOT_EXPLAIN_UI_LATENCY."
            ),
    }

    return finish(
        repo,
        report,
    )


def finish(
    repo: Path,
    report: dict[str, Any],
) -> int:
    json_path = (
        repo
        / LOG_JSON_REL
    )

    text_path = (
        repo
        / LOG_TEXT_REL
    )

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report[
        "json_path"
    ] = str(
        json_path
    )

    report[
        "text_path"
    ] = str(
        text_path
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    companion = report.get(
        "companion",
        {}
    )

    snapshots = report.get(
        "adb_snapshots",
        {}
    )

    android = report.get(
        "android_snapshot",
        {}
    )

    analysis = report.get(
        "analysis",
        {}
    )

    lines = [
        "PrivyHub D-124 TV/EPG latency probe",
        f"Classification: {report.get('classification')}",
        "",
        "COMPANION BASELINE",
        f"  status_http: {companion.get('status_http')}",
        f"  status_ms: {companion.get('status_ms')}",
        f"  epg_status_http: {companion.get('epg_status_http')}",
        f"  epg_status_ms: {companion.get('epg_status_ms')}",
        f"  epg_ready: {companion.get('epg_ready')}",
        "",
        "ADB SNAPSHOT",
        f"  adb_status: {report.get('adb', {}).get('status')}",
        f"  tv_db_ok: {snapshots.get('tv_db_ok')}",
        f"  tv_db_ms: {snapshots.get('tv_db_ms')}",
        f"  epg_db_ok: {snapshots.get('epg_db_ok')}",
        f"  epg_db_ms: {snapshots.get('epg_db_ms')}",
        "",
        "ANDROID CACHE COVERAGE",
        f"  visible_streams: {android.get('visible_streams')}",
        f"  favorite_streams: {android.get('favorite_streams')}",
        f"  favorite_distinct_channel_ids: {android.get('favorite_distinct_channel_ids')}",
        f"  fallback_guide_mappings: {android.get('fallback_guide_mappings')}",
        f"  programme_rows: {android.get('programme_rows')}",
        f"  programme_channels: {android.get('programme_channels')}",
        f"  active_programme_channels: {android.get('active_programme_channels')}",
        f"  favorite_channels_with_current_or_future_programmes: {android.get('favorite_channels_with_current_or_future_programmes')}",
        f"  favorite_programme_cache_ratio: {android.get('favorite_programme_cache_ratio')}",
        "",
        "REPRESENTATIVE SQLITE TIMINGS (LINUX SNAPSHOT; NOT ONN RENDER TIME)",
    ]

    for name, value in (
        android.get(
            "representative_query_timings",
            {}
        ).items()
    ):
        lines.append(
            (
                f"  {name}: "
                f"median={value.get('median_ms')} ms, "
                f"max={value.get('max_ms')} ms, "
                f"rows={value.get('row_count')}"
            )
        )

    lines.extend(
        [
            "",
            "COMPANION GUIDE SAMPLES",
        ]
    )

    for item in report.get(
        "companion_guide_samples",
        []
    ):
        lines.append(
            (
                "  "
                f"{item.get('display_name') or item.get('channel_id')}: "
                f"{item.get('duration_ms')} ms, "
                f"http={item.get('http')}, "
                f"cached={item.get('cached')}, "
                f"stale={item.get('stale')}, "
                f"programmes={item.get('programme_count')}, "
                f"android_cache={item.get('android_cached_programmes')}, "
                f"reason={item.get('selection_reason')}"
            )
        )

    lines.extend(
        [
            "",
            "SUMMARY",
            f"  max_successful_companion_guide_ms: {analysis.get('max_successful_companion_guide_ms')}",
            f"  max_host_snapshot_query_ms: {analysis.get('max_host_snapshot_query_ms')}",
            f"  favorite_programme_cache_ratio: {analysis.get('favorite_programme_cache_ratio')}",
            "",
            "This probe is read-only.",
            "SQLite timing is measured from onn snapshots on Linux and is not treated as Android UI/render timing.",
            "If external DB/API stages are fast, the next diagnostic is Android-side timing instrumentation.",
            "No network address or device identifier is written to this report.",
            f"JSON: {json_path}",
            f"TEXT: {text_path}",
        ]
    )

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


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
