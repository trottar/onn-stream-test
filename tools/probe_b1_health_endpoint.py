#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

CLASSIFICATION = (
    "B1_HEALTH_ENDPOINT_CONFIRMED"
)
FAILED = (
    "B1_HEALTH_ENDPOINT_NOT_CONFIRMED"
)

REQUIRED_COMPONENTS = {
    "companion",
    "media_server",
    "game_session",
    "native_stream",
    "capture",
    "video_transport",
    "audio",
    "controller_bridge",
    "host_resources",
    "end_to_end_path",
    "decoder",
}

FORBIDDEN_KEYS = {
    "pid",
    "port",
    "local_port",
    "target_pid",
    "client_ip",
    "project_root",
    "media_root",
    "path",
    "capture_target",
    "title",
    "window",
}

IPV4 = re.compile(
    r"(?<!\d)"
    r"(?:\d{1,3}\.){3}"
    r"\d{1,3}"
    r"(?!\d)"
)

MAC = re.compile(
    r"(?i)"
    r"(?<![0-9a-f])"
    r"(?:[0-9a-f]{2}[:-]){5}"
    r"[0-9a-f]{2}"
    r"(?![0-9a-f])"
)


def request_health() -> dict[str, Any]:
    request = urllib.request.Request(
        "http://127.0.0.1:8765"
        "/diagnostics/health",
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
            "Health endpoint did not return an object"
        )

    return payload


def walk(
    value: Any,
    *,
    keys: set[str],
    strings: list[str],
) -> None:
    if isinstance(
        value,
        dict,
    ):
        for key, child in value.items():
            keys.add(
                str(
                    key
                )
            )
            walk(
                child,
                keys=keys,
                strings=strings,
            )
        return

    if isinstance(
        value,
        list,
    ):
        for child in value:
            walk(
                child,
                keys=keys,
                strings=strings,
            )
        return

    if isinstance(
        value,
        str,
    ):
        strings.append(
            value
        )


def validate(
    payload: dict[str, Any],
) -> dict[str, Any]:
    components = (
        payload.get(
            "components"
        )
    )
    if not isinstance(
        components,
        list,
    ):
        raise RuntimeError(
            "components is not a list"
        )

    component_names = {
        str(
            item.get(
                "component",
                "",
            )
        )
        for item in components
        if isinstance(
            item,
            dict,
        )
    }

    missing = (
        REQUIRED_COMPONENTS
        - component_names
    )
    if missing:
        raise RuntimeError(
            "Required health components missing"
        )

    resource = (
        payload.get(
            "resources"
        )
    )
    if not isinstance(
        resource,
        dict,
    ):
        raise RuntimeError(
            "resources is not an object"
        )

    collection = (
        payload.get(
            "collection"
        )
    )
    if not isinstance(
        collection,
        dict,
    ):
        raise RuntimeError(
            "collection is not an object"
        )

    if (
        payload.get(
            "schema"
        )
        != "privyhub_diagnostics_health_v1"
    ):
        raise RuntimeError(
            "Health schema mismatch"
        )

    if (
        resource.get(
            "schema"
        )
        != "privyhub_resource_snapshot_v1"
    ):
        raise RuntimeError(
            "Resource schema mismatch"
        )

    optimization = (
        resource.get(
            "optimization"
        )
    )
    if not isinstance(
        optimization,
        dict,
    ):
        raise RuntimeError(
            "optimization is not an object"
        )

    if (
        optimization.get(
            "benchmark_thresholds_applied"
        )
        is not False
    ):
        raise RuntimeError(
            "Unexpected benchmark thresholds applied"
        )

    if (
        optimization.get(
            "capacity_classification"
        )
        != "unclassified"
    ):
        raise RuntimeError(
            "Capacity classification is premature"
        )

    if (
        collection.get(
            "new_resource_sampler_started"
        )
        is not False
    ):
        raise RuntimeError(
            "Endpoint reports a new resource sampler"
        )

    keys: set[
        str
    ] = set()
    strings: list[
        str
    ] = []

    walk(
        payload,
        keys=keys,
        strings=strings,
    )

    forbidden_present = (
        FORBIDDEN_KEYS
        & keys
    )

    if forbidden_present:
        raise RuntimeError(
            "Privacy-forbidden key present"
        )

    for text in strings:
        if (
            IPV4.search(
                text
            )
            or MAC.search(
                text
            )
        ):
            raise RuntimeError(
                "Network identifier detected in endpoint"
            )

    overall = (
        payload.get(
            "overall"
        )
        if isinstance(
            payload.get(
                "overall"
            ),
            dict,
        )
        else {}
    )

    sampling = (
        resource.get(
            "sampling"
        )
        if isinstance(
            resource.get(
                "sampling"
            ),
            dict,
        )
        else {}
    )

    return {
        "health": (
            overall.get(
                "health"
            )
        ),
        "severity": (
            overall.get(
                "severity"
            )
        ),
        "resource_availability": (
            resource.get(
                "availability"
            )
        ),
        "resource_scope": (
            resource.get(
                "measurement_scope"
            )
        ),
        "resource_sample_count": (
            sampling.get(
                "sample_count"
            )
        ),
        "resource_source": (
            collection.get(
                "host_telemetry_payload_source"
            )
        ),
        "games_status_available": bool(
            collection.get(
                "games_status_available"
            )
        ),
        "host_telemetry_available": bool(
            collection.get(
                "host_telemetry_payload_available"
            )
        ),
        "component_count": len(
            component_names
        ),
    }


def write_result(
    root: Path,
    *,
    confirmed: bool,
    result: dict[str, Any] | None,
    error_class: str = "",
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

    classification = (
        CLASSIFICATION
        if confirmed
        else FAILED
    )

    lines = [
        "PrivyHub Phase B1.3 read-only health endpoint runtime probe",
        f"Classification: {classification}",
        "Endpoint: GET /diagnostics/health",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]

    if result is not None:
        lines += [
            "=== MEASUREMENTS ===",
            "Health: "
            + str(
                result.get(
                    "health"
                )
            ),
            "Severity: "
            + str(
                result.get(
                    "severity"
                )
            ),
            "Component count: "
            + str(
                result.get(
                    "component_count"
                )
            ),
            "Games status available: "
            + str(
                result.get(
                    "games_status_available"
                )
            ),
            "Host telemetry available: "
            + str(
                result.get(
                    "host_telemetry_available"
                )
            ),
            "Host telemetry source: "
            + str(
                result.get(
                    "resource_source"
                )
            ),
            "Resource availability: "
            + str(
                result.get(
                    "resource_availability"
                )
            ),
            "Resource measurement scope: "
            + str(
                result.get(
                    "resource_scope"
                )
            ),
            "Resource sample count: "
            + str(
                result.get(
                    "resource_sample_count"
                )
            ),
            "New resource sampler started: False",
            "Benchmark thresholds applied: False",
            "Forbidden privacy keys present: False",
            "Network identifier values present: False",
        ]
    else:
        lines += [
            "=== FAILURE ===",
            "Error class: "
            + (
                error_class
                or "<unknown>"
            ),
        ]

    (
        out_dir
        / "b1_health_endpoint.txt"
    ).write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return (
        0
        if confirmed
        else 1
    )


def self_test() -> int:
    fixture = {
        "schema": (
            "privyhub_diagnostics_health_v1"
        ),
        "overall": {
            "health": "healthy",
            "severity": "info",
        },
        "components": [
            {
                "component": name,
                "subsystem": "fixture",
                "health": "idle",
                "severity": "info",
                "event_code": (
                    "FIXTURE-OK"
                ),
                "summary": "fixture",
                "measurements": {},
                "classification": {
                    "classifier": "fixture",
                    "basis": [],
                },
            }
            for name in sorted(
                REQUIRED_COMPONENTS
            )
        ],
        "resources": {
            "schema": (
                "privyhub_resource_snapshot_v1"
            ),
            "availability": "idle",
            "measurement_scope": "none",
            "sampling": {
                "sample_count": 0,
            },
            "optimization": {
                "benchmark_thresholds_applied": False,
                "capacity_classification": "unclassified",
            },
        },
        "collection": {
            "new_resource_sampler_started": False,
            "host_telemetry_payload_source": "none",
            "games_status_available": True,
            "host_telemetry_payload_available": False,
        },
    }

    result = validate(
        fixture
    )

    assert (
        result[
            "component_count"
        ]
        == len(
            REQUIRED_COMPONENTS
        )
    )

    bad = json.loads(
        json.dumps(
            fixture
        )
    )
    bad[
        "resources"
    ][
        "optimization"
    ][
        "capacity_classification"
    ] = "fast"

    try:
        validate(
            bad
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError(
            "Premature capacity classification was accepted"
        )

    return 0


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
        payload = (
            request_health()
        )
        result = (
            validate(
                payload
            )
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
        return write_result(
            root,
            confirmed=False,
            result=None,
            error_class=(
                type(
                    exc
                ).__name__
            ),
        )

    return write_result(
        root,
        confirmed=True,
        result=result,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
