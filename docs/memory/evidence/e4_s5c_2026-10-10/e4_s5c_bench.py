#!/usr/bin/env python3
"""E4-S5C -- E4-S5B's bench (e4_s5b_2026-10-10/e4_s5b_bench.py) byte for byte except the sink, which is now in
constant-frame-rate mode (-fps_mode cfr: the mode ffmpeg picks by default for the companion's rtp muxer; E4-S5B's
-f null without it was pass-through and could not drop). ffmpeg 7.1.5 has -fps_mode, so that form is used.

E4-S5B's docstring follows, the sink sentence updated.

The SNES capture fix on bad probes: a bench of 60-s encoder sessions beside one live E1-SNES-STREAM.

Each session is the encoder command EXACTLY as the companion builds it: companion/native_stream.py's
NativeStreamManager._build_linux_ffmpeg_command, on an instance carrying only the adopted profile (its own
_apply_profile_selection), with PRIVYHUB_SNES_CAPTURE_FIX set (arm B) or unset (arm A) in this process's environment at
build time -- nothing retyped. Only the sink is changed: the command's last five arguments (`-payload_type 96 -f rtp
rtp://127.0.0.1:<fec port>...`) become `-fps_mode cfr -t 60 -f null -`, so nothing reaches the companion's FEC relay or the network.
The capture target is the live RetroArch window, read from the companion's own encoder's command line (/proc) and
never written; the display is the user manager's.

Per session (bench.jsonl): arm, flag, the built command's sha256 (with the window id masked) and whether it carries an
output -r, the header's probed input tbr, the output rate, the final frame / dup / drop counters, wall time, the
session's own CPU seconds (rusage), the exit code. Arms interleave A B A B ...; `--per-arm N` sessions each.
Stops early (recorded) if the live encoder disappears or <out>/bench.stop exists.

    e4_s5c_bench.py <out_dir> --per-arm 24 [--start-index 0]

The first invocation (--start-index 0) runs one 5-s CHECK session first (arm A, index -1, never counted): the header
and the stats line must parse, or the bench stops before any counted session.
"""
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))
import native_stream  # noqa: E402  (the companion's own module; nothing in it is changed)

FLAG = "PRIVYHUB_SNES_CAPTURE_FIX"
SESSION_S = 60


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def live_encoder():
    """(pid, window id, display) of the companion's own x11grab encoder, or None."""
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            if open(f"/proc/{d}/comm").read().strip() != "ffmpeg":
                continue
            cmd = open(f"/proc/{d}/cmdline", "rb").read().split(b"\0")
        except OSError:
            continue
        if b"h264_vaapi" in cmd and b"-window_id" in cmd and b"rtp" in cmd:
            return int(d), cmd[cmd.index(b"-window_id") + 1].decode(), cmd[cmd.index(b"-i") + 1].decode()
    return None


def manager():
    m = object.__new__(native_stream.NativeStreamManager)
    m.project_root = REPO
    m._log_handle = None
    m._apply_profile_selection()          # the adopted profile (PRIVYHUB_NATIVE_PROFILE_ID unset)
    return m


def build(m, arm, wid, secs=SESSION_S):
    if arm == "B":
        os.environ[FLAG] = "output_rate"
    else:
        os.environ.pop(FLAG, None)
    try:
        cmd = m._build_linux_ffmpeg_command(ffmpeg=m._find_ffmpeg(), capture_target={"_window_id": int(wid)})
    finally:
        os.environ.pop(FLAG, None)
    masked = [("<window>" if a == str(wid) else a) for a in cmd]
    tail = cmd[-5:]
    if not (tail[0] == "-payload_type" and tail[2:4] == ["-f", "rtp"] and tail[4].startswith("rtp://127.0.0.1:")):
        raise SystemExit(f"refusing: the built command does not end in the rtp sink: {masked[-5:]}")
    return cmd[:-5] + ["-fps_mode", "cfr", "-t", str(secs), "-f", "null", "-"], masked   # E4-S5C: the sink in cfr mode


def parse(err):
    i = re.search(r"Stream #0:0: Video: rawvideo[^\n]*", err)
    o = re.search(r"Stream #0:0: Video: h264[^\n]*", err)
    tbr = re.search(r"([\d.k]+) tbr", i.group(0)).group(1) if i else None
    fps = re.search(r"([\d.]+) fps", o.group(0)).group(1) if o else None
    stats = re.findall(r"frame=\s*(\d+)[^\r\n]*", err)
    last = re.findall(r"frame=\s*\d+[^\r\n]*", err)
    line = last[-1] if last else ""
    dup = re.search(r"dup=\s*(\d+)", line)
    drop = re.search(r"drop=\s*(\d+)", line)
    # ffmpeg prints dup= / drop= only once either is non-zero: absent in the final line = 0
    return {"input_tbr": tbr, "output_fps": fps, "frames": int(stats[-1]) if stats else None,
            "dup": int(dup.group(1)) if dup else 0, "drop": int(drop.group(1)) if drop else 0,
            "stats_line_seen": bool(line)}


def main(argv):
    out = Path(argv[0])
    per_arm = int(argv[argv.index("--per-arm") + 1])
    start = int(argv[argv.index("--start-index") + 1]) if "--start-index" in argv else 0
    out.mkdir(parents=True, exist_ok=True)
    m = manager()
    with open(out / "bench.jsonl", "a") as fh:
        def w(row):
            row.setdefault("at_utc", utc())
            fh.write(json.dumps(row) + "\n")
            fh.flush()
        enc = live_encoder()
        w({"event": "bench_start", "per_arm": per_arm, "start_index": start, "session_s": SESSION_S,
           "live_encoder": bool(enc), "profile": m.PROFILE.id, "fps": m.FPS})
        if not enc:
            w({"event": "bench_stop", "why": "no live encoder"})
            return 1
        os.environ["DISPLAY"] = enc[2]
        if start == 0:
            cmd, masked = build(m, "A", enc[1], 5)
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            chk = parse(p.stderr)
            ok = p.returncode == 0 and chk["input_tbr"] and chk["output_fps"] and chk["stats_line_seen"]
            w({"event": "check_session", "index": -1, "arm": "A", "rc": p.returncode, "ok": bool(ok), **chk})
            if not ok:
                w({"event": "bench_stop", "why": "the check session did not parse",
                   "stderr_tail": [l.replace(enc[1], "<window>")[:200] for l in p.stderr.splitlines()[-6:]]})
                return 2
            time.sleep(5)
        for n in range(start, start + 2 * per_arm):
            arm = "AB"[n % 2]
            if (out / "bench.stop").exists():
                w({"event": "bench_stop", "why": "bench.stop"})
                return 0
            enc = live_encoder()
            if not enc:
                w({"event": "bench_stop", "why": "the live encoder is gone", "index": n})
                return 1
            cmd, masked = build(m, arm, enc[1])
            ru0 = resource.getrusage(resource.RUSAGE_CHILDREN)
            t0, a0 = time.time(), utc()
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=SESSION_S + 60)
                rc, err = p.returncode, p.stderr
            except subprocess.TimeoutExpired as e:
                rc, err = "timeout", (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
            wall = time.time() - t0
            ru1 = resource.getrusage(resource.RUSAGE_CHILDREN)
            row = {"event": "session", "index": n, "arm": arm, "flag": arm == "B", "start_utc": a0, "end_utc": utc(),
                   "wall_s": round(wall, 2), "rc": rc,
                   "cpu_s": round((ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime), 3),
                   "built_sha256_masked": hashlib.sha256(" ".join(masked).encode()).hexdigest(),
                   "built_has_output_r": "-r" in masked[masked.index("-i"):],
                   "companion_encoder_same": live_encoder() is not None and live_encoder()[0] == enc[0],
                   **parse(err)}
            if rc != 0:
                row["stderr_tail"] = [l.replace(enc[1], "<window>")[:200] for l in err.splitlines()[-4:]]
            w(row)
            time.sleep(5)
        w({"event": "bench_done"})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
