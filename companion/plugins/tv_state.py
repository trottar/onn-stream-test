from __future__ import annotations

import hashlib
import json
import os
import threading
import time

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


class TvStatePlugin:
    """Linux-authoritative durable TV user-state store."""

    PLUGIN_ID = "tv_state"

    STATUS_SCHEMA = "privyhub_tv_state_status_v1"
    ENVELOPE_SCHEMA = "privyhub_tv_state_envelope_v1"
    UPDATE_SCHEMA = "privyhub_tv_state_update_v1"
    USER_STATE_SCHEMA = "privyhub_tv_user_state_v1"
    STORAGE_SCHEMA = 1

    MAX_MANAGED_PROVIDERS = 64
    MAX_CUSTOM_PROVIDERS = 256
    MAX_CHANNELS = 10_000

    MAX_PROVIDER_ID_CHARS = 128
    MAX_PROVIDER_NAME_CHARS = 200
    MAX_URL_CHARS = 4_096
    MAX_LANGUAGE_CODE_CHARS = 32
    MAX_LANGUAGE_NAME_CHARS = 128
    MAX_COUNTRY_CODE_CHARS = 16
    MAX_COUNTRY_NAME_CHARS = 128

    MAX_STREAM_ID_CHARS = 160
    MAX_CHANNEL_NAME_CHARS = 240
    MAX_CATEGORY_CHARS = 128
    MAX_HEADER_CHARS = 1_024
    MAX_FAVORITE_GROUP_CHARS = 160
    MAX_CLIENT_ID_CHARS = 96

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
            else self.project_root / "data" / "tv_state"
        )
        self.state_path = self.data_root / "state.json"
        self._lock = threading.RLock()

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _bool(value: Any, field: str) -> bool:
        if not isinstance(value, bool):
            raise ValueError(f"{field} must be a boolean")
        return value

    @staticmethod
    def _int(
        value: Any,
        field: str,
        *,
        minimum: int = 0,
        maximum: int = 2_147_483_647,
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field} must be an integer")
        if value < minimum or value > maximum:
            raise ValueError(f"{field} is out of range")
        return value

    @staticmethod
    def _obj(value: Any, field: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError(f"{field} must be an object")
        return value

    @staticmethod
    def _array(value: Any, field: str) -> list[Any]:
        if not isinstance(value, list):
            raise ValueError(f"{field} must be an array")
        return value

    @staticmethod
    def _string(
        value: Any,
        field: str,
        *,
        max_chars: int,
        allow_blank: bool = True,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{field} must be a string")
        clean = value.strip()
        if not allow_blank and not clean:
            raise ValueError(f"{field} must not be blank")
        if len(clean) > max_chars:
            raise ValueError(f"{field} is too long")
        if any(ord(ch) < 0x20 for ch in clean):
            raise ValueError(f"{field} contains control characters")
        return clean

    @classmethod
    def _optional_string(
        cls,
        obj: dict[str, Any],
        key: str,
        *,
        max_chars: int,
    ) -> str:
        value = obj.get(key, "")
        if value is None:
            return ""
        return cls._string(
            value,
            key,
            max_chars=max_chars,
            allow_blank=True,
        )

    @staticmethod
    def _canonical_json(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    @classmethod
    def _state_sha256(cls, state: dict[str, Any]) -> str:
        return hashlib.sha256(
            cls._canonical_json(state).encode("utf-8")
        ).hexdigest()

    @classmethod
    def _normalize_preferences(
        cls,
        raw: Any,
    ) -> dict[str, str]:
        obj = cls._obj(raw, "preferences")

        language_code = cls._string(
            obj.get("language_code", "eng"),
            "preferences.language_code",
            max_chars=cls.MAX_LANGUAGE_CODE_CHARS,
            allow_blank=False,
        )
        language_name = cls._string(
            obj.get("language_name", "English"),
            "preferences.language_name",
            max_chars=cls.MAX_LANGUAGE_NAME_CHARS,
            allow_blank=False,
        )
        country_code = cls._string(
            obj.get("country_code", ""),
            "preferences.country_code",
            max_chars=cls.MAX_COUNTRY_CODE_CHARS,
            allow_blank=True,
        )
        country_name = cls._string(
            obj.get("country_name", "All Countries"),
            "preferences.country_name",
            max_chars=cls.MAX_COUNTRY_NAME_CHARS,
            allow_blank=False,
        )

        return {
            "language_code": language_code,
            "language_name": language_name,
            "country_code": country_code,
            "country_name": country_name,
        }

    @classmethod
    def _normalize_managed_providers(
        cls,
        raw: Any,
    ) -> list[dict[str, Any]]:
        items = cls._array(raw, "managed_providers")
        if len(items) > cls.MAX_MANAGED_PROVIDERS:
            raise ValueError("managed_providers contains too many entries")

        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        for index, raw_item in enumerate(items):
            item = cls._obj(
                raw_item,
                f"managed_providers[{index}]",
            )
            provider_id = cls._string(
                item.get("provider_id", ""),
                f"managed_providers[{index}].provider_id",
                max_chars=cls.MAX_PROVIDER_ID_CHARS,
                allow_blank=False,
            )
            if provider_id in seen:
                raise ValueError(
                    f"managed_providers contains duplicate provider_id: {provider_id}"
                )
            seen.add(provider_id)
            result.append(
                {
                    "provider_id": provider_id,
                    "enabled": cls._bool(
                        item.get("enabled", False),
                        f"managed_providers[{index}].enabled",
                    ),
                }
            )

        result.sort(key=lambda item: str(item["provider_id"]).casefold())
        return result

    @classmethod
    def _validate_url(
        cls,
        value: Any,
        field: str,
    ) -> str:
        url = cls._string(
            value,
            field,
            max_chars=cls.MAX_URL_CHARS,
            allow_blank=False,
        )
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"{field} must use http:// or https://")
        return url

    @classmethod
    def _normalize_custom_providers(
        cls,
        raw: Any,
    ) -> list[dict[str, Any]]:
        items = cls._array(raw, "providers")
        if len(items) > cls.MAX_CUSTOM_PROVIDERS:
            raise ValueError("providers contains too many entries")

        result: list[dict[str, Any]] = []
        identities: set[tuple[str, str]] = set()

        for index, raw_item in enumerate(items):
            item = cls._obj(
                raw_item,
                f"providers[{index}]",
            )
            name = cls._string(
                item.get("name", "Custom M3U"),
                f"providers[{index}].name",
                max_chars=cls.MAX_PROVIDER_NAME_CHARS,
                allow_blank=False,
            )
            url = cls._validate_url(
                item.get("url", ""),
                f"providers[{index}].url",
            )
            language_code = cls._string(
                item.get("language_code", "eng"),
                f"providers[{index}].language_code",
                max_chars=cls.MAX_LANGUAGE_CODE_CHARS,
                allow_blank=False,
            )
            enabled = cls._bool(
                item.get("enabled", True),
                f"providers[{index}].enabled",
            )

            identity = (name.casefold(), url)
            if identity in identities:
                raise ValueError("providers contains a duplicate name/url pair")
            identities.add(identity)

            result.append(
                {
                    "name": name,
                    "url": url,
                    "language_code": language_code,
                    "enabled": enabled,
                }
            )

        result.sort(
            key=lambda item: (
                str(item["name"]).casefold(),
                str(item["url"]),
            )
        )
        return result

    @classmethod
    def _normalize_channels(
        cls,
        raw: Any,
    ) -> list[dict[str, Any]]:
        items = cls._array(raw, "channels")
        if len(items) > cls.MAX_CHANNELS:
            raise ValueError("channels contains too many entries")

        result: list[dict[str, Any]] = []
        seen: set[str] = set()

        for index, raw_item in enumerate(items):
            item = cls._obj(
                raw_item,
                f"channels[{index}]",
            )
            stream_id = cls._string(
                item.get("stream_id", ""),
                f"channels[{index}].stream_id",
                max_chars=cls.MAX_STREAM_ID_CHARS,
                allow_blank=False,
            )
            if not stream_id.startswith("tv_stream_"):
                raise ValueError(
                    f"channels[{index}].stream_id is not a TV stream id"
                )
            if stream_id in seen:
                raise ValueError(
                    f"channels contains duplicate stream_id: {stream_id}"
                )
            seen.add(stream_id)

            normalized = {
                "stream_id": stream_id,
                "favorite": cls._bool(
                    item.get("favorite", False),
                    f"channels[{index}].favorite",
                ),
                "manual_hidden": cls._bool(
                    item.get("manual_hidden", False),
                    f"channels[{index}].manual_hidden",
                ),
                "custom_name": cls._optional_string(
                    item,
                    "custom_name",
                    max_chars=cls.MAX_CHANNEL_NAME_CHARS,
                ),
                "custom_category": cls._optional_string(
                    item,
                    "custom_category",
                    max_chars=cls.MAX_CATEGORY_CHARS,
                ),
                "custom_url": cls._optional_string(
                    item,
                    "custom_url",
                    max_chars=cls.MAX_URL_CHARS,
                ),
                "custom_referrer": cls._optional_string(
                    item,
                    "custom_referrer",
                    max_chars=cls.MAX_HEADER_CHARS,
                ),
                "custom_user_agent": cls._optional_string(
                    item,
                    "custom_user_agent",
                    max_chars=cls.MAX_HEADER_CHARS,
                ),
                "favorite_group": cls._optional_string(
                    item,
                    "favorite_group",
                    max_chars=cls.MAX_FAVORITE_GROUP_CHARS,
                ),
                "favorite_order": cls._int(
                    item.get("favorite_order", 0),
                    f"channels[{index}].favorite_order",
                    minimum=0,
                    maximum=1_000_000,
                ),
                "protect_auto_hide": cls._bool(
                    item.get("protect_auto_hide", False),
                    f"channels[{index}].protect_auto_hide",
                ),
            }

            custom_url = str(normalized["custom_url"])
            if custom_url:
                cls._validate_url(
                    custom_url,
                    f"channels[{index}].custom_url",
                )

            has_intent = (
                bool(normalized["favorite"])
                or bool(normalized["manual_hidden"])
                or bool(normalized["custom_name"])
                or bool(normalized["custom_category"])
                or bool(normalized["custom_url"])
                or bool(normalized["custom_referrer"])
                or bool(normalized["custom_user_agent"])
                or bool(normalized["favorite_group"])
                or int(normalized["favorite_order"]) > 0
                or bool(normalized["protect_auto_hide"])
            )
            if has_intent:
                result.append(normalized)

        result.sort(key=lambda item: str(item["stream_id"]))
        return result

    @classmethod
    def normalize_user_state(
        cls,
        raw: Any,
    ) -> dict[str, Any]:
        state = cls._obj(raw, "state")

        schema = state.get("schema")
        if schema != cls.USER_STATE_SCHEMA:
            raise ValueError(
                f"state.schema must be {cls.USER_STATE_SCHEMA}"
            )

        return {
            "schema": cls.USER_STATE_SCHEMA,
            "preferences": cls._normalize_preferences(
                state.get("preferences", {})
            ),
            "managed_providers": cls._normalize_managed_providers(
                state.get("managed_providers", [])
            ),
            "providers": cls._normalize_custom_providers(
                state.get("providers", [])
            ),
            "channels": cls._normalize_channels(
                state.get("channels", [])
            ),
        }

    def _load_envelope_unlocked(
        self,
    ) -> dict[str, Any] | None:
        if not self.state_path.is_file():
            return None

        try:
            payload = json.loads(
                self.state_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise RuntimeError(
                "TV state store is unreadable"
            ) from exc

        if not isinstance(payload, dict):
            raise RuntimeError(
                "TV state store has an invalid root"
            )

        if payload.get("storage_schema") != self.STORAGE_SCHEMA:
            raise RuntimeError(
                "TV state store schema is unsupported"
            )

        revision = payload.get("server_revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            raise RuntimeError(
                "TV state store revision is invalid"
            )

        state = self.normalize_user_state(
            payload.get("state")
        )
        expected_hash = self._state_sha256(
            state
        )
        if payload.get("state_sha256") != expected_hash:
            raise RuntimeError(
                "TV state store hash mismatch"
            )

        return {
            "storage_schema": self.STORAGE_SCHEMA,
            "server_revision": revision,
            "updated_at_ms": int(
                payload.get("updated_at_ms") or 0
            ),
            "updated_by": str(
                payload.get("updated_by") or ""
            ),
            "state_sha256": expected_hash,
            "state": state,
        }

    def _write_envelope_unlocked(
        self,
        envelope: dict[str, Any],
    ) -> None:
        self.data_root.mkdir(
            parents=True,
            exist_ok=True,
        )
        temp = self.state_path.with_suffix(
            f".{os.getpid()}.tmp"
        )
        data = (
            json.dumps(
                envelope,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n"
        )

        try:
            with temp.open(
                "w",
                encoding="utf-8",
                newline="\n",
            ) as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, 0o600)
            os.replace(
                temp,
                self.state_path,
            )
            try:
                directory_fd = os.open(
                    self.data_root,
                    os.O_RDONLY,
                )
            except OSError:
                directory_fd = None
            if directory_fd is not None:
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        finally:
            try:
                temp.unlink()
            except FileNotFoundError:
                pass

    @staticmethod
    def _public_envelope(
        envelope: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if envelope is None:
            return {
                "schema": TvStatePlugin.ENVELOPE_SCHEMA,
                "ok": True,
                "initialized": False,
                "server_revision": 0,
                "updated_at_ms": 0,
                "updated_by": "",
                "state_sha256": None,
                "state": None,
            }

        return {
            "schema": TvStatePlugin.ENVELOPE_SCHEMA,
            "ok": True,
            "initialized": True,
            "server_revision": int(
                envelope["server_revision"]
            ),
            "updated_at_ms": int(
                envelope["updated_at_ms"]
            ),
            "updated_by": str(
                envelope["updated_by"]
            ),
            "state_sha256": str(
                envelope["state_sha256"]
            ),
            "state": envelope["state"],
        }

    def state(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            return self._public_envelope(
                self._load_envelope_unlocked()
            )

    def status(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            envelope = self._load_envelope_unlocked()

        if envelope is None:
            revision = 0
            updated_at_ms = 0
            state_sha256 = None
        else:
            revision = int(
                envelope["server_revision"]
            )
            updated_at_ms = int(
                envelope["updated_at_ms"]
            )
            state_sha256 = str(
                envelope["state_sha256"]
            )

        return {
            "schema": self.STATUS_SCHEMA,
            "ok": True,
            "plugin": self.PLUGIN_ID,
            "initialized": envelope is not None,
            "server_revision": revision,
            "updated_at_ms": updated_at_ms,
            "state_sha256": state_sha256,
            "state_path": str(
                self.state_path
            ),
        }

    def put_state(
        self,
        payload: Any,
    ) -> dict[str, Any]:
        update = self._obj(
            payload,
            "payload",
        )

        if update.get("schema") != self.UPDATE_SCHEMA:
            raise ValueError(
                f"payload.schema must be {self.UPDATE_SCHEMA}"
            )

        base_revision = self._int(
            update.get("base_revision"),
            "base_revision",
            minimum=0,
        )
        client_id = self._string(
            update.get("client_id", ""),
            "client_id",
            max_chars=self.MAX_CLIENT_ID_CHARS,
            allow_blank=False,
        )
        state = self.normalize_user_state(
            update.get("state")
        )
        state_sha256 = self._state_sha256(
            state
        )

        with self._lock:
            current = self._load_envelope_unlocked()
            current_revision = (
                int(current["server_revision"])
                if current is not None
                else 0
            )

            if base_revision != current_revision:
                public = self._public_envelope(
                    current
                )
                return {
                    "schema": self.ENVELOPE_SCHEMA,
                    "ok": False,
                    "conflict": True,
                    "error_code": "revision_conflict",
                    "base_revision": base_revision,
                    "server_revision": current_revision,
                    "current": public,
                }

            if (
                current is not None
                and current["state_sha256"]
                == state_sha256
            ):
                result = self._public_envelope(
                    current
                )
                result["changed"] = False
                result["conflict"] = False
                return result

            revision = current_revision + 1
            envelope = {
                "storage_schema": self.STORAGE_SCHEMA,
                "server_revision": revision,
                "updated_at_ms": self._now_ms(),
                "updated_by": client_id,
                "state_sha256": state_sha256,
                "state": state,
            }

            self._write_envelope_unlocked(
                envelope
            )

            verified = self._load_envelope_unlocked()
            if (
                verified is None
                or verified["server_revision"] != revision
                or verified["state_sha256"] != state_sha256
            ):
                raise RuntimeError(
                    "TV state write verification failed"
                )

            result = self._public_envelope(
                verified
            )
            result["changed"] = True
            result["conflict"] = False
            return result

    def handle(
        self,
        action: str,
        raw_query: str,
    ) -> dict[str, Any]:
        del raw_query

        if action == "status":
            return self.status()

        if action == "state":
            return self.state()

        raise ValueError(
            f"Unknown TV-state action: {action}"
        )

    def handle_post_json_request(
        self,
        action: str,
        raw_query: str,
        payload: dict[str, Any],
        client_address: str,
    ) -> dict[str, Any]:
        del raw_query
        del client_address

        if action == "state":
            return self.put_state(
                payload
            )

        raise ValueError(
            f"Unknown TV-state POST action: {action}"
        )

    def shutdown(self) -> None:
        return None
