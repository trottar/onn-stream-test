#!/usr/bin/env python3
"""G4-S4 -- off-site free play: NO SUITE. DETACHED, run as pre-registered (g4_s4_preregistration.txt), as the systemd
--user transient unit privyhub-g4-s4, until STOP (~/privyhub_g4_s4/STOP) or the cap (the start + 9000 s). Built from
G4-S3's driver (g4_s3_2026-10-19/g4_s3_driver.py); changed:
- no suite: the drop-in is held for the whole play;
- an idle wait before the drop-in (no game active, no connection on the range server's port, twice 15 s apart);
- the cap is the start + 2 h 30 min, written to cap_utc.txt;
- PRIVYHUB_REMOTE_RUNG_CAP=7000; the environ reads back len(E1.ADOPTED) (ten) + 4 = fourteen, else the drop-in is
  removed at once;
- samplers: the tailnet tx/rx + the stream status every 10 s; the overlay state, the WAN block and the session state
  every 60 s; the rotating logs and the journal copied into ~/privyhub_g4_s4/ every 5 min (incremental; a rotation
  under a log is followed into the archive's .1 by inode);
- on STOP or the cap: a last copy, the drop-in removed, restart, flags_absent and the ten lines read, a copy after."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SUITE = REPO / "tools/e1_suite.py"
WATCH = Path.home() / "privyhub_g4_s4"
STOPFILE = WATCH / "STOP"
STATUS_P, WLOG_P = WATCH / "status.txt", WATCH / "driver.log"
RAW = WATCH / "logs"
STATE_P = HERE / "g4_s4_state.json"
SAMPLES = HERE / "samples"
LOGDIR = REPO / "logs/games"
ARCH = LOGDIR / "stream_log_archive"
TAILS = ["adaptive_bitrate_shadow.jsonl", "native_stream_heartbeat.log", "native_stream_recovery.log",
         "native_stream_ctrl_gaps.log", "native_frame_sizes.jsonl", "host_resource_samples.jsonl",
         "native_pulseaudio.log", "native_video_alpha.log"]
NEWDIRS = ["decoder_sessions", "audio_timing"]
CAP_S = 9000
FAST, SLOW, COPY, HEARTBEAT = 10, 60, 300, 60
RANGE_PORT = 8000
KVS = ["PRIVYHUB_REMOTE_LADDER=1", "PRIVYHUB_START_RUNG=floor", "PRIVYHUB_REMOTE_RUNG_CAP=7000",
       "PRIVYHUB_WAN_TELEMETRY=1"]
IP = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[0-9a-fA-F]{32,}\b|\bdev-[0-9a-f]{8,}\b")

spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
E1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E1)
STOP = threading.Event()
T0 = time.time()
CAP = T0 + CAP_S


def utc(t=None):
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


CAP_UTC = utc(CAP)[:19] + "Z"


def log(*a):
    line = f"[g4s4 {time.strftime('%m-%d %H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(WLOG_P, "a") as fh:
        fh.write(line + "\n")


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


# ---------------------------------------------------------------- the status line, the stop file
STATUS = {"phase": "starting", "last": "-", "state": "-"}
STATUS_LOCK = threading.Lock()


def write_status(**kw):
    with STATUS_LOCK:
        STATUS.update(kw)
        s = STATUS
        line = (f"{utc()} heartbeat | phase: {s['phase']} | last: {s['last']} | state: {s['state']} | "
                f"cap {CAP_UTC} | stop: touch ~/privyhub_g4_s4/STOP\n")
        tmp = STATUS_P.with_suffix(".tmp")
        tmp.write_text(line)
        os.replace(tmp, STATUS_P)


def stop_or_cap():
    if STOPFILE.exists():
        return "the stop file"
    if time.time() >= CAP:
        return "the cap"
    return None


def wait(s):
    """Sleep up to s seconds, waking at STOP / the cap."""
    end = time.time() + s
    while time.time() < end:
        if stop_or_cap():
            return False
        time.sleep(min(2, max(0, end - time.time())))
    return True


# ---------------------------------------------------------------- readings
def tailnet_bytes():
    for p in sorted(Path("/sys/class/net").iterdir()):
        if p.name.startswith("tailscale"):
            try:
                return int((p / "statistics/tx_bytes").read_text()), int((p / "statistics/rx_bytes").read_text())
            except (OSError, ValueError):
                return None, None
    return None, None


def range_conns():
    try:
        out = subprocess.run(["ss", "-Htn", "state", "established", f"( sport = :{RANGE_PORT} )"],
                             capture_output=True, text=True, timeout=10).stdout
        return sum(1 for l in out.splitlines() if l.strip())
    except (OSError, subprocess.SubprocessError):
        return None


def game_state():
    g = E1.games_status() or {}
    game = g.get("game") if isinstance(g.get("game"), dict) else {}
    ns = g.get("native_stream") if isinstance(g.get("native_stream"), dict) else {}
    return {"game_active": bool(g.get("active")), "paused": g.get("paused"), "system": game.get("system"),
            "elapsed_s": g.get("elapsed_seconds"), "native_stream_active": ns.get("active")}


def overlay_state():
    try:
        r = subprocess.run([sys.executable, "-m", "companion.overlay", "--state", "--provider", "tailscale"],
                           capture_output=True, text=True, timeout=30, cwd=str(REPO))
        st = (json.loads(r.stdout) or {}).get("state") or {}
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        return {"error": repr(e)[:80]}
    keep = {k: st.get(k) for k in ("connected", "path", "peer_ready", "mtu", "reason")}
    for k in ("rtt_ms", "latency_ms", "rtt"):
        if k in st:
            keep[k] = st[k]
    return keep


def encoder_rate():
    for p in E1.encoder_pids():
        try:
            argv = open(f"/proc/{p}/cmdline", "rb").read().decode(errors="replace").split("\0")
        except OSError:
            continue
        val = lambda opt: argv[argv.index(opt) + 1] if opt in argv and argv.index(opt) + 1 < len(argv) else None
        return {"b_v": val("-b:v"), "maxrate": val("-maxrate")}
    return None


# ---------------------------------------------------------------- the copier (incremental, rotation-safe)
class Tail:
    def __init__(self, name):
        self.name, self.live, self.dest = name, LOGDIR / name, RAW / name
        try:
            st = self.live.stat()
            self.ino, self.off = st.st_ino, st.st_size
        except OSError:
            self.ino, self.off = None, 0

    def _copy(self, src, off):
        with open(src, "rb") as fh, open(self.dest, "ab") as out:
            fh.seek(off)
            n = 0
            while chunk := fh.read(1 << 20):
                out.write(chunk)
                n += len(chunk)
        return n

    def step(self):
        moved, rotated = 0, False
        try:
            st = self.live.stat()
        except OSError:
            return 0, False
        if self.ino is not None and st.st_ino != self.ino:
            rotated = True
            for i in (1, 2, 3):
                a = ARCH / f"{self.name}.{i}"
                try:
                    if a.stat().st_ino == self.ino:
                        moved += self._copy(a, self.off)
                        break
                except OSError:
                    continue
            self.off = 0
        self.ino = st.st_ino
        if st.st_size < self.off:
            self.off = 0
        got = self._copy(self.live, self.off)
        self.off += got
        return moved + got, rotated


class NewFiles:
    def __init__(self, sub):
        self.src, self.dest = LOGDIR / sub, RAW / sub
        self.seen = set(os.listdir(self.src)) if self.src.is_dir() else set()

    def step(self, final=False):
        n = 0
        if not self.src.is_dir():
            return 0
        for f in sorted(os.listdir(self.src)):
            if f in self.seen:
                continue
            p = self.src / f
            try:
                if not final and time.time() - p.stat().st_mtime < 10:
                    continue
                self.dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, self.dest / f)
                self.seen.add(f)
                n += 1
            except OSError:
                pass
        return n


class Copier:
    def __init__(self):
        RAW.mkdir(parents=True, exist_ok=True)
        self.tails = [Tail(n) for n in TAILS]
        self.dirs = [NewFiles(d) for d in NEWDIRS]
        self.jsince = int(T0)
        self.lock = threading.Lock()

    def step(self, final=False):
        with self.lock:
            out = {"at_utc": utc()}
            for t in self.tails:
                try:
                    n, rot = t.step()
                    out[t.name] = {"bytes": n, "rotated": rot}
                except OSError as e:
                    out[t.name] = {"error": repr(e)[:80]}
            for d in self.dirs:
                out[d.src.name] = {"new_files": d.step(final)}
            now = int(time.time())
            try:
                j = subprocess.run(["journalctl", "--user", "-u", E1.UNIT, "-o", "short-iso-precise", "--no-pager",
                                    "--since", f"@{self.jsince}", "--until", f"@{now}"], capture_output=True, timeout=120)
                with open(RAW / "companion_journal.txt", "ab") as fh:
                    fh.write(j.stdout)
                out["journal_bytes"] = len(j.stdout)
                self.jsince = now
            except (OSError, subprocess.SubprocessError) as e:
                out["journal_error"] = repr(e)[:80]
            append(SAMPLES / "copies.jsonl", out)
            return out


# ---------------------------------------------------------------- the samplers
def samplers(copier):
    last, t_slow, t_copy = None, 0.0, time.time()
    while not STOP.is_set():
        now = time.time()
        tx, rx = tailnet_bytes()
        d = E1.stream_status() or {}
        a = d.get("adaptive_bitrate") if isinstance(d.get("adaptive_bitrate"), dict) else {}
        tk = rk = None
        if tx is not None and last and now > last[0]:
            tk = round((tx - last[1]) * 8 / 1000 / (now - last[0]), 1)
            rk = round((rx - last[2]) * 8 / 1000 / (now - last[0]), 1)
        if tx is not None:
            last = (now, tx, rx)
        row, _ = scrub({"at_utc": utc(now), "t": round(now, 3), "tailnet_tx_bytes": tx, "tailnet_rx_bytes": rx,
                        "tailnet_tx_kbps": tk, "tailnet_rx_kbps": rk, "active": d.get("active"),
                        "width": d.get("width"), "height": d.get("height"), "bitrate_kbps": d.get("bitrate_kbps"),
                        "level_kbps": a.get("level_kbps"), "state": a.get("state"), "encoder": encoder_rate()})
        append(SAMPLES / "fast_10s.jsonl", row)
        if now - t_slow >= SLOW:
            t_slow = now
            gs = game_state()
            ov = overlay_state()
            st = E1.http("GET", "/diagnostics/stream-telemetry", 10)[1] or {}
            w, n = scrub(st.get("wan") if isinstance(st, dict) else None)
            srow, _ = scrub({"at_utc": utc(), **gs, "vod_conns": range_conns(), "overlay": ov,
                             "has_wan": isinstance(st, dict) and "wan" in st, "wan": w, "redacted_matches": n})
            append(SAMPLES / "slow_60s.jsonl", srow)
            cls = ("game:" + str(gs.get("system"))) if gs.get("game_active") else ("vod" if srow.get("vod_conns") else "idle")
            write_status(state=f"{cls} | path {ov.get('path')} | tx {tk} kbps")
        if now - t_copy >= COPY:
            t_copy = now
            try:
                copier.step()
            except Exception as e:      # noqa: BLE001 -- a copy failure never stops the samplers
                log(f"copy error {e!r}")
        STOP.wait(max(0.5, FAST - (time.time() - now)))


def write_dropin():
    E1.DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in KVS))
    E1.sh(["systemctl", "--user", "daemon-reload"], 60)
    r = E1.restart_unit()
    env = r.get("environ") or []
    return {"mainpid_serves_8765": r.get("mainpid_serves_8765"), "manager": len(r.get("manager") or []),
            "environ_lines": len(env), "flags_present": {kv: kv in env for kv in KVS},
            "adopted_present": all(kv in env for kv in E1.ADOPTED),
            "ok": all(kv in env for kv in KVS) and all(kv in env for kv in E1.ADOPTED) and len(env) == len(E1.ADOPTED) + len(KVS)}


def idle_now():
    gs = game_state()
    v = range_conns()
    return (not gs["game_active"]) and v == 0, gs, v


def main():
    WATCH.mkdir(parents=True, exist_ok=True)
    SAMPLES.mkdir(parents=True, exist_ok=True)
    (HERE / "cap_utc.txt").write_text(CAP_UTC + "\n")
    st = {"started_utc": utc(T0), "cap_utc": CAP_UTC, "kvs": KVS}
    jdump(STATE_P, st)
    log("start | cap", CAP_UTC, "| adopted", len(E1.ADOPTED))
    write_status(phase="idle wait: the onn must be idle (no game, no video) before the restart")
    copier = Copier()
    th = threading.Thread(target=samplers, args=(copier,), daemon=True)
    th.start()
    why, dropin = None, False
    # ---- the idle wait
    n_idle = 0
    while True:
        why = stop_or_cap()
        if why:
            break
        ok, gs, v = idle_now()
        n_idle = n_idle + 1 if ok else 0
        if n_idle >= 2:
            break
        if not ok:
            write_status(phase=f"idle wait: busy ({'game ' + str(gs.get('system')) if gs['game_active'] else ''}"
                               f"{' vod' if v else ''}); the restart waits")
        if not wait(15):
            why = stop_or_cap()
            break
    st["idle_wait_end_utc"] = utc()
    if not why:
        # ---- the drop-in
        write_status(phase="drop-in + restart")
        wr = write_dropin()
        dropin = True
        st["dropin_readback"], st["dropin_utc"] = wr, utc()
        (HERE / "e3_flag.conf.txt").write_text(E1.DROPIN.read_text())
        log(f"drop-in written, restarted; environ {wr['environ_lines']} lines, ok {wr['ok']}")
        jdump(STATE_P, st)
        if not wr["ok"]:
            why = f"the environ read back {wr['environ_lines']} lines, not {len(E1.ADOPTED) + len(KVS)}"
        else:
            write_status(phase=f"HOLDING the four lines ({wr['environ_lines']} lines) since {utc()[11:19]}Z; "
                               f"start any game within 15 min (by {utc(time.time() + 900)[11:16]}Z)")
            while True:
                why = stop_or_cap()
                if why:
                    break
                time.sleep(2)
    # ---- the close
    log("closing:", why)
    write_status(phase=f"closing ({why}): last copy, drop-in removed, restart")
    try:
        copier.step()
    except Exception as e:      # noqa: BLE001
        log(f"copy error {e!r}")
    STOP.set()
    th.join(timeout=30)
    td = {}
    E1.teardown_flags({"dropin": KVS} if dropin or E1.DROPIN.exists() else {}, td)
    mp = E1.mainpid()
    env = E1.environ_flags(mp)
    st["teardown"] = {"dropin_removed": td.get("dropin_removed"), "dropin_env_absent": td.get("dropin_env_absent"),
                      "flags_absent": bool(td.get("flags_absent")), "environ_lines_after": len(env),
                      "ten_lines": env == E1.ADOPTED, "e3_dropin_absent": not E1.DROPIN.exists(),
                      "restarted": "restart_after_flags" in td}
    log(f"drop-in removed; flags_absent {td.get('flags_absent')}; environ {len(env)} lines (adopted {env == E1.ADOPTED})")
    time.sleep(5)
    try:
        copier.step(final=True)
    except Exception as e:      # noqa: BLE001
        log(f"copy error {e!r}")
    st["closed_utc"], st["closed_by"] = utc(), why
    jdump(STATE_P, st)
    write_status(phase=f"EXITED ({why})", last=f"flags_absent {td.get('flags_absent')} | {len(env)} lines")
    log("driver closed (" + str(why) + ")")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # a crash is written to the status line, the drop-in removed, then re-raised
        STOP.set()
        try:
            td = {}
            E1.teardown_flags({"dropin": KVS} if E1.DROPIN.exists() else {}, td)
            write_status(phase=f"CRASHED: {repr(e)[:120]}; drop-in removed, flags_absent {td.get('flags_absent')}")
        finally:
            raise
