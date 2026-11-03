"""B32: the client's `surface_lost` row, host side.

A client with `debug.privyhub.surface_hold=<1|ms>` adds `surface_lost=<compact JSON>` to one heartbeat after each loss
of its screen (held within the bound, or restarted past it). This module is imported by the heartbeat handler only when
that key is present: **no key = nothing imported, nothing written (today byte for byte)**. The value is parsed with a
whitelist (keys, types, fixed words, list lengths, a 1,024-char cap); anything else is dropped, never echoed. One
recovery-log row `{"event": "surface_lost", ...}` per accepted value. Design:
`docs/memory/evidence/b32_2026-10-31/design_written_before_code.md` (hashed before this code).
"""

from __future__ import annotations

import json
import re
from typing import Any

MAX_CHARS = 1024
INTS = ("seq", "bound_ms", "away_ms", "paused_before_ms", "focus_lost_before_ms", "top_lost_before_ms",
        "first_frame_ms")
BOOLS = ("user_leave", "interactive")
OUTCOMES = {"held", "restarted"}
REASONS = {"pad_system_key", "remote_system_key", "user_leave", "screen_off", "input_device", "top_lost",
           "focus_lost", "unknown"}
KEY_RE = re.compile(r"^\d{1,4}:(pad|remote|other):[cp]$")
DEVICE_RE = re.compile(r"^(added|removed|changed):(pad|remote|other):\d{1,6}$")


def parse(raw: Any) -> dict[str, Any] | None:
    """The whitelisted row, or None (junk, overlong, no outcome)."""
    if not isinstance(raw, str) or not raw or len(raw) > MAX_CHARS:
        return None
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or obj.get("outcome") not in OUTCOMES:
        return None
    row: dict[str, Any] = {"outcome": obj["outcome"],
                           "reason": obj.get("reason") if obj.get("reason") in REASONS else "unknown"}
    for k in INTS:
        v = obj.get(k)
        if isinstance(v, int) and not isinstance(v, bool) and -1 <= v <= 86_400_000:
            row[k] = v
    for k in BOOLS:
        v = obj.get(k)
        if isinstance(v, bool) or v is None:
            row[k] = v
    keys = obj.get("keys")
    row["keys"] = [k for k in keys if isinstance(k, str) and KEY_RE.match(k)][:8] if isinstance(keys, list) else []
    devs = obj.get("devices")
    row["devices"] = [d for d in devs if isinstance(d, str) and DEVICE_RE.match(d)][:4] if isinstance(devs, list) else []
    return row


def note(recovery: Any, raw: Any, heartbeat_sequence: Any = None) -> bool:
    """One heartbeat's value: the recovery row written (True), or nothing (False)."""
    row = parse(raw)
    if row is None:
        return False
    recovery._log("surface_lost", heartbeat_sequence=heartbeat_sequence, **row)
    return True
