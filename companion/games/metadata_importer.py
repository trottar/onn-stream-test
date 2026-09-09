from __future__ import annotations

import abc
import binascii
import difflib
import hashlib
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any


METADATA_SCHEMA_VERSION = 1
DEFAULT_PROVIDER_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_SOURCE_DOWNLOAD_BYTES = 32 * 1024 * 1024
MAX_ARTWORK_DOWNLOAD_BYTES = 10 * 1024 * 1024

LIBRETRO_DATABASE_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "libretro/libretro-database/master"
)

LIBRETRO_THUMBNAIL_BASE_URL = (
    "https://thumbnails.libretro.com"
)

LIBRETRO_DATABASE_ATTRIBUTION = {
    "name": "Libretro Database",
    "url": "https://github.com/libretro/libretro-database",
    "license": "CC-BY-SA-4.0",
}

LIBRETRO_THUMBNAIL_ATTRIBUTION = {
    "name": "Libretro Thumbnails",
    "url": "https://thumbnails.libretro.com/",
    "note": (
        "Artwork is downloaded into the user's local cache. "
        "Underlying artwork rights may belong to the respective "
        "game publishers/rights holders."
    ),
}


SYSTEM_SPECS: dict[str, dict[str, Any]] = {
    "nes": {
        "database_name": "Nintendo - Nintendo Entertainment System",
        "catalog_path": (
            "metadat/no-intro/"
            "Nintendo - Nintendo Entertainment System.dat"
        ),
        "checksum_mode": "small_rom",
    },
    "snes": {
        "database_name": "Nintendo - Super Nintendo Entertainment System",
        "catalog_path": (
            "metadat/no-intro/"
            "Nintendo - Super Nintendo Entertainment System.dat"
        ),
        "checksum_mode": "small_rom",
    },
    "genesis": {
        "database_name": "Sega - Mega Drive - Genesis",
        "catalog_path": (
            "metadat/no-intro/"
            "Sega - Mega Drive - Genesis.dat"
        ),
        "checksum_mode": "small_rom",
    },
    "ps1": {
        "database_name": "Sony - PlayStation",
        "catalog_path": "metadat/redump/Sony - PlayStation.dat",
        "checksum_mode": "title_fallback",
    },
}

METADATA_FRAGMENT_FOLDERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("developer", ("developer",)),
    ("publisher", ("publisher",)),
    ("genre", ("genre",)),
    ("releaseyear", ("releaseyear", "release_year")),
    ("maxusers", ("maxusers", "users")),
)


class MetadataError(RuntimeError):
    pass


class ProviderUnavailable(MetadataError):
    pass


class MetadataProvider(abc.ABC):
    provider_id = "provider"

    @abc.abstractmethod
    def prepare_system(self, system_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def match_game(self, game: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def fetch_artwork(
        self,
        game: dict[str, Any],
        match: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _load_json_dict(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _strip_filename_tags(value: str) -> str:
    text = value
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\s*\([^()]*\)\s*$", "", text)
        text = re.sub(r"\s*\[[^\[\]]*\]\s*$", "", text)
    return text.strip()


def normalize_title_exact(value: str) -> str:
    """Normalize punctuation while preserving meaningful tags such as region."""
    text = value.replace("_", " ")
    text = re.sub(r"[^0-9a-zA-Z]+", " ", text)
    return " ".join(text.casefold().split())


def normalize_title(value: str) -> str:
    """Broad fallback key that removes common trailing filename tags."""
    text = _strip_filename_tags(value)
    return normalize_title_exact(text)


def _title_disc_number(value: str) -> int:
    match = re.search(
        r"(?i)\(\s*disc\s+([0-9]+)\s*\)",
        value,
    )

    if match is None:
        return 0

    try:
        return max(
            0,
            int(match.group(1)),
        )
    except ValueError:
        return 0


def _title_revision_number(value: str) -> int:
    match = re.search(
        r"(?i)\(\s*rev(?:ision)?\s+([0-9]+)\s*\)",
        value,
    )

    if match is None:
        return 0

    try:
        return max(
            0,
            int(match.group(1)),
        )
    except ValueError:
        return 0


def _title_region_hint(value: str) -> str:
    """
    Extract only region tags we can compare safely against the database's
    explicit region field. Language/edition/demo tags are intentionally
    ignored rather than guessed.
    """
    known = {
        "usa": "USA",
        "canada": "Canada",
        "europe": "Europe",
        "japan": "Japan",
        "asia": "Asia",
        "australia": "Australia",
        "france": "France",
        "germany": "Germany",
        "italy": "Italy",
        "spain": "Spain",
        "ireland": "Ireland",
    }

    for raw_group in re.findall(
        r"\(([^()]*)\)",
        value,
    ):
        tokens = [
            token.strip().casefold()
            for token in raw_group.split(",")
        ]

        for token in tokens:
            if token in known:
                return known[token]

    return ""


def _variant_signature(
    title: str,
    record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = record or {}

    region = str(
        record.get(
            "region",
            "",
        )
    ).strip()

    return {
        "region": (
            region
            or _title_region_hint(title)
        ),
        "disc": _title_disc_number(title),
        "revision": _title_revision_number(title),
    }


def thumbnail_filename(canonical_title: str) -> str:
    sanitized = re.sub(r'[&*/:`<>?\\|"]', "_", canonical_title)
    return sanitized + ".png"


def _quoted_value(block: str, key: str) -> str:
    pattern = re.compile(
        rf"(?m)^\s*{re.escape(key)}\s+"
        r'"((?:[^"\\]|\\.)*)"\s*$'
    )
    match = pattern.search(block)
    if match is None:
        return ""
    return (
        match.group(1)
        .replace(r'\"', '"')
        .replace(r"\\", "\\")
    )


def _numeric_value(block: str, key: str) -> int:
    match = re.search(
        rf"(?m)^\s*{re.escape(key)}\s+" r'"?([0-9]+)"?\s*$',
        block,
    )
    if match is None:
        return 0
    try:
        return max(0, int(match.group(1)))
    except ValueError:
        return 0


def _rom_token(block: str, key: str) -> str:
    patterns = (
        re.compile(rf"(?i)\b{re.escape(key)}\s+" r'"([^"]+)"'),
        re.compile(rf"(?i)\b{re.escape(key)}\s+" r"([0-9A-Fa-f_-]+)"),
    )
    for pattern in patterns:
        match = pattern.search(block)
        if match is not None:
            return match.group(1).strip().upper()
    return ""


def parse_clrmamepro_game_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    cursor = 0
    marker = re.compile(r"(?m)^\s*game\s*\(")
    length = len(text)

    while cursor < length:
        found = marker.search(text, cursor)
        if found is None:
            break

        start = found.start()
        open_paren = text.find("(", found.start(), found.end())
        if open_paren < 0:
            break

        depth = 0
        in_quote = False
        escaped = False
        index = open_paren

        while index < length:
            character = text[index]
            if in_quote:
                if escaped:
                    escaped = False
                elif character == "\\":
                    escaped = True
                elif character == '"':
                    in_quote = False
            else:
                if character == '"':
                    in_quote = True
                elif character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        blocks.append(text[start:index + 1])
                        cursor = index + 1
                        break
            index += 1
        else:
            break

    return blocks


def _record_keys(block: str) -> dict[str, str]:
    return {
        "crc": _rom_token(block, "crc"),
        "md5": _rom_token(block, "md5"),
        "sha1": _rom_token(block, "sha1"),
        "serial": _rom_token(block, "serial"),
    }


def _record_from_block(block: str) -> dict[str, Any]:
    return {
        "canonical_title": (
            _quoted_value(block, "name")
            or _quoted_value(block, "comment")
            or _quoted_value(block, "description")
        ),
        "description": _quoted_value(block, "description"),
        "region": _quoted_value(block, "region"),
        "developer": _quoted_value(block, "developer"),
        "publisher": _quoted_value(block, "publisher"),
        "genre": _quoted_value(block, "genre"),
        "release_year": (
            _numeric_value(block, "releaseyear")
            or _numeric_value(block, "release_year")
        ),
        "max_players": (
            _numeric_value(block, "maxusers")
            or _numeric_value(block, "users")
        ),
        **_record_keys(block),
    }


def _metadata_fragment_value(block: str, keys: tuple[str, ...]) -> Any:
    for key in keys:
        numeric = _numeric_value(block, key)
        if numeric:
            return numeric
        quoted = _quoted_value(block, key)
        if quoted:
            return quoted
    return None


def _preferred_record_key(record: dict[str, Any]) -> tuple[str, str] | None:
    for key in ("crc", "sha1", "md5", "serial"):
        value = str(record.get(key, "")).strip().upper()
        if value:
            return key, value
    return None


def _file_hashes_small_rom(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MetadataError(f"Unable to read ROM for checksum: {path}") from exc

    variants: list[tuple[str, bytes]] = [("raw", raw)]

    if len(raw) > 16 and raw[:4] == b"NES\x1a":
        variants.append(("ines_payload", raw[16:]))

    if len(raw) > 512 and len(raw) % 1024 == 512:
        variants.append(("copier_header_removed", raw[512:]))

    seen: set[tuple[str, str, str]] = set()
    results: list[dict[str, str]] = []

    for label, candidate in variants:
        crc = f"{binascii.crc32(candidate) & 0xFFFFFFFF:08X}"
        md5 = hashlib.md5(candidate, usedforsecurity=False).hexdigest().upper()
        sha1 = hashlib.sha1(candidate).hexdigest().upper()
        key = (crc, md5, sha1)
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "variant": label,
                "crc": crc,
                "md5": md5,
                "sha1": sha1,
            }
        )

    return {
        "size_bytes": len(raw),
        "variants": results,
    }


def _download_limited(
    url: str,
    *,
    maximum_bytes: int,
    timeout_seconds: float,
    user_agent: str,
) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_type = str(response.headers.get("Content-Type", ""))
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum_bytes:
                    raise MetadataError(
                        "Remote response exceeded configured size limit"
                    )
                chunks.append(chunk)
            return b"".join(chunks), content_type
    except urllib.error.HTTPError as exc:
        raise ProviderUnavailable(
            f"HTTP {exc.code} for provider resource"
        ) from exc
    except urllib.error.URLError as exc:
        raise ProviderUnavailable("Provider network request failed") from exc


class LibretroProvider(MetadataProvider):
    provider_id = "libretro"

    def __init__(
        self,
        project_root: Path,
        *,
        offline: bool = False,
        refresh_cache: bool = False,
        cache_ttl_seconds: int = DEFAULT_PROVIDER_CACHE_TTL_SECONDS,
        database_base_url: str = LIBRETRO_DATABASE_BASE_URL,
        thumbnail_base_url: str = LIBRETRO_THUMBNAIL_BASE_URL,
    ) -> None:
        self.project_root = project_root.resolve()
        self.offline = bool(offline)
        self.refresh_cache = bool(refresh_cache)
        self.cache_ttl_seconds = max(0, int(cache_ttl_seconds))
        self.database_base_url = database_base_url.rstrip("/")
        self.thumbnail_base_url = thumbnail_base_url.rstrip("/")
        self.cache_root = (
            self.project_root
            / "data"
            / "games"
            / "metadata"
            / "provider_cache"
            / "libretro"
        )
        self.artwork_root = self.project_root / "media" / "games" / "box_art"
        self._prepared: dict[str, dict[str, Any]] = {}
        self._stats = {
            "source_cache_hits": 0,
            "source_downloads": 0,
            "source_unavailable": 0,
            "artwork_downloaded": 0,
            "artwork_cached": 0,
            "artwork_missing": 0,
            "artwork_errors": 0,
        }

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    def _cache_path(self, system_id: str, label: str) -> Path:
        safe = re.sub(r"[^0-9a-zA-Z_.-]+", "_", label)
        return self.cache_root / system_id / safe

    def _source_text(
        self,
        system_id: str,
        label: str,
        remote_path: str,
        *,
        required: bool,
    ) -> str:
        cache_path = self._cache_path(system_id, label)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            stat = cache_path.stat()
            age_seconds = time.time() - stat.st_mtime
            cache_usable = stat.st_size > 0
        except OSError:
            age_seconds = float("inf")
            cache_usable = False

        if (
            cache_usable
            and not self.refresh_cache
            and (self.offline or age_seconds < self.cache_ttl_seconds)
        ):
            self._stats["source_cache_hits"] += 1
            return cache_path.read_text(encoding="utf-8", errors="replace")

        if self.offline:
            if cache_usable:
                self._stats["source_cache_hits"] += 1
                return cache_path.read_text(encoding="utf-8", errors="replace")
            if required:
                raise ProviderUnavailable(
                    "Required Libretro provider cache is unavailable offline"
                )
            return ""

        encoded_path = "/".join(
            urllib.parse.quote(part, safe="") for part in remote_path.split("/")
        )
        url = self.database_base_url + "/" + encoded_path

        try:
            raw, _ = _download_limited(
                url,
                maximum_bytes=MAX_SOURCE_DOWNLOAD_BYTES,
                timeout_seconds=20.0,
                user_agent="PrivyHub-GameMetadata/0.1",
            )
        except ProviderUnavailable:
            self._stats["source_unavailable"] += 1
            if cache_usable:
                self._stats["source_cache_hits"] += 1
                return cache_path.read_text(encoding="utf-8", errors="replace")
            if required:
                raise
            return ""

        temporary = cache_path.with_name(cache_path.name + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(cache_path)
        self._stats["source_downloads"] += 1
        return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _add_keyed(
        mapping: dict[tuple[str, str], list[dict[str, Any]]],
        record: dict[str, Any],
    ) -> None:
        for key in ("crc", "sha1", "md5", "serial"):
            value = str(record.get(key, "")).strip().upper()
            if value:
                mapping.setdefault((key, value), []).append(record)

    def prepare_system(self, system_id: str) -> dict[str, Any]:
        if system_id in self._prepared:
            return self._prepared[system_id]

        spec = SYSTEM_SPECS.get(system_id)
        if spec is None:
            raise ProviderUnavailable(f"Unsupported system: {system_id}")

        database_name = str(spec["database_name"])
        catalog_text = self._source_text(
            system_id,
            "catalog.dat",
            str(spec["catalog_path"]),
            required=True,
        )

        base_records: list[dict[str, Any]] = []
        keyed: dict[tuple[str, str], list[dict[str, Any]]] = {}
        by_exact_title: dict[str, list[dict[str, Any]]] = {}
        by_normalized_title: dict[str, list[dict[str, Any]]] = {}

        for block in parse_clrmamepro_game_blocks(catalog_text):
            record = _record_from_block(block)
            canonical = str(record.get("canonical_title", "")).strip()
            if not canonical:
                continue
            base_records.append(record)
            self._add_keyed(keyed, record)

            exact_normalized = normalize_title_exact(canonical)
            if exact_normalized:
                by_exact_title.setdefault(
                    exact_normalized,
                    [],
                ).append(record)

            normalized = normalize_title(canonical)
            if normalized:
                by_normalized_title.setdefault(normalized, []).append(record)

        if not base_records:
            raise ProviderUnavailable("Libretro catalog parsed no game records")

        metadata_by_key: dict[tuple[str, str], dict[str, Any]] = {}

        for folder, value_keys in METADATA_FRAGMENT_FOLDERS:
            fragment_text = self._source_text(
                system_id,
                f"{folder}.dat",
                f"metadat/{folder}/{database_name}.dat",
                required=False,
            )
            if not fragment_text:
                continue

            for block in parse_clrmamepro_game_blocks(fragment_text):
                value = _metadata_fragment_value(block, value_keys)
                if value in (None, "", 0):
                    continue
                keys = _record_keys(block)
                for key in ("crc", "sha1", "md5", "serial"):
                    key_value = str(keys.get(key, "")).strip().upper()
                    if key_value:
                        metadata_by_key.setdefault((key, key_value), {})[
                            folder
                        ] = value

        prepared = {
            "system_id": system_id,
            "database_name": database_name,
            "checksum_mode": str(spec["checksum_mode"]),
            "records": base_records,
            "keyed": keyed,
            "by_exact_title": by_exact_title,
            "by_normalized_title": by_normalized_title,
            "normalized_titles": sorted(by_normalized_title),
            "metadata_by_key": metadata_by_key,
        }
        self._prepared[system_id] = prepared
        return prepared

    @staticmethod
    def _record_metadata(
        prepared: dict[str, Any],
        record: dict[str, Any],
    ) -> dict[str, Any]:
        result = {
            "description": str(record.get("description", "")),
            "region": str(record.get("region", "")),
            "developer": str(record.get("developer", "")),
            "publisher": str(record.get("publisher", "")),
            "genre": str(record.get("genre", "")),
            "release_year": int(record.get("release_year", 0) or 0),
            "max_players": int(record.get("max_players", 0) or 0),
        }
        metadata_by_key = prepared["metadata_by_key"]

        for key_name in ("crc", "sha1", "md5", "serial"):
            key_value = str(record.get(key_name, "")).strip().upper()
            if not key_value:
                continue
            fragment = metadata_by_key.get((key_name, key_value), {})
            if not fragment:
                continue
            if not result["developer"]:
                result["developer"] = str(fragment.get("developer", ""))
            if not result["publisher"]:
                result["publisher"] = str(fragment.get("publisher", ""))
            if not result["genre"]:
                result["genre"] = str(fragment.get("genre", ""))
            if not result["release_year"]:
                try:
                    result["release_year"] = int(fragment.get("releaseyear", 0) or 0)
                except (TypeError, ValueError):
                    pass
            if not result["max_players"]:
                try:
                    result["max_players"] = int(fragment.get("maxusers", 0) or 0)
                except (TypeError, ValueError):
                    pass

        result["player_mode_suggested"] = (
            "single"
            if result["max_players"] == 1
            else ("multi" if result["max_players"] > 1 else "unknown")
        )
        return result

    @staticmethod
    def _result_for_record(
        prepared: dict[str, Any],
        record: dict[str, Any],
        *,
        method: str,
        confidence: float,
        local_probe: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        preferred_key = _preferred_record_key(record)
        return {
            "provider": "libretro",
            "status": "matched",
            "method": method,
            "confidence": round(max(0.0, min(1.0, float(confidence))), 4),
            "canonical_title": str(record.get("canonical_title", "")),
            "source_key": (
                {"type": preferred_key[0], "value": preferred_key[1]}
                if preferred_key
                else {}
            ),
            "metadata": LibretroProvider._record_metadata(prepared, record),
            "local_probe": local_probe or {},
        }

    def _checksum_match(
        self,
        prepared: dict[str, Any],
        game: dict[str, Any],
    ) -> dict[str, Any] | None:
        if prepared["checksum_mode"] != "small_rom":
            return None

        relative = str(game.get("relative_path", "")).strip()
        if not relative:
            return None

        path = (self.project_root / relative).resolve()
        try:
            path.relative_to((self.project_root / "games").resolve())
        except (OSError, ValueError):
            return None

        if not path.is_file():
            return None

        try:
            probe = _file_hashes_small_rom(path)
        except MetadataError:
            return None

        keyed = prepared["keyed"]
        for variant in probe["variants"]:
            for key_name in ("crc", "sha1", "md5"):
                value = str(variant[key_name]).upper()
                candidates = keyed.get((key_name, value), [])
                if len(candidates) == 1:
                    return self._result_for_record(
                        prepared,
                        candidates[0],
                        method="checksum_" + key_name,
                        confidence=1.0,
                        local_probe={
                            "variant": variant["variant"],
                            key_name: value,
                            "size_bytes": probe["size_bytes"],
                        },
                    )
                if len(candidates) > 1:
                    return {
                        "provider": self.provider_id,
                        "status": "ambiguous",
                        "method": "checksum_" + key_name,
                        "confidence": 1.0,
                        "candidates": [
                            str(candidate.get("canonical_title", ""))
                            for candidate in candidates[:5]
                        ],
                        "local_probe": {
                            "variant": variant["variant"],
                            key_name: value,
                        },
                    }
        return None

    def _variant_match(
        self,
        prepared: dict[str, Any],
        game: dict[str, Any],
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """
        Resolve broad-title collisions only from explicit structured evidence.

        This is intentionally narrower than fuzzy matching:
        - compatible region is required when the local title supplies one;
        - disc number must agree when the local title supplies one;
        - revision must agree when the local title supplies one;
        - if the local title omits disc/revision, candidates carrying those
          tags are not silently selected;
        - remaining duplicate records are accepted only when their canonical
          display title is identical.
        """
        local_title = str(
            game.get(
                "title",
                "",
            )
        ).strip()

        local = _variant_signature(
            local_title
        )

        if not any(
            (
                local["region"],
                local["disc"],
                local["revision"],
            )
        ):
            return None

        narrowed: list[dict[str, Any]] = []

        for candidate in candidates:
            canonical = str(
                candidate.get(
                    "canonical_title",
                    "",
                )
            ).strip()

            variant = _variant_signature(
                canonical,
                candidate,
            )

            if local["region"]:
                if (
                    not variant["region"]
                    or str(
                        variant["region"]
                    ).casefold()
                    != str(
                        local["region"]
                    ).casefold()
                ):
                    continue

            if local["disc"]:
                if variant["disc"] != local["disc"]:
                    continue
            elif variant["disc"]:
                continue

            if local["revision"]:
                if (
                    variant["revision"]
                    != local["revision"]
                ):
                    continue
            elif variant["revision"]:
                continue

            narrowed.append(
                candidate
            )

        if not narrowed:
            return None

        canonical_groups: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for candidate in narrowed:
            canonical = str(
                candidate.get(
                    "canonical_title",
                    "",
                )
            ).strip()

            canonical_groups.setdefault(
                canonical,
                [],
            ).append(
                candidate
            )

        if len(canonical_groups) == 1:
            candidate = next(
                iter(
                    canonical_groups.values()
                )
            )[0]

            return self._result_for_record(
                prepared,
                candidate,
                method="title_variant_tags",
                confidence=0.99,
                local_probe={
                    "region": local["region"],
                    "disc": local["disc"],
                    "revision": local["revision"],
                },
            )

        return {
            "provider": self.provider_id,
            "status": "ambiguous",
            "method": "title_variant_tags",
            "confidence": 0.99,
            "candidates": list(
                canonical_groups
            )[:5],
            "local_probe": {
                "region": local["region"],
                "disc": local["disc"],
                "revision": local["revision"],
            },
        }


    def _title_match(
        self,
        prepared: dict[str, Any],
        game: dict[str, Any],
    ) -> dict[str, Any]:
        raw_title = str(game.get("title", "")).strip()

        exact_query = normalize_title_exact(raw_title)
        if exact_query:
            exact_tagged = prepared["by_exact_title"].get(
                exact_query,
                [],
            )

            # Multiple database records can legitimately carry the exact same
            # canonical display title (for example alternate dump records).
            # For metadata/art purposes those are equivalent. Only differing
            # canonical titles remain ambiguous.
            if exact_tagged:
                canonical_groups: dict[str, list[dict[str, Any]]] = {}

                for candidate in exact_tagged:
                    canonical = str(
                        candidate.get(
                            "canonical_title",
                            "",
                        )
                    ).strip()

                    canonical_groups.setdefault(
                        canonical,
                        [],
                    ).append(candidate)

                if len(canonical_groups) == 1:
                    candidate = next(
                        iter(canonical_groups.values())
                    )[0]

                    return self._result_for_record(
                        prepared,
                        candidate,
                        method="title_exact_tagged",
                        confidence=0.995,
                    )

                return {
                    "provider": self.provider_id,
                    "status": "ambiguous",
                    "method": "title_exact_tagged",
                    "confidence": 0.995,
                    "candidates": list(canonical_groups)[:5],
                }

        query = normalize_title(raw_title)
        if not query:
            return {
                "provider": self.provider_id,
                "status": "no_match",
                "method": "title",
                "confidence": 0.0,
                "candidates": [],
            }

        by_title = prepared["by_normalized_title"]
        exact = by_title.get(query, [])
        if len(exact) == 1:
            return self._result_for_record(
                prepared,
                exact[0],
                method="title_exact",
                confidence=0.97,
            )
        if len(exact) > 1:
            variant = self._variant_match(
                prepared,
                game,
                exact,
            )

            if variant is not None:
                return variant

            return {
                "provider": self.provider_id,
                "status": "ambiguous",
                "method": "title_exact",
                "confidence": 0.97,
                "candidates": [
                    str(candidate.get("canonical_title", ""))
                    for candidate in exact[:5]
                ],
            }

        possible = difflib.get_close_matches(
            query,
            prepared["normalized_titles"],
            n=3,
            cutoff=0.90,
        )
        scored: list[tuple[float, str]] = []
        for normalized in possible:
            scored.append(
                (
                    difflib.SequenceMatcher(None, query, normalized).ratio(),
                    normalized,
                )
            )
        scored.sort(reverse=True)

        if not scored:
            return {
                "provider": self.provider_id,
                "status": "no_match",
                "method": "title_fuzzy",
                "confidence": 0.0,
                "candidates": [],
            }

        best_score, best_normalized = scored[0]
        candidates_text = [
            str(prepared["by_normalized_title"][normalized][0].get(
                "canonical_title", ""
            ))
            for _score, normalized in scored
        ]

        if best_score < 0.93:
            return {
                "provider": self.provider_id,
                "status": "no_match",
                "method": "title_fuzzy",
                "confidence": round(best_score, 4),
                "candidates": candidates_text,
            }

        if len(scored) > 1 and (best_score - scored[1][0]) < 0.025:
            return {
                "provider": self.provider_id,
                "status": "ambiguous",
                "method": "title_fuzzy",
                "confidence": round(best_score, 4),
                "candidates": candidates_text,
            }

        records = prepared["by_normalized_title"][best_normalized]
        if len(records) != 1:
            return {
                "provider": self.provider_id,
                "status": "ambiguous",
                "method": "title_fuzzy",
                "confidence": round(best_score, 4),
                "candidates": [
                    str(record.get("canonical_title", ""))
                    for record in records[:5]
                ],
            }

        return self._result_for_record(
            prepared,
            records[0],
            method="title_fuzzy",
            confidence=best_score,
        )

    def match_game(self, game: dict[str, Any]) -> dict[str, Any]:
        system_id = str(game.get("system", "")).strip().casefold()
        try:
            prepared = self.prepare_system(system_id)
        except ProviderUnavailable as exc:
            return {
                "provider": self.provider_id,
                "status": "provider_unavailable",
                "method": "",
                "confidence": 0.0,
                "error": str(exc),
                "preserve_prior": True,
            }

        checksum = self._checksum_match(prepared, game)
        if checksum is not None:
            return checksum
        return self._title_match(prepared, game)

    def _artwork_url(self, system_id: str, canonical_title: str) -> str:
        database_name = str(SYSTEM_SPECS[system_id]["database_name"])
        return (
            self.thumbnail_base_url
            + "/"
            + urllib.parse.quote(database_name, safe="")
            + "/Named_Boxarts/"
            + urllib.parse.quote(thumbnail_filename(canonical_title), safe="")
        )

    def fetch_artwork(
        self,
        game: dict[str, Any],
        match: dict[str, Any],
    ) -> dict[str, Any]:
        if match.get("status") != "matched":
            return {"status": "not_applicable"}

        game_id = str(game.get("id", "")).strip()
        system_id = str(game.get("system", "")).strip().casefold()
        canonical = str(match.get("canonical_title", "")).strip()

        if not game_id or not canonical or system_id not in SYSTEM_SPECS:
            return {"status": "invalid_match"}

        destination = self.artwork_root / (game_id + ".png")
        try:
            if destination.is_file() and destination.stat().st_size > 0:
                self._stats["artwork_cached"] += 1
                return {
                    "status": "cached",
                    "relative_path": destination.relative_to(
                        self.project_root
                    ).as_posix(),
                    "source": "libretro_thumbnails",
                }
        except OSError:
            pass

        if self.offline:
            self._stats["artwork_missing"] += 1
            return {"status": "missing_offline"}

        url = self._artwork_url(system_id, canonical)
        try:
            raw, content_type = _download_limited(
                url,
                maximum_bytes=MAX_ARTWORK_DOWNLOAD_BYTES,
                timeout_seconds=15.0,
                user_agent="PrivyHub-GameMetadata/0.1",
            )
        except ProviderUnavailable as exc:
            self._stats["artwork_missing"] += 1
            return {"status": "missing", "error": str(exc)}

        if not raw.startswith(b"\x89PNG\r\n\x1a\n") and (
            "image/png" not in content_type.casefold()
        ):
            self._stats["artwork_errors"] += 1
            return {"status": "invalid_payload"}

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(destination)
        self._stats["artwork_downloaded"] += 1

        return {
            "status": "downloaded",
            "relative_path": destination.relative_to(
                self.project_root
            ).as_posix(),
            "source": "libretro_thumbnails",
        }


def scan_privyhub_games(project_root: Path) -> list[dict[str, Any]]:
    project_root = project_root.resolve()
    companion_dir = project_root / "companion"

    import sys

    companion_text = str(companion_dir)
    inserted = False
    if companion_text not in sys.path:
        sys.path.insert(0, companion_text)
        inserted = True

    try:
        from plugins.games import GamesPlugin

        scanner = GamesPlugin.__new__(GamesPlugin)
        scanner.PROJECT_ROOT = project_root
        scanner.GAMES_ROOT = project_root / "games"
        scanner._lock = threading.RLock()
        scanner._cached_at = 0.0
        scanner._cached_games = []
        return [dict(game) for game in scanner._scan()]
    finally:
        if inserted:
            try:
                sys.path.remove(companion_text)
            except ValueError:
                pass


def run_metadata_update(
    project_root: Path,
    *,
    offline: bool = False,
    refresh_provider_cache: bool = False,
    download_artwork: bool = True,
    only_system: str = "",
    limit: int = 0,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    metadata_path = project_root / "data" / "games" / "metadata.json"
    log_json_path = project_root / "logs" / "games" / "game_metadata_update.json"
    log_text_path = project_root / "logs" / "games" / "game_metadata_update.txt"

    previous = _load_json_dict(metadata_path)
    previous_games = previous.get("games", {})
    if not isinstance(previous_games, dict):
        previous_games = {}

    games = scan_privyhub_games(project_root)

    if only_system:
        wanted = only_system.strip().casefold()
        games = [
            game
            for game in games
            if str(game.get("system", "")).casefold() == wanted
        ]

    if limit > 0:
        games = games[:limit]

    provider = LibretroProvider(
        project_root,
        offline=offline,
        refresh_cache=refresh_provider_cache,
    )

    counts = {
        "total_games": len(games),
        "matched": 0,
        "checksum_matches": 0,
        "title_exact_matches": 0,
        "title_fuzzy_matches": 0,
        "ambiguous": 0,
        "no_match": 0,
        "provider_unavailable": 0,
        "prior_preserved": 0,
        "artwork_downloaded": 0,
        "artwork_cached": 0,
        "artwork_missing": 0,
        "errors": 0,
    }

    updated_games: dict[str, Any] = {}
    diagnostics: list[dict[str, Any]] = []
    now_ms = int(time.time() * 1000)

    for game in games:
        game_id = str(game.get("id", "")).strip()
        if not game_id:
            counts["errors"] += 1
            continue

        match = provider.match_game(game)
        status = str(match.get("status", ""))

        if status == "matched":
            counts["matched"] += 1
            method = str(match.get("method", ""))
            if method.startswith("checksum_"):
                counts["checksum_matches"] += 1
            elif method in {
                "title_exact_tagged",
                "title_variant_tags",
                "title_exact",
            }:
                counts["title_exact_matches"] += 1
            elif method == "title_fuzzy":
                counts["title_fuzzy_matches"] += 1
        elif status == "ambiguous":
            counts["ambiguous"] += 1
        elif status == "no_match":
            counts["no_match"] += 1
        elif status == "provider_unavailable":
            counts["provider_unavailable"] += 1
        else:
            counts["errors"] += 1

        if match.get("preserve_prior") and game_id in previous_games:
            updated_games[game_id] = previous_games[game_id]
            counts["prior_preserved"] += 1
            diagnostics.append(
                {
                    "id": game_id,
                    "title": str(game.get("title", "")),
                    "system": str(game.get("system", "")),
                    "match": match,
                    "result": "prior_preserved",
                }
            )
            continue

        artwork = {
            "status": "disabled" if not download_artwork else "not_applicable"
        }
        if download_artwork and status == "matched":
            artwork = provider.fetch_artwork(game, match)
            art_status = str(artwork.get("status", ""))
            if art_status == "downloaded":
                counts["artwork_downloaded"] += 1
            elif art_status == "cached":
                counts["artwork_cached"] += 1
            elif art_status in {"missing", "missing_offline", "invalid_payload"}:
                counts["artwork_missing"] += 1

        updated_games[game_id] = {
            "id": game_id,
            "scanned_title": str(game.get("title", "")),
            "system": str(game.get("system", "")),
            "system_name": str(game.get("system_name", "")),
            "relative_path": str(game.get("relative_path", "")),
            "updated_unix_ms": now_ms,
            "match": match,
            "artwork": artwork,
        }

        diagnostics.append(
            {
                "id": game_id,
                "title": str(game.get("title", "")),
                "system": str(game.get("system", "")),
                "match": match,
                "artwork": artwork,
            }
        )

    if only_system or limit > 0:
        for game_id, record in previous_games.items():
            updated_games.setdefault(str(game_id), record)

    payload = {
        "schema_version": METADATA_SCHEMA_VERSION,
        "generated_unix_ms": now_ms,
        "provider_priority": ["libretro"],
        "attribution": {
            "libretro_database": LIBRETRO_DATABASE_ATTRIBUTION,
            "libretro_thumbnails": LIBRETRO_THUMBNAIL_ATTRIBUTION,
        },
        "games": updated_games,
    }
    _atomic_json_write(metadata_path, payload)

    report = {
        "ok": True,
        "generated_unix_ms": now_ms,
        "project_root": str(project_root),
        "metadata_path": str(metadata_path),
        "offline": bool(offline),
        "refresh_provider_cache": bool(refresh_provider_cache),
        "download_artwork": bool(download_artwork),
        "only_system": only_system,
        "limit": int(limit),
        "counts": counts,
        "provider_stats": provider.stats,
        "games": diagnostics,
    }
    _atomic_json_write(log_json_path, report)

    lines = [
        "PrivyHub game metadata updater",
        "Provider: libretro (database + thumbnail server)",
        f"Games scanned: {counts['total_games']}",
        (
            "Matches: "
            f"{counts['matched']} "
            f"(checksum {counts['checksum_matches']}, "
            f"title exact {counts['title_exact_matches']}, "
            f"title fuzzy {counts['title_fuzzy_matches']})"
        ),
        f"Ambiguous: {counts['ambiguous']}",
        f"No match: {counts['no_match']}",
        f"Provider unavailable: {counts['provider_unavailable']}",
        f"Prior metadata preserved: {counts['prior_preserved']}",
        (
            "Artwork: "
            f"{counts['artwork_downloaded']} downloaded, "
            f"{counts['artwork_cached']} cached, "
            f"{counts['artwork_missing']} missing"
        ),
        (
            "Provider source cache: "
            f"{provider.stats['source_downloads']} downloaded, "
            f"{provider.stats['source_cache_hits']} reused, "
            f"{provider.stats['source_unavailable']} unavailable"
        ),
        f"Metadata: {metadata_path}",
        f"JSON diagnostic: {log_json_path}",
    ]
    log_text_path.parent.mkdir(parents=True, exist_ok=True)
    log_text_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report["text_log_path"] = str(log_text_path)
    return report
