"""D-BASE-S1 host-side sampler: one JSON line every 30 s for a session.

usage: s1_sampler.py <out.jsonl> <duration_s>

Records only host-local process, thermal, log and counter state. Any key
whose name suggests a network address is dropped from the companion status
blocks before writing (see _SCRUB).
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

REPO = "/home/privyhub/Projects/onn-stream-test"
LOGS = os.path.join(REPO, "logs", "games")
HB = os.path.join(LOGS, "native_stream_heartbeat.log")
REC = os.path.join(LOGS, "native_stream_recovery.log")
ARCHIVE = os.path.join(LOGS, "stream_log_archive")

_SCRUB = re.compile(
    r"(addr|address|host|ip|endpoint|peer|client_id|serial|mac|ssid)", re.I
)
_IPISH = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def scrub(obj):
    """Drop address-like keys and any value that looks like an IP."""
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items() if not _SCRUB.search(k)}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    if isinstance(obj, str) and _IPISH.search(obj):
        return "<redacted>"
    return obj


def read_int(path):
    try:
        with open(path) as fh:
            return int(fh.read().strip())
    except Exception:
        return None


def get_json(path, timeout=3.0):
    try:
        with urllib.request.urlopen(
            "http://localhost:8765" + path, timeout=timeout
        ) as r:
            return json.loads(r.read().decode())
    except Exception as exc:
        return {"_error": "%s: %s" % (type(exc).__name__, exc)}


def procs():
    """pid -> (name, argv) for the processes this soak cares about."""
    out = {}
    try:
        raw = subprocess.run(
            ["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return out
    for line in raw.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        pid, _, args = line.partition(" ")
        if not pid.isdigit():
            continue
        # Match the service itself, not a shell whose command line merely
        # contains the path -- the `pgrep -f` trap recorded in TOOLS.md.
        if args.startswith("python3") and "privyhub_service.py" in args:
            out.setdefault("companion", int(pid))
        elif "x11grab" in args:
            out.setdefault("encoder", int(pid))
        elif "privyhub_native_audio" in args:
            out.setdefault("audio_ffmpeg", int(pid))
        elif "retroarch" in args.lower():
            out.setdefault("retroarch", int(pid))
    return out


def proc_stat(pid):
    try:
        with open("/proc/%d/stat" % pid) as fh:
            parts = fh.read().rsplit(") ", 1)[1].split()
        utime, stime = int(parts[11]), int(parts[12])
        with open("/proc/%d/status" % pid) as fh:
            rss_kb = threads = None
            for line in fh:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1])
                elif line.startswith("Threads:"):
                    threads = int(line.split()[1])
        return {
            "pid": pid,
            "cpu_jiffies": utime + stime,
            "rss_kb": rss_kb,
            "threads": threads,
        }
    except Exception:
        return None


def dir_bytes(path):
    total = 0
    n = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                    n += 1
                except OSError:
                    pass
    except Exception:
        return None, None
    return total, n


def sample():
    p = procs()
    arch_bytes, arch_files = dir_bytes(ARCHIVE)
    rec = {
        "at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "monotonic": round(time.monotonic(), 3),
        "loadavg": list(os.getloadavg()),
        "cpu_temp_c": (lambda v: v / 1000.0 if v else None)(
            read_int("/sys/class/hwmon/hwmon3/temp1_input")
        ),
        "gpu_temp_c": (lambda v: v / 1000.0 if v else None)(
            read_int("/sys/class/hwmon/hwmon2/temp1_input")
        ),
        "gpu_power_w": (lambda v: v / 1e6 if v else None)(
            read_int("/sys/class/hwmon/hwmon2/power1_input")
        ),
        "rapl_pkg_energy_uj": read_int(
            "/sys/class/powercap/intel-rapl:0/energy_uj"
        ),
        "procs": {k: proc_stat(v) for k, v in p.items()},
        "log_bytes": {
            "heartbeat": os.path.getsize(HB) if os.path.exists(HB) else None,
            "recovery": os.path.getsize(REC) if os.path.exists(REC) else None,
            "archive_total": arch_bytes,
            "archive_files": arch_files,
        },
    }
    st = get_json("/plugins/games/status")
    rec["recovery_block"] = scrub(st.get("recovery")) if isinstance(st, dict) else None
    rec["game_active"] = st.get("active") if isinstance(st, dict) else None
    ns = get_json("/plugins/games/native-stream-status")
    if isinstance(ns, dict):
        ns = scrub(ns)
        rec["fec"] = ns.get("fec")
        rec["last_heartbeat"] = ns.get("last_heartbeat")
        rec["native_stream_active"] = ns.get("active")
        rec["native_stream_managed"] = ns.get("managed")
        rec["encoder_block"] = ns.get("encoder")
    return rec


def main():
    out_path, duration = sys.argv[1], float(sys.argv[2])
    end = time.monotonic() + duration
    with open(out_path, "a", buffering=1) as fh:
        while time.monotonic() < end:
            try:
                fh.write(json.dumps(sample()) + "\n")
            except Exception as exc:
                fh.write(json.dumps({"_sample_error": str(exc)}) + "\n")
            time.sleep(30)


if __name__ == "__main__":
    main()
