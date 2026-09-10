#!/usr/bin/env python3
"""
PrivyHub companion control service.

Directory-independent layout:

    project_root/
    ├── companion/
    │   ├── privyhub_service.py
    │   ├── range_server.py
    │   └── config/
    │       └── sources.json
    ├── scripts/
    ├── media/
    │   ├── vod/
    │   └── live/
    └── logs/

Public API:
    GET  /status
    GET  /sources
    POST /sources/<source_id>/start
    POST /stop

The source catalog supports both:
    - explicitly configured sources/categories
    - dynamic media-directory categories

Dynamic VOD directories are rescanned whenever /sources is requested and
whenever a generated source is started. Adding/removing/renaming media files
therefore requires no companion restart.

Windows prototype using only the Python standard library.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
import time
import urllib.error
import urllib.request

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote, unquote, urlparse, urlsplit

from plugins import (
    PLUGINS,
    shutdown_plugins,
)


COMPANION_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = COMPANION_DIR.parent

MEDIA_ROOT = PROJECT_ROOT / "media"
LIVE_DIR = MEDIA_ROOT / "live"
LOG_DIR = PROJECT_ROOT / "logs"

CATALOG_FILE = COMPANION_DIR / "config" / "sources.json"
SERVER_SCRIPT = PROJECT_ROOT / "scripts" / "start_server.ps1"

CONTROL_HOST = "0.0.0.0"
CONTROL_PORT = 8765

MEDIA_HOST_FOR_HEALTH = "127.0.0.1"
DEFAULT_MEDIA_PORT = 8000

POWERSHELL = "powershell.exe"

HEALTH_POLL_SECONDS = 0.75
HTTP_HEALTH_TIMEOUT_SECONDS = 2.0

DEFAULT_MEDIA_EXTENSIONS = {
    ".mp4",
    ".m4v",
    ".mkv",
    ".webm",
    ".mov",
    ".ts",
    ".m2ts",
}


@dataclass
class ManagedProcess:
    name: str
    process: subprocess.Popen
    log_handle: Any
    log_path: Path


class CatalogError(Exception):
    pass


class SourceStartError(Exception):
    pass


class SourceCatalog:
    def __init__(
        self,
        catalog_path: Path,
        media_root: Path,
    ) -> None:
        self.catalog_path = catalog_path
        self.media_root = media_root.resolve()

        self.lock = threading.RLock()

        self.raw: dict[str, Any] = {}
        self.static_sources: dict[str, dict[str, Any]] = {}
        self.dynamic_sources: dict[str, dict[str, Any]] = {}

        self.load()

    def load(self) -> None:
        if not self.catalog_path.exists():
            raise CatalogError(
                f"Source catalog not found: {self.catalog_path}"
            )

        with self.catalog_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)

        if not isinstance(raw, dict):
            raise CatalogError("Source catalog root must be an object")

        root = raw.get("root")

        if not isinstance(root, list):
            raise CatalogError("Source catalog must contain a root array")

        static_source_index: dict[str, dict[str, Any]] = {}
        seen_ids: set[str] = set()

        def walk(node: dict[str, Any]) -> None:
            node_id = node.get("id")
            node_type = node.get("node_type")

            if not isinstance(node_id, str) or not node_id:
                raise CatalogError(
                    "Every catalog node needs a non-empty id"
                )

            if node_id in seen_ids:
                raise CatalogError(
                    f"Duplicate catalog id: {node_id}"
                )

            seen_ids.add(node_id)

            if node_type == "category":
                children = node.get("children", [])
                dynamic = node.get("dynamic")
                lazy_path = node.get("lazy_path")

                if not isinstance(children, list):
                    raise CatalogError(
                        f"Category {node_id} must have a children array"
                    )

                if dynamic is not None:
                    self._validate_dynamic_config(
                        node_id,
                        dynamic,
                    )

                if lazy_path is not None:
                    if (
                        not isinstance(lazy_path, str)
                        or not lazy_path.startswith("/plugins/")
                    ):
                        raise CatalogError(
                            f"Category {node_id} has invalid lazy_path"
                        )

                if (
                    not children
                    and dynamic is None
                    and lazy_path is None
                ):
                    raise CatalogError(
                        f"Category {node_id} needs children, dynamic config, "
                        "or lazy_path"
                    )

                for child in children:
                    if not isinstance(child, dict):
                        raise CatalogError(
                            f"Category {node_id} contains a non-object child"
                        )

                    walk(child)

                return

            if node_type == "source":
                playback = node.get("playback")

                if not isinstance(playback, dict):
                    raise CatalogError(
                        f"Source {node_id} needs a playback object"
                    )

                playback_type = playback.get("type")

                if playback_type not in {"live", "vod"}:
                    raise CatalogError(
                        f"Source {node_id} has unsupported playback type"
                    )

                media_path = playback.get("path")

                if (
                    not isinstance(media_path, str)
                    or not media_path.startswith("/")
                ):
                    raise CatalogError(
                        f"Source {node_id} needs an absolute media path"
                    )

                static_source_index[node_id] = node
                return

            raise CatalogError(
                f"Node {node_id} has unsupported node_type: {node_type}"
            )

        for item in root:
            if not isinstance(item, dict):
                raise CatalogError(
                    "Root catalog entries must be objects"
                )

            walk(item)

        with self.lock:
            self.raw = raw
            self.static_sources = static_source_index
            self.dynamic_sources = {}

    def _validate_dynamic_config(
        self,
        node_id: str,
        dynamic: Any,
    ) -> None:
        if not isinstance(dynamic, dict):
            raise CatalogError(
                f"Category {node_id} dynamic config must be an object"
            )

        dynamic_type = dynamic.get("type")

        if dynamic_type != "media_directory":
            raise CatalogError(
                f"Category {node_id} has unsupported dynamic type: "
                f"{dynamic_type}"
            )

        relative_path = dynamic.get("path")

        if not isinstance(relative_path, str) or not relative_path.strip():
            raise CatalogError(
                f"Category {node_id} dynamic path is required"
            )

        path = Path(relative_path)

        if path.is_absolute() or ".." in path.parts:
            raise CatalogError(
                f"Category {node_id} dynamic path must stay under media/"
            )

        extensions = dynamic.get("extensions")

        if extensions is not None:
            if not isinstance(extensions, list):
                raise CatalogError(
                    f"Category {node_id} extensions must be an array"
                )

            for extension in extensions:
                if (
                    not isinstance(extension, str)
                    or not extension.startswith(".")
                ):
                    raise CatalogError(
                        f"Category {node_id} has invalid extension: "
                        f"{extension!r}"
                    )

    def _safe_media_directory(
        self,
        relative_path: str,
    ) -> Path:
        directory = (
            self.media_root / relative_path
        ).resolve()

        try:
            directory.relative_to(
                self.media_root
            )
        except ValueError as exc:
            raise CatalogError(
                f"Dynamic media path escapes media root: {relative_path}"
            ) from exc

        return directory

    @staticmethod
    def _slug(
        text: str,
    ) -> str:
        slug = re.sub(
            r"[^a-z0-9]+",
            "_",
            text.casefold(),
        ).strip("_")

        if not slug:
            slug = "media"

        return slug[:48]

    @classmethod
    def _generated_id(
        cls,
        prefix: str,
        relative_path: str,
    ) -> str:
        normalized = (
            relative_path
            .replace("\\", "/")
            .casefold()
        )

        digest = hashlib.sha1(
            normalized.encode("utf-8")
        ).hexdigest()[:10]

        readable = cls._slug(
            Path(relative_path).stem
        )

        return (
            f"{prefix}_{readable}_{digest}"
        )

    @staticmethod
    def _clean_display_name(
        raw_name: str,
    ) -> str:
        """
        Apply only conservative filename cleanup.

        - underscores become spaces
        - repeated whitespace is collapsed
        - obviously machine-style all-lowercase/all-uppercase names get
          title casing
        - deliberately mixed-case names are otherwise preserved

        This intentionally avoids metadata guessing.
        """
        cleaned = re.sub(
            r"\s+",
            " ",
            raw_name.replace("_", " "),
        ).strip()

        if not cleaned:
            return raw_name

        letters = [
            character
            for character in cleaned
            if character.isalpha()
        ]

        if letters:
            all_lower = all(
                character.islower()
                for character in letters
            )

            all_upper = all(
                character.isupper()
                for character in letters
            )

            if all_lower or all_upper:
                cleaned = cleaned.title()

        return cleaned

    @classmethod
    def _display_file_name(
        cls,
        file_path: Path,
    ) -> str:
        name = file_path.stem.strip()

        if not name:
            return file_path.name

        return cls._clean_display_name(
            name
        )

    @classmethod
    def _display_directory_name(
        cls,
        directory: Path,
    ) -> str:
        name = directory.name.strip()

        if not name:
            return directory.name

        return cls._clean_display_name(
            name
        )

    @staticmethod
    def _extensions_from_config(
        dynamic: dict[str, Any],
    ) -> set[str]:
        configured = dynamic.get("extensions")

        if configured is None:
            return set(DEFAULT_MEDIA_EXTENSIONS)

        return {
            str(extension).casefold()
            for extension in configured
        }

    def _scan_media_directory(
        self,
        category_id: str,
        dynamic: dict[str, Any],
    ) -> list[dict[str, Any]]:
        relative_root = Path(
            dynamic["path"]
        )

        disk_root = self._safe_media_directory(
            relative_root.as_posix()
        )

        if not disk_root.exists():
            return []

        if not disk_root.is_dir():
            raise CatalogError(
                f"Dynamic media path is not a directory: {disk_root}"
            )

        extensions = self._extensions_from_config(
            dynamic
        )

        dynamic_source_index: dict[str, dict[str, Any]] = {}

        def scan_directory(
            disk_directory: Path,
            relative_directory: Path,
        ) -> list[dict[str, Any]]:
            children: list[dict[str, Any]] = []

            directories = sorted(
                (
                    item
                    for item in disk_directory.iterdir()
                    if item.is_dir()
                    and not item.name.startswith(".")
                ),
                key=lambda item: item.name.casefold(),
            )

            files = sorted(
                (
                    item
                    for item in disk_directory.iterdir()
                    if item.is_file()
                    and not item.name.startswith(".")
                    and item.suffix.casefold() in extensions
                ),
                key=lambda item: item.name.casefold(),
            )

            for directory in directories:
                relative_child = (
                    relative_directory
                    / directory.name
                )

                child_nodes = scan_directory(
                    directory,
                    relative_child,
                )

                # Empty folders are implementation detail, not useful
                # navigation.  A directory is shown only when it contains
                # at least one supported media file somewhere below it.
                if not child_nodes:
                    continue

                directory_id = self._generated_id(
                    f"{category_id}_dir",
                    relative_child.as_posix(),
                )

                children.append(
                    {
                        "id": directory_id,
                        "name": self._display_directory_name(
                            directory
                        ),
                        "node_type": "category",
                        "children": child_nodes,
                    }
                )

            for media_file in files:
                relative_file = (
                    relative_directory
                    / media_file.name
                )

                source_id = self._generated_id(
                    f"{category_id}_file",
                    relative_file.as_posix(),
                )

                media_url_path = (
                    "/"
                    + quote(
                        relative_file.as_posix(),
                        safe="/",
                    )
                )

                source = {
                    "id": source_id,
                    "name": self._display_file_name(
                        media_file
                    ),
                    "node_type": "source",
                    "playback": {
                        "type": "vod",
                        "port": DEFAULT_MEDIA_PORT,
                        "path": media_url_path,
                    },
                    "health": {
                        "type": "file",
                    },
                    "_filesystem_path": str(
                        media_file.resolve()
                    ),
                    "_dynamic": True,
                }

                dynamic_source_index[
                    source_id
                ] = source

                children.append(source)

            return children

        nodes = scan_directory(
            disk_root,
            relative_root,
        )

        self.dynamic_sources.update(
            dynamic_source_index
        )

        return nodes

    def _public_node(
        self,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        node_type = node["node_type"]

        if node_type == "category":
            children = [
                self._public_node(child)
                for child in node.get("children", [])
            ]

            dynamic = node.get("dynamic")

            if dynamic is not None:
                dynamic_children = (
                    self._scan_media_directory(
                        node["id"],
                        dynamic,
                    )
                )

                children.extend(
                    self._public_node(child)
                    for child in dynamic_children
                )

            public_node = {
                "id": node["id"],
                "name": node.get(
                    "name",
                    node["id"],
                ),
                "node_type": "category",
                "children": children,
            }

            lazy_path = node.get("lazy_path")

            if lazy_path is not None:
                public_node["lazy_path"] = lazy_path

            return public_node

        playback = node["playback"]

        return {
            "id": node["id"],
            "name": node.get(
                "name",
                node["id"],
            ),
            "node_type": "source",
            "playback": {
                "type": playback["type"],
                "port": int(
                    playback.get(
                        "port",
                        DEFAULT_MEDIA_PORT,
                    )
                ),
                "path": playback["path"],
            },
        }

    def _refresh_dynamic_sources(
        self,
    ) -> None:
        self.dynamic_sources = {}

        def walk(
            node: dict[str, Any],
        ) -> None:
            if node["node_type"] != "category":
                return

            dynamic = node.get("dynamic")

            if dynamic is not None:
                self._scan_media_directory(
                    node["id"],
                    dynamic,
                )

            for child in node.get(
                "children",
                [],
            ):
                walk(child)

        for item in self.raw["root"]:
            walk(item)

    def get_source(
        self,
        source_id: str,
    ) -> dict[str, Any]:
        with self.lock:
            static_source = (
                self.static_sources.get(
                    source_id
                )
            )

            if static_source is not None:
                return static_source

            self._refresh_dynamic_sources()

            dynamic_source = (
                self.dynamic_sources.get(
                    source_id
                )
            )

            if dynamic_source is not None:
                return dynamic_source

        raise CatalogError(
            f"Unknown source: {source_id}"
        )

    def public_catalog(
        self,
    ) -> dict[str, Any]:
        with self.lock:
            self.dynamic_sources = {}

            return {
                "version": self.raw.get(
                    "version",
                    1,
                ),
                "root": [
                    self._public_node(item)
                    for item in self.raw["root"]
                ],
            }


class PrivyHubController:
    def __init__(self) -> None:
        self.lock = threading.RLock()

        MEDIA_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        LIVE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        LOG_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not SERVER_SCRIPT.exists():
            raise FileNotFoundError(
                f"Required server script not found: {SERVER_SCRIPT}"
            )

        self.catalog = SourceCatalog(
            CATALOG_FILE,
            MEDIA_ROOT,
        )

        self.server: Optional[ManagedProcess] = None
        self.source_process: Optional[ManagedProcess] = None
        self.active_source_id: Optional[str] = None

    @staticmethod
    def _running(
        item: Optional[ManagedProcess],
    ) -> bool:
        return (
            item is not None
            and item.process.poll() is None
        )

    @staticmethod
    def _close_log(
        item: Optional[ManagedProcess],
    ) -> None:
        if item is None:
            return

        try:
            item.log_handle.close()
        except Exception:
            pass

    def _launch_powershell(
        self,
        name: str,
        script: Path,
    ) -> ManagedProcess:
        script = script.resolve()

        if not script.exists():
            raise FileNotFoundError(
                f"PowerShell script not found: {script}"
            )

        log_path = (
            LOG_DIR / f"{name}.log"
        )

        log_handle = open(
            log_path,
            "a",
            encoding="utf-8",
            buffering=1,
        )

        log_handle.write("\n")
        log_handle.write("=" * 72 + "\n")
        log_handle.write(
            f"Starting PrivyHub process: {name}\n"
        )
        log_handle.write(
            f"Script: {script}\n"
        )
        log_handle.write("=" * 72 + "\n")
        log_handle.flush()

        creationflags = 0

        if os.name == "nt":
            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
            )

        try:
            process = subprocess.Popen(
                [
                    POWERSHELL,
                    "-NoLogo",
                    "-NoProfile",
                    "-File",
                    str(script),
                ],
                cwd=str(PROJECT_ROOT),
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
            )
        except Exception:
            log_handle.close()
            raise

        return ManagedProcess(
            name=name,
            process=process,
            log_handle=log_handle,
            log_path=log_path,
        )

    @staticmethod
    def _kill_process_tree(
        item: ManagedProcess,
    ) -> None:
        if item.process.poll() is not None:
            return

        if os.name == "nt":
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(item.process.pid),
                    "/T",
                    "/F",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            item.process.terminate()

        try:
            item.process.wait(
                timeout=5
            )
        except subprocess.TimeoutExpired:
            try:
                item.process.kill()
            except Exception:
                pass

    def start_server(
        self,
    ) -> None:
        with self.lock:
            if self._running(
                self.server
            ):
                return

            if self.server is not None:
                self._close_log(
                    self.server
                )
                self.server = None

            self.server = (
                self._launch_powershell(
                    "server",
                    SERVER_SCRIPT,
                )
            )

    def stop_server(
        self,
    ) -> None:
        with self.lock:
            if self.server is not None:
                self._kill_process_tree(
                    self.server
                )
                self._close_log(
                    self.server
                )
                self.server = None

    def stop_source(
        self,
    ) -> dict[str, Any]:
        with self.lock:
            if self.source_process is not None:
                self._kill_process_tree(
                    self.source_process
                )
                self._close_log(
                    self.source_process
                )

            self.source_process = None
            self.active_source_id = None

            return self.status()

    def _public_source(
        self,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        playback = source["playback"]

        return {
            "id": source["id"],
            "name": source.get(
                "name",
                source["id"],
            ),
            "playback": {
                "type": playback["type"],
                "port": int(
                    playback.get(
                        "port",
                        DEFAULT_MEDIA_PORT,
                    )
                ),
                "path": playback["path"],
            },
        }

    def _vod_is_healthy(
        self,
        source: dict[str, Any],
    ) -> bool:
        explicit_path = source.get(
            "_filesystem_path"
        )

        if explicit_path:
            media_file = Path(
                explicit_path
            ).resolve()
        else:
            playback_path = unquote(
                source["playback"]["path"]
            ).lstrip("/")

            media_file = (
                MEDIA_ROOT / playback_path
            ).resolve()

        try:
            media_file.relative_to(
                MEDIA_ROOT.resolve()
            )
        except ValueError:
            return False

        return (
            media_file.exists()
            and media_file.is_file()
            and media_file.stat().st_size > 0
        )

    def _hls_is_healthy(
        self,
        source: dict[str, Any],
    ) -> bool:
        playback = source["playback"]
        health = source.get(
            "health",
            {},
        )

        media_port = int(
            playback.get(
                "port",
                DEFAULT_MEDIA_PORT,
            )
        )

        media_path = playback["path"]

        playlist_url = (
            f"http://{MEDIA_HOST_FOR_HEALTH}:"
            f"{media_port}{media_path}"
        )

        request = urllib.request.Request(
            playlist_url,
            headers={
                "Cache-Control": "no-cache",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=HTTP_HEALTH_TIMEOUT_SECONDS,
            ) as response:
                if response.status != 200:
                    return False

                playlist = (
                    response
                    .read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ):
            return False

        if "#EXTM3U" not in playlist:
            return False

        if "#EXTINF:" not in playlist:
            return False

        segments = [
            line.strip()
            for line in playlist.splitlines()
            if line.strip().lower().endswith(
                ".ts"
            )
        ]

        min_segments = int(
            health.get(
                "min_segments",
                2,
            )
        )

        if len(segments) < min_segments:
            return False

        playlist_path = Path(
            urlparse(
                unquote(media_path)
            ).path
        )

        playlist_directory = (
            MEDIA_ROOT
            / playlist_path.parent
                .as_posix()
                .lstrip("/")
        ).resolve()

        try:
            playlist_directory.relative_to(
                MEDIA_ROOT.resolve()
            )
        except ValueError:
            return False

        for segment in segments[
            -min_segments:
        ]:
            segment_name = Path(
                urlparse(segment).path
            ).name

            segment_file = (
                playlist_directory
                / segment_name
            )

            if not segment_file.exists():
                return False

            if segment_file.stat().st_size <= 0:
                return False

        return True

    def _source_is_healthy(
        self,
        source: dict[str, Any],
    ) -> bool:
        playback_type = (
            source["playback"]["type"]
        )

        if playback_type == "vod":
            return self._vod_is_healthy(
                source
            )

        health_type = (
            source
            .get("health", {})
            .get(
                "type",
                "hls_local",
            )
        )

        if health_type == "hls_local":
            return self._hls_is_healthy(
                source
            )

        raise SourceStartError(
            f"Unsupported health check type: {health_type}"
        )

    def _wait_for_source(
        self,
        source: dict[str, Any],
        timeout_seconds: float,
    ) -> bool:
        deadline = (
            time.monotonic()
            + timeout_seconds
        )

        consecutive_ready = 0

        while time.monotonic() < deadline:
            with self.lock:
                source_process = (
                    self.source_process
                )

                if (
                    source_process is not None
                    and source_process.process.poll()
                    is not None
                ):
                    return False

            if self._source_is_healthy(
                source
            ):
                consecutive_ready += 1

                if consecutive_ready >= 2:
                    return True
            else:
                consecutive_ready = 0

            time.sleep(
                HEALTH_POLL_SECONDS
            )

        return False

    def _launch_source_process(
        self,
        source: dict[str, Any],
    ) -> None:
        runner = source.get(
            "runner"
        )

        if not isinstance(
            runner,
            dict,
        ):
            raise SourceStartError(
                f"Source {source['id']} has no runner"
            )

        runner_type = runner.get(
            "type"
        )

        if runner_type != "powershell":
            raise SourceStartError(
                f"Unsupported runner type: {runner_type}"
            )

        script_name = runner.get(
            "script"
        )

        if (
            not isinstance(
                script_name,
                str,
            )
            or not script_name
        ):
            raise SourceStartError(
                f"Source {source['id']} has no runner script"
            )

        script_path = (
            PROJECT_ROOT
            / script_name
        ).resolve()

        try:
            script_path.relative_to(
                PROJECT_ROOT.resolve()
            )
        except ValueError as exc:
            raise SourceStartError(
                f"Runner path escapes project root: {script_name}"
            ) from exc

        self.source_process = (
            self._launch_powershell(
                source["id"],
                script_path,
            )
        )

        self.active_source_id = (
            source["id"]
        )

    def start_source(
        self,
        source_id: str,
    ) -> dict[str, Any]:
        source = (
            self.catalog.get_source(
                source_id
            )
        )

        playback_type = (
            source["playback"]["type"]
        )

        with self.lock:
            self.start_server()
            self.stop_source()

        if playback_type == "vod":
            if not self._source_is_healthy(
                source
            ):
                raise SourceStartError(
                    f"VOD source is unavailable: {source_id}"
                )

            with self.lock:
                self.active_source_id = (
                    source_id
                )

            return {
                "ok": True,
                "ready": True,
                "attempts": 0,
                "source": self._public_source(
                    source
                ),
                "status": self.status(),
            }

        health = source.get(
            "health",
            {},
        )

        max_attempts = int(
            health.get(
                "max_attempts",
                2,
            )
        )

        first_timeout = float(
            health.get(
                "first_attempt_timeout_seconds",
                15,
            )
        )

        second_timeout = float(
            health.get(
                "second_attempt_timeout_seconds",
                30,
            )
        )

        last_reason = (
            "source did not become healthy"
        )

        for attempt in range(
            1,
            max_attempts + 1,
        ):
            with self.lock:
                self.stop_source()
                self._launch_source_process(
                    source
                )

            timeout_seconds = (
                first_timeout
                if attempt == 1
                else second_timeout
            )

            ready = self._wait_for_source(
                source,
                timeout_seconds,
            )

            if ready:
                return {
                    "ok": True,
                    "ready": True,
                    "attempts": attempt,
                    "source": self._public_source(
                        source
                    ),
                    "status": self.status(),
                }

            with self.lock:
                if (
                    self.source_process
                    is not None
                    and self.source_process
                        .process
                        .poll()
                    is not None
                ):
                    last_reason = (
                        "source process exited during startup"
                    )
                else:
                    last_reason = (
                        "source health check timed out"
                    )

                self.stop_source()

            if attempt < max_attempts:
                time.sleep(0.5)

        raise SourceStartError(
            f"Failed to start {source_id}: {last_reason}"
        )

    def shutdown(
        self,
    ) -> None:
        with self.lock:
            self.stop_source()
            self.stop_server()

    def status(
        self,
    ) -> dict[str, Any]:
        with self.lock:
            if (
                self.server is not None
                and not self._running(
                    self.server
                )
            ):
                self._close_log(
                    self.server
                )
                self.server = None

            if (
                self.source_process
                is not None
                and not self._running(
                    self.source_process
                )
            ):
                self._close_log(
                    self.source_process
                )
                self.source_process = None

                if (
                    self.active_source_id
                    is not None
                ):
                    active = (
                        self.catalog.get_source(
                            self.active_source_id
                        )
                    )

                    if (
                        active["playback"]["type"]
                        != "vod"
                    ):
                        self.active_source_id = None

            return {
                "service": "PrivyHub",
                "api_version": 4,
                "project_root": str(
                    PROJECT_ROOT
                ),
                "media_root": str(
                    MEDIA_ROOT
                ),
                "control_port": CONTROL_PORT,
                "server": {
                    "running": self._running(
                        self.server
                    ),
                    "pid": (
                        self.server.process.pid
                        if self._running(
                            self.server
                        )
                        else None
                    ),
                    "log": (
                        str(
                            self.server.log_path
                        )
                        if self.server
                        else None
                    ),
                },
                "active_source": {
                    "id": self.active_source_id,
                    "runner_running": self._running(
                        self.source_process
                    ),
                    "pid": (
                        self.source_process.process.pid
                        if self._running(
                            self.source_process
                        )
                        else None
                    ),
                    "log": (
                        str(
                            self.source_process.log_path
                        )
                        if self.source_process
                        else None
                    ),
                },
            }


CONTROLLER = PrivyHubController()


class PrivyHubRequestHandler(
    BaseHTTPRequestHandler
):
    server_version = "PrivyHubControl/0.6"

    def log_message(
        self,
        format: str,
        *args: Any,
    ) -> None:
        print(
            f"{self.client_address[0]} - "
            f"{self.log_date_time_string()} - "
            f"{format % args}"
        )

    def _send_json(
        self,
        status_code: int,
        payload: dict[str, Any],
    ) -> None:
        body = json.dumps(
            payload,
            indent=2,
        ).encode("utf-8")

        self.send_response(
            status_code
        )

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.end_headers()

        self.wfile.write(
            body
        )

    def do_GET(
        self,
    ) -> None:
        parsed = urlsplit(self.path)
        request_path = parsed.path

        if request_path == "/status":
            self._send_json(
                200,
                CONTROLLER.status(),
            )
            return

        if request_path == "/sources":
            self._send_json(
                200,
                CONTROLLER.catalog.public_catalog(),
            )
            return

        parts = [
            part
            for part in request_path.split("/")
            if part
        ]

        if (
            len(parts) == 3
            and parts[0] == "plugins"
        ):
            plugin_id = parts[1]
            action = parts[2]
            plugin = PLUGINS.get(plugin_id)

            if plugin is None:
                self._send_json(
                    404,
                    {
                        "ok": False,
                        "error": f"Unknown plugin: {plugin_id}",
                    },
                )
                return

            try:
                payload = plugin.handle(
                    action,
                    parsed.query,
                )
            except ValueError as exc:
                self._send_json(
                    400,
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                )
                return
            except RuntimeError as exc:
                self._send_json(
                    502,
                    {
                        "ok": False,
                        "error": str(exc),
                    },
                )
                return

            self._send_json(
                200,
                payload,
            )
            return

        self._send_json(
            404,
            {
                "ok": False,
                "error": "Not found",
            },
        )

    def do_POST(
        self,
    ) -> None:
        try:
            parsed = urlsplit(self.path)
            request_path = parsed.path

            parts = [
                part
                for part in request_path.split("/")
                if part
            ]

            if (
                len(parts) == 3
                and parts[0] == "plugins"
            ):
                plugin_id = parts[1]
                action = parts[2]
                plugin = PLUGINS.get(plugin_id)

                if plugin is None:
                    self._send_json(
                        404,
                        {
                            "ok": False,
                            "error": f"Unknown plugin: {plugin_id}",
                        },
                    )
                    return

                request_handler = getattr(
                    plugin,
                    "handle_post_request",
                    None,
                )

                handler = (
                    request_handler
                    or getattr(
                        plugin,
                        "handle_post",
                        None,
                    )
                )

                if handler is None:
                    self._send_json(
                        405,
                        {
                            "ok": False,
                            "error": f"Plugin does not support POST: {plugin_id}",
                        },
                    )
                    return

                try:
                    if request_handler is not None:
                        payload = request_handler(
                            action,
                            parsed.query,
                            self.client_address[0],
                        )
                    else:
                        payload = handler(
                            action,
                            parsed.query,
                        )
                except ValueError as exc:
                    self._send_json(
                        400,
                        {
                            "ok": False,
                            "error": str(exc),
                        },
                    )
                    return
                except RuntimeError as exc:
                    self._send_json(
                        503,
                        {
                            "ok": False,
                            "error": str(exc),
                        },
                    )
                    return

                self._send_json(
                    200,
                    payload,
                )
                return

            if self.path == "/stop":
                status = (
                    CONTROLLER.stop_source()
                )

                self._send_json(
                    200,
                    {
                        "ok": True,
                        "action": "stop",
                        "status": status,
                    },
                )
                return

            prefix = "/sources/"
            suffix = "/start"

            if (
                self.path.startswith(
                    prefix
                )
                and self.path.endswith(
                    suffix
                )
            ):
                source_id = (
                    self.path[
                        len(prefix):
                        -len(suffix)
                    ]
                    .strip("/")
                )

                if not source_id:
                    raise CatalogError(
                        "Missing source id"
                    )

                result = (
                    CONTROLLER.start_source(
                        source_id
                    )
                )

                self._send_json(
                    200,
                    result,
                )
                return

            self._send_json(
                404,
                {
                    "ok": False,
                    "error": "Not found",
                },
            )

        except CatalogError as exc:
            self._send_json(
                404,
                {
                    "ok": False,
                    "error": str(exc),
                },
            )

        except SourceStartError as exc:
            self._send_json(
                503,
                {
                    "ok": False,
                    "error": str(exc),
                    "status": CONTROLLER.status(),
                },
            )

        except Exception as exc:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": str(exc),
                    "status": CONTROLLER.status(),
                },
            )


def main(
) -> None:
    print(
        "PrivyHub companion service"
    )

    print(
        f"Project root: {PROJECT_ROOT}"
    )

    print(
        f"Media root:   {MEDIA_ROOT}"
    )

    print(
        f"Catalog:      {CATALOG_FILE}"
    )

    print(
        f"Control API:  "
        f"http://127.0.0.1:{CONTROL_PORT}"
    )

    print("")

    print(
        "Dynamic media directories are "
        "rescanned on GET /sources."
    )

    print("")

    print("Endpoints:")
    print("  GET  /status")
    print("  GET  /sources")
    print("  GET  /plugins/<plugin>/<action>")
    print("  POST /sources/<id>/start")
    print("  POST /stop")

    print("")

    print(
        f"Logs: {LOG_DIR}"
    )

    print("")

    print(
        "Starting the PrivyHub media server..."
    )

    CONTROLLER.start_server()

    httpd = ThreadingHTTPServer(
        (
            CONTROL_HOST,
            CONTROL_PORT,
        ),
        PrivyHubRequestHandler,
    )

    print(
        f"Listening on "
        f"{CONTROL_HOST}:{CONTROL_PORT}"
    )

    print(
        "Stop with Ctrl+C."
    )

    print("")

    try:
        httpd.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nStopping PrivyHub companion service..."
        )

    finally:
        httpd.server_close()

        # PRIVYHUB_A4_PLUGIN_LIFECYCLE_SHUTDOWN_V1
        # Plugin-owned child processes must be stopped before the companion
        # process exits. Games reuses its validated POST stop lifecycle.
        plugin_shutdown_errors = shutdown_plugins()

        for plugin_error in plugin_shutdown_errors:
            print(
                "Plugin shutdown warning: "
                + plugin_error
            )

        CONTROLLER.shutdown()

        print(
            "PrivyHub companion service stopped."
        )


if __name__ == "__main__":
    main()
