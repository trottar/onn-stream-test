#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

GUIDES_URL = "https://iptv-org.github.io/api/guides.json"
EPG_REPO_URL = "https://github.com/iptv-org/epg.git"
EPG_COMMIT = "78e94adb76841a63d94a53e80dbd0d52bb7c2c5c"
APP_ID = "com.safeiot.privyhub"
BUILTIN_PROVIDER_ID = "iptv_org"
NODE_MIN = (20, 20, 0)
FETCH_TIMEOUT = 30.0
MAX_GUIDES_BYTES = 40 * 1024 * 1024
SETUP_TIMEOUT = 600
GRAB_TIMEOUT = 150
MAX_ATTEMPTS = 3
PREFERRED_SITES = (
    "i.mjh.nz",
    "pluto.tv",
    "plex.tv",
    "tvtv.us",
    "tvpassport.com",
    "sky.com",
    "mytelly.co.uk",
    "tvguide.com",
    "freeview.co.uk",
)
IPV4_RE = re.compile(r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])")
IPV6_RE = re.compile(
    r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])"
)
VERSION_RE = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def clean(value: str, limit: int = 400) -> str:
    value = IPV4_RE.sub("<redacted-address>", value or "")
    value = IPV6_RE.sub("<redacted-address>", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_id(channel: str, feed: str) -> str:
    channel = (channel or "").strip()
    feed = (feed or "").strip()
    if not channel:
        return ""
    return f"{channel}@{feed}" if feed else channel


def version_tuple(value: str) -> tuple[int, int, int] | None:
    m = VERSION_RE.search(value or "")
    return tuple(int(x) for x in m.groups()) if m else None


def command_version(exe: str, args: list[str]) -> dict[str, Any]:
    path = shutil.which(exe)
    if not path:
        return {"available": False}
    try:
        proc = subprocess.run([path, *args], capture_output=True, text=True, timeout=15)
    except Exception as exc:
        return {"available": True, "ok": False, "error": exc.__class__.__name__, "detail": clean(str(exc))}
    text = (proc.stdout or proc.stderr or "").strip()
    return {
        "available": True,
        "ok": proc.returncode == 0,
        "version_text": clean(text, 120),
        "returncode": proc.returncode,
    }


def fetch(url: str, max_bytes: int) -> tuple[bytes | None, dict[str, Any]]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PrivyHub-D108/1.0", "Cache-Control": "no-cache"},
        method="GET",
    )
    meta: dict[str, Any] = {"ok": False, "max_bytes": max_bytes}
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
            status = getattr(response, "status", None)
            meta["http_status"] = int(status) if status is not None else None
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(min(1024 * 1024, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > max_bytes:
                    meta["error"] = "response_exceeds_probe_cap"
                    return None, meta
            data = b"".join(chunks)
            meta["ok"] = status is None or 200 <= int(status) < 300
            meta["bytes"] = len(data)
            meta["sha256"] = sha256(data)
            meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
            return data, meta
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        meta["error"] = "http_error"
        meta["detail"] = clean(str(exc.reason))
    except Exception as exc:
        meta["error"] = exc.__class__.__name__
        meta["detail"] = clean(str(exc))
    meta["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
    return None, meta


def adb_serial() -> tuple[str | None, dict[str, Any]]:
    adb = shutil.which("adb")
    if not adb:
        return None, {"adb_available": False, "reason": "adb_not_found"}
    proc = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        return None, {"adb_available": True, "reason": "adb_devices_failed"}

    serials = []
    for line in proc.stdout.splitlines()[1:]:
        if "\t" not in line:
            continue
        serial, state = line.split("\t", 1)
        if state.strip() == "device":
            serials.append(serial.strip())

    return (
        serials[0] if len(serials) == 1 else None,
        {
            "adb_available": True,
            "authorized_device_count": len(serials),
            "reason": "ready" if len(serials) == 1 else "need_exactly_one_authorized_device",
        },
    )


def adb_cat(serial: str, rel: str) -> bytes | None:
    adb = shutil.which("adb")
    if not adb:
        return None
    proc = subprocess.run(
        [adb, "-s", serial, "exec-out", "run-as", APP_ID, "cat", rel],
        capture_output=True,
        timeout=20,
    )
    return proc.stdout if proc.returncode == 0 else None


def read_builtin_ids(serial: str) -> tuple[set[str], dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="d108_tvdb_") as td:
        temp = Path(td)
        main = adb_cat(serial, "databases/privyhub_tv.db")
        if not main or not main.startswith(b"SQLite format 3\x00"):
            return set(), {"snapshot_ok": False, "reason": "tv_db_unavailable"}

        db = temp / "privyhub_tv.db"
        db.write_bytes(main)
        wal = adb_cat(serial, "databases/privyhub_tv.db-wal")
        if wal:
            (temp / "privyhub_tv.db-wal").write_bytes(wal)
        shm = adb_cat(serial, "databases/privyhub_tv.db-shm")
        if shm:
            (temp / "privyhub_tv.db-shm").write_bytes(shm)

        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                rows = conn.execute(
                    "SELECT channel_id FROM streams WHERE provider_id = ?",
                    (BUILTIN_PROVIDER_ID,),
                ).fetchall()
            finally:
                conn.close()
        except Exception as exc:
            return set(), {"snapshot_ok": False, "reason": "sqlite_read_failed", "detail": clean(str(exc))}

        ids = {str(row[0] or "").strip() for row in rows if str(row[0] or "").strip()}
        return ids, {
            "snapshot_ok": True,
            "stream_rows": len(rows),
            "unique_nonblank_ids": len(ids),
            "db_sha256": sha256(main),
        }


def guide_candidates(data: bytes, builtin_ids: set[str]) -> tuple[list[dict[str, str]], dict[str, Any]]:
    payload = json.loads(data.decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("guides top level is not an array")

    candidates = []
    counts = Counter()
    seen = set()

    for item in payload:
        counts["entries_total"] += 1
        if not isinstance(item, dict):
            continue

        channel = str(item.get("channel", "") or "").strip()
        feed = str(item.get("feed", "") or "").strip()
        lang = str(item.get("lang", "") or "").strip().lower()
        site = str(item.get("site", "") or "").strip()
        site_id = str(item.get("site_id", "") or "").strip()
        site_name = str(item.get("site_name", "") or "").strip() or canonical_id(channel, feed)
        cid = canonical_id(channel, feed)

        if not cid or cid not in builtin_ids:
            continue
        counts["exact_builtin_rows"] += 1

        if lang != "en":
            continue
        counts["exact_builtin_english_rows"] += 1

        if not site or not site_id:
            continue
        counts["usable_metadata_rows"] += 1

        key = (cid, site, site_id)
        if key in seen:
            continue
        seen.add(key)

        candidates.append(
            {
                "canonical_id": cid,
                "channel": channel,
                "feed": feed,
                "lang": lang,
                "site": site,
                "site_id": site_id,
                "site_name": site_name,
            }
        )

    by_site = Counter(row["site"] for row in candidates)
    return candidates, {
        **dict(counts),
        "unique_candidate_rows": len(candidates),
        "unique_candidate_sites": len(by_site),
        "top_candidate_sites": [{"site": s, "rows": n} for s, n in by_site.most_common(20)],
    }


def run_cmd(args: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": clean("\n".join(proc.stdout.splitlines()[-12:]), 1800),
            "stderr_tail": clean("\n".join(proc.stderr.splitlines()[-12:]), 1800),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "ok": False,
            "timeout": True,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "stdout_tail": clean("\n".join(stdout.splitlines()[-12:]), 1800),
            "stderr_tail": clean("\n".join(stderr.splitlines()[-12:]), 1800),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": exc.__class__.__name__,
            "detail": clean(str(exc)),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def dir_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def config_exists(epg_repo: Path, site: str) -> bool:
    site_dir = epg_repo / "sites" / site
    return site_dir.is_dir() and any(site_dir.glob(f"{site}.config.*"))


def choose_candidates(candidates: list[dict[str, str]], epg_repo: Path, limit: int):
    by_site = defaultdict(list)
    for row in candidates:
        if config_exists(epg_repo, row["site"]):
            by_site[row["site"]].append(row)

    for rows in by_site.values():
        rows.sort(key=lambda r: (r["canonical_id"], r["site_id"]))

    ranked = [site for site in PREFERRED_SITES if site in by_site]
    ranked.extend(
        sorted(
            (site for site in by_site if site not in ranked),
            key=lambda site: (-len(by_site[site]), site),
        )
    )

    selected = [by_site[site][0] for site in ranked[:limit]]
    return selected, {
        "configured_candidate_sites": len(by_site),
        "selected_sites": [row["site"] for row in selected],
        "selected_count": len(selected),
    }


def write_channels_xml(path: Path, row: dict[str, str]) -> None:
    attrs = {
        "site": row["site"],
        "site_id": row["site_id"],
        "lang": row["lang"],
        "xmltv_id": row["canonical_id"],
    }
    attr_text = " ".join(
        f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()
    )
    name = html.escape(row["site_name"] or row["canonical_id"])
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<channels>\n"
        f"  <channel {attr_text}>{name}</channel>\n"
        "</channels>\n",
        encoding="utf-8",
    )


def parse_xmltv_date(value: str) -> dt.datetime | None:
    for fmt in ("%Y%m%d%H%M%S %z", "%Y%m%d%H%M %z", "%Y%m%d%H%M%S", "%Y%m%d%H%M"):
        try:
            parsed = dt.datetime.strptime((value or "").strip(), fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            pass
    return None


def inspect_xmltv(path: Path, target_id: str) -> dict[str, Any]:
    result = {
        "xml_exists": path.exists(),
        "xml_bytes": path.stat().st_size if path.exists() else 0,
        "xml_sha256": sha256(path.read_bytes()) if path.exists() else None,
        "parse_ok": False,
        "channels": 0,
        "programmes": 0,
        "target_programmes": 0,
        "target_current_or_upcoming_48h": 0,
    }
    if not path.exists() or path.stat().st_size == 0:
        return result

    now = dt.datetime.now(dt.timezone.utc)
    horizon = now + dt.timedelta(hours=48)

    try:
        for _, elem in ET.iterparse(path, events=("end",)):
            tag = elem.tag.rsplit("}", 1)[-1]
            if tag == "channel":
                result["channels"] += 1
            elif tag == "programme":
                result["programmes"] += 1
                channel = str(elem.attrib.get("channel", "") or "").strip()
                if channel == target_id:
                    result["target_programmes"] += 1
                    start = parse_xmltv_date(str(elem.attrib.get("start", "") or ""))
                    stop = parse_xmltv_date(str(elem.attrib.get("stop", "") or ""))
                    if start and stop and stop >= now and start <= horizon:
                        result["target_current_or_upcoming_48h"] += 1
            elem.clear()
        result["parse_ok"] = True
    except Exception as exc:
        result["parse_error"] = clean(str(exc))
    return result


def classify(report: dict[str, Any]) -> str:
    env = report["environment"]
    node_tuple = env.get("node_version_tuple")

    if not env["git"].get("available"):
        return "D108_ENVIRONMENT_GIT_UNAVAILABLE"
    if not env["node"].get("available") or not node_tuple or tuple(node_tuple) < NODE_MIN:
        return "D108_ENVIRONMENT_NODE_UNSUPPORTED"
    if not env["npm"].get("available"):
        return "D108_ENVIRONMENT_NPM_UNAVAILABLE"
    if not report.get("guides_fetch", {}).get("ok"):
        return "D108_GUIDE_METADATA_FETCH_FAILED"
    if not report.get("tv_snapshot", {}).get("snapshot_ok"):
        return "D108_ONN_TV_SNAPSHOT_UNAVAILABLE"
    if not report.get("checkout", {}).get("ok"):
        return "D108_UPSTREAM_CHECKOUT_FAILED"
    if report.get("checkout", {}).get("commit") != EPG_COMMIT:
        return "D108_UPSTREAM_CHECKOUT_COMMIT_MISMATCH"
    if not report.get("setup", {}).get("ok"):
        return "D108_UPSTREAM_TOOLCHAIN_SETUP_FAILED"
    if not report.get("selection", {}).get("selected_count"):
        return "D108_NO_CONFIGURED_EXACT_MATCHES"

    attempts = report.get("attempts", [])
    successes = [
        a for a in attempts
        if a.get("grab", {}).get("ok")
        and a.get("xmltv", {}).get("parse_ok")
        and int(a.get("xmltv", {}).get("target_programmes") or 0) > 0
    ]
    success_sites = {a.get("site") for a in successes}

    if len(success_sites) >= 2:
        return "D108_LOCAL_GRABBER_VIABLE_MULTI_SITE"
    if successes:
        return "D108_LOCAL_GRABBER_VIABLE_SINGLE_SITE"
    if attempts:
        return "D108_LOCAL_GRABBER_PROGRAMME_ACQUISITION_FAILED"
    return "D108_LOCAL_GRABBER_NOT_CLASSIFIED"


def render(report: dict[str, Any]) -> str:
    env = report["environment"]
    setup = report.get("setup", {})
    selection = report.get("selection", {})
    lines = [
        "PrivyHub D-108 D5.3 EPG local-grabber viability probe",
        f"Generated: {report['generated_at']}",
        f"Classification: {report['classification']}",
        "",
        "ENVIRONMENT",
        f"  git: {env['git'].get('version_text') or 'unavailable'}",
        f"  node: {env['node'].get('version_text') or 'unavailable'}",
        f"  npm: {env['npm'].get('version_text') or 'unavailable'}",
        f"  node_min_required: {'.'.join(map(str, NODE_MIN))}",
        "",
        "D-107 INPUT BOUNDARY",
        f"  builtin_unique_ids: {report.get('tv_snapshot', {}).get('unique_nonblank_ids')}",
        f"  exact_builtin_english_guide_rows: {report.get('guide_candidates', {}).get('exact_builtin_english_rows')}",
        f"  usable_metadata_rows: {report.get('guide_candidates', {}).get('usable_metadata_rows')}",
        f"  unique_candidate_sites: {report.get('guide_candidates', {}).get('unique_candidate_sites')}",
        "",
        "UPSTREAM EPG TOOLCHAIN",
        f"  pinned_commit: {EPG_COMMIT}",
        f"  checkout_ok: {report.get('checkout', {}).get('ok')}",
        f"  checkout_commit: {report.get('checkout', {}).get('commit')}",
        f"  setup_ok: {setup.get('ok')}",
        f"  setup_elapsed_seconds: {setup.get('elapsed_seconds')}",
        f"  disposable_tree_bytes_after_setup: {report.get('disposable_tree_bytes_after_setup')}",
        "",
        "REPRESENTATIVE SELECTION",
        f"  configured_candidate_sites: {selection.get('configured_candidate_sites')}",
        f"  selected_sites: {', '.join(selection.get('selected_sites', [])) or '<none>'}",
        "",
        "GRAB ATTEMPTS",
    ]

    for attempt in report.get("attempts", []):
        x = attempt.get("xmltv", {})
        g = attempt.get("grab", {})
        lines.append(
            f"  {attempt.get('site')} / {attempt.get('canonical_id')}: "
            f"grab_ok={g.get('ok')}, elapsed={g.get('elapsed_seconds')}, "
            f"programmes={x.get('programmes')}, target_programmes={x.get('target_programmes')}, "
            f"target_48h={x.get('target_current_or_upcoming_48h')}"
        )
        if not g.get("ok"):
            detail = g.get("stderr_tail") or g.get("stdout_tail") or g.get("detail")
            if detail:
                lines.append(f"    error: {clean(str(detail), 500)}")

    lines += [
        "",
        "Raw measurements outrank the classifier.",
        "The upstream clone, node_modules, npm cache, custom channel files, and generated XMLTV files were disposable temporary state.",
        "No PrivyHub TV/EPG database or production file was modified.",
        f"JSON: {report['json_path']}",
        f"TEXT: {report['text_path']}",
    ]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    assert canonical_id("BBCOne.uk", "EastMidlandsHD") == "BBCOne.uk@EastMidlandsHD"
    assert canonical_id("BBCOne.uk", "") == "BBCOne.uk"
    assert version_tuple("v20.20.0") == (20, 20, 0)
    assert version_tuple("22.1.3") == (22, 1, 3)
    assert tuple(version_tuple("v20.20.0") or ()) >= NODE_MIN
    assert not (tuple(version_tuple("v20.19.9") or ()) >= NODE_MIN)

    fixture = [
        {"channel": "A.us", "feed": "East", "lang": "en", "site": "alpha.example", "site_id": "A1", "site_name": "A"},
        {"channel": "B.us", "feed": None, "lang": "en", "site": "beta.example", "site_id": "B1", "site_name": "B"},
    ]
    candidates, meta = guide_candidates(json.dumps(fixture).encode("utf-8"), {"A.us@East", "B.us"})
    assert len(candidates) == 2
    assert meta["exact_builtin_english_rows"] == 2

    with tempfile.TemporaryDirectory(prefix="d108_selftest_") as td:
        xml = Path(td) / "guide.xml"
        xml.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<tv>\n"
            '  <channel id="A.us@East"><display-name>A</display-name></channel>\n'
            '  <programme start="20990101000000 +0000" stop="20990101010000 +0000" channel="A.us@East">\n'
            "    <title>A Show</title>\n"
            "  </programme>\n"
            "</tv>\n",
            encoding="utf-8",
        )
        parsed = inspect_xmltv(xml, "A.us@East")
        assert parsed["parse_ok"]
        assert parsed["channels"] == 1
        assert parsed["programmes"] == 1
        assert parsed["target_programmes"] == 1

        channels = Path(td) / "custom.channels.xml"
        write_channels_xml(channels, candidates[0])
        text = channels.read_text(encoding="utf-8")
        assert 'xmltv_id="A.us@East"' in text
        assert 'site="alpha.example"' in text

    print("D108_PROBE_SELF_TEST_OK")
    return 0


def write_report(repo: Path, report: dict[str, Any]) -> None:
    logs = repo / "logs/tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d108_epg_local_grabber_viability_probe.json"
    text_path = logs / "d108_epg_local_grabber_viability_probe.txt"
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    report["classification"] = classify(report)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    report: dict[str, Any] = {
        "generated_at": now_iso(),
        "classification": "D108_RUNNING",
        "environment": {
            "git": command_version("git", ["--version"]),
            "node": command_version("node", ["--version"]),
            "npm": command_version("npm", ["--version"]),
        },
        "upstream_epg_commit": EPG_COMMIT,
        "attempts": [],
    }

    node_tuple = version_tuple(report["environment"]["node"].get("version_text", ""))
    report["environment"]["node_version_tuple"] = list(node_tuple) if node_tuple else None

    if (
        not report["environment"]["git"].get("available")
        or not report["environment"]["node"].get("available")
        or not node_tuple
        or node_tuple < NODE_MIN
        or not report["environment"]["npm"].get("available")
    ):
        write_report(repo, report)
        return 0

    print("D108 stage: reading current onn TV identity set...", flush=True)
    serial, adb_info = adb_serial()
    report["adb"] = adb_info
    if not serial:
        report["tv_snapshot"] = {"snapshot_ok": False, "reason": adb_info.get("reason")}
        write_report(repo, report)
        return 0

    builtin_ids, tv_meta = read_builtin_ids(serial)
    report["tv_snapshot"] = tv_meta
    if not tv_meta.get("snapshot_ok"):
        write_report(repo, report)
        return 0

    print("D108 stage: fetching current guide metadata...", flush=True)
    guide_data, guide_fetch = fetch(GUIDES_URL, MAX_GUIDES_BYTES)
    report["guides_fetch"] = guide_fetch
    if not guide_data:
        write_report(repo, report)
        return 0

    try:
        candidates, candidate_meta = guide_candidates(guide_data, builtin_ids)
    except Exception as exc:
        report["guide_candidates"] = {"error": exc.__class__.__name__, "detail": clean(str(exc))}
        write_report(repo, report)
        return 0

    report["guide_candidates"] = candidate_meta

    with tempfile.TemporaryDirectory(prefix="privyhub_d108_") as td:
        temp = Path(td)
        epg_repo = temp / "epg"
        npm_cache = temp / "npm-cache"

        env = os.environ.copy()
        env.update(
            {
                "HUSKY": "0",
                "CI": "1",
                "NPM_CONFIG_AUDIT": "false",
                "NPM_CONFIG_FUND": "false",
                "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                "npm_config_cache": str(npm_cache),
                "TZ": "UTC",
            }
        )

        print("D108 stage: checking out pinned upstream EPG toolchain...", flush=True)
        epg_repo.mkdir()
        init = run_cmd(["git", "init", "-q"], epg_repo, env, 30)
        remote = run_cmd(["git", "remote", "add", "origin", EPG_REPO_URL], epg_repo, env, 30) if init.get("ok") else {"ok": False}
        fetched = run_cmd(["git", "fetch", "--depth", "1", "origin", EPG_COMMIT], epg_repo, env, 120) if remote.get("ok") else {"ok": False}
        checked = run_cmd(["git", "checkout", "--detach", "-q", "FETCH_HEAD"], epg_repo, env, 30) if fetched.get("ok") else {"ok": False}
        rev = run_cmd(["git", "rev-parse", "HEAD"], epg_repo, env, 15) if checked.get("ok") else {"ok": False}
        checkout_commit = rev.get("stdout_tail", "").strip() if rev.get("ok") else None
        report["checkout"] = {
            "ok": bool(init.get("ok") and remote.get("ok") and fetched.get("ok") and checked.get("ok") and checkout_commit == EPG_COMMIT),
            "commit": checkout_commit,
            "fetch": fetched,
        }

        if not report["checkout"]["ok"]:
            write_report(repo, report)
            return 0

        print("D108 stage: installing disposable upstream dependencies...", flush=True)
        setup = run_cmd(["npm", "ci", "--no-audit", "--no-fund"], epg_repo, env, SETUP_TIMEOUT)
        report["setup"] = setup
        report["disposable_tree_bytes_after_setup"] = dir_size(epg_repo)
        if not setup.get("ok"):
            write_report(repo, report)
            return 0

        selected, selection_meta = choose_candidates(candidates, epg_repo, MAX_ATTEMPTS)
        report["selection"] = selection_meta
        if not selected:
            write_report(repo, report)
            return 0

        for index, row in enumerate(selected, start=1):
            print(f"D108 stage: grabbing representative guide {index}/{len(selected)} from {row['site']}...", flush=True)
            channels_file = temp / f"attempt_{index}.channels.xml"
            output_file = temp / f"attempt_{index}.guide.xml"
            write_channels_xml(channels_file, row)

            grab = run_cmd(
                [
                    "npm",
                    "run",
                    "grab",
                    "--",
                    f"--channels={channels_file}",
                    f"--output={output_file}",
                    "--days=1",
                    "--maxConnections=1",
                    "--timeout=15000",
                ],
                epg_repo,
                env,
                GRAB_TIMEOUT,
            )
            xmltv = inspect_xmltv(output_file, row["canonical_id"])
            report["attempts"].append(
                {
                    "site": row["site"],
                    "canonical_id": row["canonical_id"],
                    "lang": row["lang"],
                    "grab": grab,
                    "xmltv": xmltv,
                }
            )

        write_report(repo, report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
