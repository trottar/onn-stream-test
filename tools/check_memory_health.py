#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LIMITS = {
    "docs/memory/CURRENT.md": {
        "soft_bytes": 10 * 1024,
        "hard_bytes": 20 * 1024,
        "soft_lines": 200,
        "hard_lines": 400,
    },
    "docs/memory/handoffs/CURRENT_HANDOFF.md": {
        "soft_bytes": 8 * 1024,
        "hard_bytes": 15 * 1024,
    },
    "docs/memory/MEMORY.md": {
        "soft_bytes": 35 * 1024,
        "hard_bytes": 60 * 1024,
    },
}

REQUIRED = [
    "docs/memory/AGENTS.md",
    "docs/memory/CURRENT.md",
    "docs/memory/MEMORY.md",
    "docs/memory/MAINTENANCE.md",
    "docs/memory/handoffs/CURRENT_HANDOFF.md",
]

CURRENT_REQUIRED_HEADINGS = [
    "## Active Objective",
    "## Current Work Item",
    "## Verified State",
    "## Next Action",
    "## Success Criteria",
    "## Do Not Reopen Without New Evidence",
    "## Relevant References",
]


def file_stats(path: Path) -> dict:
    data = path.read_bytes()
    return {
        "bytes": len(data),
        "lines": len(data.splitlines()),
    }


def classify(stats: dict, limits: dict) -> str:
    if (
        stats["bytes"] > limits.get("hard_bytes", 10**18)
        or stats["lines"] > limits.get("hard_lines", 10**18)
    ):
        return "HARD_LIMIT"
    if (
        stats["bytes"] > limits.get("soft_bytes", 10**18)
        or stats["lines"] > limits.get("soft_lines", 10**18)
    ):
        return "SOFT_LIMIT"
    return "healthy"


def analyze(repo: Path) -> dict:
    report = {
        "required_missing": [],
        "files": {},
        "current_structure": {},
        "status": "healthy",
    }

    for rel in REQUIRED:
        if not (repo / rel).is_file():
            report["required_missing"].append(rel)

    for rel, limits in LIMITS.items():
        path = repo / rel
        if not path.is_file():
            continue
        stats = file_stats(path)
        stats["status"] = classify(stats, limits)
        report["files"][rel] = stats

    current = repo / "docs/memory/CURRENT.md"
    if current.is_file():
        text = current.read_text(encoding="utf-8-sig")
        counts = {
            heading: text.count(heading)
            for heading in CURRENT_REQUIRED_HEADINGS
        }
        report["current_structure"]["heading_counts"] = counts
        report["current_structure"]["one_active_objective"] = (
            counts.get("## Active Objective") == 1
        )
        report["current_structure"]["one_next_action"] = (
            counts.get("## Next Action") == 1
        )
        report["current_structure"]["all_required_headings_once"] = all(
            value == 1 for value in counts.values()
        )

    hard = any(
        item.get("status") == "HARD_LIMIT"
        for item in report["files"].values()
    )
    soft = any(
        item.get("status") == "SOFT_LIMIT"
        for item in report["files"].values()
    )
    structure_bad = not report["current_structure"].get(
        "all_required_headings_once", False
    )

    if report["required_missing"] or hard or structure_bad:
        report["status"] = "maintenance_required"
    elif soft:
        report["status"] = "maintenance_recommended"

    return report


def print_report(report: dict) -> None:
    print("Memory health:")
    print()
    for rel, item in report["files"].items():
        print(rel)
        print(f"  lines: {item['lines']}")
        print(f"  size: {item['bytes']} bytes")
        print(f"  status: {item['status']}")
        print()

    if report["required_missing"]:
        print("Missing required files:")
        for rel in report["required_missing"]:
            print(f"  - {rel}")
        print()

    structure = report.get("current_structure", {})
    print("CURRENT.md structure:")
    print(
        "  one active objective: "
        + str(structure.get("one_active_objective", False))
    )
    print(
        "  one next action: "
        + str(structure.get("one_next_action", False))
    )
    print(
        "  required headings exactly once: "
        + str(structure.get("all_required_headings_once", False))
    )
    print()
    print(f"Overall: {report['status']}")


def self_test() -> int:
    assert classify(
        {"bytes": 100, "lines": 10},
        {"soft_bytes": 200, "hard_bytes": 400},
    ) == "healthy"
    assert classify(
        {"bytes": 250, "lines": 10},
        {"soft_bytes": 200, "hard_bytes": 400},
    ) == "SOFT_LIMIT"
    assert classify(
        {"bytes": 450, "lines": 10},
        {"soft_bytes": 200, "hard_bytes": 400},
    ) == "HARD_LIMIT"
    print("MEMORY_HEALTH_SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--json-out")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    report = analyze(repo)
    print_report(report)

    if args.json_out:
        out = Path(args.json_out)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return 1 if report["status"] == "maintenance_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
