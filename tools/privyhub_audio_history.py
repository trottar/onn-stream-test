#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
MAC_RE = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
IPV6_CANDIDATE_RE = re.compile(
    r"(?i)(?<![0-9a-f:])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![0-9a-f:])"
)
STAMP_RE = re.compile(r"(\d{8})_(\d{6})")

LOW_BASELINE_MAX = 0.02
A4_RESIDUE_MIN = 0.0075
A4_RESIDUE_MAX = 0.0125

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def redact(text: str) -> str:
    text = IPV4_RE.sub("<IP_REDACTED>", text)
    text = MAC_RE.sub("<MAC_REDACTED>", text)

    def ipv6_replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.count(":") < 2:
            return token
        if not any(ch.isalpha() for ch in token):
            return token
        return "<IPV6_REDACTED>"

    return IPV6_CANDIDATE_RE.sub(ipv6_replace, text)

def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8-sig",
                errors="replace",
            )
        )
    except (OSError, json.JSONDecodeError):
        return None

    return payload if isinstance(payload, dict) else None

def nested(
    payload: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
    return current

def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None

def integer(value: Any) -> int | None:
    n = number(value)
    return int(n) if n is not None else None

def bool_value(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None

def volumes(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    result: list[float] = []
    for item in value:
        n = number(item)
        if n is not None:
            result.append(n)
    return result

def timestamp_for(path: Path) -> datetime:
    match = STAMP_RE.search(path.stem)
    if match:
        try:
            local_naive = datetime.strptime(
                "".join(match.groups()),
                "%Y%m%d%H%M%S",
            )
            # Filenames are host-local wall-clock stamps. We do not assume
            # timezone here; this value is only used to sort retained logs.
            return local_naive.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=timezone.utc,
    )

def summarize(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    if payload is None:
        return {
            "file": path.name,
            "parse_ok": False,
            "sort_timestamp": iso(timestamp_for(path)),
        }

    original = volumes(
        nested(
            payload,
            "local_output",
            "original_volumes",
            default=[],
        )
    )
    original_mutes_raw = nested(
        payload,
        "local_output",
        "original_mutes",
        default=[],
    )
    original_mutes = (
        [bool(x) for x in original_mutes_raw]
        if isinstance(original_mutes_raw, list)
        else []
    )

    minimum = min(original) if original else None
    maximum = max(original) if original else None
    low = bool(
        original
        and minimum is not None
        and minimum <= LOW_BASELINE_MAX
    )
    residue_like = bool(
        original
        and all(
            A4_RESIDUE_MIN <= value <= A4_RESIDUE_MAX
            for value in original
        )
    )

    return {
        "file": path.name,
        "parse_ok": True,
        "sort_timestamp": iso(timestamp_for(path)),
        "probe_version": str(payload.get("probe_version", "")),
        "ready": bool_value(payload.get("ready")),
        "final": bool_value(payload.get("final")),
        "error": str(payload.get("error", "") or ""),
        "duration_ms": number(payload.get("duration_ms")),
        "original_volumes": original,
        "original_mutes": original_mutes,
        "minimum_original_volume": minimum,
        "maximum_original_volume": maximum,
        "low_baseline": low,
        "a4_residue_like_baseline": residue_like,
        "suppression_factor": number(
            nested(
                payload,
                "local_output",
                "factor",
            )
        ),
        "digital_compensation": number(
            nested(
                payload,
                "local_output",
                "compensation",
            )
        ),
        "suppression_applied": bool_value(
            nested(
                payload,
                "local_output",
                "applied",
            )
        ),
        "suppression_restored": bool_value(
            nested(
                payload,
                "local_output",
                "restored",
            )
        ),
        "compensated_peak_absolute": number(
            nested(
                payload,
                "callback",
                "compensated_peak_absolute",
            )
        ),
        "packets_sent": integer(
            nested(
                payload,
                "send",
                "packets",
            )
        ),
        "send_errors": integer(
            nested(
                payload,
                "send",
                "errors",
            )
        ),
    }

def classify(history: list[dict[str, Any]]) -> dict[str, Any]:
    parsed = [
        item
        for item in history
        if item.get("parse_ok")
    ]

    if not parsed:
        return {
            "classification": "INSUFFICIENT_HISTORY",
            "reason": "No parseable audio timing JSON files were found.",
        }

    with_volume = [
        item
        for item in parsed
        if item.get("original_volumes")
    ]

    if not with_volume:
        return {
            "classification": "INSUFFICIENT_HISTORY",
            "reason": (
                "Audio timing logs exist, but none expose "
                "local_output.original_volumes."
            ),
        }

    low_indexes = [
        index
        for index, item in enumerate(with_volume)
        if item.get("low_baseline")
    ]

    if not low_indexes:
        return {
            "classification": "NO_LOW_BASELINE_FOUND",
            "reason": (
                f"No retained audio timing log started at or below "
                f"{LOW_BASELINE_MAX:.3f} session volume."
            ),
            "earliest": with_volume[0],
            "latest": with_volume[-1],
        }

    first_low_index = low_indexes[0]
    first_low = with_volume[first_low_index]
    previous = (
        with_volume[first_low_index - 1]
        if first_low_index > 0
        else None
    )

    if previous is None:
        cause = {
            "assessment": "CAUSE_NOT_LOCALIZED",
            "evidence": (
                "The earliest retained log already has a low baseline, "
                "so the transition predates retained audio timing history."
            ),
        }
        classification = "LOW_BASELINE_FROM_EARLIEST_RETAINED_LOG"
    else:
        classification = "LOW_BASELINE_TRANSITION_FOUND"

        previous_restored = previous.get(
            "suppression_restored"
        )
        previous_final = previous.get(
            "final"
        )
        previous_error = str(
            previous.get(
                "error",
                "",
            )
            or ""
        ).strip()

        if (
            previous_restored is False
            or previous_final is False
            or previous_error
        ):
            cause = {
                "assessment": "PRECEDING_ABNORMAL_STOP_SUPPORTED",
                "evidence": (
                    "The immediately preceding retained audio session "
                    "does not show a clean final/restored state."
                ),
            }
        elif (
            previous_restored is True
            and previous_final is True
            and not previous_error
        ):
            cause = {
                "assessment": "PRECEDING_HELPER_RESTORED_CLEANLY",
                "evidence": (
                    "The immediately preceding retained audio session "
                    "reports final=true, restored=true, and no error. "
                    "That log does not support a failed helper restore "
                    "as the transition cause."
                ),
            }
        else:
            cause = {
                "assessment": "PRECEDING_STOP_STATE_INDETERMINATE",
                "evidence": (
                    "The immediately preceding retained audio session "
                    "does not contain enough final/restored information "
                    "to classify its shutdown."
                ),
            }

    return {
        "classification": classification,
        "thresholds": {
            "low_baseline_max": LOW_BASELINE_MAX,
            "a4_residue_like_min": A4_RESIDUE_MIN,
            "a4_residue_like_max": A4_RESIDUE_MAX,
        },
        "first_low": first_low,
        "previous": previous,
        "cause_assessment": cause,
        "earliest": with_volume[0],
        "latest": with_volume[-1],
    }

def select_evidence(
    timing_dir: Path,
    history: list[dict[str, Any]],
    classification: dict[str, Any],
) -> list[Path]:
    wanted: list[str] = []

    first_low = classification.get("first_low")
    previous = classification.get("previous")

    if isinstance(previous, dict):
        wanted.append(str(previous.get("file", "")))
    if isinstance(first_low, dict):
        wanted.append(str(first_low.get("file", "")))

        try:
            idx = next(
                i
                for i, item in enumerate(history)
                if item.get("file") == first_low.get("file")
            )
        except StopIteration:
            idx = -1

        if idx >= 0:
            for candidate in history[
                max(0, idx - 2):
                min(len(history), idx + 3)
            ]:
                wanted.append(
                    str(candidate.get("file", ""))
                )

    if history:
        wanted.append(
            str(history[-1].get("file", ""))
        )

    selected: list[Path] = []
    seen: set[str] = set()
    for name in wanted:
        if not name or name in seen:
            continue
        seen.add(name)
        path = timing_dir / name
        if path.is_file():
            selected.append(path)
    return selected

def write_redacted_json_copy(
    src: Path,
    dst: Path,
) -> None:
    text = src.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )
    dst.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    dst.write_text(
        redact(text),
        encoding="utf-8",
        newline="\n",
    )

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    timing_dir = (
        root
        / "logs"
        / "games"
        / "audio_timing"
    )

    if not timing_dir.is_dir():
        raise SystemExit(
            "Audio timing log directory does not exist: "
            + str(timing_dir)
        )

    paths = sorted(
        [
            path
            for path in timing_dir.glob("*.json")
            if path.is_file()
        ],
        key=lambda path: (
            timestamp_for(path),
            path.name,
        ),
    )

    history = [
        summarize(path)
        for path in paths
    ]
    classification = classify(
        history
    )

    stamp = now_utc().strftime(
        "%Y%m%d_%H%M%S"
    )
    bundle_dir = (
        root
        / "logs"
        / "debug_bundles"
        / f"{stamp}_audio_history"
    )
    evidence_dir = (
        bundle_dir
        / "evidence"
        / "audio_timing"
    )
    evidence_dir.mkdir(
        parents=True,
        exist_ok=False,
    )

    history_path = (
        bundle_dir
        / "audio_baseline_history.json"
    )
    history_payload = {
        "schema": 1,
        "generated_utc": iso(now_utc()),
        "retained_audio_timing_files": len(history),
        "classification": classification,
        "history": history,
    }
    history_path.write_text(
        json.dumps(
            history_payload,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    selected = select_evidence(
        timing_dir,
        history,
        classification,
    )
    evidence_files: list[Path] = []
    for src in selected:
        dst = (
            evidence_dir
            / src.name
        )
        write_redacted_json_copy(
            src,
            dst,
        )
        evidence_files.append(
            dst
        )

    summary_lines = [
        "PrivyHub audio baseline history diagnostic",
        f"Generated UTC: {iso(now_utc())}",
        "",
        "QUESTION",
        "When did RetroArch's pre-suppression Windows audio-session volume first become low,",
        "and does the immediately preceding retained helper log support an abnormal stop?",
        "",
        "RESULT",
        f"Classification: {classification.get('classification', 'UNKNOWN')}",
    ]

    first_low = classification.get(
        "first_low"
    )
    previous = classification.get(
        "previous"
    )
    cause = classification.get(
        "cause_assessment"
    )

    if isinstance(first_low, dict):
        summary_lines.extend(
            [
                (
                    "First low-baseline log: "
                    + str(first_low.get("file", ""))
                ),
                (
                    "First low original volumes: "
                    + json.dumps(
                        first_low.get(
                            "original_volumes",
                            [],
                        )
                    )
                ),
                (
                    "First low A4-residue-like: "
                    + str(
                        bool(
                            first_low.get(
                                "a4_residue_like_baseline"
                            )
                        )
                    )
                ),
            ]
        )

    if isinstance(previous, dict):
        summary_lines.extend(
            [
                (
                    "Immediately preceding log: "
                    + str(previous.get("file", ""))
                ),
                (
                    "Previous original volumes: "
                    + json.dumps(
                        previous.get(
                            "original_volumes",
                            [],
                        )
                    )
                ),
                (
                    "Previous final: "
                    + str(previous.get("final"))
                ),
                (
                    "Previous suppression restored: "
                    + str(
                        previous.get(
                            "suppression_restored"
                        )
                    )
                ),
                (
                    "Previous error: "
                    + (
                        str(previous.get("error", "")).strip()
                        or "<none>"
                    )
                ),
            ]
        )

    if isinstance(cause, dict):
        summary_lines.extend(
            [
                "",
                (
                    "Cause assessment: "
                    + str(
                        cause.get(
                            "assessment",
                            "",
                        )
                    )
                ),
                (
                    "Evidence: "
                    + str(
                        cause.get(
                            "evidence",
                            "",
                        )
                    )
                ),
            ]
        )

    summary_lines.extend(
        [
            "",
            "INTERPRETATION RULES",
            "- This diagnostic does not assume that a 1% baseline was caused by PrivyHub.",
            "- final=true + restored=true in the preceding log argues against that helper run",
            "  having failed to restore its own temporary attenuation.",
            "- final/restored failure supports, but does not by itself prove, an abnormal-stop cause.",
            "- If the earliest retained log is already low, the transition predates retained history.",
            "",
            "PRIVACY",
            "- SHARE_ME.zip contains only extracted safe metrics plus a few redacted JSON logs",
            "  around the transition.",
            "- Network addresses are redacted.",
            "",
            "SHARING INSTRUCTION",
            "- Share only SHARE_ME.zip with ChatGPT.",
        ]
    )

    summary_path = (
        bundle_dir
        / "SHARE_ME.txt"
    )
    summary_path.write_text(
        "\n".join(summary_lines)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest = {
        "schema": 1,
        "files": [],
    }

    for path in [
        summary_path,
        history_path,
        *evidence_files,
    ]:
        manifest["files"].append(
            {
                "path": path.relative_to(
                    bundle_dir
                ).as_posix(),
                "sha256": sha256_file(
                    path
                ),
                "size_bytes": path.stat().st_size,
            }
        )

    manifest_path = (
        bundle_dir
        / "manifest.json"
    )
    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    zip_path = (
        bundle_dir
        / "SHARE_ME.zip"
    )
    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zf:
        zf.write(
            summary_path,
            "SHARE_ME.txt",
        )
        zf.write(
            history_path,
            "audio_baseline_history.json",
        )
        zf.write(
            manifest_path,
            "manifest.json",
        )
        for path in evidence_files:
            zf.write(
                path,
                path.relative_to(
                    bundle_dir
                ).as_posix(),
            )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(
                f"Generated SHARE_ME.zip failed integrity at {bad}"
            )

        texts = []
        for name in zf.namelist():
            if name.endswith(
                (
                    ".txt",
                    ".json",
                )
            ):
                texts.append(
                    zf.read(
                        name
                    ).decode(
                        "utf-8",
                        errors="replace",
                    )
                )

        joined = "\n".join(
            texts
        )
        if IPV4_RE.search(
            joined
        ):
            raise RuntimeError(
                "Privacy validation failed: IPv4-like address remains in bundle"
            )
        if MAC_RE.search(
            joined
        ):
            raise RuntimeError(
                "Privacy validation failed: MAC-like address remains in bundle"
            )

    print("")
    print("AUDIO HISTORY DIAGNOSTIC COMPLETE")
    print(
        "Classification: "
        + str(
            classification.get(
                "classification",
                "UNKNOWN",
            )
        )
    )
    if isinstance(cause, dict):
        print(
            "Cause assessment: "
            + str(
                cause.get(
                    "assessment",
                    "UNKNOWN",
                )
            )
        )
    print("")
    print("SHARE THIS ONE FILE WITH CHATGPT:")
    print(zip_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
