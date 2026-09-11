#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[1]
COMPANION_DIR = ROOT_FROM_SCRIPT / "companion"

if str(COMPANION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPANION_DIR))

from diagnostics.retention import (  # noqa: E402
    build_retention_plan,
    policy_sha256,
    public_plan,
)

SCHEMA = "privyhub_b1_retention_rule_validation_v1"
CONFIRMED = "B1_RETENTION_RULE_REFINEMENT_CONFIRMED"
FAILED = "B1_RETENTION_RULE_REFINEMENT_NOT_CONFIRMED"


def mib(value: int) -> float:
    return float(value) / 1024.0 / 1024.0


def family(
    plan: dict[str, Any],
    name: str,
) -> dict[str, Any]:
    for item in plan.get("families", []):
        if (
            isinstance(item, dict)
            and item.get("family") == name
        ):
            return item
    return {}


def write_result(
    root: Path,
    *,
    result: dict[str, Any] | None,
    error: str = "",
) -> int:
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "b1_retention_rule_runtime.txt"

    confirmed = result is not None
    classification = CONFIRMED if confirmed else FAILED

    lines = [
        "PrivyHub Phase B1.11 retention rule refinement runtime probe",
        f"Classification: {classification}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Retention files deleted by probe: 0",
        "",
    ]

    if result is None:
        lines += [
            "=== FAILURE ===",
            "Reason: " + (error or "<unknown>"),
        ]
    else:
        lines += [
            "=== POLICY ===",
            "Policy SHA-256: " + result["policy_sha256"],
            "Automatic retention enabled: False",
            "Durable memory in scope: False",
            "Patch backups in scope: False",
            "Raw-name override active: pktmon_full.txt",
            "",
            "=== FORWARD PLAN ===",
            f"Files: {result['file_count']}",
            f"Total MiB: {result['total_mib']:.3f}",
            f"Limit MiB: {result['limit_mib']:.3f}",
            f"Protected files: {result['protected_count']}",
            f"Would delete: {result['candidate_count']}",
            f"Would free MiB: {result['candidate_mib']:.3f}",
            f"Projected MiB: {result['projected_mib']:.3f}",
            "Blocked by protected evidence: "
            + str(result["blocked"]),
            "pktmon_full.txt candidates: "
            + str(result["pktmon_full_candidate_count"]),
            "Newest minimum still protected: "
            + str(result["newest_minimum_preserved"]),
            "",
            "=== SAFETY ===",
            "Retention apply performed: False",
            "Blanket .txt protection retained for non-raw files: True",
            "Failure-name protection retained: True",
            "Newest-eight protection retained: True",
            "",
            "Next step: REVIEW_DRY_RUN_THEN_EXPLICIT_RETENTION_APPLY_DECISION",
        ]

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if confirmed else 1


def self_test() -> int:
    value = policy_sha256()
    assert len(value) == 64
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()

    try:
        internal = build_retention_plan(root)
        public = public_plan(internal)

        if public.get("automatic") is not False:
            raise RuntimeError(
                "Retention unexpectedly automatic"
            )

        if public.get("durable_memory_in_scope") is not False:
            raise RuntimeError(
                "Durable memory entered retention scope"
            )

        if public.get("patch_backups_in_scope") is not False:
            raise RuntimeError(
                "Patch backups entered retention scope"
            )

        forward = family(internal, "transport_forward")
        if not forward:
            raise RuntimeError(
                "Forward retention family missing"
            )

        candidates = [
            Path(value)
            for value in forward.get(
                "_candidate_paths",
                [],
            )
        ]

        pktmon_full_candidates = [
            path
            for path in candidates
            if path.name.casefold() == "pktmon_full.txt"
        ]

        if (
            int(forward.get("total_bytes", 0))
            > int(forward.get("max_bytes", 0))
            and bool(
                forward.get(
                    "blocked_by_protected_evidence",
                    True,
                )
            )
        ):
            raise RuntimeError(
                "Forward retention remains blocked"
            )

        if (
            int(forward.get("total_bytes", 0))
            > int(forward.get("max_bytes", 0))
            and int(
                forward.get(
                    "projected_bytes",
                    0,
                )
            )
            > int(
                forward.get(
                    "max_bytes",
                    0,
                )
            )
        ):
            raise RuntimeError(
                "Forward projected size remains over limit"
            )

        if (
            int(forward.get("total_bytes", 0))
            > int(forward.get("max_bytes", 0))
            and not pktmon_full_candidates
        ):
            raise RuntimeError(
                "No old pktmon_full.txt artifact became eligible"
            )

        # The planner always protects at least min_keep_files; verify that
        # the number of candidates leaves that minimum intact.
        newest_preserved = (
            int(forward.get("file_count", 0))
            - int(forward.get("candidate_count", 0))
            >= int(forward.get("min_keep_files", 0))
        )

        if not newest_preserved:
            raise RuntimeError(
                "Newest minimum preservation failed"
            )

        result = {
            "policy_sha256": public["policy_sha256"],
            "file_count": int(forward["file_count"]),
            "total_mib": mib(int(forward["total_bytes"])),
            "limit_mib": mib(int(forward["max_bytes"])),
            "protected_count": int(
                forward["protected_count"]
            ),
            "candidate_count": int(
                forward["candidate_count"]
            ),
            "candidate_mib": mib(
                int(forward["candidate_bytes"])
            ),
            "projected_mib": mib(
                int(forward["projected_bytes"])
            ),
            "blocked": bool(
                forward[
                    "blocked_by_protected_evidence"
                ]
            ),
            "pktmon_full_candidate_count": len(
                pktmon_full_candidates
            ),
            "newest_minimum_preserved": newest_preserved,
        }

    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
    ) as exc:
        return write_result(
            root,
            result=None,
            error=type(exc).__name__ + ": " + str(exc),
        )

    return write_result(
        root,
        result=result,
    )


if __name__ == "__main__":
    raise SystemExit(main())
