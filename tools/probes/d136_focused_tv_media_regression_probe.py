#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

D122_JSON = Path("logs/tv/d122_d5_tv_media_regression_probe.json")
D133_JSON = Path("logs/tv/d133_epg_status_accuracy_probe.json")
D135_JSON = Path("logs/tv/d135_tv_state_executor_isolation_probe.json")

JSON_REL = Path("logs/tv/d136_focused_tv_media_regression_probe.json")
TEXT_REL = Path("logs/tv/d136_focused_tv_media_regression_probe.txt")

D122_TARGET = "D122_D5_TV_MEDIA_AUTOMATED_REGRESSION_BASELINE_VALIDATED"
D133_TARGET = "D133_EPG_STATUS_ACCURACY_RUNTIME_VALIDATED"
D135_TARGET = "D135_FAVORITES_QUEUE_CONTENTION_REMOVED"
D136_TARGET = "D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_VALIDATED"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root is not an object: {path}")
    return payload


def classification(payload: dict[str, Any]) -> str:
    return str(payload.get("classification") or "")


def self_test() -> int:
    assert classification({"classification": D122_TARGET}) == D122_TARGET
    assert classification({"classification": D133_TARGET}) == D133_TARGET
    assert classification({"classification": D135_TARGET}) == D135_TARGET
    print("D136_PROBE_SELF_TEST_OK")
    return 0


def run_d122(repo: Path) -> tuple[int, str]:
    probe = repo / "tools/probes/d122_d5_tv_media_regression_probe.py"
    result = subprocess.run(
        [sys.executable, str(probe), "--repo", str(repo)],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=90,
    )
    return result.returncode, result.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    json_path = repo / JSON_REL
    text_path = repo / TEXT_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)

    d122_rc, d122_stdout = run_d122(repo)

    problems: list[str] = []

    if d122_rc != 0:
        problems.append(f"d122_probe_exit={d122_rc}")

    payloads: dict[str, dict[str, Any] | None] = {
        "d122": None,
        "d133": None,
        "d135": None,
    }

    for key, rel in (
        ("d122", D122_JSON),
        ("d133", D133_JSON),
        ("d135", D135_JSON),
    ):
        path = repo / rel
        if not path.is_file():
            problems.append(f"{key}_result_missing")
            continue
        try:
            payloads[key] = load_json(path)
        except Exception as exc:
            problems.append(f"{key}_result_invalid:{type(exc).__name__}")

    d122_class = classification(payloads["d122"] or {})
    d133_class = classification(payloads["d133"] or {})
    d135_class = classification(payloads["d135"] or {})

    if d122_class != D122_TARGET:
        problems.append(f"d122_classification={d122_class or 'missing'}")
    if d133_class != D133_TARGET:
        problems.append(f"d133_classification={d133_class or 'missing'}")
    if d135_class != D135_TARGET:
        problems.append(f"d135_classification={d135_class or 'missing'}")

    d135 = payloads["d135"] or {}
    if d135_class == D135_TARGET:
        if int(d135.get("favorites_queue_wait_ms") or 999999) > 1500:
            problems.append("d135_queue_wait_regressed")
        if int(d135.get("favorites_total_ms") or 999999) > 5000:
            problems.append("d135_favorites_total_regressed")
        if not bool(d135.get("state_sync_complete")):
            problems.append("d135_state_sync_not_complete")
        if not bool(d135.get("state_sync_reconciled")):
            problems.append("d135_state_sync_not_reconciled")

    d133 = payloads["d133"] or {}
    if d133_class == D133_TARGET:
        if not bool(d133.get("one_column_full_width")):
            problems.append("d133_one_column_regressed")
        if int(d133.get("mislabeled_gap_row_count") or 0) != 0:
            problems.append("d133_status_regressed")

    classification_out = (
        D136_TARGET
        if not problems
        else "D136_FOCUSED_TV_MEDIA_AUTOMATED_REGRESSION_FAILED"
    )

    report = {
        "classification": classification_out,
        "problems": problems,
        "d122_classification": d122_class,
        "d133_classification": d133_class,
        "d135_classification": d135_class,
        "d135_favorites_total_ms": d135.get("favorites_total_ms"),
        "d135_favorites_queue_wait_ms": d135.get("favorites_queue_wait_ms"),
        "d135_state_sync_complete": d135.get("state_sync_complete"),
        "d135_state_sync_reconciled": d135.get("state_sync_reconciled"),
        "d133_one_column_full_width": d133.get("one_column_full_width"),
        "d133_mislabeled_gap_row_count": d133.get("mislabeled_gap_row_count"),
        "d122_stdout_tail": d122_stdout[-4000:],
    }

    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "PrivyHub D-136 focused TV/media regression probe",
        f"Classification: {classification_out}",
        "",
        "AUTOMATED BASELINE",
        f"  d122: {d122_class or 'missing'}",
        f"  d133: {d133_class or 'missing'}",
        f"  d135: {d135_class or 'missing'}",
        "",
        "RECENT TV UX/PERFORMANCE",
        f"  favorites_total_ms: {d135.get('favorites_total_ms')}",
        f"  favorites_queue_wait_ms: {d135.get('favorites_queue_wait_ms')}",
        f"  state_sync_complete: {d135.get('state_sync_complete')}",
        f"  state_sync_reconciled: {d135.get('state_sync_reconciled')}",
        f"  one_column_full_width: {d133.get('one_column_full_width')}",
        f"  mislabeled_gap_row_count: {d133.get('mislabeled_gap_row_count')}",
        "",
        "PROBLEMS",
    ]

    if problems:
        lines.extend(f"  - {item}" for item in problems)
    else:
        lines.append("  none")

    lines.extend([
        "",
        "This automated probe does not prove visible/audio playback.",
        "Complete the short manual onn smoke test: Live TV playback, guide/navigation, VOD playback.",
        "No network address or device identifier is written to this report.",
        f"JSON: {json_path}",
        f"TEXT: {text_path}",
    ])

    text = "\n".join(lines) + "\n"
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
