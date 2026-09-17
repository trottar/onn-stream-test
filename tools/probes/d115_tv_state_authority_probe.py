#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
STATE_REL = Path("data/tv_state/state.json")
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plugin(repo: Path):
    path = repo / "companion/plugins/tv_state.py"
    spec = importlib.util.spec_from_file_location(
        "d115_tv_state_plugin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Unable to load TV-state plugin"
        )
    module = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(module)
    return module.TvStatePlugin


def fixture_state(plugin_class) -> dict[str, Any]:
    return {
        "schema": plugin_class.USER_STATE_SCHEMA,
        "preferences": {
            "language_code": "eng",
            "language_name": "English",
            "country_code": "US",
            "country_name": "United States",
        },
        "managed_providers": [
            {
                "provider_id": "free_tv",
                "enabled": True,
            },
            {
                "provider_id": "freecasthub",
                "enabled": False,
            },
        ],
        "providers": [
            {
                "name": "D115 Fixture",
                "url": "https://example.invalid/d115.m3u",
                "language_code": "eng",
                "enabled": True,
            }
        ],
        "channels": [
            {
                "stream_id": "tv_stream_d115_fixture",
                "favorite": True,
                "manual_hidden": True,
                "custom_name": "Fixture Name",
                "custom_category": "news",
                "custom_url": "",
                "custom_referrer": "",
                "custom_user_agent": "",
                "favorite_group": "Fixture Group",
                "favorite_order": 7,
                "protect_auto_hide": True,
                "success_count": 999,
            }
        ],
        "runtime_observations": {
            "last_watched": 123,
        },
    }


def http_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "PrivyHub-D115-Probe/1.0",
    }

    if payload is not None:
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        CONTROL_BASE + path,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
            timeout=timeout,
        ) as response:
            raw = response.read(
                MAX_RESPONSE_BYTES + 1
            )
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError(
                    "Companion response exceeds probe cap"
                )
            decoded = json.loads(
                raw.decode("utf-8")
            )
            if not isinstance(decoded, dict):
                raise RuntimeError(
                    "Companion response is not an object"
                )
            return int(response.status), decoded
    except urllib.error.HTTPError as exc:
        raw = exc.read(
            MAX_RESPONSE_BYTES + 1
        )
        try:
            decoded = json.loads(
                raw.decode("utf-8")
            )
        except Exception:
            decoded = {
                "ok": False,
                "error": f"HTTP {exc.code}",
            }
        if not isinstance(decoded, dict):
            decoded = {
                "ok": False,
                "error": f"HTTP {exc.code}",
            }
        return int(exc.code), decoded


def direct_self_test(repo: Path) -> None:
    plugin_class = load_plugin(
        repo
    )

    with tempfile.TemporaryDirectory(
        prefix="d115_tv_state_selftest_"
    ) as td:
        plugin = plugin_class(
            project_root=repo,
            data_root=Path(td) / "tv_state",
        )

        initial = plugin.state()
        assert initial["initialized"] is False
        assert initial["server_revision"] == 0
        assert initial["state"] is None

        state = fixture_state(
            plugin_class
        )
        first = plugin.put_state(
            {
                "schema": plugin_class.UPDATE_SCHEMA,
                "base_revision": 0,
                "client_id": "d115-self-test",
                "state": state,
            }
        )
        assert first["ok"] is True
        assert first["changed"] is True
        assert first["server_revision"] == 1

        persisted = plugin.state()
        assert persisted["server_revision"] == 1
        channels = persisted["state"]["channels"]
        assert len(channels) == 1
        assert "success_count" not in channels[0]
        assert "runtime_observations" not in persisted["state"]

        same = plugin.put_state(
            {
                "schema": plugin_class.UPDATE_SCHEMA,
                "base_revision": 1,
                "client_id": "d115-self-test",
                "state": state,
            }
        )
        assert same["ok"] is True
        assert same["changed"] is False
        assert same["server_revision"] == 1

        conflict_state = json.loads(
            json.dumps(state)
        )
        conflict_state["channels"][0]["manual_hidden"] = False

        conflict = plugin.put_state(
            {
                "schema": plugin_class.UPDATE_SCHEMA,
                "base_revision": 0,
                "client_id": "d115-stale-client",
                "state": conflict_state,
            }
        )
        assert conflict["ok"] is False
        assert conflict["conflict"] is True
        assert conflict["server_revision"] == 1

        after_conflict = plugin.state()
        assert (
            after_conflict["state_sha256"]
            == persisted["state_sha256"]
        )


def self_test(repo: Path) -> int:
    direct_self_test(
        repo
    )
    print(
        "D115_PROBE_SELF_TEST_OK"
    )
    return 0


def run_probe(repo: Path) -> dict[str, Any]:
    plugin_class = load_plugin(
        repo
    )
    state_path = repo / STATE_REL
    original_directory_present = state_path.parent.exists()
    state_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_exists = state_path.is_file()
    original_bytes = (
        state_path.read_bytes()
        if original_exists
        else None
    )
    original_sha = (
        sha256_bytes(original_bytes)
        if original_bytes is not None
        else None
    )

    report: dict[str, Any] = {
        "generated_at_ms": int(
            time.time() * 1000
        ),
        "original_state_present": original_exists,
        "original_state_sha256": original_sha,
    }

    try:
        status_http, status = http_json(
            "GET",
            "/plugins/tv_state/status",
        )
        state_http, before = http_json(
            "GET",
            "/plugins/tv_state/state",
        )

        report["initial_status"] = {
            "http": status_http,
            "schema": status.get("schema"),
            "initialized": status.get("initialized"),
            "server_revision": status.get("server_revision"),
        }
        report["initial_state"] = {
            "http": state_http,
            "initialized": before.get("initialized"),
            "server_revision": before.get("server_revision"),
            "state_sha256": before.get("state_sha256"),
        }

        if status_http != 200 or state_http != 200:
            report["classification"] = (
                "D115_TV_STATE_ENDPOINT_UNAVAILABLE"
            )
            return report

        base_revision = int(
            before.get("server_revision") or 0
        )

        fixture = fixture_state(
            plugin_class
        )
        put_payload = {
            "schema": plugin_class.UPDATE_SCHEMA,
            "base_revision": base_revision,
            "client_id": "d115-runtime-probe",
            "state": fixture,
        }

        put_http, first = http_json(
            "POST",
            "/plugins/tv_state/state",
            put_payload,
        )
        report["first_put"] = {
            "http": put_http,
            "ok": first.get("ok"),
            "changed": first.get("changed"),
            "conflict": first.get("conflict"),
            "server_revision": first.get("server_revision"),
            "state_sha256": first.get("state_sha256"),
        }

        expected_revision = (
            base_revision + 1
        )
        if (
            put_http != 200
            or first.get("ok") is not True
            or first.get("changed") is not True
            or int(
                first.get("server_revision") or -1
            )
            != expected_revision
        ):
            report["classification"] = (
                "D115_TV_STATE_FIRST_WRITE_FAILED"
            )
            return report

        get_http, persisted = http_json(
            "GET",
            "/plugins/tv_state/state",
        )
        state = persisted.get("state")
        channels = (
            state.get("channels")
            if isinstance(state, dict)
            else None
        )

        runtime_fields_absent = bool(
            isinstance(channels, list)
            and len(channels) == 1
            and isinstance(channels[0], dict)
            and "success_count" not in channels[0]
            and isinstance(state, dict)
            and "runtime_observations" not in state
        )

        report["persisted_read"] = {
            "http": get_http,
            "initialized": persisted.get("initialized"),
            "server_revision": persisted.get("server_revision"),
            "state_sha256": persisted.get("state_sha256"),
            "runtime_fields_absent": runtime_fields_absent,
            "channel_count": (
                len(channels)
                if isinstance(channels, list)
                else None
            ),
        }

        if (
            get_http != 200
            or int(
                persisted.get("server_revision") or -1
            )
            != expected_revision
            or (
                persisted.get("state_sha256")
                != first.get("state_sha256")
            )
            or not runtime_fields_absent
        ):
            report["classification"] = (
                "D115_TV_STATE_PERSISTENCE_FAILED"
            )
            return report

        same_http, same = http_json(
            "POST",
            "/plugins/tv_state/state",
            {
                "schema": plugin_class.UPDATE_SCHEMA,
                "base_revision": expected_revision,
                "client_id": "d115-runtime-probe",
                "state": fixture,
            },
        )
        report["idempotent_put"] = {
            "http": same_http,
            "ok": same.get("ok"),
            "changed": same.get("changed"),
            "server_revision": same.get("server_revision"),
        }

        if (
            same_http != 200
            or same.get("ok") is not True
            or same.get("changed") is not False
            or int(
                same.get("server_revision") or -1
            )
            != expected_revision
        ):
            report["classification"] = (
                "D115_TV_STATE_IDEMPOTENCE_FAILED"
            )
            return report

        conflict_state = json.loads(
            json.dumps(fixture)
        )
        conflict_state["channels"][0]["manual_hidden"] = False

        conflict_http, conflict = http_json(
            "POST",
            "/plugins/tv_state/state",
            {
                "schema": plugin_class.UPDATE_SCHEMA,
                "base_revision": base_revision,
                "client_id": "d115-stale-runtime-probe",
                "state": conflict_state,
            },
        )
        report["conflict_put"] = {
            "http": conflict_http,
            "ok": conflict.get("ok"),
            "conflict": conflict.get("conflict"),
            "error_code": conflict.get("error_code"),
            "server_revision": conflict.get("server_revision"),
        }

        after_http, after = http_json(
            "GET",
            "/plugins/tv_state/state",
        )
        conflict_preserved_state = (
            after_http == 200
            and (
                after.get("state_sha256")
                == persisted.get("state_sha256")
            )
            and int(
                after.get("server_revision") or -1
            )
            == expected_revision
        )
        report["conflict_preserved_state"] = (
            conflict_preserved_state
        )

        if (
            conflict_http != 200
            or conflict.get("ok") is not False
            or conflict.get("conflict") is not True
            or (
                conflict.get("error_code")
                != "revision_conflict"
            )
            or not conflict_preserved_state
        ):
            report["classification"] = (
                "D115_TV_STATE_CONFLICT_GUARD_FAILED"
            )
            return report

        report["classification"] = (
            "D115_TV_STATE_AUTHORITY_RUNTIME_VALIDATED"
        )
        return report

    finally:
        if original_bytes is None:
            try:
                state_path.unlink()
            except FileNotFoundError:
                pass
        else:
            temp = state_path.with_suffix(
                ".d115-restore.tmp"
            )
            temp.write_bytes(
                original_bytes
            )
            os.replace(
                temp,
                state_path,
            )

        if (
            not original_directory_present
            and original_bytes is None
        ):
            try:
                state_path.parent.rmdir()
            except OSError:
                pass

        report["restored_original_state"] = (
            (
                not state_path.exists()
            )
            if original_bytes is None
            else (
                state_path.is_file()
                and sha256_bytes(
                    state_path.read_bytes()
                )
                == original_sha
            )
        )
        report["restored_original_directory"] = (
            state_path.parent.exists()
            == original_directory_present
        )


def render(report: dict[str, Any]) -> str:
    lines = [
        "PrivyHub D-115 D5.4 Linux TV-state authority runtime probe",
        f"Classification: {report.get('classification')}",
        "",
        "INITIAL AUTHORITY",
        f"  status_http: {report.get('initial_status', {}).get('http')}",
        f"  initialized: {report.get('initial_status', {}).get('initialized')}",
        f"  server_revision: {report.get('initial_status', {}).get('server_revision')}",
        "",
        "FIRST WRITE",
        f"  http: {report.get('first_put', {}).get('http')}",
        f"  ok: {report.get('first_put', {}).get('ok')}",
        f"  changed: {report.get('first_put', {}).get('changed')}",
        f"  server_revision: {report.get('first_put', {}).get('server_revision')}",
        "",
        "PERSISTED READ",
        f"  http: {report.get('persisted_read', {}).get('http')}",
        f"  server_revision: {report.get('persisted_read', {}).get('server_revision')}",
        f"  channel_count: {report.get('persisted_read', {}).get('channel_count')}",
        f"  runtime_fields_absent: {report.get('persisted_read', {}).get('runtime_fields_absent')}",
        "",
        "IDEMPOTENT WRITE",
        f"  http: {report.get('idempotent_put', {}).get('http')}",
        f"  changed: {report.get('idempotent_put', {}).get('changed')}",
        f"  server_revision: {report.get('idempotent_put', {}).get('server_revision')}",
        "",
        "STALE REVISION WRITE",
        f"  http: {report.get('conflict_put', {}).get('http')}",
        f"  ok: {report.get('conflict_put', {}).get('ok')}",
        f"  conflict: {report.get('conflict_put', {}).get('conflict')}",
        f"  error_code: {report.get('conflict_put', {}).get('error_code')}",
        f"  state_preserved: {report.get('conflict_preserved_state')}",
        "",
        "PROBE CLEANUP",
        f"  original_state_present: {report.get('original_state_present')}",
        f"  restored_original_state: {report.get('restored_original_state')}",
        f"  restored_original_directory: {report.get('restored_original_directory')}",
        "",
        "The probe does not retain its fixture TV state.",
        "No Android database is modified.",
        f"JSON: {report.get('json_path')}",
        f"TEXT: {report.get('text_path')}",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument(
        "--self-test",
        action="store_true",
    )
    args = ap.parse_args()

    repo = Path(
        args.repo
    ).resolve()

    if args.self_test:
        return self_test(
            repo
        )

    report = run_probe(
        repo
    )

    logs = repo / "logs/tv"
    logs.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        logs
        / "d115_tv_state_authority_probe.json"
    )
    text_path = (
        logs
        / "d115_tv_state_authority_probe.txt"
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
    text = render(
        report
    )
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
    raise SystemExit(main())
