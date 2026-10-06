#!/usr/bin/env python3
"""E3 probes -- measurement only, read-only on the host (no ptrace, no root).

    e3_probe.py tree <out.jsonl> --channel <xmltv id> [--grabs 1] [--interval 0.05]
        Forced EPG grab(s) (POST /plugins/epg/refresh) with the stream idle; every <interval> s: the companion's
        descendants (pid, ppid, comm, argv[0..1] basenames, scheduling policy, nice, ioprio class once per pid,
        utime+stime ticks, RSS; PSS every 0.25 s) and the first established TCP socket each descendant owns
        (`ss -tnp`, own processes only; the peer is never written). Prints a summary JSON.
    e3_probe.py summarize <out.jsonl>          the summary again
    e3_probe.py threads <out.json> --secs 180  the companion's threads: voluntary / involuntary context switches,
        schedstat run/wait ns and timeslices, policy, syscall -- first and last read, per-second deltas; plus the
        audio packets sent per second from /plugins/games/native-stream-status if it carries them.

Writes only the named output. Only numbers, fixed labels and process comm names / basenames are written.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request

BASE = "http://localhost:8765"
CLK = os.sysconf("SC_CLK_TCK")
PAGE_KB = os.sysconf("SC_PAGE_SIZE") // 1024


def rd(p: str, mode: str = "r"):
    try:
        with open(p, mode) as fh:
            return fh.read()
    except OSError:
        return None


def companion_pid() -> int | None:
    v = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value", "privyhub-companion"],
                       capture_output=True, text=True).stdout.strip()
    return int(v) if v.isdigit() and v != "0" else None


def children_map() -> dict:
    kids = {}
    for d in os.listdir("/proc"):
        if d.isdigit():
            s = rd(f"/proc/{d}/stat")
            if s:
                try:
                    ppid = int(s.rsplit(")", 1)[1].split()[1])
                except (ValueError, IndexError):
                    continue
                kids.setdefault(ppid, []).append(int(d))
    return kids


def descendants(root: int) -> list:
    kids, out, todo = children_map(), [], [root]
    while todo:
        p = todo.pop()
        for c in kids.get(p, []):
            out.append(c)
            todo.append(c)
    return out


def proc_row(pid: int) -> dict | None:
    s = rd(f"/proc/{pid}/stat")
    if not s:
        return None
    try:
        comm = s[s.index("(") + 1:s.rindex(")")]
        f = s.rsplit(")", 1)[1].split()
        row = {"pid": pid, "ppid": int(f[1]), "comm": comm, "ticks": int(f[11]) + int(f[12]),
               "cticks": int(f[13]) + int(f[14]), "nice": int(f[16]), "policy": int(f[38]),
               "start": int(f[19]), "rss_kb": int(f[21]) * PAGE_KB}
    except (ValueError, IndexError):
        return None
    raw = rd(f"/proc/{pid}/cmdline", "rb") or b""
    argv = [a.decode(errors="replace") for a in raw.split(b"\0") if a]
    row["argv"] = [os.path.basename(a) if "/" in a and not a.startswith("--") else re.sub(r"=.*", "=", a)
                   for a in argv[:3]]
    return row


def pss_kb(pid: int) -> int | None:
    t = rd(f"/proc/{pid}/smaps_rollup")
    m = re.search(r"^Pss:\s+(\d+)", t or "", re.M)
    return int(m.group(1)) if m else None


def ioprio(pid: int) -> str:
    out = subprocess.run(["ionice", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return out.split(":")[0] if out else "?"


def tcp_owners() -> set:
    out = subprocess.run(["ss", "-tnpH", "state", "established"], capture_output=True, text=True).stdout
    return {int(m) for m in re.findall(r"pid=(\d+),", out)}


def tree(out_path: str, channel: str, grabs: int, interval: float) -> dict:
    root = companion_pid()
    if not root:
        raise SystemExit("companion not running")
    fh = open(out_path, "w")
    t_base = time.monotonic()
    done = threading.Event()
    marks = []

    def grabber():
        for i in range(grabs):
            t0 = time.monotonic()
            req = urllib.request.Request(f"{BASE}/plugins/epg/refresh?channel_id={urllib.parse.quote(channel)}",
                                         method="POST", data=b"")
            try:
                with urllib.request.urlopen(req, timeout=150) as r:
                    d = json.loads(r.read() or b"{}")
            except Exception as exc:  # noqa: BLE001
                d = {"error": type(exc).__name__}
            marks.append({"grab": i, "t0": round(t0 - t_base, 3), "t1": round(time.monotonic() - t_base, 3),
                          "ok": bool(d.get("ok")), "programmes": d.get("programme_count")})
            time.sleep(3)
        done.set()

    seen_io, first_tcp, last_pss = {}, {}, 0.0
    th = threading.Thread(target=grabber, daemon=True)
    time.sleep(1.0)
    th.start()
    while not done.is_set():
        now = time.monotonic() - t_base
        pids = descendants(root)
        rows = [r for r in (proc_row(p) for p in pids) if r]
        if now - last_pss >= 0.25:
            for r in rows:
                r["pss_kb"] = pss_kb(r["pid"])
            last_pss = now
        if rows:
            owners = tcp_owners()
            for r in rows:
                key = (r["pid"], r["start"])
                if key not in seen_io:
                    seen_io[key] = ioprio(r["pid"])
                r["ioprio"] = seen_io[key]
                if r["pid"] in owners and key not in first_tcp:
                    first_tcp[key] = round(now, 3)
                    r["first_tcp"] = True
        fh.write(json.dumps({"t": round(now, 3), "procs": rows}) + "\n")
        time.sleep(interval)
    fh.write(json.dumps({"marks": marks}) + "\n")
    fh.close()
    return summarize(out_path)


def summarize(path: str) -> dict:
    samples, marks = [], []
    for line in open(path):
        d = json.loads(line)
        if "marks" in d:
            marks = d["marks"]
        else:
            samples.append(d)
    per = {}
    for s in samples:
        for r in s["procs"]:
            key = f"{r['pid']}:{r['start']}"
            p = per.setdefault(key, {"pid": r["pid"], "ppid": r["ppid"], "comm": r["comm"], "argv": r["argv"],
                                     "policy": r["policy"], "nice": r["nice"], "ioprio": r.get("ioprio"),
                                     "first_t": s["t"], "first_ticks": r["ticks"], "series": []})
            p["last_t"], p["last_ticks"], p["cticks"] = s["t"], r["ticks"], r["cticks"]
            p["comm"], p["argv"] = r["comm"], r["argv"]
            p["peak_rss_kb"] = max(p.get("peak_rss_kb", 0), r["rss_kb"])
            if r.get("pss_kb"):
                p["peak_pss_kb"] = max(p.get("peak_pss_kb", 0), r["pss_kb"])
            if r.get("first_tcp"):
                p["first_tcp_t"] = s["t"]
            p["series"].append((s["t"], r["ticks"]))
    out = {"marks": marks, "procs": []}
    for g in marks:
        t0, t1 = g["t0"], g["t1"]
        g["procs"] = []
        for k, p in per.items():
            if p["last_t"] < t0 or p["first_t"] > t1 + 0.5:
                continue

            def cpu_between(a, b):
                pts = [(t, x) for t, x in p["series"] if a <= t <= b]
                return round((pts[-1][1] - pts[0][1]) / CLK, 3) if len(pts) > 1 else 0.0
            # a process seen from its first sample: its ticks before that sample are counted from 0 when it
            # started inside the grab (first_ticks is what it had already used by the first 50-ms sample)
            started_inside = p["first_t"] >= t0
            pre = p["first_ticks"] / CLK if started_inside else 0.0
            g["procs"].append({
                "pid_rel": None, "comm": p["comm"], "argv": p["argv"], "ppid_is_companion": None,
                "policy": p["policy"], "nice": p["nice"], "ioprio": p["ioprio"],
                "alive_s": round(p["last_t"] - p["first_t"], 3), "start_offset_s": round(p["first_t"] - t0, 3),
                "cpu_s_total": round((p["last_ticks"] - p["first_ticks"]) / CLK + pre, 3),
                "cpu_s_first_3s": round(cpu_between(t0, t0 + 3) + (pre if p["first_t"] <= t0 + 3 else 0), 3),
                "first_tcp_offset_s": round(p["first_tcp_t"] - t0, 3) if "first_tcp_t" in p else None,
                "cpu_s_before_first_tcp": (round(cpu_between(p["first_t"], p["first_tcp_t"]) + pre, 3)
                                           if "first_tcp_t" in p else None),
                "peak_rss_mb": round(p.get("peak_rss_kb", 0) / 1024, 1),
                "peak_pss_mb": round(p.get("peak_pss_kb", 0) / 1024, 1) if p.get("peak_pss_kb") else None,
                "children_cpu_s_reaped": round(p["cticks"] / CLK, 3)})
        g["procs"].sort(key=lambda r: r["start_offset_s"])
    out["marks"] = marks
    out["samples"] = len(samples)
    out["interval_s_median"] = (round(sorted(b["t"] - a["t"] for a, b in zip(samples, samples[1:]))[len(samples) // 2],
                                      3) if len(samples) > 2 else None)
    return out


def threads(out_path: str, secs: int) -> dict:
    pid = companion_pid()

    def snap():
        res = {}
        for t in os.listdir(f"/proc/{pid}/task"):
            st = rd(f"/proc/{pid}/task/{t}/status") or ""
            sc = (rd(f"/proc/{pid}/task/{t}/schedstat") or "0 0 0").split()
            s = rd(f"/proc/{pid}/task/{t}/stat") or ""
            try:
                f = s.rsplit(")", 1)[1].split()
                ticks, pol = int(f[11]) + int(f[12]), int(f[38])
            except (ValueError, IndexError):
                continue
            vol = re.search(r"voluntary_ctxt_switches:\s+(\d+)", st)
            inv = re.search(r"nonvoluntary_ctxt_switches:\s+(\d+)", st)
            sy = (rd(f"/proc/{pid}/task/{t}/syscall") or "").split()
            res[t] = {"ticks": ticks, "policy": pol, "vol": int(vol.group(1)) if vol else None,
                      "invol": int(inv.group(1)) if inv else None, "run_ns": int(sc[0]), "wait_ns": int(sc[1]),
                      "slices": int(sc[2]), "syscall": sy[0] if sy else None}
        return res

    def status():
        try:
            with urllib.request.urlopen(BASE + "/plugins/games/native-stream-status", timeout=10) as r:
                return json.loads(r.read() or b"{}")
        except Exception:  # noqa: BLE001
            return {}

    a, sa, ta = snap(), status(), time.monotonic()
    syscalls = {}
    end = ta + secs
    while time.monotonic() < end:
        for t in os.listdir(f"/proc/{pid}/task"):
            sy = (rd(f"/proc/{pid}/task/{t}/syscall") or "").split()
            if sy:
                syscalls.setdefault(t, {}).setdefault(sy[0], 0)
                syscalls[t][sy[0]] += 1
        time.sleep(0.1)
    b, sb, tb = snap(), status(), time.monotonic()
    dt = tb - ta
    rows = []
    for t in sorted(b, key=int):
        if t not in a:
            continue
        x, y = a[t], b[t]
        rows.append({"tid_rel": int(t) - pid, "policy": y["policy"],
                     "cpu_pct": round(100 * (y["ticks"] - x["ticks"]) / CLK / dt, 2),
                     "vol_per_s": round((y["vol"] - x["vol"]) / dt, 1), "invol_per_s": round((y["invol"] - x["invol"]) / dt, 1),
                     "slices_per_s": round((y["slices"] - x["slices"]) / dt, 1),
                     "run_ms_per_s": round((y["run_ns"] - x["run_ns"]) / 1e6 / dt, 2),
                     "wait_ms_per_s": round((y["wait_ns"] - x["wait_ns"]) / 1e6 / dt, 3),
                     "syscall_modes": syscalls.get(t, {})})
    res = {"secs": round(dt, 1), "threads": rows, "status_keys_a": sorted(sa.keys())[:80],
           "status_a": {k: v for k, v in sa.items() if isinstance(v, (int, float)) and "audio" in k.lower()},
           "status_b": {k: v for k, v in sb.items() if isinstance(v, (int, float)) and "audio" in k.lower()}}
    with open(out_path, "w") as fh:
        json.dump(res, fh, indent=1)
    return res


def main(argv: list) -> int:
    if argv and argv[0] == "tree":
        ch = argv[argv.index("--channel") + 1]
        n = int(argv[argv.index("--grabs") + 1]) if "--grabs" in argv else 1
        iv = float(argv[argv.index("--interval") + 1]) if "--interval" in argv else 0.05
        print(json.dumps(tree(argv[1], ch, n, iv), indent=1))
        return 0
    if argv and argv[0] == "summarize":
        print(json.dumps(summarize(argv[1]), indent=1))
        return 0
    if argv and argv[0] == "threads":
        secs = int(argv[argv.index("--secs") + 1]) if "--secs" in argv else 180
        print(json.dumps(threads(argv[1], secs), indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
