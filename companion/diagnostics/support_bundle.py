from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
import threading
import time
import zipfile

from pathlib import Path
from typing import Any

SUPPORT_BUNDLE_SCHEMA = "privyhub_support_bundle_result_v1"
CONTEXT_SCHEMA = "privyhub_diagnostics_context_v1"

_BUNDLE_LOCK = threading.Lock()

_ADDRESS_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
_MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


class SupportBundleError(RuntimeError):
    def __init__(
        self,
        code: str,
    ) -> None:
        super().__init__(
            code
        )
        self.code = code


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:
        for chunk in iter(
            lambda: handle.read(
                1024
                * 1024
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def _redact_text(
    value: str,
) -> str:
    value = _ADDRESS_RE.sub(
        "<redacted-address>",
        value,
    )
    return _MAC_RE.sub(
        "<redacted-address>",
        value,
    )


def _sanitize(
    value: Any,
    *,
    depth: int = 0,
) -> Any:
    if depth > 6:
        return None

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        (int, float),
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        return _redact_text(
            value[:512]
        )

    if isinstance(
        value,
        list,
    ):
        return [
            _sanitize(
                item,
                depth=depth + 1,
            )
            for item in value[:256]
        ]

    if isinstance(
        value,
        dict,
    ):
        result: dict[str, Any] = {}

        for index, key in enumerate(
            sorted(
                value,
                key=lambda item: str(item),
            )
        ):
            if index >= 256:
                break

            result[
                str(key)[:128]
            ] = _sanitize(
                value[key],
                depth=depth + 1,
            )

        return result

    return str(
        type(
            value
        ).__name__
    )


def _runtime_versions(
    project_root: Path,
    companion_status: Any,
    health_snapshot: dict[str, Any],
) -> dict[str, Any]:
    versions: dict[str, Any] = {
        "python": (
            platform.python_version()
        ),
        "platform": (
            platform.system()
        ),
        "health_schema": (
            health_snapshot.get(
                "schema"
            )
        ),
    }

    if isinstance(
        companion_status,
        dict,
    ):
        versions[
            "companion_api_version"
        ] = companion_status.get(
            "api_version"
        )

    classifier = health_snapshot.get(
        "classifier"
    )

    if isinstance(
        classifier,
        dict,
    ):
        versions[
            "health_classifier"
        ] = classifier

    config_path = (
        project_root
        / "companion"
        / "games"
        / "config"
        / "emulators.json"
    )

    if config_path.is_file():
        try:
            config = json.loads(
                config_path.read_text(
                    encoding="utf-8-sig",
                    errors="replace",
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            config = {}

        if isinstance(
            config,
            dict,
        ):
            retroarch = config.get(
                "retroarch"
            )

            if isinstance(
                retroarch,
                dict,
            ):
                versions[
                    "retroarch_configured_version"
                ] = retroarch.get(
                    "version"
                )

    return _sanitize(
        versions
    )


def _existing_bundles(
    bundle_root: Path,
) -> set[Path]:
    if not bundle_root.is_dir():
        return set()

    result: set[Path] = set()

    for path in bundle_root.glob(
        "*/SHARE_ME.zip"
    ):
        try:
            if path.is_file():
                result.add(
                    path.resolve()
                )
        except OSError:
            continue

    return result


def _run_existing_bundler(
    project_root: Path,
) -> Path:
    tool = (
        project_root
        / "tools"
        / "privyhub_debug_bundle.py"
    )

    if not tool.is_file():
        raise SupportBundleError(
            "BUNDLE-TOOL-MISSING"
        )

    bundle_root = (
        project_root
        / "logs"
        / "debug_bundles"
    )

    before = _existing_bundles(
        bundle_root
    )

    for attempt in range(
        2
    ):
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(
                        tool
                    ),
                    "--root",
                    str(
                        project_root
                    ),
                    "--mode",
                    "latest",
                ],
                cwd=project_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=45.0,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SupportBundleError(
                "BUNDLE-TOOL-TIMEOUT"
            ) from exc
        except OSError as exc:
            raise SupportBundleError(
                "BUNDLE-TOOL-EXECUTION-FAILED"
            ) from exc

        after = _existing_bundles(
            bundle_root
        )

        created = sorted(
            after - before,
            key=lambda path: (
                path.stat().st_mtime_ns
            ),
            reverse=True,
        )

        if (
            completed.returncode == 0
            and created
        ):
            return created[0]

        if attempt == 0:
            time.sleep(
                1.05
            )
            before = after

    raise SupportBundleError(
        "BUNDLE-TOOL-FAILED"
    )


def _augment_bundle(
    *,
    project_root: Path,
    bundle_path: Path,
    health_snapshot: dict[str, Any],
    companion_status: Any,
) -> None:
    bundle_root = (
        project_root
        / "logs"
        / "debug_bundles"
    ).resolve()

    try:
        resolved_bundle = (
            bundle_path.resolve()
        )
        resolved_bundle.relative_to(
            bundle_root
        )
    except (
        OSError,
        ValueError,
    ) as exc:
        raise SupportBundleError(
            "BUNDLE-PATH-INVALID"
        ) from exc

    out_dir = (
        resolved_bundle.parent
    )

    manifest_path = (
        out_dir
        / "manifest.json"
    )

    summary_path = (
        out_dir
        / "SHARE_ME.txt"
    )

    if (
        not manifest_path.is_file()
        or not summary_path.is_file()
    ):
        raise SupportBundleError(
            "BUNDLE-BASE-INCOMPLETE"
        )

    try:
        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise SupportBundleError(
            "BUNDLE-MANIFEST-INVALID"
        ) from exc

    if not isinstance(
        manifest,
        dict,
    ):
        raise SupportBundleError(
            "BUNDLE-MANIFEST-INVALID"
        )

    context = {
        "schema": CONTEXT_SCHEMA,
        "generated_unix_ms": int(
            time.time()
            * 1000.0
        ),
        "privacy_classification": (
            "sanitized-no-network-identifiers"
        ),
        "versions": _runtime_versions(
            project_root,
            companion_status,
            health_snapshot,
        ),
        "health": _sanitize(
            health_snapshot
        ),
    }

    context_path = (
        out_dir
        / "diagnostics_context.json"
    )

    context_path.write_text(
        json.dumps(
            context,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    try:
        summary = summary_path.read_text(
            encoding="utf-8-sig",
            errors="replace",
        )
    except OSError as exc:
        raise SupportBundleError(
            "BUNDLE-SUMMARY-INVALID"
        ) from exc

    marker = (
        "\nDIAGNOSTICS CONTEXT\n"
        "- diagnostics_context.json contains the bounded current health/event "
        "snapshot and runtime version metadata.\n"
    )

    if marker not in summary:
        summary = (
            summary.rstrip()
            + "\n"
            + marker
            + "\n"
        )

        summary_path.write_text(
            summary,
            encoding="utf-8",
            newline="\n",
        )

    files = manifest.get(
        "files"
    )

    if not isinstance(
        files,
        list,
    ):
        files = []

    filtered = [
        item
        for item in files
        if not (
            isinstance(
                item,
                dict,
            )
            and item.get(
                "path"
            )
            in {
                "SHARE_ME.txt",
                "diagnostics_context.json",
            }
        )
    ]

    filtered.append(
        {
            "path": "diagnostics_context.json",
            "sha256": _sha256_file(
                context_path
            ).upper(),
            "size_bytes": (
                context_path.stat().st_size
            ),
        }
    )

    filtered.append(
        {
            "path": "SHARE_ME.txt",
            "sha256": _sha256_file(
                summary_path
            ).upper(),
            "size_bytes": (
                summary_path.stat().st_size
            ),
        }
    )

    manifest[
        "files"
    ] = filtered

    manifest[
        "diagnostics_context_schema"
    ] = CONTEXT_SCHEMA

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    file_paths = [
        path
        for path in out_dir.rglob(
            "*"
        )
        if (
            path.is_file()
            and path.name
            != "SHARE_ME.zip"
        )
    ]

    with zipfile.ZipFile(
        resolved_bundle,
        "w",
        compression=(
            zipfile.ZIP_DEFLATED
        ),
    ) as archive:
        for path in sorted(
            file_paths,
            key=lambda item: (
                item.relative_to(
                    out_dir
                ).as_posix()
            ),
        ):
            archive.write(
                path,
                path.relative_to(
                    out_dir
                ).as_posix(),
            )

    with zipfile.ZipFile(
        resolved_bundle,
        "r",
    ) as archive:
        bad = archive.testzip()

        if bad is not None:
            raise SupportBundleError(
                "BUNDLE-ZIP-INTEGRITY-FAILED"
            )

        names = set(
            archive.namelist()
        )

        required = {
            "SHARE_ME.txt",
            "manifest.json",
            "diagnostics_context.json",
        }

        if not required.issubset(
            names
        ):
            raise SupportBundleError(
                "BUNDLE-ZIP-INCOMPLETE"
            )


def create_sanitized_support_bundle(
    *,
    project_root: Path,
    health_snapshot: dict[str, Any],
    companion_status: Any,
) -> dict[str, Any]:
    root = project_root.resolve()

    with _BUNDLE_LOCK:
        bundle_path = _run_existing_bundler(
            root
        )

        _augment_bundle(
            project_root=root,
            bundle_path=bundle_path,
            health_snapshot=health_snapshot,
            companion_status=companion_status,
        )

        try:
            relative = bundle_path.resolve().relative_to(
                root
            ).as_posix()
        except (
            OSError,
            ValueError,
        ) as exc:
            raise SupportBundleError(
                "BUNDLE-PATH-INVALID"
            ) from exc

        return {
            "schema": SUPPORT_BUNDLE_SCHEMA,
            "ok": True,
            "filename": "SHARE_ME.zip",
            "relative_path": (
                _redact_text(
                    relative
                )
            ),
            "size_bytes": (
                bundle_path.stat().st_size
            ),
            "sha256": (
                _sha256_file(
                    bundle_path
                )
            ),
            "sanitized": True,
            "manifest_present": True,
            "diagnostics_context_present": True,
            "network_identifiers_in_response": False,
        }
