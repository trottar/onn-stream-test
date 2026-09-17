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
SESSION_REL = Path("data/tv_state/.d117_pull_probe_session.json")
LOG_JSON_REL = Path("logs/tv/d117_linux_authority_pull_probe.json")
LOG_TEXT_REL = Path("logs/tv/d117_linux_authority_pull_probe.txt")

MARKER_PREFIX = "D117 Pull Validation"
CLIENT_ID = "d117-runtime-probe"


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
        "d117_tv_state_plugin",
    )
    d116_module = load_module(
        repo / "tools/probes/d116_android_tv_state_sync_probe.py",
        "d117_d116_probe",
    )
    return plugin_module.TvStatePlugin, d116_module


def canonical_sha(
    plugin_class,
    state: dict[str, Any],
) -> str:
    normalized = plugin_class.normalize_user_state(
        state
    )
    raw = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def http_json(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    body = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "PrivyHub-D117-Probe/1.0",
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
    if not isinstance(payload, dict):
        raise RuntimeError(
            "D-117 session root is invalid"
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
    state: dict[str, Any],
) -> str:
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

    normalized = plugin_class.normalize_user_state(
        candidate
    )

    normalized_code = str(
        normalized["preferences"].get(
            "country_code",
            "",
        )
        or ""
    )

    if normalized_code != original_code:
        raise RuntimeError(
            "D-117 marker changed country code"
        )

    return normalized


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
        return None, {
            **adb_info,
            "snapshot_ok": False,
        }

    state, meta = (
        d116_module.local_projection(
            serial,
            plugin_class,
        )
    )
    return state, {
        **adb_info,
        **meta,
    }


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


def write_report(
    repo: Path,
    report: dict[str, Any],
) -> None:
    json_path = (
        repo / LOG_JSON_REL
    )
    text_path = (
        repo / LOG_TEXT_REL
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

    lines = [
        "PrivyHub D-117 D5.4 Linux-authority pull validation",
        f"Phase: {report.get('phase')}",
        f"Classification: {report.get('classification')}",
        "",
        "LINUX AUTHORITY",
        f"  initial_revision: {report.get('initial_revision')}",
        f"  prepared_revision: {report.get('prepared_revision')}",
        f"  restore_revision: {report.get('restore_revision')}",
        "",
        "PULL SIGNAL",
        f"  original_country_name: {report.get('original_country_name')}",
        f"  marker_country_name: {report.get('marker_country_name')}",
        f"  onn_country_name: {report.get('onn_country_name')}",
        f"  onn_stored_revision: {report.get('onn_stored_revision')}",
        f"  local_remote_parity: {report.get('local_remote_parity')}",
        "",
        "RESTORE",
        f"  linux_original_content_restored: {report.get('linux_original_content_restored')}",
        f"  onn_original_content_restored: {report.get('onn_original_content_restored')}",
        f"  session_active: {report.get('session_active')}",
        "",
        f"Next action: {report.get('next_action')}",
        "",
        "The country code is never changed by D-117.",
        "The full saved TV state is never printed in the report.",
        "A successful D-117 advances the Linux revision twice but restores the original user-state content.",
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


def prepare(
    repo: Path,
    plugin_class,
    d116_module,
) -> dict[str, Any]:
    if load_session(
        repo
    ) is not None:
        return {
            "phase": "prepare",
            "classification":
                "D117_SESSION_ALREADY_ACTIVE",
            "session_active": True,
            "next_action":
                "Do not prepare again; continue with --phase verify.",
        }

    http, envelope = http_json(
        "GET",
        "/plugins/tv_state/state",
    )
    if (
        http != 200
        or not envelope.get(
            "initialized"
        )
        or not isinstance(
            envelope.get("state"),
            dict,
        )
    ):
        return {
            "phase": "prepare",
            "classification":
                "D117_LINUX_AUTHORITY_UNAVAILABLE",
            "session_active": False,
            "next_action":
                "Keep the companion running and inspect the endpoint.",
        }

    original_state = (
        plugin_class.normalize_user_state(
            envelope["state"]
        )
    )
    initial_revision = int(
        envelope.get(
            "server_revision"
        )
        or 0
    )
    original_hash = canonical_sha(
        plugin_class,
        original_state,
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

    if (
        not local_meta.get(
            "snapshot_ok"
        )
        or local_hash != original_hash
        or int(
            local_meta.get(
                "server_revision_pref"
            )
            or 0
        ) != initial_revision
    ):
        return {
            "phase": "prepare",
            "classification":
                "D117_PREPARE_PRECONDITION_PARITY_FAILED",
            "initial_revision":
                initial_revision,
            "onn_stored_revision":
                local_meta.get(
                    "server_revision_pref"
                ),
            "local_remote_parity":
                local_hash == original_hash,
            "session_active":
                False,
            "next_action":
                "Open TV once and re-run prepare after D-116 parity is restored.",
        }

    original_country_name = (
        state_country_name(
            original_state
        )
    )
    marker = (
        f"{MARKER_PREFIX} r{initial_revision + 1}"
    )

    modified_state = marker_state(
        plugin_class,
        original_state,
        marker,
    )
    modified_hash = canonical_sha(
        plugin_class,
        modified_state,
    )

    if modified_hash == original_hash:
        raise RuntimeError(
            "D-117 marker did not change durable state"
        )

    put_http, result = put_state(
        plugin_class,
        base_revision=
            initial_revision,
        state=
            modified_state,
    )

    prepared_revision = int(
        result.get(
            "server_revision"
        )
        or 0
    )

    if (
        put_http != 200
        or result.get(
            "ok"
        ) is not True
        or result.get(
            "changed"
        ) is not True
        or result.get(
            "conflict"
        ) is True
        or prepared_revision !=
            initial_revision + 1
    ):
        return {
            "phase": "prepare",
            "classification":
                "D117_PREPARE_LINUX_WRITE_FAILED",
            "initial_revision":
                initial_revision,
            "prepared_revision":
                prepared_revision,
            "session_active":
                False,
            "next_action":
                "Do not open TV for D-117; inspect the Linux TV-state endpoint.",
        }

    session = {
        "schema":
            "privyhub_d117_pull_session_v1",
        "created_at_ms":
            int(time.time() * 1000),
        "initial_revision":
            initial_revision,
        "prepared_revision":
            prepared_revision,
        "restore_revision":
            None,
        "original_state":
            original_state,
        "original_state_sha256":
            original_hash,
        "prepared_state_sha256":
            modified_hash,
        "original_country_name":
            original_country_name,
        "marker_country_name":
            marker,
    }
    write_session(
        repo,
        session,
    )

    return {
        "phase": "prepare",
        "classification":
            "D117_PULL_TEST_PREPARED",
        "initial_revision":
            initial_revision,
        "prepared_revision":
            prepared_revision,
        "original_country_name":
            original_country_name,
        "marker_country_name":
            marker,
        "local_remote_parity":
            True,
        "session_active":
            True,
        "next_action":
            "Open TV on the onn once. Confirm the Country label shows the D117 marker, then run --phase verify.",
    }


def verify_and_restore(
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
                "D117_NO_ACTIVE_SESSION",
            "session_active":
                False,
            "next_action":
                "Run --phase prepare first.",
        }

    if session.get(
        "restore_revision"
    ) is not None:
        return {
            "phase": "verify",
            "classification":
                "D117_RESTORE_ALREADY_PREPARED",
            "initial_revision":
                session.get(
                    "initial_revision"
                ),
            "prepared_revision":
                session.get(
                    "prepared_revision"
                ),
            "restore_revision":
                session.get(
                    "restore_revision"
                ),
            "session_active":
                True,
            "next_action":
                "Open TV once and run --phase final.",
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
    onn_country_name = (
        state_country_name(
            local_state
        )
        if isinstance(
            local_state,
            dict,
        )
        else ""
    )
    onn_revision = int(
        local_meta.get(
            "server_revision_pref"
        )
        or 0
    )

    pull_observed = (
        local_meta.get(
            "snapshot_ok"
        )
        and remote_revision ==
            prepared_revision
        and remote_hash ==
            prepared_hash
        and local_hash ==
            prepared_hash
        and onn_revision ==
            prepared_revision
        and onn_country_name ==
            session[
                "marker_country_name"
            ]
    )

    # Restore only if Linux is still exactly the state D-117 prepared.
    # This prevents the diagnostic from overwriting any unrelated newer
    # mutation that occurred while the user was opening TV.
    if not (
        remote_revision ==
            prepared_revision
        and remote_hash ==
            prepared_hash
    ):
        return {
            "phase": "verify",
            "classification":
                "D117_LINUX_CHANGED_DURING_TEST_NO_RESTORE",
            "initial_revision":
                session.get(
                    "initial_revision"
                ),
            "prepared_revision":
                prepared_revision,
            "onn_country_name":
                onn_country_name,
            "onn_stored_revision":
                onn_revision,
            "local_remote_parity":
                local_hash ==
                remote_hash,
            "session_active":
                True,
            "next_action":
                "Do not continue the probe; Linux changed independently and D-117 refused to overwrite it.",
        }

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
        and restore_revision ==
            prepared_revision + 1
        and str(
            restored.get(
                "state_sha256"
            )
            or ""
        ) ==
            original_hash
    )

    if not restored_ok:
        return {
            "phase": "verify",
            "classification":
                "D117_LINUX_RESTORE_FAILED",
            "initial_revision":
                session.get(
                    "initial_revision"
                ),
            "prepared_revision":
                prepared_revision,
            "restore_revision":
                restore_revision,
            "onn_country_name":
                onn_country_name,
            "onn_stored_revision":
                onn_revision,
            "local_remote_parity":
                local_hash ==
                prepared_hash,
            "session_active":
                True,
            "next_action":
                "Do not continue until Linux TV-state restoration is inspected.",
        }

    session[
        "restore_revision"
    ] = restore_revision
    session[
        "pull_observed"
    ] = bool(
        pull_observed
    )
    write_session(
        repo,
        session,
    )

    return {
        "phase": "verify",
        "classification":
            (
                "D117_LINUX_TO_ONN_PULL_VALIDATED_RESTORE_PENDING"
                if pull_observed
                else
                "D117_PULL_NOT_OBSERVED_LINUX_RESTORED"
            ),
        "initial_revision":
            session.get(
                "initial_revision"
            ),
        "prepared_revision":
            prepared_revision,
        "restore_revision":
            restore_revision,
        "original_country_name":
            session.get(
                "original_country_name"
            ),
        "marker_country_name":
            session.get(
                "marker_country_name"
            ),
        "onn_country_name":
            onn_country_name,
        "onn_stored_revision":
            onn_revision,
        "local_remote_parity":
            local_hash ==
            prepared_hash,
        "linux_original_content_restored":
            True,
        "session_active":
            True,
        "next_action":
            "Open TV on the onn once more so it pulls the restored Linux state, then run --phase final.",
    }


def final_classification(
    *,
    restored: bool,
    marker_pull_observed: bool,
) -> str:
    if not restored:
        return (
            "D117_FINAL_RESTORE_PARITY_FAILED"
        )

    if marker_pull_observed:
        return (
            "D117_LINUX_AUTHORITY_PULL_AND_RESTORE_RUNTIME_VALIDATED"
        )

    return (
        "D117_LINUX_AUTHORITY_RESTORE_PULL_RUNTIME_VALIDATED"
    )


def final_verify(
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
                "D117_NO_ACTIVE_SESSION",
            "session_active":
                False,
            "next_action":
                "There is no D-117 session to finalize.",
        }

    restore_revision_value = (
        session.get(
            "restore_revision"
        )
    )
    if restore_revision_value is None:
        return {
            "phase": "final",
            "classification":
                "D117_RESTORE_NOT_PREPARED",
            "initial_revision":
                session.get(
                    "initial_revision"
                ),
            "prepared_revision":
                session.get(
                    "prepared_revision"
                ),
            "session_active":
                True,
            "next_action":
                "Run --phase verify first.",
        }

    restore_revision = int(
        restore_revision_value
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
    onn_country_name = (
        state_country_name(
            local_state
        )
        if isinstance(
            local_state,
            dict,
        )
        else ""
    )
    onn_revision = int(
        local_meta.get(
            "server_revision_pref"
        )
        or 0
    )

    restored = (
        remote_revision ==
            restore_revision
        and remote_hash ==
            original_hash
        and local_hash ==
            original_hash
        and onn_revision ==
            restore_revision
        and onn_country_name ==
            session[
                "original_country_name"
            ]
    )

    if restored:
        delete_session(
            repo
        )

    return {
        "phase": "final",
        "classification":
            final_classification(
                restored =
                    restored,
                marker_pull_observed =
                    session.get(
                        "pull_observed"
                    ) is True,
            ),
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
        "original_country_name":
            session.get(
                "original_country_name"
            ),
        "marker_country_name":
            session.get(
                "marker_country_name"
            ),
        "onn_country_name":
            onn_country_name,
        "onn_stored_revision":
            onn_revision,
        "local_remote_parity":
            (
                local_hash ==
                remote_hash ==
                original_hash
            ),
        "linux_original_content_restored":
            remote_hash ==
            original_hash,
        "onn_original_content_restored":
            local_hash ==
            original_hash,
        "session_active":
            not restored,
        "next_action":
            (
                "D-117 is complete."
                if restored
                else
                "Open TV once and re-run --phase final; do not prepare a new session."
            ),
    }


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
                "US",
            "country_name":
                "United States",
        },
        "managed_providers": [],
        "providers": [],
        "channels": [],
    }

    original = (
        plugin_class.normalize_user_state(
            state
        )
    )
    changed = marker_state(
        plugin_class,
        original,
        "D117 Pull Validation r3",
    )

    assert (
        original["preferences"][
            "country_code"
        ]
        ==
        changed["preferences"][
            "country_code"
        ]
    )
    assert (
        original["preferences"][
            "country_name"
        ]
        !=
        changed["preferences"][
            "country_name"
        ]
    )
    assert canonical_sha(
        plugin_class,
        original,
    ) != canonical_sha(
        plugin_class,
        changed,
    )

    assert final_classification(
        restored = True,
        marker_pull_observed = True,
    ) == (
        "D117_LINUX_AUTHORITY_PULL_AND_RESTORE_RUNTIME_VALIDATED"
    )

    assert final_classification(
        restored = True,
        marker_pull_observed = False,
    ) == (
        "D117_LINUX_AUTHORITY_RESTORE_PULL_RUNTIME_VALIDATED"
    )

    assert final_classification(
        restored = False,
        marker_pull_observed = True,
    ) == (
        "D117_FINAL_RESTORE_PARITY_FAILED"
    )

    print(
        "D117_PROBE_SELF_TEST_OK"
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
        report = verify_and_restore(
            repo,
            plugin_class,
            d116_module,
        )
    else:
        report = final_verify(
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
