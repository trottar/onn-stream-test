#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

LOG_JSON_REL = Path(
    "logs/tv/d122_d5_tv_media_regression_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d122_d5_tv_media_regression_probe.txt"
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


def load_contracts(
    repo: Path,
):
    plugin_module = load_module(
        repo
        / "companion/plugins/tv_state.py",
        "d122_tv_state_plugin",
    )

    d116_module = load_module(
        repo
        / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d122_d116_probe",
    )

    return (
        plugin_module.TvStatePlugin,
        d116_module,
    )


def canonical_sha(
    plugin_class,
    state: dict[str, Any],
) -> str:
    normalized = (
        plugin_class.normalize_user_state(
            state
        )
    )

    raw = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(
        raw
    ).hexdigest()


def http_json(
    path: str,
) -> tuple[
    int,
    Any,
]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D122-Probe/1.0",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=20,
        ) as response:
            raw = response.read(
                MAX_RESPONSE_BYTES + 1
            )

            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError(
                    "Companion response exceeds probe cap"
                )

            return (
                int(response.status),
                json.loads(
                    raw.decode("utf-8")
                ),
            )

    except urllib.error.HTTPError as exc:
        raw = exc.read(
            MAX_RESPONSE_BYTES + 1
        )

        try:
            payload = json.loads(
                raw.decode("utf-8")
            )
        except Exception:
            payload = {
                "ok": False,
                "error": f"HTTP {exc.code}",
            }

        return (
            int(exc.code),
            payload,
        )


def source_count(
    payload: Any,
) -> int:
    if isinstance(
        payload,
        list,
    ):
        return len(
            payload
        )

    if isinstance(
        payload,
        dict,
    ):
        for key in (
            "sources",
            "items",
            "entries",
        ):
            value = payload.get(
                key
            )

            if isinstance(
                value,
                list,
            ):
                return len(
                    value
                )

        if payload:
            return 1

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

    repo = Path(
        args.repo
    ).resolve()

    plugin_class, d116_module = (
        load_contracts(
            repo
        )
    )

    if args.self_test:
        assert source_count(
            [
                {"id": "x"},
                {"id": "y"},
            ]
        ) == 2

        assert source_count(
            {
                "sources": [
                    {"id": "x"},
                ]
            }
        ) == 1

        print(
            "D122_PROBE_SELF_TEST_OK"
        )
        return 0

    status_http, status_payload = (
        http_json(
            "/status"
        )
    )

    sources_http, sources_payload = (
        http_json(
            "/sources"
        )
    )

    epg_http, epg_payload = (
        http_json(
            "/plugins/epg/status"
        )
    )

    tv_http, tv_payload = (
        http_json(
            "/plugins/tv_state/state"
        )
    )

    epg_ready = (
        epg_http == 200
        and isinstance(
            epg_payload,
            dict,
        )
        and bool(
            epg_payload.get(
                "ready"
            )
        )
    )

    sources = source_count(
        sources_payload
    )

    serial, adb_info = (
        d116_module.adb_serial()
    )

    local_state = None
    local_meta: dict[str, Any] = {
        "snapshot_ok": False,
    }
    prefs: dict[str, Any] = {}

    if serial:
        prefs = (
            d116_module.read_prefs(
                serial
            )
        )

        local_state, local_meta = (
            d116_module.local_projection(
                serial,
                plugin_class,
            )
        )

    remote_state = (
        tv_payload.get(
            "state"
        )
        if isinstance(
            tv_payload,
            dict,
        )
        else None
    )

    remote_hash = (
        canonical_sha(
            plugin_class,
            remote_state,
        )
        if isinstance(
            remote_state,
            dict,
        )
        else None
    )

    local_hash = (
        canonical_sha(
            plugin_class,
            local_state,
        )
        if isinstance(
            local_state,
            dict,
        )
        else None
    )

    linux_revision = (
        int(
            tv_payload.get(
                "server_revision"
            )
            or 0
        )
        if isinstance(
            tv_payload,
            dict,
        )
        else 0
    )

    onn_revision = int(
        prefs.get(
            "tv_state_server_revision",
            0,
        )
        or 0
    )

    conflict_at = int(
        prefs.get(
            "tv_state_last_conflict_at_ms",
            0,
        )
        or 0
    )

    conflict_base = int(
        prefs.get(
            "tv_state_last_conflict_base_revision",
            0,
        )
        or 0
    )

    conflict_server = int(
        prefs.get(
            "tv_state_last_conflict_server_revision",
            0,
        )
        or 0
    )

    last_success_action = str(
        prefs.get(
            "tv_state_last_success_action",
            "",
        )
        or ""
    )

    last_success_revision = int(
        prefs.get(
            "tv_state_last_success_revision",
            0,
        )
        or 0
    )

    tv_parity = (
        tv_http == 200
        and isinstance(
            tv_payload,
            dict,
        )
        and bool(
            tv_payload.get(
                "initialized"
            )
        )
        and bool(
            local_meta.get(
                "snapshot_ok"
            )
        )
        and remote_hash is not None
        and local_hash is not None
        and remote_hash
            == local_hash
        and linux_revision > 0
        and onn_revision
            == linux_revision
    )

    automated_ok = (
        status_http == 200
        and sources_http == 200
        and sources > 0
        and epg_ready
        and tv_parity
        and last_success_action
            == "pulled"
        and last_success_revision
            == linux_revision
        and conflict_at > 0
        and conflict_base > 0
        and conflict_server > conflict_base
    )

    if status_http != 200:
        classification = (
            "D122_COMPANION_STATUS_FAILED"
        )
    elif (
        sources_http != 200
        or sources <= 0
    ):
        classification = (
            "D122_SOURCE_CATALOG_FAILED"
        )
    elif not epg_ready:
        classification = (
            "D122_EPG_SERVICE_NOT_READY"
        )
    elif not serial:
        classification = (
            "D122_ADB_UNAVAILABLE"
        )
    elif not tv_parity:
        classification = (
            "D122_TV_STATE_PARITY_FAILED"
        )
    elif not automated_ok:
        classification = (
            "D122_SYNC_DIAGNOSTIC_BASELINE_FAILED"
        )
    else:
        classification = (
            "D122_D5_TV_MEDIA_AUTOMATED_REGRESSION_BASELINE_VALIDATED"
        )

    report = {
        "classification":
            classification,
        "companion": {
            "status_http":
                status_http,
            "sources_http":
                sources_http,
            "source_count":
                sources,
        },
        "epg": {
            "http":
                epg_http,
            "ready":
                epg_ready,
        },
        "tv_state": {
            "http":
                tv_http,
            "linux_revision":
                linux_revision,
            "onn_revision":
                onn_revision,
            "linux_sha256":
                remote_hash,
            "onn_sha256":
                local_hash,
            "parity":
                tv_parity,
        },
        "sync_diagnostics": {
            "last_success_action":
                last_success_action,
            "last_success_revision":
                last_success_revision,
            "last_conflict_at_ms":
                conflict_at,
            "last_conflict_base_revision":
                conflict_base,
            "last_conflict_server_revision":
                conflict_server,
        },
        "adb":
            adb_info,
        "snapshot":
            local_meta,
        "automated_ok":
            automated_ok,
    }

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
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub D-122 D5.4 TV/media regression automated baseline",
        f"Classification: {classification}",
        "",
        "COMPANION",
        f"  status_http: {status_http}",
        f"  sources_http: {sources_http}",
        f"  source_count: {sources}",
        "",
        "EPG",
        f"  http: {epg_http}",
        f"  ready: {epg_ready}",
        "",
        "TV STATE",
        f"  linux_revision: {linux_revision}",
        f"  onn_revision: {onn_revision}",
        f"  linux_sha256: {remote_hash}",
        f"  onn_sha256: {local_hash}",
        f"  parity: {tv_parity}",
        "",
        "SYNC DIAGNOSTICS",
        f"  last_success_action: {last_success_action}",
        f"  last_success_revision: {last_success_revision}",
        f"  last_conflict_at_ms: {conflict_at}",
        f"  last_conflict_base_revision: {conflict_base}",
        f"  last_conflict_server_revision: {conflict_server}",
        "",
        "CHECKS",
        f"  automated_ok: {automated_ok}",
        "",
        "This probe is read-only.",
        "It does not validate visible/audio playback; use the D-122 onn smoke test for that.",
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


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
