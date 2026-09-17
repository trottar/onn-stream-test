#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_BASE = "http://127.0.0.1:8765"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024

SESSION_REL = Path(
    "data/tv_state/.d121_conflict_diagnostics_session.json"
)
LOG_JSON_REL = Path(
    "logs/tv/d121_tv_state_conflict_diagnostics_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d121_tv_state_conflict_diagnostics_probe.txt"
)

MARKER_PREFIX = "D121 Conflict Validation"
CLIENT_ID = "d121-runtime-probe"

PREF_SERVER_REVISION = "tv_state_server_revision"
PREF_LAST_SUCCESS_AT_MS = "tv_state_last_success_at_ms"
PREF_LAST_SUCCESS_ACTION = "tv_state_last_success_action"
PREF_LAST_SUCCESS_REVISION = "tv_state_last_success_revision"
PREF_LAST_CONFLICT_AT_MS = "tv_state_last_conflict_at_ms"
PREF_LAST_CONFLICT_BASE_REVISION = (
    "tv_state_last_conflict_base_revision"
)
PREF_LAST_CONFLICT_SERVER_REVISION = (
    "tv_state_last_conflict_server_revision"
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

    module = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(
        module
    )
    return module


def load_contracts(repo: Path):
    plugin_module = load_module(
        repo / "companion/plugins/tv_state.py",
        "d121_tv_state_plugin",
    )
    d116_module = load_module(
        repo / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d121_d116_probe",
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
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = None

    headers = {
        "Accept": "application/json",
        "User-Agent": "PrivyHub-D121-Probe/1.0",
    }

    if payload is not None:
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        headers["Content-Type"] = (
            "application/json; charset=utf-8"
        )

    request = urllib.request.Request(
        CONTROL_BASE + path,
        data=body,
        headers=headers,
        method=method,
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

            decoded = json.loads(
                raw.decode("utf-8")
            )

            if not isinstance(
                decoded,
                dict,
            ):
                raise RuntimeError(
                    "Companion response root is not an object"
                )

            return (
                int(response.status),
                decoded,
            )

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

        if not isinstance(
            decoded,
            dict,
        ):
            decoded = {
                "ok": False,
                "error": f"HTTP {exc.code}",
            }

        return (
            int(exc.code),
            decoded,
        )


def put_state(
    plugin_class,
    *,
    base_revision: int,
    state: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    return http_json(
        "POST",
        "/plugins/tv_state/state",
        {
            "schema":
                plugin_class.UPDATE_SCHEMA,
            "base_revision":
                base_revision,
            "client_id":
                CLIENT_ID,
            "state":
                state,
        },
    )


def local_snapshot(
    repo: Path,
    plugin_class,
    d116_module,
) -> tuple[
    dict[str, Any] | None,
    dict[str, Any],
    dict[str, Any],
]:
    serial, adb_info = (
        d116_module.adb_serial()
    )

    if not serial:
        return (
            None,
            {
                **adb_info,
                "snapshot_ok": False,
            },
            {},
        )

    prefs = (
        d116_module.read_prefs(
            serial
        )
    )

    state, meta = (
        d116_module.local_projection(
            serial,
            plugin_class,
        )
    )

    return (
        state,
        {
            **adb_info,
            **meta,
        },
        prefs,
    )


def load_session(
    repo: Path,
) -> dict[str, Any] | None:
    path = repo / SESSION_REL

    if not path.is_file():
        return None

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "D-121 session root is invalid"
        )

    return payload


def write_session(
    repo: Path,
    payload: dict[str, Any],
) -> None:
    path = repo / SESSION_REL

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        ".tmp"
    )

    temp.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    os.chmod(
        temp,
        0o600,
    )

    os.replace(
        temp,
        path,
    )


def delete_session(
    repo: Path,
) -> None:
    try:
        (repo / SESSION_REL).unlink()
    except FileNotFoundError:
        pass


def state_country_name(
    state: dict[str, Any] | None,
) -> str:
    if not isinstance(
        state,
        dict,
    ):
        return ""

    preferences = state.get(
        "preferences"
    )

    if not isinstance(
        preferences,
        dict,
    ):
        return ""

    return str(
        preferences.get(
            "country_name",
            "",
        )
        or ""
    )


def marker_state(
    plugin_class,
    original_state: dict[str, Any],
    marker: str,
) -> dict[str, Any]:
    candidate = copy.deepcopy(
        original_state
    )

    preferences = candidate.get(
        "preferences"
    )

    if not isinstance(
        preferences,
        dict,
    ):
        raise RuntimeError(
            "TV state preferences are missing"
        )

    original_code = str(
        preferences.get(
            "country_code",
            "",
        )
        or ""
    )

    preferences[
        "country_name"
    ] = marker

    normalized = (
        plugin_class.normalize_user_state(
            candidate
        )
    )

    normalized_code = str(
        normalized[
            "preferences"
        ].get(
            "country_code",
            "",
        )
        or ""
    )

    if (
        normalized_code
        != original_code
    ):
        raise RuntimeError(
            "D-121 marker changed country code"
        )

    return normalized


def restore_linux(
    plugin_class,
    session: dict[str, Any],
) -> tuple[
    bool,
    int,
    str | None,
]:
    prepared_revision = int(
        session[
            "prepared_revision"
        ]
    )

    prepared_hash = str(
        session[
            "prepared_state_sha256"
        ]
    )

    http, current = http_json(
        "GET",
        "/plugins/tv_state/state",
    )

    current_state = current.get(
        "state"
    )

    current_hash = (
        canonical_sha(
            plugin_class,
            current_state,
        )
        if (
            http == 200
            and isinstance(
                current_state,
                dict,
            )
        )
        else None
    )

    current_revision = int(
        current.get(
            "server_revision"
        )
        or 0
    )

    if not (
        current_revision
            == prepared_revision
        and current_hash
            == prepared_hash
    ):
        return (
            False,
            current_revision,
            current_hash,
        )

    original_state = (
        plugin_class.normalize_user_state(
            session[
                "original_state"
            ]
        )
    )

    original_hash = str(
        session[
            "original_state_sha256"
        ]
    )

    put_http, restored = put_state(
        plugin_class,
        base_revision=
            prepared_revision,
        state=
            original_state,
    )

    restore_revision = int(
        restored.get(
            "server_revision"
        )
        or 0
    )

    restored_ok = (
        put_http == 200
        and restored.get(
            "ok"
        ) is True
        and restored.get(
            "conflict"
        ) is not True
        and restored.get(
            "changed"
        ) is True
        and restore_revision
            == prepared_revision + 1
        and str(
            restored.get(
                "state_sha256"
            )
            or ""
        )
            == original_hash
    )

    return (
        restored_ok,
        restore_revision,
        original_hash,
    )


def prepare(
    repo: Path,
    plugin_class,
    d116_module,
) -> dict[str, Any]:
    if (
        load_session(
            repo
        )
        is not None
    ):
        return {
            "phase": "prepare",
            "classification":
                "D121_SESSION_ALREADY_ACTIVE",
            "session_active": True,
            "next_action":
                "Continue the active D-121 session; do not prepare again.",
        }

    http, remote = http_json(
        "GET",
        "/plugins/tv_state/state",
    )

    remote_state = remote.get(
        "state"
    )

    if (
        http != 200
        or not remote.get(
            "initialized"
        )
        or not isinstance(
            remote_state,
            dict,
        )
    ):
        return {
            "phase": "prepare",
            "classification":
                "D121_LINUX_AUTHORITY_UNAVAILABLE",
            "session_active": False,
            "next_action":
                "Keep the companion running and inspect the TV-state endpoint.",
        }

    remote_state = (
        plugin_class.normalize_user_state(
            remote_state
        )
    )

    remote_revision = int(
        remote.get(
            "server_revision"
        )
        or 0
    )

    remote_hash = canonical_sha(
        plugin_class,
        remote_state,
    )

    (
        local_state,
        local_meta,
        prefs,
    ) = local_snapshot(
        repo,
        plugin_class,
        d116_module,
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

    local_revision = int(
        prefs.get(
            PREF_SERVER_REVISION,
            0,
        )
        or 0
    )

    if (
        not local_meta.get(
            "snapshot_ok"
        )
        or local_hash
            != remote_hash
        or local_revision
            != remote_revision
    ):
        return {
            "phase": "prepare",
            "classification":
                "D121_PRECONDITION_PARITY_FAILED",
            "linux_revision":
                remote_revision,
            "onn_revision":
                local_revision,
            "local_remote_parity":
                local_hash
                == remote_hash,
            "adb_status":
                local_meta.get(
                    "reason"
                ),
            "session_active": False,
            "next_action":
                "Restore ADB and Linux/onn parity before starting D-121.",
        }

    marker = (
        f"{MARKER_PREFIX} "
        f"r{remote_revision + 1}"
    )

    prepared_state = marker_state(
        plugin_class,
        remote_state,
        marker,
    )

    prepared_hash = canonical_sha(
        plugin_class,
        prepared_state,
    )

    put_http, result = put_state(
        plugin_class,
        base_revision=
            remote_revision,
        state=
            prepared_state,
    )

    prepared_revision = int(
        result.get(
            "server_revision"
        )
        or 0
    )

    if not (
        put_http == 200
        and result.get(
            "ok"
        ) is True
        and result.get(
            "changed"
        ) is True
        and result.get(
            "conflict"
        ) is not True
        and prepared_revision
            == remote_revision + 1
    ):
        return {
            "phase": "prepare",
            "classification":
                "D121_PREPARE_WRITE_FAILED",
            "linux_revision":
                remote_revision,
            "prepared_revision":
                prepared_revision,
            "session_active": False,
            "next_action":
                "Do not make the local TV mutation; inspect the Linux state write.",
        }

    session = {
        "schema":
            "privyhub_d121_conflict_diagnostics_session_v1",
        "created_at_ms":
            int(
                time.time()
                * 1000
            ),
        "initial_revision":
            remote_revision,
        "prepared_revision":
            prepared_revision,
        "restore_revision":
            None,
        "original_state":
            remote_state,
        "original_state_sha256":
            remote_hash,
        "prepared_state_sha256":
            prepared_hash,
        "original_country_name":
            state_country_name(
                remote_state
            ),
        "marker_country_name":
            marker,
        "pre_conflict_at_ms":
            int(
                prefs.get(
                    PREF_LAST_CONFLICT_AT_MS,
                    0,
                )
                or 0
            ),
        "pre_conflict_base_revision":
            int(
                prefs.get(
                    PREF_LAST_CONFLICT_BASE_REVISION,
                    0,
                )
                or 0
            ),
        "pre_conflict_server_revision":
            int(
                prefs.get(
                    PREF_LAST_CONFLICT_SERVER_REVISION,
                    0,
                )
                or 0
            ),
        "conflict_observed":
            None,
    }

    write_session(
        repo,
        session,
    )

    return {
        "phase": "prepare",
        "classification":
            "D121_STALE_WRITE_CONFLICT_TEST_PREPARED",
        "initial_revision":
            remote_revision,
        "prepared_revision":
            prepared_revision,
        "onn_revision":
            local_revision,
        "marker_country_name":
            marker,
        "session_active":
            True,
        "next_action":
            (
                "Keep the onn inside its current TV UI. Do not Back out to the "
                "top-level source list and do not press Refresh. Long-press one "
                "visible channel and toggle its Favorite state exactly once. "
                "Wait a few seconds, then run D-121 --phase verify."
            ),
    }


def verify(
    repo: Path,
    plugin_class,
    d116_module,
) -> dict[str, Any]:
    session = load_session(
        repo
    )

    if session is None:
        return {
            "phase": "verify",
            "classification":
                "D121_NO_ACTIVE_SESSION",
            "session_active": False,
            "next_action":
                "Run D-121 --phase prepare first.",
        }

    if (
        session.get(
            "restore_revision"
        )
        is not None
    ):
        return {
            "phase": "verify",
            "classification":
                "D121_LINUX_ALREADY_RESTORED",
            "restore_revision":
                session.get(
                    "restore_revision"
                ),
            "session_active":
                True,
            "next_action":
                "Press TV Refresh once and run D-121 --phase final.",
        }

    initial_revision = int(
        session[
            "initial_revision"
        ]
    )

    prepared_revision = int(
        session[
            "prepared_revision"
        ]
    )

    prepared_hash = str(
        session[
            "prepared_state_sha256"
        ]
    )

    # The production push is asynchronous. Poll only the local diagnostic
    # metadata for a short bounded window; never retry or create writes here.
    deadline = (
        time.monotonic()
        + 8.0
    )

    local_state = None
    local_meta: dict[str, Any] = {
        "snapshot_ok": False,
    }
    prefs: dict[str, Any] = {}

    while True:
        (
            local_state,
            local_meta,
            prefs,
        ) = local_snapshot(
            repo,
            plugin_class,
            d116_module,
        )

        conflict_at = int(
            prefs.get(
                PREF_LAST_CONFLICT_AT_MS,
                0,
            )
            or 0
        )

        if (
            local_meta.get(
                "snapshot_ok"
            )
            and conflict_at
                > int(
                    session[
                        "pre_conflict_at_ms"
                    ]
                )
        ):
            break

        if (
            time.monotonic()
            >= deadline
        ):
            break

        time.sleep(
            0.5
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

    local_revision = int(
        prefs.get(
            PREF_SERVER_REVISION,
            0,
        )
        or 0
    )

    conflict_at = int(
        prefs.get(
            PREF_LAST_CONFLICT_AT_MS,
            0,
        )
        or 0
    )

    conflict_base = int(
        prefs.get(
            PREF_LAST_CONFLICT_BASE_REVISION,
            0,
        )
        or 0
    )

    conflict_server = int(
        prefs.get(
            PREF_LAST_CONFLICT_SERVER_REVISION,
            0,
        )
        or 0
    )

    http, remote = http_json(
        "GET",
        "/plugins/tv_state/state",
    )

    remote_state = remote.get(
        "state"
    )

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

    remote_revision = int(
        remote.get(
            "server_revision"
        )
        or 0
    )

    linux_preserved = (
        remote_revision
            == prepared_revision
        and remote_hash
            == prepared_hash
    )

    conflict_observed = (
        bool(
            local_meta.get(
                "snapshot_ok"
            )
        )
        and conflict_at
            > int(
                session[
                    "pre_conflict_at_ms"
                ]
            )
        and conflict_base
            == initial_revision
        and conflict_server
            == prepared_revision
        and local_revision
            == initial_revision
        and linux_preserved
    )

    restored_ok, restore_revision, _ = (
        restore_linux(
            plugin_class,
            session,
        )
    )

    if not restored_ok:
        return {
            "phase": "verify",
            "classification":
                "D121_LINUX_CHANGED_DURING_TEST_NO_RESTORE",
            "initial_revision":
                initial_revision,
            "prepared_revision":
                prepared_revision,
            "linux_revision":
                remote_revision,
            "onn_revision":
                local_revision,
            "last_conflict_at_ms":
                conflict_at,
            "last_conflict_base_revision":
                conflict_base,
            "last_conflict_server_revision":
                conflict_server,
            "linux_prepared_state_preserved":
                linux_preserved,
            "session_active":
                True,
            "next_action":
                (
                    "Do not continue D-121. Linux no longer exactly matches the "
                    "prepared diagnostic state, so the probe refused to overwrite it."
                ),
        }

    session[
        "restore_revision"
    ] = restore_revision

    session[
        "conflict_observed"
    ] = bool(
        conflict_observed
    )

    session[
        "observed_conflict_at_ms"
    ] = conflict_at

    session[
        "observed_conflict_base_revision"
    ] = conflict_base

    session[
        "observed_conflict_server_revision"
    ] = conflict_server

    write_session(
        repo,
        session,
    )

    if not local_meta.get(
        "snapshot_ok"
    ):
        classification = (
            "D121_CONFLICT_SNAPSHOT_UNAVAILABLE_LINUX_RESTORED"
        )
    elif conflict_observed:
        classification = (
            "D121_STALE_WRITE_REJECTED_CONFLICT_DIAGNOSTICS_VALIDATED_RESTORE_PENDING"
        )
    else:
        classification = (
            "D121_CONFLICT_NOT_OBSERVED_LINUX_RESTORED"
        )

    return {
        "phase": "verify",
        "classification":
            classification,
        "initial_revision":
            initial_revision,
        "prepared_revision":
            prepared_revision,
        "restore_revision":
            restore_revision,
        "onn_revision":
            local_revision,
        "local_state_changed":
            local_hash
            != prepared_hash,
        "last_conflict_at_ms":
            conflict_at,
        "last_conflict_base_revision":
            conflict_base,
        "last_conflict_server_revision":
            conflict_server,
        "linux_prepared_state_preserved":
            linux_preserved,
        "conflict_observed":
            conflict_observed,
        "linux_original_content_restored":
            True,
        "session_active":
            True,
        "next_action":
            (
                "While still inside TV, press the normal Refresh button once. "
                "After loading completes, optionally open TV Settings -> "
                "Catalog / EPG Status and confirm Last state conflict shows "
                f"base {initial_revision}, server {prepared_revision}. "
                "Then run D-121 --phase final."
            ),
    }


def final(
    repo: Path,
    plugin_class,
    d116_module,
) -> dict[str, Any]:
    session = load_session(
        repo
    )

    if session is None:
        return {
            "phase": "final",
            "classification":
                "D121_NO_ACTIVE_SESSION",
            "session_active": False,
            "next_action":
                "There is no active D-121 session.",
        }

    restore_value = (
        session.get(
            "restore_revision"
        )
    )

    if restore_value is None:
        return {
            "phase": "final",
            "classification":
                "D121_RESTORE_NOT_PREPARED",
            "session_active":
                True,
            "next_action":
                "Run D-121 --phase verify first.",
        }

    restore_revision = int(
        restore_value
    )

    original_hash = str(
        session[
            "original_state_sha256"
        ]
    )

    http, remote = http_json(
        "GET",
        "/plugins/tv_state/state",
    )

    remote_state = remote.get(
        "state"
    )

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

    remote_revision = int(
        remote.get(
            "server_revision"
        )
        or 0
    )

    (
        local_state,
        local_meta,
        prefs,
    ) = local_snapshot(
        repo,
        plugin_class,
        d116_module,
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

    local_revision = int(
        prefs.get(
            PREF_SERVER_REVISION,
            0,
        )
        or 0
    )

    success_action = str(
        prefs.get(
            PREF_LAST_SUCCESS_ACTION,
            "",
        )
        or ""
    )

    success_revision = int(
        prefs.get(
            PREF_LAST_SUCCESS_REVISION,
            0,
        )
        or 0
    )

    conflict_at = int(
        prefs.get(
            PREF_LAST_CONFLICT_AT_MS,
            0,
        )
        or 0
    )

    conflict_base = int(
        prefs.get(
            PREF_LAST_CONFLICT_BASE_REVISION,
            0,
        )
        or 0
    )

    conflict_server = int(
        prefs.get(
            PREF_LAST_CONFLICT_SERVER_REVISION,
            0,
        )
        or 0
    )

    restored_parity = (
        bool(
            local_meta.get(
                "snapshot_ok"
            )
        )
        and remote_revision
            == restore_revision
        and local_revision
            == restore_revision
        and remote_hash
            == original_hash
        and local_hash
            == original_hash
    )

    conflict_retained = (
        session.get(
            "conflict_observed"
        )
        is True
        and conflict_at
            == int(
                session.get(
                    "observed_conflict_at_ms"
                )
                or 0
            )
        and conflict_base
            == int(
                session.get(
                    "observed_conflict_base_revision"
                )
                or 0
            )
        and conflict_server
            == int(
                session.get(
                    "observed_conflict_server_revision"
                )
                or 0
            )
    )

    pulled_restore = (
        success_action
            == "pulled"
        and success_revision
            == restore_revision
    )

    validated = (
        restored_parity
        and conflict_retained
        and pulled_restore
    )

    if restored_parity:
        delete_session(
            repo
        )

    if validated:
        classification = (
            "D121_CONFLICT_PROTECTION_AND_DIAGNOSTICS_RUNTIME_VALIDATED"
        )
    elif restored_parity:
        classification = (
            "D121_CLEANUP_PARITY_VALIDATED_CONFLICT_EVIDENCE_INCOMPLETE"
        )
    else:
        classification = (
            "D121_FINAL_RESTORE_PARITY_FAILED"
        )

    return {
        "phase": "final",
        "classification":
            classification,
        "initial_revision":
            session.get(
                "initial_revision"
            ),
        "prepared_revision":
            session.get(
                "prepared_revision"
            ),
        "restore_revision":
            restore_revision,
        "linux_revision":
            remote_revision,
        "onn_revision":
            local_revision,
        "local_remote_parity":
            restored_parity,
        "last_success_action":
            success_action,
        "last_success_revision":
            success_revision,
        "last_conflict_at_ms":
            conflict_at,
        "last_conflict_base_revision":
            conflict_base,
        "last_conflict_server_revision":
            conflict_server,
        "conflict_diagnostics_retained":
            conflict_retained,
        "linux_original_content_restored":
            remote_hash
            == original_hash,
        "onn_original_content_restored":
            local_hash
            == original_hash,
        "session_active":
            not restored_parity,
        "next_action":
            (
                "D-121 is complete."
                if restored_parity
                else (
                    "Keep ADB connected, press TV Refresh once, "
                    "and re-run D-121 --phase final."
                )
            ),
    }


def write_report(
    repo: Path,
    report: dict[str, Any],
) -> None:
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
        "PrivyHub D-121 D5.4 stale-write conflict diagnostics probe",
        f"Phase: {report.get('phase')}",
        f"Classification: {report.get('classification')}",
        "",
        "REVISIONS",
        f"  initial_revision: {report.get('initial_revision')}",
        f"  prepared_revision: {report.get('prepared_revision')}",
        f"  restore_revision: {report.get('restore_revision')}",
        f"  linux_revision: {report.get('linux_revision')}",
        f"  onn_revision: {report.get('onn_revision')}",
        "",
        "CONFLICT",
        f"  conflict_observed: {report.get('conflict_observed')}",
        f"  last_conflict_at_ms: {report.get('last_conflict_at_ms')}",
        f"  last_conflict_base_revision: {report.get('last_conflict_base_revision')}",
        f"  last_conflict_server_revision: {report.get('last_conflict_server_revision')}",
        f"  linux_prepared_state_preserved: {report.get('linux_prepared_state_preserved')}",
        f"  conflict_diagnostics_retained: {report.get('conflict_diagnostics_retained')}",
        "",
        "RECOVERY",
        f"  last_success_action: {report.get('last_success_action')}",
        f"  last_success_revision: {report.get('last_success_revision')}",
        f"  local_remote_parity: {report.get('local_remote_parity')}",
        f"  linux_original_content_restored: {report.get('linux_original_content_restored')}",
        f"  onn_original_content_restored: {report.get('onn_original_content_restored')}",
        f"  session_active: {report.get('session_active')}",
        "",
        f"Next action: {report.get('next_action')}",
        "",
        "D-121 never changes country_code.",
        "The local Favorite toggle is intentionally discarded by the final authoritative pull.",
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


def self_test(
    repo: Path,
) -> int:
    plugin_class, _ = (
        load_contracts(
            repo
        )
    )

    state = {
        "schema":
            plugin_class.USER_STATE_SCHEMA,
        "preferences": {
            "language_code":
                "eng",
            "language_name":
                "English",
            "country_code":
                "",
            "country_name":
                "All Countries",
        },
        "managed_providers": [],
        "providers": [],
        "channels": [],
    }

    normalized = (
        plugin_class.normalize_user_state(
            state
        )
    )

    marked = marker_state(
        plugin_class,
        normalized,
        "D121 Conflict Validation r7",
    )

    assert (
        normalized[
            "preferences"
        ][
            "country_code"
        ]
        ==
        marked[
            "preferences"
        ][
            "country_code"
        ]
    )

    assert (
        normalized[
            "preferences"
        ][
            "country_name"
        ]
        !=
        marked[
            "preferences"
        ][
            "country_name"
        ]
    )

    assert (
        canonical_sha(
            plugin_class,
            normalized,
        )
        !=
        canonical_sha(
            plugin_class,
            marked,
        )
    )

    print(
        "D121_PROBE_SELF_TEST_OK"
    )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo",
        default=".",
    )

    parser.add_argument(
        "--phase",
        choices=(
            "prepare",
            "verify",
            "final",
        ),
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
        return self_test(
            repo
        )

    if not args.phase:
        raise SystemExit(
            "--phase is required unless --self-test is used"
        )

    if args.phase == "prepare":
        report = prepare(
            repo,
            plugin_class,
            d116_module,
        )
    elif args.phase == "verify":
        report = verify(
            repo,
            plugin_class,
            d116_module,
        )
    else:
        report = final(
            repo,
            plugin_class,
            d116_module,
        )

    write_report(
        repo,
        report,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
