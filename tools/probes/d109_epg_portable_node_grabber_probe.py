#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

NODE_VERSION = "24.21.0"
NODE_BASE_URL = f"https://nodejs.org/download/release/v{NODE_VERSION}"
NODE_ARCHIVES = {
    "x86_64": {
        "filename": f"node-v{NODE_VERSION}-linux-x64.tar.xz",
        "sha256": "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6",
        "dirname": f"node-v{NODE_VERSION}-linux-x64",
    },
    "amd64": {
        "filename": f"node-v{NODE_VERSION}-linux-x64.tar.xz",
        "sha256": "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6",
        "dirname": f"node-v{NODE_VERSION}-linux-x64",
    },
    "aarch64": {
        "filename": f"node-v{NODE_VERSION}-linux-arm64.tar.xz",
        "sha256": "6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2",
        "dirname": f"node-v{NODE_VERSION}-linux-arm64",
    },
    "arm64": {
        "filename": f"node-v{NODE_VERSION}-linux-arm64.tar.xz",
        "sha256": "6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2",
        "dirname": f"node-v{NODE_VERSION}-linux-arm64",
    },
}

D108_REL = Path("tools/probes/d108_epg_local_grabber_viability_probe.py")
D108_EXPECTED_GIT_BLOB = "796f2a17ea226e7e5a7ad4027d4911c8ec329b38"
DOWNLOAD_TIMEOUT = 120.0
MAX_NODE_BYTES = 48 * 1024 * 1024


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def safe_text(value: str, limit: int = 1200) -> str:
    return " ".join((value or "").split())[:limit]


def fetch_to_file(url: str, dest: Path, max_bytes: int) -> dict[str, Any]:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PrivyHub-D109/1.0", "Cache-Control": "no-cache"},
        method="GET",
    )
    meta: dict[str, Any] = {"ok": False, "url_host": "nodejs.org", "max_bytes": max_bytes}
    try:
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
            status = getattr(response, "status", None)
            total = 0
            with dest.open("wb") as out:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        out.close()
                        dest.unlink(missing_ok=True)
                        meta["error"] = "response_exceeds_probe_cap"
                        return meta
                    out.write(chunk)
            meta["ok"] = status is None or 200 <= int(status) < 300
            meta["http_status"] = int(status) if status is not None else None
            meta["bytes"] = total
            meta["sha256"] = sha256_path(dest)
            meta["elapsed_seconds"] = round(time.monotonic() - started, 3)
            return meta
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        meta["error"] = "http_error"
        meta["detail"] = safe_text(str(exc.reason))
    except Exception as exc:
        meta["error"] = exc.__class__.__name__
        meta["detail"] = safe_text(str(exc))
    meta["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return meta


def extract_node(archive: Path, dest: Path) -> dict[str, Any]:
    started = time.monotonic()
    try:
        with tarfile.open(archive, "r:xz") as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(dest, filter="data")
            else:
                root = dest.resolve()
                for member in tf.getmembers():
                    target = (dest / member.name).resolve()
                    if target != root and root not in target.parents:
                        raise RuntimeError("unsafe archive path")
                tf.extractall(dest)
        return {"ok": True, "elapsed_seconds": round(time.monotonic() - started, 3)}
    except Exception as exc:
        return {
            "ok": False,
            "error": exc.__class__.__name__,
            "detail": safe_text(str(exc)),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def run_capture(args: list[str], cwd: Path, env: dict[str, str], timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "ok": False,
            "timeout": True,
            "stdout": stdout,
            "stderr": stderr,
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": exc.__class__.__name__,
            "detail": safe_text(str(exc)),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def map_classification(d108_class: str | None) -> str:
    mapping = {
        "D108_LOCAL_GRABBER_VIABLE_MULTI_SITE": "D109_PORTABLE_NODE_LOCAL_GRABBER_VIABLE_MULTI_SITE",
        "D108_LOCAL_GRABBER_VIABLE_SINGLE_SITE": "D109_PORTABLE_NODE_LOCAL_GRABBER_VIABLE_SINGLE_SITE",
        "D108_LOCAL_GRABBER_PROGRAMME_ACQUISITION_FAILED": "D109_PORTABLE_NODE_PROGRAMME_ACQUISITION_FAILED",
        "D108_UPSTREAM_TOOLCHAIN_SETUP_FAILED": "D109_UPSTREAM_TOOLCHAIN_SETUP_FAILED",
        "D108_UPSTREAM_CHECKOUT_FAILED": "D109_UPSTREAM_CHECKOUT_FAILED",
        "D108_NO_CONFIGURED_EXACT_MATCHES": "D109_NO_CONFIGURED_EXACT_MATCHES",
        "D108_GUIDE_METADATA_FETCH_FAILED": "D109_GUIDE_METADATA_FETCH_FAILED",
        "D108_ONN_TV_SNAPSHOT_UNAVAILABLE": "D109_ONN_TV_SNAPSHOT_UNAVAILABLE",
    }
    if d108_class in mapping:
        return mapping[d108_class]
    return f"D109_D108_RESULT_{d108_class or 'UNKNOWN'}"


def render(report: dict[str, Any]) -> str:
    runtime = report.get("portable_runtime", {})
    d108 = report.get("d108_result", {})
    lines = [
        "PrivyHub D-109 D5.3 portable-Node local-grabber probe",
        f"Generated: {report.get('generated_at')}",
        f"Classification: {report.get('classification')}",
        "",
        "PORTABLE NODE RUNTIME",
        f"  host_arch: {report.get('host_arch')}",
        f"  node_version: {NODE_VERSION}",
        f"  archive: {runtime.get('filename')}",
        f"  download_ok: {runtime.get('download', {}).get('ok')}",
        f"  checksum_ok: {runtime.get('checksum_ok')}",
        f"  extract_ok: {runtime.get('extract', {}).get('ok')}",
        f"  node_verify: {runtime.get('node_verify')}",
        f"  npm_verify: {runtime.get('npm_verify')}",
        f"  temporary_runtime_removed: {report.get('temporary_runtime_removed')}",
        "",
        "D-108 SUBPROBE",
        f"  executed: {report.get('d108_executed')}",
        f"  returncode: {report.get('d108_returncode')}",
        f"  classification: {d108.get('classification')}",
        f"  checkout_ok: {d108.get('checkout', {}).get('ok')}",
        f"  setup_ok: {d108.get('setup', {}).get('ok')}",
        f"  selected_sites: {', '.join(d108.get('selection', {}).get('selected_sites', [])) or '<none>'}",
        "",
        "GRAB ATTEMPTS",
    ]
    for attempt in d108.get("attempts", []):
        xmltv = attempt.get("xmltv", {})
        grab = attempt.get("grab", {})
        lines.append(
            f"  {attempt.get('site')} / {attempt.get('canonical_id')}: "
            f"grab_ok={grab.get('ok')}, programmes={xmltv.get('programmes')}, "
            f"target_programmes={xmltv.get('target_programmes')}, "
            f"target_48h={xmltv.get('target_current_or_upcoming_48h')}"
        )

    lines += [
        "",
        "D-109 installed no system package and changed no PrivyHub production state.",
        "The portable Node runtime existed only under a temporary directory and was removed after the D-108 subprobe.",
        f"JSON: {report.get('json_path')}",
        f"TEXT: {report.get('text_path')}",
    ]
    return "\n".join(lines) + "\n"


def write_report(repo: Path, report: dict[str, Any]) -> None:
    logs = repo / "logs/tv"
    logs.mkdir(parents=True, exist_ok=True)
    json_path = logs / "d109_epg_portable_node_grabber_probe.json"
    text_path = logs / "d109_epg_portable_node_grabber_probe.txt"
    report["json_path"] = str(json_path)
    report["text_path"] = str(text_path)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    text = render(report)
    text_path.write_text(text, encoding="utf-8")
    print(text, end="")


def self_test() -> int:
    assert NODE_ARCHIVES["x86_64"]["sha256"] == "fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6"
    assert NODE_ARCHIVES["aarch64"]["sha256"] == "6ad1325edbdb5649c379b75a237147a666c95d4f9ae8d340fef2d1575d289ad2"
    assert map_classification("D108_LOCAL_GRABBER_VIABLE_MULTI_SITE") == "D109_PORTABLE_NODE_LOCAL_GRABBER_VIABLE_MULTI_SITE"
    assert map_classification("D108_UPSTREAM_TOOLCHAIN_SETUP_FAILED") == "D109_UPSTREAM_TOOLCHAIN_SETUP_FAILED"

    with tempfile.TemporaryDirectory(prefix="d109_tar_selftest_") as td:
        base = Path(td)
        source = base / "src"
        source.mkdir()
        (source / "hello.txt").write_text("hello\n", encoding="utf-8")
        archive = base / "x.tar.xz"
        with tarfile.open(archive, "w:xz") as tf:
            tf.add(source / "hello.txt", arcname="node-test/hello.txt")
        out = base / "out"
        out.mkdir()
        result = extract_node(archive, out)
        assert result["ok"]
        assert (out / "node-test/hello.txt").read_text(encoding="utf-8") == "hello\n"

    print("D109_PROBE_SELF_TEST_OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    repo = Path(args.repo).resolve()
    d108_path = repo / D108_REL
    report: dict[str, Any] = {
        "generated_at": now_iso(),
        "host_arch": platform.machine().lower(),
        "d108_executed": False,
        "d108_returncode": None,
        "portable_runtime": {},
        "temporary_runtime_removed": None,
        "d108_result": {},
    }

    if not d108_path.is_file():
        report["classification"] = "D109_D108_PROBE_MISSING"
        write_report(repo, report)
        return 0

    actual_blob = git_blob_sha(d108_path)
    report["d108_source_blob"] = actual_blob
    if actual_blob != D108_EXPECTED_GIT_BLOB:
        report["classification"] = "D109_D108_PROBE_SOURCE_MISMATCH"
        write_report(repo, report)
        return 0

    arch = report["host_arch"]
    runtime_spec = NODE_ARCHIVES.get(arch)
    if not runtime_spec:
        report["classification"] = "D109_PORTABLE_NODE_ARCH_UNSUPPORTED"
        write_report(repo, report)
        return 0

    temp_root_str = None
    try:
        with tempfile.TemporaryDirectory(prefix="privyhub_d109_") as td:
            temp_root = Path(td)
            temp_root_str = str(temp_root)
            archive_path = temp_root / runtime_spec["filename"]
            extract_root = temp_root / "node-runtime"
            extract_root.mkdir()

            url = f"{NODE_BASE_URL}/{runtime_spec['filename']}"
            download = fetch_to_file(url, archive_path, MAX_NODE_BYTES)
            report["portable_runtime"] = {
                "filename": runtime_spec["filename"],
                "expected_sha256": runtime_spec["sha256"],
                "download": download,
            }
            if not download.get("ok"):
                report["classification"] = "D109_PORTABLE_NODE_DOWNLOAD_FAILED"
                return_after = True
            else:
                actual_sha = download.get("sha256")
                checksum_ok = actual_sha == runtime_spec["sha256"]
                report["portable_runtime"]["checksum_ok"] = checksum_ok
                if not checksum_ok:
                    report["classification"] = "D109_PORTABLE_NODE_CHECKSUM_MISMATCH"
                    return_after = True
                else:
                    extract = extract_node(archive_path, extract_root)
                    report["portable_runtime"]["extract"] = extract
                    if not extract.get("ok"):
                        report["classification"] = "D109_PORTABLE_NODE_EXTRACTION_FAILED"
                        return_after = True
                    else:
                        runtime_dir = extract_root / runtime_spec["dirname"]
                        bin_dir = runtime_dir / "bin"
                        node_path = bin_dir / "node"
                        npm_path = bin_dir / "npm"
                        if not node_path.is_file() or not npm_path.exists():
                            report["classification"] = "D109_PORTABLE_NODE_RUNTIME_INVALID"
                            return_after = True
                        else:
                            env = os.environ.copy()
                            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
                            env.update(
                                {
                                    "NPM_CONFIG_AUDIT": "false",
                                    "NPM_CONFIG_FUND": "false",
                                    "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                                }
                            )

                            node_verify = run_capture([str(node_path), "--version"], repo, env, 20)
                            npm_verify = run_capture([str(npm_path), "--version"], repo, env, 20)
                            report["portable_runtime"]["node_verify"] = safe_text(node_verify.get("stdout") or node_verify.get("stderr") or "")
                            report["portable_runtime"]["npm_verify"] = safe_text(npm_verify.get("stdout") or npm_verify.get("stderr") or "")

                            if not node_verify.get("ok") or not npm_verify.get("ok"):
                                report["classification"] = "D109_PORTABLE_NODE_RUNTIME_INVALID"
                                return_after = True
                            else:
                                d108_run = run_capture(
                                    ["python3", str(d108_path), "--repo", str(repo)],
                                    repo,
                                    env,
                                    1050,
                                )
                                report["d108_executed"] = True
                                report["d108_returncode"] = d108_run.get("returncode")
                                report["d108_stdout_tail"] = safe_text("\n".join((d108_run.get("stdout") or "").splitlines()[-30:]), 5000)
                                report["d108_stderr_tail"] = safe_text("\n".join((d108_run.get("stderr") or "").splitlines()[-30:]), 5000)

                                d108_json = repo / "logs/tv/d108_epg_local_grabber_viability_probe.json"
                                if d108_json.is_file():
                                    try:
                                        report["d108_result"] = json.loads(d108_json.read_text(encoding="utf-8"))
                                    except Exception as exc:
                                        report["d108_result_parse_error"] = safe_text(str(exc))

                                if not d108_run.get("ok"):
                                    report["classification"] = "D109_D108_SUBPROBE_EXECUTION_FAILED"
                                elif not report["d108_result"]:
                                    report["classification"] = "D109_D108_RESULT_MISSING"
                                else:
                                    report["classification"] = map_classification(
                                        report["d108_result"].get("classification")
                                    )
                                return_after = True
            if not return_after:
                report["classification"] = "D109_NOT_CLASSIFIED"
    finally:
        if temp_root_str:
            report["temporary_runtime_removed"] = not Path(temp_root_str).exists()
        else:
            report["temporary_runtime_removed"] = True
        write_report(repo, report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
