"""CL-B1: the decoder session report as a POST body, and the access log's
guard against a request that never got a path.

The client used to send the report URL-encoded in the request target
(`?report=`), which `http.server` caps at a 65,536-byte request line (~41K
decoded characters, C3-L3A-R2B). The body form removes that ceiling; the
target form is still accepted unchanged, so an older APK keeps working.
Pure helpers, no I/O of their own, so they are unit-testable without the
companion.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlsplit

from games.decoder_session_log import MAX_REPORT_CHARS

# UTF-8 is at most 4 bytes a character, so this never refuses a body whose
# decoded report is within MAX_REPORT_CHARS -- the cap stays the only limit.
MAX_BODY_BYTES = MAX_REPORT_CHARS * 4


def body_length(headers: Any) -> int:
    """Content-Length of a report body; 0 when there is none."""
    raw = headers.get("Content-Length") if headers is not None else None
    if raw is None or str(raw).strip() == "":
        return 0
    try:
        n = int(str(raw).strip())
    except ValueError as exc:
        raise ValueError("Invalid Content-Length") from exc
    if n < 0:
        raise ValueError("Invalid Content-Length")
    if n > MAX_BODY_BYTES:
        raise ValueError("Decoder session report is too large")
    return n


def report_from_body(body: bytes, content_type: str | None) -> str:
    """The report text from a body: JSON as-is, or a form's `report` field."""
    text = body.decode("utf-8")
    ctype = (content_type or "").split(";", 1)[0].strip().lower()
    if ctype == "application/x-www-form-urlencoded":
        return (parse_qs(text).get("report") or [""])[0].strip()
    return text.strip()


def access_log_path(handler: Any) -> str:
    """The request path for the access log, or '' when there is none.

    `http.server` logs a 414 (request line over 65,536 bytes) before it has
    parsed a path, so `handler.path` does not exist yet; reading it raised
    AttributeError inside `log_message` and no 414 was ever sent
    (C3-L3A-R2B). This never raises.
    """
    try:
        return urlsplit(getattr(handler, "path", "") or "").path
    except Exception:
        return ""
