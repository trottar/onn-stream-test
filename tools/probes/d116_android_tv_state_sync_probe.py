#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any


APP_ID = "com.safeiot.privyhub"
CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def load_plugin(repo: Path):
    path = repo / "companion/plugins/tv_state.py"
    spec = importlib.util.spec_from_file_location(
        "d116_tv_state_plugin",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load TV-state plugin")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TvStatePlugin


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
    req = urllib.request.Request(
        CONTROL_BASE + path,
        headers={
            "Accept": "application/json",
            "User-Agent": "PrivyHub-D116-Probe/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise RuntimeError("response exceeds probe cap")
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError("response root is not an object")
            return int(response.status), payload
    except urllib.error.HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES + 1)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            payload = {"ok": False, "error": f"HTTP {exc.code}"}
        return int(exc.code), payload


def adb_serial() -> tuple[str | None, dict[str, Any]]:
    adb = shutil.which("adb")
    if not adb:
        return None, {"reason": "adb_not_found"}

    proc = subprocess.run(
        [adb, "devices"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    serials: list[str] = []
    if proc.returncode == 0:
        for line in proc.stdout.splitlines()[1:]:
            if "\t" not in line:
                continue
            serial, state = line.split("\t", 1)
            if state.strip() == "device":
                serials.append(serial.strip())

    return (
        serials[0] if len(serials) == 1 else None,
        {
            "reason": (
                "ready"
                if len(serials) == 1
                else "need_exactly_one_authorized_device"
            ),
            "authorized_device_count": len(serials),
        },
    )


def adb_cat(serial: str, rel: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None
    proc = subprocess.run(
        [
            adb,
            "-s",
            serial,
            "exec-out",
            "run-as",
            APP_ID,
            "cat",
            rel,
        ],
        capture_output=True,
        timeout=20,
    )
    return proc.stdout if proc.returncode == 0 else None


def read_prefs(serial: str) -> dict[str, Any]:
    raw = adb_cat(
        serial,
        "shared_prefs/privyhub_settings.xml",
    )
    if not raw:
        return {}
    root = ET.fromstring(raw.decode("utf-8"))
    result: dict[str, Any] = {}
    for child in root:
        name = child.attrib.get("name")
        if not name:
            continue
        if child.tag == "string":
            result[name] = child.text or ""
        elif child.tag == "long":
            result[name] = int(child.attrib.get("value", "0"))
        elif child.tag == "boolean":
            result[name] = child.attrib.get("value", "false") == "true"
    return result


def snapshot_db(serial: str, db_name: str, temp: Path) -> Path | None:
    main = adb_cat(serial, f"databases/{db_name}")
    if not main or not main.startswith(b"SQLite format 3\x00"):
        return None
    path = temp / db_name
    path.write_bytes(main)

    wal = adb_cat(serial, f"databases/{db_name}-wal")
    if wal:
        (temp / f"{db_name}-wal").write_bytes(wal)

    shm = adb_cat(serial, f"databases/{db_name}-shm")
    if shm:
        (temp / f"{db_name}-shm").write_bytes(shm)

    return path


def local_projection(serial: str, plugin_class) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    prefs = read_prefs(serial)

    with tempfile.TemporaryDirectory(prefix="d116_tvdb_") as td:
        db_path = snapshot_db(
            serial,
            "privyhub_tv.db",
            Path(td),
        )
        if db_path is None:
            return None, {
                "snapshot_ok": False,
                "reason": "tv_db_unavailable",
            }

        conn = sqlite3.connect(
            f"file:{db_path}?mode=ro",
            uri=True,
        )
        conn.row_factory = sqlite3.Row
        try:
            provider_rows = conn.execute(
                """
                SELECT provider_id, name, url, enabled, language_code, builtin
                FROM providers
                ORDER BY builtin DESC, name COLLATE NOCASE
                """
            ).fetchall()

            channel_rows = conn.execute(
                """
                SELECT stream_id, favorite, manual_hidden,
                       custom_name, custom_category, custom_url,
                       custom_referrer, custom_user_agent,
                       favorite_group, favorite_order, protect_auto_hide,
                       guide_incorrect, rejected_guide_source_key,
                       guide_incorrect_at_ms,
                       name, channel_id
                FROM streams
                WHERE favorite = 1 OR manual_hidden = 1 OR
                      custom_name IS NOT NULL OR custom_category IS NOT NULL OR
                      custom_url IS NOT NULL OR custom_referrer IS NOT NULL OR
                      custom_user_agent IS NOT NULL OR favorite_group <> '' OR
                      favorite_order > 0 OR protect_auto_hide = 1 OR
                      guide_incorrect = 1
                ORDER BY stream_id
                """
            ).fetchall()

            target = conn.execute(
                """
                SELECT stream_id, name, channel_id, manual_hidden
                FROM streams
                WHERE name LIKE '10 Bold Adelaide%'
                ORDER BY stream_id
                LIMIT 1
                """
            ).fetchone()
        finally:
            conn.close()

    managed = []
    providers = []
    for row in provider_rows:
        provider_id = str(row["provider_id"] or "")
        builtin = int(row["builtin"] or 0) != 0
        if builtin and provider_id != "iptv_org":
            managed.append(
                {
                    "provider_id": provider_id,
                    "enabled": int(row["enabled"] or 0) != 0,
                }
            )
        elif not builtin:
            providers.append(
                {
                    "name": str(row["name"] or ""),
                    "url": str(row["url"] or ""),
                    "language_code": str(row["language_code"] or "eng"),
                    "enabled": int(row["enabled"] or 0) != 0,
                }
            )

    channels = []
    for row in channel_rows:
        channels.append(
            {
                "stream_id": str(row["stream_id"] or ""),
                "favorite": int(row["favorite"] or 0) != 0,
                "manual_hidden": int(row["manual_hidden"] or 0) != 0,
                "custom_name": str(row["custom_name"] or ""),
                "custom_category": str(row["custom_category"] or ""),
                "custom_url": str(row["custom_url"] or ""),
                "custom_referrer": str(row["custom_referrer"] or ""),
                "custom_user_agent": str(row["custom_user_agent"] or ""),
                "favorite_group": str(row["favorite_group"] or ""),
                "favorite_order": int(row["favorite_order"] or 0),
                "protect_auto_hide": int(row["protect_auto_hide"] or 0) != 0,
                "guide_incorrect": int(row["guide_incorrect"] or 0) != 0,
                "rejected_guide_source_key": str(
                    row["rejected_guide_source_key"] or ""
                ),
                "guide_incorrect_at_ms": int(
                    row["guide_incorrect_at_ms"] or 0
                ),
            }
        )

    state = {
        "schema": plugin_class.USER_STATE_SCHEMA,
        "preferences": {
            "language_code": str(prefs.get("tv_language", "eng") or "eng"),
            "language_name": str(prefs.get("tv_language_name", "English") or "English"),
            "country_code": str(prefs.get("tv_country", "") or ""),
            "country_name": str(prefs.get("tv_country_name", "All Countries") or "All Countries"),
        },
        "managed_providers": managed,
        "providers": providers,
        "channels": channels,
    }

    target_info = None
    if target is not None:
        target_info = {
            "stream_id": str(target["stream_id"] or ""),
            "name": str(target["name"] or ""),
            "channel_id": str(target["channel_id"] or ""),
            "manual_hidden": int(target["manual_hidden"] or 0) != 0,
        }

    return plugin_class.normalize_user_state(state), {
        "snapshot_ok": True,
        "server_revision_pref": int(
            prefs.get("tv_state_server_revision", 0) or 0
        ),
        "client_id_present": bool(
            str(prefs.get("tv_state_client_id", "") or "").strip()
        ),
        "channel_count": len(channels),
        "favorite_count": sum(1 for row in channels if row["favorite"]),
        "manual_hidden_count": sum(1 for row in channels if row["manual_hidden"]),
        "target_10bold": target_info,
    }


def self_test(repo: Path) -> int:
    plugin_class = load_plugin(repo)
    state = {
        "schema": plugin_class.USER_STATE_SCHEMA,
        "preferences": {
            "language_code": "eng",
            "language_name": "English",
            "country_code": "",
            "country_name": "All Countries",
        },
        "managed_providers": [],
        "providers": [],
        "channels": [
            {
                "stream_id": "tv_stream_fixture",
                "favorite": False,
                "manual_hidden": True,
                "custom_name": "",
                "custom_category": "",
                "custom_url": "",
                "custom_referrer": "",
                "custom_user_agent": "",
                "favorite_group": "",
                "favorite_order": 0,
                "protect_auto_hide": False,
                "success_count": 99,
            }
        ],
    }
    normalized = plugin_class.normalize_user_state(state)
    assert "success_count" not in normalized["channels"][0]
    assert canonical_sha(plugin_class, normalized) == canonical_sha(plugin_class, state)

    guide_state = {
        "schema": plugin_class.USER_STATE_SCHEMA,
        "preferences": {
            "language_code": "eng",
            "language_name": "English",
            "country_code": "",
            "country_name": "All Countries",
        },
        "managed_providers": [],
        "providers": [],
        "channels": [
            {
                "stream_id": "tv_stream_guide_fixture",
                "favorite": False,
                "manual_hidden": False,
                "custom_name": "",
                "custom_category": "",
                "custom_url": "",
                "custom_referrer": "",
                "custom_user_agent": "",
                "favorite_group": "",
                "favorite_order": 0,
                "protect_auto_hide": False,
                "guide_incorrect": True,
                "rejected_guide_source_key": "fixture-guide-source",
                "guide_incorrect_at_ms": 123456789,
            }
        ],
    }
    normalized_guide = plugin_class.normalize_user_state(guide_state)
    assert normalized_guide["channels"][0]["guide_incorrect"] is True
    assert (
        normalized_guide["channels"][0]["rejected_guide_source_key"]
        == "fixture-guide-source"
    )
    assert normalized_guide["channels"][0]["guide_incorrect_at_ms"] == 123456789
    print("D116_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()

    if args.self_test:
        return self_test(repo)

    plugin_class = load_plugin(repo)

    http, envelope = http_get(
        "/plugins/tv_state/state"
    )

    serial, adb_info = adb_serial()
    local_state = None
    local_meta: dict[str, Any] = {
        "snapshot_ok": False,
    }
    if serial:
        local_state, local_meta = local_projection(
            serial,
            plugin_class,
        )

    remote_state = envelope.get("state")
    remote_hash = None
    local_hash = None
    if isinstance(remote_state, dict):
        remote_hash = canonical_sha(
            plugin_class,
            remote_state,
        )
    if isinstance(local_state, dict):
        local_hash = canonical_sha(
            plugin_class,
            local_state,
        )

    parity = (
        remote_hash is not None
        and local_hash is not None
        and remote_hash == local_hash
    )

    target = local_meta.get("target_10bold")
    target_stream_id = (
        target.get("stream_id")
        if isinstance(target, dict)
        else None
    )
    target_local_hidden = bool(
        isinstance(target, dict)
        and target.get("manual_hidden")
    )

    target_remote_hidden = None
    if (
        isinstance(remote_state, dict)
        and isinstance(remote_state.get("channels"), list)
        and target_stream_id
    ):
        for item in remote_state["channels"]:
            if (
                isinstance(item, dict)
                and item.get("stream_id") == target_stream_id
            ):
                target_remote_hidden = bool(
                    item.get("manual_hidden")
                )
                break
        if target_remote_hidden is None:
            target_remote_hidden = False

    server_revision = int(
        envelope.get("server_revision") or 0
    )

    push_observed = (
        server_revision >= 2
        and local_meta.get("server_revision_pref") == server_revision
    )

    if http != 200 or not envelope.get("initialized"):
        classification = "D116_LINUX_TV_STATE_NOT_INITIALIZED"
    elif not local_meta.get("snapshot_ok"):
        classification = "D116_ONN_TV_STATE_SNAPSHOT_FAILED"
    elif not parity:
        classification = "D116_TV_STATE_PARITY_FAILED"
    elif (
        target_stream_id
        and target_local_hidden
        and target_remote_hidden is not True
    ):
        classification = "D116_MANUAL_HIDDEN_PUSH_FAILED"
    elif push_observed:
        classification = "D116_ANDROID_TV_STATE_SYNC_RUNTIME_VALIDATED"
    else:
        classification = "D116_TV_STATE_SEED_PARITY_VALIDATED_NO_MUTATION_PUSH"

    report = {
        "classification": classification,
        "linux": {
            "http": http,
            "initialized": envelope.get("initialized"),
            "server_revision": server_revision,
            "state_sha256": envelope.get("state_sha256"),
            "canonical_state_sha256": remote_hash,
        },
        "onn": {
            **adb_info,
            **local_meta,
            "canonical_state_sha256": local_hash,
        },
        "parity": parity,
        "push_observed": push_observed,
        "target_10bold": {
            "stream_id_present": bool(target_stream_id),
            "local_manual_hidden": target_local_hidden,
            "remote_manual_hidden": target_remote_hidden,
        },
    }

    logs = repo / "logs/tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d116_android_tv_state_sync_probe.json"
    text_path = logs / "d116_android_tv_state_sync_probe.txt"

    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub D-116 D5.4 Android TV-state sync runtime probe",
        f"Classification: {classification}",
        "",
        "LINUX AUTHORITY",
        f"  http: {http}",
        f"  initialized: {envelope.get('initialized')}",
        f"  server_revision: {server_revision}",
        f"  canonical_state_sha256: {remote_hash}",
        "",
        "ONN DURABLE PROJECTION",
        f"  adb_status: {adb_info.get('reason')}",
        f"  snapshot_ok: {local_meta.get('snapshot_ok')}",
        f"  stored_server_revision: {local_meta.get('server_revision_pref')}",
        f"  client_id_present: {local_meta.get('client_id_present')}",
        f"  durable_channel_rows: {local_meta.get('channel_count')}",
        f"  favorites: {local_meta.get('favorite_count')}",
        f"  manual_hidden: {local_meta.get('manual_hidden_count')}",
        f"  canonical_state_sha256: {local_hash}",
        "",
        "SYNC CHECKS",
        f"  local_remote_parity: {parity}",
        f"  post_seed_push_observed: {push_observed}",
        "",
        "10 BOLD CHECK",
        f"  stream_present: {bool(target_stream_id)}",
        f"  local_manual_hidden: {target_local_hidden}",
        f"  remote_manual_hidden: {target_remote_hidden}",
        "",
        "No Android or Linux state was modified by this probe.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ]
    text = "\n".join(lines) + "\n"
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
