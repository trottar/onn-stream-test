# B157: run inside B114's child (its globals: root, port, rules_, g, m, layer, pic, FakeRetroArch, S, ...) by
# b114_scenario.py's `b157` mode; kept in its own file (the child's -c text has a size limit).
# B157: the add-a-game tool through the real routes. The made-up two-player PS1 title and the made-up four-player
# N64 one, their "user's saves" made-up states in the users' own slots (the slot index as the hub keeps it); the
# tool's register / learn / bench run in this process against this companion; the pictures made-up
# (tests/b157_add_game/fake_capture.py). The fake RetroArch shows the screen a loaded state names.
import importlib as il_
sys.path.insert(0, args["tools"]); sys.path.insert(0, args["fake_dir"])
import fake_capture as fc
try:
    agw = root / "ag"
    (agw / "dropins").mkdir(parents=True, exist_ok=True)
    for i in range(18):
        (agw / "dropins" / f"line{i:02d}.conf").write_text(f"[Service]\nEnvironment=PRIVYHUB_LINE{i:02d}=1\n")
    ctl = agw / "systemctl"
    ctl.write_text("#!/bin/sh\nif [ \"$1\" = \"--user\" ] && [ \"$2\" = \"list-units\" ]; then\n"
                   "  echo 'privyhub-companion.service loaded active running x'\n"
                   "  echo 'privyhub-diag.service loaded active running x'\nfi\nexit 0\n")
    ctl.chmod(0o755)
    os.environ.update({"PRIVYHUB_ADD_GAME_HUB": f"http://127.0.0.1:{port}", "PRIVYHUB_ADD_GAME_HOME": str(agw / "home"),
                       "PRIVYHUB_ADD_GAME_EVIDENCE": str(agw / "evidence"), "PRIVYHUB_ADD_GAME_PROJECT": str(root),
                       "PRIVYHUB_ADD_GAME_DROPINS": str(agw / "dropins"), "PRIVYHUB_ADD_GAME_SYSTEMCTL": str(ctl),
                       "PARTY_ADD_GAME_CAPTURE": "fake_capture:capture"})
    import party_add_game as pag
    import importlib.util as ilu2_
    spec2_ = ilu2_.find_spec("subprocess"); sp2_ = ilu2_.module_from_spec(spec2_); spec2_.loader.exec_module(sp2_)
    pag.subprocess = sp2_                                    # the harness replaced subprocess.Popen (its fake title)
    (agw / "kept").mkdir(parents=True, exist_ok=True)
    os.environ["PRIVYHUB_ADD_GAME_KEPT_ROOT"] = str(agw / "kept")
    (agw / "kept" / "t00").mkdir(exist_ok=True); (agw / "kept" / "t00" / "begin.state").write_text("made-up kept state")
    for k_, f_ in (args.get("bars") or {}).items():          # the tests' own bar changes (none in a normal run)
        pag.BARS[k_] = (f_, "test")
    n64 = args["n64_id"]
    for gid_ in (title, n64):                                # the harness's own rules for them: not this test's
        for suf_ in (".endscreen.json", ".endscreen.npz", ".state", ".party.json"):
            (rules_ / f"{gid_}{suf_}").unlink(missing_ok=True)
    TOK = {v: k for k, v in fc.CODES.items()}
    _put = FakeRetroArch.put
    def _put_pic(self_, a_, b_):                            # a loaded state's screen on the fake's window
        _put(self_, a_, b_)
        if int(a_) in fc.CODES:
            pic.set([fc.CODES[int(a_)]] * 4000)
    FakeRetroArch.put = _put_pic
    layer.practice_s = 1.6                                   # the practice's time alone (scaled)
    def folder():                                            # the fake's slot folder: the running title's core's own
        return m._state_root() / ("Mupen64Plus-Next" if m._n64_core else "Beetle PSX HW")
    globals()["folder"] = folder
    def slots(gid_, roles):                                  # the user's SAVE: slots 1-3 written, the index kept
        rec = g._find_game_by_id(gid_)
        rel = str(rec["relative_path"]); stem = Path(rel).stem
        core = "Mupen64Plus-Next" if rec["system"] == "n64" else "Beetle PSX HW"
        d_ = root / "data/games/retroarch/states" / core
        d_.mkdir(parents=True, exist_ok=True)
        ix = root / "data/games/retroarch/privyhub_state_slots.json"
        idx = json.loads(ix.read_text()) if ix.is_file() else {"schema": 1, "games": {}}
        ent = idx["games"].setdefault(f"{rec['system'].casefold()}::{rel.casefold()}", {"slots": {}})
        for n_, tok_ in roles.items():
            f_ = d_ / f"{stem}.state{n_}"
            tok_, _, again_ = tok_.partition("#")             # B171: "end_P1#2" — another save of the same screen
            f_.write_text(json.dumps({"P1": TOK[tok_], "P2": int(again_ or 0)}))
            ent["slots"][str(n_)] = {"state_file": str(f_.relative_to(root))}
        ix.write_text(json.dumps(idx))
        return rec
    def tool(*a_):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_ = pag.main([str(x) for x in a_])
        keep_ = [ln for ln in buf.getvalue().splitlines() if not ln.startswith("127.0.0.1 - ")]   # the companion's log
        return {"rc": rc_, "out": "\n".join(keep_)}
    def verdict(code_, stage_):
        v_ = pag.load_verdict(code_, stage_) or {}
        return {"verdict": v_.get("verdict"), "bad": [c["cell"] for c in v_.get("cells", []) if not c["met"]],
                "cells": {c["cell"]: c["read"] for c in v_.get("cells", [])}}
    rec2 = slots(title, {1: "start", 2: "other", 3: "end_P1"})
    words2 = str(rec2["title"])
    reg2 = ["register", "T90", "--players", 2, "--system", rec2["system"], "--result", "winner", "--find", words2,
            "--setup", "none"]
    S["t90_learn_first"] = tool("learn", "T90")
    S["t90_reg_missing"] = tool(*reg2, "--collect", "begin=1", "--collect", "other=2", "--collect", "end_P1=3")
    S["t90_reg_missing_v"] = verdict("T90", "register")
    slots(title, {1: "end_P2", 2: "end_P1#2", 3: "end_P2#2"})          # B171: two saves per ending
    S["t90_reg"] = tool(*reg2, "--collect", "end_P2=1", "--collect", "end_P1_2=2", "--collect", "end_P2_2=3")
    S["t90_reg_v"] = verdict("T90", "register")
    S["t90_learn"] = tool("learn", "T90")
    S["t90_learn_v"] = verdict("T90", "learn")
    ev_ = agw / "evidence" / "T90"
    m1 = {p_.name: (p_.stat().st_mtime_ns, p_.read_bytes()) for p_ in (ev_.iterdir() if ev_.is_dir() else [])}
    r1 = {p_.name: p_.stat().st_mtime_ns for p_ in rules_.iterdir() if p_.name.startswith(title)}
    S["t90_learn_again"] = tool("learn", "T90")
    m2 = {p_.name: (p_.stat().st_mtime_ns, p_.read_bytes()) for p_ in (ev_.iterdir() if ev_.is_dir() else [])}
    r2 = {p_.name: p_.stat().st_mtime_ns for p_ in rules_.iterdir() if p_.name.startswith(title)}
    S["t90_twice_same"] = [m1 == m2, r1 == r2, sorted(r1) == sorted(r2)]
    call("POST", "/plugins/games/native-stream-stop")         # the bench needs no client stream (B112)
    client.in_stream = False
    S["t90_bench"] = tool("bench", "T90")
    S["t90_bench_v"] = verdict("T90", "bench")
    S["t90_close"] = tool("close", "T90")
    S["t90_close_v"] = verdict("T90", "close")
    # the gates on the bench: a start not PAUSED (the title resumed during the hold), a file changed, a reload
    def during_hold(fn_):
        def watch():
            end_ = time.monotonic() + 40
            while time.monotonic() < end_:
                if any(r_.get("step") == "minigame_ready" for r_ in rows()[n0_:]):
                    time.sleep(1.5); fn_(); return
                time.sleep(0.1)
        n0_ = len(rows())
        threading.Thread(target=watch, daemon=True).start()
    def resume_title():
        s_ = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s_.sendto(b"PAUSE_TOGGLE", ("127.0.0.1", int(m._network_cmd_port))); s_.close()
    for tag_, fn_ in (("notpaused", resume_title),
                      ("filechanged", lambda: (agw / "kept" / "t00" / "marker").write_text("changed")),
                      ("reload", lambda: (root / "logs/games/party.jsonl").open("a").write(
                          json.dumps({"step": "minigame_watch", "loaded": True}) + "\n"))):
        board_up("b157" + tag_)                               # the stand-in board's own relaunch step
        call("POST", "/plugins/games/native-stream-stop"); client.in_stream = False
        during_hold(fn_)
        S[f"t90_bench_{tag_}"] = tool("bench", "T90")
        S[f"t90_bench_{tag_}_v"] = verdict("T90", "bench")
        tool("close", "T90")                                 # always, after a stop too
        (agw / "kept" / "t00" / "marker").unlink(missing_ok=True)
    # an ending that reads as another's class: T91's end_P2 slot holds end_P1's screen
    slots(title, {1: "start", 2: "other", 3: "end_P1"})
    reg91 = ["register", "T91"] + reg2[2:]
    tool(*reg91, "--collect", "begin=1", "--collect", "other=2", "--collect", "end_P1=3")
    (agw / "home" / "T91" / "kept" / "end_P2.state").write_text(json.dumps({"P1": TOK["end_P1"], "P2": 1}))
    for r_, p2_ in (("end_P1_2", 2), ("end_P2_2", 3)):          # B171: two saves per ending (end_P2's shows end_P1's)
        (agw / "home" / "T91" / "kept" / f"{r_}.state").write_text(json.dumps({"P1": TOK["end_P1"], "P2": p2_}))
    S["t91_reg"] = tool(*reg91)
    S["t91_learn"] = tool("learn", "T91")
    S["t91_learn_v"] = verdict("T91", "learn")
    # bench refused after its inputs changed (T90's kept end_P1 replaced since learn's PASS)
    (agw / "home" / "T90" / "kept" / "end_P1.state").write_text(json.dumps({"P1": TOK["end_P1"], "P2": 7}))
    S["t90_bench_changed"] = tool("bench", "T90")
    tool("close", "T90")
    # the four-player title (places): six saves in two rounds of three
    rec4 = slots(n64, {1: "s4start", 2: "s4other", 3: "s4r1234"})
    reg4 = ["register", "T97", "--players", 4, "--system", rec4["system"], "--result", "places", "--find",
            str(rec4["title"]), "--setup", "none"]
    tool(*reg4, "--collect", "begin=1", "--collect", "other=2", "--collect", "end_r1234=3")
    slots(n64, {1: "s4r2341", 2: "s4r3412", 3: "s4r4123"})
    S["t97_reg"] = tool(*reg4, "--collect", "end_r2341=1", "--collect", "end_r3412=2", "--collect", "end_r4123=3")
    S["t97_reg_v"] = verdict("T97", "register")
    S["t97_learn"] = tool("learn", "T97")
    S["t97_learn_v"] = verdict("T97", "learn")
    board_up("b157four")
    call("POST", "/plugins/games/native-stream-stop"); client.in_stream = False
    S["t97_bench"] = tool("bench", "T97")
    S["t97_bench_v"] = verdict("T97", "bench")
    S["t97_close"] = tool("close", "T97")
    S["names"] = [words2, str(rec4["title"]), title, n64, str(root)]
    S["written"] = [str(p_.relative_to(agw)) for p_ in sorted((agw / "evidence").rglob("*")) if p_.is_file()]
    S["texts"] = "\n".join(p_.read_text() for p_ in sorted((agw / "evidence").rglob("*")) if p_.is_file()) + \
        "\n".join(S[k_]["out"] for k_ in list(S) if isinstance(S[k_], dict) and "out" in S[k_])
except Exception as exc_:
    import traceback as tb_
    S["b157_error"] = tb_.format_exc()[-3000:]
FakeRetroArch.put = _put
timed("end_onn", "POST", "/plugins/games/stop")
finish()
