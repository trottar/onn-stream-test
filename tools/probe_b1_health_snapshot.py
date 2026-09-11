#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CLASSIFICATION = "B1_HEALTH_MODEL_SNAPSHOT_CAPTURED"
UNAVAILABLE_CLASSIFICATION = "B1_HEALTH_MODEL_COMPANION_UNAVAILABLE"

ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[1]
COMPANION_DIR = ROOT_FROM_SCRIPT / "companion"

if str(COMPANION_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(COMPANION_DIR),
    )

from diagnostics.health_model import (  # noqa: E402
    HEALTH_SCHEMA,
    RESOURCE_SCHEMA,
    build_health_snapshot,
)


def request_json(
    path: str,
) -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765"
        + path,
        headers={
            "Cache-Control": "no-cache",
        },
        method="GET",
    )

    with urllib.request.urlopen(
        request,
        timeout=3.0,
    ) as response:
        payload = json.loads(
            response.read().decode(
                "utf-8"
            )
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            f"{path} did not return a JSON object"
        )

    return payload


def host_telemetry_payload(
    root: Path,
    games_status: dict[str, Any],
) -> dict[str, Any] | None:
    native = (
        games_status.get(
            "native_stream"
        )
    )
    if not isinstance(
        native,
        dict,
    ):
        return None

    telemetry = (
        native.get(
            "host_telemetry"
        )
    )
    if not isinstance(
        telemetry,
        dict,
    ):
        return None

    raw_path = telemetry.get(
        "path"
    )
    if not isinstance(
        raw_path,
        str,
    ) or not raw_path.strip():
        return None

    try:
        path = Path(
            raw_path
        ).resolve()
        allowed = (
            root
            / "logs"
            / "games"
            / "host_telemetry"
        ).resolve()
        path.relative_to(
            allowed
        )
    except (
        OSError,
        ValueError,
    ):
        return None

    try:
        if (
            not path.is_file()
            or path.stat().st_size
            > 8 * 1024 * 1024
        ):
            return None

        payload = json.loads(
            path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    return (
        payload
        if isinstance(
            payload,
            dict,
        )
        else None
    )


def component_lookup(
    snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    result = {}

    for item in snapshot.get(
        "components",
        [],
    ):
        if not isinstance(
            item,
            dict,
        ):
            continue

        key = str(
            item.get(
                "component",
                "",
            )
        )
        if key:
            result[key] = item

    return result


def value_or_none(
    value: Any,
) -> str:
    if value is None:
        return "<unknown>"
    return str(value)


def resource_line(
    process: dict[str, Any],
    metric: str,
) -> str:
    aggregate = (
        process.get(
            "aggregate"
        )
        if isinstance(
            process.get(
                "aggregate"
            ),
            dict,
        )
        else {}
    )
    latest = (
        process.get(
            "latest"
        )
        if isinstance(
            process.get(
                "latest"
            ),
            dict,
        )
        else {}
    )

    stats = (
        aggregate.get(
            metric
        )
        if isinstance(
            aggregate.get(
                metric
            ),
            dict,
        )
        else {}
    )

    return (
        f"latest={value_or_none(latest.get(metric))} "
        f"avg={value_or_none(stats.get('avg'))} "
        f"max={value_or_none(stats.get('max'))}"
    )


def format_text(
    snapshot: dict[str, Any],
) -> str:
    overall = snapshot[
        "overall"
    ]
    coverage = snapshot[
        "coverage"
    ]
    resource = snapshot[
        "resources"
    ]

    lines = [
        "PrivyHub Phase B1.2 unified health/resource model runtime snapshot",
        f"Classification: {CLASSIFICATION}",
        f"Health schema: {snapshot['schema']}",
        f"Resource schema: {resource['schema']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== OVERALL ===",
        f"Health: {overall['health']}",
        f"Severity: {overall['severity']}",
        f"Event code: {overall['event_code']}",
        f"Summary: {overall['summary']}",
        f"Component count: {coverage['component_count']}",
        "Unknown is failure: False",
        "",
        "=== COMPONENTS ===",
    ]

    for item in snapshot[
        "components"
    ]:
        lines.append(
            f"{item['component']}: "
            f"health={item['health']} "
            f"severity={item['severity']} "
            f"event={item['event_code']}"
        )

    sampling = resource[
        "sampling"
    ]
    processes = resource[
        "processes"
    ]

    lines += [
        "",
        "=== RESOURCE OBSERVABILITY ===",
        f"Availability: {resource['availability']}",
        f"Measurement scope: {resource['measurement_scope']}",
        f"Sampling active: {sampling['active']}",
        "Sample interval seconds: "
        + value_or_none(
            sampling.get(
                "sample_interval_seconds"
            )
        ),
        f"Sample count: {sampling['sample_count']}",
        "Logical CPU count: "
        + value_or_none(
            resource.get(
                "logical_cpu_count"
            )
        ),
        "Capture process CPU host %: "
        + resource_line(
            processes["capture"],
            "cpu_total_host_percent",
        ),
        "Capture working set MiB: "
        + resource_line(
            processes["capture"],
            "working_set_mib",
        ),
        "Encoder process CPU host %: "
        + resource_line(
            processes["encoder"],
            "cpu_total_host_percent",
        ),
        "Encoder working set MiB: "
        + resource_line(
            processes["encoder"],
            "working_set_mib",
        ),
        "GPU utilization available: "
        + str(
            "gpu_utilization_percent"
            not in resource[
                "unavailable_metrics"
            ]
        ),
        "Encoder-engine utilization available: "
        + str(
            "encoder_engine_utilization_percent"
            not in resource[
                "unavailable_metrics"
            ]
        ),
        "Host total/available RAM available: "
        + str(
            "host_total_memory_mib"
            not in resource[
                "unavailable_metrics"
            ]
        ),
        "Capacity classification: "
        + str(
            resource[
                "optimization"
            ][
                "capacity_classification"
            ]
        ),
        "Stream profile fit: "
        + str(
            resource[
                "optimization"
            ][
                "stream_profile_fit"
            ]
        ),
        "Benchmark thresholds applied: "
        + str(
            resource[
                "optimization"
            ][
                "benchmark_thresholds_applied"
            ]
        ),
        "",
        "=== FUTURE-OPTIMIZATION GAPS ===",
    ]

    lookup = component_lookup(
        snapshot
    )
    network = lookup.get(
        "end_to_end_path",
        {},
    )
    decoder = lookup.get(
        "decoder",
        {},
    )

    lines += [
        "Network path feedback health: "
        + str(
            network.get(
                "health",
                "<missing>",
            )
        ),
        "Network path event: "
        + str(
            network.get(
                "event_code",
                "<missing>",
            )
        ),
        "Client decoder aggregation health: "
        + str(
            decoder.get(
                "health",
                "<missing>",
            )
        ),
        "Client decoder event: "
        + str(
            decoder.get(
                "event_code",
                "<missing>",
            )
        ),
        "",
        "Recommended next step: INTEGRATE_HEALTH_ENDPOINT_THEN_ADD_CLIENT_FEEDBACK",
    ]

    return "\n".join(
        lines
    ) + "\n"


def self_test() -> int:
    private_value = ".".join(
        [
            "192",
            "168",
            "7",
            "42",
        ]
    )
    secret_value = (
        "fixture-secret-value"
    )
    fake_path = (
        "X:"
        + "\\"
        + "fixture"
        + "\\"
        + "telemetry.json"
    )

    companion = {
        "service": "PrivyHub",
        "api_version": 4,
        "project_root": private_value,
        "server": {
            "running": True,
            "pid": 1234,
            "log": fake_path,
        },
    }
    games = {
        "active": True,
        "paused": False,
        "secret": secret_value,
        "native_stream": {
            "ready": True,
            "active": True,
            "wgc_runtime_found": True,
            "capture_backend": (
                "windows_graphics_capture"
            ),
            "capture_target": {
                "pid": 999,
                "title": secret_value,
                "peer": private_value,
            },
            "width": 1280,
            "height": 720,
            "fps": 60,
            "source_bitrate_kbps": 7000,
            "fec_enabled": True,
            "fec_group_size": 8,
            "fec": {
                "running": True,
                "group_size": 8,
                "rtp_packets": 120,
                "rtp_bytes": 100000,
                "parity_packets": 15,
                "parity_bytes": 12000,
                "skipped_packets": 0,
                "send_errors": 0,
                "local_port": 12345,
            },
            "audio": {
                "active": True,
                "sample_rate": 48000,
                "channels": 2,
                "packet_ms": 5,
                "packets_sent": 50,
                "send_errors": 0,
                "target_pid": 999,
                "port": 1234,
                "helper_status": {
                    "destination": private_value,
                },
            },
            "controller": {
                "active": True,
                "players": 4,
                "packets_received": 20,
                "lost_packets": 0,
                "rejected_packets": 0,
                "bad_packets": 0,
                "vigem_updates": 20,
                "port": 9999,
            },
            "host_telemetry": {
                "active": True,
                "samples": 2,
                "sample_interval_seconds": 2.0,
                "path": fake_path,
                "error": "",
            },
        },
    }
    telemetry = {
        "schema": (
            "privyhub_native_host_telemetry_v1"
        ),
        "logical_cpu_count": 8,
        "sample_count": 2,
        "sample_interval_seconds": 2.0,
        "capture_target": {
            "pid": 999,
            "title": secret_value,
        },
        "processes": {
            "capture": {
                "pid": 999,
                "cpu_total_host_percent": {
                    "avg": 4.0,
                    "max": 5.0,
                },
                "working_set_mib": {
                    "avg": 40.0,
                    "max": 42.0,
                },
            },
            "ffmpeg": {
                "pid": 1000,
                "cpu_total_host_percent": {
                    "avg": 3.0,
                    "max": 4.0,
                },
                "working_set_mib": {
                    "avg": 80.0,
                    "max": 82.0,
                },
            },
        },
        "latest_wgc": {
            "emitted_frames": 120,
            "copy_time_avg_ms": 0.2,
        },
        "samples": [
            {
                "capture_process": {
                    "pid": 999,
                    "cpu_total_host_percent": 5.0,
                    "working_set_mib": 42.0,
                },
                "ffmpeg_process": {
                    "pid": 1000,
                    "cpu_total_host_percent": 4.0,
                    "working_set_mib": 82.0,
                },
            }
        ],
        "path": fake_path,
        "error": "",
    }

    snapshot = build_health_snapshot(
        companion_status=companion,
        games_status=games,
        host_telemetry_payload=telemetry,
        generated_unix_ms=1,
    )

    encoded = json.dumps(
        snapshot,
        sort_keys=True,
    )

    assert snapshot[
        "schema"
    ] == HEALTH_SCHEMA
    assert snapshot[
        "resources"
    ][
        "schema"
    ] == RESOURCE_SCHEMA
    assert snapshot[
        "resources"
    ][
        "optimization"
    ][
        "benchmark_thresholds_applied"
    ] is False
    assert snapshot[
        "resources"
    ][
        "optimization"
    ][
        "capacity_classification"
    ] == "unclassified"
    assert private_value not in encoded
    assert secret_value not in encoded
    assert fake_path not in encoded
    assert '"pid"' not in encoded
    assert '"port"' not in encoded
    assert "local_port" not in encoded
    assert (
        component_lookup(
            snapshot
        )[
            "video_transport"
        ][
            "health"
        ]
        == "healthy"
    )
    assert (
        component_lookup(
            snapshot
        )[
            "host_resources"
        ][
            "health"
        ]
        == "healthy"
    )

    broken = json.loads(
        json.dumps(
            games
        )
    )
    broken[
        "native_stream"
    ][
        "fec"
    ][
        "send_errors"
    ] = 2

    degraded = build_health_snapshot(
        companion_status=companion,
        games_status=broken,
        host_telemetry_payload=telemetry,
        generated_unix_ms=2,
    )

    assert (
        component_lookup(
            degraded
        )[
            "video_transport"
        ][
            "health"
        ]
        == "degraded"
    )
    assert (
        degraded[
            "overall"
        ][
            "health"
        ]
        == "degraded"
    )

    return 0


def write_unavailable(
    root: Path,
    detail: str,
) -> int:
    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Do not echo URL/socket detail; only the error class is useful here.
    text = "\n".join(
        [
            "PrivyHub Phase B1.2 unified health/resource model runtime snapshot",
            f"Classification: {UNAVAILABLE_CLASSIFICATION}",
            "Production files modified by probe: NONE",
            "Network addresses collected/logged: NONE",
            "Companion status available: False",
            "Error class: " + detail,
            "",
        ]
    )

    (
        out_dir
        / "b1_health_snapshot.txt"
    ).write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default=".",
    )
    ap.add_argument(
        "--self-test",
        action="store_true",
    )
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(
        args.root
    ).resolve()

    try:
        companion = request_json(
            "/status"
        )
        games = request_json(
            "/plugins/games/status"
        )
    except (
        urllib.error.URLError,
        TimeoutError,
        ConnectionError,
        OSError,
        ValueError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return write_unavailable(
            root,
            type(exc).__name__,
        )

    telemetry = host_telemetry_payload(
        root,
        games,
    )

    snapshot = build_health_snapshot(
        companion_status=companion,
        games_status=games,
        host_telemetry_payload=telemetry,
        generated_unix_ms=int(
            time.time()
            * 1000.0
        ),
    )

    out_dir = (
        root
        / "logs"
        / "diagnostics"
    )
    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        out_dir
        / "b1_health_snapshot.json"
    )
    text_path = (
        out_dir
        / "b1_health_snapshot.txt"
    )

    json_path.write_text(
        json.dumps(
            snapshot,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    text_path.write_text(
        format_text(
            snapshot
        ),
        encoding="utf-8",
        newline="\n",
    )

    print(
        CLASSIFICATION
    )
    print(
        "Text:",
        text_path,
    )
    print(
        "JSON:",
        json_path,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
