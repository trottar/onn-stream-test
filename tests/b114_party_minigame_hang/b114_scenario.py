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
def watcher(kind, path):
    while watching["on"]:
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
                            "status_idle": ("GET", "/plugins/games/status"),
                            "home_idle": ("POST", "/plugins/games/native-stream-stop"),
                            "stop_idle": ("POST", "/plugins/games/stop")}.items():
        S[k] = call(meth, path)
    # B124: a title's start with the prompt answers its players and ports as today (no board without the flag)
    call("POST", f"/plugins/games/launch?id={title}")
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
    def _popen(cmd, **kw):                            # RetroArch's command line kept (its session config)
        LAST["cmd"] = [str(c) for c in cmd]
        POPENS.append(1)
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
