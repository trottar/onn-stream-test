#!/usr/bin/env python3
"""D-BASE-R3c Part 1: does a recovery state loaded into a FRESH core play?

Host only, no client. Each arm launches the PS1 reference title through the
companion's normal launch path (POST /plugins/games/launch), then:

  C  control -- unpause, no state load
  P  paused  -- load through the companion's own recovery path
                (POST /plugins/games/recovery-resume -> load_recovery_state,
                which requires a paused core), then unpause
  Q  paused, late -- unpause, run 20 s, PAUSE_TOGGLE, then the P path
                (recovery-resume through the companion), then unpause:
                separates "paused at load" from "loaded 3 s after boot"
  G  gameplay state, paused -- unpause, run until the attract demo fight
                moves (probed), SAVE_STATE_SLOT 0 (the slot-0 scratch file,
                backed up under pre_state/ first), keep running 15 s,
                PAUSE_TOGGLE, LOAD_STATE_SLOT 0 while PAUSED (the manager's
                precondition), unpause: is the loop specific to a state
                captured mid-FMV? The scratch file is restored from the
                recovery save afterwards.
  R  running -- unpause, let the core run 20 s, then LOAD_STATE_SLOT 0 sent
                straight to RetroArch while PLAYING. The manager API refuses
                this (load_recovery_state raises "Load State requires the
                game to be paused"), so it goes over the wire, after checking
                the staged slot-0 file is byte-identical to the recovery save.

Unpause is the same PAUSE_TOGGLE network command manager.resume() sends;
the companion has no HTTP resume without a stream. Then 30 s of
x11grab -> framemd5 of the managed window (the GROUP_A A3-live command),
distinct hashes counted. The game is stopped through the companion after
each arm. Nothing is discarded; the recovery file is re-hashed at the end.

usage: r3c_probe.py [--snap] C|P|R|P2|R2|C2 [...]  (labels starting P/R take that arm's path)
"""
import hashlib, json, os, re, socket, subprocess, sys, time, urllib.request

REPO = "/home/privyhub/Projects/onn-stream-test"
HERE = os.path.dirname(os.path.abspath(__file__))
GAME = "game_ps1_b0a5986638f61a11"
CFG = f"{REPO}/data/games/retroarch/config/privyhub-session.cfg"
STATES = f"{REPO}/data/games/retroarch/states/Beetle PSX HW"
RECOVERY = f"{STATES}/Tekken 3 (USA).state.recovery"
SCRATCH = f"{STATES}/Tekken 3 (USA).state"
PROBE_LOG = f"{REPO}/logs/games/save_state_probe.txt"
BASE = "http://localhost:8765/plugins/games"
ENV = dict(os.environ, DISPLAY=":0")


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(os.path.join(HERE, "r3c_probe_run.log"), "a") as f:
        f.write(line + "\n")


def http(action, method="GET"):
    req = urllib.request.Request(f"{BASE}/{action}", method=method,
                                 data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body[:300].decode(errors="replace")}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def ra_port():
    m = re.search(r'^network_cmd_port\s*=\s*"(\d+)"', open(CFG).read(), re.M)
    return int(m.group(1))


def ra(cmd, reply=False):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2.0)
    s.sendto(cmd.encode(), ("127.0.0.1", ra_port()))
    out = None
    if reply:
        try:
            out = s.recvfrom(4096)[0].decode(errors="replace").strip()
        except socket.timeout:
            out = None
    s.close()
    return out


def ra_status():
    return ra("GET_STATUS", reply=True) or ""


def wait_status(want, timeout=5.0):
    end = time.time() + timeout
    st = ""
    while time.time() < end:
        st = ra_status()
        if want in st:
            return st
        time.sleep(0.2)
    return st


def stop_game():
    http("stop", "POST")
    for _ in range(20):
        time.sleep(1)
        if not http("status")[1].get("active", True):
            return True
    return False


def window_for(pid):
    for _ in range(20):
        out = subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(pid)],
                             capture_output=True, text=True, env=ENV).stdout.split()
        if out:
            return out[0]
        time.sleep(0.5)
    return None


def grab(win, label):
    out = os.path.join(HERE, f"probe_{label}_framemd5.txt")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
                    "-framerate", "60", "-window_id", win, "-i", ":0.0", "-t", "30",
                    "-f", "framemd5", out], env=ENV, check=False)
    rows = [l.split(",") for l in open(out) if l[0] != "#"]
    md = [r[-1].strip() for r in rows]
    pts = [int(r[1]) for r in rows]
    d = [b - a for a, b in zip(pts, pts[1:])]
    per_s = [len(set(md[s:s + 60])) for s in range(0, len(md), 60)]
    # a short loop shows as few distinct hashes that each recur many times
    counts = {}
    for h in md:
        counts[h] = counts.get(h, 0) + 1
    top = sorted(counts.values(), reverse=True)[:5]
    return dict(frames=len(md), distinct=len(counts),
                dups_consecutive=sum(1 for a, b in zip(md, md[1:]) if a == b),
                pts_delta_min=min(d) if d else None, pts_delta_max=max(d) if d else None,
                distinct_per_second=per_s, top5_hash_counts=top)


def snap(win, name):
    out = os.path.join(HERE, f"snap_{name}.png")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
                    "-window_id", win, "-i", ":0.0", "-frames:v", "1", out], env=ENV, check=False)
    return os.path.basename(out)


def probe_lines_since(offset):
    try:
        with open(PROBE_LOG, errors="replace") as f:
            f.seek(offset)
            return [l.rstrip() for l in f]
    except OSError:
        return []


def arm(label):
    log(f"=== arm {label} ===")
    if not stop_game():
        log("FAILED: game still active before launch"); return None
    probe_off = os.path.getsize(PROBE_LOG) if os.path.exists(PROBE_LOG) else 0
    rec_before = sha(RECOVERY)
    code, st = http(f"launch?id={GAME}", "POST")
    log(f"launch http {code} active={st.get('active')} paused={st.get('paused')} pid={st.get('pid')}")
    pid = st.get("pid") or http("status")[1].get("pid")
    if not st.get("active"):
        log(f"FAILED to launch: {json.dumps(st)[:300]}"); return None
    win = window_for(pid)
    log(f"pid {pid} window {'found' if win else 'NOT FOUND'}; RA status '{ra_status()}'")
    if not win:
        return None
    result = {"arm": label, "pid": pid, "recovery_sha_before": rec_before}

    if label.startswith("P"):
        time.sleep(3)
        code, body = http("recovery-resume", "POST")
        result["recovery_resume_http"] = code
        result["recovery_resume"] = {k: body.get(k) for k in
                                     ("ok", "action", "accepted", "retroarch_response", "paused", "error", "message")
                                     if k in body}
        log(f"recovery-resume http {code} {json.dumps(result['recovery_resume'])}")
        if code != 200:
            return result
        ra("PAUSE_TOGGLE")
        result["after_unpause"] = wait_status("PLAYING")
        log(f"unpause -> '{result['after_unpause']}'")
    elif label.startswith("Q"):
        ra("PAUSE_TOGGLE")
        result["after_unpause"] = wait_status("PLAYING")
        time.sleep(20)
        ra("PAUSE_TOGGLE")
        result["repaused"] = wait_status("PAUSED")
        log(f"ran 20 s, re-paused -> '{result['repaused']}'")
        code, body = http("recovery-resume", "POST")
        result["recovery_resume_http"] = code
        result["recovery_resume"] = {k: body.get(k) for k in ("ok", "action", "accepted", "retroarch_response") if k in body}
        log(f"recovery-resume http {code} {json.dumps(result['recovery_resume'])}")
        if code != 200:
            return result
        ra("PAUSE_TOGGLE")
        result["after_load_unpause"] = wait_status("PLAYING")
        log(f"unpause -> '{result['after_load_unpause']}'")
    elif label.startswith("G"):
        ra("PAUSE_TOGGLE")
        result["after_unpause"] = wait_status("PLAYING")
        t0 = time.time(); moving = 0
        while time.time() - t0 < 240:
            tmp = os.path.join(HERE, "_g_probe.md5")
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "x11grab",
                            "-framerate", "60", "-window_id", win, "-i", ":0.0", "-t", "2",
                            "-f", "framemd5", tmp], env=ENV)
            u = len({l.split(",")[-1] for l in open(tmp) if l[0] != "#"})
            os.remove(tmp)
            if u > 100:
                moving += 1
                if moving >= 2:
                    break
            else:
                moving = 0
            time.sleep(3)
        result["seconds_to_motion"] = round(time.time() - t0)
        log(f"60 fps motion after {result['seconds_to_motion']} s (unique>100 per 2 s, twice)")
        if SNAP:
            result["snap_saved"] = snap(win, f"{label}_saved")
        resp = ra("SAVE_STATE_SLOT 0", reply=True)
        time.sleep(1.5)
        result["save_response"] = resp
        result["gameplay_state_sha"] = sha(SCRATCH)
        log(f"SAVE_STATE_SLOT 0 -> '{resp}', scratch sha {result['gameplay_state_sha'][:16]}")
        time.sleep(15)
        ra("PAUSE_TOGGLE")
        result["repaused"] = wait_status("PAUSED")
        resp = ra("LOAD_STATE_SLOT 0", reply=True)
        time.sleep(0.5)
        result["load_response"] = resp
        result["load_while"] = result["repaused"]
        log(f"LOAD_STATE_SLOT 0 while '{result['repaused']}' -> '{resp}'")
        ra("PAUSE_TOGGLE")
        result["after_load_unpause"] = wait_status("PLAYING")
        log(f"unpause -> '{result['after_load_unpause']}'")
    elif label.startswith("R"):
        ra("PAUSE_TOGGLE")
        result["after_unpause"] = wait_status("PLAYING")
        log(f"unpause -> '{result['after_unpause']}'; running 20 s before the load")
        time.sleep(20)
        result["scratch_equals_recovery"] = sha(SCRATCH) == sha(RECOVERY)
        log(f"slot-0 scratch == recovery: {result['scratch_equals_recovery']}")
        if not result["scratch_equals_recovery"]:
            log("scratch differs; not loading"); return result
        pre = ra_status()
        resp = ra("LOAD_STATE_SLOT 0", reply=True)
        time.sleep(0.5)
        result["load_while"] = pre
        result["load_response"] = resp
        result["after_load"] = ra_status()
        log(f"LOAD_STATE_SLOT 0 while '{pre}' -> '{resp}', now '{result['after_load']}'")
    else:
        ra("PAUSE_TOGGLE")
        result["after_unpause"] = wait_status("PLAYING")
        log(f"unpause -> '{result['after_unpause']}'")

    time.sleep(2)
    if SNAP:
        result["snap_before_grab"] = snap(win, f"{label}_a")
    result["grab"] = grab(win, label)
    if SNAP:
        result["snap_after_grab"] = snap(win, f"{label}_b")
    g = result["grab"]
    log(f"grab: frames {g['frames']} distinct {g['distinct']} pts {g['pts_delta_min']}..{g['pts_delta_max']} "
        f"per_s {g['distinct_per_second']} top5 {g['top5_hash_counts']}")
    result["status_during"] = ra_status()
    result["probe_lines"] = [l[:400] for l in probe_lines_since(probe_off)]
    ok = stop_game()
    if label.startswith("G"):
        import shutil
        shutil.copyfile(RECOVERY, SCRATCH)
        shutil.copyfile(RECOVERY + ".png", SCRATCH + ".png")
        result["scratch_restored_to_recovery"] = sha(SCRATCH) == sha(RECOVERY)
        log(f"slot-0 scratch restored to the recovery bytes: {result['scratch_restored_to_recovery']}")
    result["stopped_clean"] = ok
    result["recovery_sha_after"] = sha(RECOVERY)
    log(f"stopped={ok} recovery unchanged={result['recovery_sha_after'] == rec_before}")
    with open(os.path.join(HERE, f"probe_{label}.json"), "w") as f:
        json.dump(result, f, indent=1)
    return result


SNAP = False

if __name__ == "__main__":
    SNAP = "--snap" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--snap"]
    for a in sys.argv[1:]:
        arm(a)
