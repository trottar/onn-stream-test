#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

CLASSIFICATION = "B1_CLIENT_FEEDBACK_SOURCE_CONTEXT_CAPTURED"
SCHEMA = "privyhub_b1_client_feedback_source_context_v1"

TARGETS = {
    "native_stream_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "streaming/NativeStreamActivity.kt"
    ),
    "main_activity": (
        "PrivyHub/app/src/main/java/com/safeiot/privyhub/"
        "MainActivity.kt"
    ),
    "android_manifest": (
        "PrivyHub/app/src/main/AndroidManifest.xml"
    ),
    "companion_service": (
        "companion/privyhub_service.py"
    ),
    "health_model": (
        "companion/diagnostics/health_model.py"
    ),
    "runtime_health": (
        "companion/diagnostics/runtime_health.py"
    ),
    "games_plugin": (
        "companion/plugins/games.py"
    ),
}

METRIC_TOKENS = (
    "recentVideoFps",
    "recentVideoMbps",
    "recent_fps",
    "recent_mbps",
    "rendered",
    "renderedFrames",
    "queued",
    "queuedFrames",
    "stale",
    "staleDrops",
    "fec",
    "recovered",
    "unrecoverable",
    "packets",
    "bytes",
    "jitter",
    "rtt",
    "latency",
    "decoder",
)

SCHEDULER_TOKENS = (
    "Handler(",
    "postDelayed",
    "post(",
    "Timer(",
    "scheduleAtFixedRate",
    "ScheduledExecutor",
    "Thread.sleep",
    "delay(",
)

NETWORK_TOKENS = (
    "HttpURLConnection",
    "URL(",
    "requestMethod",
    "doOutput",
    "outputStream",
    "connectTimeout",
    "readTimeout",
)

JSON_TOKENS = (
    "JSONObject(",
    "JSONArray(",
    ".put(",
    "toString()",
)

LIFECYCLE_METHODS = (
    "onCreate",
    "onStart",
    "onResume",
    "onPause",
    "onStop",
    "onDestroy",
)

SAFE_ENDPOINT_RE = re.compile(
    r'["\'](/(?:diagnostics|plugins|status|sources|stop)[^"\']*)["\']'
)

METHOD_RE = re.compile(
    r"\b(?:private|protected|public|internal)?\s*"
    r"(?:suspend\s+)?fun\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)

ADDRESS_LIKE_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )


def git(
    root: Path,
    *args: str,
) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.rstrip()


def line_numbers(
    text: str,
    token: str,
) -> list[int]:
    result = []
    folded = token.casefold()

    for index, line in enumerate(
        text.splitlines(),
        1,
    ):
        if folded in line.casefold():
            result.append(index)

    return result


def token_inventory(
    text: str,
    tokens: tuple[str, ...],
) -> dict[str, Any]:
    return {
        token: {
            "count": text.casefold().count(
                token.casefold()
            ),
            "lines": line_numbers(
                text,
                token,
            )[:12],
        }
        for token in tokens
    }


def method_inventory(
    text: str,
) -> list[str]:
    return sorted(
        set(
            METHOD_RE.findall(
                text
            )
        )
    )


def lifecycle_inventory(
    methods: list[str],
) -> dict[str, bool]:
    method_set = set(
        methods
    )
    return {
        name: name in method_set
        for name in LIFECYCLE_METHODS
    }


def endpoint_inventory(
    text: str,
) -> list[str]:
    values = []

    for match in SAFE_ENDPOINT_RE.finditer(
        text
    ):
        value = match.group(1)

        if ADDRESS_LIKE_RE.search(
            value
        ):
            continue

        values.append(
            value
        )

    return sorted(
        set(
            values
        )
    )


def target_state(
    root: Path,
    rel: str,
) -> dict[str, Any]:
    path = root / rel
    if not path.is_file():
        return {
            "path": rel,
            "exists": False,
        }

    text = read_text(
        path
    )
    methods = method_inventory(
        text
    )

    return {
        "path": rel,
        "exists": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(
            path
        ),
        "line_count": len(
            text.splitlines()
        ),
        "method_count": len(
            methods
        ),
        "methods": methods,
        "lifecycle": lifecycle_inventory(
            methods
        ),
        "safe_endpoint_literals": endpoint_inventory(
            text
        ),
        "metric_tokens": token_inventory(
            text,
            METRIC_TOKENS,
        ),
        "scheduler_tokens": token_inventory(
            text,
            SCHEDULER_TOKENS,
        ),
        "network_tokens": token_inventory(
            text,
            NETWORK_TOKENS,
        ),
        "json_tokens": token_inventory(
            text,
            JSON_TOKENS,
        ),
    }


def bool_any(
    section: dict[str, Any],
) -> bool:
    return any(
        int(
            item.get(
                "count",
                0,
            )
        )
        > 0
        for item in section.values()
        if isinstance(
            item,
            dict,
        )
    )


def classify(
    report: dict[str, Any],
) -> tuple[str, str]:
    native = report[
        "targets"
    ][
        "native_stream_activity"
    ]

    if not native.get(
        "exists"
    ):
        return (
            "ANDROID_STREAM_SOURCE_MISSING",
            "Inspect current Android source before designing client feedback.",
        )

    has_metrics = (
        native[
            "metric_tokens"
        ][
            "recentVideoFps"
        ][
            "count"
        ]
        > 0
        and native[
            "metric_tokens"
        ][
            "recentVideoMbps"
        ][
            "count"
        ]
        > 0
        and (
            native[
                "metric_tokens"
            ][
                "stale"
            ][
                "count"
            ]
            > 0
            or native[
                "metric_tokens"
            ][
                "rendered"
            ][
                "count"
            ]
            > 0
        )
    )

    has_network = bool_any(
        native[
            "network_tokens"
        ]
    )

    has_scheduler = bool_any(
        native[
            "scheduler_tokens"
        ]
    )

    has_json = bool_any(
        native[
            "json_tokens"
        ]
    )

    endpoints = native.get(
        "safe_endpoint_literals",
        []
    )

    has_existing_diagnostics_post = any(
        value.startswith(
            "/diagnostics/"
        )
        for value in endpoints
    )

    if (
        has_metrics
        and has_network
        and has_scheduler
        and has_json
        and has_existing_diagnostics_post
    ):
        return (
            "REUSE_EXISTING_PERIODIC_DIAGNOSTICS_PATH",
            "Prefer adapting the existing Android timing/network path rather than adding a parallel sender.",
        )

    if (
        has_metrics
        and has_network
        and has_scheduler
        and has_json
    ):
        return (
            "METRICS_AND_PERIODIC_NETWORK_PRIMITIVES_EXIST",
            "A client-feedback sender can likely reuse existing activity timing/network primitives; add one bounded diagnostics request path only if exact context supports it.",
        )

    if (
        has_metrics
        and has_network
        and has_json
    ):
        return (
            "METRICS_AND_NETWORK_EXIST_NO_PERIODIC_PRIMITIVE_CONFIRMED",
            "Do not add a hot loop. Reuse an existing metrics cadence if found in surrounding source, otherwise design one low-rate bounded sender.",
        )

    if has_metrics:
        return (
            "CLIENT_METRICS_EXIST_FEEDBACK_TRANSPORT_NOT_CONFIRMED",
            "Preserve the existing metric producers and audit Android request infrastructure before adding feedback.",
        )

    return (
        "CLIENT_METRIC_SURFACE_INCOMPLETE",
        "Do not implement feedback until the missing decoder/network measurements are identified.",
    )


def build_report(
    root: Path,
) -> dict[str, Any]:
    rc, head = git(
        root,
        "rev-parse",
        "HEAD",
    )
    if rc != 0:
        head = "<unknown>"

    targets = {
        name: target_state(
            root,
            rel,
        )
        for name, rel in TARGETS.items()
    }

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "git_head": head.strip(),
        "targets": targets,
    }

    disposition, recommendation = classify(
        report
    )

    native = targets[
        "native_stream_activity"
    ]

    report[
        "architecture"
    ] = {
        "disposition": disposition,
        "recommendation": recommendation,
        "existing_client_metric_surface": bool(
            native.get(
                "exists"
            )
            and (
                native[
                    "metric_tokens"
                ][
                    "recentVideoFps"
                ][
                    "count"
                ]
                > 0
            )
            and (
                native[
                    "metric_tokens"
                ][
                    "recentVideoMbps"
                ][
                    "count"
                ]
                > 0
            )
        ),
        "existing_android_network_primitives": (
            bool_any(
                native.get(
                    "network_tokens",
                    {},
                )
            )
        ),
        "existing_android_scheduler_primitives": (
            bool_any(
                native.get(
                    "scheduler_tokens",
                    {},
                )
            )
        ),
        "existing_android_json_primitives": (
            bool_any(
                native.get(
                    "json_tokens",
                    {},
                )
            )
        ),
        "existing_diagnostics_endpoint_literal": any(
            value.startswith(
                "/diagnostics/"
            )
            for value in native.get(
                "safe_endpoint_literals",
                []
            )
        ),
        "new_feedback_loop_justified": False,
        "next_step": (
            "INSPECT_EXACT_SOURCE_CONTEXT_THEN_ONE_COHERENT_CLIENT_FEEDBACK_PATCH"
        ),
    }

    return report


def fmt_tokens(
    section: dict[str, Any],
) -> list[str]:
    lines = []
    for token, value in section.items():
        count = int(
            value.get(
                "count",
                0,
            )
        )
        if count <= 0:
            continue
        line_text = ",".join(
            str(item)
            for item in value.get(
                "lines",
                []
            )
        )
        lines.append(
            f"{token}: count={count} lines={line_text or '<none>'}"
        )
    return lines


def format_text(
    report: dict[str, Any],
) -> str:
    lines = [
        "PrivyHub Phase B1.4 Android client-feedback source-context audit",
        f"Classification: {report['classification']}",
        f"Schema: {report['schema']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CHECKPOINT ===",
        f"Git HEAD: {report['git_head']}",
        "",
        "=== EXACT SOURCE HASHES ===",
    ]

    for name, item in report[
        "targets"
    ].items():
        if not item.get(
            "exists"
        ):
            lines.append(
                f"{name}: MISSING path={item['path']}"
            )
            continue

        lines.append(
            f"{name}: sha256={item['sha256']} bytes={item['bytes']} "
            f"lines={item['line_count']} path={item['path']}"
        )

    native = report[
        "targets"
    ][
        "native_stream_activity"
    ]

    lines += [
        "",
        "=== ANDROID NATIVE STREAM METRICS ===",
    ]
    lines.extend(
        fmt_tokens(
            native.get(
                "metric_tokens",
                {},
            )
        )
        or ["<none>"]
    )

    lines += [
        "",
        "=== ANDROID NETWORK PRIMITIVES ===",
    ]
    lines.extend(
        fmt_tokens(
            native.get(
                "network_tokens",
                {},
            )
        )
        or ["<none>"]
    )

    lines += [
        "",
        "=== ANDROID SCHEDULER / CADENCE PRIMITIVES ===",
    ]
    lines.extend(
        fmt_tokens(
            native.get(
                "scheduler_tokens",
                {},
            )
        )
        or ["<none>"]
    )

    lines += [
        "",
        "=== ANDROID JSON PRIMITIVES ===",
    ]
    lines.extend(
        fmt_tokens(
            native.get(
                "json_tokens",
                {},
            )
        )
        or ["<none>"]
    )

    lines += [
        "",
        "=== ANDROID LIFECYCLE METHODS ===",
    ]
    for name, present in native.get(
        "lifecycle",
        {}
    ).items():
        lines.append(
            f"{name}: {present}"
        )

    lines += [
        "",
        "=== SAFE ENDPOINT LITERALS IN NATIVE STREAM ACTIVITY ===",
    ]
    endpoints = native.get(
        "safe_endpoint_literals",
        []
    )
    lines.extend(
        endpoints
        or ["<none>"]
    )

    architecture = report[
        "architecture"
    ]

    lines += [
        "",
        "=== ARCHITECTURE CLASSIFICATION ===",
        "Disposition: "
        + architecture[
            "disposition"
        ],
        "Existing client metric surface: "
        + str(
            architecture[
                "existing_client_metric_surface"
            ]
        ),
        "Existing Android network primitives: "
        + str(
            architecture[
                "existing_android_network_primitives"
            ]
        ),
        "Existing Android scheduler primitives: "
        + str(
            architecture[
                "existing_android_scheduler_primitives"
            ]
        ),
        "Existing Android JSON primitives: "
        + str(
            architecture[
                "existing_android_json_primitives"
            ]
        ),
        "Existing diagnostics endpoint literal: "
        + str(
            architecture[
                "existing_diagnostics_endpoint_literal"
            ]
        ),
        "New feedback loop justified by this audit: False",
        "Recommendation: "
        + architecture[
            "recommendation"
        ],
        "Next step: "
        + architecture[
            "next_step"
        ],
        "",
        "Return this file before implementing Android client feedback.",
    ]

    return "\n".join(
        lines
    ) + "\n"


def self_test() -> int:
    fixture = """
class NativeStreamActivity {
    private var recentVideoFps = 0.0
    private var recentVideoMbps = 0.0
    private val handler = Handler(Looper.getMainLooper())
    fun onCreate() {}
    fun onDestroy() {}
    fun sendThing() {
        val payload = JSONObject()
        payload.put("recent_fps", recentVideoFps)
        val c = URL(base + "/plugins/games/status").openConnection()
            as HttpURLConnection
        handler.postDelayed({ sendThing() }, 1000)
    }
}
"""
    result = {
        "metric_tokens": token_inventory(
            fixture,
            METRIC_TOKENS,
        ),
        "scheduler_tokens": token_inventory(
            fixture,
            SCHEDULER_TOKENS,
        ),
        "network_tokens": token_inventory(
            fixture,
            NETWORK_TOKENS,
        ),
        "json_tokens": token_inventory(
            fixture,
            JSON_TOKENS,
        ),
    }

    assert result[
        "metric_tokens"
    ][
        "recentVideoFps"
    ][
        "count"
    ] == 2

    assert bool_any(
        result[
            "scheduler_tokens"
        ]
    )

    assert bool_any(
        result[
            "network_tokens"
        ]
    )

    assert endpoint_inventory(
        fixture
    ) == [
        "/plugins/games/status"
    ]

    assert lifecycle_inventory(
        method_inventory(
            fixture
        )
    )[
        "onDestroy"
    ]

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

    if not (
        root
        / ".git"
    ).exists():
        raise SystemExit(
            "PrivyHub repository root not found"
        )

    report = build_report(
        root
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
        / "b1_client_feedback_source_context.json"
    )
    text_path = (
        out_dir
        / "b1_client_feedback_source_context.txt"
    )

    json_path.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    text_path.write_text(
        format_text(
            report
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
