#!/usr/bin/env python3
"""E1-S1 -- the Phase E workload suite runner (the frozen definition: docs/memory/architecture/E1_WORKLOAD_SUITE.md).

    e1_suite.py --list
    e1_suite.py run --out <dir> --prereg <e1_preregistration.txt> [--only ID[,ID]] [--runs 2] [--window 300] [--gap 120]
    e1_suite.py compare <dir>          the repeatability table (run 1 vs run 2 per workload) -> repeatability.{json,md}
    e1_suite.py manifest <dir>         sha256 of every file in <dir> -> <dir>/manifest.sha256
    e1_suite.py --check <dir>          manifest intact; every run has a summary with a full window
    e1_suite.py --self-test

One command, no hands. Per run: preflight (no PRIVYHUB_* in the user manager, the companion's environ exactly the
live default, no game, adb), the row's flags (1080p row only), a unit restart (MainPID owns 8765), the idle gap
(>= 120 s), launch, warm-up, the 300-s window, teardown to idle, checks. The sampler (tools/e1_sampler.py) runs
from the gap to the end of the teardown; the summary is over the window (and, separately, the gap).

Reuses C5's harness pieces (evidence/c5_close_2026-10-05/c5_m5_run.sh, c5_close_hold.sh; tools/d7_regression.py):
the launcher's now_playing_preview_host tap, NativeStreamActivity, recovery PLAYING, BACK and the decoder report,
POST stop, the NOW PLAYING banner check and clear, the APK hash, the counter-only game override, the adopted PS1
files' hashes, flags set in the user manager and unset on every exit path.

Writes only under <dir>, plus (removed on every exit path) the counter override in the RetroArch config tree and
the onn's /sdcard/e1s1.xml dump. Never runs nft or sudo; never touches the Opal.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "http://localhost:8765"
UNIT = "privyhub-companion"
PKG = "com.safeiot.privyhub"
EXPECT_APK = "de072762e55122c3060086f6f10b1bff54633d9165d0c475f17699127841835e"
LIVE = "PRIVYHUB_ADAPTIVE_BITRATE_MODE=live"
FLAG_NAMES = ["PRIVYHUB_ADAPTIVE_BITRATE_INJECT", "PRIVYHUB_ADAPTIVE_BITRATE_TOP", "PRIVYHUB_PS1_LOOK",
              "PRIVYHUB_NATIVE_PROFILE_ID", "PRIVYHUB_FEC_SCHEME"]
RA_CFG = Path.home() / ".config/retroarch/config"
# E3: a run's flag lives in this drop-in for that run only (written before its restart, removed + daemon-reload +
# restart at its teardown); the adopted adaptive.conf beside it is never touched
DROPIN = Path.home() / ".config/systemd/user" / f"privyhub-companion.service.d" / "e3_flag.conf"
PS1_DIR = RA_CFG / "Beetle PSX HW"
PS1_SHA = REPO / "docs/memory/evidence/c5_close_2026-10-05/adopted_ps1_sha256.txt"
INPUT_CFG = REPO / "data/games/retroarch/config/privyhub-input.cfg"
SESSDIR = REPO / "logs/games/decoder_sessions"
HB_LIVE = REPO / "logs/games/native_stream_heartbeat.log"
HB_ARCH = REPO / "logs/games/stream_log_archive"
COUNTER = 'fps_show = "true"\nframecount_show = "true"\nmenu_enable_widgets = "false"\nvideo_font_enable = "false"\n'
EPG_CHANNELS = ["ComedyCentral.us@East", "CNBCUK.uk@SD", "10Bold.au@Sydney", "FoxSports1.us@HD", "NBC.us@East",
                "FilmBox.nl@Netherlands"]

VOD_FILE = "movies/Edge Of Tomorrow.mp4"     # the E1-VOD fixed file (720x360 H.264 ~0.92 Mbps, 113 min)
VOD_TITLE = "Edge Of Tomorrow"
VOD_PATH = ["VOD", "MOVIES", VOD_TITLE]       # the launcher's tiles, tapped in order
ABR_LOG = REPO / "logs/games/adaptive_bitrate_shadow.jsonl"

TEKKEN = {"id": "game_ps1_b0a5986638f61a11", "override": PS1_DIR / "Tekken 3 (USA).cfg"}
# E3-S4: RetroArch's per-core config dir is the core's corename (its .info); the counter override follows the core
SNES_CORENAMES = {"snes9x": "Snes9x", "snes9x2010": "Snes9x 2010", "snes9x2005_plus": "Snes9x 2005 Plus"}
SMW = {"id": "game_snes_c6fecdcdddb35398", "override": RA_CFG / "bsnes" / "Super Mario World (USA).cfg"}

# The suite, as pre-registered (e1_preregistration.txt). kind: idle | local | stream | meta
WORKLOADS = [
    {"id": "E1-IDLE", "kind": "idle", "warmup": 60, "main": "companion"},
    {"id": "E1-PS1-LOCAL", "kind": "local", "game": TEKKEN, "warmup": 60, "main": "retroarch"},
    {"id": "E1-SNES-STREAM", "kind": "stream", "game": SMW, "warmup": 90, "main": "retroarch"},
    {"id": "E1-PS1-STREAM", "kind": "stream", "game": TEKKEN, "warmup": 90, "main": "retroarch"},
    {"id": "E1-PS1-1080P", "kind": "stream", "game": TEKKEN, "warmup": 60, "main": "retroarch", "rung": True,
     "flags": ["PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p", "PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1"]},
    {"id": "E1-META", "kind": "meta", "warmup": 60, "main": "companion"},
    {"id": "E1-CONC", "kind": "stream", "game": TEKKEN, "warmup": 90, "main": "retroarch", "epg_at": 30},
    # amended 2026-10-05 (E2-S1 §1): the VOD row, the drive attached
    {"id": "E1-VOD", "kind": "vod", "warmup": 60, "main": "range_server"},
]
ABSENT = {
    "E1-LIVETV": "Live TV: no unattended channel start (no intent/extra/deep link; video is upstream -> onn)",
    "E1-BROWSER": "browser source: Windows-only (PowerShell/ddagrab); no Linux implementation",
    "E1-CAMERA": "camera source: Windows-only (dshow); no camera attached (no /dev/video*)",
    "E1-NES": "NES: no fixture (games/nes empty)",
    "E1-GENESIS": "Genesis: no fixture (games/genesis empty)",
    "E1-META-RECONCILE": "metadata reconcile: writes library metadata (outside E1's no-change rule)",
}
BAR = {"cpu_points": 2.0, "gpu_points": 3.0, "rss_frac": 0.05, "fps_abs": 0.5, "grab_frac": 0.30, "vod_ratio_abs": 0.01}


def _load_sampler():
    spec = importlib.util.spec_from_file_location("e1_sampler", REPO / "tools/e1_sampler.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


S = _load_sampler()
utc = S.utc


# ---------------------------------------------------------------- plumbing
class Log:
    def __init__(self, path: Path | None):
        self.path = path

    def __call__(self, *a):
        line = f"[e1 {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
        print(line, flush=True)
        if self.path:
            with open(self.path, "a") as fh:
                fh.write(line + "\n")


log = Log(None)


def sh(cmd: list, timeout: float = 30) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as exc:  # noqa: BLE001
        return f"__error__ {type(exc).__name__}"


def adb(*args, timeout: float = 20) -> str:
    return sh(["adb", *args], timeout)


def http(method: str, path: str, timeout: float = 30):
    req = urllib.request.Request(BASE + path, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            try:
                return r.status, json.loads(body or b"{}")
            except ValueError:
                return r.status, {}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}
    except Exception as e:  # noqa: BLE001
        return None, {"error": type(e).__name__}


def games_status() -> dict:
    return http("GET", "/plugins/games/status", 10)[1]


def stream_status() -> dict:
    return http("GET", "/plugins/games/native-stream-status", 10)[1]


def mainpid() -> int | None:
    v = sh(["systemctl", "--user", "show", "-p", "MainPID", "--value", UNIT]).strip()
    return int(v) if v.isdigit() and v != "0" else None


def serving_pid() -> int | None:
    m = re.search(r":8765 .*?pid=(\d+),", sh(["ss", "-lntp"]))
    return int(m.group(1)) if m else None


def manager_flags() -> list:
    return sorted(l for l in sh(["systemctl", "--user", "show-environment"]).splitlines() if l.startswith("PRIVYHUB_"))


def environ_flags(pid: int | None) -> list:
    if not pid:
        return []
    try:
        raw = open(f"/proc/{pid}/environ", "rb").read().decode(errors="replace")
    except OSError:
        return []
    return sorted(l for l in raw.split("\0") if l.startswith("PRIVYHUB_"))


def restart_unit() -> dict:
    sh(["systemctl", "--user", "restart", UNIT], 60)
    for _ in range(40):
        if serving_pid():
            break
        time.sleep(1)
    time.sleep(2)
    mp, sp = mainpid(), serving_pid()
    return {"mainpid_serves_8765": bool(mp and mp == sp), "manager": manager_flags(), "environ": environ_flags(mp)}


def comm_pids(names: set) -> list:
    out = []
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                if open(f"/proc/{d}/comm").read().strip() in names:
                    out.append(int(d))
            except OSError:
                pass
    return out


def retroarch_pids() -> list:
    return comm_pids({"retroarch", "RetroArch-Linux"})


def encoder_pids() -> list:
    out = []
    for p in comm_pids({"ffmpeg"}):
        try:
            if b"h264_vaapi" in open(f"/proc/{p}/cmdline", "rb").read():
                out.append(p)
        except OSError:
            pass
    return out


def stop_game() -> bool:
    http("POST", "/plugins/games/stop", 30)
    for _ in range(25):
        time.sleep(1)
        if games_status().get("active") is False:
            return True
    return False


def ps1_files_identical() -> bool:
    r = subprocess.run(["sha256sum", "-c", "--quiet", str(PS1_SHA)], cwd=PS1_DIR, capture_output=True, text=True)
    return r.returncode == 0


def apk_hash() -> str | None:
    p = adb("shell", "pm", "path", PKG).strip().replace("package:", "")
    if not p or p.startswith("__error__"):
        return None
    out = adb("shell", "sha256sum", p).split()
    return out[0] if out else None


# ---------------------------------------------------------------- the onn (C5's path)
def ui_nodes() -> list:
    adb("shell", "uiautomator", "dump", "/sdcard/e1s1.xml")
    xml = adb("shell", "cat", "/sdcard/e1s1.xml")
    out = []
    for m in re.finditer(r"<node [^>]*>", xml):
        n = m.group(0)
        rid = re.search(r' resource-id="([^"]*)"', n)
        text = re.search(r' text="([^"]*)"', n)
        b = re.search(r' bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        rid_s = (rid.group(1) if rid else "").split("/")[-1]
        if rid_s == "status_text":   # carries an address; never kept
            continue
        if b:
            x1, y1, x2, y2 = map(int, b.groups())
            out.append((text.group(1) if text else "", rid_s, ((x1 + x2) // 2, (y1 + y2) // 2)))
    return out


def top_activity() -> str:
    m = re.search(r"topResumedActivity=.*", adb("shell", "dumpsys", "activity", "activities"))
    return m.group(0) if m else ""


def open_stream() -> dict:
    for attempt in (1, 2):
        adb("shell", "am", "force-stop", PKG)
        adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
        time.sleep(7)
        hit = [c for t, r, c in ui_nodes() if r == "now_playing_preview_host"]
        if hit:
            x, y = hit[0]
            adb("shell", "input", "tap", str(x), str(y))
            time.sleep(3)
            if "NativeStreamActivity" in top_activity():
                t0 = time.time()
                while time.time() - t0 < 45:
                    if (games_status().get("recovery") or {}).get("state") == "PLAYING":
                        return {"ok": True, "attempt": attempt, "s_to_playing": round(time.time() - t0, 1)}
                    time.sleep(1)
    return {"ok": False, "recovery": (games_status().get("recovery") or {}).get("state")}


def banner_clear() -> dict:
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
    time.sleep(6)
    np = sum(1 for t, r, c in ui_nodes() if "NOW PLAYING" in t.upper() or r == "now_playing_preview_host")
    out = {"now_playing_before": np}
    if np:
        adb("shell", "am", "force-stop", PKG)
        time.sleep(1)
        adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
        time.sleep(7)
        out["now_playing_after_relaunch"] = sum(1 for t, r, c in ui_nodes()
                                                if "NOW PLAYING" in t.upper() or r == "now_playing_preview_host")
    adb("shell", "rm", "-f", "/sdcard/e1s1.xml")
    return out


def back_and_report(before: set) -> str | None:
    adb("shell", "input", "keyevent", "KEYCODE_BACK")
    for _ in range(30):
        time.sleep(1)
        new = sorted(set(os.listdir(SESSDIR)) - before)
        if new:
            return new[-1]
    return None


REPORT_PATHS = ["duration_ms", "video.lost_packets", "video.sequence_resyncs", "video.recent_fps",
                "decoder.spike_20_ms", "decoder.spike_50_ms", "decoder.spike_80_ms", "decoder.stale_output_drops",
                "decoder.max_output_gap_ms", "audio.lost_packets", "audio.underruns"]


def report_fields(name: str | None) -> dict:
    if not name:
        return {}
    try:
        d = json.loads((SESSDIR / name).read_text(errors="replace"))
    except (OSError, ValueError):
        return {"unreadable": True}
    rep = d.get("report") if isinstance(d.get("report"), dict) else d
    paths = {}
    for pth in REPORT_PATHS:
        x = rep
        for k in pth.split("."):
            x = x.get(k) if isinstance(x, dict) else None
        if isinstance(x, (int, float)):
            paths[pth] = x
    keys = ("session_duration_ms", "max_output_gap_ms", "rendered_frames", "lost_packets", "stale_output_drops",
            "audio_underruns", "slow_event_retained", "slow_event_capacity")
    out = {}

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k in keys and isinstance(v, (int, float)) and k not in out:
                    out[k] = v
                walk(v)
    walk(d)
    out.update(paths)
    return out


# ---------------------------------------------------------------- VOD on the onn (E1-VOD)
def _tap_text(pattern: str, tries: int = 3) -> bool:
    for _ in range(tries):
        for t, r, c in ui_nodes():
            if re.match(pattern, t.replace("&gt;", ">").strip(), re.I):
                adb("shell", "input", "tap", str(c[0]), str(c[1]))
                time.sleep(3)
                return True
        time.sleep(2)
    return False


def _tap_id(rid: str) -> bool:
    for t, r, c in ui_nodes():
        if r == rid:
            adb("shell", "input", "tap", str(c[0]), str(c[1]))
            time.sleep(2)
            return True
    return False


def vod_progress() -> tuple:
    """(position s, wall epoch) from the launcher's now_playing_progress text ("M:SS / H:MM:SS")."""
    for t, r, c in ui_nodes():
        if r == "now_playing_progress":
            pos = t.split("/")[0].strip()
            secs = 0
            for part in pos.split(":"):
                secs = secs * 60 + int(part)
            return secs, time.time()
    return None, time.time()


def vod_start() -> dict:
    out = {}
    adb("shell", "am", "force-stop", PKG)
    adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
    adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
    time.sleep(7)
    for name in VOD_PATH[:-1]:
        if not _tap_text(rf"^{name}\s*>"):
            return {"ok": False, "step": name}
    if not _tap_text(rf"^{re.escape(VOD_TITLE)}$"):
        return {"ok": False, "step": VOD_TITLE}
    time.sleep(2)
    nodes = ui_nodes()
    if any(r == "message" and t.startswith("Resume from") for t, r, c in nodes):
        out["resume_dialog"] = [t for t, r, c in nodes if r == "message"][0]
        _tap_text(r"^Start Over$")                            # the app's own "play from the start"
    time.sleep(6)
    titles = [t for t, r, c in ui_nodes() if r == "now_playing_title"]
    out["now_playing"] = titles[:1]
    if titles[:1] != [VOD_TITLE]:
        return dict(out, ok=False, step="now_playing")
    out["restart_tapped"] = _tap_id("button_restart")        # from 0:00 every run (the app resumes otherwise)
    time.sleep(3)
    out["p0"], out["t0"] = vod_progress()
    _tap_id("now_playing_preview_host")                       # fullscreen
    time.sleep(2)
    out["fullscreen"] = any(r == "fullscreen_player_host" for t, r, c in ui_nodes())
    out["ok"] = out["p0"] is not None and out["fullscreen"]
    return out


def vod_end(start: dict) -> dict:
    adb("shell", "input", "keyevent", "KEYCODE_BACK")          # leaves fullscreen; playback continues in the preview
    time.sleep(2)
    p1, t1 = vod_progress()
    out = {"p1": p1, "t1": t1}
    if p1 is not None and start.get("p0") is not None:
        wall = t1 - start["t0"]
        played = p1 - start["p0"]
        out.update({"wall_s": round(wall, 1), "played_s": played, "progress_ratio": round(played / wall, 4),
                    "stall_s_per_min": round(max(0.0, wall - played) / (wall / 60), 3)})
    return out


def vod_teardown() -> dict:
    out = {"restart_tapped": _tap_id("button_restart")}     # clears the saved position, so the onn keeps ~0
    time.sleep(1)
    out["stop_tapped"] = _tap_id("button_stop")              # STOP: POST /stop
    time.sleep(3)
    out["now_playing_left"] = sum(1 for t, r, c in ui_nodes() if r.startswith("now_playing"))
    adb("shell", "rm", "-f", "/sdcard/e1s1.xml")
    return out


def vod_mount() -> dict:
    root = json.loads((REPO / "data/storage.json").read_text()).get("vod_root", "")
    f = Path(root) / VOD_FILE
    lines = [l.split() for l in sh(["findmnt", "-n", "-T", str(f), "-o", "FSTYPE,OPTIONS"]).splitlines() if l.strip()]
    real = [l for l in lines if l and l[0] != "autofs"]       # the autofs trigger is listed above the real mount
    fm = real[-1] if real else (lines[-1] if lines else [])
    return {"file_present": f.exists(), "size_bytes": f.stat().st_size if f.exists() else None,
            "fstype": fm[0] if fm else None, "read_only": len(fm) > 1 and fm[1].split(",")[0] == "ro"}


# ---------------------------------------------------------------- RetroArch's own command port (local row)
def ra_command(cmd: str, expect: bool) -> str | None:
    m = re.search(r'network_cmd_port = "(\d+)"', INPUT_CFG.read_text())
    if not m:
        return None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(1.5)
    try:
        s.sendto(cmd.encode(), ("127.0.0.1", int(m.group(1))))
        if expect:
            return s.recv(4096).decode(errors="replace").strip()
        return ""
    except OSError:
        return None
    finally:
        s.close()


def ra_unpause() -> dict:
    st = None
    for _ in range(3):
        st = ra_command("GET_STATUS", True)
        if st and st.upper().startswith("GET_STATUS PLAYING"):
            return {"ok": True, "status": "PLAYING"}
        if st and st.upper().startswith("GET_STATUS PAUSED"):
            ra_command("PAUSE_TOGGLE", False)
            time.sleep(1.0)
            continue
        time.sleep(1.0)
    st = ra_command("GET_STATUS", True)
    return {"ok": bool(st and st.upper().startswith("GET_STATUS PLAYING")), "status": (st or "")[:40]}


# ---------------------------------------------------------------- workload telemetry threads
class Poller(threading.Thread):
    """native-stream-status every 10 s: size, bitrate, level (the 1080p precondition and the ladder level)."""

    def __init__(self, path: Path, stop: threading.Event):
        super().__init__(daemon=True)
        self.path, self.stop = path, stop

    def run(self):
        with open(self.path, "w") as fh:
            while not self.stop.is_set():
                d = stream_status()
                a = d.get("adaptive_bitrate") or {}
                fh.write(json.dumps({"at_utc": utc(), "width": d.get("width"), "height": d.get("height"),
                                     "bitrate_kbps": d.get("bitrate_kbps"), "level_size": a.get("level_size"),
                                     "mode": a.get("mode"), "active": d.get("active")}) + "\n")
                fh.flush()
                self.stop.wait(10)


class EpgCycle(threading.Thread):
    """The E1-META grab cycle: forced refreshes over the fixed list, in order, until stopped; plus the library
    scan (GET /plugins/games/games) every 30 s on its own timer."""

    def __init__(self, path: Path, stop: threading.Event):
        super().__init__(daemon=True)
        self.path, self.stop = path, stop
        self.fh = open(path, "w")
        self.lock = threading.Lock()

    def write(self, row):
        with self.lock:
            self.fh.write(json.dumps(row) + "\n")
            self.fh.flush()

    def scans(self):
        while not self.stop.wait(30):
            t0 = time.time()
            code, d = http("GET", "/plugins/games/games", 60)
            self.write({"kind": "scan", "start_utc": utc(t0), "end_utc": utc(), "s": round(time.time() - t0, 3),
                        "http": code, "count": len(d.get("games") or []) if isinstance(d, dict) else None})

    def run(self):
        threading.Thread(target=self.scans, daemon=True).start()
        i = 0
        while not self.stop.is_set():
            ch = EPG_CHANNELS[i % len(EPG_CHANNELS)]
            t0 = time.time()
            code, d = http("POST", f"/plugins/epg/refresh?channel_id={urllib.parse.quote(ch)}", 150)
            self.write({"kind": "grab", "channel": ch, "start_utc": utc(t0), "end_utc": utc(),
                        "s": round(time.time() - t0, 3), "http": code, "ok": bool(d.get("ok")),
                        "programmes": d.get("programme_count"), "cached": d.get("cached")})
            i += 1
        self.fh.close()


# ---------------------------------------------------------------- key figures
def decision_rows(t0: str, t1: str) -> list:
    rows = []
    for f in (HB_ARCH / (ABR_LOG.name + ".1"), ABR_LOG):
        if f.exists():
            for line in f.read_text(errors="replace").splitlines()[-30000:]:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if t0 <= r.get("at_utc", "") <= t1:
                    rows.append(r)
    return rows


def heartbeat_figures(t0: str, t1: str) -> dict:
    files = sorted(HB_ARCH.glob("native_stream_heartbeat.log*")) + [HB_LIVE]
    rows, seen = [], set()
    for f in files:
        if not f.exists():
            continue
        for line in f.read_text(errors="replace").splitlines()[-20000:]:
            if line in seen:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if "lost_packets" in r and t0 <= r.get("received_at_utc", "") <= t1:
                seen.add(line)
                rows.append(r)
    rows.sort(key=lambda r: r["received_at_utc"])
    if len(rows) < 2:
        return {"heartbeats": len(rows)}
    frames = ms = lost = au = ra = 0
    segs = 1
    for a, b in zip(rows, rows[1:]):
        if b["elapsed_ms"] <= a["elapsed_ms"] or b["rendered_frames"] < a["rendered_frames"]:
            segs += 1      # a new session (restart): skip the boundary
            continue
        frames += b["rendered_frames"] - a["rendered_frames"]
        ms += b["elapsed_ms"] - a["elapsed_ms"]
        lost += b["lost_packets"] - a["lost_packets"]
        au += b.get("audio_underruns", 0) - a.get("audio_underruns", 0)
        ra += b.get("stream_resyncs", 0) - a.get("stream_resyncs", 0)
    mins = ms / 60000 if ms else None
    return {"heartbeats": len(rows), "segments": segs, "span_s": round(ms / 1000, 1),
            "rendered_fps": round(frames / (ms / 1000), 3) if ms else None,
            "video_loss_per_min": round(lost / mins, 2) if mins else None,
            "audio_underruns": au, "stream_resyncs": ra,
            "max_last_output_age_ms": max(r.get("last_output_age_ms", 0) for r in rows)}


def telemetry_figures(path: Path, t0: str, t1: str) -> dict:
    seen, rows = set(), []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("fresh") and t0 <= r["at_utc"] <= t1 and r.get("elapsed_ms") not in seen:
                seen.add(r.get("elapsed_ms"))
                rows.append(r)
    if not rows:
        return {"reports": 0}
    gap = [((r.get("latency") or {}).get("output_gap_ms")) for r in rows]
    rtt = [((r.get("latency") or {}).get("control_round_trip_ms")) for r in rows]
    r2d = [((r.get("latency") or {}).get("receive_to_decode_ms")) for r in rows]
    lost = sum(((r.get("receiver") or {}).get("lost_packets_delta") or 0) for r in rows)
    span = (rows[-1]["elapsed_ms"] - rows[0]["elapsed_ms"]) / 60000 if len(rows) > 1 else None
    num = lambda xs: [x for x in xs if isinstance(x, (int, float))]
    return {"reports": len(rows), "output_gap_ms_max": max(num(gap), default=None),
            "control_rtt_ms_median": statistics.median(num(rtt)) if num(rtt) else None,
            "receive_to_decode_ms_median": statistics.median(num(r2d)) if num(r2d) else None,
            "receiver_lost_packets_per_min": round(lost / span, 2) if span else None}


def poll_figures(path: Path, t0: str, t1: str) -> dict:
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if t0 <= r["at_utc"] <= t1:
                rows.append(r)
    if not rows:
        return {"reads": 0}
    sizes = [f"{r.get('width')}x{r.get('height')}" for r in rows]
    rates = [r.get("bitrate_kbps") for r in rows]
    return {"reads": len(rows), "frac_1920x1080": round(sizes.count("1920x1080") / len(rows), 3),
            "frac_1280x720": round(sizes.count("1280x720") / len(rows), 3),
            "bitrate_kbps_min": min((x for x in rates if x), default=None),
            "bitrate_kbps_max": max((x for x in rates if x), default=None)}


def epg_figures(path: Path, t0: str, t1: str) -> dict:
    grabs, scans = [], []
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if not (t0 <= r["start_utc"] and r["end_utc"] <= t1):
                continue
            (grabs if r["kind"] == "grab" else scans).append(r)
    ok = [g["s"] for g in grabs if g["ok"]]
    return {"grabs_in_window": len(grabs), "grabs_ok": len(ok), "grabs_failed": len(grabs) - len(ok),
            "grab_s_median": round(statistics.median(ok), 3) if ok else None,
            "grab_s_max": max(ok, default=None),
            "scans": len(scans), "scan_s_median": round(statistics.median([s["s"] for s in scans]), 4) if scans else None}


# ---------------------------------------------------------------- one run
def preflight() -> dict:
    mp = mainpid()
    d = {"manager": manager_flags(), "environ": environ_flags(mp), "game_active": games_status().get("active"),
         "adb": any(l.endswith("\tdevice") for l in adb("devices").splitlines()[1:]),
         "drop_in_live": f"Environment={LIVE}" in sh(["systemctl", "--user", "cat", UNIT]),
         "e3_dropin_absent": not DROPIN.exists()}
    d["ok"] = d["manager"] == [] and d["environ"] == [LIVE] and d["adb"] and d["drop_in_live"] and d["e3_dropin_absent"]
    return d


def environ_has(pid: int | None, kv: str) -> bool:
    try:
        return kv in open(f"/proc/{pid}/environ", "rb").read().decode(errors="replace").split("\0")
    except (OSError, TypeError):
        return False


def teardown_flags(w: dict, rec: dict):
    sh(["systemctl", "--user", "unset-environment", *FLAG_NAMES])
    if DROPIN.exists() or w.get("dropin"):
        DROPIN.unlink(missing_ok=True)
        sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["dropin_removed"] = not DROPIN.exists()
    if w.get("flags") or w.get("dropin"):
        rec["restart_after_flags"] = restart_unit()
    if w.get("dropin"):
        rec["dropin_env_absent"] = not any(environ_has(mainpid(), kv) for kv in w["dropin"])
    mp = mainpid()
    rec["flags_absent"] = manager_flags() == [] and environ_flags(mp) == [LIVE]


def run_once(w: dict, run_no: int, out: Path, window: int, gap: int, e2: bool = False) -> dict:
    rd = out / w.get("dir", w["id"]) / f"run{run_no}"
    rd.mkdir(parents=True, exist_ok=True)
    rec = {"workload": w["id"], "run": run_no, "kind": w["kind"], "main_process": w["main"], "started_utc": utc(),
           "window_s": window, "gap_s": gap, "warmup_s": w["warmup"], "status": "STARTED"}
    stream = w["kind"] == "stream"
    game = w.get("game")
    samp = None
    stop_ev = threading.Event()
    threads = []
    before_reports = set(os.listdir(SESSDIR))
    try:
        rec["preflight"] = pf = preflight()
        if not pf["ok"]:
            if pf["game_active"]:
                stop_game()
            raise RuntimeError(f"preflight not clean: {pf}")
        rec["ps1_files_identical_start"] = ps1_files_identical()
        if w["kind"] == "vod":
            rec["vod_mount"] = vm = vod_mount()
            if not (vm["file_present"] and vm["read_only"]):
                raise RuntimeError(f"the VOD file or its read-only mount is not as expected: {vm}")
        if game:
            if game["override"].exists():
                raise RuntimeError("a file already sits at the counter override's path; refusing to overwrite")
            game["override"].parent.mkdir(parents=True, exist_ok=True)   # E3-S4: a lighter core's config dir
            game["override"].write_text(COUNTER)
            rec["counter_override"] = "set"
        for kv in w.get("flags", []):
            sh(["systemctl", "--user", "set-environment", kv])
        if w.get("dropin"):
            DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in w["dropin"]))
            sh(["systemctl", "--user", "daemon-reload"], 60)
            rec["dropin"] = list(w["dropin"])
        rec["restart"] = r = restart_unit()
        want = sorted([LIVE] + w.get("flags", []) + [kv for kv in w.get("dropin", []) if kv.startswith("PRIVYHUB_")])
        if not (r["mainpid_serves_8765"] and r["environ"] == want and r["manager"] == sorted(w.get("flags", []))
                and all(environ_has(mainpid(), kv) for kv in w.get("dropin", []))):
            raise RuntimeError(f"unit not as expected after restart: {r}")
        st = stream_status()
        ov = st.get("encoder_overrides") or {}
        rec["profile_at_start"] = {"profile_id": st.get("profile_id"), "bitrate_kbps": st.get("bitrate_kbps"),
                                   "width": st.get("width"), "height": st.get("height"),
                                   "any_override": ov.get("any_override"),
                                   "adaptive_mode": (st.get("adaptive_bitrate") or {}).get("mode")}
        cmd = [sys.executable, str(REPO / "tools/e1_sampler.py"), "run", str(rd)]
        if stream:
            cmd.append("--telemetry")
        if game:
            cmd.append("--title")
        if e2:
            cmd.append("--e2")
        samp = subprocess.Popen(cmd, stdout=open(rd / "sampler.log", "w"), stderr=subprocess.STDOUT)
        g0 = utc()
        log(w["id"], f"run{run_no}: idle gap {gap}s")
        time.sleep(gap)
        g1 = utc()
        rec["gap"] = {"from": g0, "to": g1}
        # ---- launch
        if w["kind"] == "local":
            code, lr = http("POST", f"/plugins/games/launch?id={game['id']}", 90)
            rec["launch"] = {"http": code, "active": games_status().get("active")}
            time.sleep(3)
            rec["launch"]["unpause"] = u = ra_unpause()
            if not u["ok"]:
                raise RuntimeError(f"RetroArch did not reach PLAYING: {u}")
            log(w["id"], f"run{run_no}: launched, RetroArch PLAYING (no stream)")
        elif stream:
            code, lr = http("POST", f"/plugins/games/launch?id={game['id']}", 90)
            rec["launch"] = {"http": code}
            for _ in range(20):
                if games_status().get("active"):
                    break
                time.sleep(1)
            rec["launch"]["stream"] = o = open_stream()
            if not o["ok"]:
                raise RuntimeError(f"stream did not reach PLAYING: {o}")
            log(w["id"], f"run{run_no}: PLAYING ({o})")
            st = stream_status()
            ov = st.get("encoder_overrides") or {}
            rec["profile_at_playing"] = {"profile_id": st.get("profile_id"), "bitrate_kbps": st.get("bitrate_kbps"),
                                         "width": st.get("width"), "height": st.get("height"),
                                         "any_override": ov.get("any_override"),
                                         "adaptive_mode": (st.get("adaptive_bitrate") or {}).get("mode")}
            p = Poller(rd / "status_poll.jsonl", stop_ev)
            p.start()
            threads.append(p)
        if w["kind"] == "vod":
            rec["launch"] = v = vod_start()
            if not v["ok"]:
                raise RuntimeError(f"VOD did not start: {v}")
            log(w["id"], f"run{run_no}: VOD playing fullscreen from {v['p0']} s")
        playing_t = time.time()
        if w["kind"] == "meta":
            e = EpgCycle(rd / "epg.jsonl", stop_ev)
            e.start()
            threads.append(e)
        if w.get("epg_at"):
            time.sleep(w["epg_at"])
            e = EpgCycle(rd / "epg.jsonl", stop_ev)
            e.start()
            threads.append(e)
        if w.get("rung"):
            time.sleep(max(0, 75 - (time.time() - playing_t)))
            inj = []
            for attempt in (1, 2):
                code, d = http("POST", "/plugins/games/adaptive-bitrate/inject?class=INCREASE_1080P", 30)
                time.sleep(15)
                s2 = stream_status()
                inj.append({"attempt": attempt, "http": code, "reply_reason": (d or {}).get("reason"),
                            "size": f"{s2.get('width')}x{s2.get('height')}", "bitrate_kbps": s2.get("bitrate_kbps")})
                if (s2.get("width"), s2.get("height")) == (1920, 1080):
                    break
            rec["rung_injection"] = inj
            if inj[-1]["size"] != "1920x1080":
                raise RuntimeError(f"the rung was not entered: {inj}")
            log(w["id"], f"run{run_no}: at 1920x1080 ({inj[-1]})")
            playing_t = time.time()
        # ---- warm-up from PLAYING (or the switch), then the window
        time.sleep(max(0, w["warmup"] - (time.time() - playing_t)))
        t0 = utc()
        log(w["id"], f"run{run_no}: window {t0} + {window}s")
        time.sleep(window)
        t1 = utc()
        rec["window"] = {"from": t0, "to": t1}
        if stream:
            rec["status_end"] = {k: stream_status().get(k) for k in ("width", "height", "bitrate_kbps")}
        if w["kind"] == "vod":
            rec["vod_end"] = vod_end(rec["launch"])
        rec["status"] = "WINDOW_DONE"
    except Exception as exc:  # noqa: BLE001
        rec["status"] = "FAILED"
        rec["error"] = f"{type(exc).__name__}: {exc}"[:600]
        rec["trace"] = traceback.format_exc()[-1500:]
        log(w["id"], f"run{run_no}: FAILED -- {rec['error']}")
    finally:
        # ---- teardown to idle
        td = {}
        stop_ev.set()
        for t in threads:
            t.join(timeout=160)
        if stream:
            if "NativeStreamActivity" in top_activity():
                td["report"] = back_and_report(before_reports)
                td["report_fields"] = report_fields(td["report"])
        if game:
            td["stopped"] = stop_game()
            td["retroarch_left"] = len(retroarch_pids())
            td["encoder_left"] = len(encoder_pids())
            try:
                game["override"].unlink()
            except FileNotFoundError:
                pass
            td["counter_override_removed"] = not game["override"].exists()
        if stream:
            td["banner"] = banner_clear()
        if w["kind"] == "vod":
            td["vod"] = vod_teardown()
        teardown_flags(w, td)
        if stream or w.get("flags"):
            td["apk"] = "CONFIRMED" if apk_hash() == EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = ps1_files_identical()
        td["game_active"] = games_status().get("active")
        if samp:
            (rd / "sampler.stop").touch()
            try:
                samp.wait(timeout=30)
            except subprocess.TimeoutExpired:
                samp.kill()
        rec["teardown"] = td
        rec["ended_utc"] = utc()
    # ---- summaries
    if rec.get("window"):
        t0, t1 = rec["window"]["from"], rec["window"]["to"]
        rec["host"] = S.summarize(str(rd), t0, t1)
        if rec.get("gap"):
            S.summarize(str(rd), rec["gap"]["from"], rec["gap"]["to"], "sampler_summary_gap.json")
        key = {}
        if stream:
            key["heartbeat"] = heartbeat_figures(t0, t1)
            key["telemetry"] = telemetry_figures(rd / "telemetry.jsonl", t0, t1)
            key["status_poll"] = poll_figures(rd / "status_poll.jsonl", t0, t1)
        if game:
            key["retroarch"] = rec["host"].get("retroarch")
        if (rd / "epg.jsonl").exists():
            key["epg"] = epg_figures(rd / "epg.jsonl", t0, t1)
        if w["kind"] == "vod":
            ve = rec.get("vod_end") or {}
            hh = rec["host"]["host"]
            key["vod"] = {k: ve.get(k) for k in ("progress_ratio", "stall_s_per_min", "played_s", "wall_s")}
            # rchar: the range server's file reads (what it serves); its socket send() is not counted in wchar
            key["vod"]["served_kBps_mean"] = (hh.get("procs.range_server.rchar_kBps") or {}).get("mean")
            key["vod"]["eno1_tx_kBps_mean"] = (hh.get("net.eno1.tx_kBps") or {}).get("mean")
        if stream and e2:
            dr = decision_rows(t0, t1)
            (rd / "decisions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in dr))
            key["decisions"] = {"rows": len(dr), "transitions": sum(1 for r in dr if r.get("event") == "transition"
                                                                   or r.get("kind") == "transition")}
        rec["key"] = key
        rec["status"] = "OK" if rec["status"] == "WINDOW_DONE" else rec["status"]
    (rd / "summary.json").write_text(json.dumps(rec, indent=1))
    log(w["id"], f"run{run_no}: {rec['status']}; teardown {json.dumps(rec.get('teardown'))[:400]}")
    return rec


def run_suite(out: Path, only: list | None, runs: int, window: int, gap: int, plan: list | None = None,
              e2: bool = False):
    """plan: [(id, runs, first_gap_s)] in order (E2); otherwise `only` x `runs` in suite order."""
    out.mkdir(parents=True, exist_ok=True)
    global log
    log = Log(out / "suite.log")
    byid = {w["id"]: w for w in WORKLOADS}
    if plan:
        # E3: a 4th plan field KEY=VAL[+KEY=VAL] = the run's drop-in flag(s); its runs go to <ID>_flag/
        sched = []
        for row in plan:
            i, r, g = row[:3]
            fl = row[3] if len(row) > 3 else None
            w = dict(byid[i], dropin=fl, dir=f"{i}_flag") if fl else byid[i]
            core = next((kv.split("=", 1)[1] for kv in (fl or []) if kv.startswith("PRIVYHUB_SNES_CORE=")), None)
            if core and w.get("game"):
                w["game"] = dict(w["game"], override=RA_CFG / SNES_CORENAMES[core] / w["game"]["override"].name)
            sched.append((w, r, g))
    else:
        sched = [(w, runs, gap) for w in WORKLOADS if not only or w["id"] in only]
    log(f"suite start: {[(w.get('dir', w['id']), r, g, w.get('dropin')) for w, r, g in sched]}, window {window}s, gap {gap}s, e2 {e2}; "
        f"ABSENT: {sorted(ABSENT)}")
    (out / "absent.json").write_text(json.dumps(ABSENT, indent=1))
    done = {}   # E3-S5B: interleaved plan items for the same row continue its run numbers (run1, run2, ...)
    for w, nruns, first_gap in sched:
        base = done.get(w.get("dir", w["id"]), 0)
        done[w.get("dir", w["id"])] = base + nruns
        for n in range(base + 1, base + nruns + 1):
            rec = None
            g = first_gap if n == base + 1 else gap
            for attempt in range(3):          # the run, plus at most two retries of a failing launch
                rec = run_once(w, n, out, window, g, e2)
                if rec["status"] == "OK":
                    break
                log(w["id"], f"run{n}: attempt {attempt + 1} failed")
                if attempt < 2:
                    (out / w.get("dir", w["id"]) / f"run{n}" / "summary.json").rename(
                        out / w.get("dir", w["id"]) / f"run{n}" / f"summary_failed_attempt{attempt + 1}.json")
    log("suite done")
    final = {"manager": manager_flags(), "environ": environ_flags(mainpid()), "game_active": games_status().get("active"),
             "ps1_files_identical": ps1_files_identical(), "apk": "CONFIRMED" if apk_hash() == EXPECT_APK else "MISMATCH",
             "retroarch": len(retroarch_pids()), "encoder": len(encoder_pids()), "at_utc": utc()}
    final["e3_dropin_absent"] = not DROPIN.exists()
    final["flags_absent"] = final["manager"] == [] and final["environ"] == [LIVE] and final["e3_dropin_absent"]
    (out / "final_state.json").write_text(json.dumps(final, indent=1))
    log("final state:", json.dumps(final))


# ---------------------------------------------------------------- the repeatability table
def _m(summary: dict, key: str):
    v = (summary.get("host") or {}).get("host", {}).get(key)
    return v["mean"] if v else None


def compare(out: Path) -> dict:
    res = {}
    for w in WORKLOADS:
        p = [out / w["id"] / f"run{n}" / "summary.json" for n in (1, 2)]
        if not all(x.exists() for x in p):
            res[w["id"]] = {"verdict": "NOT RUN"}
            continue
        a, b = (json.loads(x.read_text()) for x in p)
        if a.get("status") != "OK" or b.get("status") != "OK":
            res[w["id"]] = {"verdict": "FAILED RUN", "status": [a.get("status"), b.get("status")],
                            "errors": [a.get("error"), b.get("error")]}
            continue
        rows, fails = [], []

        def add(name, x, y, ok, band):
            rows.append({"metric": name, "run1": x, "run2": y, "band": band, "holds": ok})
            if ok is False:
                fails.append(name)
        x, y = _m(a, "cpu.mean_pct"), _m(b, "cpu.mean_pct")
        add("host CPU mean %", x, y, None if None in (x, y) else abs(x - y) <= BAR["cpu_points"], "+/-2 points")
        x, y = _m(a, "gpu.busy_pct"), _m(b, "gpu.busy_pct")
        add("GPU busy mean %", x, y, None if None in (x, y) else abs(x - y) <= BAR["gpu_points"], "+/-3 points")
        k = f"procs.{w['main']}.rss_kb"
        x, y = _m(a, k), _m(b, k)
        add(f"RSS {w['main']} (kB)", x, y,
            None if not x or not y else abs(x - y) / ((x + y) / 2) <= BAR["rss_frac"], "+/-5 %")
        ka, kb = a.get("key", {}), b.get("key", {})
        if w.get("game"):
            x = ((ka.get("retroarch") or {}).get("frames_per_s"))
            y = ((kb.get("retroarch") or {}).get("frames_per_s"))
            add("RetroArch frames/s", x, y, None if None in (x, y) else abs(x - y) <= BAR["fps_abs"], "+/-0.5")
        if w["kind"] == "stream":
            x = (ka.get("heartbeat") or {}).get("rendered_fps")
            y = (kb.get("heartbeat") or {}).get("rendered_fps")
            add("rendered fps (heartbeat)", x, y, None if None in (x, y) else abs(x - y) <= BAR["fps_abs"], "+/-0.5")
            for nm, kk in (("video loss/min", "video_loss_per_min"), ("audio underruns", "audio_underruns")):
                add(nm, (ka.get("heartbeat") or {}).get(kk), (kb.get("heartbeat") or {}).get(kk), None,
                    "reported, not banded")
            add("max output gap ms (C2)", (ka.get("telemetry") or {}).get("output_gap_ms_max"),
                (kb.get("telemetry") or {}).get("output_gap_ms_max"), None, "reported, not banded")
        if w.get("rung"):
            x = (ka.get("status_poll") or {}).get("frac_1920x1080")
            y = (kb.get("status_poll") or {}).get("frac_1920x1080")
            pre = None if None in (x, y) else (x >= 0.95 and y >= 0.95)
            add("precondition: share of window at 1920x1080", x, y, pre, ">= 0.95 each")
        if w["kind"] == "vod":
            x = (ka.get("vod") or {}).get("progress_ratio")
            y = (kb.get("vod") or {}).get("progress_ratio")
            add("VOD progress ratio (played / wall)", x, y,
                None if None in (x, y) else abs(x - y) <= BAR["vod_ratio_abs"], "+/-0.01")
            add("served kB/s (range server)", (ka.get("vod") or {}).get("served_kBps_mean"),
                (kb.get("vod") or {}).get("served_kBps_mean"), None, "reported, not banded")
        if "epg" in ka or "epg" in kb:
            x = (ka.get("epg") or {}).get("grab_s_median")
            y = (kb.get("epg") or {}).get("grab_s_median")
            add("median grab s", x, y,
                None if not x or not y else abs(x - y) / ((x + y) / 2) <= BAR["grab_frac"], "+/-30 %")
            add("grabs ok / failed", f"{(ka.get('epg') or {}).get('grabs_ok')}/{(ka.get('epg') or {}).get('grabs_failed')}",
                f"{(kb.get('epg') or {}).get('grabs_ok')}/{(kb.get('epg') or {}).get('grabs_failed')}", None, "reported")
        res[w["id"]] = {"verdict": "REPEATABLE" if not fails else "NOT YET REPEATABLE", "failed": fails, "rows": rows}
    for k, why in ABSENT.items():
        res[k] = {"verdict": "ABSENT", "why": why}
    (out / "repeatability.json").write_text(json.dumps(res, indent=1))
    md = ["| workload | metric | run 1 | run 2 | band | holds |", "| --- | --- | --- | --- | --- | --- |"]
    fmt = lambda v: f"{v:.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)
    for wid, r in res.items():
        if "rows" not in r:
            md.append(f"| {wid} | **{r['verdict']}** | | | {r.get('why', '')} | |")
            continue
        for i, row in enumerate(r["rows"]):
            md.append(f"| {wid if i == 0 else ''} | {row['metric']} | {fmt(row['run1'])} | {fmt(row['run2'])} | "
                      f"{row['band']} | {'—' if row['holds'] is None else ('yes' if row['holds'] else '**no**')} |")
        md.append(f"| | **{r['verdict']}** | | | {', '.join(r['failed'])} | |")
    (out / "repeatability.md").write_text("\n".join(md) + "\n")
    return res


# ---------------------------------------------------------------- manifest / check
def manifest(out: Path) -> int:
    lines = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.name != "manifest.sha256":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out)}")
    (out / "manifest.sha256").write_text("\n".join(lines) + "\n")
    print(f"manifest: {len(lines)} files")
    return 0


def check(out: Path) -> int:
    probs = []
    m = out / "manifest.sha256"
    if not m.exists():
        probs.append("no manifest")
    else:
        for line in m.read_text().splitlines():
            h, _, rel = line.partition("  ")
            p = out / rel
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
                probs.append(f"changed or missing: {rel}")
    for wdir in sorted(d for d in out.iterdir() if d.is_dir() and d.name.split("_")[0] in {w["id"] for w in WORKLOADS}):
        w = {"id": wdir.name}
        for rdir in sorted(wdir.glob("run*")):
            n = rdir.name[3:]
            s = rdir / "summary.json"
            if not s.exists():
                probs.append(f"{w['id']} run{n}: no summary")
                continue
            d = json.loads(s.read_text())
            rows = ((d.get("host") or {}).get("window") or {}).get("host_rows", 0)
            if d.get("status") != "OK":
                probs.append(f"{w['id']} run{n}: status {d.get('status')}")
            elif rows < 0.95 * d.get("window_s", 300):
                probs.append(f"{w['id']} run{n}: {rows} host rows in the window")
    print("CHECK", "OK" if not probs else "PROBLEMS", *probs, sep="\n  ")
    return 0 if not probs else 1


def self_test() -> int:
    assert len({w["id"] for w in WORKLOADS}) == len(WORKLOADS)
    assert all(w["warmup"] >= 60 for w in WORKLOADS)
    assert [w for w in WORKLOADS if w.get("flags")] == [w for w in WORKLOADS if w["id"] == "E1-PS1-1080P"]
    hb = heartbeat_figures("9999", "9999")
    assert hb == {"heartbeats": 0}
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "e.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in [
            {"kind": "grab", "start_utc": "2026-01-01T00:00:01Z", "end_utc": "2026-01-01T00:00:07Z", "s": 6, "ok": True},
            {"kind": "grab", "start_utc": "2026-01-01T00:00:07Z", "end_utc": "2026-01-01T00:00:17Z", "s": 10, "ok": True},
            {"kind": "grab", "start_utc": "2026-01-01T00:00:17Z", "end_utc": "2026-01-01T00:09:00Z", "s": 9, "ok": True},
            {"kind": "scan", "start_utc": "2026-01-01T00:00:30Z", "end_utc": "2026-01-01T00:00:30Z", "s": 0.01}]))
        e = epg_figures(p, "2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z")
        assert e["grabs_in_window"] == 2 and e["grab_s_median"] == 8 and e["scans"] == 1, e
        q = Path(td) / "t.jsonl"
        q.write_text("\n".join(json.dumps(r) for r in [
            {"at_utc": "2026-01-01T00:00:01Z", "fresh": True, "elapsed_ms": 1000, "latency": {"output_gap_ms": 20},
             "receiver": {"lost_packets_delta": 1}},
            {"at_utc": "2026-01-01T00:00:02Z", "fresh": True, "elapsed_ms": 1000, "latency": {"output_gap_ms": 20},
             "receiver": {"lost_packets_delta": 1}},
            {"at_utc": "2026-01-01T00:01:01Z", "fresh": True, "elapsed_ms": 61000, "latency": {"output_gap_ms": 40},
             "receiver": {"lost_packets_delta": 2}}]))
        t = telemetry_figures(q, "2026-01-01T00:00:00Z", "2026-01-01T00:05:00Z")
        assert t["reports"] == 2 and t["output_gap_ms_max"] == 40 and t["receiver_lost_packets_per_min"] == 3.0, t
    print("E1_SUITE_SELF_TEST_OK")
    return 0


def main(argv: list) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--list" in argv:
        for w in WORKLOADS:
            print(w["id"], w["kind"], f"warmup {w['warmup']}s", "flags " + " ".join(w.get("flags", [])) if w.get("flags") else "")
        for k, v in ABSENT.items():
            print(k, "ABSENT --", v)
        return 0
    if "--check" in argv:
        return check(Path(argv[argv.index("--check") + 1]))
    if argv and argv[0] == "compare":
        r = compare(Path(argv[1]))
        print(json.dumps({k: v["verdict"] for k, v in r.items()}, indent=1))
        return 0
    if argv and argv[0] == "manifest":
        return manifest(Path(argv[1]))
    if argv and argv[0] == "run":
        out = Path(argv[argv.index("--out") + 1])
        pre = Path(argv[argv.index("--prereg") + 1]) if "--prereg" in argv else None
        if not pre or not pre.exists():
            print("refusing: --prereg <e1_preregistration.txt> is required (the suite runs only pre-registered)")
            return 2
        shaf = pre.with_suffix(".sha256")
        want = shaf.read_text().split()[0] if shaf.exists() else None
        if hashlib.sha256(pre.read_bytes()).hexdigest() != want:
            print("refusing: the pre-registration does not match its hash")
            return 2
        only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
        runs = int(argv[argv.index("--runs") + 1]) if "--runs" in argv else 2
        window = int(argv[argv.index("--window") + 1]) if "--window" in argv else 300
        gap = int(argv[argv.index("--gap") + 1]) if "--gap" in argv else 120
        plan = None
        if "--plan" in argv:
            plan = []
            for item in argv[argv.index("--plan") + 1].split(","):
                p = item.split(":")
                row = [p[0], int(p[1]) if len(p) > 1 else 1, int(p[2]) if len(p) > 2 else gap]
                if len(p) > 3 and p[3]:
                    row.append(p[3].split("+"))
                plan.append(row)
            unknown = [r[0] for r in plan if r[0] not in {w["id"] for w in WORKLOADS}]
            if unknown:
                print("refusing: unknown ids", unknown)
                return 2
        run_suite(out, only, runs, window, gap, plan, "--e2" in argv)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
