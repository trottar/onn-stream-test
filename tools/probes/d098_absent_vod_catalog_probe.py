#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

EXPECTED_HEAD = "7c029de7ff7d569bce07d26c23f0bcfbb1147e8d"
MARKER = "PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1"
OUT_REL = Path("logs/d098_absent_vod_catalog_probe.txt")


def run(
    cmd: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def request_json(
    url: str,
    *,
    method: str = "GET",
) -> tuple[int | None, dict[str, Any] | None, str]:
    req = urllib.request.Request(
        url,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=10,
        ) as response:
            raw = response.read()
            obj = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

            return (
                response.status,
                obj if isinstance(obj, dict) else None,
                "",
            )

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        obj = None

        try:
            parsed = json.loads(
                body
            )

            if isinstance(
                parsed,
                dict,
            ):
                obj = parsed
        except json.JSONDecodeError:
            pass

        return (
            exc.code,
            obj,
            body,
        )

    except Exception as exc:
        return (
            None,
            None,
            f"{type(exc).__name__}: {exc}",
        )


def flatten(
    value: Any,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    if isinstance(
        value,
        dict,
    ):
        if (
            value.get(
                "node_type"
            )
            == "source"
        ):
            out.append(
                value
            )

        children = value.get(
            "children"
        )

        if isinstance(
            children,
            list,
        ):
            for child in children:
                out.extend(
                    flatten(
                        child
                    )
                )

    elif isinstance(
        value,
        list,
    ):
        for child in value:
            out.extend(
                flatten(
                    child
                )
            )

    return out


def self_test() -> int:
    sample = {
        "root": [
            {
                "node_type": "source",
                "playback": {
                    "path": "/vod/a.mp4",
                },
            }
        ]
    }

    assert len(
        flatten(
            sample["root"]
        )
    ) == 1

    success = (
        "D098_ABSENT_VOD_CATALOG_RESILIENCE_CONFIRMED"
    )

    failure = (
        "D098_ABSENT_VOD_CATALOG_RESILIENCE_NOT_CONFIRMED"
    )

    assert (
        0
        if success
        == "D098_ABSENT_VOD_CATALOG_RESILIENCE_CONFIRMED"
        else 1
    ) == 0

    assert (
        0
        if failure
        == "D098_ABSENT_VOD_CATALOG_RESILIENCE_CONFIRMED"
        else 1
    ) == 1

    print(
        "SELF-TEST PASS"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--root",
        default="/home/privyhub/Projects/onn-stream-test",
    )

    ap.add_argument(
        "--source-id",
        default="",
        help=(
            "Optional stale Continue Watching/source id to POST. "
            "When storage is absent this must fail cleanly without "
            "making the control API unavailable."
        ),
    )

    ap.add_argument(
        "--self-test",
        action="store_true",
    )

    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(
        args.root
    ).resolve()

    out = (
        repo / OUT_REL
    )

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    head = run(
        [
            "git",
            "-C",
            str(
                repo
            ),
            "rev-parse",
            "HEAD",
        ]
    ).stdout.strip()

    source_text = (
        repo
        / "companion/privyhub_service.py"
    ).read_text(
        encoding="utf-8"
    )

    (
        status_http,
        status_obj,
        status_error,
    ) = request_json(
        "http://127.0.0.1:8765/status"
    )

    (
        sources_http,
        sources_obj,
        sources_error,
    ) = request_json(
        "http://127.0.0.1:8765/sources"
    )

    storage = (
        sources_obj.get(
            "storage",
            {},
        ).get(
            "vod",
            {},
        )
        if sources_obj
        else {}
    )

    sources = (
        flatten(
            sources_obj.get(
                "root",
                [],
            )
        )
        if sources_obj
        else []
    )

    vod_count = sum(
        1
        for item in sources
        if str(
            item.get(
                "playback",
                {},
            ).get(
                "path",
                "",
            )
        ).startswith(
            "/vod/"
        )
    )

    stale_http = None
    stale_error = "<not-run>"

    if args.source_id:
        (
            stale_http,
            _,
            stale_error,
        ) = request_json(
            "http://127.0.0.1:8765"
            + "/sources/"
            + args.source_id
            + "/start",
            method="POST",
        )

    (
        status_after_http,
        _,
        status_after_error,
    ) = request_json(
        "http://127.0.0.1:8765/status"
    )

    (
        sources_after_http,
        _,
        sources_after_error,
    ) = request_json(
        "http://127.0.0.1:8765/sources"
    )

    lines = [
        "PrivyHub D-098 absent-VOD catalog resilience probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Expected checkpoint: {EXPECTED_HEAD}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CHECKPOINT ===",
        f"Git HEAD: {head}",
        f"Git HEAD expected: {head == EXPECTED_HEAD}",
        f"D-098 source marker present: {MARKER in source_text}",
        "",
        "=== INITIAL CONTROL API ===",
        f"GET /status HTTP: {status_http}",
        f"GET /status error: {status_error or '<none>'}",
        f"GET /sources HTTP: {sources_http}",
        f"GET /sources error: {sources_error or '<none>'}",
        "",
        "=== VOD STORAGE ===",
        f"Storage configured: {storage.get('configured')}",
        f"Storage available: {storage.get('available')}",
        f"Dynamic VOD source count: {vod_count}",
        "",
        "=== OPTIONAL STALE SOURCE START ===",
        f"Source id supplied: {bool(args.source_id)}",
        f"POST source start HTTP: {stale_http}",
        f"POST source start response/error: {stale_error or '<none>'}",
        "",
        "=== CONTROL API AFTER SOURCE ATTEMPT ===",
        f"GET /status HTTP: {status_after_http}",
        f"GET /status error: {status_after_error or '<none>'}",
        f"GET /sources HTTP: {sources_after_http}",
        f"GET /sources error: {sources_after_error or '<none>'}",
    ]

    stale_clean = (
        True
        if not args.source_id
        else (
            stale_http in {
                404,
                503,
            }
        )
    )

    confirmed = (
        head == EXPECTED_HEAD
        and MARKER in source_text
        and status_http == 200
        and sources_http == 200
        and stale_clean
        and status_after_http == 200
        and sources_after_http == 200
    )

    classification = (
        "D098_ABSENT_VOD_CATALOG_RESILIENCE_CONFIRMED"
        if confirmed
        else "D098_ABSENT_VOD_CATALOG_RESILIENCE_NOT_CONFIRMED"
    )

    lines += [
        "",
        "=== RESULT ===",
        f"Classification: {classification}",
        "",
        "Interpretation:",
        "- Disk absent: /status and /sources must remain HTTP 200.",
        "- Disk absent: dynamic VOD may be empty and storage unavailable.",
        "- Stale Continue Watching/source start may return 404/503.",
        "- After that failed start, /status and /sources must still be HTTP 200.",
        "- Disk present: normal dynamic VOD count and playback should recover.",
    ]

    out.write_text(
        "\n".join(
            lines
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        classification
    )

    print(
        "Log:",
        out,
    )

    return (
        0
        if classification
        == "D098_ABSENT_VOD_CATALOG_RESILIENCE_CONFIRMED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
