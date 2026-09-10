#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
MAC_RE = re.compile(r"(?i)(?<![0-9a-f])(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
IPV6_CANDIDATE_RE = re.compile(r"(?i)(?<![0-9a-f:])(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(?![0-9a-f:])")

TEXT_SUFFIXES = {".txt", ".json", ".log", ".csv", ".md", ".cfg"}

GAME_FIXED = (
    "logs/games/latest_game_diagnostic_bundle.txt",
    "logs/games/save_state_probe.txt",
    "logs/games/retroarch_control_probe.txt",
    "logs/games/native_video_alpha.log",
)

LATEST_DIRS = (
    ("logs/games/decoder_sessions", "native_decoder_*.json", 2),
    ("logs/games/host_telemetry", "*.json", 2),
    ("logs/games/audio_timing", "*.json", 2),
    ("logs/games/capture_diagnostics", "*", 4),
)

TRANSPORT_DIRS = (
    "logs/transport_probe",
    "logs/transport_reverse",
    "logs/transport_loopback",
)

SAFE_TRANSPORT_NAMES = {
    "combined_summary.txt",
    "combined_summary.json",
    "host_summary.json",
    "android_summary.json",
    "pktmon_presence_summary.txt",
    "pktmon_presence_summary.json",
    "pktmon_stats.txt",
    "loopback_summary.txt",
    "loopback_summary.json",
}

EXCLUDED_RAW_NAMES = {
    "pktmon_full.txt",
    "pktmon.etl",
    "host_packets.csv",
    "android_packets.csv",
    "loopback_packets.csv",
    "loopback_sender.csv",
}

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def redact(text: str) -> str:
    text = IPV4_RE.sub("<IP_REDACTED>", text)
    text = MAC_RE.sub("<MAC_REDACTED>", text)

    # Conservative IPv6-like redaction. Avoid replacing timestamps and ordinary
    # colon-delimited prose by requiring at least two colons and a hex-like token.
    def _ipv6(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.count(":") < 2:
            return token
        if not any(ch.isalpha() for ch in token):
            return token
        return "<IPV6_REDACTED>"

    return IPV6_CANDIDATE_RE.sub(_ipv6, text)

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")

def latest_files(directory: Path, pattern: str, limit: int) -> list[Path]:
    if not directory.is_dir():
        return []
    files = [p for p in directory.glob(pattern) if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    return files[:limit]

def newest_session_dir(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime_ns)

def parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def is_since(path: Path, since: datetime | None) -> bool:
    if since is None:
        return True
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return False
    # Allow a small filesystem/timestamp skew window.
    return mtime >= since.replace(microsecond=0)

def unique_existing(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        try:
            key = str(p.resolve())
        except OSError:
            key = str(p)
        if key in seen or not p.is_file():
            continue
        seen.add(key)
        out.append(p)
    return out

def gather_game(root: Path, since: datetime | None, latest_mode: bool) -> list[Path]:
    selected: list[Path] = []
    for rel in GAME_FIXED:
        p = root / rel
        if p.is_file() and (latest_mode or is_since(p, since)):
            selected.append(p)

    for rel_dir, pattern, limit in LATEST_DIRS:
        directory = root / rel_dir
        for p in latest_files(directory, pattern, limit):
            if latest_mode or is_since(p, since):
                selected.append(p)

    # The fixed collector embeds the latest verbose RetroArch session log, but
    # include a recent standalone game log too when one exists.
    game_logs = [
        p for p in (root / "logs" / "games").glob("*.log")
        if p.is_file() and p.name != "native_video_alpha.log"
    ]
    game_logs.sort(key=lambda p: p.stat().st_mtime_ns, reverse=True)
    for p in game_logs[:1]:
        if latest_mode or is_since(p, since):
            selected.append(p)

    return unique_existing(selected)

def gather_transport(root: Path) -> list[Path]:
    selected: list[Path] = []
    for rel in TRANSPORT_DIRS:
        session = newest_session_dir(root / rel)
        if session is None:
            continue
        for name in SAFE_TRANSPORT_NAMES:
            p = session / name
            if p.is_file():
                selected.append(p)
    return unique_existing(selected)

def flatten_numbers(obj: Any, prefix: str = "") -> dict[str, float]:
    result: dict[str, float] = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten_numbers(value, child))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            child = f"{prefix}[{i}]"
            result.update(flatten_numbers(value, child))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        result[prefix] = float(obj)
    return result

def choose_metric(flat: dict[str, float], needles: tuple[str, ...]) -> tuple[str, float] | None:
    candidates: list[tuple[int, str, float]] = []
    for path, value in flat.items():
        folded = path.casefold()
        if all(n.casefold() in folded for n in needles):
            candidates.append((len(path), path, value))
    if not candidates:
        return None
    candidates.sort()
    _, path, value = candidates[0]
    return path, value

def classify_decoder(paths: list[Path]) -> list[str]:
    decoder = next((p for p in paths if "decoder_sessions" in p.as_posix() and p.suffix.lower() == ".json"), None)
    if decoder is None:
        return ["Decoder classification: no decoder-session JSON selected."]

    try:
        data = json.loads(read_text(decoder))
    except Exception as exc:
        return [f"Decoder classification: could not parse {decoder.name}: {exc}"]

    flat = flatten_numbers(data)
    wanted = {
        "received": (("received",),),
        "lost": (("lost",),),
        "frames_dropped": (("frames", "dropped"), ("dropped", "frames")),
        "sequence_gap_au_drops": (("sequence", "gap", "drop"),),
        "incomplete_au_drops": (("incomplete", "drop"),),
        "fec_unrecoverable_groups": (("unrecoverable", "group"),),
        "rendered": (("rendered",),),
        "stale": (("stale",),),
    }

    metrics: dict[str, tuple[str, float]] = {}
    for label, alternatives in wanted.items():
        for needles in alternatives:
            hit = choose_metric(flat, needles)
            if hit is not None:
                metrics[label] = hit
                break

    lines = [f"Decoder source: {decoder.name}"]
    for label in (
        "received", "lost", "frames_dropped", "sequence_gap_au_drops",
        "incomplete_au_drops", "fec_unrecoverable_groups", "rendered", "stale"
    ):
        if label in metrics:
            lines.append(f"  {label}: {metrics[label][1]:g}  [{metrics[label][0]}]")

    damaged = sum(
        metrics[label][1]
        for label in ("lost", "sequence_gap_au_drops", "incomplete_au_drops", "fec_unrecoverable_groups")
        if label in metrics
    )
    if damaged > 0:
        lines.append("Decoder classifier: TRANSPORT/DAMAGED-AU EVIDENCE PRESENT")
    else:
        lines.append("Decoder classifier: no obvious transport/damaged-AU counter found above zero")
    return lines

def classify_transport(paths: list[Path]) -> list[str]:
    json_candidates = [
        p for p in paths
        if p.suffix.lower() == ".json" and (
            p.name in {"combined_summary.json", "host_summary.json", "loopback_summary.json"}
        )
    ]
    lines: list[str] = []
    for p in json_candidates:
        try:
            data = json.loads(read_text(p))
        except Exception:
            continue
        flat = flatten_numbers(data)
        missing = choose_metric(flat, ("missing",))
        duplicates = choose_metric(flat, ("duplicate",))
        ge20 = choose_metric(flat, ("ge_20",))
        if ge20 is None:
            ge20 = choose_metric(flat, ("20",))
        if missing or duplicates or ge20:
            lines.append(f"Transport source: {p.parent.name}/{p.name}")
            if missing:
                lines.append(f"  missing-like metric: {missing[1]:g}  [{missing[0]}]")
            if duplicates:
                lines.append(f"  duplicate-like metric: {duplicates[1]:g}  [{duplicates[0]}]")
            if ge20:
                lines.append(f"  gap-like metric: {ge20[1]:g}  [{ge20[0]}]")
    if not lines:
        lines.append("Transport classification: no parseable summary metrics found.")
    return lines

def write_redacted_copy(src: Path, root: Path, evidence_dir: Path) -> Path:
    rel = src.relative_to(root)
    dst = evidence_dir / rel
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.name in EXCLUDED_RAW_NAMES:
        raise ValueError(f"refusing excluded raw diagnostic: {src}")

    if src.suffix.lower() in TEXT_SUFFIXES:
        dst.write_text(redact(read_text(src)), encoding="utf-8", newline="\n")
    else:
        # The current harness intentionally selects only textual evidence.
        raise ValueError(f"refusing non-text evidence: {src}")
    return dst

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", required=True, choices=("game-smear", "latest", "transport-history"))
    parser.add_argument("--since-utc", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    since = parse_since(args.since_utc)
    stamp = utc_now().strftime("%Y%m%d_%H%M%S")
    out_dir = root / "logs" / "debug_bundles" / f"{stamp}_{args.mode.replace('-', '_')}"
    evidence_dir = out_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=False)

    if args.mode == "game-smear":
        sources = gather_game(root, since, latest_mode=False)
        # If timestamp scoping finds nothing, include latest evidence but mark it.
        fallback = False
        if not sources:
            sources = gather_game(root, None, latest_mode=True)
            fallback = True
    elif args.mode == "latest":
        sources = gather_game(root, None, latest_mode=True)
        fallback = False
    else:
        sources = gather_transport(root)
        fallback = False

    copied: list[tuple[Path, Path]] = []
    for src in sources:
        try:
            dst = write_redacted_copy(src, root, evidence_dir)
        except ValueError:
            continue
        copied.append((src, dst))

    summary_lines = [
        "PrivyHub SHARE_ME diagnostic bundle",
        f"Generated UTC: {iso(utc_now())}",
        f"Mode: {args.mode}",
        "Project root: <ROOT>",
        "",
        "PRIVACY",
        "- IP-like and MAC-like addresses are redacted from bundled text/JSON.",
        "- Raw pktmon_full.txt and pktmon.etl are intentionally excluded.",
        "- Do not add raw network captures to this ZIP before sharing.",
        "",
        "ARCHITECTURE RULE",
        "- Normal PrivyHub game streaming does not require a hard-coded onn address.",
        "- Android stores the companion host; the companion learns the onn/client address",
        "  from the live HTTP request and passes that client address into native streaming.",
        "- Standalone lab probes that require an explicit address are exceptions, not the",
        "  production endpoint-resolution model.",
        "",
    ]

    if fallback:
        summary_lines += [
            "WARNING",
            "- No files changed after the GameSmear start timestamp; latest available game",
            "  evidence was bundled instead. Re-run GameSmear if a fresh reproduction is needed.",
            "",
        ]

    if args.mode in ("game-smear", "latest"):
        summary_lines += ["CLASSIFIER"] + classify_decoder([src for src, _ in copied]) + [""]
    if args.mode == "transport-history":
        summary_lines += ["CLASSIFIER"] + classify_transport([src for src, _ in copied]) + [""]

    summary_lines += [
        "BUNDLED SOURCE FILES",
    ]
    if copied:
        for src, dst in copied:
            rel = src.relative_to(root).as_posix()
            summary_lines.append(f"- {rel}")
    else:
        summary_lines.append("- [none found]")

    summary_lines += [
        "",
        "SHARING INSTRUCTION",
        "- Share only SHARE_ME.zip with ChatGPT for this run.",
        "- The ZIP already contains this summary plus the selected redacted evidence.",
        "",
    ]

    summary_path = out_dir / "SHARE_ME.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8", newline="\n")

    manifest = {
        "schema": 1,
        "generated_utc": iso(utc_now()),
        "mode": args.mode,
        "files": [],
    }
    for _, dst in copied:
        manifest["files"].append({
            "path": dst.relative_to(out_dir).as_posix(),
            "sha256": sha256_file(dst),
            "size_bytes": dst.stat().st_size,
        })
    manifest["files"].append({
        "path": "SHARE_ME.txt",
        "sha256": sha256_file(summary_path),
        "size_bytes": summary_path.stat().st_size,
    })
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

    zip_path = out_dir / "SHARE_ME.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(summary_path, "SHARE_ME.txt")
        zf.write(manifest_path, "manifest.json")
        for _, dst in copied:
            zf.write(dst, dst.relative_to(out_dir).as_posix())

    # Validate our own deliverable before telling the user to share it.
    with zipfile.ZipFile(zip_path, "r") as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"ZIP integrity validation failed at {bad}")
        names = set(zf.namelist())
        if "SHARE_ME.txt" not in names or "manifest.json" not in names:
            raise RuntimeError("ZIP validation failed: required files missing")
        if any(name.endswith("pktmon_full.txt") or name.endswith("pktmon.etl") for name in names):
            raise RuntimeError("ZIP validation failed: raw PktMon artifact included")

    print("")
    print("DIAGNOSTIC BUNDLE CREATED")
    print("")
    print("SHARE THIS ONE FILE WITH CHATGPT:")
    print(zip_path)
    print("")
    print("Do not send raw pktmon_full.txt, pktmon.etl, or network addresses.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
