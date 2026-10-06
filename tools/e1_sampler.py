#!/usr/bin/env python3
"""E1-S1 -- the Phase E sampler set: one 1-s host sampler plus the workload's own telemetry.

    e1_sampler.py run <out_dir> [--telemetry] [--title] [--interval 1.0]   stop: touch <out_dir>/sampler.stop
    e1_sampler.py summarize <out_dir> [--from <utc>] [--to <utc>]           -> <out_dir>/sampler_summary.json
    e1_sampler.py --once                                                    one host sample, printed, nothing written
    e1_sampler.py --coverage                                                what this host exposes (E2's list), printed
    e1_sampler.py --self-test

Built from evidence/c5_m4_2026-10-01/c5_m4_sampler.py (1-s CPU per core, GPU busy, socket W, per-process %
of a core, Tctl, RetroArch's window-title frame counter, the client's C2 telemetry every 2 s) and
D-BASE-T2's t2_sample.py (cpufreq, the wired interface), plus what E2 needs and this host exposes
without new hardware or root:

  cpu      per logical CPU busy %, mean / max; iowait %; /proc/pressure cpu/io/memory stall (ms per s)
  mem      MemAvailable, used, cached; swap used; pswpin / pswpout / pgmajfault per s
  disk     /proc/diskstats of the block device holding the repository (nvme0n1 here): IOs/s, kB/s,
           ms per IO (await), util % (io_ticks)
  net      /proc/net/dev bytes/s, packets/s, drops/s per interface (lo excluded)
  gpu      gpu_busy_percent; amdgpu gpu_metrics v2.x: gfx activity, **mm activity (the VCN video engine)**,
           socket / CPU / SoC power, clocks (gfx, vclk, dclk, fclk), per-core and SoC temperatures,
           throttle_status; hwmon PPT (the socket power the C5 tables called "GPU W"), k10temp Tctl, nvme
  freq     scaling_cur_freq per CPU (mean / min / max MHz); throttle_status != 0 counts as throttled
  procs    per category (companion, range_server, encoder, ffmpeg_other, retroarch, host_resource_sampler,
           epg, xorg, pulseaudio, e1_sampler, other): % of one core, RSS, PSS (smaps_rollup), RssAnon,
           threads, read/write bytes per s (/proc/<pid>/io); "other" is CPU only plus its top-3 by comm
  power    RAPL package energy: read once; on this host it is root-only (0400) -> recorded "not readable".
           Wall power needs a meter: ABSENT.

Workload telemetry (options, each its own thread):
  --telemetry  every 2 s: /diagnostics/stream-telemetry (decoder, latency, receiver) -> telemetry.jsonl
  --title      RetroArch's window title as xprop -spy delivers it -> title.txt ("|| FPS: x || Frames: n",
               written every 256 frames when the measurement-only counter override is set)

Read-only on everything; it never writes outside <out_dir>. Only numbers, fixed labels and process comm
names are written (no addresses, no hardware identifiers).
"""
from __future__ import annotations

import json
import math
import os
import re
import struct
import subprocess
import sys
import threading
import time
import urllib.request

CLK = os.sysconf("SC_CLK_TCK")
PAGE_KB = os.sysconf("SC_PAGE_SIZE") // 1024
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRM = "/sys/class/drm/card0/device"
RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"
SHELLS = {"bash", "sh", "dash", "zsh"}


def utc(t: float | None = None) -> str:
    t = time.time() if t is None else t
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".%03dZ" % int((t % 1) * 1000)


def rd(path: str, mode: str = "r"):
    try:
        with open(path, mode) as fh:
            return fh.read()
    except OSError:
        return None


# ---------------------------------------------------------------- host readers
def cpu_times() -> dict:
    rows = {}
    for line in (rd("/proc/stat") or "").splitlines():
        if line.startswith("cpu"):
            f = line.split()
            v = list(map(int, f[1:9]))
            rows[f[0]] = (sum(v), v[3] + v[4], v[4])  # total, idle+iowait, iowait
    return rows


def psi_totals() -> dict:
    out = {}
    for res in ("cpu", "io", "memory"):
        for line in (rd(f"/proc/pressure/{res}") or "").splitlines():
            m = re.match(r"(some|full) .*total=(\d+)", line)
            if m:
                out[f"{res}_{m.group(1)}"] = int(m.group(2))
    return out


def meminfo() -> dict:
    d = {}
    for line in (rd("/proc/meminfo") or "").splitlines():
        k, _, v = line.partition(":")
        try:
            d[k] = int(v.split()[0])
        except (IndexError, ValueError):
            pass
    return d


def vmstat() -> dict:
    d = {}
    for line in (rd("/proc/vmstat") or "").splitlines():
        k, _, v = line.partition(" ")
        if k in ("pswpin", "pswpout", "pgmajfault", "pgfault"):
            d[k] = int(v)
    return d


def repo_block_device() -> str | None:
    """The whole-disk name holding the repository's filesystem (nvme0n1 on this host)."""
    try:
        st = os.stat(REPO)
        maj, mnr = os.major(st.st_dev), os.minor(st.st_dev)
        link = os.path.realpath(f"/sys/dev/block/{maj}:{mnr}")
        part = os.path.basename(link)
        parent = os.path.basename(os.path.dirname(link))
        return parent if os.path.exists(f"/sys/block/{parent}") else part
    except OSError:
        return None


def diskstats(dev: str) -> tuple | None:
    for line in (rd("/proc/diskstats") or "").splitlines():
        f = line.split()
        if len(f) > 13 and f[2] == dev:
            # reads, sectors read, ms reading, writes, sectors written, ms writing, io_ticks
            return int(f[3]), int(f[5]), int(f[6]), int(f[7]), int(f[9]), int(f[10]), int(f[12])
    return None


def netdev() -> dict:
    out = {}
    for line in (rd("/proc/net/dev") or "").splitlines()[2:]:
        name, _, rest = line.partition(":")
        name = name.strip()
        if name == "lo":
            continue
        v = [int(x) for x in rest.split()]
        out[name] = (v[0], v[1], v[3], v[8], v[9], v[11])  # rx bytes, pkts, drop, tx bytes, pkts, drop
    return out


GM_FMT = "<HBB HH 8H 2H HH Q HHHH 8H 6H 6H 8H 2H I H 3H"
GM_NAMES = (["size", "fmt", "cont", "t_gfx", "t_soc"] + ["t_core%d" % i for i in range(8)] + ["t_l3_0", "t_l3_1",
            "gfx_act", "mm_act", "clk", "sock_p", "cpu_p", "soc_p", "gfx_p"] + ["core_p%d" % i for i in range(8)] +
            ["avg_gfxclk", "avg_socclk", "avg_uclk", "avg_fclk", "avg_vclk", "avg_dclk", "cur_gfxclk", "cur_socclk",
             "cur_uclk", "cur_fclk", "cur_vclk", "cur_dclk"] + ["cur_core%d" % i for i in range(8)] +
            ["l3c0", "l3c1", "throttle", "fan", "p0", "p1", "p2"])


def gpu_metrics() -> dict:
    """amdgpu gpu_metrics v2.x (APU). On this Renoir APU socket power is whole W, CPU/SoC power mW,
    temperatures centi-C; 65535 = not provided."""
    b = rd(DRM + "/gpu_metrics", "rb")
    if not b or len(b) < struct.calcsize(GM_FMT) or b[2] != 2:
        return {}
    v = dict(zip(GM_NAMES, struct.unpack_from(GM_FMT, b, 0)))
    ok = lambda x: x != 65535
    cores = [v["t_core%d" % i] / 100 for i in range(8) if ok(v["t_core%d" % i]) and v["t_core%d" % i] > 0]
    out = {
        # activities are in hundredths of a percent on this APU (gfx 1809 while gpu_busy_percent reads 18)
        "gfx_activity_pct": v["gfx_act"] / 100 if ok(v["gfx_act"]) else None,
        "vcn_activity_pct": v["mm_act"] / 100 if ok(v["mm_act"]) else None,
        "socket_power_w": v["sock_p"] if ok(v["sock_p"]) else None,
        "cpu_power_w": round(v["cpu_p"] / 1000, 3) if ok(v["cpu_p"]) else None,
        "soc_power_w": round(v["soc_p"] / 1000, 3) if ok(v["soc_p"]) else None,
        "gfxclk_mhz": v["avg_gfxclk"] if ok(v["avg_gfxclk"]) else None,
        "vclk_mhz": v["cur_vclk"] if ok(v["cur_vclk"]) else None,
        "dclk_mhz": v["cur_dclk"] if ok(v["cur_dclk"]) else None,
        "fclk_mhz": v["avg_fclk"] if ok(v["avg_fclk"]) else None,
        "t_gfx_c": v["t_gfx"] / 100 if ok(v["t_gfx"]) else None,
        "t_soc_c": v["t_soc"] / 100 if ok(v["t_soc"]) else None,
        "t_core_max_c": max(cores) if cores else None,
        "throttle_status": v["throttle"],
    }
    return out


def hwmon() -> dict:
    out = {}
    for h in sorted(os.listdir("/sys/class/hwmon")):
        p = "/sys/class/hwmon/" + h
        name = (rd(p + "/name") or "").strip()
        if name == "k10temp":
            t = rd(p + "/temp1_input")
            if t:
                out["tctl_c"] = int(t) / 1000
        elif name == "amdgpu":
            t = rd(p + "/temp1_input")
            if t:
                out["gpu_edge_c"] = int(t) / 1000
            for f in ("power1_average", "power1_input"):
                w = rd(p + "/" + f)
                if w:
                    out["ppt_w"] = int(w) / 1e6
                    break
        elif name == "nvme":
            t = rd(p + "/temp1_input")
            if t:
                out["nvme_c"] = int(t) / 1000
    return out


def cpufreq() -> dict:
    mhz = []
    base = "/sys/devices/system/cpu"
    for c in os.listdir(base):
        if re.fullmatch(r"cpu\d+", c):
            v = rd(f"{base}/{c}/cpufreq/scaling_cur_freq")
            if v:
                mhz.append(int(v) // 1000)
    if not mhz:
        return {}
    return {"cpu_mhz_mean": round(sum(mhz) / len(mhz)), "cpu_mhz_min": min(mhz), "cpu_mhz_max": max(mhz)}


def rapl_status() -> str:
    if not os.path.exists(RAPL):
        return "absent"
    return "readable" if os.access(RAPL, os.R_OK) else "not readable (root-only)"


# ---------------------------------------------------------------- processes
CATEGORIES = ("companion", "range_server", "encoder", "ffmpeg_other", "retroarch", "host_resource_sampler",
              "epg", "xorg", "pulseaudio", "e1_sampler")


def classify(pid: int, comm: str) -> str:
    raw = rd(f"/proc/{pid}/cmdline", "rb") or b""
    argv = raw.replace(b"\0", b" ").decode(errors="replace")
    try:
        exe = os.path.basename(os.readlink(f"/proc/{pid}/exe"))
    except OSError:
        exe = comm
    if exe in SHELLS or comm in SHELLS:
        return "other"
    if pid == os.getpid():
        return "e1_sampler"
    if "companion/privyhub_service.py" in argv:
        return "companion"
    if "companion/range_server.py" in argv:
        return "range_server"
    if comm == "ffmpeg":
        return "encoder" if "h264_vaapi" in argv else "ffmpeg_other"
    if comm in ("retroarch", "RetroArch-Linux"):
        return "retroarch"
    if comm == "AppRun":  # the AppImage execs its AppRun (-> usr/bin/retroarch): the emulator itself
        try:
            real = os.path.realpath(f"/proc/{pid}/exe").lower()
        except OSError:
            real = ""
        if "retroarch" in real or "retroarch" in argv.lower():
            return "retroarch"
    if "host_resource_sampler.py" in argv:
        return "host_resource_sampler"
    if re.search(r"(epg|xmltv|tv_grab|iptv-org)", argv, re.I) and "e1_" not in argv:
        return "epg"
    if comm == "Xorg":
        return "xorg"
    if comm == "pulseaudio":
        return "pulseaudio"
    return "other"


THREAD_CATS = ("companion", "encoder", "retroarch", "epg")


class ProcTable:
    """Per-category process rows. With threads=True (E2) also per-thread CPU for THREAD_CATS: tid, % of a core,
    scheduling policy (2 = SCHED_RR), the current syscall number (/proc/<pid>/task/<tid>/syscall; 7 poll, 0 read,
    202 futex, 230 clock_nanosleep, ...) -- read-only, no ptrace."""

    def __init__(self, threads: bool = False):
        self.cat = {}      # (pid, starttime, comm) -> category
        self.prev = {}     # (pid, starttime, comm) -> (ticks, rbytes, wbytes, monotonic, rchar, wchar)
        self.threads = threads
        self.tprev = {}    # (tid, tstart) -> (ticks, monotonic)
        self.last_threads = {}

    def _threads(self, cat: str, pid: int, now: float, seen: set) -> list:
        rows = []
        try:
            tids = os.listdir(f"/proc/{pid}/task")
        except OSError:
            return rows
        for t in tids:
            st = rd(f"/proc/{pid}/task/{t}/stat")
            if not st:
                continue
            try:
                f = st.rsplit(")", 1)[1].split()
                ticks, tstart, pol = int(f[11]) + int(f[12]), int(f[19]), int(f[38])
            except (ValueError, IndexError):
                continue
            sc = (rd(f"/proc/{pid}/task/{t}/syscall") or "").split()
            key = (int(t), tstart)
            seen.add(key)
            prev = self.tprev.get(key)
            self.tprev[key] = (ticks, now)
            cpu = round(100.0 * (ticks - prev[0]) / CLK / (now - prev[1]), 1) if prev and now > prev[1] else None
            rows.append([pid, int(t), cpu, pol, sc[0] if sc else None])
        return rows

    def sample(self) -> dict:
        now = time.monotonic()
        acc = {c: {"n": 0, "cpu_pct": 0.0, "rss_kb": 0, "pss_kb": 0, "pss_anon_kb": 0, "pss_file_kb": 0,
                   "rss_anon_kb": 0, "threads": 0, "read_kBps": 0.0, "write_kBps": 0.0, "rchar_kBps": 0.0,
                   "wchar_kBps": 0.0} for c in CATEGORIES}
        other_cpu, other_by = 0.0, {}
        seen, tseen, trows = set(), set(), {}
        for d in os.listdir("/proc"):
            if not d.isdigit():
                continue
            pid = int(d)
            s = rd(f"/proc/{pid}/stat")
            if not s:
                continue
            try:
                comm = s[s.index("(") + 1:s.rindex(")")]
                f = s.rsplit(")", 1)[1].split()
                ticks, start = int(f[11]) + int(f[12]), int(f[19])
                threads = int(f[17])
            except (ValueError, IndexError):
                continue
            key = (pid, start, comm)  # comm changes on exec: classify again
            seen.add(key)
            if key not in self.cat:
                self.cat[key] = classify(pid, comm)
            c = self.cat[key]
            prev = self.prev.get(key)
            cpu = None
            rb = wb = rc = wc = None
            if c != "other":
                io = rd(f"/proc/{pid}/io") or ""
                g = lambda n: (lambda m: int(m.group(1)) if m else None)(re.search(n + r": (\d+)", io))
                rb, wb, rc, wc = g("read_bytes"), g("write_bytes"), g("rchar"), g("wchar")
            if prev and now > prev[3]:
                cpu = 100.0 * (ticks - prev[0]) / CLK / (now - prev[3])
            self.prev[key] = (ticks, rb, wb, now, rc, wc)
            if c == "other":
                if cpu:
                    other_cpu += cpu
                    other_by[comm] = other_by.get(comm, 0.0) + cpu
                continue
            a = acc[c]
            a["n"] += 1
            a["threads"] += threads
            if cpu is not None:
                a["cpu_pct"] += cpu
            if prev and now > prev[3]:
                dt = now - prev[3]
                if rb is not None and prev[1] is not None:
                    a["read_kBps"] += (rb - prev[1]) / 1024 / dt
                    a["write_kBps"] += (wb - prev[2]) / 1024 / dt
                if rc is not None and len(prev) > 4 and prev[4] is not None:
                    a["rchar_kBps"] += (rc - prev[4]) / 1024 / dt
                    a["wchar_kBps"] += (wc - prev[5]) / 1024 / dt
            st = rd(f"/proc/{pid}/status") or ""
            for fld, k in (("VmRSS", "rss_kb"), ("RssAnon", "rss_anon_kb")):
                m = re.search(fld + r":\s+(\d+)", st)
                if m:
                    a[k] += int(m.group(1))
            sm = rd(f"/proc/{pid}/smaps_rollup") or ""
            for fld, k in (("Pss", "pss_kb"), ("Pss_Anon", "pss_anon_kb"), ("Pss_File", "pss_file_kb")):
                m = re.search(r"^" + fld + r":\s+(\d+)", sm, re.M)
                if m:
                    a[k] += int(m.group(1))
            if self.threads and c in THREAD_CATS:
                trows.setdefault(c, []).extend(self._threads(c, pid, now, tseen))
        for k in list(self.prev):
            if k not in seen:
                self.prev.pop(k, None)
                self.cat.pop(k, None)
        for k in list(self.tprev):
            if k not in tseen:
                self.tprev.pop(k, None)
        self.last_threads = trows
        out = {}
        for c, a in acc.items():
            if a["n"]:
                out[c] = {k: (round(v, 1) if isinstance(v, float) else v) for k, v in a.items()}
        top = sorted(other_by.items(), key=lambda kv: -kv[1])[:3]
        out["other"] = {"cpu_pct": round(other_cpu, 1), "top": [[k, round(v, 1)] for k, v in top]}
        return out


# ---------------------------------------------------------------- the host loop
def net_detail(iface: str = "eno1") -> dict:
    """E2: the transmit-side drop counters -- softnet (dropped, time_squeeze, summed over CPUs), the root qdisc
    (`tc -s qdisc show`, read-only, no root), and the interface's own tx_dropped / tx_errors."""
    out = {}
    drop = squeeze = 0
    for line in (rd("/proc/net/softnet_stat") or "").splitlines():
        f = line.split()
        if len(f) > 2:
            drop += int(f[1], 16)
            squeeze += int(f[2], 16)
    out["softnet_dropped"], out["softnet_squeeze"] = drop, squeeze
    for tc in ("/usr/sbin/tc", "/sbin/tc"):
        if os.path.exists(tc):
            try:
                t = subprocess.run([tc, "-s", "qdisc", "show", "dev", iface], capture_output=True, text=True,
                                   timeout=2).stdout
            except (OSError, subprocess.SubprocessError):
                t = ""
            m = re.search(r"dropped (\d+), overlimits (\d+) requeues (\d+)", t)
            if m:
                out["qdisc_dropped"], out["qdisc_overlimits"], out["qdisc_requeues"] = map(int, m.groups())
            m = re.search(r"backlog (\d+)b (\d+)p", t)
            if m:
                out["qdisc_backlog_b"] = int(m.group(1))
            break
    for k in ("tx_dropped", "tx_errors"):
        v = rd(f"/sys/class/net/{iface}/statistics/{k}")
        if v:
            out["if_" + k] = int(v)
    return out


class Host:
    def __init__(self, e2: bool = False):
        self.dev = repo_block_device()
        self.e2 = e2
        self.procs = ProcTable(threads=e2)
        self.t0 = time.monotonic()
        self.c0, self.p0, self.v0 = cpu_times(), psi_totals(), vmstat()
        self.d0 = diskstats(self.dev) if self.dev else None
        self.n0 = netdev()
        self.x0 = net_detail() if e2 else {}
        self.procs.sample()

    def sample(self) -> dict:
        t1 = time.monotonic()
        dt = max(1e-3, t1 - self.t0)
        c1, p1, v1 = cpu_times(), psi_totals(), vmstat()
        d1 = diskstats(self.dev) if self.dev else None
        n1 = netdev()
        row = {"at_utc": utc()}
        per = {}
        iow = None
        for k, (tot, idle, io) in c1.items():
            if k in self.c0:
                dtot = max(1, tot - self.c0[k][0])
                busy = round(100 * (1 - (idle - self.c0[k][1]) / dtot), 1)
                if k == "cpu":
                    iow = round(100 * (io - self.c0[k][2]) / dtot, 2)
                else:
                    per[k] = busy
        row["cpu"] = {"mean_pct": round(sum(per.values()) / len(per), 1) if per else None,
                      "max_pct": max(per.values()) if per else None, "iowait_pct": iow, "per_cpu": per}
        row["psi_ms_per_s"] = {k: round((p1[k] - self.p0.get(k, p1[k])) / 1000 / dt, 2) for k in p1}
        mi = meminfo()
        row["mem"] = {
            "available_mb": round(mi.get("MemAvailable", 0) / 1024),
            "used_mb": round((mi.get("MemTotal", 0) - mi.get("MemAvailable", 0)) / 1024),
            "cached_mb": round(mi.get("Cached", 0) / 1024),
            "swap_used_mb": round((mi.get("SwapTotal", 0) - mi.get("SwapFree", 0)) / 1024),
            "pswpin_per_s": round((v1.get("pswpin", 0) - self.v0.get("pswpin", 0)) / dt, 1),
            "pswpout_per_s": round((v1.get("pswpout", 0) - self.v0.get("pswpout", 0)) / dt, 1),
            "majfault_per_s": round((v1.get("pgmajfault", 0) - self.v0.get("pgmajfault", 0)) / dt, 1),
        }
        if d1 and self.d0:
            r, rs, rms, w, ws, wms, tk = (a - b for a, b in zip(d1, self.d0))
            ios = r + w
            row["disk"] = {"dev": self.dev, "reads_per_s": round(r / dt, 1), "writes_per_s": round(w / dt, 1),
                           "read_kBps": round(rs * 512 / 1024 / dt, 1), "write_kBps": round(ws * 512 / 1024 / dt, 1),
                           "await_ms": round((rms + wms) / ios, 2) if ios else None,
                           "util_pct": round(100 * tk / (dt * 1000), 1)}
        net = {}
        for name, v in n1.items():
            if name in self.n0:
                o = self.n0[name]
                net[name] = {"rx_kBps": round((v[0] - o[0]) / 1024 / dt, 1), "rx_pps": round((v[1] - o[1]) / dt, 1),
                             "rx_drop_per_s": round((v[2] - o[2]) / dt, 2),
                             "tx_kBps": round((v[3] - o[3]) / 1024 / dt, 1), "tx_pps": round((v[4] - o[4]) / dt, 1),
                             "tx_drop_per_s": round((v[5] - o[5]) / dt, 2)}
        row["net"] = net
        g = rd(DRM + "/gpu_busy_percent")
        gpu = {"busy_pct": int(g) if g and g.strip().isdigit() else None}
        gpu.update(gpu_metrics())
        gpu.update(hwmon())
        row["gpu"] = gpu
        row["freq"] = cpufreq()
        row["throttled"] = 1 if gpu.get("throttle_status") else 0
        row["procs"] = self.procs.sample()
        if self.e2:
            x1 = net_detail()
            row["netx"] = {k + "_per_s": round((x1[k] - self.x0[k]) / dt, 2) for k in x1
                           if k in self.x0 and k != "qdisc_backlog_b"}
            row["netx"]["qdisc_backlog_b"] = x1.get("qdisc_backlog_b")
            self.x0 = x1
        self.t0, self.c0, self.p0, self.v0, self.d0, self.n0 = t1, c1, p1, v1, d1, n1
        return row


def host_loop(out_dir: str, interval: float, stop: str, e2: bool = False):
    h = Host(e2)
    tfh = open(os.path.join(out_dir, "threads.jsonl"), "w") if e2 else None
    with open(os.path.join(out_dir, "samples.jsonl"), "w") as fh:
        nxt = time.monotonic() + interval
        while not os.path.exists(stop):
            time.sleep(max(0.0, nxt - time.monotonic()))
            nxt += interval
            t = time.monotonic()
            row = h.sample()
            row["cost_ms"] = round((time.monotonic() - t) * 1000, 1)
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            if tfh:
                tfh.write(json.dumps({"at_utc": row["at_utc"], "threads": h.procs.last_threads}) + "\n")
                tfh.flush()
    if tfh:
        tfh.close()


# ---------------------------------------------------------------- workload telemetry
def telem_loop(out_dir: str, stop: str):
    with open(os.path.join(out_dir, "telemetry.jsonl"), "w") as fh:
        while not os.path.exists(stop):
            try:
                d = json.load(urllib.request.urlopen("http://localhost:8765/diagnostics/stream-telemetry", timeout=2))
                fh.write(json.dumps({"at_utc": utc(), "fresh": d.get("fresh"), "elapsed_ms": d.get("session_elapsed_ms"),
                                     "decoder": d.get("decoder"), "latency": d.get("latency"),
                                     "receiver": d.get("receiver")}) + "\n")
            except Exception as e:  # noqa: BLE001 -- a sampler never stops on a failed read
                fh.write(json.dumps({"at_utc": utc(), "error": type(e).__name__}) + "\n")
            fh.flush()
            time.sleep(2)


def ra_window(env) -> str | None:
    r = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "^RetroArch "], capture_output=True,
                       text=True, env=env)
    w = r.stdout.split()
    return w[0] if w else None


def title_loop(out_dir: str, stop: str):
    env = dict(os.environ, DISPLAY=":0")
    w = None
    while not os.path.exists(stop):  # the window appears after the run's idle gap: wait for it, however long
        w = ra_window(env)
        if w:
            break
        time.sleep(2)
    with open(os.path.join(out_dir, "title.txt"), "w") as fh:
        if not w:
            fh.write("# no RetroArch window\n")
            return
        fh.write("# window found\n")
        p = subprocess.Popen(["xprop", "-spy", "-id", w, "WM_NAME"], stdout=subprocess.PIPE, text=True, env=env)

        def stopper():
            while not os.path.exists(stop):
                time.sleep(0.5)
            p.terminate()
        threading.Thread(target=stopper, daemon=True).start()
        for line in p.stdout:
            fh.write("%.3f %s\n" % (time.time(), line.strip()))
            fh.flush()


ENC_LOG = os.path.join(REPO, "logs/games/native_video_alpha.log")
ENC_RE = re.compile(r"frame=\s*(\d+)\s+fps=\s*([\d.]+).*?(?:dup=(\d+))?\s*(?:drop=(\d+))?\s*speed=\s*([\d.]+)x")


def encoder_loop(out_dir: str, stop: str):
    """E2: the encoder's own progress records (ffmpeg's `frame= fps= ... dup= drop= speed=` on stderr, which the
    companion writes to native_video_alpha.log, ~2 per s), tailed once a second: the last record's cumulative
    frame / dup / drop counts per second of host time. Read-only."""
    try:
        off = os.path.getsize(ENC_LOG)
    except OSError:
        off = 0
    with open(os.path.join(out_dir, "encoder.jsonl"), "w") as fh:
        while not os.path.exists(stop):
            time.sleep(1)
            try:
                size = os.path.getsize(ENC_LOG)
                if size < off:
                    off = 0
                with open(ENC_LOG, "rb") as f:
                    f.seek(off)
                    chunk = f.read(size - off).decode(errors="replace")
                off = size
            except OSError:
                continue
            recs = [m for m in ENC_RE.finditer(chunk.replace("\r", "\n"))]
            if not recs:
                fh.write(json.dumps({"at_utc": utc(), "records": 0}) + "\n")
                fh.flush()
                continue
            m = recs[-1]
            fh.write(json.dumps({"at_utc": utc(), "records": len(recs), "frame": int(m.group(1)),
                                 "fps": float(m.group(2)), "dup": int(m.group(3) or 0), "drop": int(m.group(4) or 0),
                                 "speed": float(m.group(5))}) + "\n")
            fh.flush()


def run(out_dir: str, telemetry: bool, title: bool, interval: float, e2: bool = False):
    os.makedirs(out_dir, exist_ok=True)
    stop = os.path.join(out_dir, "sampler.stop")
    if os.path.exists(stop):
        os.remove(stop)
    meta = {"started_utc": utc(), "interval_s": interval, "block_device": repo_block_device(),
            "rapl": rapl_status(), "telemetry": telemetry, "title": title, "e2": e2, "pid": os.getpid()}
    with open(os.path.join(out_dir, "sampler_meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    ts = [threading.Thread(target=host_loop, args=(out_dir, interval, stop, e2))]
    if e2:
        ts.append(threading.Thread(target=encoder_loop, args=(out_dir, stop)))
    if telemetry:
        ts.append(threading.Thread(target=telem_loop, args=(out_dir, stop)))
    if title:
        ts.append(threading.Thread(target=title_loop, args=(out_dir, stop)))
    for t in ts:
        t.start()
    for t in ts:
        t.join()


# ---------------------------------------------------------------- the summary
def stats(xs: list) -> dict | None:
    xs = sorted(x for x in xs if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x))
    if not xs:
        return None
    p95 = xs[min(len(xs) - 1, max(0, math.ceil(0.95 * len(xs)) - 1))]
    return {"n": len(xs), "mean": round(sum(xs) / len(xs), 3), "p95": p95, "max": xs[-1], "min": xs[0]}


def flatten(d, prefix="", out=None):
    out = {} if out is None else out
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            if k == "per_cpu":
                continue
            flatten(v, key + ".", out)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out.setdefault(key, []).append(v)
    return out


def summarize_host(rows: list) -> dict:
    series = {}
    for r in rows:
        r = dict(r)
        procs = r.pop("procs", {})
        r.pop("at_utc", None)
        flatten(r, "", series)
        for c, p in procs.items():
            if c == "other":
                series.setdefault("procs.other.cpu_pct", []).append(p.get("cpu_pct"))
                continue
            for k in ("cpu_pct", "rss_kb", "pss_kb", "pss_anon_kb", "pss_file_kb", "rss_anon_kb", "threads", "read_kBps",
                      "write_kBps", "rchar_kBps", "wchar_kBps", "n"):
                series.setdefault(f"procs.{c}.{k}", []).append(p.get(k))
    out = {k: stats(v) for k, v in sorted(series.items())}
    # per-process presence: in how many of the window's samples each category was seen
    out["_rows"] = len(rows)
    return {k: v for k, v in out.items() if v is not None}


def summarize_telemetry(rows: list) -> dict:
    """The stream's key figures from the client's C2 report (cumulative counters -> rate over the window)."""
    good = [r for r in rows if r.get("fresh") and isinstance(r.get("decoder"), dict)]
    if len(good) < 2:
        return {"rows": len(rows), "fresh_rows": len(good)}
    def g(r, *path):
        x = r
        for p in path:
            x = (x or {}).get(p) if isinstance(x, dict) else None
        return x
    first, last = good[0], good[-1]
    span_min = max(1e-6, ((last.get("elapsed_ms") or 0) - (first.get("elapsed_ms") or 0)) / 60000)
    out = {"rows": len(rows), "fresh_rows": len(good), "span_min": round(span_min, 2)}
    fps = [g(r, "decoder", "rendered_fps") for r in good]
    out["rendered_fps"] = stats(fps)
    for name in ("video_lost_packets", "lost_packets", "stale_drops", "rendered_frames", "decoder_errors",
                 "frames_over_20ms", "spikes_ge_20ms"):
        for blk in ("decoder", "receiver", "latency"):
            a, b = g(first, blk, name), g(last, blk, name)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                out[f"{blk}.{name}_per_min"] = round((b - a) / span_min, 3)
    return out


def ra_fps(title_path: str, t0: float, t1: float) -> dict:
    """RetroArch's own rate from the window-title counter: frames between the first and last title in the
    window over their time, plus the FPS readings."""
    pts, fps = [], []
    for line in (rd(title_path) or "").splitlines():
        if line.startswith("#"):
            continue
        m = re.match(r"([\d.]+) .*FPS:\s*([\d.]+).*Frames:\s*(\d+)", line)
        if m and t0 <= float(m.group(1)) <= t1:
            pts.append((float(m.group(1)), int(m.group(3))))
            fps.append(float(m.group(2)))
    if len(pts) < 2:
        return {"titles": len(pts)}
    return {"titles": len(pts), "frames_per_s": round((pts[-1][1] - pts[0][1]) / (pts[-1][0] - pts[0][0]), 3),
            "fps_reading": stats(fps)}


def parse_utc(s: str) -> float:
    import calendar
    s = s.rstrip("Z")
    frac = 0.0
    if "." in s:
        s, f = s.split(".", 1)
        frac = float("0." + f)
    return calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%S")) + frac


def summarize(out_dir: str, t_from: str | None, t_to: str | None, out_name: str = "sampler_summary.json") -> dict:
    rows = []
    for line in (rd(os.path.join(out_dir, "samples.jsonl")) or "").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if (t_from is None or r["at_utc"] >= t_from) and (t_to is None or r["at_utc"] <= t_to):
            rows.append(r)
    telem = []
    for line in (rd(os.path.join(out_dir, "telemetry.jsonl")) or "").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if (t_from is None or r["at_utc"] >= t_from) and (t_to is None or r["at_utc"] <= t_to):
            telem.append(r)
    meta = json.loads(rd(os.path.join(out_dir, "sampler_meta.json")) or "{}")
    s = {"window": {"from": t_from, "to": t_to, "host_rows": len(rows)}, "meta": meta,
         "host": summarize_host(rows),
         "throttled_samples": sum(r.get("throttled", 0) for r in rows),
         "missed_samples": None}
    if rows and t_from and t_to:
        s["missed_samples"] = max(0, round(parse_utc(t_to) - parse_utc(t_from)) - len(rows))
    if os.path.exists(os.path.join(out_dir, "telemetry.jsonl")):
        s["stream"] = summarize_telemetry(telem)
    if os.path.exists(os.path.join(out_dir, "title.txt")):
        s["retroarch"] = ra_fps(os.path.join(out_dir, "title.txt"),
                                parse_utc(t_from) if t_from else 0, parse_utc(t_to) if t_to else 1e12)
    if rows:
        s.update(e2_extras(out_dir, rows, t_from, t_to))
    with open(os.path.join(out_dir, out_name), "w") as fh:
        json.dump(s, fh, indent=1)
    return s


def _load_window(path: str, t_from, t_to) -> list:
    out = []
    for line in (rd(path) or "").splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if (t_from is None or r["at_utc"] >= t_from) and (t_to is None or r["at_utc"] <= t_to):
            out.append(r)
    return out


def e2_extras(out_dir: str, rows: list, t_from, t_to) -> dict:
    """E2 additions to a summary: per-core p95 and the busiest core's p95; throttle_status counts by value; the
    encoder's capture fps and dup / drop per minute; per-thread CPU (mean, p95) for the thread categories."""
    out = {}
    per = {}
    for r in rows:
        for k, v in ((r.get("cpu") or {}).get("per_cpu") or {}).items():
            per.setdefault(k, []).append(v)
    p95 = {k: stats(v)["p95"] for k, v in per.items() if stats(v)}
    if p95:
        out["per_core_p95"] = p95
        out["busiest_core_p95"] = max(p95.values())
    tv = {}
    for r in rows:
        t = (r.get("gpu") or {}).get("throttle_status")
        if t:
            tv[hex(t)] = tv.get(hex(t), 0) + 1
    out["throttle_by_value"] = tv
    enc = [r for r in _load_window(os.path.join(out_dir, "encoder.jsonl"), t_from, t_to) if r.get("records")]
    if len(enc) >= 2:
        a, b = enc[0], enc[-1]
        span = parse_utc(b["at_utc"]) - parse_utc(a["at_utc"])
        if span > 0 and b["frame"] >= a["frame"]:
            out["encoder"] = {"capture_fps": round((b["frame"] - a["frame"]) / span, 3),
                              "dup_per_min": round((b["dup"] - a["dup"]) / span * 60, 2),
                              "drop_per_min": round((b["drop"] - a["drop"]) / span * 60, 2),
                              "speed": stats([r["speed"] for r in enc]), "rows": len(enc)}
    th = _load_window(os.path.join(out_dir, "threads.jsonl"), t_from, t_to)
    if th:
        acc = {}
        for r in th:
            for cat, lst in (r.get("threads") or {}).items():
                for pid, tid, cpu, pol, sc in lst:
                    d = acc.setdefault((cat, pid, tid), {"cpu": [], "pol": pol, "sys": {}})
                    if cpu is not None:
                        d["cpu"].append(cpu)
                    d["sys"][sc] = d["sys"].get(sc, 0) + 1
        tout = {}
        for (cat, pid, tid), d in acc.items():
            st = stats(d["cpu"])
            if not st:
                continue
            tout.setdefault(cat, []).append({"pid": pid, "tid": tid, "is_main": pid == tid, "policy": d["pol"],
                                             "syscall_mode": max(d["sys"], key=d["sys"].get), "seen": st["n"],
                                             "cpu_mean": st["mean"], "cpu_p95": st["p95"], "cpu_max": st["max"]})
        for cat in tout:
            tout[cat].sort(key=lambda x: -x["cpu_mean"])
        out["threads"] = tout
    return out


# ---------------------------------------------------------------- coverage and self-test
def coverage() -> dict:
    gm = gpu_metrics()
    return {
        "cpu_per_core": os.path.exists("/proc/stat"),
        "psi": os.path.exists("/proc/pressure/cpu"),
        "pss_smaps_rollup": os.access(f"/proc/{os.getpid()}/smaps_rollup", os.R_OK),
        "swap": "SwapTotal" in meminfo(),
        "block_device": repo_block_device(),
        "net_interfaces": sorted(netdev()),
        "gpu_busy_percent": rd(DRM + "/gpu_busy_percent") is not None,
        "gpu_metrics": bool(gm),
        "vcn_activity": gm.get("vcn_activity_pct") is not None,
        "socket_power": gm.get("socket_power_w") is not None,
        "throttle_status": "throttle_status" in gm,
        "cpufreq": bool(cpufreq()),
        "intel_thermal_throttle_counters": os.path.exists("/sys/devices/system/cpu/cpu0/thermal_throttle"),
        "rapl": rapl_status(),
        "wall_power": "ABSENT (needs a meter)",
    }


def self_test() -> int:
    assert stats([1, 2, 3, 4]) == {"n": 4, "mean": 2.5, "p95": 4, "max": 4, "min": 1}
    assert stats([None, "x"]) is None
    assert stats(list(range(1, 101)))["p95"] == 95
    f = flatten({"a": 1, "b": {"c": 2.5, "per_cpu": {"cpu0": 1}}, "d": True})
    assert f == {"a": [1], "b.c": [2.5]}, f
    assert abs(parse_utc("2026-10-05T06:00:00.500Z") - parse_utc("2026-10-05T06:00:00Z") - 0.5) < 1e-9
    h = Host()
    time.sleep(1)
    r = h.sample()
    assert r["cpu"]["mean_pct"] is not None and "mem" in r and "procs" in r
    assert "other" in r["procs"]
    t = summarize_telemetry([{"fresh": True, "elapsed_ms": 0, "decoder": {"rendered_fps": 60, "stale_drops": 0}},
                             {"fresh": True, "elapsed_ms": 60000, "decoder": {"rendered_fps": 59, "stale_drops": 3}}])
    assert t["decoder.stale_drops_per_min"] == 3.0 and t["rendered_fps"]["mean"] == 59.5, t
    print("E1_SAMPLER_SELF_TEST_OK")
    return 0


def main(argv: list) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--coverage" in argv:
        print(json.dumps(coverage(), indent=1))
        return 0
    if "--once" in argv:
        h = Host()
        time.sleep(1)
        t = time.monotonic()
        r = h.sample()
        r["cost_ms"] = round((time.monotonic() - t) * 1000, 1)
        print(json.dumps(r, indent=1))
        return 0
    if len(argv) >= 2 and argv[0] == "run":
        iv = float(argv[argv.index("--interval") + 1]) if "--interval" in argv else 1.0
        run(argv[1], "--telemetry" in argv, "--title" in argv, iv, "--e2" in argv)
        return 0
    if len(argv) >= 2 and argv[0] == "summarize":
        f = argv[argv.index("--from") + 1] if "--from" in argv else None
        t = argv[argv.index("--to") + 1] if "--to" in argv else None
        print(json.dumps(summarize(argv[1], f, t), indent=1)[:4000])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
