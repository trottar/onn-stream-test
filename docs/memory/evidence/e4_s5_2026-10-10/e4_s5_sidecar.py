#!/usr/bin/env python3
"""E4-S5 §2 sidecar, run beside tools/e1_suite.py for the three SNES sessions (and the flagged runs). For every new
encoder (ffmpeg h264_vaapi) it records: x11grab's probed input rate (tbr) and the encoder's output rate, from the
session header in logs/games/native_video_alpha.log; and, 100 s after the encoder starts (inside the window), the
RetroArch window's own update rate -- a second x11grab of the same window at 120 fps for 60 s into framemd5,
distinct consecutive frames counted per second (the R3c method). The window id is read from the encoder's command
line and never written. Stops when <out>/sidecar.stop exists. -> <out>/sidecar.jsonl

    e4_s5_sidecar.py <out>"""
import collections
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
LOG = os.path.join(REPO, "logs/games/native_video_alpha.log")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def encoders():
    out = {}
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                if open(f"/proc/{d}/comm").read().strip() != "ffmpeg":
                    continue
                cmd = open(f"/proc/{d}/cmdline", "rb").read().split(b"\0")
            except OSError:
                continue
            if b"h264_vaapi" in cmd and b"-window_id" in cmd:
                out[int(d)] = cmd
    return out


def header_after(offset):
    """The first encoder session header written after byte offset: input tbr, output fps, the output -r if any."""
    with open(LOG, "rb") as fh:
        fh.seek(offset)
        b = fh.read(200000).decode("utf-8", "replace")
    i = re.search(r"Stream #0:0: Video: rawvideo[^\n]*", b)
    o = re.search(r"Stream #0:0: Video: h264[^\n]*", b)
    t = re.search(r"Window title: RetroArch (\S+)", b)
    return {"core": t.group(1) if t else None,
            "input_tbr": (re.search(r"([\d.k]+) tbr", i.group(0)).group(1) if i else None),
            "input_size": (re.search(r"(\d+x\d+)", i.group(0)).group(1) if i else None),
            "output_fps": (re.search(r"([\d.]+) fps", o.group(0)).group(1) if o else None)}


def distinct_per_second(text):
    """framemd5: stream, dts, pts, duration, size, hash; the time base from its '#tb 0:' header."""
    tb = 1e-6
    m = re.search(r"#tb 0: (\d+)/(\d+)", text)
    if m:
        tb = int(m.group(1)) / int(m.group(2))
    per, last, frames, first = collections.Counter(), None, 0, None
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = [x.strip() for x in line.split(",")]
        if len(p) < 6:
            continue
        frames += 1
        t = int(p[2]) * tb
        first = t if first is None else first
        if p[5] != last:
            per[int(t - first)] += 1
        last = p[5]
    secs = [per[s] for s in sorted(per)][1:-1]          # whole seconds only
    return {"frames_captured": frames, "distinct_per_s": secs,
            "distinct_mean": round(sum(secs) / len(secs), 3) if secs else None,
            "distinct_min": min(secs, default=None), "distinct_max": max(secs, default=None)}


def main(out):
    os.makedirs(out, exist_ok=True)
    seen = set()
    off = os.path.getsize(LOG)
    with open(os.path.join(out, "sidecar.jsonl"), "a") as fh:
        def w(row):
            row["at_utc"] = utc()
            fh.write(json.dumps(row) + "\n")
            fh.flush()
        w({"event": "sidecar_start"})
        while not os.path.exists(os.path.join(out, "sidecar.stop")):
            enc = encoders()
            for pid, cmd in enc.items():
                if pid in seen:
                    continue
                seen.add(pid)
                t_start = time.time()
                time.sleep(8)
                h = header_after(off)
                off = os.path.getsize(LOG)
                rate = cmd[cmd.index(b"-r") + 1].decode() if b"-r" in cmd else None
                w({"event": "encoder_start", "output_r_arg": rate, **h})
                # the window's own update rate, inside the window (the suite's warm-up is 90 s from PLAYING)
                while time.time() - t_start < 100 and pid in encoders():
                    time.sleep(2)
                if pid not in encoders():
                    w({"event": "encoder_gone_before_framemd5"})
                    continue
                wid = cmd[cmd.index(b"-window_id") + 1]
                t0 = utc()
                r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-f", "x11grab",
                                    "-framerate", "120", "-window_id", wid.decode(), "-i", ":0", "-t", "60",
                                    "-f", "framemd5", "-"], capture_output=True, text=True, timeout=150)
                w({"event": "framemd5", "from_utc": t0, "returncode": r.returncode, **distinct_per_second(r.stdout)})
            time.sleep(3)
        w({"event": "sidecar_stop"})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
