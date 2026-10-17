#!/usr/bin/env python3
"""G8-S1 -- the first adverse-network envelope, DETACHED, run as pre-registered (g8_s1_preregistration.txt). One
process from the hash to the end of the 22 cells or the cap (2026-10-17T06:00:00Z), launched as a systemd --user
transient unit (privyhub-g8-s1), not a Code-session child; resumable from g8_s1_state.json if restarted.

Built from E4-S4D's e4_s4d_watch.py scaffolding (kept: utc / log / jdump / append, the status line rewritten after
every run plus a 5-min heartbeat, history.csv, the STOP file, the busy skip, the cap, the suite call with its timeout
and SIGINT, the crash-to-status handler, --dry). Dropped: the ping trace, the Opal, the client's radio / thermal reads
and the deferral logic (not in G8-S1's task).

THE CELLS (22, in order): the eleven profiles none, loss-1, loss-5, burst-50x20, delay-50, delay-150, jitter-30,
reorder-5, cap-6000, cap-4500, delay-50+loss-1 -- each @post-fec,seed=1 -- each with PRIVYHUB_WAN_ADAPTATION absent
("off") then present ("on"). One E1-PS1-STREAM --e2 --window 600, idle gap 120 s, per cell, through
g8_s1_suite_call.py (tools/e1_suite.py's run_suite, unedited). The run's e3_flag.conf (the suite's per-run drop-in)
carries exactly PRIVYHUB_WAN_TELEMETRY=1, PRIVYHUB_IMPAIRMENT=<profile>@post-fec,seed=1, and PRIVYHUB_WAN_ADAPTATION=1
in the on arm; the suite writes it, restarts, checks the unit's environ, and removes it at teardown (flags_absent).

BESIDE EACH RUN (read-only): a thread that, 150 s into the window, reads the companion's environ (the flags under
load) and the shim's newest telemetry line; /diagnostics/stream-telemetry's `wan` every 30 s while the run lasts
(scrubbed of anything address-like) -> runs/<cell>/wan_poll_run<attempt>.jsonl; the shim's lines for the run (logs/impairment.jsonl
from the run's start offset) -> runs/<cell>/impairment_run<attempt>.jsonl, and the applied check against G8-P1's tolerances.

VALIDITY: the suite's own (PLAYING reached; a failing launch replaced at most twice -- E3-A3B's reading). A run
whose shim telemetry shows the profile not applied is `profile-not-applied` and its cell is run once more (run2).
BUSY: a game session active at a cell's start -> wait 10 min and retry, up to 3 times, then the cell is `busy`.
STOP: ~/privyhub_g8_s1/STOP ends the driver after the run in flight (never removed by the driver). THE CAP: no cell
starts at or after 2026-10-17T06:00:00Z.
--dry: about 2 min, no stream: the preflight and busy check, one cell's drop-in written (loss-1, on arm), the
companion restarted and its environ read back, 30 s held, the drop-in removed, restarted, flags_absent read; status
lines (30-s heartbeat) into dry_run/; then exit."""
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SUITE = REPO / "tools/e1_suite.py"
CALL = HERE / "g8_s1_suite_call.py"
PRE = HERE / "g8_s1_preregistration.txt"
WATCH = Path.home() / "privyhub_g8_s1"
RUNS = HERE / "runs"
CAP_UTC = "2026-10-17T14:00:00Z"
CAP = datetime(2026, 10, 17, 14, 0, 0, tzinfo=timezone.utc).timestamp()
DRY = "--dry" in sys.argv
STOPFILE = WATCH / "STOP"
OUTD = HERE / "dry_run" if DRY else WATCH
STATUS_P, HIST_P, WLOG_P = OUTD / "status.txt", OUTD / "history.csv", OUTD / "driver.log"
STATE_P = (HERE / "dry_run" if DRY else HERE) / "g8_s1_state.json"
CELLS_P = (HERE / "dry_run" if DRY else HERE) / "cells.jsonl"
IMP_LOG = REPO / "logs/impairment.jsonl"
HEARTBEAT = 30 if DRY else 300
WINDOW, GAP = 600, 120
BUSY_WAIT, BUSY_TRIES = 600, 3
SUITE_TIMEOUT = 2 * 3600
PROFILES = ["none", "loss-1", "loss-5", "burst-50x20", "delay-50", "delay-150", "jitter-30", "reorder-5",
            "cap-6000", "cap-4500", "delay-50+loss-1"]
CAPS = {"cap-6000": 6000, "cap-4500": 4500}
CELLS = [{"n": 2 * i + j + 1, "profile": p, "arm": arm, "cell": f"{2 * i + j + 1:02d}_{p}_{arm}"}
         for i, p in enumerate(PROFILES) for j, arm in enumerate(("off", "on"))]
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F]{32,}\b")

spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)
# E4-S5D's segment-aware capture fps and dup+drop (the host gates' reading, as CL-B2 / CL-B3 used it)
spec = importlib.util.spec_from_file_location("s5d", HERE.parent / "e4_s5d_2026-10-15/e4_s5d_analysis.py")
S5D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S5D)
STOP = threading.Event()


def kvs(cell):
    out = ["PRIVYHUB_WAN_TELEMETRY=1", f"PRIVYHUB_IMPAIRMENT={cell['profile']}@post-fec,seed=1"]
    return out + (["PRIVYHUB_WAN_ADAPTATION=1"] if cell["arm"] == "on" else [])


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log(*a):
    line = f"[g8s1 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    WLOG_P.parent.mkdir(parents=True, exist_ok=True)
    with open(WLOG_P, "a") as fh:
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


# ---------------------------------------------------------------- the status line, the history, the stop file
STATUS = {"cell": "-", "last": "-", "last_at": "-", "doing": "starting", "next": "-", "state": "-"}
STATUS_LOCK = threading.Lock()
HIST_COLS = ["n", "cell", "profile", "arm", "start_utc", "busy_tries", "attempt", "status", "validity", "profile_applied",
             "flags_under_load", "loss_per_min", "rendered_fps", "resyncs", "stale_per_min", "spikes20_per_min",
             "client_pauses", "wan_class", "wan_windows", "rung_min", "rung_max", "rules_suggestions", "retroarch_fps",
             "capture_fps", "dupdrop_per_min", "host_cpu", "companion_cpu", "shim_cpu_pct_core",
             "shim_packets_in", "shim_dropped", "shim_delayed", "shim_reordered", "shim_queue_max", "preflight_ok",
             "flags_absent_after", "final_flags_absent"]


def write_status(**kw):
    """One line, rewritten (atomic replace of the driver's own status file) after every run, and every HEARTBEAT s by
    the heartbeat thread: a reader can tell idle from dead by the heartbeat's age."""
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | cell {s['cell']}/22 | last: {s['last']} (at {s['last_at']}) | doing: {s['doing']} | "
                f"next: {s['next']} | state: {s['state']} | cap {CAP_UTC} | stop: touch ~/privyhub_g8_s1/STOP\n")
        STATUS_P.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATUS_P.with_suffix(".tmp")
        tmp.write_text(line)
        os.replace(tmp, STATUS_P)


def heartbeat_thread():
    while not STOP.wait(HEARTBEAT):
        write_status()


def hist_append(row):
    new = not HIST_P.exists()
    with open(HIST_P, "a") as fh:
        if new:
            fh.write(",".join(HIST_COLS) + "\n")
        fh.write(",".join("" if (v := row.get(c)) is None else str(v).replace(",", ";") for c in HIST_COLS) + "\n")


def stop_requested():
    return STOPFILE.exists()


def adopted_state():
    """The seven-line adopted state (G-A1), read back: the suite's own preflight."""
    try:
        p = E1.preflight()
    except Exception as e:      # noqa: BLE001 -- a read failure is reported, not fatal
        return {"ok": False, "error": repr(e)[:200]}, "read failed"
    return p, ("adopted7 ok" if p.get("ok") else f"NOT ok (environ {len(p.get('environ') or [])} lines, game {p.get('game_active')})")


# ---------------------------------------------------------------- the readings beside a run
def scrub(o):
    s = json.dumps(o, default=str)
    return (json.loads(IP.sub("<redacted>", s)), len(IP.findall(s))) if IP.search(s) else (o, 0)


def imp_lines():
    try:
        with open(IMP_LOG) as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def imp_read(start):
    rows = []
    try:
        with open(IMP_LOG) as fh:
            for i, l in enumerate(fh):
                if i >= start:
                    try:
                        rows.append(json.loads(l))
                    except ValueError:
                        pass
    except OSError:
        pass
    return rows


def beside_run(cell, cdir, imp_start, out, attempt):
    """150 s into the window: the flags under load (the companion's environ) and the shim live; every 30 s while the
    run lasts: /diagnostics/stream-telemetry's `wan` (scrubbed) -> wan_poll_run<attempt>.jsonl."""
    sl = cdir / "suite.log"
    seen = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
    t_window, t0 = None, time.time()
    while not out.get("done") and not STOP.is_set():
        now = time.time()
        cur = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
        if t_window is None and cur > seen:
            t_window = now
        if t_window is not None and now - t_window >= 150 and "flags_under_load" not in out:
            env = E1.environ_flags(E1.mainpid())
            want = kvs(cell)
            lines = imp_read(imp_start)
            out["flags_under_load"] = all(kv in env for kv in want) and all(kv in env for kv in E1.ADOPTED) and \
                len(env) == len(E1.ADOPTED) + len(want)
            out["environ_under_load_count"] = len(env)
            out["shim_live_under_load"] = bool(lines) and lines[-1].get("profile") == cell["profile"]
        if now - t0 >= 30 or "first" not in out:
            out["first"] = True
            t0 = now
            st = E1.http("GET", "/diagnostics/stream-telemetry", 10)[1] or {}
            w, n = scrub(st.get("wan") if isinstance(st, dict) else None)
            append(cdir / f"wan_poll_run{attempt}.jsonl", {"at_utc": utc(), "game_active": (E1.games_status() or {}).get("active"),
                                             "has_wan": isinstance(st, dict) and "wan" in st, "wan": w, "redacted_matches": n})
        time.sleep(5)


def applied(profile, rows):
    """G8-P1's tolerances, read on the run's shim telemetry (per-second deltas; see the pre-registration)."""
    rows = [r for r in rows if r.get("profile") == profile and r.get("placement") == "post-fec" and r.get("seed") == 1]
    if not rows:
        return False, {"lines": 0}
    s = lambda key: sum(r.get(key) or 0 for r in rows)
    pin, pout = s("packets_in"), s("packets_out")
    dl, db, dq, de, ro = s("dropped_loss"), s("dropped_burst"), s("dropped_queue"), s("delayed"), s("reordered")
    dur = max(r.get("t_s") or 0 for r in rows)
    m = {"lines": len(rows), "duration_s": round(dur, 1), "packets_in": pin, "packets_out": pout, "dropped_loss": dl,
         "dropped_burst": db, "dropped_queue": dq, "delayed": de, "reordered": ro, "queue_max": max(r.get("queue_max") or 0 for r in rows),
         "shim_cpu_pct_core": round(100 * s("cpu_s") / dur, 3) if dur else None, "send_errors": s("send_errors")}
    if pin <= 0:
        return False, m
    loss = dl / pin
    if profile == "none":
        ok = dl == db == dq == ro == 0 and de == 0
    elif profile in ("loss-1", "loss-5"):
        lo, hi = (0.007, 0.013) if profile == "loss-1" else (0.045, 0.055)
        ok = lo <= loss <= hi and db == dq == ro == 0
    elif profile == "burst-50x20":
        expect = int((dur - 10) // 20) + 1 if dur >= 10 else 0
        ok = db % 50 == 0 and abs(db // 50 - expect) <= 1 and dl == dq == ro == 0
        m["bursts"], m["bursts_expected"] = db // 50, expect
    elif profile in ("delay-50", "delay-150"):
        ok = de >= 0.95 * pin and dl == db == dq == ro == 0
    elif profile == "jitter-30":
        ok = de >= 0.9 * pin and ro == 0 and dl == db == dq == 0
    elif profile == "reorder-5":
        ok = 0.04 <= ro / pin <= 0.06 and dl == db == dq == 0
    elif profile in CAPS:
        cap = CAPS[profile]
        over = [r for r in rows if (r.get("bytes_in") or 0) * 8 / 1000 > cap * 1.05]
        ok = all((r.get("bytes_out") or 0) * 8 / 1000 <= cap * 1.05 for r in rows) and dl == db == ro == 0
        m["seconds_input_over_cap"] = len(over)
        m["out_kbps_max"] = round(max((r.get("bytes_out") or 0) * 8 / 1000 for r in rows), 1)
    elif profile == "delay-50+loss-1":
        ok = 0.007 <= loss <= 0.013 and de >= 0.95 * (pin - dl) and db == dq == ro == 0
    else:
        ok = False
    m["loss_frac"] = round(loss, 5)
    return bool(ok), m


# ---------------------------------------------------------------- running the suite
def suite(out, cell, timeout_s):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "suite_console.log", "a") as fh:
        p = subprocess.Popen([sys.executable, str(CALL), str(out), str(WINDOW), str(GAP), *kvs(cell)], stdout=fh,
                             stderr=subprocess.STDOUT, cwd=str(REPO))
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


def figures(s, rd):
    rf = k(s, "teardown", "report_fields") or {}
    mins = (rf.get("duration_ms") or 0) / 60000
    hh = lambda key: k(s, "host", "host", key, "mean")
    rungs, sugg = [], 0
    if rd:
        try:
            for l in open(rd / "status_poll.jsonl"):
                try:
                    r = json.loads(l)
                except ValueError:
                    continue
                if isinstance(r.get("bitrate_kbps"), (int, float)):
                    rungs.append(int(r["bitrate_kbps"]))
        except OSError:
            pass
        try:
            for l in open(rd / "decisions.jsonl"):
                if '"wan_rules"' in l:
                    sugg += 1
        except OSError:
            pass
    return {"status": (s or {}).get("status"), "window": (s or {}).get("window"),
            "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"),
            "stale_per_min": round(rf["decoder.stale_output_drops"] / mins, 3) if mins and "decoder.stale_output_drops" in rf else None,
            "spikes20_per_min": round(rf["decoder.spike_20_ms"] / mins, 2) if mins and "decoder.spike_20_ms" in rf else None,
            "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []),
            "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": hh("cpu.mean_pct"),
            "companion_cpu": hh("procs.companion.cpu_pct"),
            "rung_min": min(rungs) if rungs else None, "rung_max": max(rungs) if rungs else None,
            "rules_suggestions": sugg,
            "preflight_ok": k(s, "preflight", "ok"), "flags_absent_after": k(s, "teardown", "flags_absent"),
            "apk": k(s, "teardown", "apk"), **capture(s, rd)}


def capture(s, rd):
    try:
        cap, dd = S5D.segcap(rd, s) if s and rd else (None, None)
    except Exception as e:      # noqa: BLE001 -- reported, not fatal
        return {"capture_fps": None, "dupdrop_per_min": None, "capture_error": repr(e)[:120]}
    return {"capture_fps": cap, "dupdrop_per_min": dd}


def wan_last(cdir, attempt):
    last = None
    try:
        for l in open(cdir / f"wan_poll_run{attempt}.jsonl"):
            r = json.loads(l)
            if isinstance(r.get("wan"), dict):
                last = r["wan"]
    except (OSError, ValueError):
        pass
    return (last or {}).get("class"), (last or {}).get("window_primary_counts")


def run_cell(cell, attempt, busy_tries):
    cdir = RUNS / cell["cell"]
    wdir = cdir / "E1-PS1-STREAM_flag"
    before = latest_run(wdir)
    imp_start = imp_lines()
    t = time.time()
    write_status(cell=cell["n"], doing=f"cell {cell['n']}/22 {cell['profile']} {cell['arm']} (attempt {attempt}, started {utc(t)[11:16]}Z)",
                 next="-")
    beside = {}
    th = threading.Thread(target=beside_run, args=(cell, cdir, imp_start, beside, attempt), daemon=True)
    cdir.mkdir(parents=True, exist_ok=True)
    th.start()
    suite(cdir, cell, SUITE_TIMEOUT)
    beside["done"] = True
    th.join(timeout=30)
    rd = latest_run(wdir)
    s = load_summary(rd) if rd and rd != before else None
    f = figures(s, rd)
    rows = imp_read(imp_start)
    with open(cdir / f"impairment_run{attempt}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    ok, m = applied(cell["profile"], rows)
    final = {}
    try:
        final = json.loads((cdir / "final_state.json").read_text())
    except (OSError, ValueError):
        pass
    validity = "valid" if f["status"] == "OK" and ok else ("profile-not-applied" if f["status"] == "OK" else f"no_play ({f['status']})")
    wc, ww = wan_last(cdir, attempt)
    row = {**cell, "start_utc": utc(t), "busy_tries": busy_tries, "attempt": attempt, "validity": validity,
           "profile_applied": ok, "shim": m, "flags_under_load": beside.get("flags_under_load"),
           "environ_under_load_count": beside.get("environ_under_load_count"),
           "shim_live_under_load": beside.get("shim_live_under_load"),
           "run_dir": str(rd.relative_to(HERE)) if rd else None, **{x: v for x, v in f.items()},
           "wan_class": wc, "wan_windows": ww, "final_flags_absent": final.get("flags_absent"),
           "final_preflight_like": {x: final.get(x) for x in ("game_active", "apk", "e3_dropin_absent", "e4_constraint_absent")},
           "shim_cpu_pct_core": m.get("shim_cpu_pct_core"), "shim_packets_in": m.get("packets_in"),
           "shim_dropped": (m.get("dropped_loss") or 0) + (m.get("dropped_burst") or 0) + (m.get("dropped_queue") or 0),
           "shim_delayed": m.get("delayed"), "shim_reordered": m.get("reordered"), "shim_queue_max": m.get("queue_max")}
    append(CELLS_P, row)
    hist_append({**row, "wan_windows": json.dumps(ww) if ww else None})
    log(f"cell {cell['n']} {cell['profile']} {cell['arm']} attempt {attempt}: {f['status']} {validity} loss {f['loss_per_min']} "
        f"rendered {f['rendered_fps']} class {wc} rungs {f['rung_min']}-{f['rung_max']} rules {f['rules_suggestions']} "
        f"flags_under_load {beside.get('flags_under_load')} flags_absent {f['flags_absent_after']}/{final.get('flags_absent')}")
    if f["status"] == "OK" and not (f["flags_absent_after"] and final.get("flags_absent") and f["preflight_ok"]):
        log(f"cell {cell['n']}: STATE VIOLATION -- flags_absent / preflight not all true")
    return row


def dry():
    """--dry: about 2 min, no stream (see the module docstring)."""
    (HERE / "dry_run").mkdir(exist_ok=True)
    p, sline = adopted_state()
    log("dry: start; preflight", json.dumps(p), "| busy", bool(p.get("game_active")), "| stop file present", stop_requested())
    cell = CELLS[3]                  # 04_loss-1_on: the longest drop-in (three lines)
    write_status(cell=cell["n"], doing="dry run (no stream): the drop-in written", state=sline,
                 next=f"exit at {utc(time.time() + 120)[11:16]}Z")
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    rec = {"cell": cell["cell"], "kvs": kvs(cell)}
    E1.DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in kvs(cell)))
    E1.sh(["systemctl", "--user", "daemon-reload"], 60)
    rec["restart"] = E1.restart_unit()
    rec["environ_has_all"] = all(kv in rec["restart"]["environ"] for kv in kvs(cell)) and \
        len(rec["restart"]["environ"]) == len(E1.ADOPTED) + len(kvs(cell))
    log("dry: drop-in written, restarted; environ lines", len(rec["restart"]["environ"]), "all flags present", rec["environ_has_all"])
    t0 = time.time()
    while time.time() - t0 < 30 and not stop_requested():
        time.sleep(5)
    td = {}
    E1.teardown_flags({"dropin": kvs(cell)}, td)
    rec["teardown"] = td
    rec["preflight_after"], sline = adopted_state()
    jdump(HERE / "dry_run" / "dry_record.json", rec)
    log("dry: drop-in removed, restarted; flags_absent", td.get("flags_absent"), "| state", sline)
    write_status(doing="dry: flags written and removed", state=sline,
                 last=f"dry: environ {len(rec['restart']['environ'])} lines with the flags; flags_absent {td.get('flags_absent')}",
                 last_at=utc())
    while time.time() - t0 < 90 and not stop_requested():
        time.sleep(5)
    STOP.set()
    write_status(doing="dry run done; exited", next="-")
    log("dry: done; exit")
    return 0 if rec["environ_has_all"] and td.get("flags_absent") else 1


def main():
    if DRY:
        return dry()
    WATCH.mkdir(parents=True, exist_ok=True)
    st = json.loads(STATE_P.read_text()) if STATE_P.exists() else {"done": {}, "started_utc": utc()}
    p, sline = adopted_state()
    st.setdefault("preflight_at_start", []).append({"at_utc": utc(), **p})
    jdump(STATE_P, st)
    log("start; cells done", len(st["done"]), "| adopted state", sline, "| cap", CAP_UTC)
    write_status(cell=len(st["done"]), state=sline, doing="starting")
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    why = "all 22 cells done"
    for i, cell in enumerate(CELLS):
        if cell["cell"] in st["done"]:
            continue
        if stop_requested():
            why = "the stop file"
            log("the stop file: exiting")
            break
        if time.time() >= CAP:
            why = "the cap"
            log("the cap: no cell starts after it")
            break
        tries = 0
        while bool((E1.games_status() or {}).get("active")) and tries < BUSY_TRIES and not stop_requested():
            tries += 1
            log(f"cell {cell['n']}: busy (a game session is active) -- waiting 10 min (try {tries}/{BUSY_TRIES})")
            write_status(cell=cell["n"], doing=f"busy: waiting 10 min (try {tries}/{BUSY_TRIES})",
                         next=f"cell {cell['n']} at {utc(time.time() + BUSY_WAIT)[11:16]}Z")
            t_busy = time.time()
            while time.time() - t_busy < BUSY_WAIT and not stop_requested():
                time.sleep(15)
        if stop_requested():
            why = "the stop file"
            break
        if bool((E1.games_status() or {}).get("active")):
            row = {**cell, "start_utc": utc(), "busy_tries": tries, "validity": "busy"}
            append(CELLS_P, row)
            hist_append(row)
            st["done"][cell["cell"]] = "busy"
            jdump(STATE_P, st)
            log(f"cell {cell['n']}: busy after {tries} waits -- marked busy, next")
            write_status(last=f"cell {cell['n']} busy", last_at=utc(), doing="idle")
            continue
        row = run_cell(cell, 1, tries)
        if row["validity"] == "profile-not-applied" and time.time() < CAP and not stop_requested():
            log(f"cell {cell['n']}: profile-not-applied -- repeated once")
            row = run_cell(cell, 2, tries)
        st["done"][cell["cell"]] = row["validity"]
        jdump(STATE_P, st)
        _, sline = adopted_state()
        nxt = next((c for c in CELLS[i + 1:] if c["cell"] not in st["done"]), None)
        write_status(cell=cell["n"], last=(f"cell {cell['n']} {cell['profile']} {cell['arm']}: {row.get('status')} {row['validity']} "
                                           f"loss/min {row.get('loss_per_min')} rendered {row.get('rendered_fps')} class {row.get('wan_class')}"),
                     last_at=utc(), state=sline, doing="idle",
                     next=(f"cell {nxt['n']} {nxt['profile']} {nxt['arm']} now (~{utc(time.time() + 60)[11:16]}Z)" if nxt else "-"))
    STOP.set()
    st["closed_utc"], st["closed_by"] = utc(), why
    jdump(STATE_P, st)
    write_status(doing=f"EXITED ({why})", next="-")
    log("driver closed (" + why + ")")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # a crash is written to the status line, so a reader sees it, then re-raised
        STOP.set()
        write_status(doing=f"CRASHED: {repr(e)[:160]}", next="-")
        raise
