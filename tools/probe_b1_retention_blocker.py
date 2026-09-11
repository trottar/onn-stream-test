#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_retention_blocker_audit_v1"
CLASSIFICATION = "B1_RETENTION_BLOCKER_CONTEXT_CAPTURED"
MIB = 1024 * 1024

POLICY: dict[str, Any]
build_retention_plan: Any
policy_sha256: Any

_IPV4_RE = re.compile(r"(?<!\\d)(?:\\d{1,3}\\.){3}\\d{1,3}(?!\\d)")
_MAC_RE = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
RAWISH_TOKENS = ("packet", "pktmon", "trace", "capture", "raw", "etl", "csv", "full")


def safe_label(value: str) -> str:
    return _MAC_RE.sub("<redacted-address>", _IPV4_RE.sub("<redacted-address>", value))


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def protection_reason(path: Path, newest: set[Path]) -> str | None:
    if path in newest:
        return "newest_minimum"
    if path.suffix.lower() in set(POLICY["protected_extensions"]):
        return "summary_extension"
    folded = path.name.casefold()
    for token in POLICY["protected_name_tokens"]:
        if token in folded:
            return "evidence_name_token:" + token
    return None


def audit_family(project_root: Path, family_name: str) -> dict[str, Any]:
    config = POLICY["families"][family_name]
    family_root = (project_root / str(config["relative_path"])).resolve()
    if not is_under(family_root, project_root):
        raise RuntimeError("Retention family escaped project root")

    rows: list[tuple[Path, int, int]] = []
    if family_root.is_dir():
        for path in family_root.rglob("*"):
            try:
                if not path.is_file() or path.is_symlink():
                    continue
                resolved = path.resolve()
                if not is_under(resolved, family_root):
                    continue
                stat = resolved.stat()
                rows.append((resolved, int(stat.st_size), int(stat.st_mtime_ns)))
            except OSError:
                continue

    rows.sort(key=lambda item: (item[2], str(item[0]).casefold()), reverse=True)
    newest = {p for p, _s, _m in rows[:max(1, int(config["min_keep_files"]))]}

    protected=[]
    eligible=[]
    for path,size,mtime in rows:
        reason=protection_reason(path,newest)
        record={
            "path": safe_label(path.relative_to(project_root).as_posix()),
            "name": safe_label(path.name),
            "extension": path.suffix.lower() or "<none>",
            "bytes": size,
            "mib": round(size/MIB,3),
            "reason": reason or "eligible",
            "rawish_name": any(token in path.name.casefold() for token in RAWISH_TOKENS),
        }
        if reason is None:
            eligible.append(record)
        else:
            protected.append(record)

    by_reason=collections.defaultdict(lambda:{"count":0,"bytes":0})
    by_ext=collections.defaultdict(lambda:{"count":0,"bytes":0})
    for row in protected:
        by_reason[row["reason"]]["count"] += 1
        by_reason[row["reason"]]["bytes"] += row["bytes"]
        by_ext[row["extension"]]["count"] += 1
        by_ext[row["extension"]]["bytes"] += row["bytes"]

    protected_sorted=sorted(protected,key=lambda r:r["bytes"],reverse=True)
    summary_protected=[r for r in protected if r["reason"]=="summary_extension"]
    rawish_summary=[r for r in summary_protected if r["rawish_name"] or r["bytes"] >= 4*MIB]

    return {
        "family": family_name,
        "relative_path": str(config["relative_path"]),
        "file_count": len(rows),
        "total_bytes": sum(r["bytes"] for r in protected)+sum(r["bytes"] for r in eligible),
        "limit_bytes": int(config["max_bytes"]),
        "protected_count": len(protected),
        "protected_bytes": sum(r["bytes"] for r in protected),
        "eligible_count": len(eligible),
        "eligible_bytes": sum(r["bytes"] for r in eligible),
        "protection_by_reason": dict(sorted(by_reason.items())),
        "protection_by_extension": dict(sorted(by_ext.items())),
        "largest_protected": protected_sorted[:20],
        "summary_extension_protected_count": len(summary_protected),
        "summary_extension_protected_bytes": sum(r["bytes"] for r in summary_protected),
        "rawish_or_large_summary_extension": sorted(rawish_summary,key=lambda r:r["bytes"],reverse=True)[:20],
    }


def mib(value: int) -> float:
    return value / MIB


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args=parser.parse_args()
    if args.self_test:
        assert safe_label("capture") == "capture"
        assert safe_label("trace") == "trace"
        return 0

    root=Path(args.root).resolve()
    companion_dir = root / "companion"
    if str(companion_dir) not in sys.path:
        sys.path.insert(0, str(companion_dir))
    global POLICY, build_retention_plan, policy_sha256
    from diagnostics.retention import POLICY as _POLICY, build_retention_plan as _build_retention_plan, policy_sha256 as _policy_sha256
    POLICY = _POLICY
    build_retention_plan = _build_retention_plan
    policy_sha256 = _policy_sha256

    plan=build_retention_plan(root)
    forward_plan=next(item for item in plan["families"] if item["family"]=="transport_forward")
    audit=audit_family(root,"transport_forward")

    result={
        "schema":SCHEMA,
        "classification":CLASSIFICATION,
        "policy_sha256":policy_sha256(),
        "production_files_modified":False,
        "retention_files_deleted":0,
        "network_addresses_collected_or_logged":False,
        "forward_plan":{
            "total_bytes":forward_plan["total_bytes"],
            "limit_bytes":forward_plan["max_bytes"],
            "candidate_count":forward_plan["candidate_count"],
            "candidate_bytes":forward_plan["candidate_bytes"],
            "projected_bytes":forward_plan["projected_bytes"],
            "blocked_by_protected_evidence":forward_plan["blocked_by_protected_evidence"],
        },
        "forward_audit":audit,
    }

    out=root/"logs"/"diagnostics"
    out.mkdir(parents=True,exist_ok=True)
    (out/"b1_retention_blocker.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")

    lines=[
        "PrivyHub Phase B1.10 retention blocker audit",
        f"Classification: {CLASSIFICATION}",
        f"Schema: {SCHEMA}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "Retention files deleted: 0",
        f"Policy SHA-256: {policy_sha256()}",
        "",
        "=== FORWARD RETENTION PLAN ===",
        f"Total: {mib(forward_plan['total_bytes']):.3f} MiB",
        f"Limit: {mib(forward_plan['max_bytes']):.3f} MiB",
        f"Existing candidates: {forward_plan['candidate_count']} files / {mib(forward_plan['candidate_bytes']):.3f} MiB",
        f"Projected after candidates: {mib(forward_plan['projected_bytes']):.3f} MiB",
        f"Blocked by protected evidence: {forward_plan['blocked_by_protected_evidence']}",
        "",
        "=== PROTECTED FOOTPRINT ===",
        f"Protected: {audit['protected_count']} files / {mib(audit['protected_bytes']):.3f} MiB",
        f"Eligible: {audit['eligible_count']} files / {mib(audit['eligible_bytes']):.3f} MiB",
        f"Summary-extension protected: {audit['summary_extension_protected_count']} files / {mib(audit['summary_extension_protected_bytes']):.3f} MiB",
        "",
        "Protection by reason:",
    ]
    for reason,row in sorted(audit["protection_by_reason"].items(), key=lambda item:item[1]["bytes"], reverse=True):
        lines.append(f"  {reason}: files={row['count']} MiB={mib(row['bytes']):.3f}")
    lines += ["", "Protection by extension:"]
    for ext,row in sorted(audit["protection_by_extension"].items(), key=lambda item:item[1]["bytes"], reverse=True):
        lines.append(f"  {ext}: files={row['count']} MiB={mib(row['bytes']):.3f}")

    lines += ["", "=== LARGEST PROTECTED FILES ==="]
    for row in audit["largest_protected"]:
        lines.append(f"  {row['mib']:.3f} MiB | {row['reason']} | {row['extension']} | {row['path']}")

    lines += ["", "=== RAW-LIKE OR LARGE FILES PROTECTED ONLY BY SUMMARY EXTENSION ==="]
    if audit["rawish_or_large_summary_extension"]:
        for row in audit["rawish_or_large_summary_extension"]:
            lines.append(f"  {row['mib']:.3f} MiB | {row['extension']} | {row['path']}")
    else:
        lines.append("  NONE")

    lines += [
        "",
        "=== NEXT STEP ===",
        "Inspect raw measurements above before changing retention rules.",
        "Do not apply the B1.9 retention policy while blocked=True.",
    ]
    (out/"b1_retention_blocker.txt").write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")
    print(CLASSIFICATION)
    print("Text:", out/"b1_retention_blocker.txt")
    print("JSON:", out/"b1_retention_blocker.json")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
