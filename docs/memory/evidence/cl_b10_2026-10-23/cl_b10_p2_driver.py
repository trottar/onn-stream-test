#!/usr/bin/env python3
"""CL-B10 PART 2 -- the attended cells, ONE CELL PER LAUNCH (--cell 1 | --cell 4), as pre-registered
(cl_b10_p2_preregistration.txt), DETACHED (systemd --user unit privyhub-cl-b10-p2). From cl_b10_driver.py (PART 1's
driver; the diff is cl_b10_p2_driver_vs_cl_b10.diff). Changed:
  - the cells: 1 (5 GHz, the user presses Home ~4 min in) and 4 (2.4 GHz for the notice, the user switches back to
    5 GHz ~10 min in), both E1-SNES-STREAM (snes9x) with the drop-in PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1 only;
    cell 1 window 600, cell 4 window 780; gap 120;
  - one cell per launch; its own state file cl_b10_p2_state.json; rows appended to cells.jsonl beside cells 2 and 3;
  - the cap: the launch + 40 min (the pre-registration's rule);
  - the band read from the onn every 10 s through the cell into runs/<cell>/band.jsonl (dumpsys wifi's mWifiInfo
    line parsed in memory: frequency, band, standard, RSSI, tx / rx only; nothing else kept);
  - the watch rule: a cell is refused at launch if it could not end before 04:30Z or would start before 05:30Z
    (the nightly watch's hour; no companion restart in it);
  - the status text and the log tag name this driver and its stop file (~/privyhub_cl_b10/STOP);
  - the properties restart_guard / stall_signal / link_notice set to 1 and read back before, read back after, NOT
    cleared (stage 3 clears them)."""
import hashlib
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
CALL = HERE / "cl_b10_p2_suite_call.py"
JREAD = HERE.parent / "g8_s1_2026-10-16/g8_s1_cap_log_read.py"
PRE = HERE / "cl_b10_p2_preregistration.txt"
WATCH = Path.home() / "privyhub_cl_b10"
RUNS = HERE / "runs"


def _cap_from_pre():
    """The cap is written in the pre-registration (`CAP_UTC: <iso>Z`, launch + 3 h); none -> no cell starts."""
    try:
        for line in PRE.read_text().splitlines():
            if line.strip().startswith("CAP_UTC:"):
                v = line.split(":", 1)[1].strip()
                return v, datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except (OSError, ValueError):
        pass
    return "unset", 0.0


LAUNCH = time.time()
CAP = LAUNCH + 40 * 60
CAP_UTC = datetime.fromtimestamp(CAP, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
DRY = "--dry" in sys.argv
STOPFILE = WATCH / "STOP"
OUTD = HERE / "dry_run" if DRY else WATCH
STATUS_P, HIST_P, WLOG_P = OUTD / "status.txt", OUTD / "history_p2.csv", OUTD / "driver_p2.log"
STATE_P = (HERE / "dry_run" if DRY else HERE) / "cl_b10_p2_state.json"
CELLS_P = (HERE / "dry_run" if DRY else HERE) / "cells.jsonl"
IMP_LOG = REPO / "logs/impairment.jsonl"
LADDER_LOG = REPO / "logs/games/adaptive_bitrate_shadow.jsonl"
LADDER_ARCH = LADDER_LOG.parent / "stream_log_archive" / (LADDER_LOG.name + ".1")   # G8-S3 read "archive/" (absent)
FRAMES_LOG = REPO / "logs/games/native_frame_sizes.jsonl"
FRAMES_ARCH = FRAMES_LOG.parent / "stream_log_archive" / (FRAMES_LOG.name + ".1")
HEARTBEAT = 30 if DRY else 300
WINDOW, GAP = 600, 120
BUSY_WAIT, BUSY_TRIES = 600, 3
SUITE_TIMEOUT = 2 * 3600
NCELLS = 1
PROPS = ("restart_guard", "stall_signal", "link_notice")
P1 = {"restart_guard": "1", "stall_signal": "1", "link_notice": "1"}
STACK = ["PRIVYHUB_INPUT_HOLD=1", "PRIVYHUB_INPUT_HOLD_B6=1", "PRIVYHUB_INPUT_HOLD_B8=1", "PRIVYHUB_INPUT_HOLD_REWIND=1",
         "PRIVYHUB_STALL_SIGNAL=1", "PRIVYHUB_STALL_RESUME=1"]
NONE = "none@post-fec,seed=1"
SNES = "E1-SNES-STREAM"
# the task's exact strings (G-A3_AND_CL-B10_TASK.md PART 2; CL-B10_PART2_ATTENDED_TASK.md): the drop-in is the impairment
# line only; snes9x (line 3) and the link report (line 9) are adopted
ALL_CELLS = [
    {"n": 1, "cell": "1_snes_5ghz_restart_guard", "spec": NONE, "profile": "none", "extra": [], "props": P1, "wid": SNES, "arm": "5 GHz, Home ~4 min", "window": 600},
    {"n": 4, "cell": "4_snes_24ghz_notice", "spec": NONE, "profile": "none", "extra": [], "props": P1, "wid": SNES, "arm": "2.4 GHz notice, back to 5 GHz ~10 min", "window": 780},
]
_N = int(sys.argv[sys.argv.index("--cell") + 1]) if "--cell" in sys.argv else None
CELLS = [c for c in ALL_CELLS if c["n"] == _N]
QUIET = ((4, 15), (5, 30))      # no cell starts in [04:15, 05:30) UTC: the nightly watch samples 04:30-05:30Z
OPAL_SH = HERE / "o1_opal_sample.sh"
OPAL_DIR = (HERE / "dry_run" / "opal") if "--dry" in sys.argv else (HERE / "opal")
OPAL_INTERVAL = 10 if "--dry" in sys.argv else 300
GAPD = HERE.parent / "b6_2026-10-22/gap_distribution.py"
B6_BINS, B6_EDGE_S = [250, 300, 400, 500, 600, 800, 1000, 1500], 10.0     # gap_distribution.py's BINS / EDGE_S
LINK_KEYS = ("link_rssi_dbm", "link_tx_mbps", "link_rx_mbps", "link_frequency_mhz", "link_wifi_standard")
GUARD_KEYS = ("frames_after_dropped_reference", "loss_guard_episodes", "loss_guard_frames_held")
RA_LINE = re.compile(r"state|slot|rewind|serializ", re.I)
LOGS_G = REPO / "logs/games"
COPIED = [("native_stream_heartbeat.log", "received_at_utc"), ("native_stream_ctrl_gaps.log", "start_utc"),
          ("native_stream_recovery.log", "at_utc"), ("native_frame_sizes.jsonl", "at_utc"),
          ("adaptive_bitrate_shadow.jsonl", "at_utc")]
UNATT = REPO / "tools/unattended_frames.py"
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
    return [f"PRIVYHUB_IMPAIRMENT={cell['spec']}"] + list(cell["extra"])


def props_read():
    """The three client properties, read back (getprop; values only, no device detail kept)."""
    return {pp: str(E1.adb("shell", "getprop", f"debug.privyhub.{pp}")).strip() for pp in PROPS}


def props_set(cell):
    """The cell's pre-registered properties (setprop), then all three read back."""
    for pp, v in cell["props"].items():
        E1.adb("shell", "setprop", f"debug.privyhub.{pp}", v)
    got = props_read()
    return got, all(got[pp] == cell["props"].get(pp, "") for pp in PROPS)


def props_after():
    """CL-B10: the properties are NOT cleared (PART 2 uses and clears them); read back, True when all still read 1."""
    got = props_read()
    return got, all(got[pp] == "1" for pp in PROPS)


WIFI_KEYS = {"Wi-Fi standard": "standard", "RSSI": "rssi_dbm", "Tx Link speed": "tx_mbps", "Rx Link speed": "rx_mbps",
             "Frequency": "freq_mhz"}


def band_read():
    """The onn's mWifiInfo line, parsed in memory; only frequency / band / standard / RSSI / tx / rx are kept."""
    try:
        line = subprocess.run(["adb", "shell", "dumpsys wifi | grep -m1 '^mWifiInfo'"], capture_output=True, text=True,
                              timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        line = ""
    r = {"at_utc": utc()}
    for k_, name in WIFI_KEYS.items():
        m_ = re.search(r"(?:^|, )" + re.escape(k_) + r": (-?\d+)", line)
        r[name] = int(m_.group(1)) if m_ else None
    f_ = r.get("freq_mhz")
    r["band"] = None if f_ is None else "5" if 4900 <= f_ < 5900 else "2.4" if 2400 <= f_ < 2500 else "6" if f_ >= 5925 else "?"
    return r


def band_thread(cdir, out):
    while not out.get("done") and not STOP.is_set():
        append(cdir / "band.jsonl", band_read())
        time.sleep(10)


def cell_span_s(cell):
    return GAP + 90 + cell.get("window", WINDOW) + 120       # gap, warmup, window, teardown margin


def watch_overlap(t, cell):
    """True when a cell started at t could still be running at 04:30Z, or would start before 05:30Z, on that day."""
    d = datetime.fromtimestamp(t, timezone.utc)
    a = d.replace(hour=4, minute=30, second=0, microsecond=0).timestamp()
    b = d.replace(hour=5, minute=30, second=0, microsecond=0).timestamp()
    return t < b and t + cell_span_s(cell) > a


def in_quiet(t=None):
    d = datetime.fromtimestamp(time.time() if t is None else t, timezone.utc)
    m = d.hour * 60 + d.minute
    return QUIET[0][0] * 60 + QUIET[0][1] <= m < QUIET[1][0] * 60 + QUIET[1][1]


def props_clear():
    """All three properties set empty, read back; True when all read empty."""
    for pp in PROPS:
        E1.adb("shell", "setprop", f"debug.privyhub.{pp}", "''")
    got = props_read()
    return got, all(v == "" for v in got.values())


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log(*a):
    line = f"[cl_b10_p2 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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
             "shim_packets_out", "shim_dropped_queue", "shim_queue_max", "dropped_blackout", "uplink_dropped", "lan_loss_rule_rows",
             "lan_loss_rule_first_utc", "recovery_events", "held_ms", "ctrl_gaps_ge250", "ctrl_gaps_ge1000", "unattended",
             "preflight_ok", "flags_absent_after", "final_flags_absent", "encoder_rc_seen", "encoder_cmd_sha256_seen",
             "encoder_cpu", "max_output_gap_ms", "audio_underruns", "audio_lost_packets", "spikes50", "frame_rows",
             "wid", "retroarch_cpu", "retroarch_rss_kb", "mem_available_mb_min", "unattended_net", "props_set", "props_set_ok",
             "props_after_empty", "link_rows", "rssi_median", "tx_mbps_median", "guard_counter_max", "guard_held_max",
             "silences_ge250_per_10min", "loaded_state_slot9", "opal_rounds"]


def write_status(**kw):
    """One line, rewritten (atomic replace of the driver's own status file) after every run, and every HEARTBEAT s by
    the heartbeat thread: a reader can tell idle from dead by the heartbeat's age."""
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | cell {s['cell']} (one per launch) | last: {s['last']} (at {s['last_at']}) | doing: {s['doing']} | "
                f"next: {s['next']} | state: {s['state']} | cap {CAP_UTC} | stop: touch ~/privyhub_cl_b10/STOP\n")
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
    """The nine-line adopted state (G-A3), read back: the suite's own preflight."""
    try:
        p = E1.preflight()
    except Exception as e:      # noqa: BLE001 -- a read failure is reported, not fatal
        return {"ok": False, "error": repr(e)[:200]}, "read failed"
    return p, ("adopted9 ok" if p.get("ok") else f"NOT ok (environ {len(p.get('environ') or [])} lines, game {p.get('game_active')})")


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


def masked_argv(argv):
    """E4-S5B's method on the live argv: argv[0], the device, the window, the display and the sink masked."""
    out = list(argv)
    if out:
        out[0] = "<ffmpeg>"
    for opt, tag in (("-vaapi_device", "<device>"), ("-window_id", "<window>"), ("-i", "<display>")):
        if opt in out and out.index(opt) + 1 < len(out):
            out[out.index(opt) + 1] = tag
    out = ["<sink>" if a.startswith("rtp://") else IP.sub("<redacted>", a) for a in out]
    return out


def encoder_cmd(pid):
    try:
        argv = open(f"/proc/{pid}/cmdline", "rb").read().decode(errors="replace").split("\0")
    except OSError:
        return None
    while argv and argv[-1] == "":
        argv.pop()
    m = masked_argv(argv)
    val = lambda opt: m[m.index(opt) + 1] if opt in m and m.index(opt) + 1 < len(m) else None
    return {"masked_argv": m, "masked_sha256": hashlib.sha256("\0".join(m).encode()).hexdigest(),
            "b_v": val("-b:v"), "maxrate": val("-maxrate"), "bufsize": val("-bufsize"), "rc_mode": val("-rc_mode")}


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
    pids_seen, pids_read = {}, set()
    while not out.get("done") and not STOP.is_set():
        now = time.time()
        for pid in E1.encoder_pids():
            pids_seen.setdefault(pid, now)
            if pid not in pids_read and now - pids_seen[pid] >= 3:
                pids_read.add(pid)
                c = encoder_cmd(pid)
                if c:
                    append(cdir / f"encoder_cmd_run{attempt}.jsonl", {"at_utc": utc(), "pid_n": len(pids_read), **c})
                    out.setdefault("encoder_cmds", []).append({k_: c[k_] for k_ in ("masked_sha256", "b_v", "maxrate", "bufsize", "rc_mode")})
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


def segments(rows):
    """G8-S1 §5's reading: stream starts split where t_s restarts."""
    segs, cur, last_t = [], [], None
    for r in rows:
        t = r.get("t_s") or 0
        if last_t is not None and t < last_t:
            segs.append(cur)
            cur = []
        cur.append(r)
        last_t = t
    segs.append(cur)
    return segs


def dark_spans(segs):
    """B1's blackout on the shim's per-second lines: per stream start, runs of lines carrying dropped_blackout
    (a gap of > 10 s starts a new span) -> [(segment, t_s first, t_s last, drops)]."""
    out = []
    for i, sg in enumerate(segs):
        cur = None
        for r in sg:
            if (r.get("dropped_blackout") or 0) > 0:
                t = r.get("t_s") or 0
                if cur and t - cur[2] <= 10:
                    cur[2], cur[3] = t, cur[3] + r["dropped_blackout"]
                else:
                    cur = [i, t, t, r["dropped_blackout"]]
                    out.append(cur)
    return [tuple(x) for x in out]


def applied(cell, rows):
    """G8-S1's tolerances (none / loss-1 / loss-5 / burst-50x20) and B1's blackout, read on the run's shim telemetry
    (per-second deltas). The blackout: >= 1 dark span; each span's lines within 3-6 s (4 s on 1-s lines); span starts
    120 +/- 3 s apart within a stream start; no other drop; uplink_dropped > 0 on @both, 0 on @down."""
    profile = cell["profile"]
    rows = [r for r in rows if r.get("profile") == profile and r.get("placement") == "post-fec" and r.get("seed") == 1]
    if not rows:
        return False, {"lines": 0}
    s = lambda key: sum(r.get(key) or 0 for r in rows)
    pin, pout = s("packets_in"), s("packets_out")
    dl, db, dq, de, ro = s("dropped_loss"), s("dropped_burst"), s("dropped_queue"), s("delayed"), s("reordered")
    dbk, up = s("dropped_blackout"), s("uplink_dropped")
    dur = max(r.get("t_s") or 0 for r in rows)
    segs = segments(rows)
    m = {"lines": len(rows), "duration_s": round(dur, 1), "packets_in": pin, "packets_out": pout, "dropped_loss": dl,
         "dropped_burst": db, "dropped_queue": dq, "delayed": de, "reordered": ro, "dropped_blackout": dbk,
         "uplink_dropped": up, "queue_max": max(r.get("queue_max") or 0 for r in rows),
         "shim_cpu_pct_core": round(100 * s("cpu_s") / dur, 3) if dur else None, "send_errors": s("send_errors"),
         "stream_starts": len(segs), "seconds_each": [round(max((r.get("t_s") or 0) for r in sg), 1) for sg in segs]}
    if pin <= 0:
        return False, m
    loss = dl / pin
    if profile == "none":
        ok = dl == db == dq == ro == dbk == up == 0 and de == 0
    elif profile in ("loss-1", "loss-5"):
        lo, hi = (0.007, 0.013) if profile == "loss-1" else (0.045, 0.055)
        ok = lo <= loss <= hi and db == dq == ro == dbk == up == 0
    elif profile == "burst-50x20":
        expect = int((dur - 10) // 20) + 1 if dur >= 10 else 0
        ok = db % 50 == 0 and abs(db // 50 - expect) <= 1 and dl == dq == ro == dbk == up == 0
        m["bursts"], m["bursts_expected"] = db // 50, expect
    elif profile == "blackout-4s":
        sp = dark_spans(segs)
        lens = [round(b - a + 1, 1) for _, a, b, _ in sp]
        apart = [round(sp[j][1] - sp[j - 1][1], 1) for j in range(1, len(sp)) if sp[j][0] == sp[j - 1][0]]
        m["dark_spans"] = [{"segment": g, "t_s_from": a, "t_s_to": b, "dropped": n} for g, a, b, n in sp]
        m["dark_span_lines_s"], m["dark_span_starts_apart_s"] = lens, apart
        uplink_ok = up > 0 if cell.get("uplink") else up == 0
        ok = (bool(sp) and all(3 <= x <= 6 for x in lens) and all(117 <= x <= 123 for x in apart)
              and dl == db == dq == ro == 0 and uplink_ok)
    else:
        ok = False
    m["loss_frac"] = round(loss, 5)
    m["blackout_frac"] = round(dbk / pin, 5)
    return bool(ok), m


# ---------------------------------------------------------------- running the suite
def suite(out, cell, timeout_s):
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "suite_console.log", "a") as fh:
        p = subprocess.Popen([sys.executable, str(CALL), str(out), str(cell.get("window", WINDOW)), str(GAP), cell["wid"], *kvs(cell)], stdout=fh,
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
            "companion_cpu": hh("procs.companion.cpu_pct"), "encoder_cpu": hh("procs.encoder.cpu_pct"),
            "retroarch_cpu": hh("procs.retroarch.cpu_pct"), "retroarch_rss_kb": hh("procs.retroarch.rss_kb"),
            "retroarch_rss_kb_max": k(s, "host", "host", "procs.retroarch.rss_kb", "max"), "mem_available_mb": hh("mem.available_mb"),
            "mem_available_mb_min": k(s, "host", "host", "mem.available_mb", "min"),
            "max_output_gap_ms": rf.get("max_output_gap_ms"), "audio_underruns": rf.get("audio.underruns"),
            "audio_underruns_heartbeat": k(s, "key", "heartbeat", "audio_underruns"), "audio_lost_packets": rf.get("audio.lost_packets"),
            "spikes50": rf.get("decoder.spike_50_ms"), "spikes80": rf.get("decoder.spike_80_ms"),
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
    lan = [r for r in rows if r.get("event") == "lan_loss_rule"]
    return {"lan_loss_rule_rows": len(lan), "lan_loss_rule_first_utc": lan[0].get("at_utc") if lan else None,
            "lan_loss_rule_results": sorted({str(r.get("result")) for r in lan}),
            "rows": len(rows), "samples": sum(1 for r in rows if r.get("event") == "sample"), "start_rungs": starts,
            "transitions": trans, "rules_by_id": rules, "refused": sum(1 for r in rows if r.get("event") == "refused"),
            "rung_path": "→".join(str(x) for x in path) if path else None}


def ts_utc(v):
    try:
        v = str(v).rstrip("Z")
        return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%f" if "." in v else "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
    except ValueError:
        return None


def logs_copy(t0, t1, dest):
    """The five logs over [t0 - 1, t1 + 1] (the live file and its newest stream_log_archive/*.1, by their own UTC key,
    de-duplicated, addresses masked) into dest/ under their own names -> {name: rows}."""
    dest.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, key in COPIED:
        rows = {}
        for src in (LOGS_G / "stream_log_archive" / (name + ".1"), LOGS_G / name):
            try:
                with open(src) as fh:
                    for l in fh:
                        try:
                            d = json.loads(l)
                        except ValueError:
                            continue
                        t = ts_utc(d.get(key)) if isinstance(d, dict) else None
                        if t is not None and t0 - 1 <= t <= t1 + 1:
                            rows[(d.get(key), json.dumps(d, sort_keys=True))] = d
            except OSError:
                pass
        with open(dest / name, "w") as fh:
            for kk in sorted(rows):
                fh.write(json.dumps(scrub(rows[kk])[0], sort_keys=True) + "\n")
        counts[name] = len(rows)
    return counts


def jl(p):
    out = []
    try:
        for l in open(p):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def run_readings(ldir, t0, t1, cdir, attempt):
    """The recovery rows by event (+ trigger), the control gaps, B2's reader over the run's span."""
    rec = {}
    for r in jl(ldir / "native_stream_recovery.log"):
        ev = r.get("event")
        key = f"{ev}:{r.get('trigger')}" if ev == "desync_pause" else (f"{ev}:{r.get('via')}" if ev == "resumed" and r.get("via") else ev)
        rec[key] = rec.get(key, 0) + 1
    held = [r.get("held_ms") for r in jl(ldir / "native_stream_recovery.log") if r.get("held_ms") is not None]
    gaps = [r.get("gap_ms") or 0 for r in jl(ldir / "native_stream_ctrl_gaps.log")]
    ua = cdir / f"unattended_run{attempt}.json"
    try:
        subprocess.run([sys.executable, "-B", str(UNATT), "--logs", str(ldir), "--span", utc(t0)[:19], utc(t1)[:19],
                        "--json", str(ua)], capture_output=True, timeout=300, cwd=str(REPO))
        u = load_json(ua) or {}
    except (OSError, subprocess.SubprocessError) as e:
        u = {"error": repr(e)[:120]}
    un = cdir / f"unattended_net_run{attempt}.json"
    try:
        subprocess.run([sys.executable, "-B", str(UNATT), "--logs", str(ldir), "--span", utc(t0)[:19], utc(t1)[:19], "--net",
                        "--json", str(un)], capture_output=True, timeout=300, cwd=str(REPO))
        un_ = load_json(un) or {}
    except (OSError, subprocess.SubprocessError) as e:
        un_ = {"error": repr(e)[:120]}
    return {"unattended_net": {x: v for x, v in un_.items() if not isinstance(v, (list, dict)) or x == "held_episodes"},
            "recovery_events": rec, "held_ms": held, "ctrl_gaps_ge250": sum(1 for g in gaps if g >= 250),
            "ctrl_gaps_ge1000": sum(1 for g in gaps if g >= 1000), "ctrl_gap_max_ms": max(gaps) if gaps else None,
            "unattended": {x: u.get(x) for x in ("streaming_s", "gaps", "episodes", "unattended_frames",
                                                 "unattended_frames_per_10min", "unattended_frames_core_running",
                                                 "unattended_frames_core_running_per_10min", "held_episodes", "error")
                           if x in u}}


def med(xs):
    xs = sorted(x for x in xs if isinstance(x, (int, float)))
    return (xs[len(xs) // 2] if len(xs) % 2 else (xs[len(xs) // 2 - 1] + xs[len(xs) // 2]) / 2) if xs else None


def link_reading(ldir):
    """The link report's keys per heartbeat (B3): how many rows carry them, RSSI / tx / rx summaries, the bands seen; and
    the loss guard's heartbeat counters (B10), max per cell (cumulative per client session)."""
    hb = jl(ldir / "native_stream_heartbeat.log")
    lk = [r for r in hb if any(x in r for x in LINK_KEYS)]
    col = lambda x: [r.get(x) for r in lk if isinstance(r.get(x), (int, float))]
    out = {"heartbeat_rows": len(hb), "link_rows": len(lk), "link_keys_seen": sorted({x for r in lk for x in LINK_KEYS if x in r}),
           "rssi_median": med(col("link_rssi_dbm")), "rssi_min": min(col("link_rssi_dbm"), default=None),
           "rssi_max": max(col("link_rssi_dbm"), default=None),
           "tx_mbps_median": med(col("link_tx_mbps")), "tx_mbps_min": min(col("link_tx_mbps"), default=None),
           "rx_mbps_median": med(col("link_rx_mbps")), "rx_mbps_min": min(col("link_rx_mbps"), default=None),
           "frequencies_mhz": sorted(set(col("link_frequency_mhz"))), "wifi_standards": sorted(set(col("link_wifi_standard")))}
    gk = [r for r in hb if any(x in r for x in GUARD_KEYS)]
    out["guard_rows"] = len(gk)
    for x in GUARD_KEYS:
        out[f"{x}_max"] = max((r.get(x) for r in gk if isinstance(r.get(x), (int, float))), default=None)
    return out


def silences(ldir):
    """The uplink silences >= 250 ms with B6's gap_distribution.py bins, B6's edge rule (gaps starting within 10 s of the
    first / last heartbeat of the cell's copy excluded), per 10 min of that span."""
    hb = [ts_utc(r.get("received_at_utc")) for r in jl(ldir / "native_stream_heartbeat.log")]
    hb = [x for x in hb if x is not None]
    if len(hb) < 2:
        return {"span_s": 0}
    a, b = min(hb) + B6_EDGE_S, max(hb) - B6_EDGE_S
    g = [(r.get("gap_ms") or 0) for r in jl(ldir / "native_stream_ctrl_gaps.log")
         if (t := ts_utc(r.get("start_utc"))) is not None and a <= t <= b and (r.get("gap_ms") or 0) >= 250]
    span = max(b - a, 1.0)
    bins = {f">={lo}": sum(1 for x in g if x >= lo) for lo in B6_BINS}
    return {"span_s": round(span, 1), "ge250": len(g), "ge250_per_10min": round(len(g) * 600 / span, 2),
            "ge500_per_10min": round(bins[">=500"] * 600 / span, 2), "bins": bins, "max_ms": max(g, default=None)}


def opal_rounds(t0, t1):
    n = 0
    for r in jl(OPAL_DIR / "air.jsonl"):
        t = ts_utc(r.get("at_utc"))
        n += 1 if t is not None and t0 <= t <= t1 else 0
    return n


def retroarch_lines(t0, t1, dest):
    """RetroArch's own session logs (logs/games/<stamp>-<game>.log) written during the cell: only the lines on state /
    slot / rewind / serialization kept, scrubbed; counts of "Loaded state from slot #9" and the rewind buffer's line."""
    keep = []
    for f in sorted(LOGS_G.glob("2*-*.log")):
        try:
            if f.stat().st_mtime < t0:
                continue
            for l in open(f, errors="replace"):
                if RA_LINE.search(l):
                    keep.append(l.rstrip("\n"))
        except OSError:
            pass
    keep = [IP.sub("<redacted>", l) for l in keep]
    dest.write_text("\n".join(keep) + ("\n" if keep else ""))
    return {"lines": len(keep), "loaded_state_slot9": sum(1 for l in keep if "Loaded state from slot #9" in l),
            "state_failed": sum(1 for l in keep if "state" in l.lower() and ("fail" in l.lower() or "error" in l.lower())),
            "rewind_buffer": sum(1 for l in keep if "rewind buffer" in l.lower())}


def opal_start():
    """The O1 sampler (read-only on the Opal), every OPAL_INTERVAL s, into OPAL_DIR/air.jsonl; its own stderr logged."""
    OPAL_DIR.mkdir(parents=True, exist_ok=True)
    out = OPAL_DIR / "air.jsonl"
    return subprocess.Popen(["bash", str(OPAL_SH), str(out), str(OPAL_INTERVAL), "wlan1"], stdout=subprocess.DEVNULL,
                            stderr=open(OPAL_DIR / "opal_sampler.log", "a"), cwd=str(HERE))


def opal_stop(proc, wait_s):
    """Its own stop file (a new file; nothing deleted), then waited out (the loop checks it after each sleep)."""
    Path(str(OPAL_DIR / "air.jsonl") + ".stop").touch()
    try:
        proc.wait(timeout=wait_s)
        return f"exited {proc.returncode}"
    except subprocess.TimeoutExpired:
        proc.terminate()
        return "terminated after the wait"


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
    wdir = cdir / f"{cell['wid']}_flag"
    before = latest_run(wdir)
    imp_start, lad_off = imp_lines(), ladder_offset()
    t = time.time()
    write_status(cell=cell["n"], doing=f"cell {cell['n']} {cell['spec']} {cell['arm']} (attempt {attempt}, "
                                       f"started {utc(t)[11:16]}Z)", next="-")
    beside = {}
    th = threading.Thread(target=beside_run, args=(cell, cdir, imp_start, beside, attempt), daemon=True)
    cdir.mkdir(parents=True, exist_ok=True)
    threading.Thread(target=band_thread, args=(cdir, beside), daemon=True).start()
    pr_set, pr_set_ok = props_set(cell)
    log(f"cell {cell['n']}: properties set {pr_set} ok {pr_set_ok}")
    th.start()
    suite(cdir, cell, SUITE_TIMEOUT)
    beside["done"] = True
    th.join(timeout=30)
    pr_end, pr_end_ok = props_after()
    log(f"cell {cell['n']}: properties after (not cleared) {pr_end} still 1 {pr_end_ok}")
    t_end = time.time()
    rd = latest_run(wdir)
    s = load_json(rd / "summary.json") if rd and rd != before else None
    f = figures(s, rd)
    rows = imp_read(imp_start)
    with open(cdir / f"impairment_run{attempt}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    ok, m = applied(cell, rows)
    lrows, rotated = ladder_read(lad_off)
    lad = ladder_reading(lrows, f.get("window"))
    jr = journal_read(t, t_end, cdir / f"companion_journal_run{attempt}.txt")
    ldir = cdir / f"logs_run{attempt}"
    copied = logs_copy(t, t_end, ldir)
    nframes = copied.get("native_frame_sizes.jsonl")
    rr = run_readings(ldir, t, t_end, cdir, attempt)
    lr, sil = link_reading(ldir), silences(ldir)
    ra = retroarch_lines(t, t_end, cdir / f"retroarch_lines_run{attempt}.txt")
    opr = opal_rounds(t, t_end)
    cmds = beside.get("encoder_cmds") or []
    final = load_json(cdir / "final_state.json") or {}
    fails = failed_attempts(rd)
    outcome = "playing" if f["status"] == "OK" else "no_play"
    absent = bool(f["flags_absent_after"]) and bool(final.get("flags_absent")) and all(a.get("flags_absent") for a in fails)
    validity = ("valid" if ok and absent else "profile-not-applied" if absent else "invalid (flags_absent not true)")
    if not pr_end_ok:
        validity = "invalid (the properties did not read back 1 after the cell)"
    elif not pr_set_ok and validity == "valid":
        validity = "properties-not-set"
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
           "shim_steady_in_kbps": m.get("steady_in_kbps_median"), "shim_steady_drop_frac": m.get("steady_drop_frac"),
           "encoder_cmds": cmds, "encoder_rc_seen": sorted({f"{c['b_v']}/{c['maxrate']}/{c['bufsize']}/{c['rc_mode']}" for c in cmds}),
           "encoder_cmd_sha256_seen": sorted({c["masked_sha256"][:12] for c in cmds}), "frame_rows": nframes,
           "logs_copied": copied, **rr, "lan_loss_rule_rows": lad["lan_loss_rule_rows"],
           "lan_loss_rule_first_utc": lad["lan_loss_rule_first_utc"], "dark_spans": m.get("dark_spans"),
           "dropped_blackout": m.get("dropped_blackout"), "uplink_dropped": m.get("uplink_dropped"),
           "props_set": pr_set, "props_set_ok": pr_set_ok, "props_after": pr_end, "props_after_still_1": pr_end_ok,
           "link": lr, "link_rows": lr["link_rows"], "rssi_median": lr["rssi_median"], "tx_mbps_median": lr["tx_mbps_median"],
           "guard_counter_max": lr["frames_after_dropped_reference_max"], "guard_held_max": lr["loss_guard_frames_held_max"],
           "silences": sil, "silences_ge250_per_10min": sil.get("ge250_per_10min"), "retroarch_log": ra,
           "loaded_state_slot9": ra["loaded_state_slot9"], "opal_rounds": opr}
    append(CELLS_P, row)
    hist_append(row)
    log(f"cell {cell['n']} {cell['spec']} {cell['arm']} attempt {attempt}: {f['status']} {outcome} {validity} "
        f"recovery {rr['recovery_events']} gaps>=250 {rr['ctrl_gaps_ge250']} unattended {rr['unattended']} "
        f"lan_rule {lad['lan_loss_rule_rows']} dark {len(m.get('dark_spans') or [])} uplink_dropped {m.get('uplink_dropped')} "
        f"start {st0.get('kbps')} ({st0.get('source')}) wire {bits} enc {bv} path {lad['rung_path']} "
        f"loss {f['loss_per_min']} rendered {f['rendered_fps']} class {wc} enc_rc {row['encoder_rc_seen']} frames {nframes} "
        f"shim in {m.get('steady_in_kbps_median')} drop {m.get('steady_drop_frac')} gates {row['host_gates_met']} "
        f"flags_at_stream {beside.get('flags_at_stream')} flags_under_load {beside.get('flags_under_load')} "
        f"flags_absent {f['flags_absent_after']}/{final.get('flags_absent')} link_rows {lr['link_rows']}/{lr['heartbeat_rows']} "
        f"rssi {lr['rssi_median']} tx {lr['tx_mbps_median']} silences/10min {sil.get('ge250_per_10min')} "
        f"guard {lr['frames_after_dropped_reference_max']}/{lr['loss_guard_frames_held_max']} slot9 {ra['loaded_state_slot9']} opal {opr}")
    return row


def dry():
    """--dry: about 2 min, no stream (see the module docstring)."""
    (HERE / "dry_run").mkdir(exist_ok=True)
    p, sline = adopted_state()
    log("dry: start; preflight", json.dumps(p), "| busy", bool(p.get("game_active")), "| stop file present", stop_requested())
    cell = CELLS[0]                  # cell 2: blackout@both on SNES + the stack with state and stall resume; the three properties
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
    rec["props_set"], rec["props_set_ok"] = props_set(cell)
    log("dry: properties set", rec["props_set"], "ok", rec["props_set_ok"])
    t0 = time.time()
    while time.time() - t0 < 30 and not stop_requested():
        time.sleep(5)
    td = {}
    E1.teardown_flags({"dropin": kvs(cell)}, td)
    rec["teardown"] = td
    rec["props_after"], rec["props_after_still_1"] = props_after()
    log("dry: properties read back (not cleared)", rec["props_after"], "still 1", rec["props_after_still_1"])
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
    return 0 if (rec["environ_has_all"] and td.get("flags_absent") and rec["props_set_ok"] and rec["props_after_still_1"]) else 1


def main():
    if DRY:
        return dry()
    if len(CELLS) != 1:
        print("refusing: --cell 1 or --cell 4")
        return 2
    WATCH.mkdir(parents=True, exist_ok=True)
    st = json.loads(STATE_P.read_text()) if STATE_P.exists() else {"done": {}, "started_utc": utc()}
    p, sline = adopted_state()
    st.setdefault("preflight_at_start", []).append({"at_utc": utc(), **p})
    jdump(STATE_P, st)
    st.setdefault("props_at_start", []).append(props_read())
    log("start; cells done", len(st["done"]), "| adopted state", sline, "| cap", CAP_UTC, "| properties", st["props_at_start"][-1])
    write_status(cell=len(st["done"]), state=sline, doing="starting")
    threading.Thread(target=heartbeat_thread, daemon=True).start()
    why = f"all {NCELLS} cells done"
    op = None
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
        if watch_overlap(time.time(), cell):
            why = "refused: the cell would overlap the nightly watch's 04:30-05:30Z; launch it after 05:30Z"
            log(f"cell {cell['n']}: {why}")
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
        write_status(cell=cell["n"], last=(f"cell {cell['n']} {cell['spec']} {cell['arm']}: {row['outcome']} {row['validity']} "
                                           f"start {row.get('start_rung_kbps')} ({row.get('start_rung_source')}) wire {row.get('wire_bitrate_kbps_seen')} "
                                           f"path {row.get('rung_path')} loss/min {row.get('loss_per_min')} rendered {row.get('rendered_fps')} "
                                           f"lan_rule {row.get('lan_loss_rule_rows')} recovery {row.get('recovery_events')} "
                                           f"unattended_core {(row.get('unattended') or {}).get('unattended_frames_core_running')} class {row.get('wan_class')}"),
                     last_at=utc(), state=sline, doing="idle",
                     next=(f"cell {nxt['n']} {nxt['spec']} {nxt['arm']} now (~{utc(time.time() + 60)[11:16]}Z)" if nxt else "-"))
        if row["validity"].startswith("invalid"):
            why = f"a state violation ({row['validity']})"
            log(f"cell {cell['n']}: STATE VIOLATION -- {row['validity']}; the driver ends")
            break
    if op is not None:
        st["opal_stop"] = opal_stop(op, OPAL_INTERVAL + 60)
        st["opal_rounds"] = len(jl(OPAL_DIR / "air.jsonl"))
        log("the Opal sampler", st["opal_stop"], "rounds", st["opal_rounds"])
    st["props_at_close"], st["props_at_close_still_1"] = props_after()
    log("close: properties (left for PART 2)", st["props_at_close"], "still 1", st["props_at_close_still_1"])
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
