#!/usr/bin/env python3
"""B30: the trip check -- six plain lines, read-only, no identifiers.

    python3 tools/trip_check.py [--trip-dir docs/memory/evidence/trip_2026-10-30]

1. adopted: the adopted line count and e1_suite's host check (`manager`, `environ` == ADOPTED, every drop-in, no
   e3_flag.conf, no e4 file), the failing fields by name;
2. apk: on the pin or not (adb), or the pin with "not read (adb off-LAN)";
3. overlay: connected, the path (direct / relayed / no-peer / none), online peers by count;
4. routing: the newest `token_issued`'s routing class and time (logs/session_audit.jsonl);
5. band: 5 GHz / 2.4 GHz with the frequency if adb reaches the onn, else "adb off-LAN";
6. log-keeper: its status line (the trip dir's status.txt) and whether its unit is active.
Every line goes through the log-keeper's redactor before it prints; a failing reader prints `unknown (<why>)`.
Reads files, `adb` (devices, the APK's hash, `dumpsys wifi`), `tailscale status`, `systemctl --user is-active` and the
local control API through e1_suite; changes nothing. Design: docs/memory/evidence/b30_2026-10-28/design_written_before_code.md.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import trip_log_keeper as tlk  # noqa: E402

TRIP_DIR = REPO / "docs/memory/evidence/trip_2026-10-30"
AUDIT = REPO / "logs/session_audit.jsonl"
UNIT = "privyhub-trip-log"
HOST_FIELDS = ("drop_in_", "e3_dropin_absent", "e4_constraint_absent")


def e1_suite() -> Any:
    spec = importlib.util.spec_from_file_location("e1_suite_trip", REPO / "tools/e1_suite.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------- the six readers (each takes its source)

def line_adopted(preflight: dict[str, Any], adopted: list[str]) -> str:
    bad = []
    if preflight.get("manager") != []:
        bad.append("manager flags")
    env = list(preflight.get("environ") or [])
    if env != sorted(adopted):
        missing = [kv.split("=", 1)[0] for kv in adopted if kv not in env]
        extra = [kv.split("=", 1)[0] for kv in env if kv not in adopted]
        bad.append("environ" + (f" missing {', '.join(missing)}" if missing else "")
                   + (f" extra {', '.join(extra)}" if extra else ""))
    bad += [k for k, v in preflight.items() if k.startswith(HOST_FIELDS) and v is not True]
    return f"adopted: {len(adopted)} lines; host check " + ("ok" if not bad else f"NOT ok ({'; '.join(bad)})")


def line_apk(pin: str, installed: str | None, adb_up: bool) -> str:
    short = pin[:8] + "…"
    if not adb_up or installed is None:
        return f"apk: pin {short}, not read (adb off-LAN)"
    return f"apk: on the pin {short}" if installed == pin else f"apk: NOT on the pin (the pin {short})"


def line_overlay(state: dict[str, Any], peers: int | None) -> str:
    conn = "yes" if state.get("connected") else "no"
    return f"overlay: connected {conn}, path {state.get('path') or 'none'}, peers {peers if peers is not None else '?'}"


def line_routing(audit_tail: list[str]) -> str:
    for line in reversed(audit_tail):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") == "token_issued":
            return f"routing: newest token_issued {r.get('routing_evidence') or '?'} at {r.get('t') or r.get('at_utc') or '?'}"
    return "routing: no token_issued in the audit log"


def line_band(wifi_line: str | None) -> str:
    if not wifi_line:
        return "band: adb off-LAN"
    m = re.search(r"(?:^|, )Frequency: (\d+)", wifi_line)
    if not m:
        return "band: unknown (no frequency in the Wi-Fi read)"
    f = int(m.group(1))
    band = "5 GHz" if 4900 <= f < 5900 else "2.4 GHz" if 2400 <= f < 2500 else "6 GHz" if f >= 5925 else "?"
    return f"band: {band} ({f} MHz)"


def line_keeper(status: str | None, unit_active: str | None) -> str:
    unit = f"unit {unit_active}" if unit_active else "unit ?"
    if not status:
        return f"log-keeper: not running (no status); {unit}"
    return f"log-keeper: {status.strip()}; {unit}"


# ---------------------------------------------------------------- the real sources

def tail_lines(p: Path, n_bytes: int = 256_000) -> list[str]:
    with open(p, "rb") as fh:
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(max(0, size - n_bytes))
        return fh.read().decode("utf-8", errors="replace").splitlines()


def wifi_line() -> str | None:
    try:
        out = subprocess.run(["adb", "shell", "dumpsys wifi | grep -m1 '^mWifiInfo'"], capture_output=True, text=True,
                             timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return out.strip() or None


def unit_state() -> str | None:
    try:
        return subprocess.run(["systemctl", "--user", "is-active", UNIT], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def safe(fn: Callable[[], str], name: str) -> str:
    try:
        return fn()
    except Exception as exc:
        return f"{name}: unknown ({type(exc).__name__})"


def lines(trip_dir: Path = TRIP_DIR) -> list[str]:
    e1: Any = None
    pf: dict[str, Any] = {}

    def adopted() -> str:
        nonlocal e1, pf
        e1 = e1_suite()
        pf = e1.preflight()
        return line_adopted(pf, list(e1.ADOPTED))

    def apk() -> str:
        up = bool(pf.get("adb"))
        return line_apk(e1.EXPECT_APK, e1.apk_hash() if up else None, up)

    def overlay() -> str:
        return line_overlay(tlk.overlay_state(), tlk.online_peers())

    def routing() -> str:
        return line_routing(tail_lines(AUDIT))

    def band() -> str:
        return line_band(wifi_line() if pf.get("adb") else None)

    def keeper() -> str:
        p = trip_dir / "status.txt"
        return line_keeper(p.read_text() if p.is_file() else None, unit_state())

    return [safe(adopted, "adopted"), safe(apk, "apk"), safe(overlay, "overlay"), safe(routing, "routing"),
            safe(band, "band"), safe(keeper, "log-keeper")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--trip-dir", type=Path, default=TRIP_DIR)
    a = ap.parse_args(argv)
    red = tlk.Redactor()
    for ln in lines(a.trip_dir):
        print(red.apply(ln)[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
