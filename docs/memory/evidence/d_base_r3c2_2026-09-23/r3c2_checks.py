#!/usr/bin/env python3
"""D-BASE-R3c2 checks 1-6, adb-driven through the real launcher UI.

The launcher is navigated the way a user does it: GAMES > CONTINUE PLAYING >
the title's tile > the tile dialog's buttons (found by text in a uiautomator
dump; the dump's status line, which shows an address, is never stored).
Host-side facts come from the companion's status, RetroArch's session logs
and the decoder reports.

usage: r3c2_checks.py 1 2 3 4 5 6
"""
import glob, hashlib, json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r3c2_helpers as H  # noqa: E402
P = H.P

REPO = H.REPO
HERE = H.HERE
T3 = "game_ps1_b0a5986638f61a11"
T3_TITLE = r"^Tekken 3 \(USA\) - PlayStation"
OTHER_TITLE = r"^Crash Bandicoot \(USA\) - PlayStation"
SESS = f"{REPO}/logs/games/decoder_sessions"
GLOGS = f"{REPO}/logs/games"
FRAMES = f"{REPO}/logs/games/native_frame_sizes.jsonl"
SLOTS = f"{REPO}/data/games/retroarch/privyhub_state_slots.json"
STATES = H.STATES
SCRATCH = os.path.join(STATES, "Tekken 3 (USA).state")
RECOVERY_SHA = "05bd85c734e86378c6fb4a135bb311d9887f53ecdf81f0dfd4f2f955abbd8040"
log = H.log


def sh(cmd, timeout=30):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout).stdout


def nodes():
    sh("adb shell uiautomator dump /sdcard/r3c2.xml")
    x = sh("adb shell cat /sdcard/r3c2.xml")
    out = []
    for m in re.finditer(r"<node [^>]*>", x):
        n = m.group(0)
        t = re.search(r'text="([^"]*)"', n).group(1)
        rid = re.search(r'resource-id="([^"]*)"', n).group(1).split("/")[-1]
        b = [int(v) for v in re.findall(r"\d+", re.search(r'bounds="([^"]*)"', n).group(1))]
        if rid == "status_text":
            continue
        out.append({"text": t.replace("&gt;", ">").replace("&amp;", "&"), "rid": rid,
                    "cx": (b[0] + b[2]) // 2, "cy": (b[1] + b[3]) // 2})
    return out


def texts(ns):
    return [n["text"] for n in ns if n["text"]]


def find(regex, tries=6, delay=1.5):
    for _ in range(tries):
        ns = nodes()
        for n in ns:
            if re.search(regex, n["text"], re.I):
                return n, ns
        time.sleep(delay)
    return None, ns


def tap(regex, tries=6):
    n, ns = find(regex, tries)
    if n is None:
        raise RuntimeError(f"no node matching {regex!r}; saw {texts(ns)[:25]}")
    sh(f"adb shell input tap {n['cx']} {n['cy']}")
    return n


def top_activity():
    return sh("adb shell dumpsys activity activities | grep -m1 topResumedActivity")


def open_tile(title_regex):
    """Launcher from scratch -> GAMES -> CONTINUE PLAYING -> the tile. Returns the dialog's nodes."""
    sh("adb shell am force-stop com.safeiot.privyhub")
    sh("adb shell input keyevent KEYCODE_WAKEUP")
    sh("adb shell am start -n com.safeiot.privyhub/.MainActivity")
    time.sleep(5)
    tap(r"^GAMES")
    time.sleep(2.5)
    tap(r"^CONTINUE PLAYING")
    time.sleep(2.5)
    tap(title_regex)
    time.sleep(3)
    return nodes()


def status():
    return json.loads(sh("curl -s localhost:8765/plugins/games/status"))


def wait_stream(timeout=45):
    t0 = time.time()
    while time.time() - t0 < timeout:
        top = top_activity()
        st = status()
        if "NativeStreamActivity" in top and st.get("recovery", {}).get("state") == "PLAYING":
            return round(time.time() - t0, 1)
        time.sleep(1)
    return None


def reports():
    return set(os.listdir(SESS))


def back_and_report(before, wait=40):
    sh("adb shell input keyevent KEYCODE_BACK")
    for _ in range(wait):
        time.sleep(1)
        new = reports() - before
        if new:
            name = sorted(new)[-1]
            d = json.load(open(os.path.join(SESS, name)))["report"]
            v, dec = d["video"], d["decoder"]
            shutil.copyfile(os.path.join(SESS, name), os.path.join(HERE, name))
            return {"report": name, "duration_ms": d["duration_ms"], "first_clean_idr_ms": v.get("first_clean_idr_ms"),
                    "max_output_gap_ms": dec.get("max_output_gap_ms"), "lost_packets": v.get("lost_packets"),
                    "sequence_resyncs": v.get("sequence_resyncs"), "ssrc_changes": v.get("ssrc_changes"),
                    "rendered_fps": round(dec.get("rendered_frames", 0) / (d["duration_ms"] / 1000), 2)}
    return {"report": None}


def newest_game_log(after_ts):
    files = [f for f in glob.glob(f"{GLOGS}/2026*-game_*.log") if os.path.getmtime(f) >= after_ts - 1]
    files.sort(key=os.path.getctime)
    return files


def state_lines(path):
    try:
        return [l.strip()[:160] for l in open(path, errors="replace") if "[State]" in l or "[SRAM]" in l or "Unloading game" in l]
    except OSError:
        return []


def game_log_created_after(ts):
    c = [f for f in glob.glob(f"{GLOGS}/2026*-game_*.log") if os.path.getctime(f) >= ts - 1]
    return sorted(c, key=os.path.getctime)


def idr_spread(t0, t1):
    rows = []
    for l in open(FRAMES, errors="replace"):
        try:
            r = json.loads(l)
        except Exception:
            continue
        if t0 <= r.get("t", 0) <= t1 and r.get("frames", 0) >= 55:
            rows.append(r["max_bytes"])
    if not rows:
        return {"seconds": 0}
    return {"seconds": len(rows), "distinct": len(set(rows)), "spread_bytes": max(rows) - min(rows),
            "min": min(rows), "max": max(rows)}


def stop_game():
    return P.stop_game()


def save(name, res):
    json.dump(res, open(os.path.join(HERE, f"check{name}.json"), "w"), indent=1)
    log(f"check{name}: {json.dumps(res)[:900]}")


# ---------------------------------------------------------------- checks
def check1():
    """Live session -> tile reads Resume -> same pid, no load, output quickly."""
    res = {}
    stop_game()
    before = reports()
    code, st = P.http(f"launch?id={T3}", "POST")
    pid0 = st.get("pid")
    t_launch = time.time()
    sh("adb shell am force-stop com.safeiot.privyhub; adb shell input keyevent KEYCODE_WAKEUP; adb shell am start -n com.safeiot.privyhub/.MainActivity")
    time.sleep(6)
    sh("adb shell input tap 1008 298")  # RESUME PLAYING preview (TOOLS.md)
    res["first_open_s"] = wait_stream()
    time.sleep(30)
    res["first_session"] = back_and_report(before)
    time.sleep(2)
    st = status()
    res["after_back"] = {"active": st["active"], "paused": st["paused"], "pid": st.get("pid")}
    ns = open_tile(T3_TITLE)
    res["tile_buttons"] = [t for t in texts(ns) if re.fullmatch(r"(?i)resume|launch on companion|options|cancel|start fresh", t)]
    before = reports()
    t_tap = time.time()
    tap(r"^RESUME$")
    res["reopen_s"] = wait_stream()
    time.sleep(8)
    st = status()
    res["pid_after_resume"] = st.get("pid")
    res["same_pid"] = st.get("pid") == pid0
    res["second_session"] = back_and_report(before)
    logs = game_log_created_after(t_launch)
    res["game_logs_since_launch"] = [os.path.basename(f) for f in logs]
    res["state_loading_lines"] = [l for f in logs for l in state_lines(f) if "Loading state" in l]
    res["PASS"] = bool(res["same_pid"] and any(t.lower() == "resume" for t in res["tile_buttons"]) and not res["state_loading_lines"]
                       and len(logs) == 1 and res["second_session"].get("first_clean_idr_ms") is not None
                       and res["second_session"]["first_clean_idr_ms"] < 3000)
    save(1, res)


def prompt_flow(choice_regex):
    """No live session: tile -> Launch on Companion -> prompt -> choice."""
    ns = open_tile(T3_TITLE)
    buttons = [t for t in texts(ns) if re.fullmatch(r"(?i)resume|launch on companion|options|cancel|start fresh", t)]
    tap(r"^LAUNCH ON COMPANION$")
    time.sleep(2.5)
    n, ns2 = find(r"^Recovery Save$", tries=4)
    prompt = n is not None
    options = [t for t in texts(ns2) if re.search(r"recovery save|Copy to slot|Discard|Not now", t, re.I)]
    if prompt:
        tap(choice_regex)
    return {"tile_buttons": buttons, "prompt_shown": prompt, "prompt_options": options}


def check2():
    res = {}
    stop_game()
    pid_prev = status().get("pid")
    H.restore()
    t0 = time.time()
    before = reports()
    res.update(prompt_flow(r"^Resume from recovery save$"))
    res["open_s"] = wait_stream(60)
    st = status()
    res["pid"] = st.get("pid")
    t_play = int(time.time())
    time.sleep(62)
    res["idr_60s"] = idr_spread(t_play + 1, t_play + 61)
    res["report"] = back_and_report(before)
    logs = game_log_created_after(t0)
    res["game_logs"] = [os.path.basename(f) for f in logs]
    res["state_loading_lines"] = [l for f in logs for l in state_lines(f) if "Loading state" in l]
    res["recovery_files_after"] = H.present()
    # a second launch shows no prompt
    time.sleep(2)
    stop_game()
    ns = open_tile(T3_TITLE)
    tap(r"^LAUNCH ON COMPANION$")
    time.sleep(2.5)
    ns2 = nodes()
    res["second_launch_texts"] = [t for t in texts(ns2) if re.search(r"Recovery|Start Fresh|Load Save|Start ", t, re.I)]
    sh("adb shell input keyevent KEYCODE_BACK")
    res["PASS"] = bool(res["prompt_shown"] and res["open_s"] is not None and res["state_loading_lines"]
                       and not any(res["recovery_files_after"].values())
                       and res["idr_60s"].get("spread_bytes", 0) > 20000
                       and not any("Recovery" in t for t in res["second_launch_texts"]))
    save(2, res)


def check3():
    res = {}
    stop_game()
    H.restore()
    t0 = time.time()
    before = reports()
    res.update(prompt_flow(r"^Discard$"))
    res["open_s"] = wait_stream(60)
    time.sleep(8)
    res["recovery_files_after"] = H.present()
    res["report"] = back_and_report(before)
    logs = game_log_created_after(t0)
    res["game_logs"] = [os.path.basename(f) for f in logs]
    res["state_loading_lines"] = [l for f in logs for l in state_lines(f) if "Loading state" in l]
    res["PASS"] = bool(res["prompt_shown"] and not any(res["recovery_files_after"].values())
                       and len(logs) == 1 and not res["state_loading_lines"])
    save(3, res)


def check4():
    res = {}
    stop_game()
    slot1 = os.path.join(STATES, "Tekken 3 (USA).state1")
    res["slot1_before"] = os.path.exists(slot1)
    bak = os.path.join(HERE, "slot_backup")
    os.makedirs(bak, exist_ok=True)
    if os.path.exists(SLOTS):
        shutil.copyfile(SLOTS, os.path.join(bak, "privyhub_state_slots.json"))
    res["slots_index_sha_before"] = H.sha(SLOTS) if os.path.exists(SLOTS) else None
    H.restore()
    t0 = time.time()
    before = reports()
    res.update(prompt_flow(r"^Copy to slot 1$"))
    res["open_s"] = wait_stream(60)
    time.sleep(8)
    res["slot1_sha"] = H.sha(slot1) if os.path.exists(slot1) else None
    res["slot1_equals_recovery"] = res["slot1_sha"] == RECOVERY_SHA
    res["recovery_files_after"] = H.present()
    res["report"] = back_and_report(before)
    logs = game_log_created_after(t0)
    res["game_logs"] = [os.path.basename(f) for f in logs]
    res["state_loading_lines"] = [l for f in logs for l in state_lines(f) if "Loading state" in l]
    stop_game()
    # the validation's slot write is undone: slot 1 was empty before
    if not res["slot1_before"]:
        for f in (slot1, slot1 + ".png"):
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(os.path.join(bak, "privyhub_state_slots.json")):
            shutil.copyfile(os.path.join(bak, "privyhub_state_slots.json"), SLOTS)
    res["slots_index_sha_restored"] = H.sha(SLOTS) if os.path.exists(SLOTS) else None
    res["PASS"] = bool(res["prompt_shown"] and res["slot1_equals_recovery"]
                       and not any(res["recovery_files_after"].values()) and not res["state_loading_lines"])
    save(4, res)


def check5():
    res = {}
    stop_game()
    code, st = P.http(f"launch?id={T3}", "POST")
    old_pid = st.get("pid")
    t0 = time.time()
    res["old"] = {"pid": old_pid, "active": st.get("active"), "paused": st.get("paused")}
    ns = open_tile(OTHER_TITLE)
    res["tile_buttons"] = [t for t in texts(ns) if re.fullmatch(r"(?i)resume|launch on companion|options|cancel|start fresh", t)]
    tap(r"^LAUNCH ON COMPANION$")
    time.sleep(2.5)
    tap(r"^START FRESH$")
    res["open_s"] = wait_stream(60)
    st = status()
    res["new"] = {"pid": st.get("pid"), "title": (st.get("game") or {}).get("title")}
    res["old_pid_alive"] = os.path.exists(f"/proc/{old_pid}") if old_pid else None
    ra = sh("ps -eo pid,args | grep '[R]etroArch-Linux-x86_64.AppImage --config' | awk '{print $1}'").split()
    res["retroarch_pids_now"] = ra
    old_logs = [f for f in glob.glob(f"{GLOGS}/2026*-{T3}.log") if os.path.getctime(f) >= t0 - 60]
    res["old_session_end_lines"] = state_lines(sorted(old_logs, key=os.path.getctime)[-1])[-4:] if old_logs else []
    before = reports()
    res["report"] = back_and_report(before)
    stop_game()
    res["PASS"] = bool(res["old_pid_alive"] is False and res["new"]["pid"] and res["new"]["pid"] != old_pid
                       and any("SRAM" in l for l in res["old_session_end_lines"])
                       and any("Unloading game" in l for l in res["old_session_end_lines"]))
    save(5, res)


def check6():
    res = {}
    stop_game()
    pre_scratch = H.sha(SCRATCH)
    code, st = P.http(f"launch?id={T3}", "POST")
    win = P.window_for(st.get("pid"))
    P.ra("PAUSE_TOGGLE")
    P.wait_status("PLAYING")
    t0 = time.time(); moving = 0
    while time.time() - t0 < 240:
        tmp = os.path.join(HERE, "_probe.md5")
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "x11grab", "-framerate", "60",
                        "-window_id", win, "-i", ":0.0", "-t", "2", "-f", "framemd5", tmp], env=P.ENV)
        u = len({l.split(",")[-1] for l in open(tmp) if l[0] != "#"}); os.remove(tmp)
        moving = moving + 1 if u > 100 else 0
        if moving >= 2:
            break
        time.sleep(3)
    res["seconds_to_fight"] = round(time.time() - t0)
    res["save_reply"] = P.ra("SAVE_STATE_SLOT 0", reply=True)
    time.sleep(2)
    res["gameplay_state_sha"] = H.sha(SCRATCH)
    stop_game()
    # stage the gameplay state as the recovery save
    shutil.copyfile(SCRATCH, H.PAIRS[0][1])
    if os.path.exists(SCRATCH + ".png"):
        shutil.copyfile(SCRATCH + ".png", H.PAIRS[1][1])
    shutil.copyfile(os.path.join(H.COPY, "privyhub_recovery_save.json"), H.INDEX)
    res["staged_sha"] = H.sha(H.PAIRS[0][1])
    before = reports()
    t1 = time.time()
    res.update(prompt_flow(r"^Resume from recovery save$"))
    res["open_s"] = wait_stream(60)
    time.sleep(3)
    st = status()
    win2 = P.window_for(st.get("pid"))
    res["grab"] = P.grab(win2, "check6")
    res["report"] = back_and_report(before)
    logs = game_log_created_after(t1)
    res["state_loading_lines"] = [l for f in logs for l in state_lines(f) if "Loading state" in l]
    res["recovery_files_after"] = H.present()
    stop_game()
    # restore the slot-0 scratch to its pre-check bytes (the N150 recovery bytes)
    shutil.copyfile(os.path.join(REPO, "docs/memory/evidence/d_base_r3c_2026-09-22/pre_state/Tekken 3 (USA).state"), SCRATCH)
    shutil.copyfile(os.path.join(REPO, "docs/memory/evidence/d_base_r3c_2026-09-22/pre_state/Tekken 3 (USA).state.png"), SCRATCH + ".png")
    res["scratch_restored"] = H.sha(SCRATCH) == pre_scratch
    g = res["grab"]
    res["PASS"] = bool(res["prompt_shown"] and res["state_loading_lines"] and g["distinct"] >= 1000
                       and not any(res["recovery_files_after"].values()))
    save(6, res)


if __name__ == "__main__":
    for c in sys.argv[1:]:
        try:
            {"1": check1, "2": check2, "3": check3, "4": check4, "5": check5, "6": check6}[c]()
        except Exception as exc:
            log(f"check{c}: ERROR {type(exc).__name__}: {str(exc)[:400]}")
            json.dump({"error": f"{type(exc).__name__}: {exc}"}, open(os.path.join(HERE, f"check{c}.json"), "w"))
