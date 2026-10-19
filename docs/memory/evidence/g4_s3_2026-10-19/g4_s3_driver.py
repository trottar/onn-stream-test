#!/usr/bin/env python3
"""G4-S3 -- off-site at 4000 with Opus (adopted): ONE PS1-STREAM `--remote` run, DETACHED, run as pre-registered
(g4_s3_preregistration.txt), until the run ends or the cap (2026-10-19T16:55:00Z, launch + 3 h), as the systemd --user transient
unit privyhub-g4-s3. Built from G4-S2's driver (g4_s2_2026-10-17/g4_s2_driver.py); changed:
- one run (G4-S2 run 1's capped arm): PRIVYHUB_REMOTE_LADDER=1, PRIVYHUB_START_RUNG=floor, PRIVYHUB_REMOTE_RUNG_CAP=4000,
  PRIVYHUB_WAN_TELEMETRY=1 -- no codec line: Opus comes from the adopted drop-in; the environ reads back the adopted
  lines (len(E1.ADOPTED), eight) plus these four = twelve, else the run is not started;
- `--gap 0` (the user's cue "start Tekken 3 within 15 min" starts the wait at once; --window 600 --wait 900 --runs 1,
  E2's 90-s warm-up, no --adb);
- the counts read from E1.ADOPTED, not a literal;
- a LAN-class run is void and NOT replaced automatically (the user's call);
- the rest unchanged: the drop-in written / read back / removed, flags_absent read, the tailnet tx rate every 10 s,
  the wan poll, the ladder log and the journal after the run, STOP (~/privyhub_g4_s3/STOP), the busy wait, the cap."""
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
JREAD = HERE.parent / "g8_s1_2026-10-16/g8_s1_cap_log_read.py"
PRE = HERE / "g4_s3_preregistration.txt"
WATCH = Path.home() / "privyhub_g4_s3"
RUNS = HERE / "runs"
CAP_UTC = "2026-10-19T16:55:00Z"
CAP = datetime.strptime(CAP_UTC, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
STOPFILE = WATCH / "STOP"
STATUS_P, HIST_P, WLOG_P = WATCH / "status.txt", WATCH / "history.csv", WATCH / "driver.log"
ROWS_P = HERE / "runs.jsonl"
STATE_P = HERE / "g4_s3_state.json"
LADDER_LOG = REPO / "logs/games/adaptive_bitrate_shadow.jsonl"
LADDER_ARCH = LADDER_LOG.parent / "archive" / (LADDER_LOG.name + ".1")
HEARTBEAT = 300
WINDOW, GAP, WAIT = 600, 0, 900
BUSY_WAIT, BUSY_TRIES = 600, 3
SUITE_TIMEOUT = 3600
NRUNS = 1
BASE = ["PRIVYHUB_REMOTE_LADDER=1", "PRIVYHUB_START_RUNG=floor"]
RUNSPEC = [{"n": 1, "arm": "capped", "kvs": BASE + ["PRIVYHUB_REMOTE_RUNG_CAP=4000", "PRIVYHUB_WAN_TELEMETRY=1"]}]
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F]{32,}\b")

spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)
STOP = threading.Event()


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log(*a):
    line = f"[g4s2 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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


def scrub(o):
    s = json.dumps(o, default=str)
    return (json.loads(IP.sub("<redacted>", s)), len(IP.findall(s))) if IP.search(s) else (o, 0)


# ---------------------------------------------------------------- the status line, the history, the stop file
STATUS = {"run": "-", "last": "-", "last_at": "-", "doing": "starting", "next": "-", "state": "-"}
STATUS_LOCK = threading.Lock()
HIST_COLS = ["n", "arm", "attempt", "start_utc", "end_utc", "busy_tries", "environ_lines", "environ_ok", "status",
             "validity", "endpoint_class", "endpoint_hash", "playing_utc", "start_rung_kbps", "start_rung_source",
             "start_rung_path_class", "rung_path", "transitions", "clamps", "rules_by_id", "wire_bitrate_kbps_seen",
             "encoder_bv_seen", "tx_kbps_window_median", "tx_kbps_by_rung", "window_mb", "loss_per_min",
             "rendered_fps", "resyncs", "fec_recovered", "fec_unrecoverable", "path_counts", "path_changes",
             "wan_class", "retroarch_fps", "capture_fps", "dupdrop_per_min", "host_gates_met", "flags_absent_after"]


def write_status(**kw):
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | run {s['run']}/{NRUNS} | last: {s['last']} (at {s['last_at']}) | doing: {s['doing']} | "
                f"next: {s['next']} | state: {s['state']} | cap {CAP_UTC} | stop: touch ~/privyhub_g4_s3/STOP\n")
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
        fh.write(",".join("" if (v := row.get(c)) is None else
                          (json.dumps(v, separators=(";", ":")) if isinstance(v, (dict, list)) else str(v)).replace(",", ";")
                          for c in HIST_COLS) + "\n")


def stop_requested():
    return STOPFILE.exists()


def host_state():
    """The host side of the adopted state (len(E1.ADOPTED) lines), as e3_state's preflight reads it (adb off-LAN)."""
    mp = E1.mainpid()
    env, man = E1.environ_flags(mp), E1.manager_flags()
    game = bool((E1.games_status() or {}).get("active"))
    ok = env == E1.ADOPTED and man == [] and not E1.DROPIN.exists() and not game
    return {"environ_lines": len(env), "adopted": env == E1.ADOPTED, "adopted_lines": len(E1.ADOPTED), "manager": len(man),
            "e3_dropin_absent": not E1.DROPIN.exists(), "game_active": game, "ok": ok}, \
        (f"adopted{len(E1.ADOPTED)} ok" if ok else f"NOT ok (environ {len(env)} lines, game {game})")


# ---------------------------------------------------------------- the readings beside a run
def tailnet_tx():
    """The tailnet interface's tx byte counter (the interface named by its provider; the name is not written)."""
    for p in sorted(Path("/sys/class/net").iterdir()):
        if p.name.startswith("tailscale"):
            try:
                return int((p / "statistics/tx_bytes").read_text())
            except (OSError, ValueError):
                return None
    return None


def ladder_offset():
    try:
        return LADDER_LOG.stat().st_size
    except OSError:
        return 0


def ladder_read(off):
    chunks = []
    try:
        size = LADDER_LOG.stat().st_size
    except OSError:
        size = 0
    try:
        if size < off:
            with open(LADDER_ARCH, "rb") as fh:
                fh.seek(off)
                chunks.append(fh.read())
            off = 0
        with open(LADDER_LOG, "rb") as fh:
            fh.seek(off)
            chunks.append(fh.read())
    except OSError:
        pass
    rows = []
    for l in b"".join(chunks).decode(errors="replace").splitlines():
        try:
            rows.append(json.loads(l))
        except ValueError:
            pass
    return rows, size < off


def encoder_rate():
    for p in E1.encoder_pids():
        try:
            argv = open(f"/proc/{p}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            continue
        val = lambda opt: argv[argv.index(opt) + 1] if opt in argv and argv.index(opt) + 1 < len(argv) else None
        return {"b_v": val("-b:v"), "maxrate": val("-maxrate")}
    return None


def flags_check(kvs):
    env = E1.environ_flags(E1.mainpid())
    return (all(kv in env for kv in kvs) and all(kv in env for kv in E1.ADOPTED) and len(env) == len(E1.ADOPTED) + len(kvs),
            len(env))


def beside_run(spec_, rdir, out):
    t_enc, t_wan, t_poll, last = None, 0.0, 0.0, None
    while not out.get("done") and not STOP.is_set():
        now = time.time()
        if now - t_poll >= 10:
            t_poll = now
            tx = tailnet_tx()
            d = E1.stream_status() or {}
            a = d.get("adaptive_bitrate") if isinstance(d.get("adaptive_bitrate"), dict) else {}
            enc = encoder_rate()
            if enc and t_enc is None:
                t_enc = now
            kbps = None
            if tx is not None and last and now > last[0]:
                kbps = round((tx - last[1]) * 8 / 1000 / (now - last[0]), 1)
            last = (now, tx) if tx is not None else last
            row, _ = scrub({"at_utc": utc(now), "t": round(now, 3), "tailnet_tx_bytes": tx, "tailnet_tx_kbps": kbps,
                            "active": d.get("active"), "width": d.get("width"), "height": d.get("height"),
                            "bitrate_kbps": d.get("bitrate_kbps"), "level_kbps": a.get("level_kbps"),
                            "state": a.get("state"), "encoder": enc})
            append(rdir / "stream_poll.jsonl", row)
        if t_enc is not None and now - t_enc >= 20 and "flags_at_stream" not in out:
            out["flags_at_stream"], out["environ_at_stream_count"] = flags_check(spec_["kvs"])
            out["flags_at_stream_utc"] = utc()
        if now - t_wan >= 30:
            t_wan = now
            st = E1.http("GET", "/diagnostics/stream-telemetry", 10)[1] or {}
            w, n = scrub(st.get("wan") if isinstance(st, dict) else None)
            append(rdir / "wan_poll.jsonl", {"at_utc": utc(), "game_active": (E1.games_status() or {}).get("active"),
                                              "has_wan": isinstance(st, dict) and "wan" in st, "wan": w, "redacted_matches": n})
        time.sleep(2)


# ---------------------------------------------------------------- running the suite
def suite(rdir):
    cmd = [sys.executable, str(SUITE), "run", "--remote", "--out", str(rdir), "--prereg", str(PRE),
           "--runs", "1", "--window", str(WINDOW), "--gap", str(GAP), "--wait", str(WAIT)]
    with open(rdir / "suite_console.log", "a") as fh:
        fh.write(f"# {utc()} " + " ".join(c if not c.startswith(str(REPO)) else c.replace(str(REPO), "<repo>") for c in cmd) + "\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(REPO))
        try:
            return p.wait(timeout=SUITE_TIMEOUT)
        except subprocess.TimeoutExpired:
            log(f"the suite exceeded {SUITE_TIMEOUT} s: SIGINT (its finally-teardown runs)")
            p.send_signal(signal.SIGINT)
            try:
                return p.wait(timeout=900)
            except subprocess.TimeoutExpired:
                log("the suite did not exit 900 s after SIGINT; waiting on it")
                return p.wait()


def load_json(p):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError, TypeError):
        return None


def ladder_reading(rows, window):
    starts = [{"at_utc": r.get("at_utc"), **(r.get("start_rung") or {})} for r in rows if isinstance(r.get("start_rung"), dict)]
    w0, w1 = (window or {}).get("from"), (window or {}).get("to")
    inw = lambda t: bool(w0 and w1 and t and w0 <= t <= w1)
    trans = [{"at_utc": r.get("at_utc"), "from_kbps": r.get("from_kbps"), "to_kbps": r.get("to_kbps"), "reason": r.get("reason"),
              "class": r.get("class"), "trigger": r.get("trigger"), "in_window": inw(r.get("at_utc"))}
             for r in rows if r.get("event") == "transition" and r.get("acted")]
    clamps = [r for r in rows if r.get("source") == "remote_cap" and r.get("event") != "remote_cap_config"]
    rules = {}
    for r in rows:
        if r.get("event") == "wan_suggestion" and r.get("source") == "wan_rules":
            rules[r.get("rule")] = rules.get(r.get("rule"), 0) + 1
    path = []
    if starts:
        path.append(starts[0].get("kbps"))
    for t in trans:
        if not path or path[-1] != t["from_kbps"]:
            path.append(t["from_kbps"])
        path.append(t["to_kbps"])
    return {"rows": len(rows), "samples": sum(1 for r in rows if r.get("event") == "sample"), "start_rungs": starts,
            "remote_cap_config": [r for r in rows if r.get("event") == "remote_cap_config"][:3],
            "transitions": trans, "clamps": len(clamps),
            "clamp_events": {e: sum(1 for r in clamps if r.get("event") == e) for e in sorted({str(r.get("event")) for r in clamps})},
            "clamps_in_window": sum(1 for r in clamps if inw(r.get("at_utc"))),
            "rules_by_id": rules, "refused": sum(1 for r in rows if r.get("event") == "refused"),
            "rung_path": "→".join(str(x) for x in path) if path else None}


def journal_read(t0, t1, dest):
    try:
        j = subprocess.run(["journalctl", "--user", "-u", E1.UNIT, "-o", "short-iso", "--no-pager",
                            "--since", f"@{int(t0)}", "--until", f"@{int(t1) + 1}"], capture_output=True, timeout=120)
        r = subprocess.run([sys.executable, str(JREAD)], input=j.stdout, capture_output=True, timeout=120)
        dest.write_bytes(r.stdout)
        txt = r.stdout.decode(errors="replace")
    except (OSError, subprocess.SubprocessError) as e:
        dest.write_text(f"journal read failed: {e!r}\n")
        return {"error": repr(e)[:120]}
    lasts = [dict(kv.split("=", 1) for kv in l.split()[1:] if "=" in kv) for l in txt.splitlines() if l.strip().startswith("last ")]
    num = lambda d, x: int(d[x]) if d.get(x, "").lstrip("-").isdigit() else None
    return {"client_sessions": sum(1 for l in txt.splitlines() if l.strip().startswith("session ")),
            "fec_recovered": [num(d, "fec_recovered_packets") for d in lasts],
            "fec_unrecoverable": [num(d, "fec_unrecoverable_groups") for d in lasts],
            "rendered_frames": [num(d, "rendered_frames") for d in lasts],
            "lost_packets": [num(d, "lost_packets") for d in lasts]}


def poll_rows(rdir):
    rows = []
    try:
        for l in open(rdir / "stream_poll.jsonl"):
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass
    except OSError:
        pass
    return rows


def wire(rows, window):
    """The hub's tailnet tx rate: the median 10-s kbps over the window, per rung on the wire, and the bytes in the
    window (the counter's difference between the first and last poll inside it)."""
    w0, w1 = (window or {}).get("from"), (window or {}).get("to")
    med = lambda xs: (sorted(xs)[len(xs) // 2] if xs else None)
    inw = [r for r in rows if w0 and w1 and w0 <= r["at_utc"] <= w1]
    ks = [r["tailnet_tx_kbps"] for r in inw if isinstance(r.get("tailnet_tx_kbps"), (int, float))]
    by = {}
    for r in inw:
        if isinstance(r.get("tailnet_tx_kbps"), (int, float)) and r.get("bitrate_kbps"):
            by.setdefault(str(r["bitrate_kbps"]), []).append(r["tailnet_tx_kbps"])
    tx = [r for r in inw if isinstance(r.get("tailnet_tx_bytes"), int)]
    span = (tx[-1]["t"] - tx[0]["t"]) if len(tx) > 1 else 0
    nbytes = (tx[-1]["tailnet_tx_bytes"] - tx[0]["tailnet_tx_bytes"]) if len(tx) > 1 else None
    return {"tx_kbps_window_median": med(ks), "tx_kbps_window_mean": round(sum(ks) / len(ks), 1) if ks else None,
            "tx_kbps_by_rung": {r: {"median": med(v), "n": len(v)} for r, v in by.items()},
            "window_bytes": nbytes, "window_span_s": round(span, 1),
            "window_mb": round(nbytes / 1e6, 2) if nbytes is not None else None,
            "mb_per_10min": round(nbytes / 1e6 * 600 / span, 2) if nbytes and span else None,
            "wire_bitrate_kbps_seen": sorted({int(r["bitrate_kbps"]) for r in rows if r.get("active") and isinstance(r.get("bitrate_kbps"), (int, float))}),
            "encoder_bv_seen": sorted({r["encoder"]["b_v"] for r in rows if isinstance(r.get("encoder"), dict) and r["encoder"].get("b_v")})}


def wan_last(rdir):
    last = None
    try:
        for l in open(rdir / "wan_poll.jsonl"):
            r = json.loads(l)
            if isinstance(r.get("wan"), dict):
                last = r["wan"]
    except (OSError, ValueError):
        pass
    return (last or {}).get("class"), (last or {}).get("window_primary_counts")


def write_dropin(kvs):
    E1.DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in kvs))
    E1.sh(["systemctl", "--user", "daemon-reload"], 60)
    r = E1.restart_unit()
    env = r.get("environ") or []
    return {"mainpid_serves_8765": r.get("mainpid_serves_8765"), "manager": len(r.get("manager") or []),
            "environ_lines": len(env), "flags_present": {kv: kv in env for kv in kvs},
            "adopted_present": all(kv in env for kv in E1.ADOPTED),
            "ok": all(kv in env for kv in kvs) and all(kv in env for kv in E1.ADOPTED) and len(env) == len(E1.ADOPTED) + len(kvs)}


def run_one(spec_, attempt, busy_tries):
    rdir = RUNS / (f"run{spec_['n']}_{spec_['arm']}" + ("" if attempt == 1 else f"_r{attempt}"))
    rdir.mkdir(parents=True, exist_ok=True)
    t = time.time()
    row = {"n": spec_["n"], "arm": spec_["arm"], "attempt": attempt, "kvs": spec_["kvs"], "start_utc": utc(t),
           "busy_tries": busy_tries, "out": str(rdir.relative_to(HERE))}
    write_status(run=spec_["n"], doing=f"run {spec_['n']}/{NRUNS} {spec_['arm']} (attempt {attempt}): drop-in + restart", next="-")
    lad_off = ladder_offset()
    beside, th = {}, None
    try:
        wr = write_dropin(spec_["kvs"])
        row["dropin_readback"] = wr
        row["environ_lines"], row["environ_ok"] = wr["environ_lines"], wr["ok"]
        log(f"run {spec_['n']} {spec_['arm']}: drop-in written, restarted; environ {wr['environ_lines']} lines, ok {wr['ok']}")
        if not wr["ok"]:
            row["status"] = "NOT_STARTED"
            row["error"] = f"the environ did not read back the {len(E1.ADOPTED)} adopted lines plus the run's {len(spec_['kvs'])}"
        else:
            write_status(doing=f"run {spec_['n']}/{NRUNS} {spec_['arm']}: idle gap {GAP}s, then waiting up to {WAIT}s "
                               f"for the game (from {utc(time.time() + GAP)[11:16]}Z to {utc(time.time() + GAP + WAIT)[11:16]}Z)")
            th = threading.Thread(target=beside_run, args=(spec_, rdir, beside), daemon=True)
            th.start()
            row["suite_rc"] = suite(rdir)
    finally:
        beside["done"] = True
        if th:
            th.join(timeout=30)
        td = {}
        E1.teardown_flags({"dropin": spec_["kvs"]}, td)
        row["teardown"] = {x: td.get(x) for x in ("dropin_removed", "dropin_env_absent", "flags_absent")}
        row["teardown"]["environ_lines_after"] = len(k(td, "restart_after_flags", "environ") or [])
        row["flags_absent_after"] = bool(td.get("flags_absent"))
        log(f"run {spec_['n']} {spec_['arm']}: drop-in removed, restarted; flags_absent {td.get('flags_absent')}")
    t_end = time.time()
    row["end_utc"] = utc(t_end)
    try:
        analyse(row, rdir, t, t_end, lad_off, beside)
    except Exception as e:      # noqa: BLE001 -- the analysis never blocks the teardown or the next run
        row["analysis_error"] = repr(e)[:300]
        log(f"run {spec_['n']}: analysis error {e!r}")
    append(ROWS_P, row)
    hist_append(row)
    return row


def analyse(row, rdir, t, t_end, lad_off, beside):
    s = load_json(rdir / "E1-PS1-STREAM-REMOTE" / "run1" / "summary.json") or {}
    con = (rdir / "suite_console.log").read_text(errors="replace") if (rdir / "suite_console.log").exists() else ""
    row["status"] = row.get("status") or s.get("status") or ("REFUSED" if "refusing" in con else "NO_SUMMARY")
    row["error"] = row.get("error") or s.get("error")
    row["refused"] = row["status"] == "REFUSED" or "refusing" in con
    ep = s.get("endpoint") or {}
    row["endpoint_class"], row["endpoint_hash"] = ep.get("class"), ep.get("hash")
    row["playing_utc"], row["window"] = s.get("playing_utc"), s.get("window")
    row["profile_at_playing"] = s.get("profile_at_playing")
    lan = "not reached over the overlay" in str(s.get("error") or "")
    absent = row["flags_absent_after"]
    row["validity"] = ("invalid (flags_absent not true)" if not absent else
                       "valid" if s.get("status") == "OK" and ep.get("class") == "overlay" else
                       "void (LAN class)" if lan else f"not valid ({row['status']})")
    hb, g3, pth = k(s, "key", "heartbeat") or {}, k(s, "key", "gate3") or {}, k(s, "key", "path") or {}
    row.update({"loss_per_min": hb.get("video_loss_per_min"), "rendered_fps": hb.get("rendered_fps"),
                "resyncs": hb.get("stream_resyncs"), "heartbeat": hb, "telemetry": k(s, "key", "telemetry"),
                "status_poll": k(s, "key", "status_poll"), "path": pth, "path_counts": pth.get("path_counts"),
                "path_changes": pth.get("path_changes"), "retroarch_fps": g3.get("retroarch_fps"),
                "capture_fps": g3.get("capture_fps"), "dupdrop_per_min": g3.get("dupdrop_per_min"),
                "host_teardown": s.get("teardown")})
    if s.get("status") == "OK":
        rf_, cf, dd = g3.get("retroarch_fps"), g3.get("capture_fps"), g3.get("dupdrop_per_min")
        row["host_gates"] = {"retroarch_ge_59_9": rf_ is not None and rf_ >= 59.9,
                             "capture_60_pm_0_1": cf is not None and abs(cf - 60) <= 0.1,
                             "dupdrop_le_0_2": dd is not None and dd <= 0.2, "flags_absent": absent}
        row["host_gates_met"] = all(row["host_gates"].values())
    lrows, rotated = ladder_read(lad_off)
    with open(rdir / "ladder_log.jsonl", "w") as fh:
        for r in lrows:
            fh.write(json.dumps(scrub(r)[0], sort_keys=True) + "\n")
    lad = ladder_reading(lrows, row["window"])
    st0 = (lad["start_rungs"] or [{}])[0]
    row.update({"ladder": lad, "ladder_log_rotated": rotated, "rung_path": lad["rung_path"],
                "start_rung_kbps": st0.get("kbps"), "start_rung_source": st0.get("source"),
                "start_rung_path_class": st0.get("path_class"), "start_rung_first_row": st0 or None,
                "transitions": [f"{x['from_kbps']}→{x['to_kbps']} {x['reason']} {(x['at_utc'] or '')[11:19]}Z" for x in lad["transitions"]],
                "clamps": lad["clamps"], "rules_by_id": lad["rules_by_id"],
                "flags_at_stream": beside.get("flags_at_stream"), "environ_at_stream_count": beside.get("environ_at_stream_count")})
    jr = journal_read(t, t_end, rdir / "companion_journal.txt")
    row.update({"journal": jr, "fec_recovered": jr.get("fec_recovered"), "fec_unrecoverable": jr.get("fec_unrecoverable")})
    row.update(wire(poll_rows(rdir), row["window"]))
    row["wan_class"], row["wan_windows"] = wan_last(rdir)
    log(f"run {row['n']} {row['arm']} attempt {row['attempt']}: {row['status']} {row['validity']} endpoint {row['endpoint_class']} "
        f"start {row['start_rung_kbps']} ({row['start_rung_source']}, {row['start_rung_path_class']}) path {row['rung_path']} "
        f"clamps {row['clamps']} rules {row['rules_by_id']} wire {row.get('wire_bitrate_kbps_seen')} "
        f"tx {row.get('tx_kbps_window_median')} kbps {row.get('window_mb')} MB loss {row['loss_per_min']} "
        f"rendered {row['rendered_fps']} gates {row.get('host_gates_met')} flags_absent {row['flags_absent_after']}")


def main():
    WATCH.mkdir(parents=True, exist_ok=True)
    st = json.loads(STATE_P.read_text()) if STATE_P.exists() else {"done": {}, "started_utc": utc()}
    p, sline = host_state()
    st.setdefault("host_state_at_start", []).append({"at_utc": utc(), **p})
    jdump(STATE_P, st)
    log("start; runs done", len(st["done"]), "| host state", sline, "| cap", CAP_UTC)
    write_status(run=len(st["done"]), state=sline, doing="starting")
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    why = "the run done"
    for i, spec_ in enumerate(RUNSPEC):
        key = f"run{spec_['n']}_{spec_['arm']}"
        if key in st["done"]:
            continue
        attempt, row = 1, None
        while True:
            if stop_requested():
                why = "the stop file"
                break
            if time.time() >= CAP:
                why = "the cap"
                log("the cap: no run starts after it")
                break
            tries = 0
            while bool((E1.games_status() or {}).get("active")) and tries < BUSY_TRIES and not stop_requested():
                tries += 1
                log(f"run {spec_['n']}: busy (a game session is active) -- waiting 10 min (try {tries}/{BUSY_TRIES})")
                write_status(run=spec_["n"], doing=f"busy: waiting 10 min (try {tries}/{BUSY_TRIES})")
                t_busy = time.time()
                while time.time() - t_busy < BUSY_WAIT and bool((E1.games_status() or {}).get("active")) and not stop_requested():
                    time.sleep(15)
            if bool((E1.games_status() or {}).get("active")):
                row = {"n": spec_["n"], "arm": spec_["arm"], "attempt": attempt, "start_utc": utc(), "busy_tries": tries,
                       "validity": "busy", "flags_absent_after": True}
                append(ROWS_P, row)
                hist_append(row)
                break
            row = run_one(spec_, attempt, tries)
            if row["validity"] == "void (LAN class)":
                log(f"run {spec_['n']}: LAN class -- void; not replaced (the user's call)")
            break
        if row is None:
            break
        st["done"][key] = row["validity"]
        jdump(STATE_P, st)
        _, sline = host_state()
        nxt = RUNSPEC[i + 1] if i + 1 < len(RUNSPEC) else None
        write_status(run=spec_["n"], last=(f"run {spec_['n']} {spec_['arm']}: {row.get('status')} {row['validity']} "
                                           f"start {row.get('start_rung_kbps')} ({row.get('start_rung_source')}) path {row.get('rung_path')} "
                                           f"tx {row.get('tx_kbps_window_median')} kbps loss/min {row.get('loss_per_min')} "
                                           f"rendered {row.get('rendered_fps')} flags_absent {row.get('flags_absent_after')}"),
                     last_at=utc(), state=sline, doing="idle",
                     next=(f"run {nxt['n']} {nxt['arm']} now; start the game after {utc(time.time() + GAP + 30)[11:16]}Z" if nxt else "-"))
        if not row.get("flags_absent_after"):
            why = "a state violation (flags_absent not true after a run)"
            log(f"run {spec_['n']}: STATE VIOLATION -- flags_absent not true; the driver ends")
            break
        if row.get("refused"):
            why = "the row's preflight refused"
            log(f"run {spec_['n']}: REFUSED by the row's preflight; the driver ends")
            break
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
