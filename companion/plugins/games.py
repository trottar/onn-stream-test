from __future__ import annotations

import hashlib
import threading
import time

from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode

from games.emulator_manager import EmulatorError, EmulatorManager
from games.stream_manager import StreamHostError, StreamManager
from games.decoder_session_log import write_decoder_session_log
from native_stream import NativeStreamError, NativeStreamManager


class GamesPlugin:
    """Trusted-local, catalog-only Games plugin for PrivyHub."""

    PLUGIN_ID = "games"
    PAGE_SIZE = 80
    CACHE_SECONDS = 5.0
    MAX_GAMES = 10_000

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    GAMES_ROOT = PROJECT_ROOT / "games"

    SYSTEMS = {
        "nes": {
            "name": "NES",
            "folder": "nes",
            "extensions": {".nes"},
        },
        "snes": {
            "name": "SNES",
            "folder": "snes",
            "extensions": {".sfc", ".smc"},
        },
        "genesis": {
            "name": "Genesis",
            "folder": "genesis",
            "extensions": {".md", ".gen", ".bin"},
        },
        "ps1": {
            "name": "PlayStation",
            "folder": "ps1",
            "extensions": {".chd", ".cue", ".m3u", ".iso"},
        },
    }

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cached_at = 0.0
        self._cached_games: list[dict[str, Any]] = []
        self._emulator = EmulatorManager(
            self.PROJECT_ROOT
        )
        self._stream = StreamManager(
            self.PROJECT_ROOT
        )
        self._native_stream = NativeStreamManager(
            self.PROJECT_ROOT
        )

    @staticmethod
    def _clean_name(path: Path) -> str:
        name = path.stem.replace("_", " ").strip()
        if not name:
            return path.name

        cleaned = " ".join(name.split())
        letters = [char for char in cleaned if char.isalpha()]

        if letters and (
            all(char.islower() for char in letters)
            or all(char.isupper() for char in letters)
        ):
            cleaned = cleaned.title()

        return cleaned

    @staticmethod
    def _stable_id(system: str, relative_path: str) -> str:
        normalized = relative_path.replace("\\", "/").casefold()
        digest = hashlib.sha1(
            f"{system}:{normalized}".encode("utf-8")
        ).hexdigest()[:16]
        return f"game_{system}_{digest}"

    @staticmethod
    def _first(
        query: dict[str, list[str]],
        key: str,
        default: str = "",
    ) -> str:
        values = query.get(key)
        return values[0] if values else default

    @staticmethod
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _lazy_category(
        node_id: str,
        name: str,
        lazy_path: str,
    ) -> dict[str, Any]:
        return {
            "id": node_id,
            "name": name,
            "node_type": "category",
            "children": [],
            "lazy_path": lazy_path,
        }

    @staticmethod
    def _safe_relative(
        file_path: Path,
        root: Path,
    ) -> str | None:
        try:
            resolved = file_path.resolve()
            relative = resolved.relative_to(root.resolve())
        except (OSError, ValueError):
            return None

        return relative.as_posix()

    @staticmethod
    def _m3u_references(
        playlist: Path,
        system_root: Path,
    ) -> set[Path]:
        references: set[Path] = set()

        try:
            text = playlist.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            return references

        for raw in text.splitlines():
            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            candidate = (playlist.parent / line).resolve()

            try:
                candidate.relative_to(system_root.resolve())
            except (OSError, ValueError):
                continue

            if candidate.is_file():
                references.add(candidate)

        return references

    def _scan(self) -> list[dict[str, Any]]:
        now = time.monotonic()

        with self._lock:
            if (
                self._cached_games
                and now - self._cached_at < self.CACHE_SECONDS
            ):
                return list(self._cached_games)

        self.GAMES_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        games: list[dict[str, Any]] = []

        for system_id, config in self.SYSTEMS.items():
            system_root = (
                self.GAMES_ROOT / str(config["folder"])
            )
            system_root.mkdir(
                parents=True,
                exist_ok=True,
            )

            extensions = {
                str(extension).casefold()
                for extension in config["extensions"]
            }

            files = sorted(
                (
                    item
                    for item in system_root.rglob("*")
                    if item.is_file()
                    and not item.name.startswith(".")
                    and item.suffix.casefold() in extensions
                ),
                key=lambda item: str(item).casefold(),
            )

            represented_files: set[Path] = set()

            if system_id == "ps1":
                for item in files:
                    if item.suffix.casefold() == ".m3u":
                        represented_files.update(
                            self._m3u_references(
                                item,
                                system_root,
                            )
                        )

            for item in files:
                resolved = item.resolve()

                if (
                    resolved in represented_files
                    and item.suffix.casefold() != ".m3u"
                ):
                    continue

                relative_inside_system = self._safe_relative(
                    item,
                    system_root,
                )

                if relative_inside_system is None:
                    continue

                project_relative = (
                    Path("games")
                    / str(config["folder"])
                    / relative_inside_system
                ).as_posix()

                try:
                    size_bytes = item.stat().st_size
                except OSError:
                    size_bytes = 0

                games.append(
                    {
                        "id": self._stable_id(
                            system_id,
                            project_relative,
                        ),
                        "title": self._clean_name(item),
                        "system": system_id,
                        "system_name": str(config["name"]),
                        "relative_path": project_relative,
                        "format": item.suffix.casefold().lstrip("."),
                        "size_bytes": size_bytes,
                    }
                )

                if len(games) >= self.MAX_GAMES:
                    break

            if len(games) >= self.MAX_GAMES:
                break

        games.sort(
            key=lambda item: (
                str(item["system_name"]).casefold(),
                str(item["title"]).casefold(),
                str(item["relative_path"]).casefold(),
            )
        )

        with self._lock:
            self._cached_at = now
            self._cached_games = games

        return list(games)

    def systems(self) -> dict[str, Any]:
        games = self._scan()
        counts = {
            system_id: 0
            for system_id in self.SYSTEMS
        }

        for game in games:
            counts[str(game["system"])] += 1

        nodes = [
            {
                "id": "games_session_status",
                "name": "Game Session",
                "node_type": "game",
                "lazy_path": f"/plugins/{self.PLUGIN_ID}/status",
            },
            {
                "id": "games_stream_host",
                "name": "Streaming Host",
                "node_type": "game",
                "lazy_path": f"/plugins/{self.PLUGIN_ID}/stream-status",
            },
            {
                "id": "games_native_stream",
                "name": "Native Streaming Alpha",
                "node_type": "game",
                "lazy_path": f"/plugins/{self.PLUGIN_ID}/native-stream-status",
            },
        ]

        for system_id, config in self.SYSTEMS.items():
            params = urlencode(
                {"system": system_id}
            )
            nodes.append(
                self._lazy_category(
                    node_id=f"games_system_{system_id}",
                    name=f"{config['name']} ({counts[system_id]})",
                    lazy_path=(
                        f"/plugins/{self.PLUGIN_ID}/games?"
                        f"{params}"
                    ),
                )
            )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "games_root": str(self.GAMES_ROOT),
            "total": len(games),
            "nodes": nodes,
        }

    def games(
        self,
        query: dict[str, list[str]],
    ) -> dict[str, Any]:
        system_id = (
            self._first(query, "system")
            .strip()
            .casefold()
        )

        if system_id not in self.SYSTEMS:
            raise ValueError("Missing or invalid game system")

        matching = [
            game
            for game in self._scan()
            if game["system"] == system_id
        ]

        offset_text = self._first(query, "offset")
        offset_supplied = bool(offset_text)
        offset = max(
            0,
            self._parse_int(offset_text, 0),
        )

        limit = self._parse_int(
            self._first(query, "limit"),
            self.PAGE_SIZE,
        )
        limit = min(
            max(1, limit),
            self.PAGE_SIZE,
        )

        if (
            not offset_supplied
            and len(matching) > self.PAGE_SIZE
        ):
            nodes = []
            page = 1

            for start in range(
                0,
                len(matching),
                self.PAGE_SIZE,
            ):
                end = min(
                    start + self.PAGE_SIZE,
                    len(matching),
                )
                params = urlencode(
                    {
                        "system": system_id,
                        "offset": start,
                        "limit": self.PAGE_SIZE,
                    }
                )
                nodes.append(
                    self._lazy_category(
                        node_id=f"games_{system_id}_page_{page:02d}",
                        name=f"Page {page:02d} ({start + 1}-{end})",
                        lazy_path=(
                            f"/plugins/{self.PLUGIN_ID}/games?"
                            f"{params}"
                        ),
                    )
                )
                page += 1

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "system": system_id,
                "system_name": self.SYSTEMS[system_id]["name"],
                "total": len(matching),
                "nodes": nodes,
            }

        selected = matching[
            offset: offset + limit
        ]

        nodes = [
            {
                "id": str(game["id"]),
                "name": str(game["title"]),
                "node_type": "game",
                "lazy_path": (
                    f"/plugins/{self.PLUGIN_ID}/details?"
                    + urlencode({"id": str(game["id"])})
                ),
            }
            for game in selected
        ]

        if not nodes:
            empty_id = f"games_empty_{system_id}"
            nodes.append(
                {
                    "id": empty_id,
                    "name": (
                        "No games found — add files under "
                        f"games/{self.SYSTEMS[system_id]['folder']}/"
                    ),
                    "node_type": "game",
                    "lazy_path": (
                        f"/plugins/{self.PLUGIN_ID}/details?"
                        + urlencode({"id": empty_id})
                    ),
                }
            )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "system": system_id,
            "system_name": self.SYSTEMS[system_id]["name"],
            "total": len(matching),
            "offset": offset,
            "count": len(selected),
            "nodes": nodes,
        }

    def details(
        self,
        query: dict[str, list[str]],
    ) -> dict[str, Any]:
        game_id = self._first(
            query,
            "id",
        ).strip()

        if not game_id:
            raise ValueError("Missing game id")

        if game_id.startswith("games_empty_"):
            system_id = game_id.removeprefix(
                "games_empty_"
            )
            config = self.SYSTEMS.get(system_id)

            if config is None:
                raise ValueError("Unknown game id")

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "id": game_id,
                "title": "No games found",
                "system": system_id,
                "system_name": str(config["name"]),
                "relative_path": f"games/{config['folder']}/",
                "format": "",
                "size_bytes": 0,
                "catalog_only": True,
                "message": (
                    "Add supported game files to this folder on the "
                    "companion, then reopen Games."
                ),
            }

        game = next(
            (
                item
                for item in self._scan()
                if item["id"] == game_id
            ),
            None,
        )

        if game is None:
            raise ValueError("Unknown game id")

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            **game,
            "catalog_only": True,
            "message": (
                "PrivyHub can launch this game on the companion. "
                "Streaming uses the optional project-managed Sunshine host."
            ),
        }

    def handle(
        self,
        action: str,
        raw_query: str,
    ) -> dict[str, Any]:
        query = parse_qs(
            raw_query,
            keep_blank_values=False,
        )

        if action == "systems":
            return self.systems()

        if action == "games":
            return self.games(query)

        if action == "details":
            return self.details(query)

        if action == "status":
            payload = self._emulator.status()
            payload["stream_host"] = self._stream.status()
            payload["native_stream"] = self._native_stream.status()
            return payload

        if action == "stream-status":
            return self._stream.status()

        if action == "native-stream-status":
            return self._native_stream.status()

        raise ValueError(
            f"Unknown Games plugin action: {action}"
        )

    def _find_game_by_id(
        self,
        game_id: str,
    ) -> dict[str, Any]:
        game = next(
            (
                item
                for item in self._scan()
                if item["id"] == game_id
            ),
            None,
        )

        if game is None:
            raise ValueError("Unknown game id")

        return game

    def handle_post_request(
        self,
        action: str,
        raw_query: str,
        client_ip: str,
    ) -> dict[str, Any]:
        query = parse_qs(
            raw_query,
            keep_blank_values=False,
        )

        if action == "native-stream-start":
            game_status = self._emulator.status()

            if not game_status.get("active", False):
                raise RuntimeError(
                    "Launch a game before starting Native Video Alpha."
                )

            port = self._parse_int(
                self._first(
                    query,
                    "port",
                ),
                NativeStreamManager.DEFAULT_PORT,
            )

            try:
                return self._native_stream.start(
                    client_ip=client_ip,
                    port=port,
                )
            except NativeStreamError as exc:
                raise RuntimeError(str(exc)) from exc

        if action == "native-stream-stop":
            try:
                return self._native_stream.stop()
            except NativeStreamError as exc:
                raise RuntimeError(str(exc)) from exc

        return self.handle_post(
            action,
            raw_query,
        )

    def handle_post(
        self,
        action: str,
        raw_query: str,
    ) -> dict[str, Any]:
        query = parse_qs(
            raw_query,
            keep_blank_values=False,
        )

        try:
            if action == "decoder-session-log":
                report = self._first(
                    query,
                    "report",
                ).strip()

                return write_decoder_session_log(
                    self.PROJECT_ROOT,
                    report,
                )

            if action == "launch":
                game_id = self._first(
                    query,
                    "id",
                ).strip()

                if not game_id:
                    raise ValueError("Missing game id")

                game = self._find_game_by_id(
                    game_id
                )

                stream_warning = None

                try:
                    self._stream.ensure_running()
                except StreamHostError as exc:
                    # Streaming remains modular. A host setup problem must
                    # never break the already-proven local emulator launch.
                    stream_warning = str(exc)

                payload = self._emulator.launch(
                    game
                )
                payload["stream_host"] = self._stream.status()
                payload["stream_warning"] = stream_warning

                return payload

            if action == "stop":
                payload = self._emulator.stop()
                payload["stream_host"] = self._stream.status()
                return payload

            if action == "stream-start":
                return self._stream.start()

            if action == "stream-stop":
                return self._stream.stop()

        except (EmulatorError, StreamHostError) as exc:
            raise RuntimeError(str(exc)) from exc

        raise ValueError(
            f"Unknown Games plugin POST action: {action}"
        )
