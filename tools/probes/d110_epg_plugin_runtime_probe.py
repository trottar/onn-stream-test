#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import platform
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any


CONTROL_PORT = 8765
STATUS_PATH = "/plugins/epg/status"
BOOTSTRAP_PATH = "/plugins/epg/bootstrap"

CHANNELS = (
    "10Bold.au@Sydney",
    "5Cops.us@UK",
)

HTTP_TIMEOUT_SECONDS = 20
BOOTSTRAP_TIMEOUT_SECONDS = 900
REFRESH_TIMEOUT_SECONDS = 150


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def load_epg_module(repo: Path):
    path = repo / "companion" / "plugins" / "epg.py"
    if not path.is_file():
        raise RuntimeError("D-110 EPG plugin source is missing")
    spec = importlib.util.spec_from_file_location("privyhub_d110_epg", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("D-110 EPG plugin could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_json(
    path: str,
    *,
    method: str = "GET",
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, Any], float]:
    url = f"http://127.0.0.1:{CONTROL_PORT}{path}"
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "User-Agent": "PrivyHub-D110-Probe/1.0",
            "Cache-Control": "no-cache",
        },
    )
    started = time.monotonic()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200))
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return 0, {
            "ok": False,
            "error_class": exc.__class__.__name__,
        }, round(time.monotonic() - started, 3)

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "error": "response_not_json",
        }

    if not isinstance(payload, dict):
        payload = {
            "ok": False,
            "error": "response_not_object",
        }

    return status, payload, round(time.monotonic() - started, 3)


def classify(report: dict[str, Any]) -> str:
    status_http = report.get("initial_status_http")
    if status_http != 200:
        return "D110_COMPANION_RESTART_OR_EPG_PLUGIN_REQUIRED"

    initial = report.get("initial_status", {})
    if initial.get("schema") != "privyhub_epg_status_v1":
        return "D110_EPG_STATUS_SCHEMA_INVALID"

    bootstrap = report.get("bootstrap", {})
    if bootstrap.get("attempted") and not bootstrap.get("ok"):
        return "D110_EPG_BOOTSTRAP_FAILED"

    final_status = report.get("final_status", {})
    if not final_status.get("ready"):
        return "D110_EPG_TOOLCHAIN_NOT_READY"

    refreshes = report.get("refreshes", [])
    successful = [
        item
        for item in refreshes
        if item.get("http") == 200
        and item.get("payload", {}).get("ok")
        and int(item.get("payload", {}).get("programme_count") or 0) > 0
    ]

    if len(successful) < 2:
        return "D110_EPG_GUIDE_REFRESH_PARTIAL"

    cache = report.get("cache_recheck", {})
    if not (
        cache.get("http") == 200
        and cache.get("payload", {}).get("cached") is True
        and int(cache.get("payload", {}).get("programme_count") or 0) > 0
    ):
        return "D110_EPG_CACHE_CONTRACT_FAILED"

    return "D110_EPG_PLUGIN_RUNTIME_VALIDATED"


def render(report: dict[str, Any]) -> str:
    initial = report.get("initial_status", {})
    final = report.get("final_status", {})
    bootstrap = report.get("bootstrap", {})
    lines = [
        "PrivyHub D-110 D5.3 Linux EPG plugin runtime probe",
        f"Generated: {report['generated_at']}",
        f"Classification: {report['classification']}",
        "",
        "INITIAL STATUS",
        f"  http: {report.get('initial_status_http')}",
        f"  ready: {initial.get('ready')}",
        f"  bootstrap_in_progress: {initial.get('bootstrap_in_progress')}",
        "",
        "BOOTSTRAP",
        f"  attempted: {bootstrap.get('attempted')}",
        f"  http: {bootstrap.get('http')}",
        f"  ok: {bootstrap.get('ok')}",
        f"  elapsed_seconds: {bootstrap.get('elapsed_seconds')}",
        "",
        "FINAL STATUS",
        f"  ready: {final.get('ready')}",
        f"  node_version: {final.get('node_version')}",
        f"  epg_commit: {final.get('epg_commit')}",
        f"  toolchain_bytes: {final.get('toolchain_bytes')}",
        f"  guide_cache_files: {final.get('guide_cache_files')}",
        "",
        "GUIDE REFRESHES",
    ]

    for item in report.get("refreshes", []):
        payload = item.get("payload", {})
        source = payload.get("source") or {}
        lines.append(
            f"  {item.get('channel_id')}: http={item.get('http')}, "
            f"ok={payload.get('ok')}, programmes={payload.get('programme_count')}, "
            f"site={source.get('site')}, cached={payload.get('cached')}, "
            f"elapsed={item.get('elapsed_seconds')}"
        )

    cache = report.get("cache_recheck", {})
    cp = cache.get("payload", {})
    lines += [
        "",
        "CACHE RECHECK",
        f"  channel_id: {cache.get('channel_id')}",
        f"  http: {cache.get('http')}",
        f"  cached: {cp.get('cached')}",
        f"  programmes: {cp.get('programme_count')}",
        f"  elapsed_seconds: {cache.get('elapsed_seconds')}",
        "",
        "No Android database was modified by this probe.",
        "Linux EPG runtime/cache state under ignored data/epg is rebuildable.",
        f"JSON: {report['json_path']}",
        f"TEXT: {report['text_path']}",
    ]
    return "\n".join(lines) + "\n"


def self_test(repo: Path) -> int:
    module = load_epg_module(repo)

    with tempfile.TemporaryDirectory(prefix="d110_selftest_") as td:
        root = Path(td)
        plugin = module.EpgPlugin(
            project_root=root,
            data_root=root / "data" / "epg",
        )

        status = plugin.status()
        assert status["schema"] == plugin.STATUS_SCHEMA
        assert status["ready"] is False
        assert status["system_node_required"] is False

        try:
            plugin._validate_channel_id("tv_stream_fake")
            raise AssertionError("synthetic ID should be rejected")
        except ValueError:
            pass

        # Synthetic ready toolchain fixture.
        toolchain = plugin.toolchain_root
        (toolchain / "node" / "bin").mkdir(parents=True)
        (toolchain / "node" / "bin" / "node").write_text("", encoding="utf-8")
        (toolchain / "node" / "bin" / "npm").write_text("", encoding="utf-8")
        (toolchain / "epg" / "scripts" / "commands" / "epg").mkdir(parents=True)
        (toolchain / "epg" / "scripts" / "commands" / "epg" / "grab.ts").write_text("", encoding="utf-8")
        site_dir = toolchain / "epg" / "sites" / "example.test"
        site_dir.mkdir(parents=True)
        (site_dir / "example.test.config.ts").write_text("", encoding="utf-8")
        marker = {
            "schema": plugin.TOOLCHAIN_SCHEMA,
            "node_version": plugin.NODE_VERSION,
            "epg_commit": plugin.EPG_COMMIT,
            "host_arch": platform.machine().strip().casefold(),
            "installed_at_ms": plugin._now_ms(),
            "toolchain_bytes": 123,
        }
        (toolchain / "manifest.json").write_text(
            json.dumps(marker),
            encoding="utf-8",
        )
        assert plugin._toolchain_ready()

        metadata = [
            {
                "channel": "A.us",
                "feed": "East",
                "lang": "en",
                "site": "example.test",
                "site_id": "A1",
                "site_name": "A",
            },
            {
                "channel": "A.us",
                "feed": "West",
                "lang": "en",
                "site": "example.test",
                "site_id": "A2",
                "site_name": "A",
            },
        ]
        candidates = plugin._candidate_mappings(
            "A.us@East",
            metadata,
        )
        assert len(candidates) == 1
        assert candidates[0]["site_id"] == "A1"

        now = dt.datetime.now(dt.timezone.utc)
        start = (now + dt.timedelta(hours=1)).strftime("%Y%m%d%H%M%S +0000")
        stop = (now + dt.timedelta(hours=2)).strftime("%Y%m%d%H%M%S +0000")
        xml = root / "guide.xml"
        xml.write_text(
            "<tv>"
            f'<programme channel="A.us@East" start="{start}" stop="{stop}">'
            "<title>Fixture Show</title><desc>Fixture Description</desc>"
            "</programme></tv>",
            encoding="utf-8",
        )
        programmes = plugin._parse_xmltv_programmes(
            xml,
            "A.us@East",
            now_ms=int(now.timestamp() * 1000),
        )
        assert len(programmes) == 1
        assert programmes[0]["title"] == "Fixture Show"
        assert programmes[0]["description"] == "Fixture Description"

        cached = plugin._write_cache(
            "A.us@East",
            source={"site": "example.test"},
            programmes=programmes,
        )
        assert cached["programme_count"] == 1
        reread = plugin._read_cache(
            "A.us@East",
            allow_stale=False,
        )
        assert reread is not None
        assert reread["cached"] is True
        assert reread["programme_count"] == 1

    print("D110_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()

    if args.self_test:
        return self_test(repo)

    logs = repo / "logs" / "tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d110_epg_plugin_runtime_probe.json"
    text_path = logs / "d110_epg_plugin_runtime_probe.txt"

    report: dict[str, Any] = {
        "generated_at": now_iso(),
        "refreshes": [],
    }

    status_http, initial, initial_elapsed = request_json(STATUS_PATH)
    report["initial_status_http"] = status_http
    report["initial_status_elapsed_seconds"] = initial_elapsed
    report["initial_status"] = initial

    if status_http != 200 or initial.get("schema") != "privyhub_epg_status_v1":
        report["bootstrap"] = {"attempted": False}
        report["final_status"] = initial
    else:
        if not initial.get("ready"):
            bootstrap_http, bootstrap_payload, bootstrap_elapsed = request_json(
                BOOTSTRAP_PATH,
                method="POST",
                timeout=BOOTSTRAP_TIMEOUT_SECONDS,
            )
            report["bootstrap"] = {
                "attempted": True,
                "http": bootstrap_http,
                "ok": (
                    bootstrap_http == 200
                    and bootstrap_payload.get("ready") is True
                ),
                "elapsed_seconds": bootstrap_elapsed,
                "payload": bootstrap_payload,
            }
        else:
            report["bootstrap"] = {
                "attempted": False,
                "ok": True,
                "elapsed_seconds": 0.0,
            }

        final_http, final_status, final_elapsed = request_json(STATUS_PATH)
        report["final_status_http"] = final_http
        report["final_status_elapsed_seconds"] = final_elapsed
        report["final_status"] = final_status

        if final_http == 200 and final_status.get("ready"):
            for channel_id in CHANNELS:
                encoded = urllib.parse.quote(channel_id, safe="")
                http, payload, elapsed = request_json(
                    f"/plugins/epg/refresh?channel_id={encoded}",
                    method="POST",
                    timeout=REFRESH_TIMEOUT_SECONDS,
                )
                report["refreshes"].append(
                    {
                        "channel_id": channel_id,
                        "http": http,
                        "elapsed_seconds": elapsed,
                        "payload": payload,
                    }
                )

            encoded = urllib.parse.quote(CHANNELS[0], safe="")
            http, payload, elapsed = request_json(
                f"/plugins/epg/guide?channel_id={encoded}",
                timeout=HTTP_TIMEOUT_SECONDS,
            )
            report["cache_recheck"] = {
                "channel_id": CHANNELS[0],
                "http": http,
                "elapsed_seconds": elapsed,
                "payload": payload,
            }

    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    report["classification"] = classify(report)

    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
