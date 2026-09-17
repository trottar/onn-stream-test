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
    "logs/tv/d120_tv_state_sync_diagnostics_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d120_tv_state_sync_diagnostics_probe.txt"
)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load {path.name}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contracts(repo: Path):
    plugin_module = load_module(
        repo / "companion/plugins/tv_state.py",
        "d120_tv_state_plugin",
    )
    d116_module = load_module(
        repo / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d120_d116_probe",
    )
    return plugin_module.TvStatePlugin, d116_module


def canonical_sha(plugin_class, state: dict[str, Any]) -> str:
    normalized = plugin_class.normalize_user_state(state)
    raw = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def http_get(path: str) -> tuple[int, dict[str, Any]]:
    request = urllib.request.Request(
        CONTROL_BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D120-Probe/1.0",
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
            payload = json.loads(
                raw.decode("utf-8")
            )
            if not isinstance(payload, dict):
                raise RuntimeError(
                    "Companion response root is not an object"
                )
            return int(response.status), payload

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
        if not isinstance(payload, dict):
            payload = {
                "ok": False,
                "error": f"HTTP {exc.code}",
            }
        return int(exc.code), payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    plugin_class, d116_module = load_contracts(repo)

    if args.self_test:
        required = {
            "tv_state_server_revision",
            "tv_state_last_success_at_ms",
            "tv_state_last_success_action",
            "tv_state_last_success_revision",
            "tv_state_last_conflict_at_ms",
            "tv_state_last_conflict_base_revision",
            "tv_state_last_conflict_server_revision",
        }
        assert len(required) == 7
        print("D120_PROBE_SELF_TEST_OK")
        return 0

    http, remote = http_get(
        "/plugins/tv_state/state"
    )

    serial, adb_info = d116_module.adb_serial()
    prefs: dict[str, Any] = {}
    local_state = None
    local_meta: dict[str, Any] = {
        "snapshot_ok": False,
    }

    if serial:
        prefs = d116_module.read_prefs(serial)
        local_state, local_meta = (
            d116_module.local_projection(
                serial,
                plugin_class,
            )
        )

    remote_state = remote.get("state")

    remote_hash = (
        canonical_sha(
            plugin_class,
            remote_state,
        )
        if (
            http == 200
            and isinstance(
                remote_state,
                dict,
            )
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

    server_revision = int(
        remote.get(
            "server_revision"
        )
        or 0
    )

    stored_revision = int(
        prefs.get(
            "tv_state_server_revision",
            0,
        )
        or 0
    )

    success_at_ms = int(
        prefs.get(
            "tv_state_last_success_at_ms",
            0,
        )
        or 0
    )

    success_action = str(
        prefs.get(
            "tv_state_last_success_action",
            "",
        )
        or ""
    )

    success_revision = int(
        prefs.get(
            "tv_state_last_success_revision",
            0,
        )
        or 0
    )

    conflict_at_ms = int(
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

    parity = (
        remote_hash is not None
        and local_hash is not None
        and remote_hash == local_hash
        and server_revision > 0
        and stored_revision == server_revision
    )

    if http != 200:
        classification = (
            "D120_LINUX_TV_STATE_UNAVAILABLE"
        )
    elif not serial:
        classification = (
            "D120_ADB_UNAVAILABLE"
        )
    elif not local_meta.get(
        "snapshot_ok"
    ):
        classification = (
            "D120_ONN_TV_STATE_SNAPSHOT_FAILED"
        )
    elif not parity:
        classification = (
            "D120_TV_STATE_PARITY_FAILED"
        )
    elif success_at_ms <= 0:
        classification = (
            "D120_LAST_SYNC_TIMESTAMP_MISSING"
        )
    elif success_revision != server_revision:
        classification = (
            "D120_LAST_SYNC_REVISION_MISMATCH"
        )
    elif success_action != "pulled":
        classification = (
            "D120_LAST_SYNC_ACTION_UNEXPECTED"
        )
    else:
        classification = (
            "D120_TV_STATE_SYNC_DIAGNOSTICS_RUNTIME_VALIDATED"
        )

    report = {
        "classification": classification,
        "linux": {
            "http": http,
            "initialized": remote.get(
                "initialized"
            ),
            "server_revision": server_revision,
            "canonical_state_sha256":
                remote_hash,
        },
        "onn": {
            **adb_info,
            **local_meta,
            "stored_server_revision":
                stored_revision,
            "canonical_state_sha256":
                local_hash,
        },
        "diagnostics": {
            "last_success_at_ms":
                success_at_ms,
            "last_success_action":
                success_action,
            "last_success_revision":
                success_revision,
            "last_conflict_at_ms":
                conflict_at_ms,
            "last_conflict_base_revision":
                conflict_base,
            "last_conflict_server_revision":
                conflict_server,
        },
        "local_remote_parity": parity,
    }

    json_path = repo / LOG_JSON_REL
    text_path = repo / LOG_TEXT_REL

    json_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

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
        "PrivyHub D-120 D5.4 TV-state sync diagnostics probe",
        f"Classification: {classification}",
        "",
        "LINUX AUTHORITY",
        f"  http: {http}",
        f"  initialized: {remote.get('initialized')}",
        f"  server_revision: {server_revision}",
        f"  canonical_state_sha256: {remote_hash}",
        "",
        "ONN DURABLE PROJECTION",
        f"  adb_status: {adb_info.get('reason')}",
        f"  snapshot_ok: {local_meta.get('snapshot_ok')}",
        f"  stored_server_revision: {stored_revision}",
        f"  canonical_state_sha256: {local_hash}",
        "",
        "SYNC DIAGNOSTICS",
        f"  last_success_at_ms: {success_at_ms}",
        f"  last_success_action: {success_action}",
        f"  last_success_revision: {success_revision}",
        f"  last_conflict_at_ms: {conflict_at_ms}",
        f"  last_conflict_base_revision: {conflict_base}",
        f"  last_conflict_server_revision: {conflict_server}",
        "",
        "CHECKS",
        f"  local_remote_parity: {parity}",
        "",
        "No Android or Linux state was modified by this probe.",
        "No network address or device identifier is written to this report.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ]

    text = "\n".join(lines) + "\n"
    text_path.write_text(
        text,
        encoding="utf-8",
    )
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
