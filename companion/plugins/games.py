from __future__ import annotations

import hashlib
import json
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
    LIBRARY_STATE_PATH = (
        PROJECT_ROOT
        / "data"
        / "games"
        / "library_state.json"
    )
    SAVE_STATE_INDEX_PATH = (
        PROJECT_ROOT
        / "data"
        / "games"
        / "retroarch"
        / "privyhub_state_slots.json"
    )

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
        self._emulator.set_hotkey_sender(
            self._native_stream.retroarch_hotkey
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

    # PrivyHub Phase A6: companion-owned library state.
    @staticmethod
    def _nonnegative_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return max(
                0,
                int(value),
            )
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _game_state_key(
        game: dict[str, Any],
    ) -> str:
        return (
            str(
                game.get(
                    "system",
                    "",
                )
            ).casefold()
            + "::"
            + str(
                game.get(
                    "relative_path",
                    "",
                )
            ).casefold()
        )

    @staticmethod
    def _empty_library_state() -> dict[str, Any]:
        return {
            "schema": 1,
            "games": {},
        }

    def _read_library_state(
        self,
    ) -> dict[str, Any]:
        path = self.LIBRARY_STATE_PATH

        if not path.is_file():
            return self._empty_library_state()

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8-sig"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return self._empty_library_state()

        if not isinstance(
            payload,
            dict,
        ):
            return self._empty_library_state()

        games = payload.get(
            "games",
            {},
        )

        if not isinstance(
            games,
            dict,
        ):
            games = {}

        return {
            "schema": 1,
            "games": games,
        }

    def _write_library_state(
        self,
        payload: dict[str, Any],
    ) -> None:
        path = self.LIBRARY_STATE_PATH

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = path.with_name(
            path.name
            + ".tmp"
        )

        try:
            temporary.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            temporary.replace(
                path
            )

        except OSError as exc:
            try:
                temporary.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

            raise RuntimeError(
                "Unable to update game library state: "
                f"{exc}"
            ) from exc

    def _read_save_state_index(
        self,
    ) -> dict[str, Any]:
        path = self.SAVE_STATE_INDEX_PATH

        if not path.is_file():
            return {
                "schema": 1,
                "games": {},
            }

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8-sig"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {
                "schema": 1,
                "games": {},
            }

        if not isinstance(
            payload,
            dict,
        ):
            return {
                "schema": 1,
                "games": {},
            }

        games = payload.get(
            "games",
            {},
        )

        if not isinstance(
            games,
            dict,
        ):
            games = {}

        return {
            "schema": 1,
            "games": games,
        }

    def _continue_state_timestamp(
        self,
        game: dict[str, Any],
        state_games: dict[str, Any],
    ) -> int:
        entry = state_games.get(
            self._game_state_key(
                game
            )
        )

        if not isinstance(
            entry,
            dict,
        ):
            return 0

        slots = entry.get(
            "slots",
            {},
        )

        if not isinstance(
            slots,
            dict,
        ):
            return 0

        latest = 0

        for raw_slot in slots.values():
            if not isinstance(
                raw_slot,
                dict,
            ):
                continue

            size_bytes = self._nonnegative_int(
                raw_slot.get(
                    "size_bytes",
                    0,
                )
            )

            state_file = str(
                raw_slot.get(
                    "state_file",
                    "",
                )
            ).strip()

            if (
                size_bytes <= 0
                or not state_file
            ):
                continue

            candidate = (
                self.PROJECT_ROOT
                / state_file
            ).resolve()

            try:
                candidate.relative_to(
                    self.PROJECT_ROOT.resolve()
                )
            except ValueError:
                continue

            try:
                if (
                    not candidate.is_file()
                    or candidate.stat().st_size <= 0
                ):
                    continue
            except OSError:
                continue

            latest = max(
                latest,
                self._nonnegative_int(
                    raw_slot.get(
                        "modified_unix_ms",
                        0,
                    )
                ),
            )

        return latest

    # PrivyHub Phase A6.2: search and explicit player metadata.
    # PrivyHub Phase A6 box art: local-first stable artwork cache.
    @staticmethod
    def _box_art_extensions(
    ) -> tuple[str, ...]:
        return (
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        )

    def _box_art_cache_root(
        self,
    ) -> Path:
        return (
            self.PROJECT_ROOT
            / "media"
            / "games"
            / "box_art"
        )

    def _box_art_manual_relative_path(
        self,
        game: dict[str, Any],
    ) -> str:
        return (
            Path("media")
            / "games"
            / "box_art"
            / (
                str(
                    game.get(
                        "id",
                        "game",
                    )
                )
                + ".png"
            )
        ).as_posix()

    def _box_art_sidecar_hint(
        self,
        game: dict[str, Any],
    ) -> str:
        relative = Path(
            str(
                game.get(
                    "relative_path",
                    "",
                )
            )
        )

        if not relative.name:
            return ""

        return relative.with_name(
            relative.stem
            + ".cover.png"
        ).as_posix()

    def _resolve_box_art(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        game_id = str(
            game.get(
                "id",
                "",
            )
        ).strip()

        result = {
            "box_art_available": False,
            "artwork_path": "",
            "box_art_source": "",
            "box_art_manual_path": (
                self._box_art_manual_relative_path(
                    game
                )
            ),
            "box_art_sidecar_hint": (
                self._box_art_sidecar_hint(
                    game
                )
            ),
        }

        if (
            not game_id
            or not all(
                character.isalnum()
                or character in {"_", "-"}
                for character in game_id
            )
        ):
            return result

        cache_root = (
            self._box_art_cache_root()
        )

        extensions = (
            self._box_art_extensions()
        )

        for extension in extensions:
            candidate = (
                cache_root
                / (
                    game_id
                    + extension
                )
            )

            try:
                if (
                    candidate.is_file()
                    and candidate.stat().st_size > 0
                ):
                    return {
                        **result,
                        "box_art_available": True,
                        "artwork_path": (
                            "/games/box_art/"
                            + candidate.name
                        ),
                        "box_art_source": (
                            "stable_cache"
                        ),
                    }
            except OSError:
                continue

        raw_relative = str(
            game.get(
                "relative_path",
                "",
            )
        ).strip()

        if not raw_relative:
            return result

        game_path = (
            self.PROJECT_ROOT
            / raw_relative
        ).resolve()

        try:
            game_path.relative_to(
                self.GAMES_ROOT.resolve()
            )
        except (
            OSError,
            ValueError,
        ):
            return result

        sidecars: list[Path] = []

        for extension in extensions:
            sidecars.extend(
                [
                    game_path.with_name(
                        game_path.stem
                        + ".cover"
                        + extension
                    ),
                    game_path.with_name(
                        game_path.stem
                        + extension
                    ),
                ]
            )

        sidecar: Path | None = None

        for candidate in sidecars:
            try:
                if (
                    candidate.is_file()
                    and candidate.stat().st_size > 0
                ):
                    sidecar = candidate
                    break
            except OSError:
                continue

        if sidecar is None:
            return result

        extension = (
            sidecar.suffix.casefold()
        )

        if extension not in extensions:
            return result

        destination = (
            cache_root
            / (
                game_id
                + extension
            )
        )

        temporary: Path | None = None

        try:
            cache_root.mkdir(
                parents=True,
                exist_ok=True,
            )

            source_stat = (
                sidecar.stat()
            )

            copy_needed = True

            try:
                destination_stat = (
                    destination.stat()
                )

                copy_needed = (
                    destination_stat.st_size
                    != source_stat.st_size
                    or destination_stat.st_mtime_ns
                    < source_stat.st_mtime_ns
                )

            except OSError:
                copy_needed = True

            if copy_needed:
                temporary = (
                    destination.with_name(
                        destination.name
                        + ".tmp"
                    )
                )

                __import__(
                    "shutil"
                ).copy2(
                    sidecar,
                    temporary,
                )

                temporary.replace(
                    destination
                )

            if (
                destination.is_file()
                and destination.stat().st_size > 0
            ):
                return {
                    **result,
                    "box_art_available": True,
                    "artwork_path": (
                        "/games/box_art/"
                        + destination.name
                    ),
                    "box_art_source": (
                        "sidecar_cache"
                    ),
                }

        except OSError:
            if temporary is not None:
                try:
                    temporary.unlink(
                        missing_ok=True
                    )
                except OSError:
                    pass

        return result

# PrivyHub Phase A6.4: enrich Patch 05 artwork records from metadata.json.
    def _read_game_metadata(
        self,
    ) -> dict[str, Any]:
        path = (
            self.PROJECT_ROOT
            / "data"
            / "games"
            / "metadata.json"
        )

        if not path.is_file():
            return {
                "schema_version": 1,
                "games": {},
            }

        try:
            payload = json.loads(
                path.read_text(
                    encoding="utf-8-sig"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return {
                "schema_version": 1,
                "games": {},
            }

        if not isinstance(
            payload,
            dict,
        ):
            return {
                "schema_version": 1,
                "games": {},
            }

        games = payload.get(
            "games",
            {},
        )

        if not isinstance(
            games,
            dict,
        ):
            games = {}

        return {
            "schema_version": (
                self._nonnegative_int(
                    payload.get(
                        "schema_version",
                        1,
                    ),
                    1,
                )
            ),
            "games": games,
        }
    def _decorate_game(
        self,
        game: dict[str, Any],
        library_games: dict[str, Any],
        state_games: dict[str, Any],
        metadata_games: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        game_id = str(
            game.get(
                "id",
                "",
            )
        )

        entry = library_games.get(
            game_id
        )

        if not isinstance(
            entry,
            dict,
        ):
            entry = {}

        if metadata_games is None:
            metadata_games = (
                self._read_game_metadata()[
                    "games"
                ]
            )

        metadata_entry = (
            metadata_games.get(
                game_id
            )
        )

        if not isinstance(
            metadata_entry,
            dict,
        ):
            metadata_entry = {}

        match = metadata_entry.get(
            "match",
            {},
        )

        if not isinstance(
            match,
            dict,
        ):
            match = {}

        metadata_available = (
            str(
                match.get(
                    "status",
                    "",
                )
            ).casefold()
            == "matched"
        )

        metadata = match.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        canonical_title = (
            str(
                match.get(
                    "canonical_title",
                    "",
                )
            ).strip()
            if metadata_available
            else ""
        )

        max_players = (
            self._nonnegative_int(
                metadata.get(
                    "max_players",
                    0,
                )
            )
            if metadata_available
            else 0
        )

        suggested_mode = (
            str(
                metadata.get(
                    "player_mode_suggested",
                    "",
                )
            ).strip().casefold()
            if metadata_available
            else ""
        )

        if suggested_mode not in {
            "single",
            "multi",
        }:
            suggested_mode = (
                "single"
                if max_players == 1
                else (
                    "multi"
                    if max_players > 1
                    else ""
                )
            )

        manual_mode = str(
            entry.get(
                "player_mode",
                "",
            )
        ).strip().casefold()

        if manual_mode not in {
            "single",
            "multi",
        }:
            manual_mode = ""

        player_mode = (
            manual_mode
            or suggested_mode
            or "unknown"
        )

        player_mode_source = (
            "manual"
            if manual_mode
            else (
                "metadata"
                if suggested_mode
                else "unknown"
            )
        )

        continue_timestamp = (
            self._continue_state_timestamp(
                game,
                state_games,
            )
        )

        box_art = (
            self._resolve_box_art(
                game
            )
        )

        return {
            **game,
            **box_art,
            "metadata_available": (
                metadata_available
            ),
            "metadata_provider": (
                str(
                    match.get(
                        "provider",
                        "",
                    )
                )
                if metadata_available
                else ""
            ),
            "metadata_match_method": (
                str(
                    match.get(
                        "method",
                        "",
                    )
                )
                if metadata_available
                else ""
            ),
            "canonical_title": (
                canonical_title
            ),
            "region": (
                str(
                    metadata.get(
                        "region",
                        "",
                    )
                ).strip()
                if metadata_available
                else ""
            ),
            "developer": (
                str(
                    metadata.get(
                        "developer",
                        "",
                    )
                ).strip()
                if metadata_available
                else ""
            ),
            "publisher": (
                str(
                    metadata.get(
                        "publisher",
                        "",
                    )
                ).strip()
                if metadata_available
                else ""
            ),
            "genre": (
                str(
                    metadata.get(
                        "genre",
                        "",
                    )
                ).strip()
                if metadata_available
                else ""
            ),
            "release_year": (
                self._nonnegative_int(
                    metadata.get(
                        "release_year",
                        0,
                    )
                )
                if metadata_available
                else 0
            ),
            "max_players": (
                max_players
            ),
            "player_mode_suggested": (
                suggested_mode
                or "unknown"
            ),
            "player_mode_source": (
                player_mode_source
            ),
            "favorite": bool(
                entry.get(
                    "favorite",
                    False,
                )
            ),
            "last_played_unix_ms": (
                self._nonnegative_int(
                    entry.get(
                        "last_played_unix_ms",
                        0,
                    )
                )
            ),
            "play_count": (
                self._nonnegative_int(
                    entry.get(
                        "play_count",
                        0,
                    )
                )
            ),
            "player_mode": (
                player_mode
            ),
            "continue_available": (
                continue_timestamp > 0
            ),
            "continue_modified_unix_ms": (
                continue_timestamp
            ),
        }

    def _annotated_games(
        self,
    ) -> list[dict[str, Any]]:
        games = self._scan()
        library = self._read_library_state()
        state_index = (
            self._read_save_state_index()
        )
        metadata_index = (
            self._read_game_metadata()
        )

        library_games = library[
            "games"
        ]
        state_games = state_index[
            "games"
        ]
        metadata_games = metadata_index[
            "games"
        ]

        return [
            self._decorate_game(
                game,
                library_games,
                state_games,
                metadata_games,
            )
            for game in games
        ]

    def _toggle_favorite(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            payload = (
                self._read_library_state()
            )
            games = payload[
                "games"
            ]

            game_id = str(
                game["id"]
            )

            entry = games.get(
                game_id
            )

            if not isinstance(
                entry,
                dict,
            ):
                entry = {}

            entry = dict(
                entry
            )

            entry["favorite"] = not bool(
                entry.get(
                    "favorite",
                    False,
                )
            )

            games[
                game_id
            ] = entry

            payload[
                "games"
            ] = games

            self._write_library_state(
                payload
            )

            state_games = (
                self._read_save_state_index()[
                    "games"
                ]
            )

            return self._decorate_game(
                game,
                games,
                state_games,
            )

    def _set_player_mode(
        self,
        game: dict[str, Any],
        mode: str,
    ) -> dict[str, Any]:
        normalized = str(
            mode
        ).strip().casefold()

        if normalized not in {
            "unknown",
            "single",
            "multi",
        }:
            raise ValueError(
                "Invalid player mode"
            )

        with self._lock:
            payload = (
                self._read_library_state()
            )
            games = payload[
                "games"
            ]

            game_id = str(
                game["id"]
            )

            entry = games.get(
                game_id
            )

            if not isinstance(
                entry,
                dict,
            ):
                entry = {}

            entry = dict(
                entry
            )

            if normalized == "unknown":
                entry.pop(
                    "player_mode",
                    None,
                )
            else:
                entry[
                    "player_mode"
                ] = normalized

            if entry:
                games[
                    game_id
                ] = entry
            else:
                games.pop(
                    game_id,
                    None,
                )

            payload[
                "games"
            ] = games

            self._write_library_state(
                payload
            )

            state_games = (
                self._read_save_state_index()[
                    "games"
                ]
            )

            return self._decorate_game(
                game,
                games,
                state_games,
            )

    def _record_game_launch(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            payload = (
                self._read_library_state()
            )
            games = payload[
                "games"
            ]

            game_id = str(
                game["id"]
            )

            entry = games.get(
                game_id
            )

            if not isinstance(
                entry,
                dict,
            ):
                entry = {}

            entry = dict(
                entry
            )

            entry[
                "last_played_unix_ms"
            ] = int(
                time.time()
                * 1000.0
            )

            entry[
                "play_count"
            ] = (
                self._nonnegative_int(
                    entry.get(
                        "play_count",
                        0,
                    )
                )
                + 1
            )

            games[
                game_id
            ] = entry

            payload[
                "games"
            ] = games

            self._write_library_state(
                payload
            )

            state_games = (
                self._read_save_state_index()[
                    "games"
                ]
            )

            return self._decorate_game(
                game,
                games,
                state_games,
            )

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
        games = self._annotated_games()

        counts = {
            system_id: 0
            for system_id in self.SYSTEMS
        }

        for game in games:
            counts[
                str(
                    game["system"]
                )
            ] += 1

        favorite_count = sum(
            1
            for game in games
            if bool(
                game.get(
                    "favorite",
                    False,
                )
            )
        )

        recent_count = sum(
            1
            for game in games
            if self._nonnegative_int(
                game.get(
                    "last_played_unix_ms",
                    0,
                )
            )
            > 0
        )

        saved_count = sum(
            1
            for game in games
            if bool(
                game.get(
                    "continue_available",
                    False,
                )
            )
        )

        single_count = sum(
            1
            for game in games
            if game.get(
                "player_mode"
            ) == "single"
        )

        multi_count = sum(
            1
            for game in games
            if game.get(
                "player_mode"
            ) == "multi"
        )

        # PrivyHub Phase A3 pause/resume session routing
        game_status = self._emulator.status()

        session_name = (
            "Resume Playing"
            if (
                game_status.get(
                    "active",
                    False,
                )
                and game_status.get(
                    "paused",
                    False,
                )
            )
            else "Game Session"
        )

        nodes = [
            {
                "id": "games_session_status",
                "name": session_name,
                "node_type": "game",
                "lazy_path": (
                    f"/plugins/{self.PLUGIN_ID}/status"
                ),
            },
            self._lazy_category(
                node_id=(
                    "games_continue"
                ),
                name=(
                    "Continue Playing "
                    f"({recent_count})"
                ),
                lazy_path=(
                    f"/plugins/{self.PLUGIN_ID}/games?"
                    + urlencode(
                        {
                            "view": "recent",
                        }
                    )
                ),
            ),
            self._lazy_category(
                node_id=(
                    "games_favorites"
                ),
                name=(
                    "Favorites "
                    f"({favorite_count})"
                ),
                lazy_path=(
                    f"/plugins/{self.PLUGIN_ID}/games?"
                    + urlencode(
                        {
                            "view": "favorites",
                        }
                    )
                ),
            ),
            self._lazy_category(
                node_id=(
                    "games_saved_states"
                ),
                name=(
                    "Saved States "
                    f"({saved_count})"
                ),
                lazy_path=(
                    f"/plugins/{self.PLUGIN_ID}/games?"
                    + urlencode(
                        {
                            "view": "continue",
                        }
                    )
                ),
            ),
            {
                "id": "games_search",
                "name": "Search Games",
                "node_type": "game",
            },
            self._lazy_category(
                node_id=(
                    "games_single_player"
                ),
                name=(
                    "Single Player "
                    f"({single_count})"
                ),
                lazy_path=(
                    f"/plugins/{self.PLUGIN_ID}/games?"
                    + urlencode(
                        {
                            "view": "single",
                        }
                    )
                ),
            ),
            self._lazy_category(
                node_id=(
                    "games_multiplayer"
                ),
                name=(
                    "Multiplayer "
                    f"({multi_count})"
                ),
                lazy_path=(
                    f"/plugins/{self.PLUGIN_ID}/games?"
                    + urlencode(
                        {
                            "view": "multi",
                        }
                    )
                ),
            ),
        ]

        for system_id, config in (
            self.SYSTEMS.items()
        ):
            params = urlencode(
                {
                    "system": system_id,
                }
            )

            nodes.append(
                self._lazy_category(
                    node_id=(
                        "games_system_"
                        + system_id
                    ),
                    name=(
                        f"{config['name']} "
                        f"({counts[system_id]})"
                    ),
                    lazy_path=(
                        f"/plugins/{self.PLUGIN_ID}/games?"
                        f"{params}"
                    ),
                )
            )

        # Preserve the existing diagnostic/status entries while moving
        # them behind the player-facing library organization.
        nodes.extend(
            [
                {
                    "id": "games_stream_host",
                    "name": "Streaming Host",
                    "node_type": "game",
                    "lazy_path": (
                        f"/plugins/{self.PLUGIN_ID}/stream-status"
                    ),
                },
                {
                    "id": "games_native_stream",
                    "name": "Native Streaming Alpha",
                    "node_type": "game",
                    "lazy_path": (
                        f"/plugins/{self.PLUGIN_ID}/native-stream-status"
                    ),
                },
            ]
        )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "games_root": str(
                self.GAMES_ROOT
            ),
            "total": len(games),
            "favorites": favorite_count,
            "recent": recent_count,
            "saved_states": saved_count,
            "single_player": single_count,
            "multiplayer": multi_count,
            "nodes": nodes,
        }

    def games(
        self,
        query: dict[str, list[str]],
    ) -> dict[str, Any]:
        system_id = (
            self._first(
                query,
                "system",
            )
            .strip()
            .casefold()
        )

        view = (
            self._first(
                query,
                "view",
            )
            .strip()
            .casefold()
        )

        search_text = (
            self._first(
                query,
                "q",
            )
            .strip()
        )

        all_games = (
            self._annotated_games()
        )

        view_name = ""
        base_params: dict[
            str,
            Any,
        ]

        if view:
            if view not in {
                "continue",
                "favorites",
                "recent",
                "search",
                "single",
                "multi",
            }:
                raise ValueError(
                    "Invalid game library view"
                )

            base_params = {
                "view": view,
            }

            if view == "favorites":
                view_name = "Favorites"

                matching = [
                    game
                    for game in all_games
                    if bool(
                        game.get(
                            "favorite",
                            False,
                        )
                    )
                ]

                matching.sort(
                    key=lambda item: (
                        str(
                            item[
                                "title"
                            ]
                        ).casefold(),
                        str(
                            item[
                                "system_name"
                            ]
                        ).casefold(),
                    )
                )

            elif view == "recent":
                view_name = (
                    "Continue Playing"
                )

                matching = [
                    game
                    for game in all_games
                    if self._nonnegative_int(
                        game.get(
                            "last_played_unix_ms",
                            0,
                        )
                    )
                    > 0
                ]

                matching.sort(
                    key=lambda item: (
                        -self._nonnegative_int(
                            item.get(
                                "last_played_unix_ms",
                                0,
                            )
                        ),
                        str(
                            item[
                                "title"
                            ]
                        ).casefold(),
                    )
                )

            elif view == "search":
                terms = [
                    term
                    for term in (
                        search_text
                        .casefold()
                        .split()
                    )
                    if term
                ]

                view_name = (
                    "Search Games"
                    if not search_text
                    else (
                        "Search: "
                        + search_text
                    )
                )

                base_params[
                    "q"
                ] = search_text

                matching = [
                    game
                    for game in all_games
                    if terms
                    and all(
                        term
                        in (
                            str(
                                game.get(
                                    "title",
                                    "",
                                )
                            )
                            + " "
                            + str(
                                game.get(
                                    "system_name",
                                    "",
                                )
                            )
                        ).casefold()
                        for term in terms
                    )
                ]

                matching.sort(
                    key=lambda item: (
                        str(
                            item[
                                "title"
                            ]
                        ).casefold(),
                        str(
                            item[
                                "system_name"
                            ]
                        ).casefold(),
                    )
                )

            elif view in {
                "single",
                "multi",
            }:
                required_mode = (
                    "single"
                    if view == "single"
                    else "multi"
                )

                view_name = (
                    "Single Player"
                    if required_mode == "single"
                    else "Multiplayer"
                )

                matching = [
                    game
                    for game in all_games
                    if game.get(
                        "player_mode"
                    )
                    == required_mode
                ]

                matching.sort(
                    key=lambda item: (
                        str(
                            item[
                                "title"
                            ]
                        ).casefold(),
                        str(
                            item[
                                "system_name"
                            ]
                        ).casefold(),
                    )
                )

            else:
                view_name = (
                    "Saved States"
                )

                matching = [
                    game
                    for game in all_games
                    if bool(
                        game.get(
                            "continue_available",
                            False,
                        )
                    )
                ]

                matching.sort(
                    key=lambda item: (
                        -self._nonnegative_int(
                            item.get(
                                "continue_modified_unix_ms",
                                0,
                            )
                        ),
                        -self._nonnegative_int(
                            item.get(
                                "last_played_unix_ms",
                                0,
                            )
                        ),
                        str(
                            item[
                                "title"
                            ]
                        ).casefold(),
                    )
                )

        else:
            if (
                system_id
                not in self.SYSTEMS
            ):
                raise ValueError(
                    "Missing or invalid game system"
                )

            base_params = {
                "system": system_id,
            }

            view_name = str(
                self.SYSTEMS[
                    system_id
                ][
                    "name"
                ]
            )

            matching = [
                game
                for game in all_games
                if (
                    game[
                        "system"
                    ]
                    == system_id
                )
            ]

        offset_text = self._first(
            query,
            "offset",
        )

        offset_supplied = bool(
            offset_text
        )

        offset = max(
            0,
            self._parse_int(
                offset_text,
                0,
            ),
        )

        limit = self._parse_int(
            self._first(
                query,
                "limit",
            ),
            self.PAGE_SIZE,
        )

        limit = min(
            max(
                1,
                limit,
            ),
            self.PAGE_SIZE,
        )

        if (
            not offset_supplied
            and len(matching)
            > self.PAGE_SIZE
        ):
            nodes = []
            page = 1

            for start in range(
                0,
                len(matching),
                self.PAGE_SIZE,
            ):
                end = min(
                    start
                    + self.PAGE_SIZE,
                    len(matching),
                )

                params = {
                    **base_params,
                    "offset": start,
                    "limit": (
                        self.PAGE_SIZE
                    ),
                }

                node_prefix = (
                    "games_view_"
                    + view
                    if view
                    else (
                        "games_"
                        + system_id
                    )
                )

                nodes.append(
                    self._lazy_category(
                        node_id=(
                            f"{node_prefix}_page_"
                            f"{page:02d}"
                        ),
                        name=(
                            f"Page {page:02d} "
                            f"({start + 1}-{end})"
                        ),
                        lazy_path=(
                            f"/plugins/{self.PLUGIN_ID}/games?"
                            + urlencode(
                                params
                            )
                        ),
                    )
                )

                page += 1

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "system": system_id,
                "system_name": (
                    view_name
                ),
                "view": view,
                "view_name": (
                    view_name
                ),
                "query": search_text,
                "total": len(
                    matching
                ),
                "nodes": nodes,
            }

        selected = matching[
            offset:
            offset + limit
        ]

        nodes = [
            {
                "id": str(
                    game[
                        "id"
                    ]
                ),
                "name": (
                    str(
                        game[
                            "title"
                        ]
                    )
                    if not view
                    else (
                        str(
                            game[
                                "title"
                            ]
                        )
                        + " - "
                        + str(
                            game[
                                "system_name"
                            ]
                        )
                    )
                ),
                "node_type": "game",
                "artwork_path": str(
                    game.get(
                        "artwork_path",
                        "",
                    )
                ),
                "lazy_path": (
                    f"/plugins/{self.PLUGIN_ID}/details?"
                    + urlencode(
                        {
                            "id": str(
                                game[
                                    "id"
                                ]
                            )
                        }
                    )
                ),
            }
            for game in selected
        ]

        if not nodes:
            if view:
                empty_id = (
                    "games_empty_view_"
                    + view
                )

                empty_name = {
                    "continue": (
                        "No saved states yet"
                    ),
                    "favorites": (
                        "No favorite games yet"
                    ),
                    "recent": (
                        "No games played yet"
                    ),
                    "search": (
                        "No games match this search"
                    ),
                    "single": (
                        "No games classified as single player"
                    ),
                    "multi": (
                        "No games classified as multiplayer"
                    ),
                }[
                    view
                ]

            else:
                empty_id = (
                    "games_empty_"
                    + system_id
                )

                empty_name = (
                    "No games found - add files under "
                    f"games/{self.SYSTEMS[system_id]['folder']}/"
                )

            nodes.append(
                {
                    "id": empty_id,
                    "name": empty_name,
                    "node_type": "game",
                    "lazy_path": (
                        f"/plugins/{self.PLUGIN_ID}/details?"
                        + urlencode(
                            {
                                "id": empty_id,
                            }
                        )
                    ),
                }
            )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "system": system_id,
            "system_name": (
                view_name
            ),
            "view": view,
            "view_name": (
                view_name
            ),
            "query": search_text,
            "total": len(
                matching
            ),
            "offset": offset,
            "count": len(
                selected
            ),
            "nodes": nodes,
        }

    # PrivyHub Phase A7.1: catalog user-supplied cheats/mods only.
    # Nothing discovered here is enabled, copied into RetroArch, or applied
    # to game content in this phase.
    def _game_user_content(
        self,
        game: dict[str, Any],
    ) -> dict[str, Any]:
        game_id = str(
            game.get(
                "id",
                "",
            )
        ).strip()

        relative_path = str(
            game.get(
                "relative_path",
                "",
            )
        ).strip()

        empty = {
            "user_content_catalog_only": True,
            "cheat_file_count": 0,
            "mod_file_count": 0,
            "cheat_files": [],
            "mod_files": [],
            "user_content_managed_hint": (
                f"data/games/user_content/{game_id}/"
                if game_id
                else ""
            ),
            "user_content_sidecar_hint": "",
        }

        if (
            not game_id
            or not relative_path
        ):
            return empty

        project_root = (
            self.PROJECT_ROOT.resolve()
        )
        games_root = (
            self.GAMES_ROOT.resolve()
        )

        try:
            game_path = (
                self.PROJECT_ROOT
                / relative_path
            ).resolve()

            game_path.relative_to(
                games_root
            )

        except (
            OSError,
            ValueError,
        ):
            return empty

        managed_root = (
            self.PROJECT_ROOT
            / "data"
            / "games"
            / "user_content"
            / game_id
        )

        sidecar_root = (
            game_path.parent
            / (
                game_path.stem
                + ".privyhub"
            )
        )

        try:
            sidecar_hint = (
                sidecar_root.resolve()
                .relative_to(
                    project_root
                )
                .as_posix()
                + "/"
            )
        except (
            OSError,
            ValueError,
        ):
            sidecar_hint = ""

        result = {
            **empty,
            "user_content_sidecar_hint": (
                sidecar_hint
            ),
        }

        categories = (
            (
                "cheat_files",
                "cheats",
                {
                    ".cht",
                },
            ),
            (
                "mod_files",
                "mods",
                {
                    ".ips",
                    ".bps",
                    ".ups",
                    ".xdelta",
                },
            ),
        )

        roots = (
            (
                "managed",
                managed_root,
            ),
            (
                "sidecar",
                sidecar_root,
            ),
        )

        maximum_files = 256

        for (
            result_key,
            folder_name,
            extensions,
        ) in categories:
            entries: list[
                dict[str, Any]
            ] = []

            seen: set[
                str
            ] = set()

            for source, root in roots:
                folder = (
                    root
                    / folder_name
                )

                if not folder.is_dir():
                    continue

                try:
                    files = sorted(
                        (
                            item
                            for item in folder.rglob(
                                "*"
                            )
                            if item.is_file()
                            and not item.name.startswith(
                                "."
                            )
                            and item.suffix.casefold()
                            in extensions
                        ),
                        key=lambda item: (
                            str(
                                item
                            ).casefold()
                        ),
                    )
                except OSError:
                    continue

                for item in files:
                    if len(
                        entries
                    ) >= maximum_files:
                        break

                    try:
                        resolved = (
                            item.resolve()
                        )

                        relative = (
                            resolved
                            .relative_to(
                                project_root
                            )
                            .as_posix()
                        )

                        key = str(
                            resolved
                        ).casefold()

                        if key in seen:
                            continue

                        seen.add(
                            key
                        )

                        try:
                            size_bytes = (
                                resolved.stat()
                                .st_size
                            )
                        except OSError:
                            size_bytes = 0

                        entries.append(
                            {
                                "name": (
                                    item.name
                                ),
                                "relative_path": (
                                    relative
                                ),
                                "source": source,
                                "size_bytes": (
                                    size_bytes
                                ),
                            }
                        )

                    except (
                        OSError,
                        ValueError,
                    ):
                        continue

                if len(
                    entries
                ) >= maximum_files:
                    break

            result[
                result_key
            ] = entries

        result[
            "cheat_file_count"
        ] = len(
            result[
                "cheat_files"
            ]
        )

        result[
            "mod_file_count"
        ] = len(
            result[
                "mod_files"
            ]
        )

        return result

    def details(
        self,
        query: dict[str, list[str]],
    ) -> dict[str, Any]:
        game_id = self._first(
            query,
            "id",
        ).strip()

        if not game_id:
            raise ValueError(
                "Missing game id"
            )

        if game_id.startswith(
            "games_empty_view_"
        ):
            view = game_id.removeprefix(
                "games_empty_view_"
            )

            messages = {
                "continue": (
                    "Save a PrivyHub state in any slot, then this game will "
                    "appear under Saved States."
                ),
                "favorites": (
                    "Open a game, choose Options, and add it to Favorites."
                ),
                "recent": (
                    "Games appear here after a successful PrivyHub launch."
                ),
                "search": (
                    "No games matched this search."
                ),
                "single": (
                    "Classify a game as Single Player from its Options menu."
                ),
                "multi": (
                    "Classify a game as Multiplayer from its Options menu."
                ),
            }

            if view not in messages:
                raise ValueError(
                    "Unknown game library view"
                )

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "id": game_id,
                "title": (
                    {
                        "continue": (
                            "Saved States"
                        ),
                        "favorites": (
                            "Favorites"
                        ),
                        "recent": (
                            "Continue Playing"
                        ),
                        "search": (
                            "Search Games"
                        ),
                        "single": (
                            "Single Player"
                        ),
                        "multi": (
                            "Multiplayer"
                        ),
                    }[
                        view
                    ]
                ),
                "system": "",
                "system_name": "Games",
                "relative_path": "",
                "format": "",
                "size_bytes": 0,
                "favorite": False,
                "last_played_unix_ms": 0,
                "play_count": 0,
                "player_mode": "unknown",
                "continue_available": False,
                "catalog_only": True,
                "message": messages[
                    view
                ],
            }

        if game_id.startswith(
            "games_empty_"
        ):
            system_id = (
                game_id.removeprefix(
                    "games_empty_"
                )
            )

            config = self.SYSTEMS.get(
                system_id
            )

            if config is None:
                raise ValueError(
                    "Unknown game id"
                )

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "id": game_id,
                "title": "No games found",
                "system": system_id,
                "system_name": str(
                    config[
                        "name"
                    ]
                ),
                "relative_path": (
                    f"games/{config['folder']}/"
                ),
                "format": "",
                "size_bytes": 0,
                "favorite": False,
                "last_played_unix_ms": 0,
                "play_count": 0,
                "player_mode": "unknown",
                "continue_available": False,
                "catalog_only": True,
                "message": (
                    "Add supported game files to this folder on the "
                    "companion, then reopen Games."
                ),
            }

        game = next(
            (
                item
                for item in (
                    self._annotated_games()
                )
                if item[
                    "id"
                ]
                == game_id
            ),
            None,
        )

        if game is None:
            raise ValueError(
                "Unknown game id"
            )

        # PrivyHub Phase A PS1 controller profiles
        controller = (
            self._emulator.controller_profile(
                game
            )
        )

        user_content = (
            self._game_user_content(
                game
            )
        )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            **game,
            **user_content,
            "controller_profile": (
                controller[
                    "profile"
                ]
            ),
            "controller_profile_label": (
                controller[
                    "label"
                ]
            ),
            "controller_profile_source": (
                controller[
                    "source"
                ]
            ),
            "controller_profile_selectable": (
                controller[
                    "selectable"
                ]
            ),
            "controller_profile_options": (
                controller[
                    "options"
                ]
            ),
            "catalog_only": True,
            "message": (
                "PrivyHub can launch this game on the companion."
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

        # PRIVYHUB_A8_PATCH_01_INPUT_PROFILE_BACKEND
        if action == "input-profiles":
            game_id = self._first(
                query,
                "id",
            ).strip()

            game = (
                self._find_game_by_id(
                    game_id
                )
                if game_id
                else None
            )

            payload = (
                self._emulator.input_profiles(
                    game
                )
            )

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                **payload,
            }


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


    # PRIVYHUB_A7_PATCH_09V2_GAMES_CHEAT_API
    @staticmethod
    def _parse_cheat_indexes(value: str) -> list[int]:
        text = str(value or "").strip()
        if not text:
            return []
        result: list[int] = []
        for raw in text.split(","):
            item = raw.strip()
            if not item:
                raise ValueError("Cheat indexes must be comma-separated integers")
            try:
                index = int(item)
            except ValueError as exc:
                raise ValueError("Cheat indexes must be comma-separated integers") from exc
            if index < 0:
                raise ValueError("Cheat indexes must be non-negative")
            result.append(index)
        return sorted(set(result))

    def _parse_cheat_launch_request(
        self,
        query: dict[str, list[str]],
    ) -> tuple[int | None, list[int] | None]:
        source_text = self._first(query, "cheat_source").strip()
        indexes_text = self._first(query, "cheat_indexes").strip()
        if not source_text and not indexes_text:
            return None, None
        if not source_text:
            raise ValueError("cheat_source is required when cheat_indexes are supplied")
        try:
            source_index = int(source_text)
        except ValueError as exc:
            raise ValueError("cheat_source must be a non-negative integer") from exc
        if source_index < 0:
            raise ValueError("cheat_source must be a non-negative integer")
        return source_index, self._parse_cheat_indexes(indexes_text)

    @classmethod
    def _query_bool(
        cls,
        query: dict[str, list[str]],
        key: str,
        default: bool = False,
    ) -> bool:
        value = cls._first(query, key).strip().casefold()
        if not value:
            return bool(default)
        if value in {"1", "true", "yes", "on"}:
            return True
        if value in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"{key} must be true or false")

    # PRIVYHUB_A8_PATCH_01_INPUT_PROFILE_BACKEND
    @staticmethod
    def _parse_input_profile_mapping(
        value: str,
        *,
        supplied: bool,
    ) -> Any:
        if not supplied:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return {}

        try:
            mapping = json.loads(
                text
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Input profile mapping must be valid JSON"
            ) from exc

        if not isinstance(
            mapping,
            dict,
        ):
            raise ValueError(
                "Input profile mapping must be a JSON object"
            )

        return mapping


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

        # PRIVYHUB_A7_PATCH_11_A7_4_SOFTPATCH_MODS_ADB_FIX API
        if action == "mod-catalog":
            game_id = self._first(query, "id").strip()
            if not game_id:
                raise ValueError("Missing game id")
            game = self._find_game_by_id(game_id)
            payload = self._emulator.mod_catalog(game)
            return {"ok": True, "plugin": self.PLUGIN_ID, **payload}

        if action == "mod-profiles":
            game_id = self._first(query, "id").strip()
            if not game_id:
                raise ValueError("Missing game id")
            game = self._find_game_by_id(game_id)
            payload = self._emulator.mod_profiles(game)
            return {"ok": True, "plugin": self.PLUGIN_ID, **payload}


        # PRIVYHUB_A7_PATCH_09V2_GAMES_CHEAT_API endpoints
        if action == "cheat-catalog":
            game_id = self._first(query, "id").strip()
            if not game_id:
                raise ValueError("Missing game id")
            game = self._find_game_by_id(game_id)
            payload = self._emulator.cheat_catalog(game)
            return {"ok": True, "plugin": self.PLUGIN_ID, **payload}

        if action == "cheat-profiles":
            game_id = self._first(query, "id").strip()
            if not game_id:
                raise ValueError("Missing game id")
            game = self._find_game_by_id(game_id)
            payload = self._emulator.cheat_profiles(game)
            return {"ok": True, "plugin": self.PLUGIN_ID, **payload}

        if action == "active-cheats":
            payload = self._emulator.active_cheats()
            return {"ok": True, "plugin": self.PLUGIN_ID, **payload}


        if action == "launch":
            # PRIVYHUB_A8_PATCH_02B_CONTROLLER_PREFLIGHT_ORDER_V1
            try:
                self._native_stream.ensure_game_controller(client_ip)
            except Exception as exc:
                try:
                    self._native_stream.end_game_session()
                except Exception:
                    pass
                raise RuntimeError(
                    "Unable to establish game controller before launch: "
                    f"{exc}"
                ) from exc

            try:
                payload = self.handle_post(action, raw_query)
            except Exception:
                try:
                    self._native_stream.end_game_session()
                except Exception:
                    pass
                raise

            if not payload.get("active", False):
                try:
                    self._native_stream.end_game_session()
                except Exception:
                    pass
                return payload

            if payload.get("active", False):
                try:
                    paused = self._emulator.pause()
                except Exception as exc:
                    try:
                        self._emulator.stop()
                    finally:
                        try:
                            self._native_stream.end_game_session()
                        except Exception:
                            pass
                    raise RuntimeError(f"Unable to establish paused game session: {exc}") from exc
                payload["paused"] = bool(paused.get("paused", False))
                payload["game_session"] = paused
                payload["native_stream"] = self._native_stream.status()

                # A successful paused handoff is the point at which a game
                # counts as played. Library-history failure must never tear
                # down an otherwise healthy game session.
                try:
                    launched_game_id = self._first(
                        query,
                        "id",
                    ).strip()

                    if launched_game_id:
                        launched_game = (
                            self._find_game_by_id(
                                launched_game_id
                            )
                        )

                        payload["library"] = (
                            self._record_game_launch(
                                launched_game
                            )
                        )

                except Exception as exc:
                    payload["library_warning"] = (
                        "Game launched, but library history could not "
                        f"be updated: {exc}"
                    )

            return payload

        if action == "native-stream-start":
            game_status = self._emulator.status()
            if not game_status.get("active", False):
                raise RuntimeError("Launch a game before starting Native Video Alpha.")
            port = self._parse_int(self._first(query, "port"), NativeStreamManager.DEFAULT_PORT)
            try:
                payload = self._native_stream.start(client_ip=client_ip, port=port)
                if game_status.get("paused", False):
                    resumed = self._emulator.resume()
                    payload["game_session"] = resumed
                    payload["paused"] = False
                return payload
            except NativeStreamError as exc:
                raise RuntimeError(str(exc)) from exc
            except EmulatorError as exc:
                try:
                    self._native_stream.stop()
                except Exception:
                    pass
                raise RuntimeError(f"Native stream started but game resume failed: {exc}") from exc

        if action == "native-stream-stop":
            game_status = self._emulator.status()
            if game_status.get("active", False) and not game_status.get("paused", False):
                try:
                    paused = self._emulator.pause()
                except EmulatorError as exc:
                    try:
                        self._emulator.stop()
                    finally:
                        try:
                            self._native_stream.end_game_session()
                        except Exception:
                            pass
                    raise RuntimeError(
                        f"Unable to pause game while leaving fullscreen; the game was stopped instead: {exc}"
                    ) from exc
            else:
                paused = game_status
            try:
                payload = self._native_stream.stop()
                payload["game_session"] = paused
                payload["paused"] = bool(paused.get("paused", False))
                return payload
            except NativeStreamError as exc:
                raise RuntimeError(str(exc)) from exc

        return self.handle_post(action, raw_query)

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
            # PRIVYHUB_A8_PATCH_01_INPUT_PROFILE_BACKEND
            if action == "input-profile-create":
                name = self._first(
                    query,
                    "name",
                ).strip()

                if not name:
                    raise ValueError(
                        "Missing input profile name"
                    )

                mapping_supplied = (
                    "mapping"
                    in query
                )
                mapping = (
                    self._parse_input_profile_mapping(
                        self._first(
                            query,
                            "mapping",
                        ),
                        supplied=(
                            mapping_supplied
                        ),
                    )
                )

                profile = (
                    self._emulator.create_input_profile(
                        name,
                        (
                            mapping
                            if mapping_supplied
                            else {}
                        ),
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    "profile": profile,
                }

            if action == "input-profile-update":
                profile_id = self._first(
                    query,
                    "profile_id",
                ).strip()

                if not profile_id:
                    raise ValueError(
                        "Missing input profile id"
                    )

                name_supplied = (
                    "name"
                    in query
                )
                mapping_supplied = (
                    "mapping"
                    in query
                )

                if (
                    not name_supplied
                    and not mapping_supplied
                ):
                    raise ValueError(
                        "Input profile update supplied no changes"
                    )

                name = (
                    self._first(
                        query,
                        "name",
                    ).strip()
                    if name_supplied
                    else None
                )

                mapping = (
                    self._parse_input_profile_mapping(
                        self._first(
                            query,
                            "mapping",
                        ),
                        supplied=(
                            mapping_supplied
                        ),
                    )
                )

                profile = (
                    self._emulator.update_input_profile(
                        profile_id,
                        name=name,
                        mapping=mapping,
                        mapping_supplied=(
                            mapping_supplied
                        ),
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    "profile": profile,
                }

            if action == "input-profile-delete":
                profile_id = self._first(
                    query,
                    "profile_id",
                ).strip()

                if not profile_id:
                    raise ValueError(
                        "Missing input profile id"
                    )

                payload = (
                    self._emulator.delete_input_profile(
                        profile_id
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    **payload,
                }

            if action == "input-profile-assign":
                game_id = self._first(
                    query,
                    "id",
                ).strip()

                profile_id = self._first(
                    query,
                    "profile_id",
                ).strip()

                if not game_id:
                    raise ValueError(
                        "Missing game id"
                    )

                if not profile_id:
                    raise ValueError(
                        "Missing input profile id"
                    )

                game = (
                    self._find_game_by_id(
                        game_id
                    )
                )

                payload = (
                    self._emulator.assign_input_profile(
                        game,
                        profile_id,
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    **payload,
                }


            if action == "decoder-session-log":
                report = self._first(
                    query,
                    "report",
                ).strip()

                return write_decoder_session_log(
                    self.PROJECT_ROOT,
                    report,
                )

            # PrivyHub Phase A6: persistent favorite state.
            if action == "favorite":
                game_id = self._first(
                    query,
                    "id",
                ).strip()

                if not game_id:
                    raise ValueError(
                        "Missing game id"
                    )

                game = self._find_game_by_id(
                    game_id
                )

                library_game = (
                    self._toggle_favorite(
                        game
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    "id": game_id,
                    "favorite": bool(
                        library_game[
                            "favorite"
                        ]
                    ),
                    "library": (
                        library_game
                    ),
                }

            # PrivyHub Phase A6: explicit player grouping metadata.
            if action == "player-mode":
                game_id = self._first(
                    query,
                    "id",
                ).strip()

                mode = self._first(
                    query,
                    "mode",
                ).strip().casefold()

                if not game_id:
                    raise ValueError(
                        "Missing game id"
                    )

                game = self._find_game_by_id(
                    game_id
                )

                library_game = (
                    self._set_player_mode(
                        game,
                        mode,
                    )
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    "id": game_id,
                    "player_mode": str(
                        library_game[
                            "player_mode"
                        ]
                    ),
                    "library": (
                        library_game
                    ),
                }

            if action == "controller-profile":
                game_id = self._first(
                    query,
                    "id",
                ).strip()

                profile = self._first(
                    query,
                    "profile",
                ).strip()

                if not game_id:
                    raise ValueError("Missing game id")

                if not profile:
                    raise ValueError("Missing controller profile")

                game = self._find_game_by_id(
                    game_id
                )

                controller = self._emulator.set_controller_profile(
                    game,
                    profile,
                )

                return {
                    "ok": True,
                    "plugin": self.PLUGIN_ID,
                    "id": game_id,
                    **controller,
                }

            # PrivyHub Phase A2 save-state actions
            if action in {
                "save-state",
                "load-state",
            }:
                slot = self._parse_int(
                    self._first(
                        query,
                        "slot",
                    ),
                    0,
                )

                self._emulator.record_save_state_probe_event(
                    "plugin_request",
                    action=action,
                    slot=slot,
                )

                if action == "save-state":
                    payload = self._emulator.save_state(
                        slot,
                        replace=self._query_bool(query, "replace", False),
                    )
                else:
                    payload = self._emulator.load_state(
                        slot
                    )

                payload["stream_host"] = self._stream.status()
                return payload

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

                cheat_source_index, cheat_enabled_indexes = (
                    self._parse_cheat_launch_request(query)
                )
                mod_index_text = self._first(query, "mod_index").strip()
                mod_index = None
                if mod_index_text:
                    try:
                        mod_index = int(mod_index_text)
                    except ValueError as exc:
                        raise ValueError("mod_index must be a non-negative integer") from exc
                    if mod_index < 0:
                        raise ValueError("mod_index must be a non-negative integer")
                payload = self._emulator.launch(
                    game,
                    cheat_source_index=cheat_source_index,
                    cheat_enabled_indexes=cheat_enabled_indexes,
                    mod_index=mod_index,
                )
                payload["stream_host"] = self._stream.status()
                payload["stream_warning"] = stream_warning

                return payload

            if action == "stop":
                payload = self._emulator.stop()
                try:
                    payload["native_stream"] = self._native_stream.end_game_session()
                except NativeStreamError as exc:
                    payload["native_stream_warning"] = str(exc)
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
