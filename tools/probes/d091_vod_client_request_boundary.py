#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

EXPECTED_HEAD = "c7fe53a613d55f9d38b37b16609c590118465efd"
SERVER_LOG_REL = Path("logs/server.log")
OUT_REL = Path("logs/d5_vod_client_request_boundary.txt")
EXTENSIONS = {".mp4", ".m4v", ".mkv", ".webm", ".mov", ".ts", ".m2ts"}

ACCESS_RE = re.compile(
    r'"(?P<method>GET|HEAD)\s+(?P<path>\S+)\s+HTTP/\d(?:\.\d)?"\s+'
    r'(?P<status>\d{3})'
)

def git_head(root: Path) -> str:
    p = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return p.stdout.strip() if p.returncode == 0 else ""

def find_symlink_fixture(repo: Path) -> tuple[Path, Path] | None:
    vod = repo / "media" / "vod"
    if not vod.is_dir():
        return None
    links: list[Path] = []
    for current, dirs, _files in os.walk(vod, followlinks=False):
        base = Path(current)
        for name in dirs:
            p = base / name
            try:
                if p.is_symlink() and p.is_dir():
                    links.append(p)
            except OSError:
                continue

    for link in sorted(links, key=lambda p: str(p).casefold()):
        try:
            target = link.resolve(strict=True)
        except OSError:
            continue
        for current, dirs, files in os.walk(target, followlinks=False):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in sorted(files, key=str.casefold):
                if name.startswith("."):
                    continue
                p = Path(current) / name
                if p.suffix.casefold() not in EXTENSIONS:
                    continue
                rel = p.resolve(strict=True).relative_to(target)
                visible = link / rel
                return link, visible
    return None

def parse_events(text: str) -> list[tuple[str, str, int]]:
    events: list[tuple[str, str, int]] = []
    for raw in text.splitlines():
        match = ACCESS_RE.search(raw)
        if not match:
            continue
        encoded = match.group("path")
        path = urllib.parse.unquote(encoded.split("?", 1)[0])
        events.append(
            (
                match.group("method"),
                path,
                int(match.group("status")),
            )
        )
    return events

def self_test() -> int:
    sample = (
        'CLIENT - - [DATE] "GET /vod/movies/Aviator.mp4 HTTP/1.1" 206 -\n'
        'CLIENT - - [DATE] "HEAD /vod/x%20y.mkv HTTP/1.1" 200 -\n'
    )
    events = parse_events(sample)
    assert events == [
        ("GET", "/vod/movies/Aviator.mp4", 206),
        ("HEAD", "/vod/x y.mkv", 200),
    ]
    print("SELF-TEST PASS")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        default="/home/privyhub/Projects/onn-stream-test",
    )
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.root).resolve()
    out = repo / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    log = repo / SERVER_LOG_REL

    classification = "D5_VOD_ONN_REQUEST_BOUNDARY_INCONCLUSIVE"
    lines = [
        "PrivyHub D5 onn -> media-server VOD request boundary probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        f"Expected checkpoint: {EXPECTED_HEAD}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]

    try:
        head = git_head(repo)
        fixture = find_symlink_fixture(repo)
        lines += [
            "=== PRECHECK ===",
            f"Git HEAD: {head}",
            f"Git HEAD expected: {head == EXPECTED_HEAD}",
            f"Server access log exists: {log.is_file()}",
            f"Symlink VOD fixture available: {fixture is not None}",
        ]
        if head != EXPECTED_HEAD:
            raise RuntimeError("Git checkpoint mismatch")
        if not log.is_file():
            raise RuntimeError("logs/server.log is unavailable")
        if fixture is None:
            raise RuntimeError("No supported movie found beneath a VOD symlink")

        link, visible = fixture
        media_root = repo / "media"
        expected_path = "/" + visible.relative_to(media_root).as_posix()
        filename = visible.name

        start_size = log.stat().st_size

        print("")
        print("D5 VOD CLIENT REQUEST BOUNDARY")
        print(f"On the onn, attempt to play this exact movie: {filename}")
        print("Wait until playback either begins or shows its playback error.")
        input("Then press Enter here: ")

        time.sleep(1.0)

        with log.open("rb") as handle:
            handle.seek(start_size)
            appended = handle.read().decode("utf-8", errors="replace")

        events = parse_events(appended)
        matching = [e for e in events if e[1] == expected_path]
        vod_events = [e for e in events if e[1].startswith("/vod/")]

        lines += [
            "",
            "=== TARGET ===",
            f"Selected movie filename: {filename}",
            f"Expected media URL path: {expected_path}",
            f"New parsed HTTP access events: {len(events)}",
            f"New VOD access events: {len(vod_events)}",
            f"Exact target access events: {len(matching)}",
            "",
            "=== SANITIZED NEW VOD EVENTS ===",
        ]

        if vod_events:
            for method, path, status in vod_events:
                lines.append(f"{method} {path} -> {status}")
        else:
            lines.append("<none>")

        statuses = [status for _m, _p, status in matching]

        if matching and any(status in {200, 206} for status in statuses):
            classification = "D5_VOD_ONN_REACHES_MEDIA_SERVER"
        elif matching:
            classification = "D5_VOD_ONN_MEDIA_SERVER_HTTP_ERROR"
        elif vod_events:
            classification = "D5_VOD_ONN_DIFFERENT_PATH_REQUEST"
        else:
            classification = "D5_VOD_ONN_NO_MEDIA_REQUEST"

    except Exception as exc:
        lines += [
            "",
            "=== PROBE NOTE ===",
            f"{type(exc).__name__}: {exc}",
        ]

    lines += [
        "",
        "=== RESULT ===",
        f"Classification: {classification}",
        "",
        "Interpretation:",
        "- REACHES_MEDIA_SERVER: onn requested the exact movie and received HTTP 200/206;",
        "  next boundary is Android Media3/container/codec playback diagnostics.",
        "- MEDIA_SERVER_HTTP_ERROR: exact request arrived but HTTP serving failed.",
        "- DIFFERENT_PATH_REQUEST: onn requested VOD, but not the selected catalog path.",
        "- NO_MEDIA_REQUEST: playback failed before any VOD request reached port 8000.",
    ]

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("")
    print(classification)
    print("Log:", out)
    return 0 if classification != "D5_VOD_ONN_REQUEST_BOUNDARY_INCONCLUSIVE" else 1

if __name__ == "__main__":
    raise SystemExit(main())
