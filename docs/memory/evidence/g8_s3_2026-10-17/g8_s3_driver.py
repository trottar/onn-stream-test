#!/usr/bin/env python3
"""G8-S3 -- the rate-cap cells of G8-S1 re-run with G8-S2's start rung, DETACHED, run as pre-registered
(g8_s3_preregistration.txt). One process from the hash to the end of the 3 cells or the cap (2026-10-18T00:00:00Z),
launched as a systemd --user transient unit (privyhub-g8-s3), not a Code-session child; resumable from
g8_s3_state.json if restarted.

Built from g8_s1_driver.py's scaffolding (kept: utc / log / jdump / append, the status line rewritten after every run
plus a 5-min heartbeat, history.csv, the STOP file, the busy skip, the cap, the suite call with its timeout and SIGINT,
the crash-to-status handler, --dry, the readings beside a run, the shim's applied check with G8-P1's count tolerances).
Changed: the cells table (three), the flag lines per cell (+ PRIVYHUB_START_RUNG=floor), `no_play` as an OUTCOME (not
a validity failure), and the link-side readings G8-S3's task lists.

THE CELLS (3, in order), each @post-fec,seed=1, each with PRIVYHUB_WAN_TELEMETRY=1 and PRIVYHUB_START_RUNG=floor:
  1. cap-6000, rules off (PRIVYHUB_WAN_ADAPTATION absent)      -- G8-S1's counterpart: cell 17
  2. cap-6000, rules on  (PRIVYHUB_WAN_ADAPTATION=1)           -- G8-S1's counterpart: cell 18
  3. cap-4500, rules off                                        -- G8-S1's counterpart: cell 19 (the prediction check)
One E1-PS1-STREAM --e2 --window 600, idle gap 120 s, per cell, through g8_s3_suite_call.py (tools/e1_suite.py's
run_suite, unedited). The suite writes the run's e3_flag.conf, restarts, checks the unit's environ, and removes it at
teardown (flags_absent).

BESIDE EACH RUN (read-only): a thread that
  - every 10 s reads /plugins/games/native-stream-status (active, size, bitrate_kbps, the ladder level) and, when an
    encoder runs, its -b:v / -maxrate (only those two argv values) -> stream_poll_run<attempt>.jsonl: the rung on the
    wire even when the client never reaches PLAYING;
  - 20 s after the first encoder appears, reads the companion's environ (the flags under load, during the attempts);
  - 150 s into the window (if one opens), reads it again with the shim's newest line (G8-S1's reading);
  - every 30 s, /diagnostics/stream-telemetry's `wan` (scrubbed) -> wan_poll_run<attempt>.jsonl.
After each run: the shim's lines (logs/impairment.jsonl from the run's start) -> impairment_run<attempt>.jsonl and the
applied check; the ladder's log (logs/games/adaptive_bitrate_shadow.jsonl, from the run's start offset; its archive .1
read too if it rotated) -> ladder_log_run<attempt>.jsonl -- the start rung and its source from its first row carrying
`start_rung` (G8-S2: the suite's window decisions.jsonl does not hold that row), every acted transition with its reason,
the rules' suggestions by rule id; the companion's journal over the run, reduced by G8-S1's g8_s1_cap_log_read.py (per
client session the first / last heartbeat counters incl. FEC recovered / unrecoverable; addresses and ids masked) ->
companion_journal_run<attempt>.txt.

OUTCOME vs VALIDITY: PLAYING is the measured outcome: `playing` (the suite's status OK) or `no_play` (the suite's own
attempts all ended before PLAYING). Validity is G8-S1's: the shim's profile applied by the count tolerances and
flags_absent after. A playing run whose shim telemetry shows the profile not applied is `profile-not-applied` and is
run once more (run2). A no_play cell is NOT repeated beyond the suite's own attempts.
BUSY: a game session active at a cell's start -> wait 10 min and retry, up to 3 times, then the cell is `busy`.
STOP: ~/privyhub_g8_s3/STOP ends the driver after the run in flight (never removed by the driver). THE CAP: no cell
starts at or after 2026-10-18T00:00:00Z. A cell whose teardown does not read flags_absent ends the driver (state).
--dry: about 2 min, no stream: the preflight and busy check, cell 2's drop-in written (four lines), the companion
restarted and its environ read back, 30 s held, the drop-in removed, restarted, flags_absent read; status lines (30-s
heartbeat) into dry_run/; then exit."""
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
CALL = HERE / "g8_s3_suite_call.py"
JREAD = HERE.parent / "g8_s1_2026-10-16/g8_s1_cap_log_read.py"
PRE = HERE / "g8_s3_preregistration.txt"
WATCH = Path.home() / "privyhub_g8_s3"
RUNS = HERE / "runs"
CAP_UTC = "2026-10-18T00:00:00Z"
CAP = datetime(2026, 10, 18, 0, 0, 0, tzinfo=timezone.utc).timestamp()
DRY = "--dry" in sys.argv
STOPFILE = WATCH / "STOP"
OUTD = HERE / "dry_run" if DRY else WATCH
STATUS_P, HIST_P, WLOG_P = OUTD / "status.txt", OUTD / "history.csv", OUTD / "driver.log"
STATE_P = (HERE / "dry_run" if DRY else HERE) / "g8_s3_state.json"
CELLS_P = (HERE / "dry_run" if DRY else HERE) / "cells.jsonl"
IMP_LOG = REPO / "logs/impairment.jsonl"
LADDER_LOG = REPO / "logs/games/adaptive_bitrate_shadow.jsonl"
LADDER_ARCH = LADDER_LOG.parent / "archive" / (LADDER_LOG.name + ".1")
HEARTBEAT = 30 if DRY else 300
WINDOW, GAP = 600, 120
BUSY_WAIT, BUSY_TRIES = 600, 3
SUITE_TIMEOUT = 2 * 3600
NCELLS = 3
CAPS = {"cap-6000": 6000, "cap-4500": 4500}
CELLS = [{"n": 1, "profile": "cap-6000", "arm": "off", "cell": "01_cap-6000_floor_off", "g8_s1": "17_cap-6000_off"},
         {"n": 2, "profile": "cap-6000", "arm": "on", "cell": "02_cap-6000_floor_on", "g8_s1": "18_cap-6000_on"},
         {"n": 3, "profile": "cap-4500", "arm": "off", "cell": "03_cap-4500_floor_off", "g8_s1": "19_cap-4500_off"}]
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F]{32,}\b")

spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)
# E4-S5D's segment-aware capture fps and dup+drop (the host gates' reading, as CL-B2 / CL-B3 / G8-S1 used it)
spec = importlib.util.spec_from_file_location("s5d", HERE.parent / "e4_s5d_2026-10-15/e4_s5d_analysis.py")
S5D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S5D)
STOP = threading.Event()


def kvs(cell):
    out = ["PRIVYHUB_WAN_TELEMETRY=1", f"PRIVYHUB_IMPAIRMENT={cell['profile']}@post-fec,seed=1", "PRIVYHUB_START_RUNG=floor"]
    return out + (["PRIVYHUB_WAN_ADAPTATION=1"] if cell["arm"] == "on" else [])


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log(*a):
    line = f"[g8s3 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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
HIST_COLS = ["n", "cell", "profile", "arm", "start_utc", "busy_tries", "attempt", "status", "outcome", "validity",
             "profile_applied", "suite_attempts", "playing_attempt", "s_to_playing", "start_rung_kbps", "start_rung_source",
             "wire_bitrate_kbps_seen", "encoder_bv_seen", "rung_path", "transitions", "rules_by_id", "flags_at_stream",
             "flags_under_load", "loss_per_min", "rendered_fps", "resyncs", "stale_per_min", "client_pauses",
             "fec_recovered", "fec_unrecoverable", "wan_class", "wan_windows", "retroarch_fps", "capture_fps",
             "dupdrop_per_min", "host_gates_met", "host_cpu", "companion_cpu", "shim_cpu_pct_core", "shim_packets_in",
             "shim_packets_out", "shim_dropped_queue", "shim_queue_max", "shim_steady_in_kbps", "shim_steady_drop_frac",
             "preflight_ok", "flags_absent_after", "final_flags_absent"]


def write_status(**kw):
    """One line, rewritten (atomic replace of the driver's own status file) after every run, and every HEARTBEAT s by
    the heartbeat thread: a reader can tell idle from dead by the heartbeat's age."""
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | cell {s['cell']}/{NCELLS} | last: {s['last']} (at {s['last_at']}) | doing: {s['doing']} | "
                f"next: {s['next']} | state: {s['state']} | cap {CAP_UTC} | stop: touch ~/privyhub_g8_s3/STOP\n")
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


def ladder_offset():
    try:
        return LADDER_LOG.stat().st_size
    except OSError:
        return 0


def ladder_read(off):
    """The ladder's rows written since `off`: the live file from the offset; if it rotated (now shorter than the
    offset), the newest archive from the offset, then the whole live file."""
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
    """Only the -b:v and -maxrate values of the running encoder's argv (nothing else of it is kept)."""
    for p in E1.encoder_pids():
        try:
            argv = open(f"/proc/{p}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            continue
        val = lambda opt: argv[argv.index(opt) + 1] if opt in argv and argv.index(opt) + 1 < len(argv) else None
        return {"b_v": val("-b:v"), "maxrate": val("-maxrate")}
    return None


def flags_check(cell):
    env = E1.environ_flags(E1.mainpid())
    want = kvs(cell)
    return (all(kv in env for kv in want) and all(kv in env for kv in E1.ADOPTED) and len(env) == len(E1.ADOPTED) + len(want),
            len(env))


def beside_run(cell, cdir, imp_start, out, attempt):
    """See the module docstring: the stream poll every 10 s, the flags 20 s into the first encoder and 150 s into the
    window, `wan` every 30 s."""
    sl = cdir / "suite.log"
    seen = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
    t_window, t_enc, t_wan, t_poll = None, None, 0.0, 0.0
    while not out.get("done") and not STOP.is_set():
        now = time.time()
        cur = sum(1 for l in open(sl) if ": window " in l) if sl.exists() else 0
        if t_window is None and cur > seen:
            t_window = now
        if now - t_poll >= 10:
            t_poll = now
            d = E1.stream_status() or {}
            a = d.get("adaptive_bitrate") if isinstance(d.get("adaptive_bitrate"), dict) else {}
            enc = encoder_rate()
            if enc and t_enc is None:
                t_enc = now
            row, _ = scrub({"at_utc": utc(), "active": d.get("active"), "width": d.get("width"), "height": d.get("height"),
                            "bitrate_kbps": d.get("bitrate_kbps"), "level_kbps": a.get("level_kbps"), "state": a.get("state"),
                            "encoder": enc})
            append(cdir / f"stream_poll_run{attempt}.jsonl", row)
        if t_enc is not None and now - t_enc >= 20 and "flags_at_stream" not in out:
            out["flags_at_stream"], out["environ_at_stream_count"] = flags_check(cell)
            out["flags_at_stream_utc"] = utc()
        if t_window is not None and now - t_window >= 150 and "flags_under_load" not in out:
            out["flags_under_load"], out["environ_under_load_count"] = flags_check(cell)
            lines = imp_read(imp_start)
            out["shim_live_under_load"] = bool(lines) and lines[-1].get("profile") == cell["profile"]
        if now - t_wan >= 30:
            t_wan = now
            st = E1.http("GET", "/diagnostics/stream-telemetry", 10)[1] or {}
            w, n = scrub(st.get("wan") if isinstance(st, dict) else None)
            append(cdir / f"wan_poll_run{attempt}.jsonl", {"at_utc": utc(), "game_active": (E1.games_status() or {}).get("active"),
                                                         "has_wan": isinstance(st, dict) and "wan" in st, "wan": w, "redacted_matches": n})
        time.sleep(2)


def applied(profile, rows):
    """G8-P1's tolerances for the cap profiles, read on the run's shim telemetry (per-second deltas), as G8-S1."""
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
    if pin <= 0 or profile not in CAPS:
        return False, m
    cap = CAPS[profile]
    over = [r for r in rows if (r.get("bytes_in") or 0) * 8 / 1000 > cap * 1.05]
    ok = all((r.get("bytes_out") or 0) * 8 / 1000 <= cap * 1.05 for r in rows) and dl == db == ro == 0
    m["seconds_input_over_cap"] = len(over)
    m["out_kbps_max"] = round(max((r.get("bytes_out") or 0) * 8 / 1000 for r in rows), 1)
    # G8-S1 §5's reading: stream starts split where t_s restarts; "steady" = the seconds after the first 2.5 s
    segs, cur, last_t = [], [], None
    for r in rows:
        t = r.get("t_s") or 0
        if last_t is not None and t < last_t:
            segs.append(cur)
            cur = []
        cur.append(r)
        last_t = t
    segs.append(cur)
    st = [r for sg in segs for r in sg if (r.get("t_s") or 0) > 2.5]
    spin = sum(r.get("packets_in") or 0 for r in st)
    m["stream_starts"] = len(segs)
    m["seconds_each"] = [round(max((r.get("t_s") or 0) for r in sg), 1) for sg in segs]
    in_k = sorted((r.get("bytes_in") or 0) * 8 / 1000 for r in st)
    m["steady_in_kbps_median"] = round(in_k[len(in_k) // 2], 1) if in_k else None
    m["steady_in_kbps_range"] = [round(in_k[0], 1), round(in_k[-1], 1)] if in_k else None
    m["steady_drop_frac"] = round(sum(r.get("dropped_queue") or 0 for r in st) / spin, 4) if spin else None
    m["loss_frac"] = round(dl / pin, 5)
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


def load_json(p):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError, TypeError):
        return None


def figures(s, rd):
    rf = k(s, "teardown", "report_fields") or {}
    mins = (rf.get("duration_ms") or 0) / 60000
    hh = lambda key: k(s, "host", "host", key, "mean")
    rungs = []
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
    return {"status": (s or {}).get("status"), "window": (s or {}).get("window"),
            "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"),
            "stale_per_min": round(rf["decoder.stale_output_drops"] / mins, 3) if mins and "decoder.stale_output_drops" in rf else None,
            "spikes20_per_min": round(rf["decoder.spike_20_ms"] / mins, 2) if mins and "decoder.spike_20_ms" in rf else None,
            "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []),
            "pauses": k(s, "key", "recovery"),
            "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": hh("cpu.mean_pct"),
            "companion_cpu": hh("procs.companion.cpu_pct"),
            "rung_min": min(rungs) if rungs else None, "rung_max": max(rungs) if rungs else None,
            "playing_attempt": k(s, "launch", "stream", "attempt"), "s_to_playing": k(s, "launch", "stream", "s_to_playing"),
            "report_fields": rf,
            "preflight_ok": k(s, "preflight", "ok"), "flags_absent_after": k(s, "teardown", "flags_absent"),
            "apk": k(s, "teardown", "apk"), **capture(s, rd)}


def capture(s, rd):
    try:
        cap, dd = S5D.segcap(rd, s) if s and rd and (s or {}).get("status") == "OK" else (None, None)
    except Exception as e:      # noqa: BLE001 -- reported, not fatal
        return {"capture_fps": None, "dupdrop_per_min": None, "capture_error": repr(e)[:120]}
    return {"capture_fps": cap, "dupdrop_per_min": dd}


def failed_attempts(rd):
    """The suite's failed attempts (summary_failed_attempt<n>.json): the client's end-of-session report per attempt."""
    out = []
    for p in sorted(rd.glob("summary_failed_attempt*.json")) if rd else []:
        f = load_json(p) or {}
        rf = k(f, "teardown", "report_fields") or {}
        out.append({"file": p.name, "error": str(f.get("error"))[:200], "launch": k(f, "launch", "stream"),
                    "flags_absent": k(f, "teardown", "flags_absent"),
                    **{x: rf.get(x) for x in ("duration_ms", "rendered_frames", "lost_packets", "max_output_gap_ms",
                                              "video.sequence_resyncs", "audio.underruns", "stale_output_drops")}})
    return out


def ladder_reading(rows, window):
    """From the ladder's rows over the run: the start rung(s) (first row carrying `start_rung`), the acted transitions
    with their reasons, the rules' suggestions by rule id, the rung path."""
    starts = [{"at_utc": r.get("at_utc"), **(r.get("start_rung") or {})} for r in rows if isinstance(r.get("start_rung"), dict)]
    w0, w1 = (window or {}).get("from"), (window or {}).get("to")
    inw = lambda t: bool(w0 and w1 and t and w0 <= t <= w1)
    trans = [{"at_utc": r.get("at_utc"), "from_kbps": r.get("from_kbps"), "to_kbps": r.get("to_kbps"), "reason": r.get("reason"),
              "class": r.get("class"), "trigger": r.get("trigger"), "in_window": inw(r.get("at_utc"))}
             for r in rows if r.get("event") == "transition" and r.get("acted")]
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
            "transitions": trans, "rules_by_id": rules, "refused": sum(1 for r in rows if r.get("event") == "refused"),
            "rung_path": "→".join(str(x) for x in path) if path else None}


def journal_read(t0, t1, dest):
    """The companion's journal over [t0, t1], reduced by G8-S1's reader (addresses / ids masked before writing)."""
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
            "lost_packets": [num(d, "lost_packets") for d in lasts], "rx_packets": [num(d, "rx_packets") for d in lasts],
            "last_output_age_ms": [num(d, "last_output_age_ms") for d in lasts]}


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


def stream_seen(cdir, attempt):
    bits, bv = set(), set()
    try:
        for l in open(cdir / f"stream_poll_run{attempt}.jsonl"):
            r = json.loads(l)
            if r.get("active") and isinstance(r.get("bitrate_kbps"), (int, float)):
                bits.add(int(r["bitrate_kbps"]))
            if isinstance(r.get("encoder"), dict) and r["encoder"].get("b_v"):
                bv.add(r["encoder"]["b_v"])
    except (OSError, ValueError):
        pass
    return sorted(bits), sorted(bv)


def run_cell(cell, attempt, busy_tries):
    cdir = RUNS / cell["cell"]
    wdir = cdir / "E1-PS1-STREAM_flag"
    before = latest_run(wdir)
    imp_start, lad_off = imp_lines(), ladder_offset()
    t = time.time()
    write_status(cell=cell["n"], doing=f"cell {cell['n']}/{NCELLS} {cell['profile']} floor rules-{cell['arm']} (attempt {attempt}, "
                                       f"started {utc(t)[11:16]}Z)", next="-")
    beside = {}
    th = threading.Thread(target=beside_run, args=(cell, cdir, imp_start, beside, attempt), daemon=True)
    cdir.mkdir(parents=True, exist_ok=True)
    th.start()
    suite(cdir, cell, SUITE_TIMEOUT)
    beside["done"] = True
    th.join(timeout=30)
    t_end = time.time()
    rd = latest_run(wdir)
    s = load_json(rd / "summary.json") if rd and rd != before else None
    f = figures(s, rd)
    rows = imp_read(imp_start)
    with open(cdir / f"impairment_run{attempt}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    ok, m = applied(cell["profile"], rows)
    lrows, rotated = ladder_read(lad_off)
    with open(cdir / f"ladder_log_run{attempt}.jsonl", "w") as fh:
        for r in lrows:
            fh.write(json.dumps(scrub(r)[0], sort_keys=True) + "\n")
    lad = ladder_reading(lrows, f.get("window"))
    jr = journal_read(t, t_end, cdir / f"companion_journal_run{attempt}.txt")
    final = load_json(cdir / "final_state.json") or {}
    fails = failed_attempts(rd)
    outcome = "playing" if f["status"] == "OK" else "no_play"
    absent = bool(f["flags_absent_after"]) and bool(final.get("flags_absent")) and all(a.get("flags_absent") for a in fails)
    validity = ("valid" if ok and absent else "profile-not-applied" if absent else "invalid (flags_absent not true)")
    wc, ww = wan_last(cdir, attempt)
    bits, bv = stream_seen(cdir, attempt)
    st0 = (lad["start_rungs"] or [{}])[0]
    gates = None
    if outcome == "playing":
        rf_, cf, dd = f.get("retroarch_fps"), f.get("capture_fps"), f.get("dupdrop_per_min")
        gates = {"retroarch_ge_59_9": rf_ is not None and rf_ >= 59.9, "capture_60_pm_0_1": cf is not None and abs(cf - 60) <= 0.1,
                 "dupdrop_le_0_2": dd is not None and dd <= 0.2, "flags_absent": absent}
    row = {**cell, "start_utc": utc(t), "end_utc": utc(t_end), "busy_tries": busy_tries, "attempt": attempt, "outcome": outcome,
           "validity": validity, "profile_applied": ok, "shim": m, "suite_attempts": len(fails) + (1 if outcome == "playing" else 0),
           "failed_attempts": fails, "flags_at_stream": beside.get("flags_at_stream"),
           "environ_at_stream_count": beside.get("environ_at_stream_count"), "flags_under_load": beside.get("flags_under_load"),
           "environ_under_load_count": beside.get("environ_under_load_count"), "shim_live_under_load": beside.get("shim_live_under_load"),
           "run_dir": str(rd.relative_to(HERE)) if rd else None, **{x: v for x, v in f.items()},
           "start_rung_kbps": st0.get("kbps"), "start_rung_source": st0.get("source"), "start_rung_first_row": st0 or None,
           "ladder": lad, "ladder_log_rotated": rotated, "rung_path": lad["rung_path"],
           "transitions": [f"{x['from_kbps']}→{x['to_kbps']} {x['reason']} {(x['at_utc'] or '')[11:19]}Z" for x in lad["transitions"]],
           "rules_by_id": lad["rules_by_id"], "journal": jr,
           "fec_recovered": jr.get("fec_recovered"), "fec_unrecoverable": jr.get("fec_unrecoverable"),
           "wire_bitrate_kbps_seen": bits, "encoder_bv_seen": bv, "wan_class": wc, "wan_windows": ww,
           "host_gates": gates, "host_gates_met": (all(gates.values()) if gates else None),
           "final_flags_absent": final.get("flags_absent"),
           "final_preflight_like": {x: final.get(x) for x in ("game_active", "apk", "e3_dropin_absent", "e4_constraint_absent")},
           "shim_cpu_pct_core": m.get("shim_cpu_pct_core"), "shim_packets_in": m.get("packets_in"),
           "shim_packets_out": m.get("packets_out"), "shim_dropped_queue": m.get("dropped_queue"), "shim_queue_max": m.get("queue_max"),
           "shim_steady_in_kbps": m.get("steady_in_kbps_median"), "shim_steady_drop_frac": m.get("steady_drop_frac")}
    append(CELLS_P, row)
    hist_append(row)
    log(f"cell {cell['n']} {cell['profile']} rules-{cell['arm']} attempt {attempt}: {f['status']} {outcome} {validity} "
        f"start {st0.get('kbps')} ({st0.get('source')}) wire {bits} enc {bv} path {lad['rung_path']} "
        f"loss {f['loss_per_min']} rendered {f['rendered_fps']} class {wc} rules {lad['rules_by_id']} "
        f"shim in {m.get('steady_in_kbps_median')} drop {m.get('steady_drop_frac')} gates {row['host_gates_met']} "
        f"flags_at_stream {beside.get('flags_at_stream')} flags_under_load {beside.get('flags_under_load')} "
        f"flags_absent {f['flags_absent_after']}/{final.get('flags_absent')}")
    return row


def dry():
    """--dry: about 2 min, no stream (see the module docstring)."""
    (HERE / "dry_run").mkdir(exist_ok=True)
    p, sline = adopted_state()
    log("dry: start; preflight", json.dumps(p), "| busy", bool(p.get("game_active")), "| stop file present", stop_requested())
    cell = CELLS[1]                  # 02: the longest drop-in (four lines)
    write_status(cell=cell["n"], doing="dry run (no stream): the drop-in written", state=sline,
                 next=f"exit at {utc(time.time() + 120)[11:16]}Z")
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    rec = {"cell": cell["cell"], "kvs": kvs(cell), "preflight_before": p}
    if p.get("game_active") or not p.get("ok"):
        log("dry: the preflight is not ok or a game is active; nothing written")
        STOP.set()
        write_status(doing="dry: refused (state)", next="-")
        return 1
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
    why = f"all {NCELLS} cells done"
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
        if row["validity"] == "profile-not-applied" and row["outcome"] == "playing" and time.time() < CAP and not stop_requested():
            log(f"cell {cell['n']}: profile-not-applied -- repeated once")
            row = run_cell(cell, 2, tries)
        st["done"][cell["cell"]] = f"{row['outcome']} {row['validity']}"
        jdump(STATE_P, st)
        _, sline = adopted_state()
        nxt = next((c for c in CELLS[i + 1:] if c["cell"] not in st["done"]), None)
        write_status(cell=cell["n"], last=(f"cell {cell['n']} {cell['profile']} floor rules-{cell['arm']}: {row['outcome']} {row['validity']} "
                                           f"start {row.get('start_rung_kbps')} ({row.get('start_rung_source')}) wire {row.get('wire_bitrate_kbps_seen')} "
                                           f"path {row.get('rung_path')} loss/min {row.get('loss_per_min')} rendered {row.get('rendered_fps')} "
                                           f"shim drop {row.get('shim_steady_drop_frac')} class {row.get('wan_class')}"),
                     last_at=utc(), state=sline, doing="idle",
                     next=(f"cell {nxt['n']} {nxt['profile']} rules-{nxt['arm']} now (~{utc(time.time() + 60)[11:16]}Z)" if nxt else "-"))
        if row["validity"].startswith("invalid"):
            why = "a state violation (flags_absent not true after a cell)"
            log(f"cell {cell['n']}: STATE VIOLATION -- flags_absent not all true; the driver ends")
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
