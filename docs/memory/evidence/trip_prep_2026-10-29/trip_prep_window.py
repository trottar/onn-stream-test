#!/usr/bin/env python3
"""TRIP-PREP: G-A9's confirmation window (G-A7's g_a7_window.py, itself G-A5's, G-A4's, for THIRTEEN lines; the flag
PRIVYHUB_REMOTE=1; the APK fcd924c2..., the loss guard out). Added here: the running encoder's argv every 2 s for the
first pid's -b:v / -maxrate (nothing else of it is kept), /status every 30 s for `wan` (presence only), and
logs/wan_sessions.jsonl's line count before and after. Runs one E1-SNES-STREAM through the suite's
own CLI (run --only E1-SNES-STREAM --runs 1 --window 600 --gap 120 --e2 --prereg <this dir's>), reads the environ back
every 15 s (the thirteen adopted lines expected throughout), the onn's band every 30 s (trip_prep_state.py's parse: frequency /
band / standard / RSSI / tx / rx only) and tools/e3_state.py once mid-window (link_recovery.stack), and copies the run's
five logs over its span (BENCH-R3's driver's logs_copy, addresses masked). No setprop. The reading is trip_prep_read.py's.
    python3 -B g_a7_window.py
"""
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location("bench_r3_driver", EV / "bench_r3_2026-10-22/bench_r3_driver.py")
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)          # module level only defines (main() runs under __main__ alone)
E1 = D.E1


class _Band:
    import re as _re
    WIFI = {"Wi-Fi standard": "standard", "RSSI": "rssi_dbm", "Tx Link speed": "tx_mbps", "Rx Link speed": "rx_mbps",
            "Frequency": "freq_mhz"}

    def band_read(self):
        try:
            line = subprocess.run(["adb", "shell", "dumpsys wifi | grep -m1 '^mWifiInfo'"], capture_output=True,
                                  text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError):
            line = ""
        b = {}
        for k, n in self.WIFI.items():
            m = self._re.search(r"(?:^|, )" + self._re.escape(k) + r": (-?\d+)", line)
            b[n] = int(m.group(1)) if m else None
        f = b.get("freq_mhz")
        b["band"] = None if f is None else "5" if 4900 <= f < 5900 else "2.4" if 2400 <= f < 2500 else "6" if f >= 5925 else "?"
        return b


SB = _Band()
FLAG = "PRIVYHUB_REMOTE=1"
WAN_SESSIONS = REPO / "logs/wan_sessions.jsonl"
OUT = HERE / "runs"
STOP = threading.Event()
ENV = {"reads": 0, "max_lines": 0, "thirteen_with_flag": 0, "lines_at_thirteen": None}
ENC = {"first": None, "seen": []}
WAN = {"polls": 0, "in_game": 0, "status_has_wan": 0}


def log(*a):
    line = f"{D.utc()} " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(HERE / "window_console.txt", "a") as fh:
        fh.write(line + "\n")


def environ_watch():
    while not STOP.is_set():
        try:
            env = E1.environ_flags(E1.mainpid()) or []
        except Exception:       # noqa: BLE001 -- a read failure is a missed read, not fatal
            env = []
        ENV["reads"] += 1
        ENV["max_lines"] = max(ENV["max_lines"], len(env))
        if len(env) == 13 and FLAG in env and sorted(env) == E1.ADOPTED:
            ENV["thirteen_with_flag"] += 1
            ENV["lines_at_thirteen"] = ENV["lines_at_thirteen"] or sorted(env)
        STOP.wait(15)


def state_read():
    try:
        return json.loads(subprocess.run([sys.executable, "-B", str(HERE / "trip_prep_state.py")], capture_output=True, text=True,
                                         timeout=180).stdout or "{}")
    except (ValueError, subprocess.SubprocessError):
        return {}


def band_watch(t0):
    mid = False
    while not STOP.is_set():
        s = state_read() if (not mid and time.time() - t0 > 420) else None
        if s:
            mid = True
            (HERE / "state_midwindow.json").write_text(json.dumps(s) + "\n")
            b = dict(s.get("band") or {}, at_utc=s.get("at_utc"))
        else:
            b = dict(SB.band_read() if SB else {}, at_utc=D.utc())
        with open(HERE / "band.jsonl", "a") as fh:
            fh.write(json.dumps(b) + "\n")
        STOP.wait(30)


def wan_lines():
    try:
        with open(WAN_SESSIONS) as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def encoder_watch():
    """Only -b:v / -maxrate of each new encoder pid (in order of appearance)."""
    seen = set()
    while not STOP.is_set():
        for pid in E1.encoder_pids():
            if pid in seen:
                continue
            try:
                argv = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace").split("\0")
            except OSError:
                continue
            seen.add(pid)
            val = lambda o: argv[argv.index(o) + 1] if o in argv and argv.index(o) + 1 < len(argv) else None
            row = {"at_utc": D.utc(), "pid_n": len(seen), "b_v": val("-b:v"), "maxrate": val("-maxrate")}
            ENC["first"] = ENC["first"] or row
            ENC["seen"].append(row)
        STOP.wait(2)


def wan_watch():
    while not STOP.is_set():
        try:
            st = E1.http("GET", "/status", 10)[1] or {}
            game = bool((E1.games_status() or {}).get("active"))
        except Exception:       # noqa: BLE001 -- a missed poll
            st, game = {}, False
        WAN["polls"] += 1
        WAN["in_game"] += 1 if game else 0
        WAN["status_has_wan"] += 1 if isinstance(st, dict) and "wan" in st else 0
        STOP.wait(30)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pf = E1.preflight()
    log("preflight ok", pf.get("ok"), "environ", len(pf.get("environ") or []), "game", pf.get("game_active"))
    if not pf.get("ok"):
        log("refusing: the preflight is not ok")
        return 2
    t0 = time.time()
    wan0 = wan_lines()
    threading.Thread(target=encoder_watch, daemon=True).start()
    threading.Thread(target=wan_watch, daemon=True).start()
    th = threading.Thread(target=environ_watch, daemon=True)
    th.start()
    threading.Thread(target=band_watch, args=(t0,), daemon=True).start()
    with open(OUT / "suite_console.log", "a") as fh:
        rc = subprocess.run([sys.executable, str(REPO / "tools/e1_suite.py"), "run", "--out", str(OUT), "--prereg",
                             str(HERE / "trip_prep_preregistration.txt"), "--only", "E1-SNES-STREAM", "--runs", "1", "--window",
                             "600", "--gap", "120", "--e2"], stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO)).returncode
    t1 = time.time()
    STOP.set()
    log("the suite exited", rc)
    rd = D.latest_run(OUT / "E1-SNES-STREAM")
    s = D.load_json(rd / "summary.json") if rd else None
    f = D.figures(s, rd) if s else {}
    copied = D.logs_copy(t0, t1, OUT / "logs_run1")
    final = D.load_json(OUT / "final_state.json") or {}
    rec = {"t0": D.utc(t0), "t1": D.utc(t1), "suite_rc": rc, "run_dir": rd.name if rd else None, "environ_watch": ENV,
           "encoder": ENC, "wan_polls": WAN, "wan_sessions_lines": [wan0, wan_lines()],
           "logs_copied": copied, "final_flags_absent": final.get("flags_absent"), "final_environ_lines": len(final.get("environ") or []),
           "figures": {k: v for k, v in f.items() if k not in ("report_fields", "pauses")},
           "post_check": json.loads(subprocess.run(
               [sys.executable, str(REPO / "tools/e3_state.py")], capture_output=True, text=True).stdout or "{}")}
    (HERE / "window_result.json").write_text(json.dumps(rec, indent=1) + "\n")
    log("done:", json.dumps({k: rec[k] for k in ("suite_rc", "run_dir", "environ_watch", "final_flags_absent", "final_environ_lines",
                                                 "encoder", "wan_polls", "wan_sessions_lines")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
