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
    "data/tv_state/.d119_tv_entry_sync_session.json"
)
LOG_JSON_REL = Path(
    "logs/tv/d119_tv_entry_sync_trigger_probe.json"
)
LOG_TEXT_REL = Path(
    "logs/tv/d119_tv_entry_sync_trigger_probe.txt"
)

MARKER_PREFIX = "D119 TV Entry Validation"
CLIENT_ID = "d119-runtime-probe"


def load_module(
    path: Path,
    module_name: str,
):
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


def load_contracts(
    repo: Path,
):
    plugin_module = load_module(
        repo / "companion/plugins/tv_state.py",
        "d119_tv_state_plugin",
    )
    d116_module = load_module(
        repo / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d119_d116_probe",
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
        "User-Agent": "PrivyHub-D119-Probe/1.0",
    }

    if payload is not None:
        body = json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")

        headers["Content-Type"] = (
            "application/json; charset=utf-8"
        )

    req = urllib.request.Request(
        CONTROL_BASE + path,
        data=body,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            req,
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
                    "Companion response is not an object"
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


def local_snapshot(
    repo: Path,
    plugin_class,
    d116_module,
) -> tuple[
    dict[str, Any] | None,
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
            "D-119 session root is invalid"
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
        (
            repo
            / SESSION_REL
        ).unlink()
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
            "D-119 marker changed country code"
        )

    return normalized


def put_state(
    plugin_class,
    *,
    base_revision: int,
    state: dict[str, Any],
) -> tuple[
    int,
    dict[str, Any],
]:
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
                "D119_SESSION_ALREADY_ACTIVE",
            "session_active": True,
            "next_action":
                "Continue the active D-119 session; do not prepare again.",
        }

    http, envelope = http_json(
        "GET",
        "/plugins/tv_state/state",
    )

    remote_state = envelope.get(
        "state"
    )

    if (
        http != 200
        or not envelope.get(
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
                "D119_LINUX_AUTHORITY_UNAVAILABLE",
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
        envelope.get(
            "server_revision"
        )
        or 0
    )

    remote_hash = canonical_sha(
        plugin_class,
        remote_state,
    )

    local_state, local_meta = (
        local_snapshot(
            repo,
            plugin_class,
            d116_module,
        )
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
        local_meta.get(
            "server_revision_pref"
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
                "D119_PRECONDITION_PARITY_FAILED",
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
                "Restore ADB and D-116 parity before starting D-119.",
        }

    original_country = (
        state_country_name(
            remote_state
        )
    )

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
                "D119_PREPARE_WRITE_FAILED",
            "linux_revision":
                remote_revision,
            "prepared_revision":
                prepared_revision,
            "session_active": False,
            "next_action":
                "Do not enter TV for D-119; inspect the Linux state write.",
        }

    session = {
        "schema":
            "privyhub_d119_tv_entry_sync_session_v1",
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
            original_country,
        "marker_country_name":
            marker,
        "top_level_entry_observed":
            None,
    }

    write_session(
        repo,
        session,
    )

    return {
        "phase": "prepare",
        "classification":
            "D119_TOP_LEVEL_TV_ENTRY_TEST_PREPARED",
        "initial_revision":
            remote_revision,
        "prepared_revision":
            prepared_revision,
        "original_country_name":
            original_country,
        "marker_country_name":
            marker,
        "onn_revision":
            local_revision,
        "local_remote_parity":
            True,
        "session_active":
            True,
        "next_action":
            (
                "On the onn, press Back until the top-level PrivyHub source list "
                "is visible, then select TV exactly once. Do not press Refresh. "
                "After the TV home finishes loading, run D-119 --phase verify."
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
                "D119_NO_ACTIVE_SESSION",
            "session_active":
                False,
            "next_action":
                "Run D-119 --phase prepare first.",
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
                "D119_LINUX_ALREADY_RESTORED",
            "restore_revision":
                session.get(
                    "restore_revision"
                ),
            "session_active":
                True,
            "next_action":
                "Use TV Refresh once and run D-119 --phase final.",
        }

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

    local_state, local_meta = (
        local_snapshot(
            repo,
            plugin_class,
            d116_module,
        )
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
        local_meta.get(
            "server_revision_pref"
        )
        or 0
    )

    local_country = (
        state_country_name(
            local_state
        )
    )

    snapshot_ok = bool(
        local_meta.get(
            "snapshot_ok"
        )
    )

    trigger_observed = (
        snapshot_ok
        and local_revision
            == prepared_revision
        and local_hash
            == prepared_hash
        and local_country
            == session[
                "marker_country_name"
            ]
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
                "D119_LINUX_CHANGED_DURING_TEST_NO_RESTORE",
            "prepared_revision":
                prepared_revision,
            "onn_revision":
                local_revision,
            "adb_status":
                local_meta.get(
                    "reason"
                ),
            "top_level_entry_observed":
                trigger_observed,
            "session_active":
                True,
            "next_action":
                (
                    "Do not continue D-119. Linux no longer matches the "
                    "prepared diagnostic state, so the probe refused to overwrite it."
                ),
        }

    session[
        "restore_revision"
    ] = restore_revision

    session[
        "top_level_entry_observed"
    ] = bool(
        trigger_observed
    )

    write_session(
        repo,
        session,
    )

    if not snapshot_ok:
        classification = (
            "D119_TOP_LEVEL_TV_ENTRY_SNAPSHOT_UNAVAILABLE_LINUX_RESTORED"
        )
    elif trigger_observed:
        classification = (
            "D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_VALIDATED_RESTORE_PENDING"
        )
    else:
        classification = (
            "D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_NOT_OBSERVED_LINUX_RESTORED"
        )

    return {
        "phase": "verify",
        "classification":
            classification,
        "initial_revision":
            session.get(
                "initial_revision"
            ),
        "prepared_revision":
            prepared_revision,
        "restore_revision":
            restore_revision,
        "marker_country_name":
            session.get(
                "marker_country_name"
            ),
        "onn_country_name":
            local_country,
        "onn_revision":
            local_revision,
        "adb_status":
            local_meta.get(
                "reason"
            ),
        "top_level_entry_observed":
            trigger_observed,
        "linux_original_content_restored":
            True,
        "session_active":
            True,
        "next_action":
            (
                "While still inside TV, press the normal Refresh button once. "
                "After loading completes, run D-119 --phase final."
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
                "D119_NO_ACTIVE_SESSION",
            "session_active":
                False,
            "next_action":
                "There is no active D-119 session.",
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
                "D119_RESTORE_NOT_PREPARED",
            "session_active":
                True,
            "next_action":
                "Run D-119 --phase verify first.",
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

    local_state, local_meta = (
        local_snapshot(
            repo,
            plugin_class,
            d116_module,
        )
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
        local_meta.get(
            "server_revision_pref"
        )
        or 0
    )

    local_country = (
        state_country_name(
            local_state
        )
    )

    restored = (
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
        and local_country
            == session[
                "original_country_name"
            ]
    )

    observed = (
        session.get(
            "top_level_entry_observed"
        )
        is True
    )

    if restored:
        delete_session(
            repo
        )

    if not restored:
        classification = (
            "D119_FINAL_RESTORE_PARITY_FAILED"
        )
    elif observed:
        classification = (
            "D119_TOP_LEVEL_TV_ENTRY_SYNC_TRIGGER_AND_RESTORE_VALIDATED"
        )
    else:
        classification = (
            "D119_TOP_LEVEL_TV_ENTRY_TRIGGER_NOT_OBSERVED_CLEANUP_VALIDATED"
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
        "onn_revision":
            local_revision,
        "onn_country_name":
            local_country,
        "local_remote_parity":
            (
                local_hash
                == remote_hash
                == original_hash
            ),
        "top_level_entry_observed":
            observed,
        "linux_original_content_restored":
            remote_hash
            == original_hash,
        "onn_original_content_restored":
            local_hash
            == original_hash,
        "session_active":
            not restored,
        "next_action":
            (
                "D-119 is complete."
                if restored
                else (
                    "Keep ADB connected, press TV Refresh once, "
                    "and re-run D-119 --phase final."
                )
            ),
    }


def render(
    report: dict[str, Any],
) -> str:
    lines = [
        "PrivyHub D-119 D5.4 TV-entry sync-trigger probe",
        f"Phase: {report.get('phase')}",
        f"Classification: {report.get('classification')}",
        "",
        "REVISIONS",
        f"  initial_revision: {report.get('initial_revision')}",
        f"  prepared_revision: {report.get('prepared_revision')}",
        f"  restore_revision: {report.get('restore_revision')}",
        f"  onn_revision: {report.get('onn_revision')}",
        "",
        "TRIGGER SIGNAL",
        f"  marker_country_name: {report.get('marker_country_name')}",
        f"  onn_country_name: {report.get('onn_country_name')}",
        f"  adb_status: {report.get('adb_status')}",
        f"  top_level_entry_observed: {report.get('top_level_entry_observed')}",
        f"  local_remote_parity: {report.get('local_remote_parity')}",
        "",
        "RESTORE",
        f"  linux_original_content_restored: {report.get('linux_original_content_restored')}",
        f"  onn_original_content_restored: {report.get('onn_original_content_restored')}",
        f"  session_active: {report.get('session_active')}",
        "",
        f"Next action: {report.get('next_action')}",
        "",
        "D-119 never changes country_code.",
        "D-119 never prints network addresses or the full saved TV state.",
        "The probe restores Linux user-state content before cleanup.",
        f"JSON: {report.get('json_path')}",
        f"TEXT: {report.get('text_path')}",
    ]

    return "\n".join(
        lines
    ) + "\n"


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
            "language_code": "eng",
            "language_name": "English",
            "country_code": "",
            "country_name": "All Countries",
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
        "D119 TV Entry Validation r5",
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
        "D119_PROBE_SELF_TEST_OK"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--repo",
        default=".",
    )

    ap.add_argument(
        "--phase",
        choices=(
            "prepare",
            "verify",
            "final",
        ),
    )

    ap.add_argument(
        "--self-test",
        action="store_true",
    )

    args = ap.parse_args()

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
    raise SystemExit(main())
