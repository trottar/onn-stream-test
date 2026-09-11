#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_FROM_SCRIPT = Path(__file__).resolve().parents[1]
COMPANION_DIR = ROOT_FROM_SCRIPT / "companion"

if str(COMPANION_DIR) not in sys.path:
    sys.path.insert(0, str(COMPANION_DIR))

from diagnostics.retention import (  # noqa: E402
    apply_retention_plan,
    build_retention_plan,
    policy_sha256,
    public_plan,
)


def mib(value: int) -> float:
    return float(value) / 1024.0 / 1024.0


def format_plan(plan: dict) -> str:
    lines = [
        "PrivyHub diagnostic retention plan",
        "Schema: " + str(plan["schema"]),
        "Mode: DRY_RUN",
        "Files deleted: 0",
        "Automatic retention enabled: False",
        "Durable memory in scope: False",
        "Patch backups in scope: False",
        "Policy SHA-256: " + str(plan["policy_sha256"]),
        "",
        "=== FAMILIES ===",
    ]

    for item in plan["families"]:
        lines.append(
            f"{item['family']}: "
            f"files={item['file_count']} "
            f"total_mib={mib(item['total_bytes']):.3f} "
            f"limit_mib={mib(item['max_bytes']):.3f} "
            f"protected={item['protected_count']} "
            f"would_delete={item['candidate_count']} "
            f"would_free_mib={mib(item['candidate_bytes']):.3f} "
            f"projected_mib={mib(item['projected_bytes']):.3f} "
            f"blocked={item['blocked_by_protected_evidence']}"
        )

        labels = item.get("candidate_labels", [])
        if labels:
            lines.append("  First candidates:")
            for row in labels[:10]:
                lines.append(
                    "    "
                    + str(row["path"])
                    + " ("
                    + f"{mib(row['bytes']):.3f}"
                    + " MiB)"
                )

    lines += [
        "",
        "Total would delete: "
        + str(plan["total_candidate_count"])
        + " file(s)",
        "Total would free: "
        + f"{mib(plan['total_candidate_bytes']):.3f}"
        + " MiB",
        "",
        "No files were deleted.",
        "To apply later, re-run with --apply and the exact policy SHA-256.",
    ]

    return "\n".join(lines) + "\n"


def self_test() -> int:
    assert len(policy_sha256()) == 64
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--policy-sha256", default="")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()

    if args.apply:
        if not args.policy_sha256:
            raise SystemExit(
                "--apply requires --policy-sha256"
            )

        result = apply_retention_plan(
            root,
            expected_policy_sha256=args.policy_sha256,
        )
        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if result["failure_count"] == 0 else 1

    plan = public_plan(
        build_retention_plan(root)
    )

    if args.json_only:
        print(
            json.dumps(
                plan,
                sort_keys=True,
            )
        )
        return 0

    output = format_plan(plan)
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "b1_retention_plan.txt").write_text(
        output,
        encoding="utf-8",
        newline="\n",
    )
    (out_dir / "b1_retention_plan.json").write_text(
        json.dumps(
            plan,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print("B1_RETENTION_PLAN_CAPTURED")
    print("Text:", out_dir / "b1_retention_plan.txt")
    print("JSON:", out_dir / "b1_retention_plan.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
