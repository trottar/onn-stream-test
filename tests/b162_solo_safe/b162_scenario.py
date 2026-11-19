# B162: run inside B114's child (its globals: root, port, rules_, g, m, layer, pic, call, rows, one, END1, board_up,
# client, S, finish, title, ...) by b114_scenario.py's `b162` mode; kept in its own file (the child's -c text has a
# size limit). The add-a-game tool's solo against this companion: two made-up two-player titles and a four-player one
# listed (the other two-player one the harness's N64 title), the one-title setting set by solo, a match of the other, the setting cleared by solo --read, by close
# and by a new layer (a restart); three two-player titles, the one under test always the only two-player entry.
sys.path.insert(0, args["tools"])
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
    (agw / "kept").mkdir(parents=True, exist_ok=True)
    os.environ.update({"PRIVYHUB_ADD_GAME_HUB": f"http://127.0.0.1:{port}", "PRIVYHUB_ADD_GAME_HOME": str(agw / "home"),
                       "PRIVYHUB_ADD_GAME_EVIDENCE": str(agw / "evidence"), "PRIVYHUB_ADD_GAME_PROJECT": str(root),
                       "PRIVYHUB_ADD_GAME_DROPINS": str(agw / "dropins"), "PRIVYHUB_ADD_GAME_SYSTEMCTL": str(ctl),
                       "PRIVYHUB_ADD_GAME_KEPT_ROOT": str(agw / "kept")})
    import party_add_game as pag
    import importlib.util as ilu2_
    spec2_ = ilu2_.find_spec("subprocess"); sp2_ = ilu2_.module_from_spec(spec2_); spec2_.loader.exec_module(sp2_)
    pag.subprocess = sp2_                                    # the harness replaced subprocess.Popen (its fake title)
    kilo, bravo = args["kilo"], args["bravo"]
    def put(gid_, players_):                                 # a title in the rules folder: the harness title's spec
        js2 = json.loads((rules_ / f"{title}.endscreen.json").read_text())
        shutil.copyfile(rules_ / js2["arrays"], rules_ / f"{gid_}.endscreen.npz")
        js2["arrays"] = f"{gid_}.endscreen.npz"
        (rules_ / f"{gid_}.endscreen.json").write_text(json.dumps(js2))
        (rules_ / f"{gid_}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
        sc_ = {"end_P1": [1, 0] + [0] * (players_ - 2), "end_P2": [0, 1] + [0] * (players_ - 2)}
        (rules_ / f"{gid_}.party.json").write_text(json.dumps({"players": players_, "scores": sc_}))
    put(kilo, 2)
    put(bravo, 4)
    def listed():
        return sorted((e["players"], e["title"], e["id"]) for e in
                      call("GET", "/plugins/games/party-minigames")["body"]["minigames"])
    def two_titles():
        return sorted(t_ for n_, t_, _i in listed() if n_ == 2)
    def name_of(gid_):
        return str(g._find_game_by_id(gid_)["title"])
    TOK = {name_of(x): None for x in (title, kilo, bravo)}
    for n_, t_, i_ in listed():
        TOK[t_] = i_
    S["names"] = [name_of(x) for x in (title, kilo, bravo)] + [title, kilo, bravo, str(root)]
    S["list_before"] = [[n_, t_] for n_, t_, _i in listed()]
    def tool(*a_):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc_ = pag.main([str(x) for x in a_])
        keep_ = [ln for ln in buf.getvalue().splitlines() if not ln.startswith("127.0.0.1 - ")]
        return {"rc": rc_, "out": "\n".join(keep_)}
    def verdict(code_, stage_):
        v_ = pag.load_verdict(code_, stage_) or {}
        return {"verdict": v_.get("verdict"), "bad": [c["cell"] for c in v_.get("cells", []) if not c["met"]],
                "cells": {c["cell"]: c["read"] for c in v_.get("cells", [])}}
    lines0 = pag._companion_lines()
    for code_, gid_ in (("T90", title), ("T91", kilo)):      # described titles (T88's way), learn's PASS kept
        b_ = {"code": code_, "game": gid_, "players": 2, "system": "ps1" if gid_ == title else "n64", "result": "winner",
              "cheat": None,
              "relative_path": "", "title": "", "content": "", "described": True, "register_inputs": "r" + code_,
              "found_lines": pag.digest(lines0)}
        (agw / "home" / code_).mkdir(parents=True, exist_ok=True)
        (agw / "home" / code_ / "binding.json").write_text(json.dumps(b_))
        (agw / "evidence" / code_).mkdir(parents=True, exist_ok=True)
        (agw / "evidence" / code_ / "learn.json").write_text(json.dumps({"verdict": "PASS",
                                                                           "inputs": pag.learn_inputs(code_, b_)}))
    def snapshot():                                          # every file under the tree but the logs and the tool's own
        out_ = {}
        for p_ in sorted(root.rglob("*")):
            rel_ = str(p_.relative_to(root))
            if p_.is_file() and not rel_.startswith(("logs/", "ag/", "xdg/")) and "__pycache__" not in rel_:
                out_[rel_] = hashlib.sha256(p_.read_bytes()).hexdigest()
        return out_
    # 1. two two-player titles and a four-player one: the solo of T90 offers it alone
    call("POST", "/plugins/games/native-stream-stop"); client.in_stream = False
    files0 = snapshot()
    r0 = len(rows())
    S["solo_set"] = tool("solo", "T90")
    S["files_same_after_set"] = snapshot() == files0
    S["list_set"] = [[n_, t_] for n_, t_, _i in listed()]
    S["only_rows_set"] = [r_ for r_ in rows()[r0:] if r_.get("step") == "minigame_only"]
    S["only_not_loopback"] = None
    try:
        g.handle_post_request("party-minigame-only", "clear=1", "a-remote-caller")
    except ValueError as exc_:
        S["only_not_loopback"] = str(exc_)
    S["list_after_refused"] = [[n_, t_] for n_, t_, _i in listed()]
    # a match of the other two-player title (its token from before the setting)
    board_up("b162a")
    one("b162kilo", "1,2", END1, tok=TOK[name_of(kilo)])
    call("POST", "/plugins/games/native-stream-stop"); client.in_stream = False
    r1 = len(rows())
    S["read_other"] = tool("solo", "T90", "--read", "--winner", 1)
    S["read_other_v"] = verdict("T90", "solo")
    S["list_after_read"] = [[n_, t_] for n_, t_, _i in listed()]
    S["only_rows_read"] = [r_ for r_ in rows()[r1:] if r_.get("step") == "minigame_only"]
    S["launch_logs"] = len([p_ for p_ in (root / "logs/games").glob("*.log") if pag.LAUNCH_LOG.match(p_.name)
                            and pag.LAUNCH_LOG.match(p_.name).group(2) not in pag.NOT_A_LAUNCH])
    # 2. three two-player titles: the one under test (T91) the only two-player entry at every read
    put(bravo, 2)
    S["three_before"] = two_titles()
    S["solo_set3"] = tool("solo", "T91")
    S["reads3"] = [two_titles() for _ in range(20)]
    board_up("b162b")
    one("b162kilo2", "1,2", END1, tok=TOK[name_of(kilo)])
    call("POST", "/plugins/games/native-stream-stop"); client.in_stream = False
    S["read_this"] = tool("solo", "T91", "--read", "--winner", 1)
    S["read_this_v"] = verdict("T91", "solo")
    S["three_after_read"] = two_titles()
    # 3. cleared by close
    S["solo_again"] = tool("solo", "T90")
    S["before_close"] = two_titles()
    call("POST", "/plugins/games/stop")
    r2 = len(rows())
    S["close"] = tool("close", "T90")
    S["close_v"] = verdict("T90", "close")
    S["after_close"] = two_titles()
    S["only_rows_close"] = [r_ for r_ in rows()[r2:] if r_.get("step") == "minigame_only"]
    # 4. cleared by a restart: the setting is the layer's memory; a new layer (as a new process has) lists all
    S["solo_restart"] = tool("solo", "T90")
    S["before_restart"] = two_titles()
    g._party_minigame_obj = None
    S["after_restart"] = two_titles()
    tool("close", "T90")
    S["texts"] = "\n".join(p_.read_text() for p_ in sorted((agw / "evidence").rglob("*")) if p_.is_file()) + \
        "\n".join(S[k_]["out"] for k_ in list(S) if isinstance(S[k_], dict) and "out" in S[k_])
    S["only_rows_all"] = [r_ for r_ in rows() if r_.get("step") == "minigame_only"]
except Exception as exc_:
    import traceback as tb_
    S["b162_error"] = tb_.format_exc()[-3000:]
timed("end_onn", "POST", "/plugins/games/stop")
finish()
