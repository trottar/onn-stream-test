from __future__ import annotations

import hashlib
import threading
import time
import urllib.error
import urllib.request

from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse


class IPTVOrgPlugin:
    """Lazy, low-overhead catalog adapter for iptv-org public playlists."""

    PLUGIN_ID = "iptv_org"
    BASE_URL = "https://iptv-org.github.io/iptv/categories"
    CACHE_SECONDS = 15 * 60
    PAGE_SIZE = 80
    FETCH_TIMEOUT_SECONDS = 12.0

    # Kept local on purpose: loading the giant all-channel playlist merely to
    # discover category names would work against the minimal-resource goal.
    CATEGORIES = (
        ("animation", "Animation"),
        ("auto", "Auto"),
        ("business", "Business"),
        ("classic", "Classic"),
        ("comedy", "Comedy"),
        ("cooking", "Cooking"),
        ("culture", "Culture"),
        ("documentary", "Documentary"),
        ("education", "Education"),
        ("entertainment", "Entertainment"),
        ("family", "Family"),
        ("general", "General"),
        ("interactive", "Interactive"),
        ("kids", "Kids"),
        ("legislative", "Legislative"),
        ("lifestyle", "Lifestyle"),
        ("movies", "Movies"),
        ("music", "Music"),
        ("news", "News"),
        ("outdoor", "Outdoor"),
        ("public", "Public"),
        ("relax", "Relax"),
        ("religious", "Religious"),
        ("science", "Science"),
        ("series", "Series"),
        ("shop", "Shop"),
        ("sports", "Sports"),
        ("travel", "Travel"),
        ("weather", "Weather"),
        ("undefined", "Undefined"),
    )

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: dict[str, tuple[float, list[dict[str, str]]]] = {}
        self._category_names = dict(self.CATEGORIES)

    @staticmethod
    def _stable_id(category: str, url: str) -> str:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        return f"iptv_{category}_{digest}"

    @staticmethod
    def _first(query: dict[str, list[str]], key: str, default: str = "") -> str:
        values = query.get(key)
        if not values:
            return default
        return values[0]

    @staticmethod
    def _parse_int(value: str, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _playlist_url(self, category: str) -> str:
        if category not in self._category_names:
            raise ValueError(f"Unknown IPTV category: {category}")
        return f"{self.BASE_URL}/{category}.m3u"

    def _fetch_playlist(self, category: str) -> str:
        request = urllib.request.Request(
            self._playlist_url(category),
            headers={
                "User-Agent": "PrivyHub/0.1 (+iptv-org catalog adapter)",
                "Accept": "audio/x-mpegurl, application/vnd.apple.mpegurl, text/plain, */*",
            },
            method="GET",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.FETCH_TIMEOUT_SECONDS,
            ) as response:
                if response.status != 200:
                    raise RuntimeError(f"IPTV playlist returned HTTP {response.status}")

                return response.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Unable to fetch IPTV playlist: {exc}") from exc

    @staticmethod
    def _parse_playlist(text: str) -> list[dict[str, str]]:
        channels: list[dict[str, str]] = []
        pending_name: str | None = None

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith("#EXTINF:"):
                if "," in line:
                    pending_name = line.split(",", 1)[1].strip()
                else:
                    pending_name = "Channel"
                continue

            if line.startswith("#"):
                continue

            if pending_name is None:
                continue

            parsed = urlparse(line)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                pending_name = None
                continue

            channels.append(
                {
                    "name": pending_name or "Channel",
                    "url": line,
                }
            )
            pending_name = None

        # De-duplicate exact stream URLs while preserving the first display name.
        deduped: dict[str, dict[str, str]] = {}
        for channel in channels:
            deduped.setdefault(channel["url"], channel)

        return sorted(
            deduped.values(),
            key=lambda item: item["name"].casefold(),
        )

    def _channels(self, category: str) -> list[dict[str, str]]:
        now = time.monotonic()

        with self._lock:
            cached = self._cache.get(category)
            if cached is not None:
                cached_at, channels = cached
                if now - cached_at < self.CACHE_SECONDS:
                    return channels

        channels = self._parse_playlist(self._fetch_playlist(category))

        with self._lock:
            self._cache[category] = (now, channels)

        return channels

    @staticmethod
    def _lazy_category(node_id: str, name: str, lazy_path: str) -> dict[str, Any]:
        return {
            "id": node_id,
            "name": name,
            "node_type": "category",
            "children": [],
            "lazy_path": lazy_path,
        }

    def categories(self) -> dict[str, Any]:
        nodes = []
        for slug, name in self.CATEGORIES:
            query = urlencode({"category": slug})
            nodes.append(
                self._lazy_category(
                    node_id=f"iptv_category_{slug}",
                    name=name,
                    lazy_path=f"/plugins/{self.PLUGIN_ID}/channels?{query}",
                )
            )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "nodes": nodes,
        }

    def channels(self, query: dict[str, list[str]]) -> dict[str, Any]:
        category = self._first(query, "category").strip().casefold()
        if category not in self._category_names:
            raise ValueError("Missing or invalid IPTV category")

        channels = self._channels(category)
        category_name = self._category_names[category]

        offset_text = self._first(query, "offset")
        offset_supplied = bool(offset_text)
        offset = max(0, self._parse_int(offset_text, 0))
        limit = self._parse_int(self._first(query, "limit"), self.PAGE_SIZE)
        limit = min(max(1, limit), self.PAGE_SIZE)

        # Large categories are broken into pages so Android TV never creates
        # thousands of Button views at once.
        if not offset_supplied and len(channels) > self.PAGE_SIZE:
            page_nodes = []
            page_number = 1
            for start in range(0, len(channels), self.PAGE_SIZE):
                end = min(start + self.PAGE_SIZE, len(channels))
                params = urlencode(
                    {
                        "category": category,
                        "offset": start,
                        "limit": self.PAGE_SIZE,
                    }
                )
                page_nodes.append(
                    self._lazy_category(
                        node_id=f"iptv_{category}_page_{page_number:02d}",
                        name=f"Page {page_number:02d} ({start + 1}-{end})",
                        lazy_path=f"/plugins/{self.PLUGIN_ID}/channels?{params}",
                    )
                )
                page_number += 1

            return {
                "ok": True,
                "plugin": self.PLUGIN_ID,
                "category": category,
                "category_name": category_name,
                "total": len(channels),
                "nodes": page_nodes,
            }

        selected = channels[offset: offset + limit]
        nodes = []

        for channel in selected:
            nodes.append(
                {
                    "id": self._stable_id(category, channel["url"]),
                    "name": channel["name"],
                    "node_type": "source",
                    "playback": {
                        "type": "live",
                        "url": channel["url"],
                    },
                }
            )

        return {
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "category": category,
            "category_name": category_name,
            "total": len(channels),
            "offset": offset,
            "count": len(nodes),
            "nodes": nodes,
        }

    def handle(self, action: str, raw_query: str) -> dict[str, Any]:
        query = parse_qs(raw_query, keep_blank_values=False)

        if action == "categories":
            return self.categories()

        if action == "channels":
            return self.channels(query)

        raise ValueError(f"Unknown IPTV plugin action: {action}")
