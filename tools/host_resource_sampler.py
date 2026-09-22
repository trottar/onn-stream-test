#!/usr/bin/env python3
"""D-BASE-T1 piece 2: a durable host resource sampler.

`D-BASE-S1` and `D-BASE-S2` each measured host temperature, load and
per-process memory with a sampler written for that one run and thrown away
afterwards. This is that sampler as a permanent tool, started and stopped
by the companion with every native stream session, so future sessions carry
a host series without anyone building a harness first.

One JSON line every `--interval` seconds to
`logs/games/host_resource_samples.jsonl`, rotated by the same helper as the
heartbeat log (4 MiB, keep 3, into `logs/games/stream_log_archive/`) and
bounded by `tools/diagnostic_retention.py`.

Trace only. It reads `/sys` and `/proc`, never writes outside its own log,
and every reader is wrapped: a sensor that disappears, a process that exits
mid-read or a `/sys` node that turns unreadable must not stop the sampling
and must never disturb the stream.

Processes are matched on their command line with an explicit `ps` scan
rather than `pgrep -f`, which `docs/memory/TOOLS.md` records as matching
the caller's own shell.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(REPO_ROOT / "companion"),
)

from games.log_rotation import append_line  # noqa: E402

SCHEMA = "privyhub_host_resource_sample_v1"

DEFAULT_INTERVAL_S = 30.0

# Matches the heartbeat log's bounds so the archive family holds one kind
# of thing at one scale.
MAX_LOG_BYTES = 4 * 1024 * 1024
KEEP_ROTATED = 3

HWMON_ROOT = Path("/sys/class/hwmon")

# Substring -> label. The first match wins, so a process is counted once.
PROCESS_MATCHERS = (
    ("retroarch", "retroarch"),
    ("privyhub_service.py", "companion"),
    ("x11grab", "encoder"),
    ("privyhub_native_audio", "audio_ffmpeg"),
    ("native_fec_relay", "fec_relay"),
)

# The FEC relay is a `threading.Thread` inside the companion on this build
# (`companion/native_fec_relay.py`), not its own process, so it has no RSS
# of its own. When nothing matches it by command line the sampler records
# that fact and the companion's figures it actually shares, rather than
# leaving a gap that reads like a failed sensor.
THREAD_HOSTED = {"fec_relay": "companion"}

# A shell whose command line merely contains one of the needles above is
# never the process being looked for — this is the `pgrep -f` trap from
# TOOLS.md, which also catches an explicit `ps` scan if it does not exclude
# interpreters of shell text.
SHELL_BASENAMES = frozenset(
    {
        "bash",
        "sh",
        "dash",
        "zsh",
        "ksh",
        "fish",
        "awk",
        "gawk",
        "grep",
        "ps",
        "xargs",
        "timeout",
        "nohup",
        "env",
    }
)

_CLOCK_TICKS = float(os.sysconf("SC_CLK_TCK") or 100)


def sample_log_path(
    project_root: Path,
) -> Path:
    return (
        Path(project_root)
        / "logs"
        / "games"
        / "host_resource_samples.jsonl"
    )


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except Exception:
        return None


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except Exception:
        return None


def read_hwmon() -> dict[str, Any]:
    """Temperatures in °C and power in W, keyed by sensor name."""

    out: dict[str, Any] = {}

    try:
        entries = sorted(HWMON_ROOT.iterdir())
    except Exception:
        return out

    for entry in entries:
        name = _read_text(entry / "name")

        if not name:
            continue

        block: dict[str, Any] = {}

        for node in sorted(entry.glob("temp*_input")):
            raw = _read_int(node)

            if raw is None:
                continue

            label = (
                _read_text(
                    entry / node.name.replace("_input", "_label")
                )
                or node.name.replace("_input", "")
            )

            block[f"{label}_c"] = round(raw / 1000.0, 2)

        for node in sorted(entry.glob("power*_input")):
            raw = _read_int(node)

            if raw is None:
                continue

            block[f"{node.name.replace('_input', '')}_w"] = round(
                raw / 1_000_000.0, 2
            )

        if block:
            # Two hwmon devices can share a name; keep both.
            key = name
            suffix = 2

            while key in out:
                key = f"{name}#{suffix}"
                suffix += 1

            out[key] = block

    return out


def hottest_c(
    hwmon: dict[str, Any],
) -> float | None:
    """The hottest temperature across every sensor, for `status`."""

    hottest: float | None = None

    for block in hwmon.values():
        if not isinstance(block, dict):
            continue

        for key, value in block.items():
            if not key.endswith("_c"):
                continue

            if not isinstance(value, (int, float)):
                continue

            if hottest is None or value > hottest:
                hottest = float(value)

    return hottest


def find_processes() -> dict[str, int]:
    """label -> pid, matched on the command line via an explicit ps scan."""

    out: dict[str, int] = {}

    try:
        raw = subprocess.run(
            ["ps", "-eo", "pid,args"],
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except Exception:
        return out

    for line in raw.splitlines()[1:]:
        line = line.strip()

        if not line:
            continue

        pid_text, _, args = line.partition(" ")

        if not pid_text.isdigit():
            continue

        pid = int(pid_text)

        if pid == os.getpid():
            continue

        first = args.split(" ", 1)[0]

        if os.path.basename(first) in SHELL_BASENAMES:
            continue

        for needle, label in PROCESS_MATCHERS:
            if needle not in args:
                continue

            # The companion is `python3 ./companion/privyhub_service.py`;
            # a shell whose command line merely contains that path is not
            # the service (TOOLS.md).
            if label == "companion" and not args.startswith("python3"):
                continue

            out.setdefault(label, pid)
            break

    return out


def read_process(
    pid: int,
) -> dict[str, Any] | None:
    try:
        with open(f"/proc/{pid}/stat") as handle:
            parts = handle.read().rsplit(") ", 1)[1].split()

        utime = int(parts[11])
        stime = int(parts[12])

        fields: dict[str, int] = {}

        with open(f"/proc/{pid}/status") as handle:
            for line in handle:
                for key in (
                    "VmRSS:",
                    "RssAnon:",
                    "RssFile:",
                    "VmSwap:",
                    "Threads:",
                ):
                    if line.startswith(key):
                        fields[key.rstrip(":")] = int(line.split()[1])

        return {
            "pid": pid,
            "cpu_jiffies": utime + stime,
            "rss_kb": fields.get("VmRSS"),
            "rss_anon_kb": fields.get("RssAnon"),
            "rss_file_kb": fields.get("RssFile"),
            "swap_kb": fields.get("VmSwap"),
            "threads": fields.get("Threads"),
        }
    except Exception:
        return None


def build_sample(
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    now = time.monotonic()

    hwmon = read_hwmon()

    procs: dict[str, Any] = {}

    for label, pid in find_processes().items():
        stats = read_process(pid)

        if stats is not None:
            procs[label] = stats

    for label, host_label in THREAD_HOSTED.items():
        if label in procs:
            continue

        host = procs.get(host_label)

        procs[label] = {
            "hosted_in": host_label,
            "pid": (host or {}).get("pid"),
            "rss_kb": (host or {}).get("rss_kb"),
            "rss_anon_kb": (host or {}).get("rss_anon_kb"),
            "threads": (host or {}).get("threads"),
            "shared_with_host": True,
        }

    record: dict[str, Any] = {
        "schema": SCHEMA,
        "at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z"),
        "monotonic": round(now, 3),
        "loadavg": [round(v, 3) for v in os.getloadavg()],
        "hwmon": hwmon,
        "host_thermal_c": hottest_c(hwmon),
        "procs": procs,
    }

    # CPU % needs two samples of the same pid; the first line carries none
    # rather than a figure averaged over the process's whole life.
    if previous is not None:
        span = now - float(previous.get("monotonic") or 0.0)

        if span > 0:
            for label, stats in procs.items():
                before = (previous.get("procs") or {}).get(label) or {}

                if (
                    before.get("pid") != stats.get("pid")
                    or before.get("cpu_jiffies") is None
                    or stats.get("cpu_jiffies") is None
                ):
                    continue

                delta = stats["cpu_jiffies"] - before["cpu_jiffies"]

                stats["cpu_pct"] = round(
                    delta / _CLOCK_TICKS / span * 100.0, 1
                )

    return record


def write_sample(
    project_root: Path,
    record: dict[str, Any],
) -> None:
    path = sample_log_path(project_root)

    path.parent.mkdir(parents=True, exist_ok=True)

    append_line(
        path,
        json.dumps(record, sort_keys=False),
        max_bytes=MAX_LOG_BYTES,
        keep=KEEP_ROTATED,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append host temperature, load and per-process "
        "resource samples to logs/games/host_resource_samples.jsonl.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_S,
        help="seconds between samples (default 30)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="print one sample as JSON and exit, writing nothing",
    )
    parser.add_argument(
        "--project-root",
        default=str(REPO_ROOT),
        help="repository root (default: this tool's repository)",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root)

    if args.once:
        print(json.dumps(build_sample(None), indent=2))
        return 0

    interval = max(1.0, float(args.interval))
    previous: dict[str, Any] | None = None

    while True:
        try:
            record = build_sample(previous)
            write_sample(project_root, record)
            previous = record
        except Exception as exc:
            # A sampler that dies takes the host series with it; one that
            # logs its own failure keeps going.
            try:
                write_sample(
                    project_root,
                    {
                        "schema": SCHEMA,
                        "at_utc": datetime.now(timezone.utc)
                        .isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z"),
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                )
            except Exception:
                pass

        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
