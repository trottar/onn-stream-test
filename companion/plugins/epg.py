from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs


class EpgPlugin:
    """Linux-owned EPG acquisition/cache adapter.

    Runtime/tooling state is rebuildable and lives under ignored data/epg/.
    Construction is side-effect free: no network, subprocess, or filesystem
    writes occur until bootstrap/guide work is explicitly requested.
    """

    PLUGIN_ID = "epg"

    STATUS_SCHEMA = "privyhub_epg_status_v1"
    GUIDE_SCHEMA = "privyhub_epg_guide_v1"
    TOOLCHAIN_SCHEMA = 1
    CACHE_SCHEMA = 1

    NODE_VERSION = "24.21.0"
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

    NODE_BASE_URL = f"https://nodejs.org/download/release/v{NODE_VERSION}"
    EPG_REPO_URL = "https://github.com/iptv-org/epg.git"
    EPG_COMMIT = "78e94adb76841a63d94a53e80dbd0d52bb7c2c5c"
    GUIDES_URL = "https://iptv-org.github.io/api/guides.json"

    METADATA_TTL_SECONDS = 24 * 60 * 60
    PROGRAMME_TTL_SECONDS = 6 * 60 * 60
    NEGATIVE_TTL_SECONDS = 30 * 60

    DOWNLOAD_TIMEOUT_SECONDS = 45.0
    SETUP_TIMEOUT_SECONDS = 10 * 60
    GRAB_PROCESS_TIMEOUT_SECONDS = 90
    GRAB_HTTP_TIMEOUT_MS = 15_000
    GRAB_DAYS = 2
    MAX_SOURCE_ATTEMPTS = 3
    MAX_GUIDES_BYTES = 48 * 1024 * 1024
    MAX_NODE_BYTES = 64 * 1024 * 1024

    # D-108 measured a ~446 MB upstream checkout + dependency tree. Bootstrap
    # needs additional temporary space for Node, npm cache, and staging.
    MIN_BOOTSTRAP_FREE_BYTES = 1_250_000_000

    PREFERRED_SITES = (
        "i.mjh.nz",
        "pluto.tv",
        "plex.tv",
        "tvtv.us",
        "xumo.tv",
        "tvpassport.com",
        "sky.com",
        "mytelly.co.uk",
        "tvguide.com",
        "freeview.co.uk",
    )

    IPV4_RE = re.compile(
        r"(?<![0-9A-Fa-f:])(?:\d{1,3}\.){3}\d{1,3}(?![0-9])"
    )
    IPV6_RE = re.compile(
        r"(?<![0-9A-Fa-f:])(?:[0-9A-Fa-f]{1,4}:){2,7}[0-9A-Fa-f]{0,4}(?![0-9A-Fa-f:])"
    )

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        data_root: Path | None = None,
    ) -> None:
        default_project_root = Path(__file__).resolve().parents[2]
        self.project_root = (
            Path(project_root).resolve()
            if project_root is not None
            else default_project_root
        )
        self.data_root = (
            Path(data_root).resolve()
            if data_root is not None
            else self.project_root / "data" / "epg"
        )

        self.toolchain_root = self.data_root / "toolchain"
        self.metadata_root = self.data_root / "metadata"
        self.cache_root = self.data_root / "cache"
        self.tmp_root = self.data_root / "tmp"

        self._bootstrap_lock = threading.Lock()
        self._grab_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._bootstrap_thread: threading.Thread | None = None
        self._last_error: dict[str, Any] | None = None

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @classmethod
    def _sanitize(cls, value: str, limit: int = 500) -> str:
        text = cls.IPV4_RE.sub("<redacted-address>", value or "")
        text = cls.IPV6_RE.sub("<redacted-address>", text)
        return re.sub(r"\s+", " ", text).strip()[:limit]

    @staticmethod
    def _canonical_id(channel: str, feed: str) -> str:
        channel = (channel or "").strip()
        feed = (feed or "").strip()
        if not channel:
            return ""
        return f"{channel}@{feed}" if feed else channel

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return (value or "").strip().casefold() in {"1", "true", "yes", "on"}

    @staticmethod
    def _first(query: dict[str, list[str]], key: str, default: str = "") -> str:
        values = query.get(key)
        return values[0] if values else default

    @classmethod
    def _validate_channel_id(cls, channel_id: str) -> str:
        value = (channel_id or "").strip()
        if not value:
            raise ValueError("channel_id is required")
        if len(value) > 180:
            raise ValueError("channel_id is too long")
        if value.startswith("tv_stream_"):
            raise ValueError("channel_id is synthetic and not EPG-matchable")
        if any(ord(ch) < 0x20 for ch in value):
            raise ValueError("channel_id contains control characters")
        return value

    def _marker_path(self) -> Path:
        return self.toolchain_root / "manifest.json"

    def _node_bin(self) -> Path:
        return self.toolchain_root / "node" / "bin"

    def _node_path(self) -> Path:
        return self._node_bin() / "node"

    def _npm_path(self) -> Path:
        return self._node_bin() / "npm"

    def _epg_root(self) -> Path:
        return self.toolchain_root / "epg"

    def _toolchain_marker(self) -> dict[str, Any] | None:
        path = self._marker_path()
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _runtime_spec(self) -> dict[str, str] | None:
        return self.NODE_ARCHIVES.get(platform.machine().strip().casefold())

    def _toolchain_ready(self) -> bool:
        marker = self._toolchain_marker()
        spec = self._runtime_spec()
        if marker is None or spec is None:
            return False
        return (
            marker.get("schema") == self.TOOLCHAIN_SCHEMA
            and marker.get("node_version") == self.NODE_VERSION
            and marker.get("epg_commit") == self.EPG_COMMIT
            and marker.get("host_arch") == platform.machine().strip().casefold()
            and self._node_path().is_file()
            and self._npm_path().exists()
            and (self._epg_root() / "scripts" / "commands" / "epg" / "grab.ts").is_file()
            and (self._epg_root() / "sites").is_dir()
        )

    def _record_error(self, code: str, error: Exception | str) -> None:
        message = (
            self._sanitize(str(error))
            if not isinstance(error, str)
            else self._sanitize(error)
        )
        with self._state_lock:
            self._last_error = {
                "code": code,
                "message": message,
                "at_ms": self._now_ms(),
            }

    def _clear_error(self) -> None:
        with self._state_lock:
            self._last_error = None

    @staticmethod
    def _dir_size(path: Path) -> int:
        total = 0
        if not path.exists():
            return 0
        for root, _, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    pass
        return total

    def _metadata_age_seconds(self) -> float | None:
        path = self.metadata_root / "guides.json"
        try:
            return max(0.0, time.time() - path.stat().st_mtime)
        except OSError:
            return None

    def _cache_file_count(self) -> int:
        try:
            return sum(1 for path in self.cache_root.iterdir() if path.suffix == ".json")
        except OSError:
            return 0

    def status(self) -> dict[str, Any]:
        marker = self._toolchain_marker()
        with self._state_lock:
            thread = self._bootstrap_thread
            last_error = dict(self._last_error) if self._last_error else None
        try:
            free_bytes = shutil.disk_usage(self.data_root.parent).free
        except OSError:
            free_bytes = None

        return {
            "schema": self.STATUS_SCHEMA,
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "ready": self._toolchain_ready(),
            "bootstrap_in_progress": bool(thread and thread.is_alive()),
            "runtime_policy": "persistent_rebuildable_data",
            "system_node_required": False,
            "node_version": self.NODE_VERSION,
            "epg_commit": self.EPG_COMMIT,
            "toolchain_bytes": (
                marker.get("toolchain_bytes")
                if isinstance(marker, dict)
                else None
            ),
            "installed_at_ms": (
                marker.get("installed_at_ms")
                if isinstance(marker, dict)
                else None
            ),
            "free_bytes": free_bytes,
            "minimum_bootstrap_free_bytes": self.MIN_BOOTSTRAP_FREE_BYTES,
            "metadata_age_seconds": self._metadata_age_seconds(),
            "guide_cache_files": self._cache_file_count(),
            "last_error": last_error,
        }

    @staticmethod
    def _run(
        args: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                args,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (
                exc.stdout.decode(errors="replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            )
            stderr = (
                exc.stderr.decode(errors="replace")
                if isinstance(exc.stderr, bytes)
                else (exc.stderr or "")
            )
            if stderr:
                stderr += "\n"
            stderr += "PrivyHub subprocess timeout"
            return subprocess.CompletedProcess(
                args=args,
                returncode=124,
                stdout=stdout,
                stderr=stderr,
            )

    def _download_file(
        self,
        url: str,
        dest: Path,
        *,
        max_bytes: int,
    ) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "PrivyHub/1.0 (+EPG bootstrap)",
                "Cache-Control": "no-cache",
            },
            method="GET",
        )
        digest = hashlib.sha256()
        total = 0
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.DOWNLOAD_TIMEOUT_SECONDS,
            ) as response:
                status = getattr(response, "status", None)
                if status is not None and not (200 <= int(status) < 300):
                    raise RuntimeError(f"download returned HTTP {status}")
                with dest.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            raise RuntimeError("download exceeded safety size cap")
                        digest.update(chunk)
                        output.write(chunk)
        except Exception:
            dest.unlink(missing_ok=True)
            raise
        return digest.hexdigest()

    @staticmethod
    def _safe_extract_tar_xz(archive: Path, dest: Path) -> None:
        with tarfile.open(archive, "r:xz") as tf:
            if hasattr(tarfile, "data_filter"):
                tf.extractall(dest, filter="data")
                return

            root = dest.resolve()
            for member in tf.getmembers():
                target = (dest / member.name).resolve()
                if target != root and root not in target.parents:
                    raise RuntimeError("unsafe archive path")
            tf.extractall(dest)

    def _bootstrap_env(
        self,
        node_bin: Path,
        npm_cache: Path,
    ) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "PATH": str(node_bin) + os.pathsep + env.get("PATH", ""),
                "HUSKY": "0",
                "CI": "1",
                "NPM_CONFIG_AUDIT": "false",
                "NPM_CONFIG_FUND": "false",
                "NPM_CONFIG_UPDATE_NOTIFIER": "false",
                "npm_config_cache": str(npm_cache),
                "TZ": "UTC",
            }
        )
        return env

    def bootstrap(self) -> dict[str, Any]:
        with self._bootstrap_lock:
            if self._toolchain_ready():
                payload = self.status()
                payload["changed"] = False
                return payload

            spec = self._runtime_spec()
            if spec is None:
                self._record_error("unsupported_architecture", platform.machine())
                raise RuntimeError("EPG portable runtime architecture is unsupported")

            try:
                self.data_root.mkdir(parents=True, exist_ok=True)
                free_bytes = shutil.disk_usage(self.data_root).free
            except OSError as exc:
                self._record_error("storage_unavailable", exc)
                raise RuntimeError("EPG runtime storage is unavailable") from exc

            if free_bytes < self.MIN_BOOTSTRAP_FREE_BYTES:
                self._record_error("insufficient_space", "bootstrap free-space preflight failed")
                raise RuntimeError("EPG runtime bootstrap requires more free disk space")

            staging = self.data_root / (
                f".toolchain-staging-{os.getpid()}-{self._now_ms()}"
            )
            old = self.data_root / (
                f".toolchain-old-{os.getpid()}-{self._now_ms()}"
            )
            started = time.monotonic()

            try:
                shutil.rmtree(staging, ignore_errors=True)
                staging.mkdir(parents=True)
                archive = staging / spec["filename"]
                extract_root = staging / "node_extract"
                extract_root.mkdir()
                npm_cache = staging / "npm-cache"

                actual_sha = self._download_file(
                    f"{self.NODE_BASE_URL}/{spec['filename']}",
                    archive,
                    max_bytes=self.MAX_NODE_BYTES,
                )
                if actual_sha != spec["sha256"]:
                    raise RuntimeError("portable Node checksum mismatch")

                self._safe_extract_tar_xz(archive, extract_root)
                extracted_node = extract_root / spec["dirname"]
                if not extracted_node.is_dir():
                    raise RuntimeError("portable Node archive did not contain expected directory")

                node_root = staging / "node"
                extracted_node.rename(node_root)
                shutil.rmtree(extract_root, ignore_errors=True)
                archive.unlink(missing_ok=True)

                git_path = shutil.which("git")
                if not git_path:
                    raise RuntimeError("git is required for EPG runtime bootstrap")

                epg_root = staging / "epg"
                epg_root.mkdir()

                env = self._bootstrap_env(node_root / "bin", npm_cache)

                steps = (
                    ([git_path, "init", "-q"], 30),
                    ([git_path, "remote", "add", "origin", self.EPG_REPO_URL], 30),
                    ([git_path, "fetch", "--depth", "1", "origin", self.EPG_COMMIT], 180),
                    ([git_path, "checkout", "--detach", "-q", "FETCH_HEAD"], 30),
                )
                for args, timeout in steps:
                    result = self._run(args, cwd=epg_root, env=env, timeout=timeout)
                    if result.returncode != 0:
                        raise RuntimeError(
                            "EPG upstream checkout failed: "
                            + self._sanitize(result.stderr or result.stdout)
                        )

                npm_path = node_root / "bin" / "npm"
                result = self._run(
                    [str(npm_path), "ci", "--no-audit", "--no-fund"],
                    cwd=epg_root,
                    env=env,
                    timeout=self.SETUP_TIMEOUT_SECONDS,
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        "EPG upstream dependency setup failed: "
                        + self._sanitize(result.stderr or result.stdout)
                    )

                node_result = self._run(
                    [str(node_root / "bin" / "node"), "--version"],
                    cwd=epg_root,
                    env=env,
                    timeout=20,
                )
                npm_result = self._run(
                    [str(npm_path), "--version"],
                    cwd=epg_root,
                    env=env,
                    timeout=20,
                )
                if node_result.returncode != 0 or npm_result.returncode != 0:
                    raise RuntimeError("portable Node/npm verification failed")

                if not (
                    epg_root / "scripts" / "commands" / "epg" / "grab.ts"
                ).is_file():
                    raise RuntimeError("EPG grab command is missing after setup")
                if not (epg_root / "sites").is_dir():
                    raise RuntimeError("EPG site definitions are missing after setup")

                # Runtime is pinned and rebuildable. Git history and npm download
                # cache are unnecessary after successful setup.
                shutil.rmtree(epg_root / ".git", ignore_errors=True)
                shutil.rmtree(npm_cache, ignore_errors=True)

                marker = {
                    "schema": self.TOOLCHAIN_SCHEMA,
                    "node_version": self.NODE_VERSION,
                    "npm_version": (npm_result.stdout or "").strip(),
                    "epg_commit": self.EPG_COMMIT,
                    "host_arch": platform.machine().strip().casefold(),
                    "installed_at_ms": self._now_ms(),
                    "setup_elapsed_seconds": round(time.monotonic() - started, 3),
                }
                marker["toolchain_bytes"] = self._dir_size(staging)
                (staging / "manifest.json").write_text(
                    json.dumps(marker, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                shutil.rmtree(old, ignore_errors=True)
                if self.toolchain_root.exists():
                    self.toolchain_root.rename(old)
                staging.rename(self.toolchain_root)
                shutil.rmtree(old, ignore_errors=True)

                self._clear_error()
                payload = self.status()
                payload["changed"] = True
                payload["setup_elapsed_seconds"] = marker["setup_elapsed_seconds"]
                return payload

            except Exception as exc:
                shutil.rmtree(staging, ignore_errors=True)
                if old.exists() and not self.toolchain_root.exists():
                    old.rename(self.toolchain_root)
                self._record_error("bootstrap_failed", exc)
                raise RuntimeError("EPG runtime bootstrap failed") from exc
            finally:
                shutil.rmtree(old, ignore_errors=True)

    def _start_bootstrap_async(self) -> bool:
        if self._toolchain_ready():
            return False

        with self._state_lock:
            if self._bootstrap_thread and self._bootstrap_thread.is_alive():
                return False

            def runner() -> None:
                try:
                    self.bootstrap()
                except Exception:
                    # Error details are already recorded by bootstrap().
                    pass
                finally:
                    with self._state_lock:
                        if self._bootstrap_thread is threading.current_thread():
                            self._bootstrap_thread = None

            thread = threading.Thread(
                target=runner,
                name="PrivyHubEpgBootstrap",
                daemon=True,
            )
            self._bootstrap_thread = thread
            thread.start()
            return True

    def _metadata_file(self) -> Path:
        return self.metadata_root / "guides.json"

    def _fetch_guides_metadata(self, *, force: bool = False) -> list[dict[str, Any]]:
        path = self._metadata_file()
        if not force and path.is_file():
            try:
                if time.time() - path.stat().st_mtime < self.METADATA_TTL_SECONDS:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(payload, list):
                        return payload
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                pass

        self.metadata_root.mkdir(parents=True, exist_ok=True)
        temp = self.metadata_root / f".guides-{os.getpid()}-{self._now_ms()}.tmp"

        request = urllib.request.Request(
            self.GUIDES_URL,
            headers={
                "User-Agent": "PrivyHub/1.0 (+EPG metadata)",
                "Cache-Control": "no-cache",
            },
            method="GET",
        )

        try:
            total = 0
            chunks: list[bytes] = []
            with urllib.request.urlopen(
                request,
                timeout=self.DOWNLOAD_TIMEOUT_SECONDS,
            ) as response:
                status = getattr(response, "status", None)
                if status is not None and not (200 <= int(status) < 300):
                    raise RuntimeError(f"guide metadata returned HTTP {status}")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self.MAX_GUIDES_BYTES:
                        raise RuntimeError("guide metadata exceeded safety size cap")
                    chunks.append(chunk)

            raw = b"".join(chunks)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, list):
                raise RuntimeError("guide metadata root is not an array")

            temp.write_bytes(raw)
            os.replace(temp, path)
            return payload
        except Exception:
            temp.unlink(missing_ok=True)
            raise

    def _candidate_mappings(
        self,
        channel_id: str,
        metadata: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        candidates: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()

        for item in metadata:
            if not isinstance(item, dict):
                continue

            canonical = self._canonical_id(
                str(item.get("channel", "") or ""),
                str(item.get("feed", "") or ""),
            )
            if canonical != channel_id:
                continue

            site = str(item.get("site", "") or "").strip()
            site_id = str(item.get("site_id", "") or "").strip()
            language = str(item.get("lang", "") or "").strip()
            name = str(item.get("site_name", "") or "").strip() or channel_id
            if not site or not site_id:
                continue

            site_dir = self._epg_root() / "sites" / site
            if not (
                site_dir.is_dir()
                and any(site_dir.glob(f"{site}.config.*"))
            ):
                continue

            key = (site, site_id, language.casefold())
            if key in seen:
                continue
            seen.add(key)

            candidates.append(
                {
                    "site": site,
                    "site_id": site_id,
                    "language": language,
                    "name": name,
                }
            )

        preferred_rank = {
            site: index for index, site in enumerate(self.PREFERRED_SITES)
        }
        candidates.sort(
            key=lambda row: (
                0 if row["language"].casefold() == "en" else 1,
                preferred_rank.get(row["site"], len(preferred_rank)),
                row["site"].casefold(),
                row["site_id"],
            )
        )
        return candidates

    @staticmethod
    def _parse_xmltv_date(value: str) -> int:
        value = (value or "").strip()
        if not value:
            return 0

        formats = (
            "%Y%m%d%H%M%S %z",
            "%Y%m%d%H%M %z",
            "%Y%m%d%H%M%S",
            "%Y%m%d%H%M",
        )
        for fmt in formats:
            try:
                parsed = dt.datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=dt.timezone.utc)
                return int(parsed.timestamp() * 1000)
            except ValueError:
                continue
        return 0

    def _parse_xmltv_programmes(
        self,
        path: Path,
        channel_id: str,
        *,
        now_ms: int,
    ) -> list[dict[str, Any]]:
        earliest = now_ms - 2 * 60 * 60 * 1000
        latest = now_ms + 48 * 60 * 60 * 1000
        programmes: list[dict[str, Any]] = []

        for _, elem in ET.iterparse(path, events=("end",)):
            tag = elem.tag.rsplit("}", 1)[-1]
            if tag != "programme":
                continue

            xml_channel = str(elem.attrib.get("channel", "") or "").strip()
            if xml_channel != channel_id:
                elem.clear()
                continue

            start_ms = self._parse_xmltv_date(
                str(elem.attrib.get("start", "") or "")
            )
            stop_ms = self._parse_xmltv_date(
                str(elem.attrib.get("stop", "") or "")
            )
            if not start_ms or stop_ms <= earliest or start_ms >= latest:
                elem.clear()
                continue

            title = ""
            description: str | None = None
            for child in list(elem):
                child_tag = child.tag.rsplit("}", 1)[-1]
                text = (child.text or "").strip()
                if child_tag == "title" and text and not title:
                    title = text
                elif child_tag == "desc" and text and description is None:
                    description = text

            if not title:
                title = "Programme"

            programmes.append(
                {
                    "channel_id": channel_id,
                    "start_ms": start_ms,
                    "stop_ms": stop_ms,
                    "title": title,
                    "description": description,
                }
            )
            elem.clear()

        programmes.sort(
            key=lambda item: (
                int(item["start_ms"]),
                int(item["stop_ms"]),
                str(item["title"]),
            )
        )
        return programmes[:120]

    def _cache_path(self, channel_id: str) -> Path:
        digest = hashlib.sha256(channel_id.encode("utf-8")).hexdigest()
        return self.cache_root / f"{digest}.json"

    def _read_cache(
        self,
        channel_id: str,
        *,
        allow_stale: bool,
    ) -> dict[str, Any] | None:
        path = self._cache_path(channel_id)
        if not path.is_file():
            return None

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return None
            if payload.get("schema") != self.CACHE_SCHEMA:
                return None
            if payload.get("channel_id") != channel_id:
                return None
            refreshed_at_ms = int(payload.get("refreshed_at_ms") or 0)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return None

        programmes = payload.get("programmes")
        if not isinstance(programmes, list):
            return None

        age_seconds = max(
            0.0,
            (self._now_ms() - refreshed_at_ms) / 1000.0,
        )
        ttl = (
            self.PROGRAMME_TTL_SECONDS
            if programmes
            else self.NEGATIVE_TTL_SECONDS
        )
        fresh = age_seconds < ttl
        if not fresh and not allow_stale:
            return None

        result = {
            "schema": self.GUIDE_SCHEMA,
            "ok": True,
            "ready": self._toolchain_ready(),
            "channel_id": channel_id,
            "cached": True,
            "stale": not fresh,
            "refreshed_at_ms": refreshed_at_ms,
            "source": payload.get("source"),
            "programmes": programmes,
            "programme_count": len(programmes),
        }
        empty_reason = payload.get("empty_reason")
        if isinstance(empty_reason, str) and empty_reason:
            result["empty_reason"] = empty_reason
        return result

    def _write_cache(
        self,
        channel_id: str,
        *,
        source: dict[str, Any] | None,
        programmes: list[dict[str, Any]],
        empty_reason: str | None = None,
    ) -> dict[str, Any]:
        self.cache_root.mkdir(parents=True, exist_ok=True)
        path = self._cache_path(channel_id)
        temp = path.with_suffix(f".{os.getpid()}.tmp")
        refreshed_at_ms = self._now_ms()

        stored = {
            "schema": self.CACHE_SCHEMA,
            "channel_id": channel_id,
            "refreshed_at_ms": refreshed_at_ms,
            "source": source,
            "programmes": programmes,
            "empty_reason": empty_reason,
        }
        temp.write_text(
            json.dumps(stored, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temp, path)

        return {
            "schema": self.GUIDE_SCHEMA,
            "ok": True,
            "ready": True,
            "channel_id": channel_id,
            "cached": False,
            "stale": False,
            "refreshed_at_ms": refreshed_at_ms,
            "source": source,
            "programmes": programmes,
            "programme_count": len(programmes),
            **(
                {"empty_reason": empty_reason}
                if empty_reason
                else {}
            ),
        }

    def _write_channels_xml(
        self,
        path: Path,
        channel_id: str,
        candidate: dict[str, str],
    ) -> None:
        attrs = {
            "site": candidate["site"],
            "site_id": candidate["site_id"],
            "lang": candidate["language"] or "en",
            "xmltv_id": channel_id,
        }
        attr_text = " ".join(
            f'{key}="{html.escape(value, quote=True)}"'
            for key, value in attrs.items()
        )
        name = html.escape(candidate["name"] or channel_id)
        path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<channels>\n"
            f"  <channel {attr_text}>{name}</channel>\n"
            "</channels>\n",
            encoding="utf-8",
        )

    def _grab_environment(self, npm_cache: Path) -> dict[str, str]:
        return self._bootstrap_env(self._node_bin(), npm_cache)

    def _grab_from_candidate(
        self,
        channel_id: str,
        candidate: dict[str, str],
        *,
        now_ms: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        self.tmp_root.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix="grab_",
            dir=self.tmp_root,
        ) as td:
            temp = Path(td)
            channels = temp / "channel.channels.xml"
            output = temp / "guide.xml"
            npm_cache = temp / "npm-cache"

            self._write_channels_xml(
                channels,
                channel_id,
                candidate,
            )

            env = self._grab_environment(npm_cache)
            started = time.monotonic()
            result = self._run(
                [
                    str(self._npm_path()),
                    "run",
                    "grab",
                    "--",
                    f"--channels={channels}",
                    f"--output={output}",
                    f"--days={self.GRAB_DAYS}",
                    "--maxConnections=1",
                    f"--timeout={self.GRAB_HTTP_TIMEOUT_MS}",
                ],
                cwd=self._epg_root(),
                env=env,
                timeout=self.GRAB_PROCESS_TIMEOUT_SECONDS,
            )
            elapsed = round(time.monotonic() - started, 3)

            if result.returncode != 0:
                return [], {
                    "site": candidate["site"],
                    "ok": False,
                    "elapsed_seconds": elapsed,
                    "error": self._sanitize(
                        result.stderr or result.stdout or "grab failed"
                    ),
                }

            if not output.is_file():
                return [], {
                    "site": candidate["site"],
                    "ok": False,
                    "elapsed_seconds": elapsed,
                    "error": "grab produced no XMLTV output",
                }

            try:
                programmes = self._parse_xmltv_programmes(
                    output,
                    channel_id,
                    now_ms=now_ms,
                )
            except Exception as exc:
                return [], {
                    "site": candidate["site"],
                    "ok": False,
                    "elapsed_seconds": elapsed,
                    "error": self._sanitize(str(exc)),
                }

            return programmes, {
                "site": candidate["site"],
                "ok": True,
                "elapsed_seconds": elapsed,
                "programme_count": len(programmes),
            }

    def guide(
        self,
        channel_id: str,
        *,
        force: bool = False,
    ) -> dict[str, Any]:
        channel_id = self._validate_channel_id(channel_id)

        if not force:
            cached = self._read_cache(
                channel_id,
                allow_stale=False,
            )
            if cached is not None:
                return cached

        stale = self._read_cache(
            channel_id,
            allow_stale=True,
        )

        if not self._toolchain_ready():
            started = self._start_bootstrap_async()
            if stale is not None:
                stale["ready"] = False
                stale["bootstrap_started"] = started
                stale["refresh_deferred"] = True
                return stale

            return {
                "schema": self.GUIDE_SCHEMA,
                "ok": False,
                "ready": False,
                "channel_id": channel_id,
                "cached": False,
                "stale": False,
                "bootstrap_started": started,
                "error_code": "toolchain_preparing",
                "programmes": [],
                "programme_count": 0,
            }

        with self._grab_lock:
            if not force:
                cached = self._read_cache(
                    channel_id,
                    allow_stale=False,
                )
                if cached is not None:
                    return cached

            stale = self._read_cache(
                channel_id,
                allow_stale=True,
            )

            try:
                metadata = self._fetch_guides_metadata()
                candidates = self._candidate_mappings(
                    channel_id,
                    metadata,
                )
            except Exception as exc:
                self._record_error("metadata_failed", exc)
                if stale is not None:
                    stale["refresh_error_code"] = "metadata_failed"
                    return stale
                raise RuntimeError("EPG metadata acquisition failed") from exc

            if not candidates:
                self._clear_error()
                return self._write_cache(
                    channel_id,
                    source=None,
                    programmes=[],
                    empty_reason="no_exact_configured_mapping",
                )

            attempts: list[dict[str, Any]] = []
            now_ms = self._now_ms()
            for candidate in candidates[: self.MAX_SOURCE_ATTEMPTS]:
                programmes, attempt = self._grab_from_candidate(
                    channel_id,
                    candidate,
                    now_ms=now_ms,
                )
                attempts.append(attempt)

                if programmes:
                    self._clear_error()
                    result = self._write_cache(
                        channel_id,
                        source={
                            "site": candidate["site"],
                            "site_id": candidate["site_id"],
                            "language": candidate["language"],
                        },
                        programmes=programmes,
                    )
                    result["attempts"] = attempts
                    return result

            self._record_error(
                "programme_acquisition_failed",
                "all configured guide sources returned no usable programmes",
            )
            if stale is not None:
                stale["refresh_error_code"] = "programme_acquisition_failed"
                stale["attempts"] = attempts
                return stale

            result = self._write_cache(
                channel_id,
                source=None,
                programmes=[],
                empty_reason="programme_acquisition_failed",
            )
            result["attempts"] = attempts
            return result

    def handle(
        self,
        action: str,
        raw_query: str,
    ) -> dict[str, Any]:
        query = parse_qs(
            raw_query,
            keep_blank_values=False,
        )

        if action == "status":
            return self.status()

        if action == "guide":
            channel_id = self._first(
                query,
                "channel_id",
            )
            force = self._parse_bool(
                self._first(
                    query,
                    "force",
                )
            )
            try:
                return self.guide(
                    channel_id,
                    force=force,
                )
            except (ValueError, RuntimeError):
                raise
            except Exception as exc:
                self._record_error("guide_request_failed", exc)
                raise RuntimeError("EPG guide request failed") from exc

        raise ValueError(f"Unknown EPG action: {action}")

    def handle_post(
        self,
        action: str,
        raw_query: str,
    ) -> dict[str, Any]:
        query = parse_qs(
            raw_query,
            keep_blank_values=False,
        )

        if action == "bootstrap":
            return self.bootstrap()

        if action == "refresh":
            channel_id = self._first(
                query,
                "channel_id",
            )
            try:
                if not self._toolchain_ready():
                    self.bootstrap()
                return self.guide(
                    channel_id,
                    force=True,
                )
            except (ValueError, RuntimeError):
                raise
            except Exception as exc:
                self._record_error("guide_refresh_failed", exc)
                raise RuntimeError("EPG guide refresh failed") from exc

        raise ValueError(f"Unknown EPG POST action: {action}")

    def shutdown(self) -> None:
        # The plugin owns no persistent child process. Individual grab
        # subprocesses are synchronous and bounded by timeout.
        return None
