#!/usr/bin/env python3
"""LINK-N1: the nightly read-only watch on the 1-am quarter-hour (LINK-R1 Part 2; task
docs/memory/handoffs/LINK-R1_5GHZ_CHECK_AND_NIGHTLY_WATCH_TASK.md). Runs detached as the systemd --user unit
privyhub-link-n1. NO STREAM, NO COMPANION RESTART, NO GAME: it only reads.

Each night it sleeps until 00:30 America/New_York (04:30Z while EDT holds; the UTC target is computed with zoneinfo and
written to the status line), samples until 01:30 local, writes nights/<local date>.jsonl and a summary.md row, and sleeps
again -- until the cap written in the pre-registration (CAP_UTC) or ~/privyhub_link_n1/STOP.

Per night, read-only:
  - ping: the hub -> the onn, the unprivileged `ping -D -O -n -i 1 -W 2` (ICMP datagram socket, no sudo), 1-s rows:
    {kind: ping, t, rtt_ms | null, lost}. The onn's address is read from adb's device list into memory only (the
    companion's paired-device store holds no address: id, name, key, permissions -- disclosed); it is NEVER written:
    rows carry RTT and loss only;
  - onn, every 30 s over adb (state reads): dumpsys wifi's mWifiInfo line -> frequency, band, channel, standard, RSSI,
    link / tx / rx speed (SSID, BSSID, MAC, IP never kept); /proc/net/udp6 drops for the stream ports 48100 / 48101 if
    such a socket exists (D-BASE-P5's parse; only the port and the drops are read); /proc/uptime;
  - opal, every 60 s: LINK-R1's copy of B's o1_opal_sample.sh (wlan1, read-only; every byte through o1_redact.py, then
    o1_parse.py) -> {kind: opal, ...the parsed round}; the onn's station is marked by connected-time continuity from
    the last identification (seeded from LINK-R1's window, where it was told by behaviour), else by the closest link
    rate / signal to the onn's own adb read in the same minute (method recorded per round);
  - host, every 30 s: /proc/loadavg and the hub's clock.
  - every row carries stream_active (the companion's /plugins/games/status `active`, read every 30 s): if the user is
    playing, it samples anyway and marks the rows.
    python3 link_n1_watch.py [--dry]     (--dry: a 2-min sample now into dry_run/, then exit)
"""
import hashlib
import importlib.util
import json
import re
import signal
import statistics
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
EV = HERE.parent
REPO = HERE.parents[3]
PRE = HERE / "link_n1_preregistration.txt"
OPAL_SH = EV / "link_r1_2026-10-23/o1_opal_sample.sh"
WATCH = Path.home() / "privyhub_link_n1"
DRY = "--dry" in sys.argv
OUTD = HERE / "dry_run" if DRY else WATCH
NIGHTS = HERE / "dry_run" / "nights" if DRY else HERE / "nights"
SUMMARY = (HERE / "dry_run" if DRY else HERE) / "summary.md"
STATE_P = (HERE / "dry_run" if DRY else HERE) / "watch_state.json"
STATUS_P, LOG_P, STOPFILE = OUTD / "status.txt", OUTD / "watch.log", WATCH / "STOP"
ET = ZoneInfo("America/New_York")
START_HM, END_HM = (0, 30), (1, 30)
PORTS = {"BBE4": "video_48100", "BBE5": "audio_48101"}
STOP = threading.Event()
LOCK = threading.Lock()
STATUS = {"doing": "starting", "next": "-", "nights": 0, "last": "-"}

spec = importlib.util.spec_from_file_location("e1_suite", REPO / "tools/e1_suite.py")
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def cap_from_pre():
    for line in PRE.read_text().splitlines():
        if line.strip().startswith("CAP_UTC:"):
            v = line.split(":", 1)[1].strip()
            return v, datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    return "unset", 0.0


CAP_UTC, CAP = cap_from_pre()


def log(*a):
    line = f"{utc()} " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with LOCK, open(LOG_P, "a") as fh:
        fh.write(line + "\n")


def write_status(**kw):
    with LOCK:
        STATUS.update(kw)
        line = (f"{utc()} | doing: {STATUS['doing']} | next: {STATUS['next']} | nights done: {STATUS['nights']} | "
                f"last: {STATUS['last']} | cap {CAP_UTC} | stop: touch ~/privyhub_link_n1/STOP\n")
        STATUS_P.write_text(line)


def heartbeat():
    while not STOP.is_set():
        write_status()
        STOP.wait(300)


def stopped():
    return STOPFILE.exists() or time.time() >= CAP


def stop_watch():
    """The STOP file (or the cap) ends everything within ~10 s, a night in flight included: its threads see STOP, the
    night is closed and summarized, and main() writes the final status line."""
    while not STOP.is_set():
        if stopped():
            STOP.set()
            return
        time.sleep(10)


def adb_shell(cmd, timeout=20):
    try:
        return subprocess.run(["adb", "shell", cmd], capture_output=True, text=True, timeout=timeout).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


ADDR = {"v": None}       # the onn's LAN address: memory only, never written


def refresh_addr():
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    for line in out.splitlines()[1:]:
        m = re.match(r"(\d{1,3}(?:\.\d{1,3}){3}):\d+\s+device", line)
        if m:
            ADDR["v"] = m.group(1)
            return True
    return False


def windows_from(now):
    """The next (start, end) epoch pair of 00:30-01:30 America/New_York at or after now (a window in progress counts)."""
    d = datetime.fromtimestamp(now, ET).date() - timedelta(days=1)
    while True:
        a = datetime(d.year, d.month, d.day, *START_HM, tzinfo=ET).timestamp()
        b = datetime(d.year, d.month, d.day, *END_HM, tzinfo=ET).timestamp()
        if b > now:
            return a, b, d.isoformat()
        d += timedelta(days=1)


# ------------------------------------------------------------------ the readers
def stream_active():
    try:
        return bool((E1.games_status() or {}).get("active"))
    except Exception:       # noqa: BLE001
        return None


WIFI_KEYS = {"Supplicant state": "supplicant", "Wi-Fi standard": "standard", "RSSI": "rssi_dbm", "Link speed": "link_mbps",
             "Tx Link speed": "tx_mbps", "Rx Link speed": "rx_mbps", "Frequency": "freq_mhz"}


def onn_read():
    row = {}
    line = adb_shell("dumpsys wifi | grep -m1 '^mWifiInfo'")
    if "mWifiInfo" not in line:
        row["wifi"] = None
    else:
        for k, name in WIFI_KEYS.items():
            m = re.search(r"(?:^|, )" + re.escape(k) + r": ([^,]+)", line)
            v = m.group(1).strip() if m else None
            if v is not None and name != "supplicant":
                v = re.sub(r"(Mbps|MHz)$", "", v)
                try:
                    v = int(v)
                except ValueError:
                    pass
            row[name] = v
        f = row.get("freq_mhz")
        if isinstance(f, int):
            row["band"] = "5" if 4900 <= f < 5900 else "2.4" if 2400 <= f < 2500 else "6" if f >= 5925 else "?"
            row["channel"] = (f - 5000) // 5 if row["band"] == "5" else (f - 2407) // 5 if row["band"] == "2.4" else None
    socks = []
    for line in adb_shell("cat /proc/net/udp6").splitlines()[1:]:
        p = line.split()
        if len(p) >= 13 and ":" in p[1]:
            role = PORTS.get(p[1].rsplit(":", 1)[1].upper())
            if role:
                try:
                    socks.append({"port": role, "drops": int(p[-1])})
                except ValueError:
                    pass
    row["udp6_privyhub"] = socks or None
    up = adb_shell("cat /proc/uptime").split()
    row["uptime_s"] = float(up[0]) if up else None
    row["adb_ok"] = "rssi_dbm" in row or row["uptime_s"] is not None
    return row


class Night:
    def __init__(self, a, b, date):
        self.a, self.b, self.date = a, b, date
        NIGHTS.mkdir(parents=True, exist_ok=True)
        self.path = NIGHTS / f"{date}.jsonl"
        self.active = None
        self.onn_last = None
        self.anchor = (load_state().get("onn_anchor") or None)     # [epoch, connected_time_s]
        self.lock = threading.Lock()

    def emit(self, row):
        row.setdefault("stream_active", self.active)
        with self.lock, open(self.path, "a") as fh:
            fh.write(json.dumps(row) + "\n")

    # ---- ping, 1 s rows
    def ping(self, end):
        rx_reply = re.compile(r"^\[(\d+\.\d+)\].*icmp_seq=(\d+).*time=([\d.]+) ms")
        rx_seq = re.compile(r"^\[(\d+\.\d+)\].*icmp_seq=(\d+)")
        gen = 0
        while time.time() < end and not STOP.is_set():
            if not ADDR["v"]:
                refresh_addr()
            if not ADDR["v"]:
                self.emit({"kind": "event", "t": utc(), "event": "no_onn_address"})
                STOP.wait(30)
                continue
            n, gen, lost = max(1, int(end - time.time())), gen + 1, set()
            proc = subprocess.Popen(["ping", "-D", "-O", "-n", "-i", "1", "-W", "2", "-w", str(n + 3), ADDR["v"]],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            self.emit({"kind": "event", "t": utc(), "event": "ping_start",
                       "how": "ping -D -O -n -i 1 -W 2 <onn> (unprivileged; address in memory only)"})
            for line in proc.stdout:
                if STOP.is_set() or time.time() >= end + 3:
                    break
                m = rx_reply.match(line)
                if m:
                    t, sq, rtt = float(m.group(1)), int(m.group(2)), float(m.group(3))
                    if sq in lost:      # answered after ping's 1-s "no answer yet" (within -W 2): kept apart
                        self.emit({"kind": "ping_late", "t": utc(t - rtt / 1000), "gen": gen, "seq": sq, "rtt_ms": rtt})
                    else:
                        self.emit({"kind": "ping", "t": utc(t - rtt / 1000), "gen": gen, "seq": sq, "rtt_ms": rtt, "lost": False})
                    continue
                m = rx_seq.match(line)
                if m and "no answer yet" in line:
                    t, sq = float(m.group(1)), int(m.group(2))
                    lost.add(sq)
                    self.emit({"kind": "ping", "t": utc(t - 1.0), "gen": gen, "seq": sq, "rtt_ms": None, "lost": True})
                elif m:
                    self.emit({"kind": "ping", "t": utc(float(m.group(1))), "gen": gen, "seq": int(m.group(2)), "rtt_ms": None,
                               "lost": True, "error": True})
            if proc.poll() is None:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self.emit({"kind": "event", "t": utc(), "event": "ping_exit", "rc": proc.returncode})
            if time.time() < end - 5 and not STOP.is_set():
                STOP.wait(5)
                refresh_addr()

    # ---- onn + host + stream_active, every 30 s
    def every30(self, end):
        while time.time() < end and not STOP.is_set():
            t0 = time.time()
            self.active = stream_active()
            try:
                la = Path("/proc/loadavg").read_text().split()[:3]
            except OSError:
                la = None
            self.emit({"kind": "host", "t": utc(t0), "loadavg": [float(x) for x in la] if la else None})
            r = onn_read()
            r.update({"kind": "onn", "t": utc(t0)})
            self.onn_last = r
            self.emit(r)
            STOP.wait(max(0.0, 30 - (time.time() - t0)))

    # ---- the Opal, every 60 s
    def opal(self, end):
        raw = OUTD / f"opal_{self.date}.jsonl"
        proc = subprocess.Popen(["bash", str(OPAL_SH), str(raw), "60", "wlan1"], stdout=subprocess.DEVNULL,
                                stderr=open(OUTD / f"opal_{self.date}.log", "a"), cwd=str(OPAL_SH.parent))
        self.emit({"kind": "event", "t": utc(), "event": "opal_start", "how": "o1_opal_sample.sh wlan1 60 (read-only, redacted)"})
        seen = 0
        while True:
            done = time.time() >= end or STOP.is_set()
            if done:
                Path(str(raw) + ".stop").touch()
                try:
                    proc.wait(timeout=90)
                except subprocess.TimeoutExpired:
                    proc.terminate()
            try:
                lines = raw.read_text().splitlines()
            except OSError:
                lines = []
            for l in lines[seen:]:
                try:
                    r = json.loads(l)
                except ValueError:
                    continue
                self.mark_onn(r)
                r["kind"] = "opal"
                self.emit(r)
            seen = len(lines)
            if done:
                break
            STOP.wait(10)
        self.emit({"kind": "event", "t": utc(), "event": "opal_stop", "rc": proc.returncode})

    def mark_onn(self, r):
        """Mark the onn's station in a redacted round, without any identifier: connected-time continuity from the
        anchor; else the closest tx/rx rate and signal to the onn's own adb read; the method is recorded."""
        st = r.get("stations") or []
        t = datetime.strptime(r["at_utc"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()
        idx, how = None, None
        if self.anchor:
            want = self.anchor[1] + (t - self.anchor[0])
            c = [(abs((s.get("connected_time_s") or -1e9) - want), i) for i, s in enumerate(st)]
            c = [x for x in c if x[0] <= 120]
            if c:
                idx, how = min(c)[1], "connected_time_continuity"
        if idx is None and st and self.onn_last and isinstance(self.onn_last.get("rssi_dbm"), int):
            o = self.onn_last

            def score(s):
                return (abs((s.get("tx_bitrate_mbps") or 0) - (o.get("rx_mbps") or 0)) / 10
                        + abs((s.get("rx_bitrate_mbps") or 0) - (o.get("tx_mbps") or 0)) / 10
                        + abs((s.get("signal_dbm") or 0) - o["rssi_dbm"]))
            idx, how = min(range(len(st)), key=lambda i: score(st[i])), "link_rate_signal_match"
        r["onn_station_index"], r["onn_match"] = idx, how
        if idx is not None and st[idx].get("connected_time_s") is not None:
            self.anchor = [t, st[idx]["connected_time_s"]]
            s = load_state()
            s["onn_anchor"] = self.anchor
            save_state(s)

    def run(self):
        self.emit({"kind": "event", "t": utc(), "event": "night_start", "window_utc": [utc(self.a), utc(self.b)],
                   "window_local": f"{self.date} 00:30-01:30 America/New_York"})
        refresh_addr()
        th = [threading.Thread(target=f, args=(self.b,), daemon=True) for f in (self.ping, self.every30, self.opal)]
        for x in th:
            x.start()
        for x in th:
            x.join()
        self.emit({"kind": "event", "t": utc(), "event": "night_end", "stopped": STOP.is_set()})
        return summarize(self.path, self.date)


# ------------------------------------------------------------------ the summary
def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def summarize(path, date):
    rows = [json.loads(l) for l in open(path)]
    late = {(r["gen"], r["seq"]): r["rtt_ms"] for r in rows if r["kind"] == "ping_late"}
    pg = [dict(r, lost=False, rtt_ms=late[(r.get("gen"), r.get("seq"))]) if r["lost"] and (r.get("gen"), r.get("seq")) in late
          else r for r in rows if r["kind"] == "ping"]
    rtt = [r["rtt_ms"] for r in pg if r["rtt_ms"] is not None]
    run, best, best_at, cur_at = 0, 0, None, None
    for r in sorted(pg, key=lambda r: r["t"]):
        if r["lost"]:
            run, cur_at = run + 1, cur_at or r["t"]
            if run > best:
                best, best_at = run, cur_at
        else:
            run, cur_at = 0, None
    on = [r for r in rows if r["kind"] == "onn" and isinstance(r.get("rssi_dbm"), int)]
    txm = min(on, key=lambda r: r.get("tx_mbps") if isinstance(r.get("tx_mbps"), int) else 1e9, default=None)
    op = [r for r in rows if r["kind"] == "opal" and r.get("onn_station_index") is not None]
    st = [r["stations"][r["onn_station_index"]] for r in op]
    pk = [(s.get("tx_packets"), s.get("tx_retries")) for s in st if s.get("tx_packets") is not None and s.get("tx_retries") is not None]
    dp = pk[-1][0] - pk[0][0] if len(pk) >= 2 else None
    dr = pk[-1][1] - pk[0][1] if len(pk) >= 2 else None
    act = sorted(r["t"] for r in rows if r.get("stream_active"))
    s = {"night": date, "ping_sent": len(pg), "ping_loss_pct": round(100 * sum(r["lost"] for r in pg) / len(pg), 2) if pg else None,
         "rtt_p50": pct(rtt, 0.5), "rtt_p95": pct(rtt, 0.95), "rtt_max": max(rtt, default=None),
         "longest_lost_run_s": best, "longest_lost_run_at": best_at,
         "rssi_min": min((r["rssi_dbm"] for r in on), default=None),
         "rssi_median": statistics.median([r["rssi_dbm"] for r in on]) if on else None,
         "tx_min_mbps": txm.get("tx_mbps") if txm else None, "tx_min_at": txm["t"] if txm else None,
         "bands": sorted({r.get("band") for r in on if r.get("band")}),
         "opal_rounds": sum(1 for r in rows if r["kind"] == "opal"), "opal_onn_rounds": len(op),
         "opal_retry_rate": round(dr / dp, 4) if dp else None,
         "stream_active_span": [act[0], act[-1]] if act else None,
         "onn_reads": len([r for r in rows if r["kind"] == "onn"]), "onn_reads_ok": len(on)}
    new = not SUMMARY.exists()
    with open(SUMMARY, "a") as fh:
        if new:
            fh.write("# LINK-N1 — one row per night (00:30-01:30 America/New_York, no stream; written by link_n1_watch.py)\n\n"
                     "| night | ping sent | loss % | RTT p50 / p95 / max ms | longest lost run s (at) | RSSI min / median | "
                     "tx min Mbps (at) | bands | Opal rounds (onn) | Opal retry rate | stream_active span |\n"
                     "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
        fh.write(f"| {s['night']} | {s['ping_sent']} | {s['ping_loss_pct']} | {s['rtt_p50']} / {s['rtt_p95']} / {s['rtt_max']} | "
                 f"{s['longest_lost_run_s']} ({(s['longest_lost_run_at'] or '-')[11:19]}) | {s['rssi_min']} / {s['rssi_median']} | "
                 f"{s['tx_min_mbps']} ({(s['tx_min_at'] or '-')[11:19]}) | {','.join(s['bands']) or '-'} | "
                 f"{s['opal_rounds']} ({s['opal_onn_rounds']}) | {s['opal_retry_rate']} | "
                 f"{'-' if not s['stream_active_span'] else s['stream_active_span'][0][11:19] + '-' + s['stream_active_span'][1][11:19]} |\n")
    return s


def load_state():
    try:
        return json.loads(STATE_P.read_text())
    except (OSError, ValueError):
        return {}


def save_state(s):
    STATE_P.write_text(json.dumps(s, indent=1) + "\n")


def preregistered():
    want = PRE.with_suffix(".sha256").read_text().split()[0] if PRE.with_suffix(".sha256").exists() else None
    return hashlib.sha256(PRE.read_bytes()).hexdigest() == want


def main():
    OUTD.mkdir(parents=True, exist_ok=True)
    WATCH.mkdir(parents=True, exist_ok=True)
    if not preregistered():
        write_status(doing="REFUSED: the pre-registration does not match its hash; exited")
        return 2
    if DRY:
        write_status(doing="dry run: 2-min sample")
        refresh_addr()
        log("dry: address in memory", bool(ADDR["v"]))
        now = time.time()
        n = Night(now, now + 120, "dry_" + datetime.now(ET).date().isoformat())
        s = n.run()
        log("dry: done", json.dumps(s))
        write_status(doing="dry run done; exited", last=json.dumps(s)[:200])
        return 0
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=stop_watch, daemon=True).start()
    refresh_addr()
    log("start; onn address in memory:", bool(ADDR["v"]), "cap", CAP_UTC)
    try:
        while not stopped():
            a, b, date = windows_from(time.time())
            st = load_state()
            if date in st.get("nights_done", []):
                a, b, date = windows_from(b + 1)
            if a >= CAP:
                break
            tgt = f"{utc(a)} ({date} 00:30 America/New_York, UTC{datetime.fromtimestamp(a, ET).strftime('%z')})"
            write_status(doing=f"sleeping until {tgt}", next=f"night {date}: sample {utc(a)[11:16]}-{utc(b)[11:16]}Z")
            log("sleeping until", tgt)
            while time.time() < a and not stopped():
                STOP.wait(min(30, a - time.time()))
            if stopped():
                break
            write_status(doing=f"sampling night {date} until {utc(b)}")
            log("night", date, "sampling", utc(a), "->", utc(b))
            s = Night(a, b, date).run()
            st = load_state()
            st.setdefault("nights_done", []).append(date)
            save_state(st)
            log("night", date, "done", json.dumps(s))
            write_status(nights=len(st["nights_done"]), last=f"{date}: loss {s['ping_loss_pct']} % rtt p95 {s['rtt_p95']} "
                         f"rssi min {s['rssi_min']} tx min {s['tx_min_mbps']} retry {s['opal_retry_rate']}")
        why = "STOP file" if STOPFILE.exists() else f"cap {CAP_UTC}"
        write_status(doing=f"EXITED ({why})", next="-")
        log("exited:", why)
    except Exception as e:      # noqa: BLE001 -- written to the status line
        write_status(doing=f"CRASHED: {e!r}"[:300], next="-")
        log("CRASHED", repr(e))
        raise
    finally:
        STOP.set()
    return 0


if __name__ == "__main__":
    sys.exit(main())
