"""B35: the VOD range server's per-request log and the movie player's retry rows.

Only with `PRIVYHUB_VOD_LOG=1` in the service's environment (the range server inherits it). Absent = today:
this module is never imported, the range server's handler class is not touched, the service has no new route.

- `RangeLog.install(handler_class)` wraps the range server's handler on the class: one row per request into
  `logs/vod_range.jsonl` -- when it started and ended, the Range header, the status, the length, the bytes actually
  written, the duration, and how it closed (complete / short / client_reset / broken_pipe / error / no_body). An
  exception is re-raised, so today's traceback still reaches the range server's log.
- `ClientLog.accept(payload)` -- the client's `vod_error` / `vod_retry` / `vod_resumed` / `vod_gave_up` rows
  (`POST /diagnostics/vod-client`), field by field, into `logs/vod_client.jsonl`.

Redacted by construction: no address, no file path, no title, no URL, no query (the media token) in any row; the
media is an opaque 12-hex id.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote, urlsplit

from games.log_rotation import append_line

FLAG_ENV = "PRIVYHUB_VOD_LOG"
RANGE_LOG_NAME = "vod_range.jsonl"
CLIENT_LOG_NAME = "vod_client.jsonl"
MAX_BYTES = 5 * 1024 * 1024
KEEP = 3
_RANGE_SHAPE = re.compile(r"^bytes=\d{0,19}-\d{0,19}$")
CLIENT_EVENTS = ("vod_error", "vod_retry", "vod_resumed", "vod_gave_up")
CLIENT_INT_FIELDS = ("attempt", "position_ms", "error_code", "delay_ms", "elapsed_ms", "bound_ms", "attempts")
_HEX12 = re.compile(r"^[0-9a-f]{12}$")
_CODE_NAME = re.compile(r"^[A-Z0-9_]{1,64}$")
# B43: the retry's reason / give-up kind / token refetch (a B35 client sends none of them: its rows as today)
CLIENT_REASONS = ("reset", "refused", "timeout", "401", "403")
CLIENT_KINDS = ("lost", "refused")


def enabled(environ: Mapping[str, str]) -> bool:
    return (environ.get(FLAG_ENV) or "").strip() == "1"


def utc_ms(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def opaque_id(request_path: str) -> str:
    """12 hex over the URL path only (the query -- the media token -- dropped first)."""
    path = unquote(urlsplit(request_path).path)
    return hashlib.sha256(("privyhub-vod:" + path).encode("utf-8", "replace")).hexdigest()[:12]


def _kind(request_path: str) -> str:
    parts = [p for p in unquote(urlsplit(request_path).path).split("/") if p]
    return "vod" if parts[:1] == ["vod"] else "media"


class _Writer:
    """Appends JSON rows to one rotating log under logs/; one lock per file."""

    def __init__(self, project_root: Path, name: str) -> None:
        self.path = Path(project_root) / "logs" / name
        self._lock = threading.Lock()

    def write(self, row: Mapping[str, Any]) -> None:
        line = json.dumps(row, sort_keys=False)
        with self._lock:
            append_line(self.path, line, max_bytes=MAX_BYTES, keep=KEEP)


class _Counting:
    """The socket file, counting what was written to it."""

    def __init__(self, raw: Any, box: dict) -> None:
        self._raw = raw
        self._box = box

    def write(self, data: Any) -> Any:
        n = self._raw.write(data)
        self._box["bytes"] += len(data) if n is None else n
        return n

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw, name)


class RangeLog:
    def __init__(self, project_root: Path, clock=time.time, mono=time.monotonic) -> None:
        self._out = _Writer(project_root, RANGE_LOG_NAME)
        self._clock = clock
        self._mono = mono

    def install(self, handler_class: type) -> type:
        log = self
        orig_send_response = handler_class.send_response
        orig_send_header = handler_class.send_header
        orig_copyfile = handler_class.copyfile

        def send_response(self, code, message=None):
            box = getattr(self, "_b35_box", None)
            if box is not None and box["status"] is None:
                box["status"] = int(code)
            return orig_send_response(self, code, message)

        def send_header(self, keyword, value):
            box = getattr(self, "_b35_box", None)
            if box is not None and str(keyword).lower() == "content-length":
                try:
                    box["length"] = int(value)
                except (TypeError, ValueError):
                    pass
            return orig_send_header(self, keyword, value)

        def copyfile(self, source, outputfile):
            box = getattr(self, "_b35_box", None)
            if box is None:
                return orig_copyfile(self, source, outputfile)
            box["body"] = True
            return orig_copyfile(self, source, _Counting(outputfile, box))

        def wrap(method_name: str):
            orig = getattr(handler_class, method_name)

            def logged(self):
                box = {"status": None, "length": None, "bytes": 0, "body": False}
                self._b35_box = box
                t0, m0 = log._clock(), log._mono()
                closed, error = None, None
                try:
                    return orig(self)
                except BrokenPipeError:
                    closed = "broken_pipe"
                    raise
                except ConnectionResetError:
                    closed = "client_reset"
                    raise
                except Exception as exc:
                    closed, error = "error", type(exc).__name__
                    raise
                finally:
                    self._b35_box = None
                    try:
                        log._row(self, method_name[3:], box, t0, m0, closed, error)
                    except Exception:
                        pass  # the log must never disturb a request

            logged.__name__ = method_name
            return logged

        handler_class.send_response = send_response
        handler_class.send_header = send_header
        handler_class.copyfile = copyfile
        handler_class.do_GET = wrap("do_GET")
        handler_class.do_HEAD = wrap("do_HEAD")
        return handler_class

    def _row(self, handler: Any, method: str, box: dict, t0: float, m0: float, closed, error) -> None:
        if closed is None:
            if not box["body"]:
                closed = "no_body"
            elif box["length"] is not None and box["bytes"] < box["length"]:
                closed = "short"
            else:
                closed = "complete"
        rng = None
        try:
            raw = handler.headers.get("Range")
        except Exception:
            raw = None
        if raw is not None:
            rng = raw.strip() if _RANGE_SHAPE.match(raw.strip()) else "invalid"
        row = {
            "at_utc": utc_ms(t0),
            "end_utc": utc_ms(self._clock()),
            "event": "vod_range",
            "method": method,
            "id": opaque_id(getattr(handler, "path", "") or ""),
            "kind": _kind(getattr(handler, "path", "") or ""),
            "range": rng,
            "status": box["status"],
            "length": box["length"],
            "bytes": box["bytes"],
            "duration_ms": int(round((self._mono() - m0) * 1000)),
            "closed": closed,
        }
        if error:
            row["error"] = error
        self._out.write(row)


class ClientLog:
    def __init__(self, project_root: Path, clock=time.time) -> None:
        self._out = _Writer(project_root, CLIENT_LOG_NAME)
        self._clock = clock

    def accept(self, payload: Any) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("vod-client: an object expected")
        event = payload.get("event")
        if event not in CLIENT_EVENTS:
            raise ValueError("vod-client: unknown event")
        row: dict[str, Any] = {"at_utc": utc_ms(self._clock()), "event": event}
        for key, value in payload.items():
            if key == "event":
                continue
            if key in CLIENT_INT_FIELDS:
                if isinstance(value, bool) or not isinstance(value, int):
                    raise ValueError(f"vod-client: {key} not an int")
                row[key] = value
            elif key == "media":
                if not isinstance(value, str) or not _HEX12.match(value):
                    raise ValueError("vod-client: media not an opaque id")
                row[key] = value
            elif key == "error_name":
                if not isinstance(value, str) or not _CODE_NAME.match(value):
                    raise ValueError("vod-client: error_name not a code name")
                row[key] = value
            elif key == "reason":
                if value not in CLIENT_REASONS:
                    raise ValueError("vod-client: reason unknown")
                row[key] = value
            elif key == "kind":
                if value not in CLIENT_KINDS:
                    raise ValueError("vod-client: kind unknown")
                row[key] = value
            elif key == "token_refetched":
                if not isinstance(value, bool):
                    raise ValueError("vod-client: token_refetched not a bool")
                row[key] = value
            else:
                raise ValueError("vod-client: unknown field")
        self._out.write(row)
        return {"ok": True, "recorded": event}


def range_log_from_environ(environ: Mapping[str, str], project_root: Path) -> RangeLog | None:
    return RangeLog(project_root) if enabled(environ) else None


def client_log_from_environ(environ: Mapping[str, str], project_root: Path) -> ClientLog | None:
    return ClientLog(project_root) if enabled(environ) else None
