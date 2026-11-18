# B114's child scenario (appended to B103's harness head; run by test_b114.py). Not a test module by itself.
# The stream stub models what the real stream does that B110's stub did not: its own RLock held across start / stop /
# status / the recovery's restart / the bitrate's step; the capture bound to the process it was started for (that
# process gone -> the stream down until the next start). A client thread plays the onn: client-health every 0.1 s
# (the real observe() path), heartbeats with the real output age, the stall datagrams (PHS1) through the real stall
# worker. Other threads call status / party-minigame-result throughout; Home / RESUME / END are sent during matches.
import struct, traceback, collections
try:
    import party_session as party
    party.QUIT_WAIT_S = 1.0
except ImportError:
    party = None
import stall_owner
stall_owner.V2_MS = 1000
import stall_signal as ss
board_dir = Path(args["board_dir"])
cmds = []
def fake_run(cmd, timeout=3.0):
    cmds.append(list(cmd))
    pid = (board_dir / "pid").read_text() if (board_dir / "pid").exists() else ""
    out, rc = "", 0
    if cmd[:4] == ["xdotool", "search", "--onlyvisible", "--class"]:
        out = "4242\n" if pid else ""
    elif cmd[:2] == ["xdotool", "getwindowpid"]:
        out = pid + "\n"
    elif cmd[:2] == ["xdotool", "windowactivate"]:
        with (board_dir / "keys").open("a") as fh:
            fh.write(cmd[-1] + "\n")
    elif cmd[:2] == ["pactl", "list"]:
        out = f'application.process.id = "{pid}"\n' if pid else ""
    else:
        rc = 1
    return types.SimpleNamespace(returncode=rc, stdout=out, stderr="")
m._party_session_kwargs = {"run": fake_run, "devices": Path(args["devices"])}
import native_session_io as nsio
bridge = nsio.NativeControllerBridge(Path(args["board_dir"]) / "bridge")
bridge._gamepads = ["P1", "P2", "P3", "P4"]
bridge._controller_backend = "linux_uinput"
bridge._write_linux_report_locked = lambda index, report, *a, **k: None
T0 = time.monotonic()
B139_KEYS = ("video_font_enable", "menu_show_load_content_animation")
def b139_config(cmd):
    """B139: the session config RetroArch was started with — its B139 keys (every assignment) and the text normalised
    (the temp root and the per-launch command port), for byte-for-byte comparisons across runs."""
    cmd = [str(c) for c in cmd]
    if "--config" not in cmd:
        return {"keys": {}, "text": None}
    cfg = Path(cmd[cmd.index("--config") + 1]); cfg = cfg if cfg.is_absolute() else root / cfg
    text = cfg.read_text()
    keys = {k: re.findall(rf'(?m)^[ \t]*{k}[ \t]*=[ \t]*"([^"]*)"', text) for k in B139_KEYS}
    norm = text
    for form in {str(root.resolve()), str(root)}:
        norm = norm.replace(form, "<root>")
    norm = re.sub(r'(?m)^(network_cmd_port = )"\d+"', r'\1"<port>"', norm)
    return {"keys": {k: v for k, v in keys.items() if v}, "text": norm}
def now_s():
    return round(time.monotonic() - T0, 3)


class StubStream:
    """The real stream's shape: one RLock over start / stop / status / restarts; the capture follows one process."""
    def __init__(self):
        self._lock = threading.RLock()
        self.active = False
        self.captured = None
        self.captured_pid = None
        self.restarting = False
        self.frames_at = time.monotonic()
        self.events = []
        self.start_s = float(args.get("start_s", 0.6))
        self.gate = threading.Event(); self.gate.set()          # cleared: a start blocks inside the lock (stuck)
        self.emu_lock_in_start = []
        self._session_io = types.SimpleNamespace(controller=bridge)
    def _proc_for(self, pid):
        cands = [m.process]
        st = getattr(m, "_party_stash", None)
        if isinstance(st, dict):
            cands.append(st.get("process"))
        for p in cands:
            if p is not None and getattr(p, "pid", None) == pid:
                return p
        return None
    def _reap(self):
        if self.active and (self.captured is None or self.captured.poll() is not None):
            self.active = False
            self.events.append(["down", self.captured_pid, now_s()])
    def flowing(self):
        return self.active and not self.restarting and self.captured is not None and self.captured.poll() is None
    def status(self):
        with self._lock:
            self._reap()
            return {"active": self.active, "bitrate_kbps": 7000}
    def start(self, client_ip=None, port=None, managed_process_id=None):
        self.emu_lock_in_start.append(bool(m.lock._is_owned()))
        with self._lock:
            self.restarting = True
            self.events.append(["start_begin", managed_process_id, now_s()])
            time.sleep(self.start_s / 2)                         # the old capture, encoder and sound stopped
            self.gate.wait()
            proc = self._proc_for(managed_process_id)
            time.sleep(self.start_s / 2)                         # the new encoder, its check, the new sound
            self.captured, self.captured_pid = proc, managed_process_id
            self.active = proc is not None and proc.poll() is None
            self.restarting = False
            self.frames_at = time.monotonic()
            self.events.append(["start", managed_process_id, now_s()])
            return {"active": self.active, "bitrate_kbps": 7000}
    def stop(self):
        with self._lock:
            self.active = False
            self.events.append(["stop", None, now_s()])
            return {"active": False}
    def end_game_session(self):
        with self._lock:
            self.active = False
            self.events.append(["end_session", None, now_s()])
            return {"active": False}
    def recovery_restart_encoder(self):
        with self._lock:
            self.restarting = True
            time.sleep(self.start_s / 2)
            self.restarting = False
            self.frames_at = time.monotonic()
            self.events.append(["restart", self.captured_pid, now_s()])
            return {"video": {}}
    def adaptive_level_transition(self, kbps):
        with self._lock:
            time.sleep(0.2)
            self.events.append(["level", kbps, now_s()])
            return {"ok": True, "target_bitrate_kbps": kbps}
    def __getattr__(self, name):
        return Inert()


stream = StubStream()
g._native_stream = stream
g._adaptive_bitrate.bind(actuator=stream.adaptive_level_transition, context=g._adaptive_bitrate_context,
                         serial_lock=stream._lock, recovery_state=g._recovery.current_state)
out = {"steps": {}, "lat": collections.defaultdict(list), "slow": []}
S = out["steps"]
S["abr_live_same"] = bool(svc.adaptive_bitrate_controller(svc.PROJECT_ROOT) is g._adaptive_bitrate)
S["stall_worker"] = g._recovery._client_stall is not None


def mg_on():
    """A mini game on (not yet finished) — the calls the 2-s bound is about."""
    lay = getattr(g, "_party_minigame_obj", None)
    mg_ = getattr(lay, "mg", None) if lay is not None else None
    return mg_ is not None and not (mg_.get("closed") and mg_.get("actor_done", True))


def timed(kind, method, path, timeout=12):
    on = mg_on()
    t = time.monotonic()
    try:
        r = call(method, path, timeout=timeout)
    except Exception as exc:
        r = {"code": 0, "raw": "", "body": {"error": f"{type(exc).__name__}"}}
    dt = round(time.monotonic() - t, 3)
    on = on or mg_on()
    out["lat"][kind + ("" if on else "_no_minigame")].append(dt)
    if dt >= 2.0:
        out["slow"].append([kind, dt, now_s(), r["code"], on])
    return r


class Client:
    """The onn: in the stream or not (Home leaves it, RESUME returns)."""
    def __init__(self):
        self.in_stream = False; self.seq = 0; self.hb = 0; self.stalling = False; self.stop = False
        self.stalls_sent = 0; self.ends_sent = 0; self.silent = False
        g._recovery._client_packet_age_ms = lambda: 20.0 if self.in_stream else None
        for target, every in ((self.health, 0.1), (self.heartbeat, 0.25), (self.stall_watch, 0.05)):
            threading.Thread(target=self.loop, args=(target, every), daemon=True).start()
    def loop(self, fn, every):
        while not self.stop:
            if self.in_stream:
                try:
                    fn()
                except Exception:
                    pass
            time.sleep(every)
    def age_ms(self):
        if stream.flowing() and not self.silent:
            stream.frames_at = time.monotonic()
        return int((time.monotonic() - stream.frames_at) * 1000)
    def report(self):
        """The onn's client-health report (privyhub_client_health_v1), its counters rising."""
        self.hseq = getattr(self, "hseq", 0) + 1
        n = self.hseq
        v = {k: 0 for k in ("lost_packets", "dropped_frames", "fec_recovered_packets", "fec_unrecoverable_groups",
                            "late_or_reordered_packets", "forward_gap_events")}
        v.update(packets=600 * n, recent_fps=59.8, recent_mbps=7.0, waiting_for_idr=False)
        d = {k: 0 for k in ("queued_frames", "dropped_frames", "queue_overflow_drops", "stale_output_drops")}
        d.update(rendered_frames=60 * n, queue_depth=0, latest_rx_to_decode_ms=8,
                 latest_output_gap_ms=min(self.age_ms(), 60000), hardware_accelerated=True, vendor_codec=True,
                 low_latency_enabled=True)
        return {"schema": "privyhub_client_health_v1", "sequence": n, "interval_ms": 2000,
                "session_elapsed_ms": 100 * n, "video": v, "decoder": d}
    def health(self):
        req = urllib.request.Request(f"http://127.0.0.1:{port}/diagnostics/client-health", method="POST",
                                     data=json.dumps(self.report()).encode(),
                                     headers={"Content-Type": "application/json"})
        t = time.monotonic()
        try:
            urllib.request.urlopen(req, timeout=12).read()
        except Exception:
            pass
        out["lat"]["client_health"].append(round(time.monotonic() - t, 3))
    def heartbeat(self):
        self.hb += 1
        timed("heartbeat", "POST", f"/plugins/games/native-stream-heartbeat?sequence={self.hb}&interval_ms=2000"
              f"&last_output_age_ms={self.age_ms()}&rendered_frames={600 + self.hb}&queued_frames=0&rx_packets=900"
              f"&elapsed_ms={self.hb * 250}")
    def stall_watch(self):
        age = self.age_ms()
        sig = g._recovery._client_stall
        if age >= 400:
            self.seq += 1; self.stalls_sent += 1; self.stalling = True
            sig.on_datagram(ss.PACKET.pack(ss.MAGIC, ss.KIND_STALL, 0, 0, self.seq, 1000 + self.seq, age), time.monotonic())
        elif self.stalling and age < 100:
            self.seq += 1; self.ends_sent += 1; self.stalling = False
            sig.on_datagram(ss.PACKET.pack(ss.MAGIC, ss.KIND_END, 0, 0, self.seq, 1000 + self.seq, age), time.monotonic())


client = Client()
watching = {"on": True}
QUIET = set()                                 # B133: kinds whose polls are paused (the board no longer asking)
def watcher(kind, path):
    while watching["on"]:
        if kind not in QUIET:
            timed(kind, "GET", path)
        time.sleep(0.1)
for kind, path in (("status", "/plugins/games/status"), ("result", "/plugins/games/party-minigame-result"),
                   ("ns_status", "/plugins/games/native-stream-status")):
    threading.Thread(target=watcher, args=(kind, path), daemon=True).start()


def stacks():
    names = {t.ident: t.name for t in threading.enumerate()}
    res = []
    for ident, frame in sys._current_frames().items():
        if ident == threading.get_ident():
            continue
        fr = [f"{Path(f.filename).name}:{f.name}:{f.lineno}" for f in traceback.extract_stack(frame)][-6:]
        res.append({"thread": re.sub(r"\d+", "#", names.get(ident, "?")), "top": fr})
    return res


def finish(hung_at=None):
    watching["on"] = False; client.stop = True
    out["hung"] = hung_at
    if hung_at is not None:
        st = stacks()
        out["stacks"] = st
        out["waiting_on_emu_lock"] = sum(1 for s in st if any(":status:" in x or ":pause:" in x or ":stop:" in x or ":end:" in x for x in s["top"][-2:]) and any("emulator_manager.py" in x for x in s["top"][-2:]))
        out["mg_thread"] = [s for s in st if s["thread"].startswith("party-minigame")]
    out["stream_events"] = stream.events
    out["abr_samples"] = sum(1 for r in abr_rows() if r.get("event") == "sample")
    out["emu_lock_in_start"] = stream.emu_lock_in_start
    out["lat"] = {k: {"n": len(v), "max": max(v) if v else None} for k, v in out["lat"].items()}
    text = json.dumps(out)
    for form in {str(root), str(root.resolve())}:
        text = text.replace(form, "<root>")
    sys.stdout.write(text + "\n"); sys.stdout.flush()
    os._exit(0)


def keys():
    p = board_dir / "keys"
    return p.read_text().split() if p.exists() else []
def rows():
    p = root / "logs/games/party.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.is_file() else []
def rec_rows():
    p = g._recovery.log_path()
    out_ = []
    if p.is_file():
        for l in p.read_text().splitlines():
            try:
                out_.append(json.loads(l))
            except ValueError:
                pass
    return out_
def abr_rows():
    p = root / "logs/games/adaptive_bitrate_shadow.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.is_file() else []
def result_now():
    return call("GET", "/plugins/games/party-minigame-result", timeout=12)["body"]
def wait_for(pred, bound):
    end = time.monotonic() + bound; b = {}
    while time.monotonic() < end:
        try:
            b = result_now()
        except Exception:
            b = {}
        if pred(b):
            return b
        time.sleep(0.05)
    return dict(b, timeout=True)
def wait_until(pred, bound):
    end = time.monotonic() + bound
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False


cfg = Path(os.environ["PRIVYHUB_PARTY_CONFIG"])
cfg.write_text(json.dumps({"godot": args["board"], "project": args["project"], "pictures": args["pictures"]}))
board_nodes = call("GET", "/plugins/games/games?system=party")["body"].get("nodes", [])
board_id = next((n["id"] for n in board_nodes if n.get("node_type") == "game"), None)
title = args["id"]


def board_pid_now():
    try:
        return int((board_dir / "pid").read_text())
    except (OSError, ValueError):
        return None


def board_up(tag):
    """The board as the session, the onn's stream up (as the onn has it)."""
    if board_pid_now() is not None and call("GET", "/plugins/games/status")["body"].get("launch_kind") == "godot":
        call("POST", "/plugins/games/stop")                  # the board left by the last case: a fresh one
        wait_until(lambda: board_pid_now() is None, 10)
    (board_dir / "keys").unlink(missing_ok=True)
    S[tag + "_board_launch"] = call("POST", f"/plugins/games/launch?id={board_id}")["code"]
    call("POST", "/plugins/games/native-stream-start?port=48100")
    call("POST", "/plugins/games/native-stream-ready")
    client.in_stream = True
    return int((board_dir / "pid").read_text())


if args["mode"] == "probe":
    pr = S["probe"] = {}
    try:
        acc = svc.CLIENT_HEALTH_STORE.accept(client.report(), payload_bytes=400)
        pr["accept"] = str(type(acc))
        ns_ = g.handle("native-stream-status", "")
        pr["ns_keys"] = sorted(ns_)[:40]
        tel = svc.STREAM_TELEMETRY_STORE.accept(client_health_feedback=svc.CLIENT_HEALTH_STORE.snapshot(),
                                                native_stream_status=ns_)
        pr["tel"] = str(type(tel))
        abr = svc.adaptive_bitrate_controller(svc.PROJECT_ROOT)
        pr["live"] = bool(svc.adaptive_bitrate_is_live(abr)); pr["log"] = str(abr.log_path)
        import adaptive_bitrate as ab_
        pr["sample"] = str(ab_._sample(tel))[:300]
        abr.observe(tel, stream_bitrate_kbps=7000, native_status=ns_)
        pr["rows"] = len(abr_rows())
    except Exception as exc:
        pr["error"] = f"{type(exc).__name__}: {exc}"[:400]
    finish()

if args["mode"] == "today":
    for k, (meth, path) in {"list": ("GET", "/plugins/games/party-minigames"),
                            "start": ("POST", "/plugins/games/party-minigame-start?id=x&seats=1,2"),
                            "result": ("GET", "/plugins/games/party-minigame-result"),
                            "end": ("POST", "/plugins/games/party-minigame-end"),
                            "go": ("POST", "/plugins/games/party-minigame-go"),     # B133
                            "status_idle": ("GET", "/plugins/games/status"),
                            "home_idle": ("POST", "/plugins/games/native-stream-stop"),
                            "stop_idle": ("POST", "/plugins/games/stop")}.items():
        S[k] = call(meth, path)
    # B124: a title's start with the prompt answers its players and ports as today (no board without the flag)
    _cfg_cmds = []
    _P0 = em.subprocess.Popen
    def _pk(cmd, **kw):                                # B139: the users' launch's session config, kept
        _cfg_cmds.append(b139_config(cmd))
        return _P0(cmd, **kw)
    em.subprocess.Popen = _pk
    call("POST", f"/plugins/games/launch?id={title}")
    em.subprocess.Popen = _P0
    S["b139_users_cfg"] = _cfg_cmds[0] if _cfg_cmds else None
    pr = call("POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1")["body"]
    S["ports_today"] = {"players": pr.get("players"), "players_source": pr.get("players_source"),
                        "ports_set": pr.get("ports_set")}
    call("POST", "/plugins/games/stop")
    finish()

if args["mode"] == "cheat_today":
    # B127: the onn's Extras launch and the routes B127 touches, as the flags leave them (HEAD's code against mine)
    def _apply(self):
        self._active_cheat_session["activation_verified"] = True
        return dict(self._active_cheat_session)
    em.EmulatorManager._apply_active_cheat_profile = _apply
    for k, (meth, path) in {"launch_cheat": ("POST", f"/plugins/games/launch?id={title}&cheat_source=0&cheat_indexes=1"),
                            "status_cheat": ("GET", "/plugins/games/status"),
                            "h7_start": ("POST", "/plugins/games/h7-start?bench=1"),
                            "h7_result": ("GET", "/plugins/games/h7-result"),
                            "list": ("GET", "/plugins/games/party-minigames"),
                            "start": ("POST", "/plugins/games/party-minigame-start?id=x&seats=1,2"),
                            "stop_cheat": ("POST", "/plugins/games/stop"),
                            "profiles": ("POST", f"/plugins/games/cheat-profiles?id={title}"),
                            "launch_plain": ("POST", f"/plugins/games/launch?id={title}"),
                            "stop_plain": ("POST", "/plugins/games/stop")}.items():
        S[k] = call(meth, path)
    # B131: SAVE / LOAD with the board as the session (no mini game) — today's answers
    _nodes = call("GET", "/plugins/games/games?system=party")["body"].get("nodes", []) if args.get("board_saveload") else []
    _bid = next((n["id"] for n in _nodes if n.get("node_type") == "game"), None)
    if _bid is not None:
        S["board_launch"] = call("POST", f"/plugins/games/launch?id={_bid}")
        S["board_launch"] = {"code": S["board_launch"]["code"], "raw": "", "body": {}}
        S["board_save"] = call("POST", "/plugins/games/save-state?slot=1")
        S["board_load"] = call("POST", "/plugins/games/load-state?slot=1")
        S["board_stop"] = {"code": call("POST", "/plugins/games/stop")["code"], "raw": "", "body": {}}
    finish()

rules_ = Path(rules); rules_.mkdir(parents=True, exist_ok=True)
for name in os.listdir(args["spec_dir"]):
    shutil.copyfile(Path(args["spec_dir"], name), rules_ / name.replace("GAME", title))
js_ = json.loads((rules_ / f"{title}.endscreen.json").read_text())
js_["arrays"] = f"{title}.endscreen.npz"
(rules_ / f"{title}.endscreen.json").write_text(json.dumps(js_))
(rules_ / f"{title}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
(rules_ / f"{title}.party.json").write_text(json.dumps({"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}))
token = call("GET", "/plugins/games/party-minigames")["body"]["minigames"][0]["id"]
mini = g._h7_minigame_runner(); mini.picture = pic; mini.read_every = 0.2; mini.recognise_s = 1.6
layer = g._party_minigame_runner(); layer.tick = 0.05
LIMITS = ("start_limit_s", "switch_limit_s", "step_grace_s")
S["limits_present"] = [k for k in LIMITS if hasattr(layer, k)]


def one(tag, seats, script, during=None, home_resume=False, tok=None):
    pic.set(script)
    r0, q0, k0 = len(rows()), len(rec_rows()), len(keys())
    a0, e0 = len(abr_rows()), len(stream.events)
    S[tag + "_start"] = timed("start", "POST", f"/plugins/games/party-minigame-start?id={tok or token}&seats={seats}")
    p = wait_for(lambda b: b.get("state") in ("playing", "ended", "given_up"), 25)
    S[tag + "_playing"] = p
    if p.get("timeout"):
        S[tag + "_rows"] = [r["step"] for r in rows()[r0:]]
        finish(hung_at=tag + ": never playing (" + str(p.get("state")) + ")")
    k_play = len(keys())
    if home_resume:
        time.sleep(0.4)
        h = timed("home", "POST", "/plugins/games/native-stream-stop")
        client.in_stream = False
        time.sleep(0.3)
        S[tag + "_title_paused_after_home"] = fake["ra"].paused if "ra" in fake else None
        rs = timed("resume_start", "POST", "/plugins/games/native-stream-start?port=48100", timeout=30)
        client.in_stream = True
        rr = timed("resume_ready", "POST", "/plugins/games/native-stream-ready", timeout=30)
        S[tag + "_home"] = {"code": h["code"], "taken": h["body"].get("taken")}
        S[tag + "_resume"] = {"start": rs["code"], "start_active": rs["body"].get("active"), "ready": rr["code"],
                              "released": rr["body"].get("released")}
        S[tag + "_title_running_after_resume"] = (not fake["ra"].paused) if "ra" in fake else None
    if during is not None:
        during(tag)
    e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 40)
    S[tag] = e
    if e.get("timeout"):
        finish(hung_at=tag + ": never ended")
    k_end = len(keys())
    S[tag + "_end"] = timed("board_end", "POST", "/plugins/games/party-minigame-end")
    S[tag + "_closed"] = wait_for(lambda b: b.get("closed"), 20).get("closed")
    S[tag + "_end_again"] = call("POST", "/plugins/games/party-minigame-end")["body"].get("again")
    S[tag + "_title_gone"] = fake["ra"].poll() is not None if "ra" in fake else None
    S[tag + "_route_after"] = bridge._party_route
    S[tag + "_keys_in_match"] = keys()[k_play:k_end]
    S[tag + "_rows"] = [r["step"] for r in rows()[r0:]]
    S[tag + "_stream_rows"] = [{k: v for k, v in r.items() if k in ("window", "switched", "why")}
                               for r in rows()[r0:] if r["step"] == "minigame_stream"]
    S[tag + "_rec"] = [r.get("event") for r in rec_rows()[q0:]]
    S[tag + "_status_kind"] = call("GET", "/plugins/games/status")["body"].get("launch_kind")
    S[tag + "_keys_all"] = keys()[k0:]
    S[tag + "_abr"] = [[r.get("event"), r.get("source")] for r in abr_rows()[a0:]
                       if r.get("event") in ("ssrc_change", "escalation_armed", "transition", "transition_done")]
    S[tag + "_stream_events"] = [e[:2] for e in stream.events[e0:]]
    S[tag + "_switches"] = [{k: v for k, v in r.items() if k in ("window", "switched", "planned", "seconds", "why")}
                            for r in rows()[r0:] if r["step"] == "minigame_stream"]
    n_sw = sum(1 for r in rows()[r0:] if r["step"] == "minigame_stream" and r.get("switched"))
    wait_until(lambda: sum(1 for r in rows()[r0:] if r["step"] == "minigame_switch_window") >= n_sw, 6)
    S[tag + "_windows"] = [{k: v for k, v in r.items() if k != "at_utc" and k != "schema"}
                           for r in rows()[r0:] if r["step"] == "minigame_switch_window"]
    S[tag + "_stalls_sent"] = client.stalls_sent
    t_ = time.monotonic()
    S[tag + "_board_picture_back"] = wait_until(lambda: stream.flowing() and stream.captured_pid == board_pid_now(), 20)
    S[tag + "_board_picture_s"] = round(time.monotonic() - t_, 2)


END1 = ["start"] * 3 + ["other"] * 6 + ["end_P1"] * 40
END2 = ["start"] * 3 + ["other"] * 30 + ["end_P2"] * 40
END3 = ["start"] * 3 + ["other"] * 60 + ["end_P1"] * 40
board_pid = board_up("b1")
out["board_pid"] = board_pid
if args["mode"] == "four":
    # B124: a four-player title (an N64 one, B122's version-3 spec, B123's places sidecar) beside the two-player one
    n64 = args["n64_id"]
    v3 = Path(args["v3"]); js4 = json.loads(v3.read_text())
    shutil.copyfile(v3.with_name(js4["arrays"]), rules_ / f"{n64}.endscreen.npz")
    js4["arrays"] = f"{n64}.endscreen.npz"
    (rules_ / f"{n64}.endscreen.json").write_text(json.dumps(js4))
    (rules_ / f"{n64}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
    (rules_ / f"{n64}.party.json").write_text(json.dumps({"players": 4}))      # places_to_scores left out: 4,3,2,1
    def folder():                                     # the fake's slot folder: the running title's core's own
        return m._state_root() / ("Mupen64Plus-Next" if m._n64_core else "Beetle PSX HW")
    listed = call("GET", "/plugins/games/party-minigames")["body"]["minigames"]
    S["four_list"] = sorted(e["players"] for e in listed)
    tok2 = next(e["id"] for e in listed if e["players"] == 2)
    tok4 = next(e["id"] for e in listed if e["players"] == 4)
    pr = call("POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1")["body"]
    call("POST", "/plugins/games/native-stream-ready")
    S["board_ports"] = {"players": pr.get("players"), "players_source": pr.get("players_source"),
                        "ports_set": pr.get("ports_set")}
    S["on_hub_word"] = party.launch_env({}).get("PRIVYPARTY_ON_HUB") if party is not None else None
    S["refuse_4p_two_seats"] = call("POST", f"/plugins/games/party-minigame-start?id={tok4}&seats=1,2")
    S["refuse_2p_four_seats"] = call("POST", f"/plugins/games/party-minigame-start?id={tok2}&seats=1,2,3,4")
    R2143 = ["s4start"] * 4 + ["s4other"] * 8 + ["s4r2143"] * 40
    def four_during(tag):
        S[tag + "_route_during"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
        time.sleep(0.3)
        timed("home", "POST", "/plugins/games/native-stream-stop")
        client.in_stream = False
        time.sleep(0.2)
        rs = timed("resume_start", "POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1", timeout=30)
        client.in_stream = True
        timed("resume_ready", "POST", "/plugins/games/native-stream-ready", timeout=30)
        S[tag + "_resume_ports"] = {"players": rs["body"].get("players"),
                                    "ports": (rs["body"].get("ports_set") or {}).get("players")}
    def two_during(tag):
        S[tag + "_route_during"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
    one("a2", "1,2", END1, tok=tok2, during=two_during)
    one("b4", "3,1,4,2", R2143, tok=tok4, during=four_during)
    one("c2", "2,1", END2, tok=tok2, during=two_during)
    one("d4", "1,2,3,4", R2143, tok=tok4, during=two_during)
    S["abr_all"] = [[r.get("event"), r.get("source")] for r in abr_rows()
                    if r.get("event") in ("ssrc_change", "escalation_armed", "transition", "transition_done")]
    timed("end_onn", "POST", "/plugins/games/stop")
    finish()
if args["mode"] == "cheat":
    # B127: the mini games under each title's cheat setup (the setups made by the onn's Extras launch from loopback)
    n64 = args["n64_id"]
    LAST, LOADS, POPENS, APPLIED, LQ = {}, [], [], [], []
    _FR = em.subprocess.Popen
    B139_CFG = []
    def _popen(cmd, **kw):                            # RetroArch's command line kept (its session config)
        LAST["cmd"] = [str(c) for c in cmd]
        POPENS.append(1)
        _lay = getattr(g, "_party_minigame_obj", None); _mg = getattr(_lay, "mg", None)
        B139_CFG.append({"party": bool(_mg is not None and not _mg.get("launched") and not _mg.get("closed")),
                         "keys": b139_config(cmd)["keys"]})
        return _FR(cmd, **kw)
    em.subprocess.Popen = _popen
    def _apply(self):                                 # RetroArch's network side of the cheat toggles (B83's stub)
        APPLIED.append(self._active_cheat_session.get("profile_id"))
        self._active_cheat_session["activation_verified"] = True
        return dict(self._active_cheat_session)
    em.EmulatorManager._apply_active_cheat_profile = _apply
    _hp = g.handle_post
    def _hp_kept(action, raw_query):
        if action == "launch":
            LQ.append(raw_query)
        return _hp(action, raw_query)
    g.handle_post = _hp_kept
    def config_states():
        """Where RetroArch itself reads states: the session config's one savestate_directory (the launch wrote it)."""
        cmd = LAST["cmd"]
        cfg = Path(cmd[cmd.index("--config") + 1])
        cfg = cfg if cfg.is_absolute() else root / cfg
        mm = re.search(r'(?m)^\s*savestate_directory\s*=\s*"([^"]*)"', cfg.read_text())
        p = Path(mm.group(1))
        return p if p.is_absolute() else root / p
    def folder():                                     # the fake's slot folder: the config's + the core's own
        d = config_states() / ("Mupen64Plus-Next" if m._n64_core else "Beetle PSX HW")
        LOADS.append(str(d.resolve().relative_to(root.resolve())))
        return d
    def mem():
        return [int.from_bytes(fake["ra"].mem[args["p1"]:args["p1"] + 2], "little"),
                int.from_bytes(fake["ra"].mem[args["p2"]:args["p2"] + 2], "little")]
    def tree_hashes(*rels):
        outh = {}
        for rel in rels:
            base = root / rel
            for p in sorted(base.rglob("*")) if base.is_dir() else []:
                if p.is_file():
                    outh[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
        return outh
    def scratch_anywhere():
        return sorted(str(p.relative_to(root)) for p in (root / "data").rglob("*.state8"))
    PROF = "data/games/retroarch/cheat_profiles"
    import h7_minigame as h7m
    # the N64 title's spec (B122's version 3) and its places sidecar beside the PS1 one (B124's)
    v3 = Path(args["v3"]); js4 = json.loads(v3.read_text())
    shutil.copyfile(v3.with_name(js4["arrays"]), rules_ / f"{n64}.endscreen.npz")
    js4["arrays"] = f"{n64}.endscreen.npz"
    (rules_ / f"{n64}.endscreen.json").write_text(json.dumps(js4))
    # 1. the setups as the user made them: the onn's Extras launch from loopback, stopped; read back as the onn does
    call("POST", "/plugins/games/stop")
    wait_until(lambda: board_pid_now() is None, 10)
    setups, stems = {}, {}
    for key, gid, picks in (("ps1", title, "1"), ("n64", n64, "5")):
        r = call("POST", f"/plugins/games/launch?id={gid}&cheat_source=0&cheat_indexes={picks}")
        S[f"c_make_{key}"] = {"code": r["code"], "profile_id": ((r["body"].get("cheat_session") or {}).get("profile_id")),
                              "error": r["body"].get("error")}
        stems[key] = m._active_state_stem() if m.active_game else None
        call("POST", "/plugins/games/stop")
        profs = call("POST", f"/plugins/games/cheat-profiles?id={gid}")["body"].get("profiles") or []
        S[f"c_profiles_{key}"] = len(profs)
        p = profs[0]
        setups[key] = {"source_index": p["source_index"], "enabled_cheat_indexes": p["enabled_cheat_indexes"],
                       "profile_id": p["profile_id"]}
        S[f"c_setup_{key}"] = {"source_index": p["source_index"], "enabled": p["enabled_cheat_indexes"],
                               "same_id_as_launch": p["profile_id"] == S[f"c_make_{key}"]["profile_id"]}
        sroot = root / PROF / gid / p["profile_id"]
        core = "Mupen64Plus-Next" if key == "n64" else "Beetle PSX HW"
        for sub, names in (("states", (".state", ".state1", ".state1.png")), ("saves", (".srm",))):
            (sroot / sub / core).mkdir(parents=True, exist_ok=True)
            for nm in names:
                (sroot / sub / core / (stems[key] + nm)).write_bytes(os.urandom(96))
    gid_of = {"ps1": title, "n64": n64}
    (root / "data/games/retroarch/states/Beetle PSX HW").mkdir(parents=True, exist_ok=True)
    (root / "data/games/retroarch/states/Beetle PSX HW" / (stems["ps1"] + ".state1")).write_bytes(os.urandom(64))
    before = tree_hashes(PROF, "data/games/retroarch/states")
    S["c_files_hashed"] = len(before)
    dirs_before = sorted(str(p.relative_to(root)) for p in (root / PROF).glob("*/*"))
    # 2. h7-start under each setup (bench: no stream), the begin the setup's own, into the setup's own folder
    def setup_states(key):
        return f"{PROF}/{gid_of[key]}/{setups[key]['profile_id']}/states"
    q_ps1 = f"id={title}&cheat_source={setups['ps1']['source_index']}&cheat_indexes=" + \
            ",".join(map(str, setups["ps1"]["enabled_cheat_indexes"]))
    q_n64 = f"id={n64}&cheat_source={setups['n64']['source_index']}&cheat_indexes=" + \
            ",".join(map(str, setups["n64"]["enabled_cheat_indexes"]))
    call("POST", "/plugins/games/launch?" + q_ps1)
    fake["ra"].paused = False
    S["c_ps1_session"] = (m._active_cheat_session or {}).get("profile_id") == setups["ps1"]["profile_id"]
    pic.set(["start"] * 3 + ["other"] * 200)
    S["c_h7_ps1_normal"] = call("POST", "/plugins/games/h7-start?bench=1")["body"]
    call("POST", "/plugins/games/h7-stop")
    (rules_ / h7m.setup_begin_name(title, setups["ps1"]["profile_id"])).write_text(json.dumps({"P1": 7, "P2": 9}))
    n0 = len(LOADS)
    S["c_h7_ps1_setup"] = call("POST", "/plugins/games/h7-start?bench=1")["body"]
    S["c_h7_ps1_loaded_from"] = LOADS[n0:]
    S["c_h7_ps1_want"] = setup_states("ps1") + "/Beetle PSX HW"
    S["c_h7_ps1_mem"] = mem()
    S["c_h7_ps1_scratch"] = scratch_anywhere()
    call("POST", "/plugins/games/h7-stop")
    call("POST", "/plugins/games/stop")
    call("POST", "/plugins/games/launch?" + q_n64)
    ra = fake["ra"]; ra.paused = False
    (rules_ / h7m.setup_begin_name(n64, setups["n64"]["profile_id"])).write_text(json.dumps({"P1": 3, "P2": 4}))
    n0, l0 = len(LOADS), len(ra.log)
    S["c_h7_n64_running"] = call("POST", "/plugins/games/h7-start?bench=1")
    S["c_h7_n64_running_sent"] = [c for c in ra.log[l0:] if c == "LOAD_STATE_SLOT"]
    ra.paused = True
    S["c_h7_n64_paused"] = call("POST", "/plugins/games/h7-start?bench=1")["body"]
    S["c_h7_n64_loaded_from"] = LOADS[n0:]
    S["c_h7_n64_want"] = setup_states("n64") + "/Mupen64Plus-Next"
    S["c_h7_n64_mem"] = mem()
    S["c_h7_n64_scratch"] = scratch_anywhere()
    call("POST", "/plugins/games/h7-stop")
    call("POST", "/plugins/games/stop")
    # 3. refusals: nothing launched, the board still the session, no new setup folder
    board_up("c_ref")
    side_ps1 = {"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}, "cheat": setups["ps1"]}
    side_n64 = {"players": 4, "cheat": setups["n64"]}
    def refused(tag, side):
        (rules_ / f"{title}.party.json").write_text(json.dumps(side))
        lst = call("GET", "/plugins/games/party-minigames")["body"]["minigames"]
        tk = next((e["id"] for e in lst if e["players"] == 2), None)
        p0, r0 = len(POPENS), len(rows())
        res = call("POST", f"/plugins/games/party-minigame-start?id={tk}&seats=1,2") if tk else {"code": None}
        S[tag] = {"listed": tk is not None, "code": res["code"], "error": (res.get("body") or {}).get("error"),
                  "popens": len(POPENS) - p0, "rows": [{k: v for k, v in r.items() if k in ("step", "why", "check")}
                                                       for r in rows()[r0:]],
                  "board_session": call("GET", "/plugins/games/status")["body"].get("launch_kind"),
                  "mg": call("GET", "/plugins/games/party-minigame-result")["body"].get("state")}
    gone_id = "0" * 64
    (rules_ / h7m.setup_begin_name(title, gone_id)).write_text(json.dumps({"P1": 1, "P2": 1}))
    refused("c_ref_no_profile", dict(side_ps1, cheat=dict(setups["ps1"], profile_id=gone_id)))
    sdir = root / PROF / title / setups["ps1"]["profile_id"]
    shutil.move(str(sdir), str(root / "moved_setup"))
    refused("c_ref_folder_gone", side_ps1)
    shutil.move(str(root / "moved_setup"), str(sdir))
    refused("c_ref_indexes_changed", dict(side_ps1, cheat=dict(setups["ps1"], enabled_cheat_indexes=[1])))
    (rules_ / f"{title}.party.json").write_text(json.dumps(dict(side_ps1, cheat=dict(setups["ps1"], profile_id="xyz"))))
    S["c_malformed_listed"] = [e["players"] for e in call("GET", "/plugins/games/party-minigames")["body"]["minigames"]]
    S["c_dirs_after_refusals"] = sorted(str(p.relative_to(root)) for p in (root / PROF).glob("*/*")) == dirs_before
    # 4. two back to back with the onn's calls throughout: two-player under the PS1 setup, four-player under N64's
    (rules_ / f"{title}.party.json").write_text(json.dumps(side_ps1))
    (rules_ / f"{n64}.party.json").write_text(json.dumps(side_n64))
    listed = call("GET", "/plugins/games/party-minigames")["body"]["minigames"]
    S["c_list"] = sorted(e["players"] for e in listed)
    tok2 = next(e["id"] for e in listed if e["players"] == 2)
    tok4 = next(e["id"] for e in listed if e["players"] == 4)
    pr = call("POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1")["body"]
    call("POST", "/plugins/games/native-stream-ready")
    def under_setup(key, home_resume):
        def during(tag):
            S[tag + "_route_during"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
            S[tag + "_session_profile"] = (m._active_cheat_session or {}).get("profile_id") == setups[key]["profile_id"]
            st = call("GET", "/plugins/games/status")["body"]
            S[tag + "_status_profile"] = (st.get("cheat_session") or {}).get("profile_id") == setups[key]["profile_id"]
            S[tag + "_mem"] = mem()
            if args.get("saveload"):                  # B131: the onn's SAVE / LOAD during the mini game
                l0, q0 = len(fake["ra"].log), len(rows())
                S[tag + "_saveload"] = {k: call("POST", "/plugins/games/" + q) for k, q in
                                        (("save", "save-state?slot=1"), ("save_replace", "save-state?slot=1&replace=true"),
                                         ("load", "load-state?slot=1"))}
                S[tag + "_saveload_sent"] = [c for c in fake["ra"].log[l0:] if c in ("SAVE_STATE_SLOT", "LOAD_STATE_SLOT",
                                                                                    "SAVE_STATE", "LOAD_STATE")]
                S[tag + "_saveload_rows"] = [{k: v for k, v in r_.items() if k in ("step", "what", "state")}
                                             for r_ in rows()[q0:] if r_["step"] == "minigame_state_refused"]
                S[tag + "_state_after_saveload"] = call("GET", "/plugins/games/party-minigame-result")["body"].get("state")
            if home_resume:
                time.sleep(0.3)
                timed("home", "POST", "/plugins/games/native-stream-stop")
                client.in_stream = False
                time.sleep(0.2)
                rs = timed("resume_start", "POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1",
                           timeout=30)
                client.in_stream = True
                timed("resume_ready", "POST", "/plugins/games/native-stream-ready", timeout=30)
                S[tag + "_resume_ports"] = {"players": rs["body"].get("players"),
                                            "ports": (rs["body"].get("ports_set") or {}).get("players")}
        return during
    R2143 = ["s4start"] * 4 + ["s4other"] * 8 + ["s4r2143"] * 40
    for tag, seats, script, tk, key, hr in (("ca2", "2,1", END2, tok2, "ps1", False),
                                            ("cb4", "3,1,4,2", R2143, tok4, "n64", True)):
        q0, n0 = len(LQ), len(LOADS)
        one(tag, seats, script, tok=tk, during=under_setup(key, hr))
        S[tag + "_launch_queries"] = [x.replace(gid_of[key], "<id>") for x in LQ[q0:]]
        S[tag + "_want_query"] = (q_ps1 if key == "ps1" else q_n64).replace(gid_of[key], "<id>")
        S[tag + "_loaded_from"] = LOADS[n0:]
        S[tag + "_want_folder"] = setup_states(key) + ("/Mupen64Plus-Next" if key == "n64" else "/Beetle PSX HW")
        S[tag + "_launch_row"] = [{k: v for k, v in r.items() if k in ("cheat", "profile_matches", "pid_owned")}
                                  for r in rows() if r["step"] == "minigame_launch"][-1]
    S["c_applied"] = [a == setups["ps1"]["profile_id"] or a == setups["n64"]["profile_id"] for a in APPLIED]
    if args.get("saveload"):                          # B131: after the mini games, on the board's session: today's path
        S["c_board_saveload"] = {k: call("POST", "/plugins/games/" + q) for k, q in
                                 (("save", "save-state?slot=1"), ("load", "load-state?slot=1"))}
    S["abr_all"] = [[r.get("event"), r.get("source")] for r in abr_rows()
                    if r.get("event") in ("ssrc_change", "escalation_armed", "transition", "transition_done")]
    timed("end_onn", "POST", "/plugins/games/stop")
    wait_until(lambda: board_pid_now() is None, 10)
    # 5. the users' files byte-equal; no scratch; nothing running
    after = tree_hashes(PROF, "data/games/retroarch/states")
    S["c_files_same"] = after == before
    S["c_files_diff"] = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    S["c_scratch_end"] = scratch_anywhere()
    S["c_running_after"] = [m.process is not None and m.process.poll() is None, board_pid_now()]
    S["c_b139_cfg"] = [{"party": c["party"], "keys": c["keys"]} for c in B139_CFG]
    finish()
if args["mode"] in ("hold", "practice", "nopress", "nopress_head", "b143", "select151"):
    # B133 / B134: the title prepared behind the board, handed over on the board's go; practice from the load screen
    n64 = args["n64_id"]
    v3 = Path(args["v3"]); js4 = json.loads(v3.read_text())
    shutil.copyfile(v3.with_name(js4["arrays"]), rules_ / f"{n64}.endscreen.npz")
    js4["arrays"] = f"{n64}.endscreen.npz"
    (rules_ / f"{n64}.endscreen.json").write_text(json.dumps(js4))
    (rules_ / f"{n64}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
    (rules_ / f"{n64}.party.json").write_text(json.dumps({"players": 4}))
    def folder():
        return m._state_root() / ("Mupen64Plus-Next" if m._n64_core else "Beetle PSX HW")
    listed = call("GET", "/plugins/games/party-minigames")["body"]["minigames"]
    S["h_list"] = [{"players": e["players"], "title": e.get("title")} for e in listed]
    tok2 = next(e["id"] for e in listed if e["players"] == 2)
    tok4 = next(e["id"] for e in listed if e["players"] == 4)
    layer.poll_gone_s = 120.0

    def res():
        return call("GET", "/plugins/games/party-minigame-result")["body"]

    def wait_phase(pred, bound=15):
        end = time.monotonic() + bound
        b = {}
        while time.monotonic() < end:
            b = res()
            if pred(b):
                return b
            time.sleep(0.05)
        return dict(b, timeout=True)

    def steps_since(r0):
        return [r["step"] for r in rows()[r0:]]

    def title_alive():
        return fake["ra"].poll() is None if "ra" in fake else None

    def held_start(tag, tok, seats, script):
        """Start held; returns rows index. The board up first if it is not."""
        if call("GET", "/plugins/games/status")["body"].get("launch_kind") != "godot" or board_pid_now() is None:
            board_up(tag)
        pic.set(script)
        r0 = len(rows())
        S[tag + "_start"] = timed("start", "POST", f"/plugins/games/party-minigame-start?id={tok}&seats={seats}&hold=1")
        return r0

    def finish_case(tag, r0, k0=None):
        S[tag + "_end"] = timed("board_end", "POST", "/plugins/games/party-minigame-end")
        S[tag + "_closed"] = wait_for(lambda b: b.get("closed"), 20).get("closed")
        S[tag + "_rows"] = steps_since(r0)
        S[tag + "_title_gone"] = not title_alive()
        S[tag + "_route_after"] = bridge._party_route
        S[tag + "_switches"] = [[r.get("window"), r.get("switched")] for r in rows()[r0:] if r["step"] == "minigame_stream"]
        S[tag + "_board_picture_back"] = wait_until(lambda: stream.flowing() and stream.captured_pid == board_pid_now(), 20)

    def during_ready(tag):
        S[tag + "_route_ready"] = bridge._party_route
        S[tag + "_stream_on_board"] = stream.captured_pid == board_pid_now()
        S[tag + "_title_paused_ready"] = fake["ra"].paused if "ra" in fake else None

    if args["mode"] == "hold":
        # H1: T88-shaped — notices-like pictures, then the start; held, the board asking; the go; the end
        r0 = held_start("h1", tok2, "1,2", ["other"] * 5 + ["start"] * 400)
        S["h1_preparing"] = wait_phase(lambda b: b.get("phase") == "preparing" or b.get("state") != "starting", 5)
        b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        S["h1_ready"] = {k: b.get(k) for k in ("state", "phase", "recognised", "practices")}
        during_ready("h1")
        S["h1_rows_at_ready"] = steps_since(r0)
        time.sleep(3.0)                                         # a hold with the board asking
        S["h1_still"] = {k: res().get(k) for k in ("state", "phase")}
        S["h1_go"] = timed("go", "POST", "/plugins/games/party-minigame-go")["body"]
        pic.set(["other"] * 6 + ["end_P1"] * 60)
        S["h1_go_again"] = call("POST", "/plugins/games/party-minigame-go")
        p_ = wait_phase(lambda b: b.get("state") != "starting", 20)
        S["h1_route_playing"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
        S["h1_stream_on_title"] = stream.captured_pid == getattr(fake.get("ra"), "pid", None)
        e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
        S["h1"] = {k: e.get(k) for k in ("state", "class", "scores", "why")}
        finish_case("h1", r0)
        S["h1_row_fields"] = {r["step"]: {k: v for k, v in r.items() if k in ("prepare_s", "held_s", "handover_s",
                                                                             "remembered", "hold")}
                              for r in rows()[r0:] if r["step"] in ("minigame_start", "minigame_ready", "minigame_go",
                                                                     "minigame_playing")}
        # H2: the go before ready (remembered), a second go; T89-shaped (N64: the loads only while paused)
        r0 = held_start("h2", tok4, "3,1,4,2", ["s4other"] * 6 + ["s4start"] * 400)
        S["h2_go_early"] = call("POST", "/plugins/games/party-minigame-go")["body"]
        S["h2_go_second"] = call("POST", "/plugins/games/party-minigame-go")["body"]
        p_ = wait_phase(lambda b: b.get("state") != "starting", 25)
        S["h2_playing"] = {k: p_.get(k) for k in ("state", "phase")}
        pic.set(["s4other"] * 3 + ["s4r2143"] * 60)
        e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
        S["h2"] = {k: e.get(k) for k in ("state", "places", "scores", "seats", "why")}
        finish_case("h2", r0)
        S["h2_go_row"] = [{k: v for k, v in r.items() if k in ("remembered",)} for r in rows()[r0:]
                          if r["step"] == "minigame_go"]
        # H3: never the start → given up, no route, no switch, the title gone, the board's session back
        r0 = held_start("h3", tok2, "1,2", ["other"] * 400)
        e = wait_for(lambda b: b.get("state") in ("given_up", "ended") or b.get("phase") == "ready", 20)
        S["h3"] = {k: e.get(k) for k in ("state", "why", "phase")}
        finish_case("h3", r0)
        S["h3_status_kind"] = call("GET", "/plugins/games/status")["body"].get("launch_kind")
        # H4: the board stops asking during the hold → given up, the title stopped
        r0 = held_start("h4", tok2, "1,2", ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        layer.poll_gone_s = 1.5
        QUIET.add("result")
        wait_until(lambda: layer.mg.get("closed"), 15)
        S["h4"] = {k: layer.mg.get(k) for k in ("state", "why", "closed")}
        S["h4_title_gone"] = not title_alive()
        S["h4_rows"] = steps_since(r0)
        QUIET.discard("result")
        layer.poll_gone_s = 120.0
        # H5: the board's end during the preparation and during the hold
        for tag, when in (("h5p", "preparing"), ("h5h", "ready")):
            r0 = held_start(tag, tok2, "1,2", ["other"] * 6 + ["start"] * 400)
            wait_phase(lambda b, w=when: b.get("phase") == w or b.get("state") != "starting", 20)
            S[tag + "_second_start"] = call("POST", f"/plugins/games/party-minigame-start?id={tok2}&seats=1,2&hold=1")
            finish_case(tag, r0)
            S[tag + "_state"] = layer.mg.get("state")
        # H6: the onn's Home during the hold → given up, then Home / RESUME act on the board
        r0 = held_start("h6", tok2, "1,2", ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        S["h6_home"] = timed("home", "POST", "/plugins/games/native-stream-stop")["body"]
        client.in_stream = False
        wait_until(lambda: layer.mg.get("closed"), 15)
        S["h6"] = {k: layer.mg.get(k) for k in ("state", "why", "closed")}
        S["h6_title_gone"] = not title_alive()
        rs = timed("resume_start", "POST", "/plugins/games/native-stream-start?port=48100", timeout=30)
        client.in_stream = True
        rr = timed("resume_ready", "POST", "/plugins/games/native-stream-ready", timeout=30)
        S["h6_resume"] = {"start": rs["code"], "ready": rr["code"],
                          "kind": call("GET", "/plugins/games/status")["body"].get("launch_kind")}
        S["h6_rows"] = steps_since(r0)
        S["h6_route_ever"] = [r for r in steps_since(r0) if r == "minigame_route"]
        # H7: the onn's END during the preparation (everything ends, as today)
        r0 = held_start("h7", tok2, "1,2", ["other"] * 8 + ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "preparing", 10)
        S["h7_end"] = timed("end_onn", "POST", "/plugins/games/stop")["body"]
        wait_until(lambda: layer.mg.get("closed"), 15)
        S["h7"] = {k: layer.mg.get(k) for k in ("state", "why", "closed")}
        S["h7_title_gone"] = not title_alive()
        S["h7_board_gone"] = wait_until(lambda: board_pid_now() is None, 15)
        S["h7_rows"] = steps_since(r0)
        # the go with nothing held
        S["h_go_none"] = call("POST", "/plugins/games/party-minigame-go")
        S["h_go_bad"] = call("POST", "/plugins/games/party-minigame-go?practice=2")
        S["h_hold_bad"] = call("POST", f"/plugins/games/party-minigame-start?id={tok2}&seats=1,2&hold=2")
    if args["mode"] == "practice":
        r0 = held_start("p", tok2, "1,2", ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        S["p_rows_before"] = rows()[r0:]
        for n in range(3):
            tag = f"p{n + 1}"
            S[tag + "_go"] = timed("go", "POST", "/plugins/games/party-minigame-go?practice=1")["body"]
            b = wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
            S[tag + "_playing"] = {k: b.get(k) for k in ("state", "practice", "practices")}
            pic.set(["end_P1"] * 400)                      # an end screen shown in the practice changes nothing
            time.sleep(1.2)
            S[tag + "_still"] = {k: res().get(k) for k in ("state", "practice", "scores", "class")}
            S[tag + "_route_in"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
            S[tag + "_stream_on_title"] = stream.captured_pid == getattr(fake.get("ra"), "pid", None)
            pic.set(["start"] * 400)
            bridge._apply_report(1, 0x0010, 0, 0, 0, 0, 0, 0)        # B151: Start reaches the title, the practice goes on
            bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
            time.sleep(0.6)
            S[tag + "_after_start"] = {k: res().get(k) for k in ("state", "practice")}
            if n < 2:
                bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)    # B151: the second pad's Select
                bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
            else:
                layer.practice_s = 2.0                              # the practice's time alone (scaled)
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
            S[tag + "_back"] = {k: b.get(k) for k in ("state", "phase", "practices", "scores")}
            S[tag + "_route_back"] = bridge._party_route
            S[tag + "_stream_on_board"] = wait_until(lambda: stream.captured_pid == board_pid_now(), 10)
            layer.practice_s = 90.0
        S["p_end_rows"] = [{k: v for k, v in r.items() if k in ("step", "by")} for r in rows()[r0:]
                           if r["step"] in ("minigame_practice_end", "minigame_ready")]
        # then a real go: scored as today; Start in it does nothing on the hub
        S["p_real_go"] = timed("go", "POST", "/plugins/games/party-minigame-go")["body"]
        b = wait_phase(lambda b: b.get("state") != "starting", 20)
        bridge._apply_report(0, 0x0010, 0, 0, 0, 0, 0, 0)
        bridge._apply_report(0, 0, 0, 0, 0, 0, 0, 0)
        bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)            # B151: Select in a real one: nothing on the hub
        bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
        time.sleep(1.0)
        S["p_real_after_start"] = {k: res().get(k) for k in ("state", "practice")}
        pic.set(["other"] * 3 + ["end_P2"] * 60)
        e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
        S["p_real"] = {k: e.get(k) for k in ("state", "class", "scores", "practices")}
        finish_case("p", r0)
        S["p_practice_end_rows_total"] = sum(1 for r in rows()[r0:] if r["step"] == "minigame_practice_end")
        all_rows = (root / "logs/games/party.jsonl").read_text() if (root / "logs/games/party.jsonl").is_file() else ""
        S["p_names_in_rows"] = [t for t in (e_.get("title") for e_ in listed) if t and t in all_rows]
        # END from the board, the onn's END / Home during a practice and during its way back
        for tag, how, when in (("q1", "board", "practice"), ("q2", "home", "practice"), ("q3", "board", "way_back"),
                               ("q4", "onn_end", "practice")):
            r0 = held_start(tag, tok2, "1,2", ["start"] * 400)
            wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
            call("POST", "/plugins/games/party-minigame-go?practice=1")
            wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
            if when == "way_back":
                pic.set(["other"] * 400)                    # the way back's preparation runs on
                bridge._apply_report(0, 0x0020, 0, 0, 0, 0, 0, 0)    # B151: Select
                bridge._apply_report(0, 0, 0, 0, 0, 0, 0, 0)
                wait_phase(lambda b: b.get("phase") == "preparing", 10)
            if how == "board":
                S[tag + "_end"] = timed("board_end", "POST", "/plugins/games/party-minigame-end")["body"]
            elif how == "home":
                S[tag + "_end"] = timed("home", "POST", "/plugins/games/native-stream-stop")["body"]
                client.in_stream = False
            else:
                S[tag + "_end"] = timed("end_onn", "POST", "/plugins/games/stop")["body"]
            wait_until(lambda: layer.mg.get("closed"), 15)
            S[tag] = {k: layer.mg.get(k) for k in ("state", "why", "closed", "scores")}
            S[tag + "_title_gone"] = not title_alive()
            S[tag + "_hook_cleared"] = getattr(bridge, "_party_buttons", None) is None
            if how == "home":
                call("POST", "/plugins/games/native-stream-start?port=48100")
                client.in_stream = True
                call("POST", "/plugins/games/native-stream-ready")
    if args["mode"] == "b143":
        # B143 / B144: behind the stub's own start, the real stream start (`_start_linux_locked` on G8-S2's stubbed
        # manager: nothing spawned, the encoder's command recorded) and the real audio streamer (Opus, as the hub runs
        # it; pactl answered by stubs, the capture a made-up process writing silence at the real rate) sending to a
        # socket on loopback — the onn's audio as it arrives: [t, sequence, version, timestamp] per datagram.
        import socket as socket_, struct as struct_, importlib.util as ilu_
        import native_stream as nsm, native_session_io as nsio_, audio_codec as ac_
        spec_ = ilu_.find_spec("subprocess")                # the harness replaced subprocess.Popen (its fake title):
        sp_ = ilu_.module_from_spec(spec_); spec_.loader.exec_module(sp_)   # a fresh copy for the made-up capture

        class _Alive:
            def is_dir(self):
                return True

        def _alias_path(*a_):                               # the fake title's pid has no /proc entry: alive for the
            if len(a_) == 1 and str(a_[0]) == "/proc/999999999":   # stream's and the audio's own checks
                return _Alive()
            return Path(*a_)
        nsm.Path = _alias_path
        nsio_.Path = _alias_path
        sys.path.insert(0, args["start_rung"])
        import stub_manager as stubm
        rx = socket_.socket(socket_.AF_INET, socket_.SOCK_DGRAM)
        rx.bind(("127.0.0.1", 0)); rx.settimeout(0.2)
        AP = rx.getsockname()[1]
        DG = []

        def rx_loop():
            while watching["on"]:
                try:
                    d_ = rx.recv(2048)
                except OSError:
                    continue
                if len(d_) >= 16 and d_[:4] == b"PHA1":
                    _m, v_, _c, sq_, ts_, _f = struct_.unpack_from("<4sBBHII", d_)
                    DG.append([round(time.monotonic() - T0, 4), sq_, v_, ts_])
        threading.Thread(target=rx_loop, daemon=True).start()
        PCM = ("import sys,time\nb=bytes(1920)\nt=time.monotonic()\nwhile True:\n t+=0.01\n"
               " time.sleep(max(0,t-time.monotonic()))\n sys.stdout.buffer.write(b); sys.stdout.buffer.flush()\n")

        class _SP:
            PIPE, DEVNULL, STDOUT = sp_.PIPE, sp_.DEVNULL, sp_.STDOUT

            def __getattr__(self, n):
                return getattr(sp_, n)

            @staticmethod
            def Popen(cmd, **kw):
                return sp_.Popen([sys.executable, "-c", PCM], stdout=sp_.PIPE, stdin=sp_.DEVNULL, stderr=sp_.DEVNULL,
                                 bufsize=0)
        nsio_.subprocess = _SP()
        nsio_.AUDIO_CODEC = ac_.from_environ_fresh({"PRIVYHUB_AUDIO_CODEC": "opus"}, log=lambda *a_: None)
        _fake_popen, subprocess.Popen = subprocess.Popen, sp_.Popen     # libopus found (ctypes asks ldconfig) with
        try:                                                          # the real Popen, once
            ac_.libopus()
        finally:
            subprocess.Popen = _fake_popen
        audio = nsio_.NativeAudioStreamer(root / "b143_audio")
        audio._linux_run_pactl = lambda *a_, **k_: types.SimpleNamespace(returncode=0, stdout="7\n", stderr="")
        audio._linux_pactl_json = lambda *a_: ([{"name": audio._linux_sink_name, "index": 3,
                                                 "monitor_source_name": "fixture.monitor"}] if a_[-1] == "sinks"
                                               else [{"index": 5, "sink": 3}])
        audio._linux_find_owned_sink_inputs = lambda pid_: [{"index": 5, "sink": 0}]
        threading.excepthook = lambda a_: S.setdefault("b143_thread_exc", []).append(   # a worker's death, kept
            f"{a_.exc_type.__name__}: {a_.exc_value}"[:300])
        real = stubm.stub_manager(nsm, [])
        shutil.rmtree(real.project_root, ignore_errors=True)
        real.project_root = root / "b143_stream"; real.data_dir = real.project_root / "data"
        real.log_dir = real.project_root / "logs"; real.log_path = real.log_dir / "native_video_alpha.log"

        def sio_start(ffmpeg, client_ip, audio_port, input_port, process_id):
            audio._audio_codec_opus = ac_.OpusSession(128, 10)        # as the codec's prepare (the onn declared opus)
            return audio.start(ffmpeg=Path(sys.executable), client_ip="127.0.0.1", client_port=AP,
                               process_id=process_id)
        real._session_io = types.SimpleNamespace(stop_stream=audio.stop, start=sio_start, audio=audio)
        nsm.subprocess = types.SimpleNamespace(Popen=lambda argv, **k_: stubm.FakeProc(argv), DEVNULL=-3, STDOUT=-2)
        stream._session_io.audio = audio
        if hasattr(nsm.NativeStreamManager, "party_banner_next"):
            type(stream).party_banner_next = lambda self_, pid_: real.party_banner_next(pid_)
        STARTS = []
        stub_start = stream.start

        def start_real(client_ip=None, port=None, managed_process_id=None):
            r_ = stub_start(client_ip, port, managed_process_id)
            with stream._lock:
                t_stop = round(time.monotonic() - T0, 4)
                try:
                    real._start_linux_locked(client_ip="127.0.0.1", port=48100,
                                             managed_process_id=int(managed_process_id))
                except Exception as exc_:
                    c_ = exc_.__cause__ or exc_.__context__
                    S.setdefault("b143_errors", []).append(f"{type(exc_).__name__}: {exc_}"[:300]
                                                           + (f" ({type(c_).__name__}: {c_})"[:300] if c_ else ""))
                    raise
                STARTS.append({"pid": int(managed_process_id), "board": int(managed_process_id) == board_pid_now(),
                               "t_stop": t_stop, "t_up": round(time.monotonic() - T0, 4),
                               "argv": list(real._encoder_command or []),
                               "audio_start": list(getattr(audio, "_audio_start", (0, 0)))})
            return r_
        stream.start = start_real

        def switches_since(r0):
            return [{k: v for k, v in r.items() if k in ("window", "switched", "planned", "why")} for r in rows()[r0:]
                    if r["step"] == "minigame_stream"]
        n_ = len(STARTS)
        board_up("b143")                                    # a fresh board: its stream a users' start (the onn's)
        S["b143_board_up"] = [n_, len(STARTS), S.get("b143_board_launch")]
        S["b143_users_start"] = list(STARTS[-1]["audio_start"]) if STARTS else None
        time.sleep(1.0)
        # two planned switches: a real go and its end
        s0 = len(STARTS)
        r0 = held_start("a2", tok2, "1,2", ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        time.sleep(0.8)
        S["a2_go"] = call("POST", "/plugins/games/party-minigame-go")["body"].get("go")
        wait_phase(lambda b: b.get("state") != "starting", 20)
        time.sleep(1.4)
        pic.set(["end_P1"] * 400)
        e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
        S["a2"] = {k: e.get(k) for k in ("state", "class", "scores")}
        finish_case("a2", r0)
        time.sleep(1.2)
        S["a2_switch_rows"] = switches_since(r0)
        S["a2_starts"] = [s0, len(STARTS)]
        # five planned switches (and the end's way back): practice by Select (B151), practice by time, a real go
        s0 = len(STARTS)
        r0 = held_start("a5", tok2, "1,2", ["start"] * 400)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
        time.sleep(0.6)
        call("POST", "/plugins/games/party-minigame-go?practice=1")
        wait_phase(lambda b: b.get("state") == "playing", 20)
        time.sleep(1.0)
        bridge._apply_report(1, 0x0020 | 0x0010, 0, 0, 0, 0, 0, 0)   # B151: Select leaves it (Start passes); the
                                                                       # HEAD runs of this mode: Start, as before
        bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
        time.sleep(0.7)
        call("POST", "/plugins/games/party-minigame-go?practice=1")
        wait_phase(lambda b: b.get("state") == "playing", 20)
        layer.practice_s = 1.6                                         # the practice's time alone (scaled)
        wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
        layer.practice_s = 90.0
        time.sleep(0.9)
        S["a5_go"] = call("POST", "/plugins/games/party-minigame-go")["body"].get("go")
        wait_phase(lambda b: b.get("state") != "starting", 20)
        time.sleep(1.2)
        pic.set(["end_P1"] * 400)
        e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
        S["a5"] = {k: e.get(k) for k in ("state", "class", "scores", "practices")}
        finish_case("a5", r0)
        time.sleep(1.2)
        S["a5_switch_rows"] = switches_since(r0)
        S["a5_starts"] = [s0, len(STARTS)]
        S["b143_starts"] = STARTS
        S["b143_dg"] = DG
        S["b143_redundancy"] = [audio._redundancy_copies, audio._redundancy_offset_packets]
        S["b143_ffmpeg_fixture"] = "/fixture/ffmpeg"
        audio.stop()
    if args["mode"] in ("nopress", "nopress_head", "select151"):
        # B137: nothing a player presses reaches the title before the go. B101's fake RetroArch taught FRAMEADVANCE and
        # a title: running, it reads the virtual pads every 1/60 s and leaves its start screen when any button but
        # neutral reaches it (a pick on the select screen -> a fight); a frame advance runs one frame; its load puts the
        # begin back (PS1-shaped: shown at the next frame; N64-shaped: the load runs a frame, reading the pads); notices
        # cover its picture for NOTICE_S after a load; its own log. The watcher's picture follows the fake (RetroArch's
        # "Paused." drawn in its corner while paused). A confirm press from each player through the bridge every 0.2 s.
        import h7_minigame as h7m
        NOTICE_S, CONFIRM = 0.6, 0x1000                     # XUSB_A: the board's confirm
        if hasattr(h7m, "LABEL_BOX"):
            h7m.LABEL_BOX = (24, 10)                        # the label's box at the fixtures' scale (320 x 260)
        LBL = (20, 8)
        VP = {"cur": [0, 0, 0, 0], "log": []}

        def _rec(index, report, *a_, forced_buttons=0, **k_):
            b_ = (int(report["buttons"]) | int(forced_buttons)) & 0xFFFF
            VP["cur"][index] = b_
            VP["log"].append([time.monotonic(), index, b_])
        bridge._write_linux_report_locked = _rec
        EV = []                                             # the fake title's own log: [t, what, detail]
        TITLE = {"begin": "start", "show_after": None}     # B140: frames after a load before the begin shows (None:
                                                            # the core's own — PS1-shaped 1, N64-shaped 0); "never"

        class TitleRA(FakeRetroArch):
            def __init__(self, cmd, **kw):
                self.screen, self.shown, self.notice_until = "boot", "boot", 0.0
                self.loads = self.advances = self.frames = 0
                self.since_load, self.show_after = None, None       # B140
                c_ = b139_config(cmd)                       # B139: RetroArch reads its session config
                self.notices_on = c_["keys"].get("video_font_enable", ["true"])[-1] != "false"
                _lay = getattr(g, "_party_minigame_obj", None); _mg = getattr(_lay, "mg", None)
                LAUNCH_CFG.append({"party": bool(_mg is not None and not _mg.get("launched") and not _mg.get("closed")),
                                   "keys": c_["keys"], "text": c_["text"]})
                super().__init__(cmd, **kw)
                EV.append([time.monotonic(), "launch", None])
                threading.Thread(target=self.run_frames, daemon=True).start()

            def frame(self, why):
                pads = list(VP["cur"])
                if self.screen == "start" and any(b_ != 0 for b_ in pads):
                    self.screen = "fight"
                    EV.append([time.monotonic(), "left_start", why])
                if self.since_load is not None:                     # B140: the begin shows after show_after frames
                    self.since_load += 1
                    if self.show_after == "never" or self.since_load < self.show_after:
                        self.frames += 1
                        EV.append([time.monotonic(), "frame", [why, pads]])
                        return
                    self.since_load = None
                self.shown = self.screen
                self.frames += 1
                EV.append([time.monotonic(), "frame", [why, pads]])

            def run_frames(self):
                while not self.stop:
                    if not self.paused:
                        self.frame("run")
                    for i_, b_ in enumerate(VP["cur"]):     # B141: RetroArch's hotkeys, polled paused or running
                        if b_ & 0x0020 and b_ & (0x0100 | 0x0200 | 0x0010 | 0x0080):
                            HOTKEYS.append([time.monotonic(), i_, b_])
                    time.sleep(1 / 60)

            def serve(self):
                while not self.stop:
                    try:
                        data, addr = self.sock.recvfrom(4096)
                    except OSError:
                        continue
                    c = data.decode().strip(); w = c.split()
                    self.log.append(w[0] if w else "")
                    if c == "GET_STATUS":
                        self.sock.sendto(f"GET_STATUS {'PAUSED' if self.paused else 'PLAYING'} psx,fixture,crc32=0".encode(), addr)
                    elif c == "PAUSE_TOGGLE":
                        self.paused = not self.paused
                        EV.append([time.monotonic(), "pause" if self.paused else "resume", None])
                    elif c == "FRAMEADVANCE":
                        if self.paused:
                            self.advances += 1
                            self.frame("advance")
                            EV.append([time.monotonic(), "advance", self.advances])
                    elif c == "SAVE_FILES":
                        self.sock.sendto(b"SAVE_FILES OK", addr)
                    elif w and w[0] == "LOAD_STATE_SLOT" and len(w) == 2:
                        p_ = folder() / (m._active_state_stem() + f".state{w[1]}")
                        if not p_.is_file():
                            self.logline(f'[ERROR] [State] Failed to load state from "{p_}".')
                        else:
                            self.screen = TITLE["begin"]
                            self.loads += 1
                            sa = TITLE["show_after"]
                            self.show_after = sa if sa is not None else (0 if m._n64_core else 1)
                            self.since_load = 0
                            if self.show_after == 0:                # shown with the load itself
                                self.since_load = None
                                self.shown = self.screen
                            self.notice_until = time.monotonic() + (NOTICE_S if self.notices_on else 0.0)
                            EV.append([time.monotonic(), "load", self.loads])
                            if m._n64_core:                 # the N64 core's load runs a frame (B137's settle)
                                self.frame("load")
                            self.logline(f'[INFO] [State] Loading state "{p_}", {p_.stat().st_size} bytes.')
                        self.sock.sendto(c.encode(), addr)
                    elif w and w[0] in ("READ_CORE_RAM", "READ_CORE_MEMORY") and len(w) == 3:
                        self.sock.sendto(f"{w[0]} {w[1]} -1".encode(), addr)
        em.subprocess.Popen = TitleRA
        LAUNCH_CFG = []                                     # B139: every launch's session config keys (party or not)
        HOTKEYS = []                                        # B141: every poll that saw Select with a paired button
        P_UNROUTE = []                                      # each route cleared while a title runs: was it paused
        _set_route = bridge.set_party_route

        def _route_spy(route):
            ra_ = fake.get("ra")
            if route is None and ra_ is not None and ra_.poll() is None and layer.mg is not None \
                    and layer.mg.get("practice_end_by") is not None:                   # a practice's way back
                P_UNROUTE.append(bool(ra_.paused))
            return _set_route(route)
        bridge.set_party_route = _route_spy
        READS = []                                          # every read: [t, paused, the label's corner max]

        class FollowPicture:
            def __init__(self):
                self.n = {}

            def grab(self):
                ra_ = fake.get("ra")
                if ra_ is None or ra_.poll() is not None:
                    raise RuntimeError("the picture was not read: no game window")
                n64_ = bool(m._n64_core)
                shown = ra_.shown
                if time.monotonic() < ra_.notice_until or shown in ("boot", "fight"):
                    tok = "s4other" if n64_ else "other"
                elif shown == "start":
                    tok = "s4start" if n64_ else "start"
                else:
                    tok = shown
                i = self.n[tok] = (self.n.get(tok, -1) + 1) % 6
                if tok in ("other", "s4other"):             # B140: the same picture while nothing changes; a fight
                    i = 3 if (shown == "fight" and time.monotonic() >= ra_.notice_until) else 0   # is not the boot frame
                with Image.open(frames / f"{tok}_{i}.png") as im:
                    img = im.convert("L")
                if ra_.paused and ra_.notices_on:          # RetroArch's "Paused." in the corner (B139: only with text on)
                    img.paste(255, (img.size[0] - LBL[0], 0, img.size[0], LBL[1]))
                return img
        follow = FollowPicture()
        mini.picture = follow
        es_ = h7m.endscreen()
        _read = es_.Reader.read

        def _spy(self_, img):
            ra_ = fake.get("ra")
            W_ = img.size[0]
            corner = max(img.crop((W_ - LBL[0], 0, W_, LBL[1])).getdata())
            READS.append([time.monotonic(), bool(ra_ is not None and ra_.paused), corner,
                          bool(ra_ is not None and ra_.paused and ra_.notices_on)])
            return _read(self_, img)
        es_.Reader.read = _spy
        PRESS = {"on": False, "players": [0, 1], "sent": []}

        def presser():
            while watching["on"]:
                if not PRESS["on"]:
                    time.sleep(0.02); continue
                for pl in list(PRESS["players"]):
                    bridge._apply_report(pl, CONFIRM, 0, 0, 0, 0, 0, 0)
                PRESS["sent"].append([time.monotonic(), "down"])
                time.sleep(0.1)
                for pl in list(PRESS["players"]):
                    bridge._apply_report(pl, 0, 0, 0, 0, 0, 0, 0)
                PRESS["sent"].append([time.monotonic(), "up"])
                time.sleep(0.1)
        threading.Thread(target=presser, daemon=True, name="b137-presses").start()

        W0 = [time.time()]

        def h7_rows():
            p_ = root / "logs/games/h7_results.jsonl"
            return [json.loads(l) for l in p_.read_text().splitlines()] if p_.is_file() else []

        def ev_since(t0_):
            return [e for e in EV if e[0] >= t0_]

        def segment(t_from, t_go):
            """From the first pause at or after t_from to the go: the resumes, the frames that saw a button, the loads."""
            p0 = next((e[0] for e in EV if e[0] >= t_from and e[1] == "pause"), None)
            if p0 is None:
                return {"paused_from": None}
            seg = [e for e in EV if p0 <= e[0] <= t_go]
            return {"paused_from": True, "resumes": sum(1 for e in seg if e[1] == "resume"),
                    "frames": sum(1 for e in seg if e[1] == "frame"),
                    "frames_with_a_button": sum(1 for e in seg if e[1] == "frame" and any(e[2][1])),
                    "left_start": sum(1 for e in seg if e[1] == "left_start"),
                    "loads": sum(1 for e in seg if e[1] == "load"),
                    "advances": sum(1 for e in seg if e[1] == "advance")}

        def mute_windows(t_from, t_to):
            """Each load .. the last advance after it (inside the mute): presses sent in it, buttons written in it."""
            outw = []
            loads = [e[0] for e in EV if t_from <= e[0] <= t_to and e[1] == "load"]
            for tl in loads:
                adv = [e[0] for e in EV if e[0] >= tl and e[1] == "advance"][:2]
                if not adv:
                    continue
                te = adv[-1]
                outw.append({"s": round(te - tl, 3),
                             "presses_sent": sum(1 for x in PRESS["sent"] if tl <= x[0] <= te and x[1] == "down"),
                             "buttons_written": sum(1 for x in VP["log"] if tl <= x[0] <= te and x[2] != 0)})
            return outw

        def screen_at_resume_after(t_):
            """The fake's screen the moment it was first resumed after t_ (the go): the frame right after it."""
            r_ = next((e[0] for e in EV if e[0] >= t_ and e[1] == "resume"), None)
            if r_ is None:
                return None
            f_ = next((e for e in EV if e[0] >= r_ and e[1] == "frame"), None)
            lf = [e for e in EV if r_ <= e[0] and e[1] == "left_start"]
            return {"left_start_at_first_frame": bool(lf and f_ is not None and lf[0][0] <= f_[0]),
                    "loads_after_go": sum(1 for e in EV if e[0] >= t_ and e[1] == "load")}

        def reads_paused_unmasked(t_from, t_to):
            return [r_ for r_ in READS if t_from <= r_[0] <= t_to and r_[1] and r_[2] != 0]

        def press_case(tag, tok, seats, players, remembered=False, t_end_tok="end_P1"):
            PRESS["players"] = players
            PRESS["on"] = True
            t0_ = time.monotonic()
            r0 = held_start(tag, tok, seats, ["other"])
            if remembered:
                S[tag + "_go_early"] = call("POST", "/plugins/games/party-minigame-go")["body"]
                wait_until(lambda: layer.mg.get("phase") == "handing_over" or layer.mg.get("state") != "starting", 25)
                PRESS["on"] = False                          # the go acted on: the players' presses are theirs again
                b = wait_phase(lambda b: b.get("state") != "starting", 25)
                go_t = [e[0] for e in EV if e[0] >= t0_ and e[1] == "resume"]     # the go acted on at ready
                t_go = go_t[0] - 0.001 if go_t else time.monotonic()
                S[tag + "_ready"] = {"state": b.get("state"), "phase": b.get("phase")}
            else:
                b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
                S[tag + "_ready"] = {k: b.get(k) for k in ("state", "phase", "recognised", "why")}
                if b.get("phase") != "ready":
                    PRESS["on"] = False
                    S[tag + "_rows"] = steps_since(r0)
                    S[tag + "_ev"] = [[round(e[0] - t0_, 3), e[1]] for e in EV if e[0] >= t0_ and e[1] != "frame"][:40]
                    finish_case(tag, r0)
                    return r0, t0_, None
                time.sleep(1.0)                              # held, the presses go on
                t_go = time.monotonic()
                S[tag + "_go"] = timed("go", "POST", "/plugins/games/party-minigame-go")["body"]
            PRESS["on"] = False
            p_ = wait_phase(lambda b: b.get("state") != "starting", 20)
            S[tag + "_playing"] = {k: p_.get(k) for k in ("state", "recognised")}
            time.sleep(0.4)
            S[tag + "_segment"] = segment(t0_ + 0.05, t_go)
            S[tag + "_mute"] = mute_windows(t0_, t_go)
            S[tag + "_on_the_begin"] = screen_at_resume_after(t_go)
            S[tag + "_reads_paused_unmasked"] = len(reads_paused_unmasked(t0_, t_go))
            S[tag + "_reads_paused_label"] = sum(1 for r_ in READS if t0_ <= r_[0] <= t_go and r_[3])   # B139
            S[tag + "_reads_paused"] = sum(1 for r_ in READS if t0_ <= r_[0] <= t_go and r_[1])
            S[tag + "_reads_running_masked"] = sum(1 for r_ in READS if r_[0] > t_go + 0.5 and not r_[1] and r_[2] == 0)
            S[tag + "_route_playing"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
            fake["ra"].screen = t_end_tok                    # the title's own end screen
            e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
            S[tag] = {k: e.get(k) for k in ("state", "class", "scores", "places", "why")}
            finish_case(tag, r0)
            S[tag + "_row_fields"] = [{k: v for k, v in r.items() if k in ("step", "frames", "mute_ms", "paused",
                                                                         "remembered", "label_mask", "batches",
                                                                         "changed", "moved")}
                                      for r in rows()[r0:] if r["step"] in ("minigame_frame_advance", "minigame_go",
                                                                             "minigame_reloaded")]
            S[tag + "_mute_after"] = bool(getattr(bridge, "_party_mute", False))
            S[tag + "_watching_label_mask"] = [r.get("label_mask") for r in h7_rows() if r.get("step") == "watching"
                                               and r.get("time_unix", 0) >= W0[0]][-1:]
            return r0, t0_, t_go

        if args["mode"] == "nopress_head":
            # HEAD's code (B133's order): the same presses -> the title leaves its start behind the board; and the
            # control, no presses -> ready
            layer.advance_gap_s = 0.06
            press_case("x1", tok2, "1,2", [0, 1])
            PRESS["players"] = []
            press_case("x0", tok2, "1,2", [])
        elif args["mode"] == "select151":
            # B151: T89-shaped (four seats 3,1,4,2; its start screen left only by a press): a practice is left by a
            # Select press on any pad; Start reaches the title; Select never does before a real go
            layer.advance_gap_s = 0.06
            SELB, STARTB = 0x0020, 0x0010

            def tap(pl, bits, down_s=0.08):
                bridge._apply_report(pl, bits, 0, 0, 0, 0, 0, 0)
                time.sleep(down_s)
                bridge._apply_report(pl, 0, 0, 0, 0, 0, 0, 0)

            def practice_go():
                g_ = call("POST", "/plugins/games/party-minigame-go?practice=1")["body"].get("go")
                b_ = wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
                return g_, {k: b_.get(k) for k in ("state", "practice")}

            def back_ready():
                b_ = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
                return {k: b_.get(k) for k in ("state", "phase", "practices")}

            def now_playing():
                return {k: res().get(k) for k in ("state", "practice")}
            st_dir = folder()
            st_before = {p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}
            r0 = held_start("s1", tok4, "3,1,4,2", ["s4other"])
            S["s1_hold_seen"] = wait_until(lambda: bool(getattr(bridge, "_party_hold_select", False)), 10)
            h0, v0_ = len(HOTKEYS), len(VP["log"])           # from the hold on: before the title's launch
            S["s1_ready"] = back_ready()
            # practice 1: Start from each pad -> the title's pads get it, the practice goes on; then pad 1's Select
            t_go = time.monotonic()
            S["s1_p1_go"] = practice_go()
            vs_ = len(VP["log"])
            for pl in range(4):
                tap(pl, STARTB)
                time.sleep(0.15)
            time.sleep(0.6)
            S["s1_after_starts"] = now_playing()
            S["s1_start_written_to"] = sorted({x[1] for x in VP["log"][vs_:] if x[2] & STARTB})
            S["s1_title_left_start_in_practice"] = any(e_[1] == "left_start" for e_ in EV if e_[0] >= t_go)
            S["s1_route_in"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
            tap(0, SELB)
            S["s1_p1_back"] = back_ready()
            # practices 2-4: left by the Select of pads 2, 3, 4
            for n, pl in ((2, 1), (3, 2), (4, 3)):
                S[f"s1_p{n}_go"] = practice_go()
                time.sleep(0.4)
                S[f"s1_p{n}_before"] = now_playing()
                tap(pl, SELB)
                S[f"s1_p{n}_back"] = back_ready()
            # practice 5: pad 3's Select already down at the hand-over (repeated reports) -> the practice goes on;
            # let go -> still on; pressed again -> it ends
            bridge._apply_report(2, SELB, 0, 0, 0, 0, 0, 0)
            time.sleep(0.2)
            S["s1_p5_go"] = practice_go()
            for _ in range(4):
                bridge._apply_report(2, SELB, 0, 0, 0, 0, 0, 0)
                time.sleep(0.2)
            S["s1_p5_held"] = now_playing()
            bridge._apply_report(2, 0, 0, 0, 0, 0, 0, 0)
            time.sleep(0.4)
            S["s1_p5_let_go"] = now_playing()
            tap(2, SELB)
            S["s1_p5_back"] = back_ready()
            # practice 6: Select + Start together on pad 4 -> left by Select; Start written alone; no hotkey
            S["s1_p6_go"] = practice_go()
            time.sleep(0.3)
            v6_ = len(VP["log"])
            tap(3, SELB | STARTB)
            S["s1_p6_back"] = back_ready()
            S["s1_p6_start_written"] = any(x[2] & STARTB for x in VP["log"][v6_:])
            S["s1_title_alive"] = title_alive()
            # practice 7: the time bound (scaled)
            S["s1_p7_go"] = practice_go()
            layer.practice_s = 1.0
            S["s1_p7_back"] = back_ready()
            layer.practice_s = 90.0
            S["s1_end_by"] = [r.get("by") for r in rows()[r0:] if r["step"] == "minigame_practice_end"]
            S["s1_select_written_before_real_go"] = sum(1 for x in VP["log"][v0_:] if x[2] & SELB)
            S["s1_writes_before_real_go"] = len(VP["log"]) - v0_
            S["s1_hotkeys_before_real_go"] = len(HOTKEYS) - h0
            S["s1_states_same"] = ({p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}) == st_before
            # a real go: Select and Start pass; nothing on the hub
            S["s1_real_go"] = call("POST", "/plugins/games/party-minigame-go")["body"].get("go")
            wait_phase(lambda b: b.get("state") != "starting", 20)
            v2_ = len(VP["log"])
            tap(0, SELB)
            tap(1, STARTB)
            time.sleep(0.6)
            S["s1_real_after"] = now_playing()
            S["s1_real_select_written"] = sum(1 for x in VP["log"][v2_:] if x[2] & SELB)
            S["s1_real_start_written"] = sum(1 for x in VP["log"][v2_:] if x[2] & STARTB)
            S["s1_hook_in_real"] = getattr(bridge, "_party_buttons", None) is not None
            fake["ra"].screen = "s4r2143"
            e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
            S["s1_real"] = {k: e.get(k) for k in ("state", "class", "places", "scores", "seats", "practices")}
            finish_case("s1", r0)
            S["s1_hook_after_end"] = getattr(bridge, "_party_buttons", None) is None
            S["s1_held_after_end"] = bool(getattr(bridge, "_party_hold_select", False))
            S["s1_seen_after_end"] = getattr(bridge, "_party_select_down", None)
        else:
            layer.advance_gap_s = 0.15                       # the mute long enough to see presses dropped in it
            # N1: T88-shaped, a confirm press from both players every 0.2 s from the start call to the go
            press_case("n1", tok2, "1,2", [0, 1])
            # N2: three practices, the presses throughout (the ways back too); Start twice, time once; a real go
            PRESS["players"] = [0, 1]; PRESS["on"] = True
            t0_ = time.monotonic()
            r0 = held_start("n2", tok2, "1,2", ["other"])
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
            S["n2_ready0"] = {k: b.get(k) for k in ("state", "phase")}
            gos, ends = [], []
            for n in range(3):
                gos.append(time.monotonic())
                call("POST", "/plugins/games/party-minigame-go?practice=1")
                wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
                time.sleep(0.8)                              # practising: routed presses reach the title
                ends.append(time.monotonic())
                if n < 2:
                    bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)    # B151: Select on the second pad
                    bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
                else:
                    layer.practice_s = 0.5
                b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
                layer.practice_s = 90.0
                S[f"n2_back{n + 1}"] = {k: b.get(k) for k in ("state", "phase", "practices")}
            time.sleep(0.6)
            t_go = time.monotonic()
            S["n2_go"] = timed("go", "POST", "/plugins/games/party-minigame-go")["body"]
            PRESS["on"] = False
            p_ = wait_phase(lambda b: b.get("state") != "starting", 20)
            S["n2_playing"] = {k: p_.get(k) for k in ("state", "practice")}
            time.sleep(0.4)
            segs = [segment(ends[k], (gos + [t_go])[k + 1]) for k in range(3)]
            S["n2_way_back_segments"] = segs
            S["n2_way_back_mute"] = [mute_windows(ends[k], (gos + [t_go])[k + 1]) for k in range(3)]
            S["n2_first_segment"] = segment(t0_ + 0.05, gos[0])
            # each way back: the pause before the route was cleared (the fake paused while still routed)
            S["n2_pause_before_unroute"] = [P_UNROUTE[k] for k in range(len(P_UNROUTE))]
            S["n2_on_the_begin"] = screen_at_resume_after(t_go)
            S["n2_reads_paused_unmasked"] = len(reads_paused_unmasked(t0_, t_go))
            fake["ra"].screen = "end_P2"
            e = wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
            S["n2"] = {k: e.get(k) for k in ("state", "class", "scores", "practices")}
            finish_case("n2", r0)
            S["n2_steps"] = [r["step"] for r in rows()[r0:] if r["step"] in (
                "minigame_practice_end", "minigame_frame_advance", "minigame_ready", "minigame_go",
                "minigame_reloaded", "minigame_route", "minigame_playing")]
            # N3: T89-shaped (N64, its load runs a frame), four players pressing, a remembered go
            press_case("n3", tok4, "3,1,4,2", [0, 1, 2, 3], remembered=True, t_end_tok="s4r2143")
            # N4: never the start (the begin shows a fight) -> given up, no route, no switch, never resumed
            TITLE["begin"] = "fight"
            PRESS["players"] = [0, 1]; PRESS["on"] = True
            t0_ = time.monotonic()
            r0 = held_start("n4", tok2, "1,2", ["other"])
            e = wait_for(lambda b: b.get("state") in ("given_up", "ended") or b.get("phase") == "ready", 20)
            PRESS["on"] = False
            S["n4"] = {k: e.get(k) for k in ("state", "why", "phase")}
            S["n4_resumes"] = sum(1 for e_ in ev_since(t0_) if e_[1] == "resume")
            finish_case("n4", r0)
            TITLE["begin"] = "start"
            # B140: the begin shown after 0, 2, 12 and never frames following the load; presses from every pad
            layer.advance_gap_s = 0.05
            for tag, sa in (("v0", 0), ("v2", 2), ("v12", 12)):
                TITLE["show_after"] = sa
                press_case(tag, tok2, "1,2", [0, 1, 2, 3])
            TITLE["show_after"] = "never"
            PRESS["players"] = [0, 1, 2, 3]; PRESS["on"] = True
            t0_ = time.monotonic()
            r0 = held_start("vn", tok2, "1,2", ["other"])
            e = wait_for(lambda b: b.get("state") in ("given_up", "ended") or b.get("phase") == "ready", 20)
            PRESS["on"] = False
            S["vn"] = {k: e.get(k) for k in ("state", "why", "phase")}
            S["vn_s"] = round(time.monotonic() - t0_, 2)
            S["vn_resumes"] = sum(1 for e_ in ev_since(t0_) if e_[1] == "resume")
            S["vn_frames_with_a_button"] = sum(1 for e_ in ev_since(t0_) if e_[1] == "frame" and e_[2][0] != "run" and any(e_[2][1]))
            finish_case("vn", r0)
            S["vn_row"] = [{k: v for k, v in r.items() if k in ("frames", "batches", "changed", "moved", "mute_ms")}
                           for r in rows()[r0:] if r["step"] == "minigame_frame_advance"]
            # the practices' ways back with a title that needs 12 frames
            TITLE["show_after"] = 12
            PRESS["players"] = [0, 1]; PRESS["on"] = True
            t0_ = time.monotonic()
            r0 = held_start("vp", tok2, "1,2", ["other"])
            wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
            gos_, ends_ = [], []
            for n in range(2):
                gos_.append(time.monotonic())
                call("POST", "/plugins/games/party-minigame-go?practice=1")
                wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
                time.sleep(0.5)
                ends_.append(time.monotonic())
                bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)    # B151: Select
                bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
                b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
                S[f"vp_back{n + 1}"] = {k: b.get(k) for k in ("state", "phase", "practices")}
            t_go = time.monotonic()
            call("POST", "/plugins/games/party-minigame-go")
            PRESS["on"] = False
            wait_phase(lambda b: b.get("state") != "starting", 20)
            time.sleep(0.3)
            S["vp_way_back_segments"] = [segment(ends_[k], (gos_ + [t_go])[k + 1]) for k in range(2)]
            S["vp_on_the_begin"] = screen_at_resume_after(t_go)
            S["vp_fa_rows"] = [{k: v for k, v in r.items() if k in ("frames", "batches", "changed")}
                            for r in rows()[r0:] if r["step"] == "minigame_frame_advance"]
            finish_case("vp", r0)
            TITLE["show_after"] = None
            # B141: Select with each paired button (L1, R1, Start, R3) from every pad during the preparation, the hold
            # and a practice's way back; Select alone after the go
            SEL = {"on": False}
            PAIRS = (0x0100, 0x0200, 0x0010, 0x0080)

            def selector():
                k = 0
                while watching["on"] and SEL["on"]:
                    pair = PAIRS[k % 4]; k += 1
                    for pl in range(4):
                        bridge._apply_report(pl, 0x0020 | pair, 0, 0, 0, 0, 0, 0)
                    time.sleep(0.1)
                    for pl in range(4):
                        bridge._apply_report(pl, 0, 0, 0, 0, 0, 0, 0)
                    time.sleep(0.1)
            st_dir = folder()
            st_before = {p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}
            r0 = held_start("sl", tok2, "1,2", ["other"])
            S["sl_hold_seen"] = wait_until(lambda: bool(getattr(bridge, "_party_hold_select", False)), 10)
            h0, v0_ = len(HOTKEYS), len(VP["log"])           # from the hold on: before the title's launch
            SEL["on"] = True
            threading.Thread(target=selector, daemon=True).start()
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
            S["sl_ready"] = b.get("phase")
            time.sleep(1.0)                                 # held, the pairs go on
            SEL["on"] = False; time.sleep(0.3)
            S["sl_select_written_before_practice"] = sum(1 for x in VP["log"][v0_:] if x[2] & 0x0020)
            S["sl_hotkeys_before_practice"] = len(HOTKEYS) - h0
            call("POST", "/plugins/games/party-minigame-go?practice=1")
            wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
            bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)    # B151: Select leaves the practice
            bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
            wait_until(lambda: bool(getattr(bridge, "_party_hold_select", False)), 10)   # the way back under way
            h1, v1_ = len(HOTKEYS), len(VP["log"])
            SEL["on"] = True
            threading.Thread(target=selector, daemon=True).start()
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
            S["sl_back"] = b.get("phase")
            time.sleep(0.6)
            SEL["on"] = False; time.sleep(0.3)
            S["sl_select_written_way_back"] = sum(1 for x in VP["log"][v1_:] if x[2] & 0x0020)
            S["sl_hotkeys_way_back"] = len(HOTKEYS) - h1
            S["sl_go"] = call("POST", "/plugins/games/party-minigame-go")["body"].get("go")
            wait_phase(lambda b: b.get("state") != "starting", 20)
            v2_ = len(VP["log"])
            bridge._apply_report(0, 0x0020, 0, 0, 0, 0, 0, 0)    # Select alone after the go: passes
            bridge._apply_report(0, 0, 0, 0, 0, 0, 0, 0)
            S["sl_select_written_after_go"] = sum(1 for x in VP["log"][v2_:] if x[2] & 0x0020)
            S["sl_held_flag_after_go"] = bool(getattr(bridge, "_party_hold_select", False))
            S["sl_states_same"] = ({p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}) == st_before
            fake["ra"].screen = "end_P1"
            wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
            finish_case("sl", r0)
            S["sl_held_flag_after_end"] = bool(getattr(bridge, "_party_hold_select", False))
            # B145: Select held through a practice too — Select + L1 / R1 / R3 from every pad while a practice plays;
            # the practice left by Select + Start (Start passes: the way back, the title not quit); Select alone after
            # a real go passes
            st_before = {p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}
            PAIRS_P = (0x0100, 0x0200, 0x0080)

            def selector_p():
                k = 0
                while watching["on"] and SEL["on"]:
                    pair = PAIRS_P[k % 3]; k += 1
                    for pl in range(4):
                        bridge._apply_report(pl, 0x0020 | pair, 0, 0, 0, 0, 0, 0)
                    time.sleep(0.1)
                    for pl in range(4):
                        bridge._apply_report(pl, 0, 0, 0, 0, 0, 0, 0)
                    time.sleep(0.1)
            r0 = held_start("sp", tok2, "1,2", ["other"])
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") != "starting", 20)
            S["sp_ready"] = b.get("phase")
            S["sp_go"] = call("POST", "/plugins/games/party-minigame-go?practice=1")["body"].get("go")
            b = wait_phase(lambda b: b.get("state") == "playing" or b.get("state") in ("ended", "given_up"), 20)
            S["sp_playing"] = {k: b.get(k) for k in ("state", "practice")}
            S["sp_held_in_practice"] = bool(getattr(bridge, "_party_hold_select", False))
            S["sp_title_running"] = not fake["ra"].paused
            h0, v0_ = len(HOTKEYS), len(VP["log"])
            SEL["on"] = True
            threading.Thread(target=selector_p, daemon=True).start()
            time.sleep(1.5)                                 # the pairs while the practice plays
            SEL["on"] = False; time.sleep(0.3)
            S["sp_writes_in_practice"] = len(VP["log"]) - v0_
            S["sp_select_written_in_practice"] = sum(1 for x in VP["log"][v0_:] if x[2] & 0x0020)
            S["sp_hotkeys_in_practice"] = len(HOTKEYS) - h0
            bridge._apply_report(1, 0x0020, 0, 0, 0, 0, 0, 0)     # B151: Select leaves the practice (was Select + Start)
            bridge._apply_report(1, 0, 0, 0, 0, 0, 0, 0)
            b = wait_phase(lambda b: b.get("phase") == "ready" or b.get("state") in ("ended", "given_up"), 30)
            S["sp_back"] = b.get("phase")
            S["sp_end_by"] = [r.get("by") for r in rows()[r0:] if r["step"] == "minigame_practice_end"]
            S["sp_title_alive"] = title_alive()
            S["sp_hotkeys_total"] = len(HOTKEYS) - h0
            S["sp_states_same"] = ({p_.name: p_.read_bytes() for p_ in st_dir.glob("*")} if st_dir.is_dir() else {}) == st_before
            S["sp_real_go"] = call("POST", "/plugins/games/party-minigame-go")["body"].get("go")
            wait_phase(lambda b: b.get("state") != "starting", 20)
            v2_ = len(VP["log"])
            bridge._apply_report(0, 0x0020, 0, 0, 0, 0, 0, 0)    # Select alone after a real go: passes
            bridge._apply_report(0, 0, 0, 0, 0, 0, 0, 0)
            S["sp_select_written_after_real_go"] = sum(1 for x in VP["log"][v2_:] if x[2] & 0x0020)
            S["sp_held_after_real_go"] = bool(getattr(bridge, "_party_hold_select", False))
            fake["ra"].screen = "end_P1"
            wait_for(lambda b: b.get("state") in ("ended", "given_up"), 30)
            finish_case("sp", r0)
            S["sp_held_after_end"] = bool(getattr(bridge, "_party_hold_select", False))
            # N5: during the mute — the board's end, the onn's Home, a second start, the onn's END
            layer.advance_gap_s = 0.7
            TITLE["show_after"] = 2
            for tag, how in (("n5b", "board"), ("n5h", "home"), ("n5s", "second"), ("n5e", "onn_end")):
                PRESS["players"] = [0, 1]; PRESS["on"] = True
                r0 = held_start(tag, tok2, "1,2", ["other"])
                S[tag + "_mute_seen"] = wait_until(lambda: bool(getattr(bridge, "_party_mute", False)), 10)
                if how == "board":
                    S[tag + "_call"] = timed("board_end", "POST", "/plugins/games/party-minigame-end")["code"]
                elif how == "home":
                    S[tag + "_call"] = timed("home", "POST", "/plugins/games/native-stream-stop")["code"]
                    client.in_stream = False
                elif how == "second":
                    S[tag + "_call"] = call("POST", f"/plugins/games/party-minigame-start?id={tok2}&seats=1,2&hold=1")["code"]
                    S[tag + "_mute_still"] = bool(getattr(bridge, "_party_mute", False))
                    timed("board_end", "POST", "/plugins/games/party-minigame-end")
                else:
                    S[tag + "_call"] = timed("end_onn", "POST", "/plugins/games/stop")["code"]
                wait_until(lambda: layer.mg.get("closed"), 15)
                PRESS["on"] = False
                time.sleep(0.3)
                S[tag] = {k: layer.mg.get(k) for k in ("state", "why", "closed")}
                S[tag + "_mute_after"] = bool(getattr(bridge, "_party_mute", False))
                S[tag + "_title_gone"] = not title_alive()
                S[tag + "_route"] = bridge._party_route
                S[tag + "_switches"] = [[r.get("window"), r.get("switched")] for r in rows()[r0:]
                                        if r["step"] == "minigame_stream"]
                if how == "home":
                    call("POST", "/plugins/games/native-stream-start?port=48100")
                    client.in_stream = True
                    call("POST", "/plugins/games/native-stream-ready")
                    S[tag + "_kind_after"] = call("GET", "/plugins/games/status")["body"].get("launch_kind")
                if how == "onn_end":
                    S[tag + "_board_gone"] = wait_until(lambda: board_pid_now() is None, 15)
            layer.advance_gap_s = 0.06
            TITLE["show_after"] = None
            S["n_lat"] = {k: max(v) if v else None for k, v in out["lat"].items()}
            # B139: the users' own launch of the same game in the same companion (no mini game on)
            wait_until(lambda: board_pid_now() is None, 10)
            call("POST", f"/plugins/games/launch?id={title}")
            call("POST", "/plugins/games/stop")
        S["b139_launches"] = [{"party": c["party"], "keys": c["keys"]} for c in LAUNCH_CFG]
        S["b139_users_cfg"] = next((c for c in reversed(LAUNCH_CFG) if not c["party"]), None)
        es_.Reader.read = _read
    S["h_running_at_end"] = [title_alive()]
    timed("end_onn", "POST", "/plugins/games/stop")
    wait_until(lambda: board_pid_now() is None, 10)
    S["h_board_at_end"] = board_pid_now()
    finish()
if args["mode"] == "three":
    def real_stall(tag):
        """The client's video stops while the title plays, outside the switch windows: handled as today."""
        time.sleep(4.0)                                    # past the way in's window (3 s after its switch)
        q0, k0 = len(rec_rows()), len(keys())
        client.silent = True
        S[tag + "_paused_by_stall"] = wait_until(lambda: fake["ra"].paused, 3)
        time.sleep(0.2)
        client.silent = False
        S[tag + "_resumed_after_stall"] = wait_until(lambda: not fake["ra"].paused, 5)
        time.sleep(0.5)
        S[tag + "_stall_rec"] = [[r.get("event"), r.get("trigger") or r.get("via")] for r in rec_rows()[q0:]]
        S[tag + "_stall_keys"] = keys()[k0:]
    s0 = len(client.__dict__)
    one("m1", "1,2", END2, home_resume=True)
    one("m2", "2,1", END1)
    one("m3", "1,2", END3, during=real_stall)
    S["abr_all"] = [[r.get("event"), r.get("source")] for r in abr_rows()
                    if r.get("event") in ("ssrc_change", "escalation_armed", "transition", "transition_done")]
    S["stream_all"] = [e[:2] for e in stream.events]
    timed("end_onn", "POST", "/plugins/games/stop")
    finish()
one("m1", "1,2", END2, home_resume=True)
one("m2", "1,2", END1)
S["b2b_events"] = [e[:2] for e in stream.events]
out["board_pid"] = board_pid

if args["mode"] == "b2b":
    call("POST", "/plugins/games/stop")
    finish()

# --- after the fix: END in every phase, and the stuck starts ------------------------------------------------------
LONG = ["start"] * 3 + ["other"] * 2000


def end_case(tag, when):
    """END (`stop`) from the onn at a phase; then the title, the board and the stream must be gone."""
    bp = board_up(tag)
    pic.set(LONG)
    k0, r0 = len(keys()), len(rows())
    if when == "starting":
        stream.start_s = 2.0
        timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
        time.sleep(0.05)
    elif when == "playing":
        timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
        wait_for(lambda b: b.get("state") == "playing", 25)
    elif when == "handover_in":
        stream.start_s = 3.0
        timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
        wait_until(lambda: stream.restarting, 15)
    elif when == "handover_back":
        stream.start_s = 3.0
        pic.set(END1)
        timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
        wait_for(lambda b: b.get("state") == "ended", 30)
        timed("board_end", "POST", "/plugins/games/party-minigame-end")
        wait_until(lambda: stream.restarting, 15)
    elif when == "stuck":
        stream.gate.clear()
        timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
        wait_until(lambda: stream.restarting, 15)
        time.sleep(0.5)
    S[tag + "_state_at_end"] = result_now().get("state")
    st = timed("end_onn", "POST", "/plugins/games/stop")
    S[tag + "_stop"] = {"code": st["code"], "taken": st["body"].get("taken")}
    gone = wait_until(lambda: not (board_dir / "pid").exists() and ("ra" not in fake or fake["ra"].poll() is not None), 20)
    if when == "stuck":
        stream.gate.set()
    S[tag + "_gone"] = gone
    S[tag + "_closed"] = wait_for(lambda b: b.get("closed"), 20).get("closed")
    S[tag + "_why"] = result_now().get("why")
    S[tag + "_keys"] = keys()[k0:]
    S[tag + "_active_after"] = wait_until(lambda: call("GET", "/plugins/games/status")["body"].get("active") is False, 10)
    S[tag + "_route_after"] = bridge._party_route
    S[tag + "_rows"] = [r["step"] for r in rows()[r0:]]
    stream.start_s = float(args.get("start_s", 0.6))
    client.in_stream = False


for tag in ("starting", "playing", "handover_in", "handover_back", "stuck"):
    end_case("end_" + tag, tag)


def give_up_case(tag, how):
    bp = board_up(tag)
    pic.set(LONG)
    r0 = len(rows())
    layer.start_limit_s, layer.switch_limit_s = 3.0, 2.0
    if how == "switch":
        stream.gate.clear()
    else:
        real = mini.start
        hold = threading.Event()
        def stuck_start(*a, **k):
            hold.wait(30)
            return real(*a, **k)
        mini.start = stuck_start
    timed("start", "POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
    g_ = wait_for(lambda b: b.get("state") == "given_up", 15)
    S[tag] = {"state": g_.get("state"), "why": g_.get("why")}
    if how == "switch":
        stream.gate.set()
    S[tag + "_board_end"] = timed("board_end", "POST", "/plugins/games/party-minigame-end")["code"]   # as the board does
    S[tag + "_closed"] = wait_for(lambda b: b.get("closed"), 20).get("closed")
    S[tag + "_title_gone"] = wait_until(lambda: fake["ra"].poll() is not None, 10)
    S[tag + "_board_kind"] = wait_until(lambda: call("GET", "/plugins/games/status")["body"].get("launch_kind") == "godot", 10)
    S[tag + "_board_alive"] = (board_dir / "pid").exists()
    S[tag + "_route_after"] = bridge._party_route
    S[tag + "_picture_back"] = wait_until(lambda: stream.captured_pid == bp and stream.active, 15)
    S[tag + "_rows"] = [r["step"] for r in rows()[r0:]]
    if how != "switch":
        hold.set(); mini.start = real
    layer.start_limit_s, layer.switch_limit_s = 30.0, 15.0
    timed("end_onn", "POST", "/plugins/games/stop")
    wait_until(lambda: not (board_dir / "pid").exists(), 10)
    client.in_stream = False


give_up_case("stuck_watch", "watch")
give_up_case("stuck_switch", "switch")
finish()
