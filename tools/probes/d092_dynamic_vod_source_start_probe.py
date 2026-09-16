#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "http://127.0.0.1:8765"
OUT_REL = Path("logs/d092_dynamic_vod_source_start_probe.txt")

def request_json(path: str, method: str = "GET") -> tuple[int | None, dict[str, Any] | None, str]:
    req = urllib.request.Request(BASE + path, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            body = response.read().decode("utf-8")
            obj = json.loads(body)
            return response.status, obj if isinstance(obj, dict) else None, ""
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, None, body
    except Exception as exc:
        return None, None, f"{type(exc).__name__}: {exc}"

def flatten(node: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if node.get("node_type") == "source":
            out.append(node)
        children = node.get("children")
        if isinstance(children, list):
            for child in children:
                out.extend(flatten(child))
    elif isinstance(node, list):
        for child in node:
            out.extend(flatten(child))
    return out

def self_test() -> int:
    sample = {"root": [{"node_type": "source", "id": "x", "name": "Aviator", "playback": {"path": "/vod/movies/Aviator.mp4"}}]}
    assert flatten(sample["root"])[0]["id"] == "x"
    print("SELF-TEST PASS")
    return 0

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/home/privyhub/Projects/onn-stream-test")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()

    repo = Path(args.root).resolve()
    out = repo / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "PrivyHub D-092 dynamic VOD source-start probe",
        f"Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}",
        "Production files modified by probe: NONE",
        "Network addresses collected/logged: NONE",
        "",
    ]
    classification = "D092_DYNAMIC_VOD_SOURCE_START_NOT_CONFIRMED"

    status, catalog, err = request_json("/sources")
    lines += [
        "=== CATALOG ===",
        f"GET /sources HTTP: {status if status is not None else '<error>'}",
        f"GET /sources error: {err or '<none>'}",
    ]
    target = None
    if status == 200 and catalog:
        for item in flatten(catalog.get("root", [])):
            playback = item.get("playback")
            if not isinstance(playback, dict):
                continue
            if playback.get("path") == "/vod/movies/Aviator.mp4":
                target = item
                break

    lines += [
        f"Aviator catalog source found: {target is not None}",
    ]

    if target is not None:
        source_id = str(target.get("id", ""))
        start_status, start_obj, start_err = request_json(
            f"/sources/{source_id}/start",
            method="POST",
        )
        ready = bool(start_obj and start_obj.get("ready"))
        lines += [
            "",
            "=== SOURCE START ===",
            f"POST source start HTTP: {start_status if start_status is not None else '<error>'}",
            f"POST source start ready: {ready}",
            f"POST source start error: {start_err or '<none>'}",
        ]
        if start_status == 200 and ready:
            classification = "D092_DYNAMIC_VOD_SOURCE_START_CONFIRMED"

    lines += [
        "",
        "=== RESULT ===",
        f"Classification: {classification}",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(classification)
    print("Log:", out)
    return 0 if classification.endswith("_CONFIRMED") else 1

if __name__ == "__main__":
    raise SystemExit(main())
