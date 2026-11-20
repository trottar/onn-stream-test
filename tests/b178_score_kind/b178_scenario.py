# B178: run inside B114's child (its globals: root, port, rules_, g, m, layer, pic, FakeRetroArch, S, title, one, ...)
# by b114_scenario.py's `b178` mode; kept in its own file (the child's -c text has a size limit).
# Part 1 — the add-a-game tool through the real routes for a made-up `score` title (the harness's two-player PS1
# title): the user's "saves" made-up states in the users' own slots, the pictures made-up (score_capture.py), the
# session's readings given as the session would; register --result score -> label -> learn -> bench -> close.
# Part 2 — the hub with the rules learn wrote: listed; ended with the real numbers and the winner's seat (seats 1,2
# and 2,1); a tie -> winner null; numbers with digits never learnt -> no result (given up by the unknown rule), never
# a guess; a sidecar `score` with another spec or with `scores` -> not listed.
sys.path.insert(0, args["tools"]); sys.path.insert(0, args["b178_dir"])
import score_capture as sc
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
                       "PARTY_ADD_GAME_CAPTURE": "score_capture:capture_codes",
                       "PRIVYHUB_ADD_GAME_KEPT_ROOT": str(agw / "kept")})
    (agw / "kept").mkdir(parents=True, exist_ok=True)
    import party_add_game as pag
    import importlib.util as ilu3_
    spec3_ = ilu3_.find_spec("subprocess"); sp3_ = ilu3_.module_from_spec(spec3_); spec3_.loader.exec_module(sp3_)
    pag.subprocess = sp3_                                    # the harness replaced subprocess.Popen (its fake title)
    for suf_ in (".endscreen.json", ".endscreen.npz", ".state", ".party.json"):
        (rules_ / f"{title}{suf_}").unlink(missing_ok=True)  # the harness's own rules for it: not this test's
    _put = FakeRetroArch.put
    def _put_pic(self_, a_, b_):                            # a loaded state's screen on the fake's window
        _put(self_, a_, b_)
        if int(a_) in sc.CODES:
            pic.set([f"sc{int(a_)}"] * 4000)
    FakeRetroArch.put = _put_pic
    layer.practice_s = 1.6
    def slots(gid_, roles):                                  # the user's SAVE: slots 1-3 written, the index kept
        rec = g._find_game_by_id(gid_)
        rel = str(rec["relative_path"]); stem = Path(rel).stem
        d_ = root / "data/games/retroarch/states" / "Beetle PSX HW"
        d_.mkdir(parents=True, exist_ok=True)
        ix = root / "data/games/retroarch/privyhub_state_slots.json"
        idx = json.loads(ix.read_text()) if ix.is_file() else {"schema": 1, "games": {}}
        ent = idx["games"].setdefault(f"{rec['system'].casefold()}::{rel.casefold()}", {"slots": {}})
        for n_, code_ in roles.items():
            f_ = d_ / f"{stem}.state{n_}"
            f_.write_text(json.dumps({"P1": int(code_), "P2": 0}))
            ent["slots"][str(n_)] = {"state_file": str(f_.relative_to(root))}
        ix.write_text(json.dumps(idx))
        return rec
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
    # --- part 1: the tool's whole path
    rec2 = slots(title, {1: 300, 2: 301, 3: 310})
    words2 = str(rec2["title"])
    reg = ["register", "T90", "--players", 2, "--system", rec2["system"], "--result", "score", "--find", words2,
           "--setup", "none"]
    S["s_reg1"] = tool(*reg, "--collect", "begin=1", "--collect", "other=2", "--collect", "end_P1=3")
    slots(title, {1: 312, 2: 311, 3: 313})
    S["s_reg"] = tool(*reg, "--collect", "end_P2=1", "--collect", "end_P1_2=2", "--collect", "end_P2_2=3")
    S["s_reg_v"] = verdict("T90", "register")
    S["s_learn_before_label"] = tool("learn", "T90")
    S["s_label_first"] = tool("label", "T90")
    S["s_label_pictures"] = sorted(p_.name for p_ in (agw / "home" / "T90" / "label").iterdir())
    readings = [f"{r_}={'-'.join(map(str, sc.SCORES[c_]))},{'-'.join(map(str, sc.SCORES[c_]))}"
                for r_, c_ in (("end_P1", 310), ("end_P1_2", 311), ("end_P2", 312), ("end_P2_2", 313))]
    S["s_label"] = tool("label", "T90", *readings)
    S["s_label_v"] = verdict("T90", "label")
    S["s_learn"] = tool("learn", "T90")
    S["s_learn_v"] = verdict("T90", "learn")
    S["s_sidecar"] = json.loads((rules_ / f"{title}.party.json").read_text()) if (rules_ / f"{title}.party.json").is_file() else None
    S["s_spec_version"] = json.loads((rules_ / f"{title}.endscreen.json").read_text()).get("version") \
        if (rules_ / f"{title}.endscreen.json").is_file() else None
    call("POST", "/plugins/games/native-stream-stop")
    client.in_stream = False
    S["s_bench"] = tool("bench", "T90")
    S["s_bench_v"] = verdict("T90", "bench")
    S["s_close"] = tool("close", "T90")
    S["s_close_v"] = verdict("T90", "close")
    S["names"] = [words2, title, str(root)]
    S["texts"] = "\n".join(p_.read_text() for p_ in sorted((agw / "evidence").rglob("*")) if p_.is_file()) + \
        "\n".join(S[k_]["out"] for k_ in list(S) if isinstance(S[k_], dict) and "out" in S[k_])
    FakeRetroArch.put = _put
    # --- part 2: the hub with the rules learn wrote
    (rules_ / f"{title}.state").write_text(json.dumps({"P1": 0, "P2": 0}))    # the begin: the fake's plain state
    board_up("b178hub")                                      # close stopped the board: the stand-in board again
    call("POST", "/plugins/games/native-stream-start?port=48100&player_prompt=1")
    call("POST", "/plugins/games/native-stream-ready")
    client.in_stream = True
    listed = call("GET", "/plugins/games/party-minigames")["body"]["minigames"]
    S["h_list"] = sorted(e["players"] for e in listed)
    tok = next(e["id"] for e in listed if e["players"] == 2)
    lead = ["sc300"] * 3 + ["sc301"] * 6
    for tag, seats, end_tok in (("h_a", "1,2", "sc310"), ("h_b", "2,1", "sc310"), ("h_tie", "1,2", "sc320")):
        r0 = len(rows())
        one(tag, seats, lead + [end_tok] * 40, tok=tok)
        S[tag + "_ended_rows"] = [{k_: v_ for k_, v_ in r_.items() if k_ in ("class", "scores", "winner")}
                                  for r_ in rows()[r0:] if r_["step"] == "minigame_ended"]
    layer.unknown_limit_s = 2.0                              # an unreadable final screen: no result, never a guess
    r0 = len(rows())
    one("h_unread", "1,2", lead + ["sc321"] * 400, tok=tok)
    S["h_unread_rows"] = [r_["step"] for r_ in rows()[r0:] if r_["step"] in ("minigame_ended", "minigame_given_up")]
    layer.unknown_limit_s = 30.0
    side_ = json.loads((rules_ / f"{title}.party.json").read_text())
    for tag, side2 in (("with_scores", {**side_, "scores": {"end": [1, 0]}}), ("four", {**side_, "players": 4})):
        (rules_ / f"{title}.party.json").write_text(json.dumps(side2))
        S["h_list_" + tag] = sorted(e["players"] for e in call("GET", "/plugins/games/party-minigames")["body"]["minigames"])
    (rules_ / f"{title}.party.json").write_text(json.dumps(side_))
except Exception as exc_:
    import traceback as tb_
    S["b178_error"] = tb_.format_exc()[-3000:]
FakeRetroArch.put = _put
timed("end_onn", "POST", "/plugins/games/stop")
finish()
