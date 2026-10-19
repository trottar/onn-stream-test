#!/usr/bin/env python3
"""CL-B7: where the PrivyHub process's CPU goes, per thread, on the onn (adb state reads only).

Written in CL-B7P (2026-10-19), not run there. For each arm of CL-B7's A/B, taken mid-window:

- `top -H -p <PrivyHub pid>` for N+1 one-second iterations; the first is dropped (it covers the process's life).
  Per thread: the name, PR, NI, state and %CPU of one core, per iteration, then the mean and max per name.
- `top` (processes) at the same time: %CPU of PrivyHub, media.swcodec (where the c2.android.* software codecs, the
  Opus decoder among them, are expected to run), the media codec / C2 HAL services, audioserver, surfaceflinger.
- the onn's busy % of capacity, uptime, and `getprop debug.privyhub.opus_decode` (the CL-B7P drain flag in force).

Written: numbers, thread and process names only. No PID or TID is written; digit runs inside names (binder threads
carry the pid) are masked to `#`. No address, serial or identifier.

    cl_b7_onn_threads.py <label> [--samples N]   -> one JSON line on stdout
"""
import argparse, datetime, json, re, statistics, subprocess

PKG = "com.safeiot.privyhub"
PROCS = re.compile(r"^(com\.safeiot\.privyhub|media\.swcodec|media\.codec|mediaserver|audioserver|surfaceflinger"
                   r"|.*hardware\.media\.c2.*|.*media\.omx.*|.*mediacodec.*)$")
OURS = re.compile(r"^PrivyHub-")
FRAMEWORK_CODEC = re.compile(r"(MediaCodec|CodecLooper|CCodec|C2|Codec2|codec|ACodec)", re.I)
BINDER = re.compile(r"^(binder|HwBinder|hwbinder)", re.I)


def sh(cmd, timeout=60):
    return subprocess.run(["adb", "shell", cmd], capture_output=True, text=True, timeout=timeout).stdout


def mask(name):
    return re.sub(r"\d{2,}", "#", name)


def iterations(text):
    """Split batch top output into iterations (each starts with a 'Tasks:' or 'Threads:' line)."""
    parts = re.split(r"(?m)^(?=\s*(?:Tasks|Threads):)", text)
    return [p for p in parts if re.match(r"\s*(?:Tasks|Threads):", p)]


def rows(block, fields):
    """Rows of an -o table: the header line is the one starting with the first field name."""
    out, seen = [], False
    for line in block.splitlines():
        f = line.split(None, len(fields) - 1)
        if not f:
            continue
        if f[0] == fields[0]:
            seen = True
            continue
        if seen and len(f) == len(fields):
            out.append(dict(zip(fields, f)))
    return out


def category(name):
    if OURS.match(name):
        return "privyhub_own"
    if BINDER.match(name):
        return "binder"
    if FRAMEWORK_CODEC.search(name):
        return "framework_codec"
    if name in ("RenderThread", PKG[:15], "safeiot.privyhub"):
        return "ui_render"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label")
    ap.add_argument("--samples", type=int, default=10)
    a = ap.parse_args()
    out = {"label": a.label, "at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "samples": a.samples}
    up = sh("cat /proc/uptime").split()
    out["uptime_s"] = float(up[0]) if up else None
    out["opus_decode_flag"] = sh("getprop debug.privyhub.opus_decode").strip() or "(absent)"
    pid = sh(f"pidof {PKG}").split()
    if not pid:
        out["error"] = "PrivyHub not running"
        print(json.dumps(out))
        return
    n = a.samples + 1

    # Threads of the PrivyHub process. CMD is the thread's name (comm, 15 chars).
    tfields = ["TID", "PR", "NI", "S", "%CPU", "CMD"]
    th = iterations(sh(f"top -H -p {pid[0]} -b -d 1 -n {n} -o {','.join(tfields)}", timeout=30 + 2 * n))[1:]
    per = {}
    for i, block in enumerate(th):
        for r in rows(block, tfields):
            name = mask(r["CMD"].strip())
            d = per.setdefault(name, {"pr": r["PR"], "ni": r["NI"], "cpu": [0.0] * len(th), "threads": set()})
            d["cpu"][i] += float(r["%CPU"])
            d["threads"].add(r["TID"])
    threads = []
    for name, d in per.items():
        threads.append({"name": name, "category": category(name), "pr": d["pr"], "ni": d["ni"],
                        "count": len(d["threads"]), "cpu_mean": round(statistics.fmean(d["cpu"]), 2),
                        "cpu_max": max(d["cpu"]), "cpu_per_iteration": d["cpu"]})
    threads.sort(key=lambda t: -t["cpu_mean"])
    out["iterations_kept"] = len(th)
    out["threads"] = threads
    cats = {}
    for t in threads:
        cats[t["category"]] = round(cats.get(t["category"], 0.0) + t["cpu_mean"], 2)
    out["privyhub_by_category"] = cats
    out["privyhub_threads_total"] = round(sum(t["cpu_mean"] for t in threads), 2)

    # Processes, the same iterations' shape (separate call: top cannot do both at once).
    pfields = ["PID", "PR", "NI", "%CPU", "NAME"]
    raw = sh(f"top -b -d 1 -n {n} -o {','.join(pfields)}", timeout=30 + 2 * n)
    pit = iterations(raw)[1:]
    procs = {}
    for i, block in enumerate(pit):
        for r in rows(block, pfields):
            name = r["NAME"].strip()
            if PROCS.match(name):
                procs.setdefault(name, [0.0] * len(pit))[i] += float(r["%CPU"])
    out["processes"] = {k: {"cpu_mean": round(statistics.fmean(v), 2), "cpu_max": max(v)} for k, v in procs.items()}
    busy = []
    for block in pit:
        m = re.search(r"(\d+)%cpu\s+\d+%user\s+\d+%nice\s+\d+%sys\s+(\d+)%idle", block)
        if m:
            tot, idle = map(int, m.groups())
            busy.append(100 * (tot - idle) / tot)
    out["onn_busy_pct_of_capacity_mean"] = round(statistics.fmean(busy), 1) if busy else None
    print(json.dumps(out))


if __name__ == "__main__":
    main()
