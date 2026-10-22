#!/usr/bin/env python3
"""BENCH-R2 -- the Wi-Fi lock A/B, the clean cells with the whole stack, the blackout cells with the hold + B6 + rewind +
the stall signal, the loss cells with the bidirectional rule, and the per-core rewind CPU rows: fifteen cells run as
pre-registered (bench_r2_preregistration.txt), DETACHED (systemd --user unit privyhub-bench-r2), the cap read from the
pre-registration's `CAP_UTC:` line (launch + 5 h); resumable from bench_r2_state.json.

Built from bench_r1_driver.py's scaffolding (kept: the status line / heartbeat / history / STOP / busy skip / cap / the
suite call with its timeout and SIGINT / the crash handler / --dry / the readings beside a run / the encoder read-back /
the applied check (G8-S1's tolerances + B1's blackout) / the per-run log copies (heartbeat, control gaps, recovery, frame
sizes, ladder) / B2's reader / no_play as an outcome / the profile-not-applied repeat / the state stop). Changed:
  - the cells table (fifteen, in the pre-registered order; session B's exact strings, SESSION_B_DONE_2026-10-22C.md items
    8-9), each with its workload (E1-PS1-STREAM, or E1-SNES-STREAM on the f rows marked SNES) passed to the wrapper;
  - the client properties per cell: `adb shell setprop debug.privyhub.<p> <v>` before the suite (which force-stops the
    app and starts a new stream activity that reads them), read back with getprop; after the cell all three
    (wifi_lock, stall_signal, link_report) set empty and read back empty -- a cell that does not read back empty ends the
    driver (the state stop); adb's only writes besides the install;
  - added to each row: RetroArch's CPU % and RSS (procs.retroarch.*), the host's available memory, B2's reader with
    --net (B4) beside the plain count, the property read-backs.
--dry: about 2 min, no stream: the preflight, cell b1's drop-in (six lines) written, the companion restarted, its environ
read back (fourteen lines), b1's properties set and read back, 30 s held, the drop-in removed, restarted, flags_absent
read, the properties cleared and read back empty; then exit."""
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
CALL = HERE / "bench_r2_suite_call.py"
JREAD = HERE.parent / "g8_s1_2026-10-16/g8_s1_cap_log_read.py"
PRE = HERE / "bench_r2_preregistration.txt"
WATCH = Path.home() / "privyhub_bench_r2"
RUNS = HERE / "runs"


def _cap_from_pre():
    """The cap is written in the pre-registration (`CAP_UTC: <iso>Z`, launch + 5 h); none -> no cell starts."""
    try:
        for line in PRE.read_text().splitlines():
            if line.strip().startswith("CAP_UTC:"):
                v = line.split(":", 1)[1].strip()
                return v, datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()
    except (OSError, ValueError):
        pass
    return "unset", 0.0


CAP_UTC, CAP = _cap_from_pre()
DRY = "--dry" in sys.argv
STOPFILE = WATCH / "STOP"
OUTD = HERE / "dry_run" if DRY else WATCH
STATUS_P, HIST_P, WLOG_P = OUTD / "status.txt", OUTD / "history.csv", OUTD / "driver.log"
STATE_P = (HERE / "dry_run" if DRY else HERE) / "bench_r2_state.json"
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
NCELLS = 15
PROPS = ("wifi_lock", "stall_signal", "link_report")
STACK = ["PRIVYHUB_INPUT_HOLD=1", "PRIVYHUB_INPUT_HOLD_B6=1", "PRIVYHUB_INPUT_HOLD_REWIND=1", "PRIVYHUB_STALL_SIGNAL=1"]
HOLD3 = ["PRIVYHUB_INPUT_HOLD=1", "PRIVYHUB_INPUT_HOLD_B6=1", "PRIVYHUB_INPUT_HOLD_REWIND=1"]
NONE, BOTH, DOWN = "none@post-fec,seed=1", "blackout-4s@both,every=120s,seed=1", "blackout-4s@down,every=120s,seed=1"
LL = {"wifi_lock": "low_latency"}
LLS = {"wifi_lock": "low_latency", "stall_signal": "1"}
PS1, SNES = "E1-PS1-STREAM", "E1-SNES-STREAM"
# session B's exact strings (SESSION_B_DONE_2026-10-22C.md items 8-9); a blackout spec takes NO @post-fec
CELLS = [
    {"n": 1, "cell": "a1_lock_none", "spec": NONE, "profile": "none", "extra": [], "props": {}, "wid": PS1, "arm": "lock none"},
    {"n": 2, "cell": "a2_lock_low_latency", "spec": NONE, "profile": "none", "extra": [], "props": LL, "wid": PS1, "arm": "lock low_latency"},
    {"n": 3, "cell": "a3_lock_high_perf", "spec": NONE, "profile": "none", "extra": [], "props": {"wifi_lock": "high_perf"}, "wid": PS1, "arm": "lock high_perf"},
    {"n": 4, "cell": "d1_clean_stack", "spec": NONE, "profile": "none", "extra": STACK, "props": LLS, "wid": PS1, "arm": "stack"},
    {"n": 5, "cell": "d2_clean_stack_stall400", "spec": NONE, "profile": "none", "extra": STACK[:3] + ["PRIVYHUB_STALL_SIGNAL=400"], "props": LLS, "wid": PS1, "arm": "stack, stall 400"},
    {"n": 6, "cell": "b1_blackout_both_stack", "spec": BOTH, "profile": "blackout-4s", "uplink": True, "extra": STACK, "props": LLS, "wid": PS1, "arm": "stack"},
    {"n": 7, "cell": "b2_blackout_both_no_stall", "spec": BOTH, "profile": "blackout-4s", "uplink": True, "extra": HOLD3, "props": LL, "wid": PS1, "arm": "hold+B6+rewind"},
    {"n": 8, "cell": "c1_blackout_down_stack", "spec": DOWN, "profile": "blackout-4s", "uplink": False, "extra": STACK, "props": LLS, "wid": PS1, "arm": "stack"},
    {"n": 9, "cell": "e1_loss-1_bidir", "spec": "loss-1@post-fec,seed=1", "profile": "loss-1", "extra": ["PRIVYHUB_LAN_LOSS_RULE=bidir"], "props": LL, "wid": PS1, "arm": "bidir"},
    {"n": 10, "cell": "e2_loss-5_bidir", "spec": "loss-5@post-fec,seed=1", "profile": "loss-5", "extra": ["PRIVYHUB_LAN_LOSS_RULE=bidir"], "props": LL, "wid": PS1, "arm": "bidir"},
    {"n": 11, "cell": "e3_burst-50x20_bidir", "spec": "burst-50x20@post-fec,seed=1", "profile": "burst-50x20", "extra": ["PRIVYHUB_LAN_LOSS_RULE=bidir"], "props": LL, "wid": PS1, "arm": "bidir"},
    {"n": 12, "cell": "f1_snes9x_rewind_off", "spec": NONE, "profile": "none", "extra": [], "props": LL, "wid": SNES, "arm": "rewind off"},
    {"n": 13, "cell": "f2_snes9x_rewind_on", "spec": NONE, "profile": "none", "extra": ["PRIVYHUB_INPUT_HOLD=1", "PRIVYHUB_INPUT_HOLD_REWIND=1", "PRIVYHUB_INPUT_HOLD_B6=1"], "props": LL, "wid": SNES, "arm": "rewind on"},
    {"n": 14, "cell": "f3_psx_hw_rewind_off", "spec": NONE, "profile": "none", "extra": [], "props": LL, "wid": PS1, "arm": "rewind off"},
    {"n": 15, "cell": "f4_psx_hw_rewind_on", "spec": NONE, "profile": "none", "extra": ["PRIVYHUB_INPUT_HOLD=1", "PRIVYHUB_INPUT_HOLD_REWIND=1", "PRIVYHUB_INPUT_HOLD_B6=1"], "props": LL, "wid": PS1, "arm": "rewind on"},
]
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
    return ["PRIVYHUB_WAN_TELEMETRY=1", f"PRIVYHUB_IMPAIRMENT={cell['spec']}"] + list(cell["extra"])


def props_read():
    """The three client properties, read back (getprop; values only, no device detail kept)."""
    return {pp: str(E1.adb("shell", "getprop", f"debug.privyhub.{pp}")).strip() for pp in PROPS}


def props_set(cell):
    """The cell's pre-registered properties (setprop), then all three read back."""
    for pp, v in cell["props"].items():
        E1.adb("shell", "setprop", f"debug.privyhub.{pp}", v)
    got = props_read()
    return got, all(got[pp] == cell["props"].get(pp, "") for pp in PROPS)


def props_clear():
    """All three properties set empty, read back; True when all read empty."""
    for pp in PROPS:
        E1.adb("shell", "setprop", f"debug.privyhub.{pp}", "''")
    got = props_read()
    return got, all(v == "" for v in got.values())


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def log(*a):
    line = f"[benchr2 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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
             "props_after_empty"]


def write_status(**kw):
    """One line, rewritten (atomic replace of the driver's own status file) after every run, and every HEARTBEAT s by
    the heartbeat thread: a reader can tell idle from dead by the heartbeat's age."""
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | cell {s['cell']}/{NCELLS} | last: {s['last']} (at {s['last_at']}) | doing: {s['doing']} | "
                f"next: {s['next']} | state: {s['state']} | cap {CAP_UTC} | stop: touch ~/privyhub_bench_r2/STOP\n")
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
    """The eight-line adopted state (G-A2), read back: the suite's own preflight."""
    try:
        p = E1.preflight()
    except Exception as e:      # noqa: BLE001 -- a read failure is reported, not fatal
        return {"ok": False, "error": repr(e)[:200]}, "read failed"
    return p, ("adopted8 ok" if p.get("ok") else f"NOT ok (environ {len(p.get('environ') or [])} lines, game {p.get('game_active')})")


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
        p = subprocess.Popen([sys.executable, str(CALL), str(out), str(WINDOW), str(GAP), cell["wid"], *kvs(cell)], stdout=fh,
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
    write_status(cell=cell["n"], doing=f"cell {cell['n']}/{NCELLS} {cell['spec']} {cell['arm']} (attempt {attempt}, "
                                       f"started {utc(t)[11:16]}Z)", next="-")
    beside = {}
    th = threading.Thread(target=beside_run, args=(cell, cdir, imp_start, beside, attempt), daemon=True)
    cdir.mkdir(parents=True, exist_ok=True)
    pr_set, pr_set_ok = props_set(cell)
    log(f"cell {cell['n']}: properties set {pr_set} ok {pr_set_ok}")
    th.start()
    suite(cdir, cell, SUITE_TIMEOUT)
    beside["done"] = True
    th.join(timeout=30)
    pr_end, pr_end_ok = props_clear()
    log(f"cell {cell['n']}: properties cleared {pr_end} empty {pr_end_ok}")
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
    cmds = beside.get("encoder_cmds") or []
    final = load_json(cdir / "final_state.json") or {}
    fails = failed_attempts(rd)
    outcome = "playing" if f["status"] == "OK" else "no_play"
    absent = bool(f["flags_absent_after"]) and bool(final.get("flags_absent")) and all(a.get("flags_absent") for a in fails)
    validity = ("valid" if ok and absent else "profile-not-applied" if absent else "invalid (flags_absent not true)")
    if not pr_end_ok:
        validity = "invalid (the properties did not read back empty)"
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
           "props_set": pr_set, "props_set_ok": pr_set_ok, "props_after": pr_end, "props_after_empty": pr_end_ok}
    append(CELLS_P, row)
    hist_append(row)
    log(f"cell {cell['n']} {cell['spec']} {cell['arm']} attempt {attempt}: {f['status']} {outcome} {validity} "
        f"recovery {rr['recovery_events']} gaps>=250 {rr['ctrl_gaps_ge250']} unattended {rr['unattended']} "
        f"lan_rule {lad['lan_loss_rule_rows']} dark {len(m.get('dark_spans') or [])} uplink_dropped {m.get('uplink_dropped')} "
        f"start {st0.get('kbps')} ({st0.get('source')}) wire {bits} enc {bv} path {lad['rung_path']} "
        f"loss {f['loss_per_min']} rendered {f['rendered_fps']} class {wc} enc_rc {row['encoder_rc_seen']} frames {nframes} "
        f"shim in {m.get('steady_in_kbps_median')} drop {m.get('steady_drop_frac')} gates {row['host_gates_met']} "
        f"flags_at_stream {beside.get('flags_at_stream')} flags_under_load {beside.get('flags_under_load')} "
        f"flags_absent {f['flags_absent_after']}/{final.get('flags_absent')}")
    return row


def dry():
    """--dry: about 2 min, no stream (see the module docstring)."""
    (HERE / "dry_run").mkdir(exist_ok=True)
    p, sline = adopted_state()
    log("dry: start; preflight", json.dumps(p), "| busy", bool(p.get("game_active")), "| stop file present", stop_requested())
    cell = CELLS[5]                  # b1: blackout@both + the whole stack (six lines) and its two properties
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
    rec["props_after"], rec["props_after_empty"] = props_clear()
    log("dry: properties cleared", rec["props_after"], "empty", rec["props_after_empty"])
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
    return 0 if rec["environ_has_all"] and td.get("flags_absent") and rec["props_set_ok"] and rec["props_after_empty"] else 1


def main():
    if DRY:
        return dry()
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
    st["props_at_close"], st["props_at_close_empty"] = props_clear()
    log("close: properties", st["props_at_close"], "empty", st["props_at_close_empty"])
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
