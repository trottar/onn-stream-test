#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "privyhub_b1_diagnostics_inventory_v1"
CLASSIFICATION = "B1_DIAGNOSTICS_INVENTORY_CAPTURED"

KNOWN_SOURCE = {
    "debug_harness": "tools/run_privyhub_debug.ps1",
    "share_bundle": "tools/privyhub_debug_bundle.py",
    "game_collector": "tools/collect_game_session_diagnostics.py",
    "audio_history": "tools/privyhub_audio_history.py",
    "repo_audit": "tools/audit_repo_checkpoint.py",
    "decoder_session_writer": "companion/games/decoder_session_log.py",
    "host_telemetry": "companion/native_host_telemetry.py",
    "native_stream_manager": "companion/native_stream.py",
    "native_session_io": "companion/native_session_io.py",
    "wgc_bridge": "companion/native_wgc_bridge.py",
    "android_stream": "PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/NativeStreamActivity.kt",
}

RUNTIME_FAMILIES = (
    ("decoder_sessions", "logs/games/decoder_sessions"),
    ("host_telemetry", "logs/games/host_telemetry"),
    ("audio_timing", "logs/games/audio_timing"),
    ("capture_diagnostics", "logs/games/capture_diagnostics"),
    ("debug_bundles", "logs/debug_bundles"),
    ("transport_forward", "logs/transport_probe"),
    ("transport_reverse", "logs/transport_reverse"),
    ("transport_loopback", "logs/transport_loopback"),
    ("repo_audit", "logs/repo_audit"),
    ("android_diagnostics", "logs/android"),
)

LIVE_STATE_DIRS = ("data/games/native_stream",)

DIAGNOSTIC_PATH_RE = re.compile(
    r"(diagnostic|debug|probe|telemetry|decoder_session|audio_history|repo_audit)",
    re.I,
)
SCHEMA_ID_RE = re.compile(r"\bprivyhub_[a-z0-9_]+_v\d+(?:\.\d+)?\b", re.I)

COMMON_FIELDS = (
    "subsystem",
    "severity",
    "event_code",
    "health",
    "measurements",
    "raw_measurements",
    "classification",
    "classifier",
    "session_id",
)

SOURCE_SUFFIXES = {".py", ".ps1", ".kt", ".cs", ".md"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def run_git(root: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout.rstrip()

def safe_read(path: Path, limit: int = 2_000_000) -> str:
    data = path.read_bytes()
    if len(data) > limit:
        return ""
    return data.decode("utf-8-sig", errors="replace")

def tracked_paths(root: Path) -> list[str]:
    rc, out = run_git(root, "ls-files")
    if rc != 0:
        raise RuntimeError("git ls-files failed")
    return [line for line in out.splitlines() if line]

def extract_harness_modes(text: str) -> list[str]:
    match = re.search(r'ValidateSet\(([^)]*)\)', text, re.I | re.S)
    if not match:
        return []
    return re.findall(r'"([^"]+)"', match.group(1))

def json_shape(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "parseable": False,
        "top_level_keys": [],
        "nested_report_keys": [],
        "schema": "",
    }
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return result
    if not isinstance(data, dict):
        return result

    result["parseable"] = True
    result["top_level_keys"] = sorted(str(k) for k in data.keys())

    schema = data.get("schema")
    if isinstance(schema, str) and SCHEMA_ID_RE.fullmatch(schema.strip()):
        result["schema"] = schema.strip()

    report = data.get("report")
    if isinstance(report, dict):
        result["nested_report_keys"] = sorted(str(k) for k in report.keys())

    return result

def family_stats(root: Path, name: str, rel: str) -> dict[str, Any]:
    directory = root / rel
    out: dict[str, Any] = {
        "name": name,
        "path": rel,
        "exists": directory.is_dir(),
        "file_count": 0,
        "total_bytes": 0,
        "extensions": {},
        "newest_age_seconds": None,
        "newest_json_shape": None,
    }
    if not directory.is_dir():
        return out

    files = [p for p in directory.rglob("*") if p.is_file()]
    out["file_count"] = len(files)
    out["total_bytes"] = sum(p.stat().st_size for p in files)
    out["extensions"] = dict(sorted(Counter((p.suffix.lower() or "<none>") for p in files).items()))

    if files:
        newest = max(files, key=lambda p: p.stat().st_mtime_ns)
        out["newest_age_seconds"] = round(max(0.0, time.time() - newest.stat().st_mtime), 3)

    json_files = [
        p for p in files
        if p.suffix.lower() == ".json" and p.stat().st_size <= 2_000_000
    ]
    if json_files:
        newest_json = max(json_files, key=lambda p: p.stat().st_mtime_ns)
        out["newest_json_shape"] = json_shape(newest_json)

    return out

def live_state_stats(root: Path, rel: str) -> dict[str, Any]:
    directory = root / rel
    items = []
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            if not path.is_file():
                continue
            items.append({
                "name": path.name,
                "bytes": path.stat().st_size,
                "shape": json_shape(path),
            })
    return {"path": rel, "exists": directory.is_dir(), "json_files": items}

def scan_schema_ids(root: Path, tracked: list[str]) -> list[str]:
    values: set[str] = set()
    for rel in tracked:
        path = root / rel
        if path.suffix.lower() not in SOURCE_SUFFIXES or not path.is_file():
            continue
        text = safe_read(path)
        if text:
            values.update(x.lower() for x in SCHEMA_ID_RE.findall(text))
    return sorted(values)

def diagnostic_source_inventory(root: Path, tracked: list[str]) -> list[dict[str, Any]]:
    rows = []
    for rel in tracked:
        path = root / rel
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if not DIAGNOSTIC_PATH_RE.search(rel) or not path.is_file():
            continue
        rows.append({
            "path": rel,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return rows

def common_field_coverage(root: Path, diagnostic_paths: list[str]) -> dict[str, list[str]]:
    coverage = {field: [] for field in COMMON_FIELDS}
    for rel in diagnostic_paths:
        path = root / rel
        if not path.is_file():
            continue
        folded = safe_read(path).casefold()
        for field in COMMON_FIELDS:
            if f'"{field}"' in folded or f"'{field}'" in folded:
                coverage[field].append(rel)
    return coverage

def android_diagnostic_surface(root: Path, tracked: list[str]) -> dict[str, Any]:
    diagnostic_activities = [
        rel for rel in tracked
        if rel.startswith("PrivyHub/app/src/main/")
        and "/diagnostics/" in rel
        and rel.endswith(".kt")
    ]

    main_path = root / "PrivyHub/app/src/main/java/com/safeiot/privyhub/MainActivity.kt"
    main_text = safe_read(main_path) if main_path.is_file() else ""
    stream_path = root / KNOWN_SOURCE["android_stream"]
    stream_text = safe_read(stream_path) if stream_path.is_file() else ""

    unified_tokens = (
        "privyhub diagnostics",
        "system health",
        "run self-test",
        "collect diagnostics",
    )
    unified_hits = [token for token in unified_tokens if token in main_text.casefold()]

    decoder_metrics = [
        token for token in (
            "recent_mbps",
            "recentVideoFps",
            "stale",
            "fec",
            "rendered",
        )
        if token.casefold() in stream_text.casefold()
    ]

    return {
        "diagnostic_activity_count": len(diagnostic_activities),
        "diagnostic_activities": diagnostic_activities,
        "main_activity_unified_diagnostics_tokens": unified_hits,
        "unified_gui_detected": bool(unified_hits),
        "native_stream_metric_tokens": decoder_metrics,
    }

def known_source_state(root: Path) -> dict[str, Any]:
    out = {}
    for label, rel in KNOWN_SOURCE.items():
        path = root / rel
        out[label] = {
            "path": rel,
            "exists": path.is_file(),
            "sha256": sha256(path) if path.is_file() else "",
            "bytes": path.stat().st_size if path.is_file() else 0,
        }
    return out

def build_report(root: Path) -> dict[str, Any]:
    tracked = tracked_paths(root)
    source_state = known_source_state(root)

    harness_text = (
        safe_read(root / KNOWN_SOURCE["debug_harness"])
        if source_state["debug_harness"]["exists"]
        else ""
    )
    bundle_text = (
        safe_read(root / KNOWN_SOURCE["share_bundle"])
        if source_state["share_bundle"]["exists"]
        else ""
    )

    modes = extract_harness_modes(harness_text)
    bundle_privacy = {
        "ipv4_redaction": "IPV4_RE" in bundle_text,
        "mac_redaction": "MAC_RE" in bundle_text,
        "ipv6_candidate_redaction": "IPV6_CANDIDATE_RE" in bundle_text,
        "raw_pktmon_exclusion": "pktmon_full.txt" in bundle_text and "pktmon.etl" in bundle_text,
        "share_me_bundle": "SHARE_ME" in bundle_text,
    }

    diag_source = diagnostic_source_inventory(root, tracked)
    diag_paths = [row["path"] for row in diag_source]
    field_coverage = common_field_coverage(root, diag_paths)
    schema_ids = scan_schema_ids(root, tracked)
    android = android_diagnostic_surface(root, tracked)

    runtime = [family_stats(root, name, rel) for name, rel in RUNTIME_FAMILIES]
    live_state = [live_state_stats(root, rel) for rel in LIVE_STATE_DIRS]

    structured_runtime_families = sum(
        1 for item in runtime
        if item["newest_json_shape"] and item["newest_json_shape"]["parseable"]
    )

    common_contract_detected = all(
        bool(field_coverage[field])
        for field in ("subsystem", "severity", "event_code", "health")
    )

    health_aggregator_candidates = [
        rel for rel in tracked
        if re.search(
            r"(health|diagnostic).*(snapshot|state|aggregate)|"
            r"(snapshot|aggregate).*(health|diagnostic)",
            rel,
            re.I,
        )
    ]

    if (
        source_state["debug_harness"]["exists"]
        and source_state["share_bundle"]["exists"]
        and all(bundle_privacy.values())
        and not common_contract_detected
    ):
        next_step = "DESIGN_COMMON_SCHEMA_AND_HEALTH_AGGREGATOR"
    elif common_contract_detected:
        next_step = "AUDIT_EXISTING_COMMON_CONTRACT_BEFORE_NEW_SCHEMA"
    else:
        next_step = "FILL_MISSING_DIAGNOSTIC_FOUNDATION"

    rc, head = run_git(root, "rev-parse", "HEAD")
    if rc != 0:
        head = "<unknown>"

    return {
        "schema": SCHEMA,
        "classification": CLASSIFICATION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "production_files_modified_by_probe": "NONE",
        "network_addresses_collected_or_logged": "NONE",
        "git_head": head.strip(),
        "tracked_file_count": len(tracked),
        "known_source": source_state,
        "harness": {"modes": modes, "mode_count": len(modes), "privacy": bundle_privacy},
        "diagnostic_source": {"count": len(diag_source), "files": diag_source},
        "structured_schema_ids": schema_ids,
        "common_field_coverage": field_coverage,
        "common_event_health_contract_detected": common_contract_detected,
        "health_aggregator_candidates": health_aggregator_candidates,
        "android": android,
        "runtime_families": runtime,
        "structured_runtime_family_count": structured_runtime_families,
        "live_state": live_state,
        "retention_observations": {
            "host_telemetry_max_samples_marker": (
                "MAX_SAMPLES" in safe_read(root / KNOWN_SOURCE["host_telemetry"])
                if source_state["host_telemetry"]["exists"] else False
            ),
            "share_bundle_timestamped_output_marker": (
                "debug_bundles" in bundle_text and "stamp" in bundle_text
            ),
            "runtime_family_file_counts_available": True,
            "directory_retention_policy_not_inferred_from_counts_alone": True,
        },
        "recommended_next_step": next_step,
    }

def format_text(report: dict[str, Any]) -> str:
    lines = [
        "PrivyHub Phase B1.1 existing diagnostics inventory",
        f"Classification: {report['classification']}",
        f"Schema: {report['schema']}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
        "=== CHECKPOINT ===",
        f"Git HEAD: {report['git_head']}",
        f"Tracked files scanned: {report['tracked_file_count']}",
        "",
        "=== EXISTING DEBUG HARNESS ===",
        "Harness modes: " + (", ".join(report["harness"]["modes"]) or "<none>"),
    ]

    privacy = report["harness"]["privacy"]
    for key in (
        "ipv4_redaction",
        "ipv6_candidate_redaction",
        "mac_redaction",
        "raw_pktmon_exclusion",
        "share_me_bundle",
    ):
        lines.append(f"{key}: {privacy[key]}")

    lines += ["", "=== KNOWN DIAGNOSTIC PRODUCERS / CONSUMERS ==="]
    for label, entry in report["known_source"].items():
        digest = entry["sha256"][:16] if entry["sha256"] else "<none>"
        lines.append(
            f"{label}: exists={entry['exists']} bytes={entry['bytes']} sha256={digest}"
        )

    lines += [
        "",
        "=== STRUCTURED SCHEMAS ===",
        f"Schema identifiers found: {len(report['structured_schema_ids'])}",
    ]
    for value in report["structured_schema_ids"]:
        lines.append(f"  {value}")

    lines += ["", "=== COMMON EVENT / HEALTH CONTRACT ==="]
    for field, paths in report["common_field_coverage"].items():
        lines.append(f"{field}: {len(paths)} diagnostic source file(s)")
    lines.append(
        "Common subsystem+severity+event_code+health contract detected: "
        + str(report["common_event_health_contract_detected"])
    )
    lines.append(
        "Health aggregator path candidates: "
        + str(len(report["health_aggregator_candidates"]))
    )

    lines += [
        "",
        "=== ANDROID DIAGNOSTIC SURFACE ===",
        f"Diagnostic activity count: {report['android']['diagnostic_activity_count']}",
        "Unified GUI diagnostics detected: " + str(report["android"]["unified_gui_detected"]),
        "Native stream metric tokens: "
        + (", ".join(report["android"]["native_stream_metric_tokens"]) or "<none>"),
    ]
    for rel in report["android"]["diagnostic_activities"]:
        lines.append(f"  diagnostic activity: {rel}")

    lines += ["", "=== LOCAL DIAGNOSTIC ARTIFACT FAMILIES ==="]
    for item in report["runtime_families"]:
        newest = (
            "<none>"
            if item["newest_age_seconds"] is None
            else f"{item['newest_age_seconds']:.1f}s"
        )
        shape = item.get("newest_json_shape")
        schema = shape.get("schema", "") if isinstance(shape, dict) else ""
        top_keys = len(shape.get("top_level_keys", [])) if isinstance(shape, dict) else 0
        lines.append(
            f"{item['name']}: exists={item['exists']} files={item['file_count']} "
            f"bytes={item['total_bytes']} newest_age={newest} "
            f"json_schema={schema or '<none>'} top_keys={top_keys}"
        )

    lines += ["", "=== LIVE JSON STATE SHAPES ==="]
    for item in report["live_state"]:
        lines.append(
            f"{item['path']}: exists={item['exists']} json_files={len(item['json_files'])}"
        )
        for child in item["json_files"]:
            keys = child["shape"].get("top_level_keys", [])
            lines.append(
                f"  {child['name']}: bytes={child['bytes']} keys="
                + (",".join(keys) if keys else "<unparsed>")
            )

    lines += [
        "",
        "=== RETENTION / CONSOLIDATION ===",
        "Host telemetry bounded sample marker: "
        + str(report["retention_observations"]["host_telemetry_max_samples_marker"]),
        "Debug bundle timestamped-output marker: "
        + str(report["retention_observations"]["share_bundle_timestamped_output_marker"]),
        "Directory retention policy inferred from counts: False",
        "",
        "=== B1.2 DIRECTION ===",
        f"Recommended next step: {report['recommended_next_step']}",
        "",
        "Return this file for B1.2 architecture design.",
    ]
    return "\n".join(lines) + "\n"

def self_test() -> int:
    assert extract_harness_modes('[ValidateSet("GameSmear", "CollectLatest")]') == [
        "GameSmear",
        "CollectLatest",
    ]
    assert SCHEMA_ID_RE.findall('SCHEMA="privyhub_native_decoder_session_log_v1"') == [
        "privyhub_native_decoder_session_log_v1"
    ]

    with tempfile.TemporaryDirectory(prefix="b1_inventory_selftest_") as td:
        root = Path(td)
        d = root / "logs/test"
        d.mkdir(parents=True)
        private_value = ".".join(["192", "168", "5", "12"])
        p = d / "state.json"
        p.write_text(
            json.dumps({
                "schema": "privyhub_fixture_v1",
                "peer": private_value,
                "report": {"secret_value": "do-not-log", "packets": 10},
            }),
            encoding="utf-8",
        )
        shape = json_shape(p)
        encoded = json.dumps(shape)
        assert private_value not in encoded
        assert "do-not-log" not in encoded
        assert shape["schema"] == "privyhub_fixture_v1"
        assert shape["top_level_keys"] == ["peer", "report", "schema"]
        assert shape["nested_report_keys"] == ["packets", "secret_value"]
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        raise SystemExit("PrivyHub repository root not found")

    report = build_report(root)
    out_dir = root / "logs" / "diagnostics"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "b1_diagnostics_inventory.json"
    text_path = out_dir / "b1_diagnostics_inventory.txt"

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    text_path.write_text(
        format_text(report),
        encoding="utf-8",
        newline="\n",
    )

    print(CLASSIFICATION)
    print("Text:", text_path)
    print("JSON:", json_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
