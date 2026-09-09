from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path
from typing import Any, Callable

from games.metadata_importer import (
    SYSTEM_SPECS,
    normalize_title,
    scan_privyhub_games,
)


CHEAT_SCHEMA_VERSION = 1
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
MAX_CHT_BYTES = 2 * 1024 * 1024
MAX_PROVIDER_JSON_BYTES = 32 * 1024 * 1024
MAX_CHEATS_PER_FILE = 4096
GITHUB_BRANCH = "master"
GITHUB_API_ROOT = (
    "https://api.github.com/repos/libretro/libretro-database"
)
RAW_ROOT = (
    "https://raw.githubusercontent.com/libretro/"
    "libretro-database/master/cht"
)

LIBRETRO_CHEAT_ATTRIBUTION = {
    "name": "libretro-database cheat files",
    "provider": "libretro",
    "repository": "https://github.com/libretro/libretro-database",
    "source_path": "cht/",
    "license": "CC-BY-SA-4.0",
    "license_url": (
        "https://github.com/libretro/libretro-database/blob/master/LICENSE"
    ),
    "note": (
        "Cheat files are fetched on user request and cached locally. "
        "PrivyHub does not bundle the upstream cheat database."
    ),
}


class CheatError(RuntimeError):
    pass


class ProviderUnavailable(CheatError):
    pass


class InvalidCheatFile(CheatError):
    pass


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


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _git_blob_sha1(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _download_limited(
    url: str,
    *,
    maximum_bytes: int,
    timeout_seconds: float,
    user_agent: str,
) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/vnd.github+json, */*",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            declared = response.headers.get("Content-Length", "").strip()
            if declared:
                try:
                    if int(declared) > maximum_bytes:
                        raise ProviderUnavailable(
                            "Provider payload exceeds configured size limit"
                        )
                except ValueError:
                    pass

            raw = response.read(maximum_bytes + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ProviderUnavailable(
            "Provider request failed: " + str(exc)
        ) from exc

    if len(raw) > maximum_bytes:
        raise ProviderUnavailable(
            "Provider payload exceeds configured size limit"
        )

    return raw


def _download_json(url: str) -> Any:
    raw = _download_limited(
        url,
        maximum_bytes=MAX_PROVIDER_JSON_BYTES,
        timeout_seconds=20.0,
        user_agent="PrivyHub-GameCheats/0.1",
    )

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderUnavailable(
            "Provider returned invalid JSON"
        ) from exc


def _cache_is_fresh(payload: dict[str, Any]) -> bool:
    try:
        fetched = float(payload.get("fetched_unix", 0.0) or 0.0)
    except (TypeError, ValueError):
        return False
    return fetched > 0 and time.time() - fetched < CACHE_TTL_SECONDS


def _safe_tree_relative(value: str) -> Path:
    normalized = value.replace("\\", "/").strip("/")
    if not normalized:
        raise CheatError("Empty provider tree path")

    path = Path(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise CheatError("Unsafe provider tree path")

    return path


def _safe_local_filename(name: str, blob_sha: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).rstrip(" .")
    if not cleaned:
        cleaned = "cheats"
    if not cleaned.casefold().endswith(".cht"):
        cleaned += ".cht"

    # Preserve clean upstream names. If sanitization changed the name, include
    # the immutable blob prefix so two unsafe source names cannot collide.
    if cleaned != name:
        stem = cleaned[:-4]
        cleaned = f"{stem}__{blob_sha[:8]}.cht"

    return cleaned


_GROUP_RE = re.compile(r"\(([^()]*)\)|\[([^\[\]]*)\]")
_DISC_RE = re.compile(r"(?i)^\s*disc\s+([0-9]+)\s*$")
_REV_RE = re.compile(r"(?i)^\s*rev(?:ision)?\s+([0-9]+)\s*$")

_REGION_TOKENS = {
    "usa": "usa",
    "united states": "usa",
    "canada": "canada",
    "europe": "europe",
    "japan": "japan",
    "asia": "asia",
    "australia": "australia",
    "france": "france",
    "germany": "germany",
    "italy": "italy",
    "spain": "spain",
    "ireland": "ireland",
    "uk": "uk",
    "united kingdom": "uk",
    "korea": "korea",
    "brazil": "brazil",
    "world": "world",
    # Common optical-disc region shorthand used by upstream cheat filenames.
    # Treat these as region metadata, not semantic game variants.
    "ntsc-u": "usa",
    "ntsc-uc": "usa",
    "ntsc-u/c": "usa",
    "ntsc-j": "japan",
}

_CHEAT_QUALIFIER_PATTERNS = (
    "game genie",
    "gamegenie",
    "action replay",
    "pro action replay",
    "pro action rocky",
    "codebreaker",
    "code breaker",
    "game shark",
    "gameshark",
    "game buster",
    "gamebuster",
    "xploder",
    "x-ploder",
    "duckstation",
    "goldfinger",
    "raw codes",
    "raw code",
)

_LANGUAGE_TAG_TOKENS = {
    "en",
    "fr",
    "de",
    "es",
    "it",
    "nl",
    "sv",
    "no",
    "da",
    "fi",
    "pt",
    "ru",
    "pl",
    "ja",
    "jp",
    "ko",
    "zh",
}


def _group_values(value: str) -> list[str]:
    result: list[str] = []
    for match in _GROUP_RE.finditer(value):
        text = (match.group(1) or match.group(2) or "").strip()
        if text:
            result.append(text)
    return result


def _is_cheat_qualifier(value: str) -> bool:
    folded = " ".join(value.casefold().replace("_", " ").split())
    if folded == "diff":
        return True
    return any(pattern in folded for pattern in _CHEAT_QUALIFIER_PATTERNS)


def _is_language_bundle(value: str) -> bool:
    tokens = [
        token.strip().casefold()
        for token in value.split(",")
        if token.strip()
    ]
    return (
        len(tokens) >= 2
        and all(token in _LANGUAGE_TAG_TOKENS for token in tokens)
    )


def _region_group(value: str) -> set[str] | None:
    tokens = [
        token.strip().casefold()
        for token in value.split(",")
        if token.strip()
    ]
    if not tokens:
        return None

    mapped: set[str] = set()
    for token in tokens:
        region = _REGION_TOKENS.get(token)
        if region is None:
            return None
        mapped.add(region)
    return mapped


def _title_signature(
    title: str,
    *,
    explicit_region: str = "",
    ignore_cheat_qualifiers: bool = False,
) -> dict[str, Any]:
    regions: set[str] = set()
    semantic: list[str] = []
    disc = 0
    revision = 0

    if explicit_region:
        explicit = _region_group(explicit_region)
        if explicit:
            regions.update(explicit)
        else:
            folded = explicit_region.strip().casefold()
            mapped = _REGION_TOKENS.get(folded)
            if mapped:
                regions.add(mapped)

    for group in _group_values(title):
        if ignore_cheat_qualifiers and _is_cheat_qualifier(group):
            continue

        # Multi-language filename bundles identify a distribution/language set,
        # not a different game for cheat-catalog purposes. Keep semantic tags
        # such as Demo/Beta/Arcade Mode/Claire strict.
        if _is_language_bundle(group):
            continue

        region = _region_group(group)
        if region is not None:
            regions.update(region)
            continue

        match = _DISC_RE.match(group)
        if match is not None:
            disc = max(disc, int(match.group(1)))
            continue

        match = _REV_RE.match(group)
        if match is not None:
            revision = max(revision, int(match.group(1)))
            continue

        semantic.append(" ".join(group.casefold().split()))

    return {
        "base": normalize_title(title),
        "regions": sorted(regions),
        "disc": disc,
        "revision": revision,
        "semantic_tags": semantic,
    }


def _metadata_identity(
    game: dict[str, Any],
    metadata_record: dict[str, Any],
) -> dict[str, Any] | None:
    match = metadata_record.get("match", {})
    if not isinstance(match, dict):
        return None
    if str(match.get("status", "")) != "matched":
        return None

    canonical = str(match.get("canonical_title", "")).strip()
    if not canonical:
        return None

    metadata = match.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    region = str(metadata.get("region", "")).strip()
    signature = _title_signature(
        canonical,
        explicit_region=region,
    )

    return {
        "game_id": str(game.get("id", "")),
        "scanned_title": str(game.get("title", "")),
        "canonical_title": canonical,
        "system": str(game.get("system", "")),
        "system_name": str(game.get("system_name", "")),
        "relative_path": str(game.get("relative_path", "")),
        "region": region,
        "signature": signature,
        "metadata_match_method": str(match.get("method", "")),
        "metadata_match_confidence": match.get("confidence", 0.0),
    }


def match_cheat_entries(
    game: dict[str, Any],
    metadata_record: dict[str, Any],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    identity = _metadata_identity(game, metadata_record)
    if identity is None:
        return {
            "status": "metadata_missing",
            "provider": "libretro",
            "candidates": [],
        }

    local = identity["signature"]
    broad: list[dict[str, Any]] = []
    compatible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for entry in entries:
        source_path = str(entry.get("path", "")).strip()
        if not source_path.casefold().endswith(".cht"):
            continue

        source_title = Path(source_path).stem
        candidate = _title_signature(
            source_title,
            ignore_cheat_qualifiers=True,
        )

        if candidate["base"] != local["base"]:
            continue

        broad.append(entry)
        reasons: list[str] = []

        local_regions = set(local["regions"])
        candidate_regions = set(candidate["regions"])
        compatibility: list[str] = []

        # A provider "World" set is explicitly generalized by the provider.
        # Likewise, omitted provider region/disc/revision tags are treated as
        # generic applicability for cataloging only. Explicit contradictions
        # remain hard blockers and A7.2 still cannot activate any cheat.
        if local_regions:
            if not candidate_regions:
                compatibility.append("provider_region_unspecified")
            elif "world" in candidate_regions:
                if "world" not in local_regions:
                    compatibility.append("provider_world_region")
            elif not local_regions.intersection(candidate_regions):
                reasons.append("region_mismatch")
        elif candidate_regions:
            if candidate_regions == {"world"}:
                compatibility.append("local_region_unspecified_provider_world")
            else:
                reasons.append("local_region_missing")

        local_disc = int(local["disc"])
        candidate_disc = int(candidate["disc"])
        if candidate_disc and local_disc and candidate_disc != local_disc:
            reasons.append("disc_mismatch")
        elif candidate_disc and not local_disc:
            reasons.append("local_disc_unspecified")
        elif local_disc and not candidate_disc:
            compatibility.append("provider_disc_unspecified")

        local_revision = int(local["revision"])
        candidate_revision = int(candidate["revision"])
        if candidate_revision and local_revision and candidate_revision != local_revision:
            reasons.append("revision_mismatch")
        elif candidate_revision and not local_revision:
            reasons.append("local_revision_unspecified")
        elif local_revision and not candidate_revision:
            compatibility.append("provider_revision_unspecified")

        if list(candidate["semantic_tags"]) != list(local["semantic_tags"]):
            reasons.append("semantic_tag_mismatch")

        if reasons:
            rejected.append(
                {
                    "path": source_path,
                    "reasons": reasons,
                    "signature": candidate,
                }
            )
            continue

        item = dict(entry)
        item["source_title"] = source_title
        item["signature"] = candidate
        item["compatibility"] = compatibility
        compatible.append(item)

    if compatible:
        compatible.sort(
            key=lambda item: str(item.get("path", "")).casefold()
        )
        return {
            "status": "matched",
            "provider": "libretro",
            "method": "metadata_structured_title",
            "canonical_title": identity["canonical_title"],
            "identity": identity,
            "files": compatible,
            "rejected_same_base": rejected[:20],
        }

    if broad:
        return {
            "status": "ambiguous",
            "provider": "libretro",
            "method": "metadata_structured_title",
            "canonical_title": identity["canonical_title"],
            "identity": identity,
            "candidates": [
                str(item.get("path", ""))
                for item in broad[:20]
            ],
            "rejected_same_base": rejected[:20],
        }

    return {
        "status": "no_cheats",
        "provider": "libretro",
        "method": "metadata_structured_title",
        "canonical_title": identity["canonical_title"],
        "identity": identity,
        "candidates": [],
    }


_CHEATS_RE = re.compile(
    r'^\s*cheats\s*=\s*["\']?([0-9]+)["\']?\s*$',
    flags=re.IGNORECASE | re.MULTILINE,
)
_KEY_RE = re.compile(r"^\s*cheat([0-9]+)_([A-Za-z0-9_]+)\s*=", re.MULTILINE)
_ENABLE_TRUE_RE = re.compile(
    r'^(\s*cheat[0-9]+_enable\s*=\s*)(["\']?)(true|yes|1)(["\']?)(\s*)$',
    flags=re.IGNORECASE | re.MULTILINE,
)


def validate_and_normalize_cht(raw: bytes) -> dict[str, Any]:
    if not raw:
        raise InvalidCheatFile("Cheat file is empty")
    if len(raw) > MAX_CHT_BYTES:
        raise InvalidCheatFile("Cheat file exceeds 2 MiB safety limit")
    if b"\x00" in raw:
        raise InvalidCheatFile("Cheat file contains NUL/binary data")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidCheatFile("Cheat file is not valid UTF-8 text") from exc

    match = _CHEATS_RE.search(text)
    if match is None:
        raise InvalidCheatFile("Cheat file has no parseable cheats count")

    count = int(match.group(1))
    if count < 1 or count > MAX_CHEATS_PER_FILE:
        raise InvalidCheatFile("Cheat count is outside accepted bounds")

    desc_indices: set[int] = set()
    payload_indices: set[int] = set()

    for key_match in _KEY_RE.finditer(text):
        index = int(key_match.group(1))
        key = key_match.group(2).casefold()
        if index >= count:
            raise InvalidCheatFile(
                "Cheat file references an index beyond the declared count"
            )
        if key == "desc":
            desc_indices.add(index)
        if key in {"code", "address", "value"}:
            payload_indices.add(index)

    if not desc_indices:
        raise InvalidCheatFile("Cheat file contains no cheat descriptions")
    if not desc_indices.intersection(payload_indices):
        raise InvalidCheatFile("Cheat file contains no usable cheat payload")

    forced_disabled = 0

    def disable(match: re.Match[str]) -> str:
        nonlocal forced_disabled
        forced_disabled += 1
        quote = match.group(2)
        if quote not in {'"', "'"} or match.group(4) != quote:
            quote = ""
        return match.group(1) + quote + "false" + quote + match.group(5)

    normalized = _ENABLE_TRUE_RE.sub(disable, text)
    normalized_raw = normalized.encode("utf-8")

    return {
        "raw_sha256": _sha256(raw),
        "local_sha256": _sha256(normalized_raw),
        "cheat_count": count,
        "forced_disabled": forced_disabled,
        "normalized_raw": normalized_raw,
    }


class LibretroCheatProvider:
    provider_id = "libretro"

    def __init__(
        self,
        project_root: Path,
        *,
        offline: bool = False,
        refresh_cache: bool = False,
        json_fetcher: Callable[[str], Any] | None = None,
        bytes_fetcher: Callable[[str], bytes] | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.offline = bool(offline)
        self.refresh_cache = bool(refresh_cache)
        self.cache_root = (
            self.project_root
            / "data"
            / "games"
            / "cheats"
            / "provider_cache"
            / "libretro"
        )
        self.file_cache = self.cache_root / "files"
        self._json_fetcher = json_fetcher or _download_json
        self._bytes_fetcher = bytes_fetcher or self._download_bytes
        self._root_cache: dict[str, Any] | None = None
        self._prepared: dict[str, dict[str, Any]] = {}
        self._stats = {
            "index_downloads": 0,
            "index_cache_hits": 0,
            "index_unavailable": 0,
            "file_downloads": 0,
            "file_cache_hits": 0,
            "file_unavailable": 0,
        }

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)

    @staticmethod
    def _download_bytes(url: str) -> bytes:
        return _download_limited(
            url,
            maximum_bytes=MAX_CHT_BYTES,
            timeout_seconds=15.0,
            user_agent="PrivyHub-GameCheats/0.1",
        )

    def _read_cache(self, path: Path) -> dict[str, Any]:
        return _load_json_dict(path)

    def _write_cache(self, path: Path, payload: dict[str, Any]) -> None:
        _atomic_json_write(path, payload)

    def _root_index(self) -> dict[str, Any]:
        if self._root_cache is not None:
            return self._root_cache

        path = self.cache_root / "cht_root.json"
        cached = self._read_cache(path)
        use_cached = (
            bool(cached)
            and not self.refresh_cache
            and (_cache_is_fresh(cached) or self.offline)
        )

        if use_cached:
            self._stats["index_cache_hits"] += 1
            self._root_cache = cached
            return cached

        if self.offline:
            self._stats["index_unavailable"] += 1
            raise ProviderUnavailable("Libretro cheat root index is not cached")

        url = f"{GITHUB_API_ROOT}/contents/cht?ref={GITHUB_BRANCH}"
        try:
            raw = self._json_fetcher(url)
        except Exception as exc:
            if cached:
                self._stats["index_cache_hits"] += 1
                self._root_cache = cached
                return cached
            self._stats["index_unavailable"] += 1
            if isinstance(exc, ProviderUnavailable):
                raise
            raise ProviderUnavailable(str(exc)) from exc

        if not isinstance(raw, list):
            raise ProviderUnavailable("Libretro cheat root index has invalid shape")

        systems: dict[str, dict[str, str]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            if str(item.get("type", "")) != "dir":
                continue
            name = str(item.get("name", "")).strip()
            sha = str(item.get("sha", "")).strip()
            if name and sha:
                systems[name] = {"name": name, "sha": sha}

        payload = {
            "schema_version": 1,
            "fetched_unix": time.time(),
            "source_url": url,
            "systems": systems,
        }
        self._write_cache(path, payload)
        self._stats["index_downloads"] += 1
        self._root_cache = payload
        return payload

    def prepare_system(self, system_id: str) -> dict[str, Any]:
        system_id = system_id.strip().casefold()
        if system_id in self._prepared:
            return self._prepared[system_id]
        if system_id not in SYSTEM_SPECS:
            raise CheatError("Unsupported game system: " + system_id)

        system_name = str(SYSTEM_SPECS[system_id]["database_name"])
        root = self._root_index()
        systems = root.get("systems", {})
        if not isinstance(systems, dict):
            raise ProviderUnavailable("Cached cheat root system map is invalid")

        root_record = systems.get(system_name, {})
        if not isinstance(root_record, dict):
            root_record = {}
        tree_sha = str(root_record.get("sha", "")).strip()
        if not tree_sha:
            raise ProviderUnavailable(
                "Libretro cheat directory missing for " + system_name
            )

        path = self.cache_root / f"system_{system_id}.json"
        cached = self._read_cache(path)
        cached_sha = str(cached.get("tree_sha", "")).strip()
        use_cached = (
            bool(cached)
            and cached_sha == tree_sha
            and not self.refresh_cache
            and (_cache_is_fresh(cached) or self.offline)
        )

        if use_cached:
            self._stats["index_cache_hits"] += 1
            self._prepared[system_id] = cached
            return cached

        if self.offline:
            if cached and cached_sha == tree_sha:
                self._stats["index_cache_hits"] += 1
                self._prepared[system_id] = cached
                return cached
            self._stats["index_unavailable"] += 1
            raise ProviderUnavailable(
                "Libretro cheat index is not cached for " + system_id
            )

        url = f"{GITHUB_API_ROOT}/git/trees/{tree_sha}?recursive=1"
        try:
            raw = self._json_fetcher(url)
        except Exception as exc:
            if cached and cached_sha == tree_sha:
                self._stats["index_cache_hits"] += 1
                self._prepared[system_id] = cached
                return cached
            self._stats["index_unavailable"] += 1
            if isinstance(exc, ProviderUnavailable):
                raise
            raise ProviderUnavailable(str(exc)) from exc

        if not isinstance(raw, dict) or raw.get("truncated") is True:
            raise ProviderUnavailable(
                "Libretro cheat tree is invalid or truncated for " + system_id
            )

        tree = raw.get("tree", [])
        if not isinstance(tree, list):
            raise ProviderUnavailable("Libretro cheat tree has invalid shape")

        entries: list[dict[str, Any]] = []
        for item in tree:
            if not isinstance(item, dict):
                continue
            if str(item.get("type", "")) != "blob":
                continue
            relative = str(item.get("path", "")).strip()
            blob_sha = str(item.get("sha", "")).strip()
            if not relative.casefold().endswith(".cht") or not blob_sha:
                continue
            _safe_tree_relative(relative)
            entries.append(
                {
                    "path": relative,
                    "blob_sha": blob_sha,
                    "size": int(item.get("size", 0) or 0),
                }
            )

        entries.sort(key=lambda item: str(item["path"]).casefold())
        payload = {
            "schema_version": 1,
            "fetched_unix": time.time(),
            "source_url": url,
            "system": system_id,
            "system_directory": system_name,
            "tree_sha": tree_sha,
            "entries": entries,
        }
        self._write_cache(path, payload)
        self._stats["index_downloads"] += 1
        self._prepared[system_id] = payload
        return payload

    def entries_for_system(self, system_id: str) -> list[dict[str, Any]]:
        prepared = self.prepare_system(system_id)
        entries = prepared.get("entries", [])
        return [dict(item) for item in entries if isinstance(item, dict)]

    def fetch_cheat_file(
        self,
        system_id: str,
        entry: dict[str, Any],
    ) -> tuple[bytes, dict[str, Any]]:
        prepared = self.prepare_system(system_id)
        directory = str(prepared.get("system_directory", "")).strip()
        source_path = str(entry.get("path", "")).strip()
        blob_sha = str(entry.get("blob_sha", "")).strip()
        if not directory or not source_path or not blob_sha:
            raise ProviderUnavailable("Incomplete cheat source record")

        _safe_tree_relative(source_path)
        self.file_cache.mkdir(parents=True, exist_ok=True)
        cached_path = self.file_cache / f"{blob_sha}.cht"

        if cached_path.is_file():
            raw = cached_path.read_bytes()
            if (
                raw
                and len(raw) <= MAX_CHT_BYTES
                and _git_blob_sha1(raw).casefold() == blob_sha.casefold()
            ):
                self._stats["file_cache_hits"] += 1
                return raw, {
                    "status": "cached",
                    "cache_path": cached_path.relative_to(
                        self.project_root
                    ).as_posix(),
                }

            # A corrupt content-addressed provider cache must never be trusted.
            try:
                cached_path.unlink()
            except OSError:
                pass

        if self.offline:
            self._stats["file_unavailable"] += 1
            raise ProviderUnavailable(
                "Cheat file is not cached for offline use: " + source_path
            )

        quoted_directory = urllib.parse.quote(directory, safe="")
        quoted_path = urllib.parse.quote(source_path, safe="/")
        url = f"{RAW_ROOT}/{quoted_directory}/{quoted_path}"
        try:
            raw = self._bytes_fetcher(url)
        except Exception as exc:
            self._stats["file_unavailable"] += 1
            if isinstance(exc, ProviderUnavailable):
                raise
            raise ProviderUnavailable(str(exc)) from exc

        if not raw or len(raw) > MAX_CHT_BYTES:
            self._stats["file_unavailable"] += 1
            raise ProviderUnavailable("Invalid cheat file payload size")

        if _git_blob_sha1(raw).casefold() != blob_sha.casefold():
            self._stats["file_unavailable"] += 1
            raise ProviderUnavailable(
                "Downloaded cheat file does not match provider blob identity"
            )

        temporary = cached_path.with_name(cached_path.name + ".tmp")
        temporary.write_bytes(raw)
        temporary.replace(cached_path)
        self._stats["file_downloads"] += 1
        return raw, {
            "status": "downloaded",
            "source_url": url,
            "cache_path": cached_path.relative_to(
                self.project_root
            ).as_posix(),
        }


def _replace_provider_directory(
    destination: Path,
    staged: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = destination.with_name(
        destination.name + f".previous.{os.getpid()}"
    )
    if previous.exists():
        shutil.rmtree(previous)

    moved_previous = False
    try:
        if destination.exists():
            destination.replace(previous)
            moved_previous = True
        staged.replace(destination)
        if previous.exists():
            shutil.rmtree(previous)
    except Exception:
        if destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        if moved_previous and previous.exists():
            previous.replace(destination)
        raise


def _sync_game_files(
    project_root: Path,
    provider: LibretroCheatProvider,
    game: dict[str, Any],
    match: dict[str, Any],
) -> dict[str, Any]:
    game_id = str(game.get("id", "")).strip()
    system_id = str(game.get("system", "")).strip().casefold()
    if not game_id or not system_id:
        raise CheatError("Incomplete scanned game record")

    destination = (
        project_root
        / "data"
        / "games"
        / "user_content"
        / game_id
        / "cheats"
        / "libretro"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f"{game_id}.libretro.staging.",
        dir=str(destination.parent),
    ) as temp_name:
        staged = Path(temp_name) / "libretro"
        staged.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        used_names: set[str] = set()

        for entry in match.get("files", []):
            if not isinstance(entry, dict):
                continue
            source_path = str(entry.get("path", "")).strip()
            blob_sha = str(entry.get("blob_sha", "")).strip()
            raw, fetch = provider.fetch_cheat_file(system_id, entry)
            validated = validate_and_normalize_cht(raw)

            local_name = _safe_local_filename(
                Path(source_path).name,
                blob_sha,
            )
            key = local_name.casefold()
            if key in used_names:
                stem = Path(local_name).stem
                local_name = f"{stem}__{blob_sha[:8]}.cht"
                key = local_name.casefold()
            used_names.add(key)

            local_path = staged / local_name
            local_path.write_bytes(validated["normalized_raw"])

            records.append(
                {
                    "source_path": source_path,
                    "source_blob_sha": blob_sha,
                    "source_title": str(entry.get("source_title", "")),
                    "compatibility": list(entry.get("compatibility", [])),
                    "local_filename": local_name,
                    "local_path": (
                        Path("data")
                        / "games"
                        / "user_content"
                        / game_id
                        / "cheats"
                        / "libretro"
                        / local_name
                    ).as_posix(),
                    "raw_sha256": validated["raw_sha256"],
                    "local_sha256": validated["local_sha256"],
                    "cheat_count": validated["cheat_count"],
                    "forced_disabled": validated["forced_disabled"],
                    "fetch": fetch,
                }
            )

        # Only a fully staged, validated set replaces provider-owned files.
        _replace_provider_directory(destination, staged)

    return {
        "status": "cached",
        "provider_directory": destination.relative_to(project_root).as_posix(),
        "files": records,
    }


def run_cheat_update(
    project_root: Path,
    *,
    offline: bool = False,
    refresh_provider_cache: bool = False,
    download_files: bool = True,
    only_system: str = "",
    limit: int = 0,
) -> dict[str, Any]:
    project_root = project_root.resolve()
    metadata_path = project_root / "data" / "games" / "metadata.json"
    manifest_path = project_root / "data" / "games" / "cheats.json"
    log_json_path = project_root / "logs" / "games" / "game_cheat_update.json"
    log_text_path = project_root / "logs" / "games" / "game_cheat_update.txt"

    metadata_payload = _load_json_dict(metadata_path)
    metadata_games = metadata_payload.get("games", {})
    if not isinstance(metadata_games, dict):
        metadata_games = {}

    previous = _load_json_dict(manifest_path)
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

    provider = LibretroCheatProvider(
        project_root,
        offline=offline,
        refresh_cache=refresh_provider_cache,
    )

    counts = {
        "total_games": len(games),
        "metadata_ready": 0,
        "games_with_cheats": 0,
        "cheat_files_matched": 0,
        "cheat_files_downloaded": 0,
        "cheat_files_cached_source": 0,
        "cheat_codes_cataloged": 0,
        "forced_disabled": 0,
        "no_cheats": 0,
        "ambiguous": 0,
        "metadata_missing": 0,
        "provider_unavailable": 0,
        "invalid_cheat_files": 0,
        "prior_preserved": 0,
        "errors": 0,
    }

    diagnostics: list[dict[str, Any]] = []
    updated_games: dict[str, Any] = {}
    processed_ids: set[str] = set()
    now_ms = int(time.time() * 1000)

    entries_by_system: dict[str, list[dict[str, Any]]] = {}
    unavailable_systems: dict[str, str] = {}

    for game in games:
        game_id = str(game.get("id", "")).strip()
        system_id = str(game.get("system", "")).strip().casefold()
        if not game_id or not system_id:
            counts["errors"] += 1
            continue
        processed_ids.add(game_id)

        metadata_record = metadata_games.get(game_id, {})
        if not isinstance(metadata_record, dict):
            metadata_record = {}

        identity = _metadata_identity(game, metadata_record)
        if identity is None:
            counts["metadata_missing"] += 1
            diagnostic = {
                "id": game_id,
                "title": str(game.get("title", "")),
                "system": system_id,
                "match": {
                    "status": "metadata_missing",
                    "provider": "libretro",
                },
            }
            diagnostics.append(diagnostic)
            if download_files:
                updated_games[game_id] = {
                    **diagnostic,
                    "updated_unix_ms": now_ms,
                }
            continue

        counts["metadata_ready"] += 1

        if system_id in unavailable_systems:
            match = {
                "status": "provider_unavailable",
                "provider": "libretro",
                "error": unavailable_systems[system_id],
            }
        else:
            try:
                if system_id not in entries_by_system:
                    entries_by_system[system_id] = provider.entries_for_system(
                        system_id
                    )
                match = match_cheat_entries(
                    game,
                    metadata_record,
                    entries_by_system[system_id],
                )
            except ProviderUnavailable as exc:
                unavailable_systems[system_id] = str(exc)
                match = {
                    "status": "provider_unavailable",
                    "provider": "libretro",
                    "error": str(exc),
                }

        status = str(match.get("status", ""))
        diagnostic: dict[str, Any] = {
            "id": game_id,
            "title": str(game.get("title", "")),
            "system": system_id,
            "canonical_title": identity["canonical_title"],
            "match": match,
        }

        if status == "matched":
            files = match.get("files", [])
            files = files if isinstance(files, list) else []
            counts["games_with_cheats"] += 1
            counts["cheat_files_matched"] += len(files)

            if download_files:
                try:
                    cached = _sync_game_files(
                        project_root,
                        provider,
                        game,
                        match,
                    )
                except ProviderUnavailable as exc:
                    counts["provider_unavailable"] += 1
                    if game_id in previous_games:
                        updated_games[game_id] = previous_games[game_id]
                        counts["prior_preserved"] += 1
                        diagnostic["result"] = "prior_preserved"
                    diagnostic["download_error"] = str(exc)
                    diagnostics.append(diagnostic)
                    continue
                except InvalidCheatFile as exc:
                    counts["invalid_cheat_files"] += 1
                    if game_id in previous_games:
                        updated_games[game_id] = previous_games[game_id]
                        counts["prior_preserved"] += 1
                        diagnostic["result"] = "prior_preserved"
                    diagnostic["validation_error"] = str(exc)
                    diagnostics.append(diagnostic)
                    continue
                except OSError as exc:
                    counts["errors"] += 1
                    if game_id in previous_games:
                        updated_games[game_id] = previous_games[game_id]
                        counts["prior_preserved"] += 1
                        diagnostic["result"] = "prior_preserved"
                    diagnostic["download_error"] = str(exc)
                    diagnostics.append(diagnostic)
                    continue

                file_records = cached.get("files", [])
                file_records = file_records if isinstance(file_records, list) else []
                for record in file_records:
                    if not isinstance(record, dict):
                        continue
                    fetch = record.get("fetch", {})
                    if isinstance(fetch, dict):
                        if fetch.get("status") == "downloaded":
                            counts["cheat_files_downloaded"] += 1
                        elif fetch.get("status") == "cached":
                            counts["cheat_files_cached_source"] += 1
                    counts["cheat_codes_cataloged"] += int(
                        record.get("cheat_count", 0) or 0
                    )
                    counts["forced_disabled"] += int(
                        record.get("forced_disabled", 0) or 0
                    )

                updated_games[game_id] = {
                    "id": game_id,
                    "scanned_title": str(game.get("title", "")),
                    "canonical_title": identity["canonical_title"],
                    "system": system_id,
                    "system_name": str(game.get("system_name", "")),
                    "relative_path": str(game.get("relative_path", "")),
                    "updated_unix_ms": now_ms,
                    "provider": "libretro",
                    "status": "cached",
                    "match_method": str(match.get("method", "")),
                    "provider_tree_sha": str(
                        provider.prepare_system(system_id).get("tree_sha", "")
                    ),
                    "provider_directory": cached["provider_directory"],
                    "files": file_records,
                }
                diagnostic["cache"] = cached

        elif status == "no_cheats":
            counts["no_cheats"] += 1
            if download_files:
                # A complete successful provider index with no compatible files
                # means the provider-owned directory should be empty. Manual
                # A7.1 files outside /libretro are untouched.
                destination = (
                    project_root
                    / "data"
                    / "games"
                    / "user_content"
                    / game_id
                    / "cheats"
                    / "libretro"
                )
                if destination.exists():
                    shutil.rmtree(destination)
                updated_games[game_id] = {
                    "id": game_id,
                    "scanned_title": str(game.get("title", "")),
                    "canonical_title": identity["canonical_title"],
                    "system": system_id,
                    "updated_unix_ms": now_ms,
                    "provider": "libretro",
                    "status": "no_cheats",
                    "files": [],
                }

        elif status == "ambiguous":
            counts["ambiguous"] += 1
            if download_files:
                if game_id in previous_games:
                    updated_games[game_id] = previous_games[game_id]
                    counts["prior_preserved"] += 1
                    diagnostic["result"] = "prior_preserved"
                else:
                    updated_games[game_id] = {
                        "id": game_id,
                        "scanned_title": str(game.get("title", "")),
                        "canonical_title": identity["canonical_title"],
                        "system": system_id,
                        "updated_unix_ms": now_ms,
                        "provider": "libretro",
                        "status": "ambiguous",
                        "files": [],
                    }

        elif status == "provider_unavailable":
            counts["provider_unavailable"] += 1
            if download_files and game_id in previous_games:
                updated_games[game_id] = previous_games[game_id]
                counts["prior_preserved"] += 1
                diagnostic["result"] = "prior_preserved"

        else:
            counts["errors"] += 1

        diagnostics.append(diagnostic)

    if download_files:
        # Partial runs are additive: preserve manifest records outside selection.
        for game_id, record in previous_games.items():
            if str(game_id) not in processed_ids:
                updated_games[str(game_id)] = record

        payload = {
            "schema_version": CHEAT_SCHEMA_VERSION,
            "generated_unix_ms": now_ms,
            "provider_priority": ["libretro"],
            "attribution": {
                "libretro_database_cheats": LIBRETRO_CHEAT_ATTRIBUTION,
            },
            "games": updated_games,
        }
        _atomic_json_write(manifest_path, payload)

    report = {
        "ok": True,
        "generated_unix_ms": now_ms,
        "project_root": str(project_root),
        "manifest_path": str(manifest_path),
        "metadata_path": str(metadata_path),
        "offline": bool(offline),
        "refresh_provider_cache": bool(refresh_provider_cache),
        "download_files": bool(download_files),
        "only_system": only_system,
        "limit": int(limit),
        "counts": counts,
        "provider_stats": provider.stats,
        "games": diagnostics,
    }
    _atomic_json_write(log_json_path, report)

    lines = [
        "PrivyHub game cheat updater",
        "Provider: libretro-database/cht (local cache; activation disabled)",
        f"Games scanned: {counts['total_games']}",
        f"Metadata ready: {counts['metadata_ready']}",
        f"Games with cheats: {counts['games_with_cheats']}",
        f"Cheat files matched: {counts['cheat_files_matched']}",
        f"No cheats: {counts['no_cheats']}",
        f"Ambiguous: {counts['ambiguous']}",
        f"Metadata missing: {counts['metadata_missing']}",
        f"Provider unavailable: {counts['provider_unavailable']}",
        f"Invalid cheat files: {counts['invalid_cheat_files']}",
        f"Prior cache preserved: {counts['prior_preserved']}",
        (
            "Cheat files: "
            f"{counts['cheat_files_downloaded']} downloaded, "
            f"{counts['cheat_files_cached_source']} source-cache reused"
        ),
        f"Cheat codes cataloged: {counts['cheat_codes_cataloged']}",
        f"Upstream enabled entries forced off: {counts['forced_disabled']}",
        (
            "Provider index cache: "
            f"{provider.stats['index_downloads']} downloaded, "
            f"{provider.stats['index_cache_hits']} reused, "
            f"{provider.stats['index_unavailable']} unavailable"
        ),
        (
            "Provider file cache: "
            f"{provider.stats['file_downloads']} downloaded, "
            f"{provider.stats['file_cache_hits']} reused, "
            f"{provider.stats['file_unavailable']} unavailable"
        ),
        "Activation: DISABLED (A7.2 catalog/cache only)",
        f"Manifest: {manifest_path}",
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
