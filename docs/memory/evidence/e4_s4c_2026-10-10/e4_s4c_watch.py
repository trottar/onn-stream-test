#!/usr/bin/env python3
"""E4-S4C -- the link watch, and grab deferral on the first clean window, run as pre-registered
(e4_s4c_preregistration.txt §1-§6). One process from the hash to the cap (2026-10-15T04:00:00Z); resumable from
watch_state.json if restarted.

THE PING TRACE (a thread, from start to the cap): the unprivileged `ping` as installed (ICMP datagram socket; no sudo),
1 echo/s, host -> client. The client's address is read from adb's device list at (re)start and never written. Parsed
in memory into 60-s bins (sent, lost, RTT min / median / p99) -> ping.jsonl, each bin tagged with what was running.

THE PROBE, every 45 min start-to-start: tools/e1_suite.py run --plan E1-PS1-STREAM:1:120 --e2 --window 300 into
~/privyhub_link_watch/probe_<n>/ (outside the repo). Beside it: the Opal read-only (o1_opal_sample.sh, O1's sampler
copied here, 10-s rounds, redacted before storage, into the probe dir); the client's thermal reading once, 150 s into
the window (dumpsys thermalservice); after the teardown the client's own radio series harvested (p4_harvest.py, D-BASE
P4's, copied here) and read over the window. One row per probe -> link_watch.jsonl; the probe's summary.json,
encoder.jsonl and title.txt copied into probes/<n>/. A probe whose status is not OK (the runner's own two launch
replacements included) is retried once, then recorded no_play.

THE DEFERRAL (deferral.json): on the first CLEAN probe (loss/min < 10, rendered >= 59.5, resyncs <= 2) the control
(E1-PS1-STREAM, 20 min, no flag -> runs/). Clean control (loss < 10, rendered >= 59.5, resyncs <= 10) -> the pre-run
guide read (>= 60 s after the EPG's background refresh last moved) -> E1-CONC + flag r1, r2, E1-CONC + flag at
CPUQuota=150%, one suite invocation each (runs/). A flagged run with loss/min > 3 x the control's AND > 100 is
link_voided and re-run on the next clean probe (a fresh guide read first), at most 2 re-runs per slot. After the set
is complete: probing only, until the cap. No probe or run starts after the cap.

Next start = max(now, the last start + 45 min) -- the last start being the probe's, or the control's / the last
flagged run's when they ran."""
import importlib.util
import json
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SUITE = REPO / "tools/e1_suite.py"
PRE = HERE / "e4_s4c_preregistration.txt"
WATCH = Path.home() / "privyhub_link_watch"
RUNS = HERE / "runs"
CAP = datetime(2026, 10, 15, 4, 0, 0, tzinfo=timezone.utc).timestamp()
PERIOD = 45 * 60
ET = ZoneInfo("America/New_York")
FLAG = "PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1"
SLOTS = [("conc_flag_r1", "E1-CONC_flag", f"E1-CONC:1:120:{FLAG}"),
         ("conc_flag_r2", "E1-CONC_flag", f"E1-CONC:1:120:{FLAG}"),
         ("conc_flag_cpu150", "E1-CONC_flag_cpu150", f"E1-CONC:1:120:{FLAG}:CPUQuota=150%")]
MAX_RERUNS = 2
STATE_P, LW_P, PING_P, DEF_P = HERE / "watch_state.json", HERE / "link_watch.jsonl", HERE / "ping.jsonl", HERE / "deferral.json"

spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)

ACTIVITY = "idle"
STOP = threading.Event()


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def ep(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp() + \
        (float("0." + s[20:-1]) if len(s) > 20 and s[19] == "." else 0)


def log(*a):
    line = f"[e4s4c {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(HERE / "watch_console.log", "a") as fh:
        fh.write(line + "\n")


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def jdump(p, obj):
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, default=str))
    os.replace(tmp, p)          # an atomic replace of the driver's own state file (not a deletion of data)


def append(p, row):
    with open(p, "a") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]


# ---------------------------------------------------------------- the ping trace
RAW = deque()           # (send epoch, rtt ms or None) for the last 3 h, in memory only
RAW_LOCK = threading.Lock()


def client_addr():
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    for line in out.splitlines()[1:]:
        m = re.match(r"(\d{1,3}(?:\.\d{1,3}){3}):\d+\s+device", line)
        if m:
            return m.group(1)
    return None


def ping_thread():
    seqs = {}           # seq -> [send epoch, rtt or None, activity]
    flushed_to = (int(time.time()) // 60) * 60
    proc = None
    rx_reply = re.compile(r"^\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=([\d.]+) ms")
    rx_noans = re.compile(r"^\[(\d+\.\d+)\] no answer yet for icmp_seq=(\d+)")
    rx_other = re.compile(r"^\[(\d+\.\d+)\].*icmp_seq=(\d+)")
    lines = deque()
    gen = 0

    def reader(p, g):
        for line in p.stdout:
            lines.append((g, line))

    while not STOP.is_set():
        if proc is None or proc.poll() is not None:
            if proc is not None:
                append(PING_P, {"event": "ping_exit", "at_utc": utc(), "rc": proc.returncode})
                time.sleep(10)
            addr = client_addr()
            if not addr:
                append(PING_P, {"event": "no_client_address", "at_utc": utc()})
                time.sleep(60)
                continue
            gen += 1
            seqs = {}
            proc = subprocess.Popen(["ping", "-D", "-O", "-n", "-i", "1", "-W", "2", addr], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, bufsize=1)
            threading.Thread(target=reader, args=(proc, gen), daemon=True).start()
            append(PING_P, {"event": "ping_start", "at_utc": utc(), "generation": gen,
                            "how": "ping -D -O -n -i 1 -W 2 <client> (unprivileged, ICMP datagram socket)"})
        while lines:
            g, line = lines.popleft()
            if g != gen:
                continue
            m = rx_reply.match(line)
            if m:
                t, sq, rtt = float(m.group(1)), int(m.group(2)), float(m.group(3))
                e = seqs.setdefault(sq, [t - rtt / 1000, None, ACTIVITY])
                e[1] = rtt
                continue
            m = rx_noans.match(line) or rx_other.match(line)
            if m:
                t, sq = float(m.group(1)), int(m.group(2))
                seqs.setdefault(sq, [t - 1.0, None, ACTIVITY])
                if line.find("no answer yet") < 0 and line.find("time=") < 0:
                    seqs[sq].append("error")
        now = time.time()
        while flushed_to + 60 <= now - 15:
            b0, b1 = flushed_to, flushed_to + 60
            inb = [(sq, e) for sq, e in seqs.items() if b0 <= e[0] < b1]
            if inb:
                rtts = [e[1] for _, e in inb if e[1] is not None]
                acts = sorted({e[2] for _, e in inb})
                append(PING_P, {"bin_utc": utc(b0), "sent": len(inb), "lost": sum(1 for _, e in inb if e[1] is None),
                                "rtt_min": min(rtts, default=None), "rtt_median": statistics.median(rtts) if rtts else None,
                                "rtt_p99": pct(rtts, 0.99), "running": acts})
                with RAW_LOCK:
                    for _, e in sorted(inb, key=lambda x: x[1][0]):
                        RAW.append((e[0], e[1]))
                    while RAW and RAW[0][0] < now - 3 * 3600:
                        RAW.popleft()
                for sq, _ in inb:
                    seqs.pop(sq, None)
            flushed_to = b1
        time.sleep(1)
    if proc and proc.poll() is None:
        proc.send_signal(signal.SIGINT)
    append(PING_P, {"event": "ping_stop", "at_utc": utc()})


def ping_before(t, span=2400):
    with RAW_LOCK:
        xs = [r for s, r in RAW if t - span <= s < t]
    if not xs:
        return {"sent": 0}
    rt = [r for r in xs if r is not None]
    return {"sent": len(xs), "lost": len(xs) - len(rt), "loss_pct": round(100 * (len(xs) - len(rt)) / len(xs), 3),
            "rtt_median": round(statistics.median(rt), 2) if rt else None, "rtt_p99": pct(rt, 0.99)}


# ---------------------------------------------------------------- the readings beside a probe
def opal_summary(path, t0, t1):
    rows = []
    if path.exists():
        for l in path.read_text().splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if r.get("at_utc") and t0 <= r["at_utc"] <= t1:
                rows.append(r)
    if not rows:
        return {"rounds": 0}
    air = [r.get("airtime") or {} for r in rows]
    util = [a["utilization_pct"] for a in air if a.get("utilization_pct") is not None]
    # the client = the station whose tx packets advanced most over the window (by behaviour, never by identifier)
    first, last = {}, {}
    for r in rows:
        for st in r.get("stations") or []:
            first.setdefault(st["station"], st)
            last[st["station"]] = st
    best = max(last, key=lambda s: (last[s].get("tx_packets") or 0) - (first[s].get("tx_packets") or 0), default=None)
    out = {"rounds": len(rows), "channel": statistics.mode([a.get("channel") for a in air]),
           "width_mhz": statistics.mode([a.get("width_mhz") for a in air]),
           "utilization_mean_pct": round(statistics.mean(util), 2) if util else None, "utilization_max_pct": max(util, default=None),
           "noise_dbm_median": statistics.median([a["noise_dbm"] for a in air if a.get("noise_dbm") is not None] or [None]) if any(a.get("noise_dbm") is not None for a in air) else None,
           "stations_median": statistics.median([len(r.get("stations") or []) for r in rows]),
           "log_events": sum(len(r.get("log_events") or []) for r in rows),
           "opal_load_median": statistics.median([r["loadavg_1m"] for r in rows if r.get("loadavg_1m") is not None] or [0])}
    if best:
        sig = [st.get("signal_dbm") for r in rows for st in (r.get("stations") or []) if st["station"] == best and st.get("signal_dbm") is not None]
        txb = [st.get("tx_bitrate_mbps") for r in rows for st in (r.get("stations") or []) if st["station"] == best and st.get("tx_bitrate_mbps") is not None]
        dtx = (last[best].get("tx_packets") or 0) - (first[best].get("tx_packets") or 0)
        drt = (last[best].get("tx_retries") or 0) - (first[best].get("tx_retries") or 0)
        out["client_station"] = {"signal_dbm_median": statistics.median(sig) if sig else None, "signal_dbm_min": min(sig, default=None),
                                 "tx_bitrate_mbps_median": statistics.median(txb) if txb else None,
                                 "tx_packets": dtx, "tx_retries": drt, "retry_pct": round(100 * drt / dtx, 2) if dtx > 0 else None}
    return out


def client_summary(path, t0, t1):
    try:
        h = json.loads(path.read_text())
    except (OSError, ValueError):
        return {"harvest": False}
    rows = [r for r in h.get("score_report_rows") or [] if r.get("at_utc") and t0 <= r["at_utc"] <= t1]

    def col(c):
        out = []
        for r in rows:
            try:
                out.append(float(r[c]))
            except (KeyError, ValueError, TypeError):
                pass
        return out
    rssi, tx, rx = col("rssi"), col("txLinkSpeed"), col("rxLinkSpeed")
    scans = [s for s in h.get("scan_events") or [] if s.get("at_utc") and t0 <= s["at_utc"] <= t1]
    a = h.get("association") or {}
    return {"harvest": True, "score_rows_in_window": len(rows), "rssi_median": statistics.median(rssi) if rssi else None,
            "rssi_min": min(rssi, default=None), "rssi_max": max(rssi, default=None),
            "tx_link_mbps_median": statistics.median(tx) if tx else None, "rx_link_mbps_median": statistics.median(rx) if rx else None,
            "scans_in_window": len(scans), "band": a.get("band"), "channel": a.get("channel"),
            "width_mhz": a.get("channel_width_mhz"), "supplicant_state": a.get("supplicant_state")}


def client_thermal():
    try:
        t = subprocess.run(["adb", "shell", "dumpsys thermalservice | grep -E 'Thermal Status|mValue'"],
                           capture_output=True, text=True, timeout=20).stdout
    except Exception:
        return None
    hal = [float(x) for x in re.findall(r"mValue=([-\d.]+), mType=\d+, mName=cpu-thermal", t)]
    st = re.search(r"Thermal Status: (\d+)", t)
    return {"cpu_thermal_c": hal[-1] if hal else None, "thermal_status": int(st.group(1)) if st else None, "at_utc": utc()}


# ---------------------------------------------------------------- running the suite
def suite(out, plan, window, timeout_s):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "suite_console.log" if not str(out).startswith(str(HERE)) else HERE / "runs_console.log", "a") as fh:
        p = subprocess.Popen([sys.executable, str(SUITE), "run", "--out", str(out), "--prereg", str(PRE), "--e2",
                              "--window", str(window), "--gap", "120", "--plan", plan], stdout=fh, stderr=subprocess.STDOUT,
                             cwd=str(REPO))
        try:
            return p.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            log(f"the suite exceeded {timeout_s} s: SIGINT (its finally-teardown runs)")
            p.send_signal(signal.SIGINT)
            try:
                return p.wait(timeout=900)
            except subprocess.TimeoutExpired:
                log("the suite did not exit 900 s after SIGINT; waiting on it")
                return p.wait()


def latest_run(wdir):
    runs = [d for d in wdir.glob("run*") if d.name[3:].isdigit()]
    return max(runs, key=lambda d: int(d.name[3:])) if runs else None


def load_summary(rd):
    try:
        return json.loads((rd / "summary.json").read_text())
    except (OSError, ValueError, TypeError):
        return None


def figures(s):
    rf = k(s, "teardown", "report_fields") or {}
    mins = (rf.get("duration_ms") or 0) / 60000
    hh = lambda key: k(s, "host", "host", key, "mean")
    return {"status": (s or {}).get("status"), "window": (s or {}).get("window"),
            "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "underruns": k(s, "key", "heartbeat", "audio_underruns"),
            "receiver_lost_per_min": k(s, "key", "telemetry", "receiver_lost_packets_per_min"),
            "stale_per_min": round(rf["decoder.stale_output_drops"] / mins, 3) if mins and "decoder.stale_output_drops" in rf else None,
            "spikes20_per_min": round(rf["decoder.spike_20_ms"] / mins, 2) if mins and "decoder.spike_20_ms" in rf else None,
            "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []),
            "controller_pauses": len(k(s, "key", "recovery", "controller_pauses") or []),
            "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": hh("cpu.mean_pct"),
            "companion_cpu": hh("procs.companion.cpu_pct"), "socket_w": hh("gpu.socket_power_w"),
            "host_tctl_c": hh("gpu.tctl_c"), "host_soc_c": hh("gpu.t_soc_c"),
            "preflight_ok": k(s, "preflight", "ok"), "flags_absent_after": k(s, "teardown", "flags_absent"),
            "apk": k(s, "teardown", "apk")}


def probe_clean(f):
    return f["status"] == "OK" and None not in (f["loss_per_min"], f["rendered_fps"], f["resyncs"]) and \
        f["loss_per_min"] < 10 and f["rendered_fps"] >= 59.5 and f["resyncs"] <= 2


def control_clean(f):
    return f["status"] == "OK" and None not in (f["loss_per_min"], f["rendered_fps"], f["resyncs"]) and \
        f["loss_per_min"] < 10 and f["rendered_fps"] >= 59.5 and f["resyncs"] <= 10


def run_probe(n):
    global ACTIVITY
    pdir = WATCH / f"probe_{n:03d}"
    pdir.mkdir(parents=True, exist_ok=True)
    ACTIVITY = f"probe_{n}"
    t_start = time.time()
    attempts, f, s, rd = 0, None, None, None
    therm = {}
    for attempt in (1, 2):
        attempts = attempt
        air = pdir / f"air_{attempt}.jsonl"
        op = subprocess.Popen(["bash", str(HERE / "o1_opal_sample.sh"), str(air), "10", "wlan1"],
                              stdout=subprocess.DEVNULL, stderr=open(pdir / f"opal_{attempt}.log", "a"))
        before = latest_run(pdir / "E1-PS1-STREAM")

        def thermal_when_window(attempt=attempt):
            sl = pdir / "suite.log"
            seen = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
            t0 = time.time()
            while time.time() - t0 < 1800 and not STOP.is_set():
                cur = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
                if cur > seen:
                    time.sleep(150)
                    therm[attempt] = client_thermal()
                    return
                time.sleep(5)
        th = threading.Thread(target=thermal_when_window, daemon=True)
        th.start()
        suite(pdir, "E1-PS1-STREAM:1:120", 300, 3 * 3600)
        (Path(str(air) + ".stop")).touch()
        try:
            op.wait(timeout=60)
        except subprocess.TimeoutExpired:
            op.send_signal(signal.SIGINT)
        rd = latest_run(pdir / "E1-PS1-STREAM")
        s = load_summary(rd) if rd and rd != before else None
        f = figures(s)
        if f["status"] == "OK":
            break
        log(f"probe {n}: attempt {attempt} not OK ({f['status']})" + ("; retrying once" if attempt == 1 else "; no_play"))
    # the client's radio series, harvested after the teardown (D-BASE P4's way)
    subprocess.run([sys.executable, str(HERE / "p4_harvest.py"), "probe", str(pdir)], capture_output=True, text=True,
                   timeout=120, cwd=str(HERE))
    ACTIVITY = "idle"
    final = {}
    try:
        final = json.loads((pdir / "final_state.json").read_text())
    except (OSError, ValueError):
        pass
    w = (f or {}).get("window") or {}
    t0, t1 = w.get("from"), w.get("to")
    st = datetime.fromtimestamp(t_start, timezone.utc)
    et = st.astimezone(ET)
    row = {"probe": n, "start_utc": utc(t_start), "start_et": et.isoformat(timespec="seconds"), "hour_et": et.hour,
           "day_et": et.strftime("%Y-%m-%d"), "weekday_et": et.strftime("%a"), "attempts": attempts,
           "no_play": f["status"] != "OK", "run_dir": f"~/privyhub_link_watch/probe_{n:03d}/" + (str(rd.relative_to(pdir)) if rd else ""),
           **{x: v for x, v in f.items() if x != "window"}, "window": w,
           "clean": probe_clean(f), "final_flags_absent": final.get("flags_absent"),
           "final_e4_constraint_absent": final.get("e4_constraint_absent"),
           "client_thermal": therm.get(attempts),
           "air": opal_summary(pdir / f"air_{attempts}.jsonl", t0, t1) if t0 else {"rounds": 0},
           "client": client_summary(pdir / "air_harvest_probe.json", t0, t1) if t0 else {"harvest": None},
           "ping_40min_before": ping_before(t_start)}
    append(LW_P, row)
    dst = HERE / "probes" / f"{n:03d}"
    dst.mkdir(parents=True, exist_ok=True)
    if rd:
        for name in ("summary.json", "encoder.jsonl", "title.txt"):
            if (rd / name).exists():
                shutil.copy2(rd / name, dst / name)
    log(f"probe {n}: {'CLEAN' if row['clean'] else ('no_play' if row['no_play'] else 'not clean')} loss {f['loss_per_min']} "
        f"rendered {f['rendered_fps']} resyncs {f['resyncs']} flags_absent {f['flags_absent_after']}/{final.get('flags_absent')}")
    if f["status"] == "OK" and not (f["flags_absent_after"] and final.get("flags_absent") and f["preflight_ok"]):
        log(f"probe {n}: STATE VIOLATION -- flags_absent / preflight not all true")
    return row


# ---------------------------------------------------------------- the deferral
def bg_quiet_then_guide(limit_s=1800):
    """The pre-run guide read, >= 60 s after the EPG's background refresh last moved (worker idle, nothing pending,
    the completed / failed counts unchanged for 60 s)."""
    t0, quiet_since, last = time.time(), None, None
    while time.time() - t0 < limit_s:
        b = (E1.http("GET", "/plugins/epg/status", 10)[1] or {}).get("background_refresh") or {}
        sig = (b.get("worker_alive"), b.get("pending_count"), b.get("completed_count"), b.get("failed_count"))
        idle = not b.get("worker_alive") and (b.get("pending_count") or 0) == 0
        if idle and sig == last:
            quiet_since = quiet_since or time.time()
        else:
            quiet_since = time.time() if idle else None
        last = sig
        if quiet_since and time.time() - quiet_since >= 60:
            break
        time.sleep(5)
    g = E1.guide_read()
    g.update({"at_utc": utc(), "waited_s": round(time.time() - t0, 1), "background_refresh": b,
              "quiet_60s": bool(quiet_since and time.time() - quiet_since >= 60)})
    return g


def run_one(wdir_name, plan, window, act):
    global ACTIVITY
    ACTIVITY = act
    t = time.time()
    before = latest_run(RUNS / wdir_name)
    suite(RUNS, plan, window, 4 * 3600)
    ACTIVITY = "idle"
    rd = latest_run(RUNS / wdir_name)
    s = load_summary(rd) if rd and rd != before else None
    return t, rd, figures(s)


def flagged_pass(st, d):
    """Run every slot that needs a run (never run, or last attempt voided with re-runs left), in order."""
    ctl = d["control"]
    todo = [sl for sl in SLOTS if not d["slots"][sl[0]] or
            (d["slots"][sl[0]][-1]["link_voided"] and len(d["slots"][sl[0]]) <= MAX_RERUNS)]
    if not todo:
        return
    g = bg_quiet_then_guide()
    d["guide_reads"].append(g)
    gi = len(d["guide_reads"]) - 1
    jdump(DEF_P, d)
    log("pre-run guide read", {x: g.get(x) for x in ("channels_serving", "programmes_total", "waited_s", "quiet_60s")})
    for name, wdir, plan in todo:
        if time.time() >= CAP:
            log("the cap: no flagged run starts after it")
            return
        t, rd, f = run_one(wdir, plan, 1200, name)
        st["last_start"] = t
        voided = bool(f["status"] == "OK" and f["loss_per_min"] is not None and
                      f["loss_per_min"] > 3 * ctl["loss_per_min"] and f["loss_per_min"] > 100)
        a = {"run": str(rd.relative_to(HERE)) if rd else None, "start_utc": utc(t), "guide_read": gi, **f, "link_voided": voided}
        d["slots"][name].append(a)
        jdump(DEF_P, d)
        jdump(STATE_P, st)
        log(f"{name} attempt {len(d['slots'][name])}: {f['status']} loss {f['loss_per_min']} rendered {f['rendered_fps']} "
            f"resyncs {f['resyncs']} link_voided {voided} flags_absent {f['flags_absent_after']}")


def set_state(d):
    if d["control"] is None:
        return "await_clean_probe"
    pend = [sl[0] for sl in SLOTS if not d["slots"][sl[0]] or
            (d["slots"][sl[0]][-1]["link_voided"] and len(d["slots"][sl[0]]) <= MAX_RERUNS)]
    return "await_rerun" if pend else "set_complete"


def main():
    WATCH.mkdir(parents=True, exist_ok=True)
    st = json.loads(STATE_P.read_text()) if STATE_P.exists() else {"probes": 0, "last_start": None, "started_utc": utc()}
    d = json.loads(DEF_P.read_text()) if DEF_P.exists() else {"controls": [], "control": None, "guide_reads": [],
                                                              "slots": {sl[0]: [] for sl in SLOTS}}
    log("start; state", {x: st.get(x) for x in ("probes", "last_start")}, "deferral", set_state(d))
    pt = threading.Thread(target=ping_thread, daemon=True)
    pt.start()
    while True:
        now = time.time()
        nxt = max(now, (st["last_start"] or 0) + PERIOD)
        if nxt >= CAP:
            log("the cap: no probe starts after it")
            break
        if now < nxt:
            time.sleep(min(30, nxt - now))
            continue
        n = st["probes"] + 1
        st["probes"] = n
        st["last_start"] = now
        jdump(STATE_P, st)
        row = run_probe(n)
        phase = set_state(d)
        if row["clean"] and phase == "await_clean_probe" and time.time() < CAP:
            log(f"probe {n} clean: the control")
            t, rd, f = run_one("E1-PS1-STREAM", "E1-PS1-STREAM:1:120", 1200, "control")
            st["last_start"] = t
            c = {"probe": n, "run": str(rd.relative_to(HERE)) if rd else None, "start_utc": utc(t), **f, "clean": control_clean(f)}
            d["controls"].append(c)
            log(f"control: {'CLEAN' if c['clean'] else 'not clean'} loss {f['loss_per_min']} rendered {f['rendered_fps']} resyncs {f['resyncs']}")
            if c["clean"]:
                d["control"] = c
            jdump(DEF_P, d)
            jdump(STATE_P, st)
            if c["clean"]:
                flagged_pass(st, d)
        elif row["clean"] and phase == "await_rerun" and time.time() < CAP:
            log(f"probe {n} clean: the voided flagged run(s) re-run")
            flagged_pass(st, d)
        d["state"] = set_state(d)
        jdump(DEF_P, d)
        jdump(STATE_P, st)
    STOP.set()
    pt.join(timeout=30)
    d["state"] = set_state(d)
    d["closed_utc"] = utc()
    jdump(DEF_P, d)
    log("watch closed; deferral state", d["state"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
