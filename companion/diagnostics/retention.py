from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

RETENTION_SCHEMA = "privyhub_diagnostic_retention_v1"
MIB = 1024 * 1024

POLICY: dict[str, Any] = {
    "schema": RETENTION_SCHEMA,
    "automatic": False,
    "families": {
        "transport_forward": {
            "relative_path": "logs/transport_probe",
            "max_bytes": 256 * MIB,
            "min_keep_files": 8,
        },
        "transport_reverse": {
            "relative_path": "logs/transport_reverse",
            "max_bytes": 128 * MIB,
            "min_keep_files": 8,
        },
        "debug_bundles": {
            "relative_path": "logs/debug_bundles",
            "max_bytes": 64 * MIB,
            "min_keep_files": 8,
        },
    },
    "protected_extensions": [".json", ".md", ".txt"],
    "raw_name_overrides": [
        "pktmon_full.txt",
    ],
    "protected_name_tokens": [
        "crash",
        "degraded",
        "error",
        "exception",
        "fail",
        "failed",
        "failure",
        "latest",
        "loss",
        "unrecoverable",
    ],
    "never_touch_prefixes": [
        "docs/memory",
        "archive/patch_backups",
    ],
}

_IPV4_RE = re.compile(
    r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)"
)
_MAC_RE = re.compile(
    r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])"
)


def policy_sha256() -> str:
    encoded = json.dumps(
        POLICY,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_label(value: str) -> str:
    value = _IPV4_RE.sub("<redacted-address>", value)
    return _MAC_RE.sub("<redacted-address>", value)


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _protected_reason(
    path: Path,
    *,
    newest_paths: set[Path],
) -> str | None:
    if path in newest_paths:
        return "newest_minimum"

    folded = path.name.casefold()

    raw_names = {
        str(value).casefold()
        for value in POLICY.get(
            "raw_name_overrides",
            [],
        )
    }

    if (
        path.suffix.lower()
        in set(POLICY["protected_extensions"])
        and folded not in raw_names
    ):
        return "summary_extension"

    for token in POLICY["protected_name_tokens"]:
        if token in folded:
            return "evidence_name_token:" + token

    return None


def _family_plan(
    project_root: Path,
    family_name: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    relative_path = str(config["relative_path"])
    directory = (project_root / relative_path).resolve()

    if not _is_under(directory, project_root):
        raise RuntimeError("Retention family escaped project root")

    max_bytes = max(1, int(config["max_bytes"]))
    min_keep = max(1, int(config["min_keep_files"]))

    if not directory.is_dir():
        return {
            "family": family_name,
            "relative_path": relative_path,
            "exists": False,
            "max_bytes": max_bytes,
            "min_keep_files": min_keep,
            "file_count": 0,
            "total_bytes": 0,
            "protected_count": 0,
            "protected_bytes": 0,
            "candidate_count": 0,
            "candidate_bytes": 0,
            "projected_bytes": 0,
            "blocked_by_protected_evidence": False,
            "candidate_labels": [],
            "_candidate_paths": [],
        }

    rows: list[tuple[Path, int, int]] = []

    for path in directory.rglob("*"):
        try:
            if not path.is_file() or path.is_symlink():
                continue

            resolved = path.resolve()
            if not _is_under(resolved, directory):
                continue

            stat = resolved.stat()
            rows.append(
                (
                    resolved,
                    int(stat.st_size),
                    int(stat.st_mtime_ns),
                )
            )
        except OSError:
            continue

    rows.sort(
        key=lambda item: (
            item[2],
            str(item[0]).casefold(),
        ),
        reverse=True,
    )

    newest_paths = {
        row[0]
        for row in rows[:min_keep]
    }

    total_bytes = sum(row[1] for row in rows)

    protected: list[tuple[Path, int, int, str]] = []
    eligible: list[tuple[Path, int, int]] = []

    for path, size, mtime_ns in rows:
        reason = _protected_reason(
            path,
            newest_paths=newest_paths,
        )
        if reason is None:
            eligible.append((path, size, mtime_ns))
        else:
            protected.append((path, size, mtime_ns, reason))

    eligible.sort(
        key=lambda item: (
            item[2],
            str(item[0]).casefold(),
        )
    )

    projected = total_bytes
    candidates: list[tuple[Path, int]] = []

    if projected > max_bytes:
        for path, size, _mtime_ns in eligible:
            if projected <= max_bytes:
                break
            candidates.append((path, size))
            projected -= size

    candidate_bytes = sum(size for _path, size in candidates)
    protected_bytes = sum(size for _path, size, _mtime, _reason in protected)

    labels: list[dict[str, Any]] = []
    for path, size in candidates[:20]:
        try:
            relative = path.relative_to(project_root).as_posix()
        except ValueError:
            relative = path.name
        labels.append(
            {
                "path": _safe_label(relative),
                "bytes": size,
            }
        )

    return {
        "family": family_name,
        "relative_path": relative_path,
        "exists": True,
        "max_bytes": max_bytes,
        "min_keep_files": min_keep,
        "file_count": len(rows),
        "total_bytes": total_bytes,
        "protected_count": len(protected),
        "protected_bytes": protected_bytes,
        "candidate_count": len(candidates),
        "candidate_bytes": candidate_bytes,
        "projected_bytes": projected,
        "blocked_by_protected_evidence": projected > max_bytes,
        "candidate_labels": labels,
        "_candidate_paths": [str(path) for path, _size in candidates],
    }


def build_retention_plan(project_root: Path) -> dict[str, Any]:
    root = project_root.resolve()

    families = [
        _family_plan(root, family_name, config)
        for family_name, config in POLICY["families"].items()
    ]

    return {
        "schema": RETENTION_SCHEMA,
        "policy_sha256": policy_sha256(),
        "automatic": False,
        "apply_requested": False,
        "project_root_in_output": False,
        "durable_memory_in_scope": False,
        "patch_backups_in_scope": False,
        "families": families,
        "total_candidate_count": sum(
            int(item["candidate_count"])
            for item in families
        ),
        "total_candidate_bytes": sum(
            int(item["candidate_bytes"])
            for item in families
        ),
    }


def public_plan(plan: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(plan))
    for family in result.get("families", []):
        if isinstance(family, dict):
            family.pop("_candidate_paths", None)
    return result


def apply_retention_plan(
    project_root: Path,
    *,
    expected_policy_sha256: str,
) -> dict[str, Any]:
    if expected_policy_sha256 != policy_sha256():
        raise RuntimeError(
            "Retention policy SHA-256 confirmation mismatch"
        )

    root = project_root.resolve()
    plan = build_retention_plan(root)

    deleted_count = 0
    deleted_bytes = 0
    failures: list[dict[str, str]] = []

    for family in plan["families"]:
        family_root = (
            root / str(family["relative_path"])
        ).resolve()

        for raw_path in family.get("_candidate_paths", []):
            path = Path(raw_path)
            try:
                resolved = path.resolve()

                if not _is_under(resolved, family_root):
                    raise RuntimeError(
                        "candidate escaped family root"
                    )

                if not resolved.is_file() or resolved.is_symlink():
                    raise RuntimeError(
                        "candidate is no longer a regular file"
                    )

                size = int(resolved.stat().st_size)
                resolved.unlink()
                deleted_count += 1
                deleted_bytes += size

            except Exception as exc:
                failures.append(
                    {
                        "path": _safe_label(path.name),
                        "error_class": type(exc).__name__,
                    }
                )

    after = build_retention_plan(root)

    return {
        "schema": RETENTION_SCHEMA,
        "policy_sha256": policy_sha256(),
        "automatic": False,
        "apply_requested": True,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "failure_count": len(failures),
        "failures": failures,
        "after": public_plan(after),
    }
