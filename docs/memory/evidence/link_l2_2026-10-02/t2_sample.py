#!/usr/bin/env python3
"""D-BASE-T2 sampler: host, onn and Opal, one JSON line every INTERVAL s.

    t2_sample.py <out.jsonl> [interval_s=10]      stop: touch <out.jsonl>.stop

Per round, three reads in parallel (so the round stays on its 10 s grid):

  host  every hwmon temperature by name/label (C), per-core cpufreq (MHz),
        the encoder (ffmpeg h264_vaapi) and RetroArch CPU % since the last
        round, /proc/net/dev counters of the wired interface.
  onn   one `adb shell`: `dumpsys thermalservice` (status and the HAL's
        current temperatures), `dumpsys battery` temperature, and
        `cmd wifi status` -> RSSI, link / tx / rx speed, frequency.
  opal  one `ssh opal` (READ-ONLY: iw station dump, iwinfo assoclist,
        /proc/loadavg, thermal_zone temp): the onn's station row on the
        5 GHz AP -> signal, tx/rx bitrate + MCS, tx retries/failed,
        inactive ms; the SoC temperature and load.

PRIVACY: the onn's hardware address is read from `cmd wifi status` once,
held in memory only to find its station row on the Opal, and never
written. Only numbers and fixed labels are written; the output is checked
with h2_prep_redact.py --check afterwards.
"""
import json, os, re, subprocess, sys, threading, time
from datetime import datetime, timezone

OUT = sys.argv[1]
INTERVAL = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
STOP = OUT + ".stop"
WIRED = "eno1"
OPAL_IF = "wlan1"
MAC_RE = re.compile(r"([0-9a-f]{2}(?::[0-9a-f]{2}){5})", re.I)
CLK = os.sysconf("SC_CLK_TCK")

_onn_mac = None      # memory only
_prev_cpu = {}       # pid -> (ticks, monotonic)


def run(cmd, timeout=8):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as exc:
        return f"__error__ {type(exc).__name__}"


def num(pat, text, cast=float):
    m = re.search(pat, text)
    return cast(m.group(1)) if m else None


def proc_cpu(match):
    """CPU % since the previous round for the first process whose argv matches."""
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            argv = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
            exe = os.path.basename(os.readlink(f"/proc/{pid}/exe"))
        except Exception:
            continue
        if exe in ("bash", "sh", "dash") or not match(exe, argv):
            continue
        try:
            f = open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()
            ticks = int(f[11]) + int(f[12])
        except Exception:
            continue
        now = time.monotonic()
        prev = _prev_cpu.get(pid)
        _prev_cpu[pid] = (ticks, now)
        if not prev:
            return {"pid_seen": True, "cpu_pct": None}
        return {"pid_seen": True, "cpu_pct": round(100.0 * (ticks - prev[0]) / CLK / (now - prev[1]), 1)}
    return {"pid_seen": False, "cpu_pct": None}


def host():
    temps = {}
    for h in sorted(os.listdir("/sys/class/hwmon")):
        base = f"/sys/class/hwmon/{h}"
        try:
            name = open(f"{base}/name").read().strip()
        except Exception:
            continue
        for fn in sorted(os.listdir(base)):
            if not (fn.startswith("temp") and fn.endswith("_input")):
                continue
            try:
                v = int(open(f"{base}/{fn}").read()) / 1000.0
            except Exception:
                continue
            try:
                label = open(f"{base}/{fn[:-6]}_label").read().strip()
            except Exception:
                label = fn[:-6]
            temps[f"{name}/{label}"] = v
    mhz = []
    for c in sorted(os.listdir("/sys/devices/system/cpu")):
        p = f"/sys/devices/system/cpu/{c}/cpufreq/scaling_cur_freq"
        if re.fullmatch(r"cpu\d+", c) and os.path.exists(p):
            mhz.append(round(int(open(p).read()) / 1000))
    net = {}
    for line in open("/proc/net/dev"):
        if line.strip().startswith(WIRED + ":"):
            v = [int(x) for x in line.split(":", 1)[1].split()]
            net = {"rx_packets": v[1], "rx_errs": v[2], "rx_drop": v[3],
                   "tx_packets": v[9], "tx_errs": v[10], "tx_drop": v[11]}
    return {
        "temps_c": temps,
        "cpu_mhz": mhz,
        "cpu_mhz_min": min(mhz) if mhz else None,
        "cpu_mhz_mean": round(sum(mhz) / len(mhz)) if mhz else None,
        "encoder": proc_cpu(lambda exe, a: exe == "ffmpeg" and "h264_vaapi" in a),
        "retroarch": proc_cpu(lambda exe, a: "retroarch" in exe.lower() or "retroarch" in a.lower().split(" ")[0]),
        "net_" + WIRED: net,
    }


def onn():
    global _onn_mac
    t = run(["adb", "shell",
             "dumpsys thermalservice | grep -E 'Thermal Status|mValue'; echo @@T2SEP@@; "
             "dumpsys battery | grep -i temperature; echo @@T2SEP@@; cmd wifi status"], timeout=9)
    if t.startswith("__error__"):
        return {"error": t}
    # `cmd wifi status` prints its own "====" headers: a unique separator
    parts = t.split("@@T2SEP@@")
    therm = parts[0] if parts else ""
    hal = [float(x) for x in re.findall(r"mValue=([-\d.]+), mType=\d+, mName=cpu-thermal", therm)]
    wifi = parts[2] if len(parts) > 2 else ""
    if _onn_mac is None:
        m = re.search(r"MAC: " + MAC_RE.pattern, wifi, re.I)
        if m:
            _onn_mac = m.group(1).lower()
    return {
        "thermal_status": num(r"Thermal Status: (\d+)", therm, int),
        # dumpsys prints "Cached" then "Current temperatures from HAL"; the
        # last cpu-thermal value is the HAL's current reading.
        "cpu_thermal_c": hal[-1] if hal else None,
        "battery_temp_c": (num(r"temperature: (\d+)", parts[1] if len(parts) > 1 else "", int) or 0) / 10.0 or None,
        "rssi_dbm": num(r"RSSI: (-?\d+)", wifi, int),
        "link_mbps": num(r"Link speed: (\d+)Mbps", wifi, int),
        "tx_link_mbps": num(r"Tx Link speed: (\d+)Mbps", wifi, int),
        "rx_link_mbps": num(r"Rx Link speed: (\d+)Mbps", wifi, int),
        "freq_mhz": num(r"Frequency: (\d+)MHz", wifi, int),
    }


def opal():
    t = run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "opal",
             f"iw dev {OPAL_IF} station dump; echo @@T2SEP@@; iwinfo {OPAL_IF} assoclist; echo @@T2SEP@@; "
             "cat /proc/loadavg; echo @@T2SEP@@; cat /sys/class/thermal/thermal_zone0/temp"], timeout=9)
    if t.startswith("__error__"):
        return {"error": t}
    parts = t.split("@@T2SEP@@")
    out = {"stations": len(re.findall(r"^Station ", parts[0], re.M)),
           "load1": num(r"^([\d.]+)", parts[2].strip()) if len(parts) > 2 else None,
           "soc_temp_c": (num(r"(\d+)", parts[3]) / 1000.0) if len(parts) > 3 and num(r"(\d+)", parts[3]) else None,
           "onn_row_found": False}
    if _onn_mac:
        for block in re.split(r"(?=^Station )", parts[0], flags=re.M):
            if block.lower().startswith("station " + _onn_mac):
                out.update({
                    "onn_row_found": True,
                    "signal_dbm": num(r"signal:\s*(-?\d+)", block, int),
                    "signal_avg_dbm": num(r"signal avg:\s*(-?\d+)", block, int),
                    "tx_bitrate_mbps": num(r"tx bitrate:\s*([\d.]+)", block),
                    "tx_mcs": num(r"tx bitrate:[^\n]*?MCS (\d+)", block, int),
                    "tx_nss": num(r"tx bitrate:[^\n]*?NSS (\d+)", block, int),
                    "rx_bitrate_mbps": num(r"rx bitrate:\s*([\d.]+)", block),
                    "rx_mcs": num(r"rx bitrate:[^\n]*?MCS (\d+)", block, int),
                    "tx_packets": num(r"tx packets:\s*(\d+)", block, int),
                    "tx_retries": num(r"tx retries:\s*(\d+)", block, int),
                    "tx_failed": num(r"tx failed:\s*(\d+)", block, int),
                    "rx_drop_misc": num(r"rx drop misc:\s*(\d+)", block, int),
                    "inactive_ms": num(r"inactive time:\s*(\d+)", block, int),
                })
        for block in re.split(r"\n\s*\n", parts[1] if len(parts) > 1 else ""):
            if block.lower().lstrip().startswith(_onn_mac):
                out["iwinfo_signal_dbm"] = num(r"(-?\d+) dBm", block, int)
                out["iwinfo_tx_mbps"] = num(r"TX:\s*([\d.]+) MBit", block)
                out["iwinfo_rx_mbps"] = num(r"RX:\s*([\d.]+) MBit", block)
    return out


def main():
    seq = 0
    nxt = time.monotonic()
    while not os.path.exists(STOP):
        t0 = time.monotonic()
        stamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        res = {}
        def go(k, f):
            try:
                res[k] = f()
            except Exception as exc:
                res[k] = {"error": f"{type(exc).__name__}"}
        # onn first so the MAC is known before the first Opal parse
        if _onn_mac is None:
            go("onn", onn)
            ths = [threading.Thread(target=go, args=(k, f)) for k, f in (("host", host), ("opal", opal))]
        else:
            ths = [threading.Thread(target=go, args=(k, f)) for k, f in (("host", host), ("onn", onn), ("opal", opal))]
        for th in ths: th.start()
        for th in ths: th.join()
        row = {"seq": seq, "at_utc": stamp, "cost_ms": round((time.monotonic() - t0) * 1000),
               "host": res.get("host"), "onn": res.get("onn"), "opal": res.get("opal")}
        with open(OUT, "a") as fh:
            fh.write(json.dumps(row) + "\n")
        seq += 1
        nxt += INTERVAL
        time.sleep(max(0.0, nxt - time.monotonic()))


if __name__ == "__main__":
    main()
